import os
import shutil
import time

import pytest

import audbackend
import audeer

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

MODEL_FILES = {
    "1.0.0": ["test", os.path.join("sub", "test")],
    "2.0.0": ["other", os.path.join("sub", "test")],
}
SUBGROUP = f"{pytest.ID}.load"


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
    for version, files in MODEL_FILES.items():
        clear_root(pytest.MODEL_ROOT)

        for file in files:
            path = os.path.join(pytest.MODEL_ROOT, file)
            audeer.mkdir(os.path.dirname(path))
            with open(path, "w"):
                pass

        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            version,
            author=pytest.AUTHOR,
            date=pytest.DATE,
            meta=pytest.META[version],
            repository=pytest.REPOSITORIES[0],
            subgroup=SUBGROUP,
        )

    yield

    clear_root(pytest.MODEL_ROOT)


@pytest.mark.parametrize(
    "function",
    [
        audmodel.author,
        audmodel.date,
        audmodel.exists,
        audmodel.header,
        audmodel.latest_version,
        audmodel.load,
        audmodel.meta,
        audmodel.name,
        audmodel.parameters,
        audmodel.subgroup,
        lambda uid: audmodel.update_meta(uid, {}),
        audmodel.url,
        audmodel.version,
        audmodel.versions,
    ],
)
def test_bad_repository(non_existing_repository, function):
    """Test for non existing repository.

    If no connection can be established to the backend,
    an ``audbackend.BackendError``
    should be raised.

    """
    uid = audmodel.uid(
        pytest.NAME,
        pytest.PARAMS,
        "1.0.0",
        subgroup=SUBGROUP,
    )
    error = audbackend.BackendError
    error_msg = (
        "An exception was raised by the backend, "
        "please see stack trace for further information."
    )
    with pytest.raises(error, match=error_msg):
        function(uid)


@pytest.mark.parametrize(
    "uid,expected_error",
    [
        (
            "bad-id",  # bad ID with version string
            "A model with ID 'bad-id' does not exist.",
        ),
        (
            "000",  # bad ID without version string
            "A model with ID '000' does not exist.",
        ),
        (
            "00000000",
            "A model with ID '00000000' does not exist.",
        ),
        (
            "00000000-0000-0000-0000-000000000000",
            ("A model with ID '00000000-0000-0000-0000-000000000000' does not exist."),
        ),
    ],
)
def test_bad_uid(uid, expected_error):
    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.author(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.date(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.header(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.latest_version(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.meta(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.name(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.parameters(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.subgroup(uid)

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.update_meta(uid, {})

    with pytest.raises(RuntimeError, match=expected_error):
        audmodel.version(uid)

    assert not audmodel.versions(uid)
    assert not audmodel.exists(uid)


@pytest.mark.parametrize(
    "name, params, subgroup, version",
    (
        (pytest.NAME, pytest.PARAMS, SUBGROUP, "1.0.0"),
        (pytest.NAME, pytest.PARAMS, SUBGROUP, "2.0.0"),
        (pytest.NAME, pytest.PARAMS, SUBGROUP, None),
        pytest.param(  # version does not exist
            pytest.NAME,
            pytest.PARAMS,
            SUBGROUP,
            "3.0.0",
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        pytest.param(  # short ID does not exist
            "does-not-exist",
            pytest.PARAMS,
            SUBGROUP,
            None,
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
    ),
)
def test_load(name, params, subgroup, version):
    uid = audmodel.uid(name, params, version, subgroup=subgroup)

    # ensure it also works if we have already an existing EMPTY model folder

    if version == "1.0.0":
        root = audeer.mkdir(os.path.join(audmodel.config.CACHE_ROOT, *uid.split("-")))

    # load from backend

    root = audmodel.load(uid)
    if version is None:
        version = audmodel.latest_version(uid)
    header = os.path.join(
        os.path.dirname(root), f"{version}.{audmodel.core.define.HEADER_EXT}"
    )
    files = audmodel.core.utils.scan_files(root)
    paths = [os.path.join(root, file) for file in files]

    assert sorted(MODEL_FILES[version]) == sorted(files)

    # store modification times

    mtimes = {path: os.path.getmtime(path) for path in paths}
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


@pytest.mark.parametrize(
    "name, params, version, subgroup, expected",
    [
        (
            "name",
            {},
            None,
            None,
            audeer.uid(from_string=".name" + str({}))[-8:],
        ),
        (
            "name",
            {},
            None,
            "",
            audeer.uid(from_string=".name" + str({}))[-8:],
        ),
        (
            "name",
            {},
            None,
            "subgroup",
            audeer.uid(from_string="subgroup.name" + str({}))[-8:],
        ),
        (
            "name",
            {"a": 1},
            "1.0.0",
            None,
            (audeer.uid(from_string=".name" + str({"a": 1}))[-8:] + "-1.0.0"),
        ),
    ],
)
def test_uid(name, params, version, subgroup, expected):
    uid = audmodel.uid(
        name,
        params,
        version=version,
        subgroup=subgroup,
    )
    assert uid == expected


def test_update_meta():
    uid = audmodel.uid(
        pytest.NAME,
        pytest.PARAMS,
        "1.0.0",
        subgroup=SUBGROUP,
    )
    meta = {"model": pytest.CANNOT_PICKLE}
    with pytest.raises(RuntimeError, match=r"Cannot serialize"):
        audmodel.update_meta(uid, meta)
    meta = {"cnn10": {"layers": 10}}
    original_meta = audmodel.meta(uid)
    expected_meta = audmodel.meta(uid)
    audmodel.core.utils.update_dict(expected_meta, meta)
    new_meta = audmodel.update_meta(uid, meta)
    assert new_meta == expected_meta
    new_meta = audmodel.update_meta(uid, original_meta, replace=True)
    assert new_meta == original_meta


def test_url():
    with pytest.raises(ValueError):
        uid = audmodel.uid(
            pytest.NAME,
            pytest.PARAMS,
            "1.0.0",
            subgroup=SUBGROUP,
        )
        audmodel.url(uid, type="something")
