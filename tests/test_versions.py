import pytest

import audmodel

from .config import config


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,params,expected_version',
    [
        (
            config.NAME,
            None,
            config.DEFAULT_VERSION,
        ),
        (
            config.NAME,
            config.DEFAULT_PARAMS[0],
            config.DEFAULT_VERSION,
        ),
        (
            config.NAME,
            {'bad': 'params'},
            None,
        ),
    ]
)
def test_versions(name, params, expected_version):
    versions = audmodel.versions(name, params)
    latest = audmodel.latest_version(name, params)
    if len(versions) > 0:
        assert latest in versions
    assert expected_version == latest
