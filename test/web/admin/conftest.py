import os
from tempfile import mkstemp

import pytest

from auslib.global_state import dbo, cache
from auslib.web.admin.base import app
from auslib.blobs.base import createBlob


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
    dbo.setDb('sqlite:///:memory:')
    dbo.setDomainWhitelist({'good.com': ('a', 'b', 'c', 'd')})
    yield None
    os.close(version_fd)
    os.remove(version_file)


@pytest.fixture
def balrogadmin(balrogadmin_init, sampledata):
    cache.reset()
    dbo.create()
    with dbo.begin() as trans:
        for statement in sampledata:
            trans.execute(statement)
    return app.test_client()
