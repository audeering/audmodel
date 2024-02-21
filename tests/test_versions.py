import pytest

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

SUBGROUP = f"{pytest.ID}.versions"


def test_versions():
    sid = audmodel.uid(
        pytest.NAME,
        pytest.PARAMS,
        subgroup=SUBGROUP,
    )

    with pytest.raises(RuntimeError):
        audmodel.latest_version(sid)
    assert not audmodel.versions(sid)

    versions = []
    for version in ["1.0.0", "2.0.0"]:
        uid = audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            version,
            repository=pytest.REPOSITORIES[0],
            subgroup=SUBGROUP,
        )
        assert audmodel.latest_version(sid) == version
        assert audmodel.latest_version(uid) == version
        versions.append(version)
        assert audmodel.versions(sid) == versions
        assert audmodel.versions(uid) == versions
