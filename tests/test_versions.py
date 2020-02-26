import pytest

import audmodel

from .default import default


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize(
    'name,params,expected_version',
    [
        (
            default.NAME,
            None,
            default.VERSION,
        ),
        (
            default.NAME,
            default.PARAMS[0],
            default.VERSION,
        ),
        (
            default.NAME,
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
