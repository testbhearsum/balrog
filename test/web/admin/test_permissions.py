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


@pytest.mark.parametrize("username,request_as,code,expected", [
    (
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
    (
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
    (
        "current",
        "vikas",
        200,
        {
            "username": "vikas",
            "permissions": {},
            "roles": {},
        },
    ),
])
def test_get_user(balrogadmin, username, request_as, code, expected):
    ret = balrogadmin.get("/users/{}".format(username), environ_base={"REMOTE_USER": request_as})
    assert ret.status_code == code
    assert ret.get_json() == expected
