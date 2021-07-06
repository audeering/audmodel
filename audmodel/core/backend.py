import datetime
import os
import shutil
import tempfile
import typing
import oyaml as yaml

import audbackend
import audeer

from audmodel.core.config import config
import audmodel.core.define as define
import audmodel.core.legacy as legacy
import audmodel.core.utils as utils


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
        f'{version}.yaml',
    )

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
        if utils.is_legacy_uid(short_id):
            uid = short_id
        else:
            uid = f'{short_id}-{version}'
        header = yaml.load(fp, Loader=yaml.Loader)[uid]

    return backend, header


def header_path(
        short_id: str,
        version: str,
) -> typing.Union[
    typing.Tuple[audbackend.Backend, str],
]:
    r"""Return backend, header path and version."""

    for private in [False, True]:
        backend = get_backend(private)
        path = backend.join(
            define.HEADER_FOLDER,
            short_id + '.yaml',
        )
        if backend.exists(path, version=version):
            return backend, path

    raise RuntimeError(
        f"A header with ID "
        f"'{short_id}' "
        f"and version "
        f"'{version} "
        f"does not exist."
    )


def header_versions(
        short_id: str,
) -> typing.Sequence[typing.Tuple[audbackend.Backend, str, str]]:
    r"""Return list of backend, header path and version."""

    matches = []

    for private in [False, True]:
        backend = get_backend(private)
        path = backend.join(
            define.HEADER_FOLDER,
            short_id + '.yaml',
        )
        versions = backend.versions(path)
        for version in versions:
            matches.append((backend, path, version))

    return matches


def put_archive(
        short_id: str,
        version: str,
        name: str,
        subgroup: str,
        root: str,
        backend: audbackend.Backend,
):
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


def put_header(
        short_id: str,
        version: str,
        header: typing.Dict[str, typing.Any],
        backend: audbackend.Backend,
):
    r"""Put header to backend."""

    dst_path = backend.join(
        define.HEADER_FOLDER,
        short_id + '.yaml',
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, 'model.yaml')
        with open(src_path, 'w') as fp:
            yaml.dump(header, fp)
        backend.put_file(src_path, dst_path, version)


def split_uid(uid: str) -> (str, str):
    r"""Split uid into short id and version."""

    if utils.is_legacy_uid(uid):

        short_id = uid
        version = None

        # if a header was created for the model already,
        # we can derive the version from it (fast!)

        for private in [False, True]:
            backend = get_backend(private)
            remote_path = backend.join(
                define.HEADER_FOLDER,
                uid + '.yaml',
            )
            versions = backend.versions(remote_path)
            if versions:
                # uid of legacy models encode version
                # i.e. we cannot have more than one version
                version = versions[0]
                break

        if version is None:

            # otherwise use old api to get the version (slow!)
            # and publish a header to speed up in future

            url = legacy.url(uid)
            private = legacy.private_from_url(url)
            backend = get_backend(private)
            version = legacy.version(uid)

            header = utils.create_header(
                uid,
                author=legacy.author(uid),
                date=datetime.datetime.strptime(legacy.date(uid), '%Y/%m/%d'),
                name=legacy.name(uid),
                meta={},
                parameters=legacy.parameters(uid),
                subgroup=f'com.audeering.models.{legacy.subgroup(uid)}',
                version=version,
            )
            put_header(uid, version, header, backend)

    else:

        tokens = uid.split('-')
        short_id = tokens[0]
        version = '-'.join(tokens[1:])

    return short_id, version
