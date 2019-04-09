import logging

from flask import current_app as app
from flask import request
from flask.views import MethodView

from auslib.db import (ChangeScheduledError, OutdatedDataError,
                       PermissionDeniedError, SignoffRequiredError,
                       UpdateMergeError)
from auslib.global_state import dbo
from auslib.util.auth import verified_userinfo
from auslib.web.admin.views.problem import problem

log = logging.getLogger(__name__)


def requirelogin(f):
    def decorated(*args, **kwargs):
        username = verified_userinfo(request, app.config["AUTH_DOMAIN"], app.config["AUTH_AUDIENCE"])["email"]
        if not username:
            log.warning("Login Required")
            return problem(401, "Unauthenticated", "Login Required")
        # Machine to machine accounts are identified by uninformative clientIds
        # In order to keep Balrog permissions more readable, we map them to
        # more useful usernames, which are stored in the app config.
        if "@" not in username:
            username = app.config["M2M_ACCOUNT_MAPPING"].get(username, username)
        # Even if the user has provided a valid access token, we don't want to assume
        # that person should be able to access Balrog (in case auth0 is not configured
        # to be restrictive enough.
        elif not dbo.isKnownUser(username):
            log.warning("Authorization Required")
            return problem(403, "Forbidden", "Authorization Required")
        return f(*args, changed_by=username, **kwargs)

    return decorated


def handleGeneralExceptions(messages):
    def wrap(f):
        def decorated(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except OutdatedDataError as e:
                msg = "Couldn't perform the request %s. Outdated Data Version. " "old_data_version doesn't match current data_version" % messages
                log.warning("Bad input: %s", msg)
                log.warning(e)
                # using connexion.problem results in TypeError: 'ConnexionResponse' object is not callable
                # hence using flask.Response but modifying response's json data into connexion.problem format
                # for validation purpose
                return problem(400, "Bad Request", "OutdatedDataError", ext={"exception": msg})
            except UpdateMergeError as e:
                msg = "Couldn't perform the request %s due to merge error. " "Is there a scheduled change that conflicts with yours?" % messages
                log.warning("Bad input: %s", msg)
                log.warning(e)
                return problem(400, "Bad Request", "UpdateMergeError", ext={"exception": msg})
            except ChangeScheduledError as e:
                msg = "Couldn't perform the request %s due a conflict with a scheduled change. " % messages
                msg += str(e)
                log.warning("Bad input: %s", msg)
                log.warning(e)
                return problem(400, "Bad Request", "ChangeScheduledError", ext={"exception": msg})
            except SignoffRequiredError as e:
                msg = "This change requires signoff, it cannot be done directly. {}".format(e)
                log.warning(msg)
                log.warning(e)
                return problem(400, "Bad Request", "SignoffRequiredError", ext={"exception": msg})
            except PermissionDeniedError as e:
                msg = "Permission denied to perform the request. {}".format(e)
                log.warning(msg)
                return problem(403, "Forbidden", "PermissionDeniedError", ext={"exception": msg})
            except ValueError as e:
                msg = "Bad input: {}".format(e)
                log.warning(msg)
                return problem(400, "Bad Request", "ValueError", ext={"exception": msg})

        return decorated

    return wrap


def transactionHandler(request_handler):
    def decorated(*args, **kwargs):
        trans = dbo.begin()
        # Transactions are automatically rolled back by the context manager if
        # _post raises an Exception, but we need to make sure they are also
        # rolled back if the View returns any sort of error.
        try:
            ret = request_handler(*args, transaction=trans, **kwargs)
            if ret.status_code >= 400:
                trans.rollback()
            else:
                trans.commit()
            return ret
        except Exception:
            trans.rollback()
            raise
        finally:
            trans.close()

    return decorated


class AdminView(MethodView):
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(self.__class__.__name__)
        MethodView.__init__(self, *args, **kwargs)

    @transactionHandler
    @handleGeneralExceptions("POST")
    def post(self, *args, **kwargs):
        self.log.debug("processing POST request to %s" % request.path)
        return self._post(*args, **kwargs)

    @transactionHandler
    @handleGeneralExceptions("PUT")
    def put(self, *args, **kwargs):
        self.log.debug("processing PUT request to %s" % request.path)
        return self._put(*args, **kwargs)

    @transactionHandler
    @handleGeneralExceptions("DELETE")
    def delete(self, *args, **kwargs):
        self.log.debug("processing DELETE request to %s" % request.path)
        return self._delete(*args, **kwargs)


def serialize_signoff_requirements(requirements):
    dct = {}
    for rs in requirements:
        signoffs_required = max(dct.get(rs["role"], 0), rs["signoffs_required"])
        dct[rs["role"]] = signoffs_required

    return dct
