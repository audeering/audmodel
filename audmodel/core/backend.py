import os
import shutil
import tempfile
import typing
import oyaml as yaml

import audbackend
import audeer

from audmodel.core.config import config
import audmodel.core.define as define
from audmodel.core.utils import split_uid


def archive_path(
        uid: str,
        cache_root: str,
) -> typing.Tuple[audbackend.Backend, str, str]:
    r"""Return backend, archive path and version."""

    short_id, version = split_uid(uid)
    backend, header = load_header(uid, cache_root)
    name = header['name']
    subgroup = header['subgroup'].split('.')
    group_id = config.GROUP_ID.split('.')
    path = backend.join(*group_id, *subgroup, name, short_id + '.zip')

    return backend, path, version


def get_backend(
        private: bool,
) -> audbackend.Backend:
    r"""Return backend."""

    if private:  # pragma: no cover
        repository = config.REPOSITORY_PRIVATE
    else:
        repository = config.REPOSITORY_PUBLIC
    return audbackend.create(
        name=config.BACKEND_HOST[0],
        host=config.BACKEND_HOST[1],
        repository=repository,
    )


def header_path(
        uid: str,
) -> typing.Union[
    typing.Tuple[audbackend.Backend, str, str],
]:
    r"""Return backend, header path and version."""

    short_id, version = split_uid(uid)

    for private in [False, True]:
        backend = get_backend(private)
        path = backend.join(
            *config.GROUP_ID.split('.'),
            define.HEADER_FOLDER,
            short_id + '.yaml',
        )
        if backend.exists(path, version=version):
            return backend, path, version

    raise RuntimeError(
        f"No header found for a model with ID "
        f"'{uid}'."
    )


def header_versions(
        short_id: str,
) -> typing.Sequence[typing.Tuple[audbackend.Backend, str, str]]:
    r"""Return list of backend, header path and version."""

    matches = []

    for private in [False, True]:
        backend = get_backend(private)
        path = backend.join(
            *config.GROUP_ID.split('.'),
            define.HEADER_FOLDER,
            short_id + '.yaml',
        )
        versions = backend.versions(path)
        for version in versions:
            matches.append((backend, path, version))

    return matches


def load_archive(
        uid: str,
        cache_root: str,
        verbose: bool,
) -> typing.Tuple[audbackend.Backend, str]:
    r"""Return backend and local archive path."""

    backend, path, version = archive_path(uid, cache_root)
    sub_root = os.path.splitext(path)[0]
    sub_root = sub_root.replace(backend.sep, os.path.sep)

    root = os.path.join(
        cache_root,
        sub_root,
        version,
    )

    if not os.path.exists(root):
        tmp_root = audeer.mkdir(root + '~')

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

    return backend, root


def load_header(
        uid: str,
        cache_root: str,
) -> typing.Tuple[audbackend.Backend, typing.Dict[str, typing.Any]]:
    r"""Return backend and header content."""

    local_path = os.path.join(
        cache_root,
        config.GROUP_ID.replace('.', os.sep),
        f'{uid}.yaml',
    )
    backend, remote_path, version = header_path(uid)

    # if header in cache,
    # figure out if it matches remote version
    # and delete it if this is not the case
    if os.path.exists(local_path):
        local_checksum = audbackend.md5(local_path)
        remote_checksum = backend.checksum(remote_path, version)
        # TODO: remove pragma once we have a function to update the header
        if local_checksum != remote_checksum:  # pragma: no cover
            os.remove(local_path)

    # download header if it is not in cache yet
    if not os.path.exists(local_path):
        audeer.mkdir(os.path.dirname(local_path))
        with tempfile.TemporaryDirectory() as root:
            tmp_path = os.path.join(root, 'model.yaml')
            backend.get_file(
                remote_path,
                tmp_path,
                version,
            )
            shutil.move(tmp_path, local_path)

    # read header from local file
    with open(local_path, 'r') as fp:
        header = yaml.load(fp, Loader=yaml.Loader)[uid]

    return backend, header
