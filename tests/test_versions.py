import pytest

import audmodel


audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT

SUBGROUP = f'{pytest.ID}.versions'


def test_versions():

    with pytest.raises(RuntimeError):
        audmodel.latest_version(
            pytest.NAME,
            pytest.PARAMS,
            subgroup=SUBGROUP,
        )
    assert not audmodel.versions(
        pytest.NAME,
        pytest.PARAMS,
        subgroup=SUBGROUP
    )

    versions = []
    for version in ['1.0.0', '2.0.0']:
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            version,
            subgroup=SUBGROUP,
        )
        assert audmodel.latest_version(
            pytest.NAME,
            pytest.PARAMS,
            subgroup=SUBGROUP,
        ) == version
        versions.append(version)
        assert audmodel.versions(
            pytest.NAME,
            pytest.PARAMS,
            subgroup=SUBGROUP
        ) == versions
