import os
import shutil
import time

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
            author=pytest.AUTHOR,
            date=pytest.DATE,
            meta=pytest.META[version],
            subgroup=SUBGROUP,
        )

    yield

    clear_root(pytest.MODEL_ROOT)


@pytest.mark.parametrize(
    'name, params, subgroup, version',
    (
        (pytest.NAME, pytest.PARAMS, SUBGROUP, '1.0.0'),
        (pytest.NAME, pytest.PARAMS, SUBGROUP, '2.0.0'),
        pytest.param(
            pytest.NAME, pytest.PARAMS, SUBGROUP, '3.0.0',
            marks=pytest.mark.xfail(raises=RuntimeError),
        )
    ),
)
def test_load(name, params, subgroup, version):

    uid = audmodel.uid(name, params, version, subgroup=subgroup)

    # load from backend

    root = audmodel.load(uid)
    header = root + '.yaml'
    files = audmodel.core.utils.scan_files(root)
    paths = [os.path.join(root, file) for file in files]

    assert sorted(MODEL_FILES[version]) == sorted(files)

    # store modification times

    mtimes = {
        path: os.path.getmtime(path) for path in paths
    }
    mtimes[header] = os.path.getmtime(header)

    # load again from cache and assert modification times have not changed

    audmodel.load(uid)
    for path, mtime in mtimes.items():
        assert os.path.getmtime(path) == mtime

    # load again from backend and assert modification times have changed

    time.sleep(0.1)  # sleep to get a new modification time
    shutil.rmtree(root)
    os.remove(header)
    audmodel.load(uid)
    for path, mtime in mtimes.items():
        assert os.path.getmtime(path) != mtime
