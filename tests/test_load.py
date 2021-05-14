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
SUBGROUP = f'{pytest.ID}.load'

MODEL_ID = audmodel.uid(pytest.NAME, pytest.PARAMS, subgroup=SUBGROUP)


def clear_root(root: str):
    root = audeer.safe_path(root)
    if os.path.exists(root):
        shutil.rmtree(root)
    audeer.mkdir(root)


@pytest.fixture(
    scope='module',
    autouse=True,
)
def fixture_publish_model():

    for version, files in MODEL_FILES.items():

        clear_root(pytest.MODEL_ROOT)

        for file in files:
            path = os.path.join(pytest.MODEL_ROOT, file)
            audeer.mkdir(os.path.dirname(path))
            with open(path, 'w'):
                pass

        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            version,
            subgroup=SUBGROUP,
        )

    yield

    clear_root(pytest.MODEL_ROOT)


@pytest.mark.parametrize(
    'uid, version',
    (
        (MODEL_ID, '1.0.0'),
        (MODEL_ID, '2.0.0'),
        (MODEL_ID, None),
        pytest.param(
            MODEL_ID, '3.0.0',
            marks=pytest.mark.xfail(raises=RuntimeError),
        )
    ),
)
def test_load(uid, version):

    root = audmodel.load(uid, version=version)

    if version is None:
        version = audmodel.latest_version(uid)

    files = audmodel.core.api.scan_files(root)
    assert sorted(MODEL_FILES[version]) == sorted(files)
