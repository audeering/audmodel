import os
import shutil
import tempfile
import typing
import oyaml as yaml

import audbackend
import audeer

from audmodel.core.config import config
import audmodel.core.define as define
import audmodel.core.utils as utils


SERIALIZE_ERROR_MESSAGE = (
    'Cannot serialize the following object to a YAML file:\n'
)


def archive_path(
        short_id: str,
        version: str,
        cache_root: str,
) -> typing.Tuple[audbackend.Backend, str]:
    r"""Return backend, archive path and version."""

    backend, header = get_header(short_id, version, cache_root)
    name = header['name']
    subgroup = header['subgroup'].split('.')
    path = backend.join(*subgroup, name, short_id + '.zip')

    return backend, path


def get_archive(
        short_id: str,
        version: str,
        cache_root: str,
        verbose: bool,
) -> str:
    r"""Return backend and local archive path."""

    root = os.path.join(
        cache_root,
        short_id,
        version,
    )

    if not os.path.exists(root):

        tmp_root = audeer.mkdir(root + '~')
        backend, path = archive_path(short_id, version, cache_root)

        # get archive
        src_path = path
        dst_path = os.path.join(tmp_root, 'model.zip')
        backend.get_file(
            src_path,
            dst_path,
            version,
        )

        # extract files
        audeer.extract_archive(
            dst_path,
            tmp_root,
            keep_archive=False,
            verbose=verbose,
        )

        # move folder
        audeer.mkdir(root)
        os.rename(tmp_root, root)

    return root


def get_backend(
        repository: audbackend.Repository,
) -> audbackend.Backend:
    r"""Return backend."""

    return audbackend.create(
        name=repository.backend,
        host=repository.host,
        repository=repository.name,
    )


def get_header(
        short_id: str,
        version: str,
        cache_root: str,
) -> typing.Tuple[audbackend.Backend, typing.Dict[str, typing.Any]]:
    r"""Return backend and header content."""

    backend, remote_path = header_path(short_id, version)
    local_path = os.path.join(
        cache_root,
        short_id,
        f'{version}.{define.HEADER_EXT}',
    )

    # header is not in cache download it
    try:
        if not os.path.exists(local_path):
            audeer.mkdir(os.path.dirname(local_path))
            with tempfile.TemporaryDirectory() as root:
                tmp_path = os.path.join(root, 'model.yaml')
                backend.get_file(
                    remote_path,
                    tmp_path,
                    version,
                    ext=define.HEADER_EXT,
                )
                shutil.move(tmp_path, local_path)
    except FileNotFoundError:
        raise_model_not_found_error(short_id, version)

    # read header from local file
    with open(local_path, 'r') as fp:
        header = yaml.load(fp, Loader=yaml.Loader)

    return backend, header


def get_meta(
        short_id: str,
        version: str,
        cache_root: str,
) -> (audbackend.Backend, typing.Dict[str, typing.Any]):
    r"""Return backend and metadata."""

    backend, remote_path = meta_path(short_id, version, cache_root)

    local_path = os.path.join(
        cache_root,
        short_id,
        f'{version}.{define.META_EXT}',
    )

    # if metadata in cache,
    # figure out if it matches remote version
    # and delete it if this is not the case
    if os.path.exists(local_path):
        local_checksum = audbackend.md5(local_path)
        remote_checksum = backend.checksum(
            remote_path,
            version,
            ext=define.META_EXT,
        )
        if local_checksum != remote_checksum:
            os.remove(local_path)

    # download metadata if it is not in cache yet
    if not os.path.exists(local_path):
        audeer.mkdir(os.path.dirname(local_path))
        with tempfile.TemporaryDirectory() as root:
            tmp_path = os.path.join(root, 'meta.yaml')
            backend.get_file(
                remote_path,
                tmp_path,
                version,
                ext=define.META_EXT,
            )
            shutil.move(tmp_path, local_path)

    # read metadata from local file
    with open(local_path, 'r') as fp:
        meta = yaml.load(fp, Loader=yaml.Loader)
        if meta is None:
            meta = {}

    return backend, meta


def header_path(
        short_id: str,
        version: str,
) -> typing.Union[
    typing.Tuple[audbackend.Backend, str],
]:
    r"""Return backend and header path."""

    # if we have only one repository
    # we assume the header exists there
    # and return without checking if file exists
    for repository in config.REPOSITORIES:
        backend = get_backend(repository)
        path = backend.join(
            define.UID_FOLDER,
            f'{short_id}.{define.HEADER_EXT}',
        )
        if (
                len(config.REPOSITORIES) == 1
                or backend.exists(path, version=version, ext=define.HEADER_EXT)
        ):
            return backend, path

    # This error is only raised if we have several repos,
    # so we need to tackle it in get_header() as well
    raise_model_not_found_error(short_id, version)


def header_versions(
        short_id: str,
) -> typing.Sequence[typing.Tuple[audbackend.Backend, str, str]]:
    r"""Return list of backend, header path and version."""

    matches = []

    for repository in config.REPOSITORIES:
        backend = get_backend(repository)
        path = backend.join(
            define.UID_FOLDER,
            f'{short_id}.{define.HEADER_EXT}',
        )
        versions = backend.versions(path, ext=define.HEADER_EXT)
        for version in versions:
            matches.append((backend, path, version))

    return matches


def meta_path(
        short_id: str,
        version: str,
        cache_root: str,
) -> typing.Tuple[audbackend.Backend, str]:
    r"""Return backend, metadata path and version."""

    backend, header = get_header(short_id, version, cache_root)
    path = backend.join(
        define.UID_FOLDER,
        f'{short_id}.{define.META_EXT}',
    )

    return backend, path


def put_archive(
        short_id: str,
        version: str,
        name: str,
        subgroup: str,
        root: str,
        backend: audbackend.Backend,
) -> str:
    r"""Put archive to backend."""

    dst_path = backend.join(
        *subgroup.split('.'),
        name,
        short_id + '.zip',
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, 'model.zip')
        files = utils.scan_files(root)
        audeer.create_archive(root, files, src_path)
        backend.put_file(src_path, dst_path, version)

    return dst_path


def put_header(
        short_id: str,
        version: str,
        header: typing.Dict[str, typing.Any],
        backend: audbackend.Backend,
) -> str:
    r"""Put header to backend."""

    dst_path = backend.join(
        define.UID_FOLDER,
        f'{short_id}.{define.HEADER_EXT}',
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, 'model.yaml')
        write_yaml(src_path, header)
        backend.put_file(
            src_path,
            dst_path,
            version,
            ext=define.HEADER_EXT,
        )

    return dst_path


def put_meta(
        short_id: str,
        version: str,
        meta: typing.Dict[str, typing.Any],
        backend: audbackend.Backend,
) -> str:
    r"""Put meta to backend."""

    dst_path = backend.join(
        define.UID_FOLDER,
        f'{short_id}.{define.META_EXT}',
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, 'meta.yaml')
        write_yaml(src_path, meta)
        backend.put_file(
            src_path,
            dst_path,
            version,
            ext=define.META_EXT,
        )

    return dst_path


def raise_model_not_found_error(
        short_id: str,
        version: str,
):
    r"""Raise RuntimeError with custom error message."""
    if version:
        uid = f'{short_id}-{version}'
    else:
        uid = short_id
    raise RuntimeError(
        f"A model with ID "
        f"'{uid}' "
        f"does not exist."
    )


def split_uid(
        uid: str,
        cache_root: str,
) -> typing.Tuple[str, str]:
    r"""Split uid into short id and version."""

    if utils.is_legacy_uid(uid):

        short_id = uid
        version = None

        # if header is in cache, derive the version from there (very fast)

        root = os.path.join(
            cache_root,
            uid,
        )
        if os.path.exists(root):
            files = audeer.list_file_names(
                root,
                basenames=True,
                filetype=define.HEADER_EXT,
            )
            if files:
                version = files[0].replace(f'.{define.HEADER_EXT}', '')

        if version is None:

            # otherwise try to derive from header on backend (still faster)

            for repository in config.REPOSITORIES:
                backend = get_backend(repository)
                remote_path = backend.join(
                    define.UID_FOLDER,
                    uid,
                )
                versions = backend.versions(remote_path)
                if versions:
                    # uid of legacy models encode version
                    # i.e. we cannot have more than one version
                    version = versions[0]
                    break

        if version is None:
            raise_model_not_found_error(short_id, version)

    elif utils.is_short_uid(uid):

        short_id = uid
        versions = header_versions(short_id)

        if not versions:
            raise_model_not_found_error(short_id, None)

        version = versions[-1][2]

    else:

        tokens = uid.split('-')
        short_id = tokens[0]
        version = '-'.join(tokens[1:])

    return short_id, version


def write_yaml(
    src_path: str,
    obj: typing.Dict,
):
    r"""Write dictionary to YAML file."""
    with open(src_path, 'w') as fp:
        try:
            yaml.dump(obj, fp)
        except Exception:
            raise RuntimeError(
                f"{SERIALIZE_ERROR_MESSAGE}"
                f"'{obj}'"
            )
