from collections import OrderedDict
import pytest


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
        "current",
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
        "current",
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
        "current",
        "vikas",
        200,
        {
            "username": "vikas",
            "permissions": {},
            "roles": {},
        },
    ),
    "named_user_not_as_admin": (
        "vikas",
        "vikas",
        404,
        None,
    ),
    "named_user_as_admin": (
        "mary",
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
        "mary",
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
        "bill",
        "mary",
        403,
        None,
    ),
    "non_existant_user": (
        "uhetonhueo",
        "bob",
        404,
        None,
    ),
})
@pytest.mark.parametrize(
    "username,request_as,code,expected",
    get_user_tests.values(),
    # In Python 3, OrderedDict.keys()' returns a data structure that
    # doesn't support indexing, which pytest requires
    ids=list(get_user_tests.keys()),
)
def test_get_user(balrogadmin, username, request_as, code, expected):
    ret = balrogadmin.get("/users/{}".format(username), environ_base={"REMOTE_USER": request_as})
    assert ret.status_code == code
    # No response body to test if the code wasn't 200
    if code == 200:
        assert ret.get_json() == expected
