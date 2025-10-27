from collections.abc import Sequence
import os
import shutil
import tempfile

import oyaml as yaml

import audbackend
import audeer

from audmodel.core.config import config
import audmodel.core.define as define
from audmodel.core.lock import lock
import audmodel.core.utils as utils


SERIALIZE_ERROR_MESSAGE = "Cannot serialize the following object to a YAML file:\n"


def archive_path(
    short_id: str,
    version: str,
    cache_root: str,
    verbose: bool,
) -> tuple[audbackend.interface.Maven, str]:
    r"""Return backend, archive path and version.

    Args:
        short_id: model ID without version
        version: model version
        cache_root: path of cache root
        verbose: if ``True`` show message
            or progress bar
            when downloading header file

    Returns:
        backend interface, model path on backend

    Raises:
        BackendError: if connection to backend
            cannot be established
        RuntimeError: if requested model does not exists

    """
    backend_interface, header = get_header(
        short_id,
        version,
        cache_root,
        verbose,
    )
    name = header["name"]
    subgroup = header["subgroup"].split(".")
    path = backend_interface.join("/", *subgroup, name, short_id + ".zip")

    return backend_interface, path


def get_archive(
    short_id: str,
    version: str,
    cache_root: str,
    timeout: float,
    verbose: bool,
) -> str:
    r"""Return backend and local archive path.

    Args:
        short_id: model ID without version
        version: model version
        cache_root: path of cache root
        timeout: maximum time in seconds
            before giving up acquiring a lock
        verbose: if ``True`` show message
            or progress bar
            when downloading file

    Returns:
        backend interface, path to downloaded model folder

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    root = os.path.join(
        cache_root,
        short_id,
        version,
    )

    with lock(root, timeout=timeout):
        if not os.path.exists(root) or len(os.listdir(root)) == 0:
            tmp_root = audeer.mkdir(f"{root}~")
            backend_interface, path = archive_path(
                short_id,
                version,
                cache_root,
                verbose,
            )

            with backend_interface.backend:
                # get archive
                src_path = path
                dst_path = os.path.join(tmp_root, "model.zip")
                backend_interface.get_file(
                    src_path,
                    dst_path,
                    version,
                    verbose=verbose,
                )

            # extract files
            audeer.extract_archive(
                dst_path,
                tmp_root,
                keep_archive=False,
                verbose=verbose,
            )

            # move tmp folder to final destination
            if os.path.exists(root):
                os.rmdir(root)
            os.rename(tmp_root, root)

    return root


def get_header(
    short_id: str,
    version: str,
    cache_root: str,
    verbose: bool,
) -> tuple[audbackend.interface.Maven, dict[str, object]]:
    r"""Return backend and header content.

    Args:
        short_id: model ID without version
        version: model version
        cache_root: path of cache root
        verbose: if ``True`` show message
            or progress bar
            when downloading file

    Returns:
        backend interface, model header

    Raises:
        BackendError: if connection to backend
            cannot be established
        RuntimeError: if requested model does not exist

    """
    backend_interface, remote_path = header_path(short_id, version)
    local_path = os.path.join(
        cache_root,
        short_id,
        f"{version}.{define.HEADER_EXT}",
    )

    with lock(local_path):
        # header is not in cache download it
        if not os.path.exists(local_path):
            with backend_interface.backend:
                audeer.mkdir(os.path.dirname(local_path))
                with tempfile.TemporaryDirectory() as root:
                    tmp_path = os.path.join(root, "model.yaml")
                    backend_interface.get_file(
                        remote_path,
                        tmp_path,
                        version,
                        verbose=verbose,
                    )
                    shutil.move(tmp_path, local_path)

        # read header from local file
        with open(local_path) as fp:
            header = yaml.load(fp, Loader=yaml.Loader)

    return backend_interface, header


def get_meta(
    short_id: str,
    version: str,
    cache_root: str,
    verbose: bool,
) -> (audbackend.interface.Maven, dict[str, object]):
    r"""Return backend and metadata.

    Args:
        short_id: model ID without version
        version: model version
        cache_root: path of cache root
        verbose: if ``True`` show message
            or progress bar
            when downloading file

    Returns:
        backend interface, model metadata

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    backend_interface, remote_path = meta_path(
        short_id,
        version,
        cache_root,
        verbose,
    )

    local_path = os.path.join(
        cache_root,
        short_id,
        f"{version}.{define.META_EXT}",
    )

    with lock(local_path):
        with backend_interface.backend:
            # if metadata in cache,
            # figure out if it matches remote version
            # and delete it if this is not the case
            if os.path.exists(local_path):
                local_checksum = audeer.md5(local_path)
                remote_checksum = backend_interface.checksum(
                    remote_path,
                    version,
                )
                if local_checksum != remote_checksum:
                    os.remove(local_path)

            # download metadata if it is not in cache yet
            if not os.path.exists(local_path):
                audeer.mkdir(os.path.dirname(local_path))
                with tempfile.TemporaryDirectory() as root:
                    tmp_path = os.path.join(root, "meta.yaml")
                    backend_interface.get_file(
                        remote_path,
                        tmp_path,
                        version,
                        verbose=verbose,
                    )
                    shutil.move(tmp_path, local_path)

        # read metadata from local file
        with open(local_path) as fp:
            meta = yaml.load(fp, Loader=yaml.Loader)
            if meta is None:
                meta = {}

    return backend_interface, meta


def header_path(
    short_id: str,
    version: str,
) -> tuple[audbackend.interface.Maven, str]:
    r"""Return backend and header path.

    Args:
        short_id: model ID without version
        version: model version

    Returns:
        backend interface, path to header on backend

    Raises:
        BackendError: if connection to backend
            cannot be established
        RuntimeError: if requested model does not exist

    """
    for repository in config.REPOSITORIES:
        if not version:
            break

        backend_interface = repository.create_backend_interface()
        path = backend_interface.join(
            "/",
            define.UID_FOLDER,
            f"{short_id}.{define.HEADER_EXT}",
        )

        # Look for the repository,
        # that contains the requested header
        with backend_interface.backend:
            header_exists = backend_interface.exists(
                path,
                version,
                suppress_backend_errors=True,
            )
        if header_exists:
            return backend_interface, path

    # If no repository can be found,
    # reuested model does not exist
    raise_model_not_found_error(short_id, version)


def header_versions(
    short_id: str,
) -> Sequence[tuple[audbackend.interface.Maven, str, str]]:
    r"""Return list of backend, header path and version.

    Args:
        short_id: model ID without version

    Returns:
        list of backend interface, model header path on backend, model version

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    matches = []

    for repository in config.REPOSITORIES:
        backend_interface = repository.create_backend_interface()
        path = backend_interface.join(
            "/",
            define.UID_FOLDER,
            f"{short_id}.{define.HEADER_EXT}",
        )
        with backend_interface.backend:
            versions = backend_interface.versions(path, suppress_backend_errors=True)
            for version in versions:
                matches.append((backend_interface, path, version))

    return matches


def meta_path(
    short_id: str,
    version: str,
    cache_root: str,
    verbose: bool,
) -> tuple[audbackend.interface.Maven, str]:
    r"""Return backend, metadata path and version.

    Args:
        short_id: model ID without version
        version: model version
        cache_root: path of cache root
        verbose: if ``True`` show message
            or progress bar
            when downloading file

    Returns:
        backend interface, model metadata path on backend

    Raises:
        BackendError: if connection to backend
            cannot be established
        RuntimeError: if requested model does not exists

    """
    backend_interface, header = get_header(
        short_id,
        version,
        cache_root,
        verbose,
    )
    path = backend_interface.join(
        "/",
        define.UID_FOLDER,
        f"{short_id}.{define.META_EXT}",
    )

    return backend_interface, path


def put_archive(
    short_id: str,
    version: str,
    name: str,
    subgroup: str,
    root: str,
    backend_interface: audbackend.interface.Maven,
    verbose: bool,
) -> str:
    r"""Put archive to backend.

    Args:
        short_id: model ID without version
        version: model version
        name: model name
        subgroup: model subgroup
        root: path to model root folder
        backend_interface: backend interface instance
        verbose: if ``True`` show message
            when uploading file

    Returns:
        archive path on backend

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    dst_path = backend_interface.join(
        "/",
        *subgroup.split("."),
        name,
        short_id + ".zip",
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, "model.zip")
        files = utils.scan_files(root)
        audeer.create_archive(
            root,
            files,
            src_path,
            verbose=verbose,
        )
        with backend_interface.backend:
            backend_interface.put_file(
                src_path,
                dst_path,
                version,
                verbose=verbose,
            )

    return dst_path


def put_header(
    short_id: str,
    version: str,
    header: dict[str, object],
    backend_interface: audbackend.interface.Maven,
    verbose: bool,
) -> str:
    r"""Put header to backend.

    Args:
        short_id: model ID without version
        version: model version
        header: model header
        backend_interface: backend interface instance
        verbose: if ``True`` show message
            when uploading file

    Returns:
        header path on backend

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    dst_path = backend_interface.join(
        "/",
        define.UID_FOLDER,
        f"{short_id}.{define.HEADER_EXT}",
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, "model.yaml")
        write_yaml(src_path, header)
        with backend_interface.backend:
            backend_interface.put_file(
                src_path,
                dst_path,
                version,
                verbose=verbose,
            )

    return dst_path


def put_meta(
    short_id: str,
    version: str,
    meta: dict[str, object],
    backend_interface: audbackend.interface.Maven,
    verbose: bool,
) -> str:
    r"""Put meta to backend.

    Args:
        short_id: model ID without version
        version: model version
        meta: model metadata
        backend_interface: backend interface instance
        verbose: if ``True`` show message
            when uploading file

    Returns:
        metadata path on backend

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    dst_path = backend_interface.join(
        "/",
        define.UID_FOLDER,
        f"{short_id}.{define.META_EXT}",
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, "meta.yaml")
        write_yaml(src_path, meta)
        with backend_interface.backend:
            backend_interface.put_file(
                src_path,
                dst_path,
                version,
                verbose=verbose,
            )

    return dst_path


def alias_path(
    alias: str,
) -> tuple[audbackend.interface.Maven, str]:
    r"""Return backend and alias path.

    Args:
        alias: alias name

    Returns:
        backend interface, path to alias on backend

    Raises:
        BackendError: if connection to backend
            cannot be established
        RuntimeError: if requested alias does not exist

    """
    for repository in config.REPOSITORIES:
        backend_interface = repository.create_backend_interface()
        path = backend_interface.join(
            "/",
            define.ALIAS_FOLDER,
            f"{alias}.{define.ALIAS_EXT}",
        )

        # Look for the repository that contains the requested alias
        with backend_interface.backend:
            alias_exists = backend_interface.exists(
                path,
                "1.0.0",
                suppress_backend_errors=True,
            )
        if alias_exists:
            return backend_interface, path

    # If no repository can be found, requested alias does not exist
    raise RuntimeError(f"An alias with name '{alias}' does not exist.")


def get_alias(
    alias: str,
    cache_root: str,
    verbose: bool,
) -> tuple[audbackend.interface.Maven, str]:
    r"""Return backend and UID for alias.

    Args:
        alias: alias name
        cache_root: path of cache root
        verbose: if ``True`` show message
            or progress bar
            when downloading file

    Returns:
        backend interface, model UID

    Raises:
        BackendError: if connection to backend
            cannot be established
        RuntimeError: if requested alias does not exist,
            or alias file is corrupted

    """
    backend_interface, remote_path = alias_path(alias)

    with backend_interface.backend:
        # Download and read alias
        with tempfile.TemporaryDirectory() as root:
            tmp_path = os.path.join(root, "alias.yaml")
            backend_interface.get_file(
                remote_path,
                tmp_path,
                "1.0.0",
                verbose=verbose,
            )
            try:
                with open(tmp_path) as fp:
                    alias_data = yaml.load(fp, Loader=yaml.Loader)
            except yaml.YAMLError as yaml_ex:
                raise RuntimeError(f"Failed to parse alias file: {yaml_ex}")

    return backend_interface, alias_data["uid"]


def put_alias(
    alias: str,
    uid: str,
    backend_interface: audbackend.interface.Maven,
    verbose: bool,
) -> str:
    r"""Put alias to backend.

    Args:
        alias: alias name
        uid: model UID
        backend_interface: backend interface instance
        verbose: if ``True`` show message
            when uploading file

    Returns:
        alias path on backend

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    dst_path = backend_interface.join(
        "/",
        define.ALIAS_FOLDER,
        f"{alias}.{define.ALIAS_EXT}",
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, "alias.yaml")
        alias_data = {"uid": uid}
        write_yaml(src_path, alias_data)
        with backend_interface.backend:
            backend_interface.put_file(
                src_path,
                dst_path,
                "1.0.0",
                verbose=verbose,
            )

    return dst_path


def aliases_path(
    short_id: str,
    version: str,
) -> tuple[audbackend.interface.Maven, str]:
    r"""Return backend and aliases list path.

    Args:
        short_id: model ID without version
        version: model version

    Returns:
        backend interface, path to aliases list on backend

    Raises:
        BackendError: if connection to backend
            cannot be established
        RuntimeError: if requested model does not exist

    """
    backend_interface, path = header_path(short_id, version)
    aliases_path = backend_interface.join(
        "/",
        define.UID_FOLDER,
        f"{short_id}.{define.ALIASES_EXT}",
    )

    return backend_interface, aliases_path


def get_aliases(
    short_id: str,
    version: str,
    cache_root: str,
    verbose: bool,
) -> tuple[audbackend.interface.Maven, list[str]]:
    r"""Return backend and aliases list.

    Args:
        short_id: model ID without version
        version: model version
        cache_root: path of cache root
        verbose: if ``True`` show message
            or progress bar
            when downloading file

    Returns:
        backend interface, list of aliases

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    backend_interface, remote_path = aliases_path(short_id, version)

    with backend_interface.backend:
        # Check if aliases file exists on backend
        aliases_exists = backend_interface.exists(
            remote_path,
            version,
            suppress_backend_errors=True,
        )

        if not aliases_exists:
            # No aliases file means no aliases for this model
            return backend_interface, []

        # Download and read aliases
        with tempfile.TemporaryDirectory() as root:
            tmp_path = os.path.join(root, "aliases.yaml")
            backend_interface.get_file(
                remote_path,
                tmp_path,
                version,
                verbose=verbose,
            )
            with open(tmp_path) as fp:
                aliases_data = yaml.load(fp, Loader=yaml.Loader)
                if aliases_data is None or "aliases" not in aliases_data:
                    return backend_interface, []

    return backend_interface, aliases_data["aliases"]


def put_aliases(
    short_id: str,
    version: str,
    aliases: list[str],
    backend_interface: audbackend.interface.Maven,
    verbose: bool,
) -> str:
    r"""Put aliases list to UID folder on backend.

    Args:
        short_id: model ID without version
        version: model version
        aliases: list of alias names
        backend_interface: backend interface instance
        verbose: if ``True`` show message
            when uploading file

    Returns:
        aliases path on backend

    Raises:
        BackendError: if connection to backend
            cannot be established

    """
    dst_path = backend_interface.join(
        "/",
        define.UID_FOLDER,
        f"{short_id}.{define.ALIASES_EXT}",
    )

    with tempfile.TemporaryDirectory() as tmp_root:
        src_path = os.path.join(tmp_root, "aliases.yaml")
        aliases_data = {"aliases": sorted(aliases)}
        write_yaml(src_path, aliases_data)
        with backend_interface.backend:
            backend_interface.put_file(
                src_path,
                dst_path,
                version,
                verbose=verbose,
            )

    return dst_path


def raise_model_not_found_error(
    short_id: str,
    version: str,
):
    r"""Raise RuntimeError with custom error message."""
    if version:
        uid = f"{short_id}-{version}"
    else:
        uid = short_id
    raise RuntimeError(f"A model with ID '{uid}' does not exist.")


def split_uid(
    uid: str,
    cache_root: str,
) -> tuple[str, str]:
    r"""Split uid into short id and version.

    Args:
        uid: unique model ID (omit version for latest version) or alias
        cache_root: path to cache root

    Returns:
        model ID without version (short ID), model version

    Raises:
        BackendError: if short or legacy model ID is provided,
            and connection to backend
            cannot be established
        RuntimeError: if short or legacy model ID is provided,
            and requested model does not exists
        RuntimeError: if an alias is provided and does not exist

    """
    # Check if it's a potential alias (doesn't match UID patterns)
    # If so, try to resolve it first
    if utils.is_alias(uid):
        try:
            _, resolved_uid = get_alias(uid, cache_root, verbose=False)
            uid = resolved_uid
        except RuntimeError:
            # Alias doesn't exist - this could be either:
            # 1. A legitimate alias that doesn't exist
            # 2. An invalid UID that was misidentified as an alias
            #
            # To maintain backward compatibility, we report it as a model ID error
            # since there's no way to know the user's intent
            raise_model_not_found_error(uid, None)

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
                version = files[0].replace(f".{define.HEADER_EXT}", "")

        if version is None:
            # otherwise try to derive from header on backend (still faster)

            for repository in config.REPOSITORIES:
                backend_interface = repository.create_backend_interface()
                with backend_interface.backend:
                    remote_path = backend_interface.join(
                        "/",
                        define.UID_FOLDER,
                        f"{uid}.{define.HEADER_EXT}",
                    )
                    versions = backend_interface.versions(
                        remote_path,
                        suppress_backend_errors=True,
                    )
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
        tokens = uid.split("-")
        short_id = tokens[0]
        version = "-".join(tokens[1:])

    return short_id, version


def write_yaml(
    src_path: str,
    obj: dict,
):
    r"""Write dictionary to YAML file.

    Args:
        src_path: path to YAML file
        obj: object that should be serialized as YAML file

    Raises:
        RuntimeError: if ``obj`` cannot be serialized,
            or file cannot be opened

    """
    with open(src_path, "w") as fp:
        try:
            yaml.dump(obj, fp)
        except Exception:
            raise RuntimeError(f"{SERIALIZE_ERROR_MESSAGE}'{obj}'")
