import json
import os
from tempfile import mkstemp

import pytest

from flask.testing import FlaskClient

from auslib.global_state import dbo, cache
from auslib.web.admin.base import app
from auslib.blobs.base import createBlob


class BalrogTestClient(FlaskClient):
    def open(self, *args, **kwargs):
        kwargs.setdefault("content_type", "application/json")
        if "data" in kwargs:
            # add csrf tokens to any requests that need them
            if kwargs.get("method") in ("POST", "PUT", "DELETE") and "csrf_token" not in kwargs["data"]:
                kwargs["data"]["csrf_token"] = "lorem ipsum"
            # and automatically convert data for supported request types
            # this reduces a lot of json.dumps(...) usage in actual tests
            if kwargs.get("method") in ("POST", "PUT"):
                kwargs["data"] = json.dumps(kwargs["data"])
        return super(BalrogTestClient, self).open(*args, **kwargs)


@pytest.fixture(scope="module")
def sampledata():
    statements = []
    with open(os.path.join(os.path.dirname(__file__), "..", "..", "sample_data.sql")) as f:
        for line in f.readlines():
            if not line.startswith(";"):
                statements.append(line)
    return statements


@pytest.fixture(scope="module")
def balrogadmin_init():
    version_fd, version_file = mkstemp()
    cache.make_copies = True
    app.config["SECRET_KEY"] = "abc123"
    app.config["DEBUG"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["WHITELISTED_DOMAINS"] = {"good.com": ("a", "b", "c", "d")}
    app.config["VERSION_FILE"] = version_file
    with open(version_file, "w+") as f:
        f.write("""
{
  "source":"https://github.com/mozilla/balrog",
  "version":"1.0",
  "commit":"abcdef123456"
}
""")
    yield None
    os.close(version_fd)
    os.remove(version_file)


@pytest.fixture
def balrogadmin(balrogadmin_init, sampledata):
    cache.reset()
    dbo.setDb('sqlite:///:memory:')
    dbo.setDomainWhitelist({'good.com': ('a', 'b', 'c', 'd')})
    dbo.create()
    with dbo.begin() as trans:
        for statement in sampledata:
            trans.execute(statement)
    app.test_client_class = BalrogTestClient
    yield app.test_client()
    dbo.reset()
