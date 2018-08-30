from collections import OrderedDict
import json

import pytest

from auslib.global_state import dbo


def test_users(balrogadmin):
    ret = balrogadmin.get("/users")
    assert ret.status_code == 200
    data = ret.get_json()
    assert data == {
        'ashanti': {'roles': []},
        'bill': {'roles': [
            {'role': 'qa', 'data_version': 1},
            {'role': 'releng', 'data_version': 1}]},
        'billy': {'roles': []},
        'bob': {'roles': [{'role': 'relman', 'data_version': 1}]},
        'julie': {'roles': [{'role': 'releng', 'data_version': 1}]},
        'mary': {'roles': [{'role': 'relman', 'data_version': 1}]}
    }


get_user_tests = OrderedDict({
    "current_user_with_permissions_and_roles": (
        "/users/current",
        "bill",
        200,
        {
            "username": "bill",
            "permissions": {
                "admin": {
                    "options": None, "data_version": 1,
                },
            },
            "roles": {
                "releng": {
                    "data_version": 1,
                },
                "qa": {
                    "data_version": 1,
                },
            },
        },
    ),
    "current_user_no_roles": (
        "/users/current",
        "billy",
        200,
        {
            "username": "billy",
            "permissions": {
                "admin": {
                    "options": {
                        "products": ["a"]
                    },
                    "data_version": 1,
                }
            },
            "roles": {},
        },
    ),
    "current_user_no_permissions_or_roles": (
        "/users/current",
        "vikas",
        200,
        {
            "username": "vikas",
            "permissions": {},
            "roles": {},
        },
    ),
    "named_user_not_as_admin": (
        "/users/vikas",
        "vikas",
        404,
        None,
    ),
    "named_user_as_admin": (
        "/users/mary",
        "bill",
        200,
        {
            "username": "mary",
            "permissions": {
                "scheduled_change": {
                    "options": {
                        "actions": ["enact"]
                    },
                    "data_version": 1,
                }
            },
            "roles": {
                "relman": {
                    "data_version": 1,
                },
            },
        },
    ),
    "named_user_with_specific_permission": (
        "/users/mary",
        "bob",
        200,
        {
            "username": "mary",
            "permissions": {
                "scheduled_change": {
                    "options": {
                        "actions": ["enact"]
                    },
                    "data_version": 1,
                }
            },
            "roles": {
                "relman": {
                    "data_version": 1,
                },
            },
        },
    ),
    "named_user_without_permission": (
        "/users/bill",
        "mary",
        403,
        None,
    ),
    "non_existant_user": (
        "/users/uhetonhueo",
        "bob",
        404,
        None,
    ),
})
@pytest.mark.parametrize(
    "path,request_as,code,expected",
    get_user_tests.values(),
    # In Python 3, OrderedDict.keys()' returns a data structure that
    # doesn't support indexing, which pytest requires
    ids=list(get_user_tests.keys()),
)
def test_get_user(balrogadmin, path, request_as, code, expected):
    ret = balrogadmin.get(path, environ_base={"REMOTE_USER": request_as})
    assert ret.status_code == code
    # No response body to test if the code wasn't 200
    if code == 200:
        assert ret.get_json() == expected


get_permission_tests = OrderedDict({
    "collection": (
        "/users/bill/permissions",
        None,
        200,
        {
            "admin": {
                "options": None,
                "data_version": 1,
            }
        },
    ),
    "get": (
        "/users/bill/permissions/admin",
        None,
        200,
        {
            "options": None,
            "data_version": 1,
        },
    ),
    "get_non_existant": (
        "/users/bill/permissions/rule",
        None,
        404,
        None,
    ),
})
@pytest.mark.parametrize(
    "path,request_as,code,expected",
    get_permission_tests.values(),
    ids=list(get_permission_tests.keys()),
)
def test_get_permission(balrogadmin, path, request_as, code, expected):
    ret = balrogadmin.get(path, environ_base={"REMOTE_USER": request_as})
    assert ret.status_code == code
    # No response body to test if the code wasn't 200
    if code == 200:
        assert ret.get_json() == expected


change_permission_tests = OrderedDict({
    "with_options": (
        "PUT",
        "bob",
        "admin",
        {
            "options": json.dumps({
                "products": ["a"],
            })
        },
        "bill",
        201,
        1,
        ("admin", "bob", {"products": ["a"]}, 1),
    ),
    # TODO: This test currently fails because there's no way to insert a permission
    # without options that isn't subject to signoff with our current test fixtures
    #"no_options": (
    #    "PUT",
    #    "bob",
    #    "admin",
    #    {
    #        "options": "{}",
    #    },
    #    "bill",
    #    201,
    #    1,
    #    ("admin", "bob", None, 1),
    #),
    "with_email": (
        "PUT",
        "bob@bobsworld.com",
        "admin",
        {
            "options": json.dumps({
                "products": ["a"],
            })
        },
        "bill",
        201,
        1,
        ("admin", "bob@bobsworld.com", {"products": ["a"]}, 1),
    ),
    # This test is meant to verify that the app properly unquotes URL parts
    # as part of routing, because it is required when running under uwsgi.
    # Unfortunately, Werkzeug's test Client will unquote URL parts before
    # the app sees them, so this test doesn't actually verify that case...
    #"with_quoted_email": (
    #    "PUT",
    #    "bob%40bobsworld.com",
    #    "admin",
    #    {
    #        "options": json.dumps({
    #            "products": ["a"],
    #        })
    #    },
    #    "bill",
    #    201,
    #    1,
    #    ("admin", "bob@bobsworld.com", {"products": ["a"]}, 1),
    #),
    "put_requires_signoff": (
        "PUT",
        "nancy",
        "admin",
        None,
        "bill",
        400,
        None,
        None,
    ),
    "put_modify_existing": (
        "PUT",
        "bob",
        "rule",
        {
            "data_version": 1,
            "options": json.dumps({
                "products": ["a", "b"],
            }),
        },
        "bill",
        200,
        2,
        ("rule", "bob", {"products": ["a", "b"]}, 2),
    ),
    "put_modify_without_data_version": (
        "PUT",
        "bob",
        "release",
        {
            "options": json.dumps({
                "products": ["different"],
            })
        },
        "bill",
        400,
        None,
        None,
    ),
    "put_bad_permission": (
        "PUT",
        "bob",
        "fake",
        None,
        "bill",
        400,
        None,
        None,
    ),
    "put_bad_option": (
        "PUT",
        "bob",
        "admin",
        {
            "options": json.dumps({
                "foo": 2,
            })
        },
        "bill",
        400,
        None,
        None,
    ),
    # Discovered in https://bugzilla.mozilla.org/show_bug.cgi?id=1237264
    "put_bad_json": (
        "PUT",
        "ashanti",
        "rule",
        {
            "options": '{"products":',
        },
        "bill",
        400,
        None,
        None,
    ),
    "put_without_permission": (
        "PUT",
        "bob",
        "rule",
        {
            "data_version": 1,
            "options": json.dumps({
                "actions": ["create"],
            }),
        },
        "julie",
        403,
        None,
        None,
    ),
    "post": (
        "POST",
        "bob",
        "release_read_only",
        {
            "data_version": 1,
            "options": json.dumps({
                "products": ["a", "b"],
            }),
        },
        "bill",
        200,
        2,
        ("release_read_only", "bob", {"products": ["a", "b"]}, 2),
    ),
    "post_non_existant": (
        "POST",
        "bill",
        "rule",
        {
            "data_version": 1,
            "options": "",
        },
        "bill",
        404,
        None,
        None,
    ),
    "post_bad_input": (
        "POST",
        "bill",
        "admin",
        None,
        "bill",
        400,
        None,
        None,
    ),
    "post_without_permission": (
        "POST",
        "bob",
        "rule",
        {
            "data_version": 1,
            "options": json.dumps({
                "actions": ["create"],
            }),
        },
        "shane",
        403,
        None,
        None,
    ),
})
@pytest.mark.parametrize(
    "method,username,permission,data,request_as,code,new_data_version,expected",
    change_permission_tests.values(),
    ids=list(change_permission_tests.keys()),
)
def test_change_permission(balrogadmin, method, username, permission, data, request_as, code, new_data_version, expected):
    ret = balrogadmin.open("/users/{}/permissions/{}".format(username, permission),
                           method=method, data=data, environ_base={"REMOTE_USER": request_as})
    assert ret.status_code == code, ret.data
    if 200 <= code < 300:
        assert ret.get_json() == {"new_data_version": new_data_version}, ret.data
        got = dbo.permissions.t.select()\
            .where(dbo.permissions.username == username)\
            .where(dbo.permissions.permission == permission)\
            .execute()\
            .fetchall()
        assert len(got) == 1
        assert got[0] == expected


delete_permission_tests = {
    "delete": (
        "bob",
        "release_read_only",
        {
            "data_version": 1,
        },
        "bill",
        200,
    ),
    "delete_non_existant": (
        "bill",
        "release",
        {
            "data_version": 1,
        },
        "bill",
        404,
    ),
    "delete_bad_input": (
        "bill",
        "admin",
        None,
        "bill",
        400,
    ),
    "delete_without_permission": (
        "bob",
        "permission",
        {
            "data_version": 1,
        },
        "ashanti",
        403,
    ),
    "delete_requires_signoff": (
        "bob",
        "release",
        {
            "data_version": 1,
        },
        "bill",
        400,
    ),
}
@pytest.mark.parametrize(
    "username,permission,query_string,request_as,code",
    delete_permission_tests.values(),
    ids=list(delete_permission_tests.keys()),
)
def test_delete_permission(balrogadmin, username, permission, query_string, request_as, code):
    ret = balrogadmin.delete("/users/{}/permissions/{}".format(username, permission),
                             query_string=query_string, environ_base={"REMOTE_USER": request_as})
    assert ret.status_code == code, ret.data
    got = dbo.permissions.t.select()\
        .where(dbo.permissions.username == username)\
        .where(dbo.permissions.permission == permission)\
        .execute()\
        .fetchall()
    if (200 <= code < 300) or code == 404:
        assert len(got) == 0
    else:
        assert len(got) == 1
