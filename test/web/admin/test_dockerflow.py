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
