import pytest

from auslib.errors import BadDataError
from auslib.util.versions import MozillaVersion


@pytest.mark.parametrize("test_version,version,prerelease,str_version", [
    ("3.6.3plugin1", (3, 6, 3), ("p", 1), "3.6.3p1"),
    ("1.5.0.12", (1, 5, 12), None, "1.5.12"),
    ("1.2.3a1", (1, 2, 3), ("a", 1), "1.2.3a1"),
    ("1.2.0", (1, 2, 0), None, "1.2"),
])
def test_version_parsing(test_version, version, prerelease, str_version):
    v = MozillaVersion(test_version)
    assert v.version == version
    assert v.prerelease == prerelease
    assert str(v) == str_version


# This test is lifted from upstream:
# https://hg.python.org/cpython/file/v2.7.3/Lib/distutils/tests/test_version.py#l18
@pytest.mark.parametrize("version1,version2,expected", [
    ('1.5.1', '1.5.2b2', -1),
    ('161', '3.10a', BadDataError),
    ('8.02', '8.02', 0),
    ('3.4j', '1996.07.12', BadDataError),
    ('3.2.pl0', '3.1.1.6', BadDataError),
    ('2g6', '11g', BadDataError),
    ('0.9', '2.2', -1),
    ('1.2.1', '1.2', 1),
    ('1.1', '1.2.2', -1),
    ('1.2', '1.1', 1),
    ('1.2.1', '1.2.2', -1),
    ('1.2.2', '1.2', 1),
    ('1.2', '1.2.2', -1),
    ('0.4.0', '0.4', 0),
    ('1.13++', '5.5.kw', BadDataError)
])
def test_cmp_strict(version1, version2, expected):
    def cmp(x, y):
        return (x > y) - (x < y)

    try:
        res = cmp(MozillaVersion(version1), MozillaVersion(version2))
        assert res == expected, "cmp({}, {}) should be {}, got {}".format(version1, version2, expected, res)
    except BadDataError:
        if expected is not BadDataError:
            assert False, "cmp({}, {}) shouldn't raise BadDataError".format(version1, version2)
