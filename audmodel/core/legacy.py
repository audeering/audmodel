import errno
import os
import tempfile
import typing
import zipfile

import audeer
import audfactory

from audmodel.core.config import config


class defaults():

    ARTIFACTORY_HOST = 'https://artifactory.audeering.com/artifactory'
    r"""Server address of Artifactory server."""

    LOOKUP_TABLE_NAME = 'lookup'
    r"""Name of lookup table."""
    LOOKUP_TABLE_EXT = 'csv'
    r"""Extension of lookup table."""
    LOOKUP_TABLE_INDEX = 'id'
    r"""Name of lookup table index."""


# helper functions

def scan_files(
        root: str,
        sub_dir: str = '',
) -> (str, str):  # pragma: no cover

    for entry in os.scandir(root):
        if entry.is_dir(follow_symlinks=False):
            yield from scan_files(
                entry.path,
                os.path.join(sub_dir, entry.name),
            )
        else:
            yield sub_dir, entry.name


def upload_folder(
        root: str,
        group_id: str,
        repository: str,
        name: str,
        version: str,
        verbose: bool = False,
) -> str:  # pragma: no cover

    root = audeer.safe_path(root)
    if not os.path.isdir(root):
        raise FileNotFoundError(
            errno.ENOENT,
            os.strerror(errno.ENOENT),
            root,
        )

    server_url = audfactory.url(
        defaults.ARTIFACTORY_HOST,
        repository=repository,
        group_id=group_id,
        name=name,
        version=version,
    )
    url = f'{server_url}/{name}-{version}.zip'

    if not audfactory.path(url).exists():
        src_path = os.path.join(
            tempfile._get_default_tempdir(),
            f'{name}-{version}.zip',
        )
        zip_folder(root, src_path, verbose=verbose)
        audfactory.deploy(src_path, url, verbose=verbose)
        os.remove(src_path)

    return url


def zip_folder(
        src_root: str,
        dst_path: str,
        *,
        verbose: bool = False,
):  # pragma: no cover

    with zipfile.ZipFile(dst_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        files = list(scan_files(src_root))
        if verbose:
            with audeer.progress_bar(
                    files,
                    total=len(files),
                    desc=''
            ) as pbar:
                for base, file in pbar:
                    path = os.path.join(src_root, base, file)
                    desc = audeer.format_display_message(
                        f'Zip {path}',
                        pbar=True,
                    )
                    pbar.set_description_str(desc, refresh=True)
                    zf.write(path, arcname=os.path.join(base, file))
        else:
            for base, file in files:
                zf.write(
                    os.path.join(src_root, base, file),
                    arcname=os.path.join(base, file),
                )


def name_from_url(url: str) -> str:  # pragma: no cover
    return url.split('/')[-4]


def private_from_url(url: str) -> bool:  # pragma: no cover
    repository = repository_from_url(url)
    return repository == config.LEGACY_REPOSITORY_PRIVATE


def repository_from_url(url: str) -> str:  # pragma: no cover
    return url.split('/')[4]


def subgroup_from_url(url: str) -> typing.Union[None, str]:  # pragma: no cover
    # Consider length of group ID
    url_start = (
        f'{defaults.ARTIFACTORY_HOST}/'
        f'repo/'
        f'{audfactory.group_id_to_path("com.audeering.models")}'
    )
    start_length = len(url_start.split('/'))
    subgroup = '.'.join(url.split('/')[start_length:-4])
    if len(subgroup) == 0:
        return None
    else:
        return subgroup


def version_from_url(url: str) -> str:  # pragma: no cover
    return url.split('/')[-2]


# legacy api

def author(uid: str) -> str:  # pragma: no cover
    r"""Author of model.

    The author is defined
    by the Artifactory user name
    of the person that published the model.

    Args:
        uid: unique model ID

    Returns:
        model author

    """
    model_url = url(uid)
    path = audfactory.path(model_url)
    stats = path.stat()
    return stats.modified_by


def date(uid: str) -> str:  # pragma: no cover
    r"""Publication date of model.

    The publication date is defined
    as the last date the model artifact was modified
    on Artifactory.

    Args:
        uid: unique model ID

    Returns:
        model publication date

    """
    model_url = url(uid)
    path = audfactory.path(model_url)
    stats = path.stat()
    return stats.mtime.strftime('%Y/%m/%d')


def latest_version(
        name: str,
        params: typing.Dict[str, typing.Any] = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:  # pragma: no cover
    r"""Latest available version of model.

    The highest version,
    that is available for the combination
    of provided ``name``, ``subgroup``,
    and model ``params``.

    Args:
        name: model name
        params: dictionary with parameters
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private

    Returns:
        latest version of model

    """
    version = audfactory.Lookup.latest_version(
        defaults.ARTIFACTORY_HOST,
        _repository(private),
        _group_id(name, subgroup),
        params=params,
    )
    return version


def load(
        uid: str,
        root: str,
        *,
        verbose: bool = False,
) -> str:  # pragma: no cover
    r"""Download a model by its unique ID.

    If ``root`` is not set,
    the model is downloaded to the default cache folder,
    see :meth:`audmodel.default_cache_root`.
    If the model already exists in the cache folder,
    the download is skipped.

    Args:
        uid: unique model identifier
        root: store model within this folder
        verbose: show verbose output

    Returns:
        path to model folder

    Raises:
        RuntimeError: if model does not exist

    """
    model_url = url(uid)
    repository = repository_from_url(model_url)
    group_id = _group_id(
        name_from_url(model_url),
        subgroup_from_url(model_url),
    )
    version = version_from_url(model_url)

    root = os.path.join(
        root,
        repository,
        audfactory.group_id_to_path(group_id),
        version,
        uid,
    )
    root = audeer.safe_path(root)

    zip_file = os.path.join(tempfile._get_default_tempdir(), f'{uid}.zip')
    if not os.path.exists(root):
        audeer.mkdir(root)
        audfactory.download(model_url, zip_file, verbose=verbose)
        audeer.extract_archive(
            zip_file,
            root,
            keep_archive=False,
            verbose=verbose,
        )

    return root


def lookup_table(
        name: str,
        version: str = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> audfactory.Lookup:  # pragma: no cover
    r"""Lookup table of specified models.

    Models are specified by the ``name``, ``subgroup``, ``version``,
    and ``private`` arguments.
    Besides they can vary by having different parameters,
    which are locked inside a lookup table
    and assigned to unique model IDs.
    To get an overview of all different parameters models
    where trained with,
    you can download the lookup table and inspect it.

    Args:
        name: model name
        version: version string
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private

    Returns:
        lookup table of models

    Raises:
        RuntimeError: if table does not exist

    """
    lookup = audfactory.Lookup(
        defaults.ARTIFACTORY_HOST,
        _repository(private),
        _group_id(name, subgroup),
        version=version,
    )
    return lookup


def name(uid: str) -> str:  # pragma: no cover
    r"""Name of model.

    Args:
        uid: unique model ID

    Returns:
        model name

    """
    model_url = url(uid)
    return name_from_url(model_url)


def parameters(uid: str) -> typing.Dict:  # pragma: no cover
    r"""Parameters of model.

    Args:
        uid: unique model ID

    Returns:
        model parameters

    Raises:
        RuntimeError: if table does not exist

    """
    model_url = url(uid)
    lookup = _lookup_from_url(model_url)
    return lookup[uid]


def publish(
        root: str,
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str,
        *,
        subgroup: str = None,
        private: bool = False,
        create: bool = True,
        verbose: bool = False,
) -> str:  # pragma: no cover
    r"""Zip model and publish as a new artifact.

    Assigns a unique ID
    and adds an entry in the lookup table.
    If the lookup table does not exist,
    it will be created.
    If an entry already exists,
    the operation will fail.

    Before publishing a model,
    pick meaningful model ``params``, ``name``, ``subgroup``
    values.

    For model ``params`` we recommend to encode:

    * data used to train the model
    * sampling rate
    * feature set(s)
    * scaling applied to the features
    * classifier

    For ``subgroup`` we recommend to encode:

    * task the model was trained for, e.g. ``gender``
    * maybe also project, e.g. ``projectsmile.agent-tone4``
    * package that was used for training,
      if not encoded in name,
      e.g. ``projectsmile.agent-tone4.autrainer``

    For ``name`` we recommend to encode:

    * package that was used for training, e.g. ``autrainer``
    * or if the package contains different sub-routines,
      encode package in ``subgroup`` and the sub-routine
      in ``name``,
      e.g. ``sklearn``

    Args:
        root: folder with model files
        name: model name
        params: dictionary with parameters
        version: version string
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting
            ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private
        create: create lookup table if it does not exist
        verbose: show verbose output

    Returns:
        unique model ID

    Raises:
        RuntimeError: if an artifact exists already

    """
    server = defaults.ARTIFACTORY_HOST
    group_id = _group_id(name, subgroup)
    repository = _repository(private)
    if not audfactory.Lookup.exists(server, repository, group_id, version):
        if create:
            audfactory.Lookup.create(
                server,
                repository,
                group_id,
                version,
                list(params.keys()),
            )
        else:
            raise RuntimeError(f"A lookup table for '{name}' and "
                               f"'{version}' does not exist yet.")

    lookup = audfactory.Lookup(
        server,
        repository,
        group_id,
        version=version,
    )

    param_keys = list(params.keys())
    # Extend lookup table if more parameters are given
    if param_keys not in lookup.columns:
        lookup.extend(param_keys)
    # Extend parameters if more are available in lookup table
    for column in lookup.columns:
        if column not in param_keys:
            params[column] = None

    uid = lookup.append(params)
    upload_folder(root, group_id, repository, uid, version, verbose)

    return uid


def remove(uid: str):  # pragma: no cover
    r"""Remove a model.

    The model will be deleted on Artifactory,
    and removed from its corresponding lookup table.

    Args:
        uid: unique model ID

    """
    model_url = url(uid)
    lookup = _lookup_from_url(model_url)
    lookup.remove(lookup[uid])
    audfactory.path(model_url).parent.parent.rmdir()


def subgroup(uid: str) -> str:  # pragma: no cover
    r"""Subgroup of model.

    Args:
        uid: unique model ID

    Returns:
        model subgroup

    """
    model_url = url(uid)
    return subgroup_from_url(model_url)


def uid(
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:  # pragma: no cover
    r"""Unique model ID for given model arguments.

    Look for the unique ID of a published model,
    specified by model ``params``, ``name``, and ``subgroup``.

    Args:
        name: model name
        params: dictionary with parameters
        version: version string
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting
            ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private

    Returns:
        unique model ID

    Raises:
        RuntimeError: if no lookup table for the model exists

    """
    repository = _repository(private)
    group_id = _group_id(name, subgroup)
    if version is None:
        version = audfactory.Lookup.latest_version(
            defaults.ARTIFACTORY_HOST,
            repository,
            group_id,
            params=params,
        )
    lookup = audfactory.Lookup(
        defaults.ARTIFACTORY_HOST,
        repository,
        group_id,
        version=version,
    )
    return lookup.find(params)


def url(uid: str) -> str:  # pragma: no cover
    r"""Search for model of given ID.

    Args:
        uid: unique model ID

    Returns:
        URL of model

    Raises:
        ValueError: if given unique ID is not valid
        ConnectionError: if Artifactory is not available
        RuntimeError: if Artifactory REST API query failes
        RuntimeError: if more than one model is found
        RuntimeError: if no model is found

    """
    if not audeer.is_uid(uid):
        raise ValueError(f"'{uid}' is not a valid ID")
    try:
        pattern = f'artifact?name={uid}'
        for repository in [
                config.LEGACY_REPOSITORY_PUBLIC,
                config.LEGACY_REPOSITORY_PRIVATE,
        ]:
            search_url = (
                f'{defaults.ARTIFACTORY_HOST}/'
                f'api/search/{pattern}'
                f'&repos={repository}'
            )
            r = audfactory.rest_api_get(search_url)
            if r.status_code != 200:  # pragma: no cover
                raise RuntimeError(
                    f'Error trying to find model.\n'
                    f'The REST API query was not successful:\n'
                    f'Error code: {r.status_code}\n'
                    f'Error message: {r.text}'
                )
            urls = r.json()['results']
            # TODO: remove line if we can limit search to
            #  'com.audeering.models'
            urls = [u for u in urls if u['uri'].endswith('.zip')]
            if len(urls) > 1:  # pragma: no cover
                raise RuntimeError(f'Found more than one model: {urls}')
            elif len(urls) == 1:
                break
        if len(urls) == 0:
            raise RuntimeError(f"A model with ID '{uid}' does not exist")
        url = urls[0]['uri']
    except ConnectionError:  # pragma: no cover
        raise ConnectionError(
            'Artifactory is offline.\n\n'
            'Please make sure https://artifactory.audeering.com '
            'is reachable.'
        )
    # Replace beginning of URL as it includes /api/storage and port
    relative_repo_url = '/'.join(url.split('/')[6:])
    url = f'{defaults.ARTIFACTORY_HOST}/{relative_repo_url}'
    return url


def version(uid: str) -> str:  # pragma: no cover
    r"""Version of model.

    Args:
        uid: unique model ID

    Returns:
        model version

    """
    model_url = url(uid)
    return version_from_url(model_url)


def versions(
        name: str,
        params: typing.Dict[str, typing.Any] = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> typing.List[str]:  # pragma: no cover
    r"""Available model versions.

    All versions,
    that are available for the combination
    of provided ``name``, ``subgroup``,
    and model ``params``.

    Args:
        name: model name
        params: dictionary with parameters
        subgroup: extend group ID to
            ``com.audeering.models.<subgroup>``.
            You can increase the depth
            by using dot-notation,
            e.g. setting
            ``subgroup=foo.bar``
            will result in
            ``com.audeering.models.foo.bar``
        private: repository is private

    Returns:
        available model versions

    """
    versions = audfactory.Lookup.versions(
        defaults.ARTIFACTORY_HOST,
        _repository(private),
        _group_id(name, subgroup),
        name=defaults.LOOKUP_TABLE_NAME,
        params=params,
    )
    return versions


def _group_id(name: str, subgroup: str) -> str:  # pragma: no cover
    if subgroup is None:
        return f'com.audeering.models.{name}'
    else:
        return f'com.audeering.models.{subgroup}.{name}'


def _lookup_from_url(model_url: str) -> audfactory.Lookup:  # pragma: no cover
    group_id = _group_id(
        name_from_url(model_url),
        subgroup_from_url(model_url),
    )
    version = version_from_url(model_url)
    repository = repository_from_url(model_url)
    return audfactory.Lookup(
        defaults.ARTIFACTORY_HOST,
        repository,
        group_id,
        version=version,
    )


def _repository(private: bool) -> str:  # pragma: no cover
    if private:
        return config.LEGACY_REPOSITORY_PRIVATE
    else:
        return config.LEGACY_REPOSITORY_PUBLIC
