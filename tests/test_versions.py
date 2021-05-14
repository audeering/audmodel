import os
import shutil

import pytest

import audeer
import audmodel


audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT

MODEL_FILES = {
    '1.0.0': ['test', 'sub/test'],
    '2.0.0': ['other', 'sub/test'],
}
SUBGROUP = f'{pytest.ID}.versions'

MODEL_ID = audmodel.uid(pytest.NAME, pytest.PARAMS, subgroup=SUBGROUP)


def test_versions():

    with pytest.raises(RuntimeError):
        audmodel.versions(MODEL_ID)

    with pytest.raises(RuntimeError):
        audmodel.latest_version(MODEL_ID)

    versions = []
    for version in ['1.0.0', '2.0.0']:
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            version,
            subgroup=SUBGROUP,
        )
        assert audmodel.latest_version(MODEL_ID) == version
        versions.append(version)
        assert audmodel.versions(MODEL_ID) == versions
