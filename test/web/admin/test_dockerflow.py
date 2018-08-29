def test_version(balrogadmin):
    ret = balrogadmin.get("/__version__")
    expected = """
{
  "source":"https://github.com/mozilla/balrog",
  "version":"1.0",
  "commit":"abcdef123456"
}
"""
    assert ret.get_data(as_text=True) == expected

def testHeartbeat(mocker, balrogadmin):
    cr = mocker.patch("auslib.global_state.dbo.dockerflow.incrementWatchdogValue")
    cr.side_effect = (1, 2, 3)
    for i in range(1, 3):
        ret = balrogadmin.get("/__heartbeat__")
        assert ret.status_code == 200
        assert cr.call_count == i
        assert ret.headers["Cache-Control"] == "public, max-age=60"
        assert int(ret.get_data(as_text=True)) == i

def testHeartbeatWithException(mocker, balrogadmin):
    cr = mocker.patch("auslib.global_state.dbo.dockerflow.incrementWatchdogValue")
    cr.side_effect = Exception("kabom!")
    # Because there's no web server between us and the endpoint, we receive
    # the Exception directly instead of a 500 error
    ret = balrogadmin.get("/__heartbeat__")
    assert ret.status_code == 502
    assert cr.call_count == 1
    assert ret.get_data(as_text=True) == "Can't connect to the database."
    assert ret.headers["Cache-Control"] == "public, max-age=60"

def testLbHeartbeat(mocker, balrogadmin):
    ret = balrogadmin.get("/__lbheartbeat__")
    assert ret.status_code == 200
    assert ret.headers["Cache-Control"] == "no-cache"
