import os

import pytest

import audbackend

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

SUBGROUP = f"{pytest.ID}.publish"


@pytest.mark.parametrize(
    "root, name, params, version, author, date, meta, subgroup, repository",
    (
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            SUBGROUP,
            None,
        ),
        # different name
        pytest.param(
            pytest.MODEL_ROOT,
            "other",
            pytest.PARAMS,
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
        ),
        # different subgroup
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            f"{SUBGROUP}.other",
            audmodel.config.REPOSITORIES[0],
        ),
        # different parameters
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            {},
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
        ),
        # new version
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "2.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["2.0.0"],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
        ),
        # new version in second repository
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "3.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["3.0.0"],
            SUBGROUP,
            audmodel.config.REPOSITORIES[1],
        ),
        # already published
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            SUBGROUP,
            audmodel.config.REPOSITORIES[1],
            marks=pytest.mark.xfail(raises=RuntimeError),
        ),
        # invalid root
        pytest.param(
            "./does-not-exist",
            pytest.NAME,
            pytest.PARAMS,
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            SUBGROUP,
            audmodel.config.REPOSITORIES[0],
            marks=pytest.mark.xfail(raises=FileNotFoundError),
        ),
        # invalid subgroup
        pytest.param(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "1.0.0",
            pytest.AUTHOR,
            pytest.DATE,
            pytest.META["1.0.0"],
            "_uid",
            audmodel.config.REPOSITORIES[0],
            marks=pytest.mark.xfail(raises=ValueError),
        ),
    ),
)
def test_publish(root, name, subgroup, params, author, date, meta, version, repository):
    uid = audmodel.publish(
        root,
        name,
        params,
        version,
        author=author,
        date=date,
        meta=meta,
        repository=repository,
        subgroup=subgroup,
    )

    assert audmodel.exists(uid)
    assert uid == audmodel.uid(
        name,
        params,
        version,
        subgroup=subgroup,
    )

    header = audmodel.header(uid)

    assert header["author"] == author
    assert audmodel.author(uid) == author

    assert header["date"] == date
    assert audmodel.date(uid) == str(date)

    assert header["name"] == name
    assert audmodel.name(uid) == name

    assert header["parameters"] == params
    assert audmodel.parameters(uid) == params

    assert header["subgroup"] == subgroup
    assert audmodel.subgroup(uid) == subgroup

    assert header["version"] == version
    assert audmodel.version(uid) == version

    assert audmodel.meta(uid) == meta

    assert os.path.exists(audmodel.url(uid))
    assert os.path.exists(audmodel.url(uid, type="header"))
    assert os.path.exists(audmodel.url(uid, type="meta"))


@pytest.mark.parametrize(
    "params, meta, repository, error, error_msg",
    [
        (
            {},
            {"object": pytest.CANNOT_PICKLE},
            pytest.REPOSITORIES[0],
            RuntimeError,
            r"Cannot serialize",
        ),
        (
            {"object": pytest.CANNOT_PICKLE},
            {},
            pytest.REPOSITORIES[0],
            RuntimeError,
            r"Cannot serialize",
        ),
        (
            {},
            {},
            audmodel.Repository("repo", "non-existing", "file-system"),
            audbackend.BackendError,
            (
                "An exception was raised by the backend, "
                "please see stack trace for further information."
            ),
        ),
    ],
)
def test_publish_error(params, meta, repository, error, error_msg):
    r"""Tests for errors during publication.

    This tests for the errors,
    that ``audb.publish()``
    might raise during publication.

    Args:
        params: model parameter
        meta: model metadata
        repository: repository to publish the model to
        error: expected error
        error_msg: expected (part of the) error message

    """
    name = pytest.NAME
    version = "1.0.0"
    with pytest.raises(error, match=error_msg):
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            meta=meta,
            repository=repository,
        )
    uid = audmodel.uid(
        name,
        params,
        version,
    )
    assert not audmodel.exists(uid)
