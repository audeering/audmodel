import os
import shutil

import pytest

import audeer

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

MODEL_FILES = ["test", "sub/test"]
VERSION = "1.0.0"
SUBGROUP = f"{pytest.ID}.legacy"


def clear_root(root: str):
    root = audeer.safe_path(root)
    if os.path.exists(root):
        shutil.rmtree(root)
    audeer.mkdir(root)


@pytest.fixture(
    scope="module",
    autouse=True,
)
def fixture_publish_model():
    clear_root(pytest.MODEL_ROOT)

    for file in MODEL_FILES:
        path = os.path.join(pytest.MODEL_ROOT, file)
        audeer.mkdir(os.path.dirname(path))
        with open(path, "w"):
            pass

    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        VERSION,
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META[VERSION],
        repository=pytest.REPOSITORIES[0],
        subgroup=SUBGROUP,
    )

    # Rename files to contain legacy UID
    old_uid = uid.split("-")[0]
    new_uid = audmodel.legacy_uid(
        pytest.NAME,
        pytest.PARAMS,
        VERSION,
        subgroup=SUBGROUP,
    )

    path = os.path.join(
        pytest.HOST,
        pytest.REPOSITORIES[0].name,
        audmodel.core.define.UID_FOLDER,
    )
    src = os.path.join(path, old_uid)
    dst = os.path.join(path, new_uid)
    os.rename(src, dst)

    path = os.path.join(
        path,
        new_uid,
        VERSION,
    )
    for ext in [
        audmodel.core.define.HEADER_EXT,
        audmodel.core.define.META_EXT,
    ]:
        src = os.path.join(path, f"{old_uid}-{VERSION}.{ext}")
        dst = os.path.join(path, f"{new_uid}-{VERSION}.{ext}")
        os.rename(src, dst)

    path = os.path.join(
        pytest.HOST,
        pytest.REPOSITORIES[0].name,
        *SUBGROUP.split("."),
        pytest.NAME,
    )
    src = os.path.join(path, old_uid)
    dst = os.path.join(path, new_uid)
    os.rename(src, dst)

    path = os.path.join(path, new_uid, VERSION)
    src = os.path.join(path, f"{old_uid}-{VERSION}.zip")
    dst = os.path.join(path, f"{new_uid}-{VERSION}.zip")
    os.rename(src, dst)

    yield

    clear_root(pytest.MODEL_ROOT)


@pytest.mark.parametrize(
    "name, params, subgroup, version",
    (
        (pytest.NAME, pytest.PARAMS, SUBGROUP, "1.0.0"),
        pytest.param(
            pytest.NAME,
            pytest.PARAMS,
            SUBGROUP,
            "3.0.0",
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ),
)
def test_load(name, params, subgroup, version):
    uid = audmodel.legacy_uid(
        pytest.NAME,
        pytest.PARAMS,
        version,
        subgroup=SUBGROUP,
    )
    # Load from backend
    audmodel.load(uid)
    # Load from cache
    audmodel.load(uid)
    assert audmodel.versions(uid) == [version]
