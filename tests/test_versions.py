import pytest

import audmodel


@pytest.mark.usefixtures('create')
@pytest.mark.parametrize('name,params,expected_version', [
    (
        pytest.NAME,
        None,
        pytest.VERSION,
    ),
    (
        pytest.NAME,
        pytest.PARAMS[0],
        pytest.VERSION,
    ),
    (
        pytest.NAME,
        {'bad': 'params'},
        None,
    ),
])
def test_versions(name, params, expected_version):
    versions = audmodel.versions(name, params, subgroup=pytest.SUBGROUP)
    latest = audmodel.latest_version(name, params, subgroup=pytest.SUBGROUP)
    if len(versions) > 0:
        assert latest in versions
    assert expected_version == latest
