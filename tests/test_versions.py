import pytest

import audmodel

from .config import config


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name',
    [
        config.NAME,
    ]
)
def test_load(name):
    versions = audmodel.versions(name)
    print(versions)
    latest = audmodel.latest_version(name)
    print(latest)
    assert latest in versions
    assert config.DEFAULT_VERSION == latest
