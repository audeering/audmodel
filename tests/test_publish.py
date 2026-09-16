import os
import platform
import signal
import zipfile

import pytest

import audbackend
import audeer

import audmodel
from audmodel.core import api


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
            audmodel.config.REPOSITORIES[0],
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


def test_publish_tmp_root(tmp_path):
    r"""Test publishing with a custom ``tmp_root`` folder.

    The archive should be staged inside ``tmp_root``
    and the folder should be created
    if it does not exist yet.

    """
    tmp_root = os.path.join(tmp_path, "does", "not", "exist")
    assert not os.path.exists(tmp_root)

    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        {"tmp_root": "custom"},
        "1.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        subgroup=f"{SUBGROUP}.tmp_root",
        tmp_root=tmp_root,
        repository=pytest.REPOSITORIES[0],
    )

    assert audmodel.exists(uid)
    # ``tmp_root`` is created on demand,
    # and ``TemporaryDirectory`` cleans up its content,
    # but the folder we created stays around
    assert os.path.isdir(tmp_root)
    assert audeer.list_file_names(tmp_root) == []


def test_publish_missing_repository_raises():
    """Test error message if repository is None."""
    error_msg = (
        "You have to provide a repository, "
        "see audmodel.config.REPOSITORIES for an example."
    )
    with pytest.raises(ValueError, match=error_msg):
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            {},
            "1.0.0",
            repository=None,
        )


@pytest.mark.parametrize(
    "compression, expected_compress_type",
    [
        # deflate level 1 by default
        (None, zipfile.ZIP_DEFLATED),
        (0, zipfile.ZIP_STORED),
        (1, zipfile.ZIP_DEFLATED),
        (9, zipfile.ZIP_DEFLATED),
    ],
)
def test_publish_compression(tmp_path, compression, expected_compress_type):
    r"""Test compression of the published model archive.

    Args:
        tmp_path: tmp_path fixture
        compression: compression level,
            ``None`` publishes without the argument
        expected_compress_type: expected compression method
            of the entries in the model archive

    """
    root = audeer.mkdir(tmp_path, "model")
    with open(os.path.join(root, "model.bin"), "w") as file:
        file.write("a" * 10000)

    kwargs = {} if compression is None else {"compression": compression}
    effective_compression = 1 if compression is None else compression
    uid = audmodel.publish(
        root,
        pytest.NAME,
        {"compression": effective_compression, "compression_arg": compression},
        "1.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        subgroup=f"{SUBGROUP}.compression",
        repository=pytest.REPOSITORIES[0],
        **kwargs,
    )

    with zipfile.ZipFile(audmodel.url(uid)) as archive:
        infos = archive.infolist()
    assert [info.filename for info in infos] == ["model.bin"]
    assert infos[0].compress_type == expected_compress_type


@pytest.mark.parametrize("compression", [-1, 10])
def test_publish_compression_error(compression):
    r"""Test error for a compression level outside 0-9.

    Args:
        compression: invalid compression level

    """
    error_msg = f"'compression' has to be between 0 and 9, not {compression}."
    with pytest.raises(ValueError, match=error_msg):
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            {},
            "1.0.0",
            compression=compression,
            repository=pytest.REPOSITORIES[0],
        )


def assert_nothing_published(uid, alias):
    r"""Assert no file of a model is stored in a repository.

    Args:
        uid: unique model ID
        alias: alias of the model

    """
    assert not audmodel.exists(uid)
    assert not audmodel.exists(alias)
    short_id = uid.split("-")[0]
    for repository in pytest.REPOSITORIES:
        files = audeer.list_file_names(
            audeer.path(repository.host, repository.name),
            recursive=True,
        )
        files = [os.path.basename(file) for file in files]
        assert not [file for file in files if short_id in file or alias in file]


@pytest.mark.parametrize(
    "interrupted_function",
    ["put_header", "put_meta", "put_archive", "put_alias", "put_aliases"],
)
def test_publish_interrupted(monkeypatch, interrupted_function):
    r"""Test publication interrupted by the user.

    If publication is interrupted,
    all files that have been published so far
    have to be removed from the backend again.
    Otherwise a model would be registered,
    that cannot be loaded.

    Args:
        monkeypatch: monkeypatch fixture
        interrupted_function: name of the function
            during which publication is interrupted

    """

    def interrupt(*args, **kwargs):
        r"""Interrupt publication."""
        raise KeyboardInterrupt()

    monkeypatch.setattr(api, interrupted_function, interrupt)

    name = pytest.NAME
    params = {"interrupted": interrupted_function}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.interrupted"
    alias = f"alias-{interrupted_function}"

    with pytest.raises(KeyboardInterrupt):
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            alias=alias,
            subgroup=subgroup,
            repository=pytest.REPOSITORIES[0],
        )

    uid = audmodel.uid(name, params, version, subgroup=subgroup)
    assert_nothing_published(uid, alias)


def test_publish_archive_error(monkeypatch):
    r"""Test error during creation of the model archive.

    An error during archive creation
    has to be raised as ``RuntimeError``,
    like any other unexpected error during publication.

    Args:
        monkeypatch: monkeypatch fixture

    """

    def raise_error(*args, **kwargs):
        r"""Fail to create the model archive."""
        raise PermissionError()

    monkeypatch.setattr(api, "create_archive", raise_error)

    name = pytest.NAME
    params = {"interrupted": "archive"}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.interrupted"
    alias = "alias-archive"

    error_msg = "Could not publish model due to an unexpected error."
    with pytest.raises(RuntimeError, match=error_msg):
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            alias=alias,
            subgroup=subgroup,
            repository=pytest.REPOSITORIES[0],
        )

    uid = audmodel.uid(name, params, version, subgroup=subgroup)
    assert_nothing_published(uid, alias)


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="SIGTERM cannot be delivered to a running process under Windows",
)
def test_publish_sigterm(monkeypatch):
    r"""Test publication interrupted by SIGTERM.

    SIGTERM does not raise an error by default,
    but terminates the process,
    which would leave a registered model
    that cannot be loaded.

    Args:
        monkeypatch: monkeypatch fixture

    """

    def send_sigterm(*args, **kwargs):
        r"""Send SIGTERM to the running process."""
        os.kill(os.getpid(), signal.SIGTERM)

    monkeypatch.setattr(api, "put_archive", send_sigterm)

    name = pytest.NAME
    params = {"interrupted": "sigterm"}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.interrupted"
    alias = "alias-sigterm"

    with pytest.raises(KeyboardInterrupt):
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            alias=alias,
            subgroup=subgroup,
            repository=pytest.REPOSITORIES[0],
        )

    uid = audmodel.uid(name, params, version, subgroup=subgroup)
    assert_nothing_published(uid, alias)


def test_publish_after_interruption(monkeypatch):
    r"""Test publication of a model that was interrupted before.

    An interrupted publication
    must not block publishing the same model again.

    Args:
        monkeypatch: monkeypatch fixture

    """

    def interrupt(*args, **kwargs):
        r"""Interrupt publication."""
        raise KeyboardInterrupt()

    name = pytest.NAME
    params = {"interrupted": "before"}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.interrupted"

    with monkeypatch.context() as patch:
        patch.setattr(api, "put_archive", interrupt)
        with pytest.raises(KeyboardInterrupt):
            audmodel.publish(
                pytest.MODEL_ROOT,
                name,
                params,
                version,
                subgroup=subgroup,
                repository=pytest.REPOSITORIES[0],
            )

    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        name,
        params,
        version,
        subgroup=subgroup,
        repository=pytest.REPOSITORIES[0],
    )

    assert audmodel.exists(uid)
    assert os.path.exists(audmodel.load(uid))


def test_publish_order(monkeypatch):
    r"""Test order in which files are published.

    The header registers the model,
    so it has to be published last.
    Otherwise,
    a publication that is aborted
    without removing the published files,
    e.g. due to a lost connection,
    would leave a registered model
    that cannot be loaded.

    Args:
        monkeypatch: monkeypatch fixture

    """
    functions = ["put_archive", "put_meta", "put_aliases", "put_alias", "put_header"]
    called = []

    def record(function):
        r"""Wrap function to record its call."""
        original = getattr(api, function)

        def wrapper(*args, **kwargs):
            called.append(function)
            return original(*args, **kwargs)

        return wrapper

    for function in functions:
        monkeypatch.setattr(api, function, record(function))

    name = pytest.NAME
    params = {"order": "header-last"}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.order"

    audmodel.publish(
        pytest.MODEL_ROOT,
        name,
        params,
        version,
        alias="alias-order",
        subgroup=subgroup,
        repository=pytest.REPOSITORIES[0],
    )

    assert called == functions


def test_publish_concurrent(monkeypatch):
    r"""Test publication of the same model by another process.

    As the header is published last,
    another process might publish the same model
    while the archive is uploaded.
    In this case,
    an error has to be raised
    without publishing our header,
    and without removing the files of the other publication.

    Args:
        monkeypatch: monkeypatch fixture

    """
    name = pytest.NAME
    params = {"concurrent": True}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.concurrent"
    uid = audmodel.uid(name, params, version, subgroup=subgroup)
    other_author = "other-process"

    original_put_meta = api.put_meta

    def put_meta_and_publish_concurrently(
        short_id,
        version,
        meta,
        backend_interface,
        verbose,
    ):
        r"""Publish header of another process after publishing meta."""
        path = original_put_meta(short_id, version, meta, backend_interface, verbose)
        header = audmodel.core.utils.create_header(
            uid,
            author=other_author,
            date=None,
            name=name,
            parameters=params,
            subgroup=subgroup,
            version=version,
        )
        api.put_header(short_id, version, header, backend_interface, verbose)
        return path

    monkeypatch.setattr(api, "put_meta", put_meta_and_publish_concurrently)

    error_msg = (
        f"A model with ID '{uid}' "
        "was published by another process in the meantime. "
        "Its archive, metadata, or alias files "
        "might have been replaced by the ones of this process."
    )
    with pytest.raises(RuntimeError, match=error_msg):
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            author="this-process",
            subgroup=subgroup,
            repository=pytest.REPOSITORIES[0],
        )

    # Model of other process is untouched and can be loaded
    assert audmodel.exists(uid)
    assert audmodel.author(uid) == other_author
    assert os.path.exists(audmodel.load(uid))


def test_publish_dangling_alias(monkeypatch):
    r"""Test alias left behind by an aborted publication.

    The alias is published before the header.
    If publication is aborted afterwards,
    and the published files cannot be removed,
    e.g. due to a lost connection,
    an alias pointing to an unregistered model is left behind.
    Such an alias must not report the model as existing,
    and must not block publishing the model again.

    Args:
        monkeypatch: monkeypatch fixture

    """

    def raise_error(*args, **kwargs):
        r"""Fail to publish header."""
        raise audbackend.BackendError(ConnectionError())

    def do_not_remove(*args, **kwargs):
        r"""Fail to remove files during cleanup."""

    name = pytest.NAME
    params = {"dangling": "alias"}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.dangling"
    alias = "alias-dangling"
    uid = audmodel.uid(name, params, version, subgroup=subgroup)

    with monkeypatch.context() as patch:
        patch.setattr(api, "put_header", raise_error)
        patch.setattr(audbackend.interface.Maven, "remove_file", do_not_remove)
        error_msg = "Could not publish model due to an unexpected error."
        with pytest.raises(RuntimeError, match=error_msg):
            audmodel.publish(
                pytest.MODEL_ROOT,
                name,
                params,
                version,
                alias=alias,
                subgroup=subgroup,
                repository=pytest.REPOSITORIES[0],
            )

    # Archive, meta, and alias are left behind,
    # but the header is missing
    repository = pytest.REPOSITORIES[0]
    files = audeer.list_file_names(
        audeer.path(repository.host, repository.name),
        recursive=True,
    )
    files = [os.path.basename(file) for file in files]
    short_id = uid.split("-")[0]
    assert f"{short_id}-{version}.zip" in files
    assert f"{short_id}-{version}.{audmodel.core.define.META_EXT}" in files
    assert f"{alias}-1.0.0.{audmodel.core.define.ALIAS_EXT}" in files
    assert f"{short_id}-{version}.{audmodel.core.define.HEADER_EXT}" not in files

    # Alias points to unregistered model
    assert audmodel.resolve_alias(alias) == uid
    assert not audmodel.exists(uid)
    assert not audmodel.exists(alias)
    with pytest.raises(RuntimeError, match=f"A model with ID '{uid}' does not exist."):
        audmodel.load(alias)

    # Publishing the model again repairs the alias
    assert (
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            alias=alias,
            subgroup=subgroup,
            repository=repository,
        )
        == uid
    )
    assert audmodel.exists(alias)
    assert audmodel.resolve_alias(alias) == uid
    assert audmodel.aliases(uid) == [alias]
    assert os.path.exists(audmodel.load(alias))


@pytest.mark.parametrize("replaced_file", ["archive", "meta", "aliases", "alias"])
def test_publish_concurrent_replaced_file(monkeypatch, tmp_path, replaced_file):
    r"""Test files replaced by another process before publishing the header.

    Another process publishing the same model
    might replace files after we uploaded them,
    but before we publish the header.
    As our header registers the model,
    the replaced files have to be uploaded again,
    and a warning has to be shown.

    Args:
        monkeypatch: monkeypatch fixture
        tmp_path: tmp_path fixture
        replaced_file: file replaced by the other process

    """
    name = pytest.NAME
    params = {"replaced": replaced_file}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.replaced"
    alias = f"alias-replaced-{replaced_file}"
    meta = {"replaced": replaced_file}
    uid = audmodel.uid(name, params, version, subgroup=subgroup)
    short_id = uid.split("-")[0]
    repository = pytest.REPOSITORIES[0]
    backend_interface = repository.create_backend_interface()
    define = audmodel.core.define

    paths = {
        "archive": (
            backend_interface.join("/", *subgroup.split("."), name, f"{short_id}.zip"),
            version,
        ),
        "meta": (
            backend_interface.join(
                "/", define.UID_FOLDER, f"{short_id}.{define.META_EXT}"
            ),
            version,
        ),
        "aliases": (
            backend_interface.join(
                "/", define.UID_FOLDER, f"{short_id}.{define.ALIASES_EXT}"
            ),
            version,
        ),
        "alias": (
            backend_interface.join(
                "/", define.ALIAS_FOLDER, f"{alias}.{define.ALIAS_EXT}"
            ),
            "1.0.0",
        ),
    }
    path, file_version = paths[replaced_file]
    other_file = audeer.touch(tmp_path, "other")
    with open(other_file, "w") as fp:
        fp.write("file of other process")
    other_checksum = audeer.md5(other_file)

    original_exists = api.exists
    calls = []

    def exists_and_replace_file(uid):
        r"""Replace file after the check performed before publishing header."""
        result = original_exists(uid)
        calls.append(uid)
        if len(calls) == 2:
            with backend_interface.backend:
                backend_interface.put_file(other_file, path, file_version)
        return result

    monkeypatch.setattr(api, "exists", exists_and_replace_file)

    warning_msg = (
        f"Another process published a model with ID '{uid}' at the same time, "
        f"and replaced the following files after they were uploaded: '{path}'. "
        "The files are now uploaded again, "
        "so the published model contains the correct files."
    )
    with pytest.warns(UserWarning, match=warning_msg):
        assert (
            audmodel.publish(
                pytest.MODEL_ROOT,
                name,
                params,
                version,
                alias=alias,
                meta=meta,
                subgroup=subgroup,
                repository=repository,
            )
            == uid
        )

    # Replaced file was uploaded again
    with backend_interface.backend:
        assert backend_interface.checksum(path, file_version) != other_checksum

    # Published model contains the files of this process
    assert audmodel.exists(uid)
    assert audmodel.meta(uid) == meta
    assert audmodel.aliases(uid) == [alias]
    assert audmodel.resolve_alias(alias) == uid
    model_root = audmodel.load(uid)
    assert audeer.list_file_names(
        model_root, recursive=True, basenames=True
    ) == audeer.list_file_names(pytest.MODEL_ROOT, recursive=True, basenames=True)


def test_publish_concurrent_replaced_header(monkeypatch):
    r"""Test header replaced by another process.

    Two processes publishing the same model
    might both pass the check before publishing the header,
    and both publish their header.
    The process whose header was replaced
    must raise an error,
    and must not replace the files of the other process,
    as its header registers the model.

    Args:
        monkeypatch: monkeypatch fixture

    """
    name = pytest.NAME
    params = {"replaced": "header"}
    version = "1.0.0"
    subgroup = f"{SUBGROUP}.replaced"
    alias = "alias-replaced-header"
    uid = audmodel.uid(name, params, version, subgroup=subgroup)
    other_author = "other-process"
    other_meta = {"author": other_author}

    original_put_header = api.put_header

    def put_header_and_replace_files(
        short_id,
        version,
        header,
        backend_interface,
        verbose,
    ):
        r"""Replace header and meta by the ones of another process."""
        result = original_put_header(
            short_id,
            version,
            header,
            backend_interface,
            verbose,
        )
        other_header = audmodel.core.utils.create_header(
            uid,
            author=other_author,
            date=None,
            name=name,
            parameters=params,
            subgroup=subgroup,
            version=version,
        )
        original_put_header(
            short_id,
            version,
            other_header,
            backend_interface,
            verbose,
        )
        api.put_meta(short_id, version, other_meta, backend_interface, verbose)
        return result

    monkeypatch.setattr(api, "put_header", put_header_and_replace_files)

    error_msg = f"A model with ID '{uid}' was published by another process"
    with pytest.raises(RuntimeError, match=error_msg):
        audmodel.publish(
            pytest.MODEL_ROOT,
            name,
            params,
            version,
            alias=alias,
            author="this-process",
            meta={"author": "this-process"},
            subgroup=subgroup,
            repository=pytest.REPOSITORIES[0],
        )

    # Files of other process are untouched
    assert audmodel.exists(uid)
    assert audmodel.author(uid) == other_author
    assert audmodel.meta(uid) == other_meta
    assert os.path.exists(audmodel.load(uid))
