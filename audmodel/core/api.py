import os
import tempfile
import typing

import audeer
import audfactory

from audmodel.core.config import config
from audmodel.core.url import (
    name_from_url,
    repository_from_url,
    subgroup_from_url,
    version_from_url,
)
from audmodel.core.utils import upload_folder


def default_cache_root() -> str:
    r"""Return the default path under which models will be stored.

    """
    return os.environ.get('AUDMODEL_CACHE_ROOT') or config.AUDMODEL_CACHE_ROOT


def get_lookup_table(
        name: str,
        version: str = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> audfactory.Lookup:
    r"""Return lookup table.

    Args:
        name: model name
        version: version string
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private

    Raises:
        RuntimeError: if table does not exist

    """
    lookup = audfactory.Lookup(
        _group_id(name, subgroup),
        version=version,
        repository=_repository(private),
    )
    return lookup


def get_model_id(
        name: str,
        params: typing.Dict[str, typing.Any],
        version: str = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:
    r"""Return unique model id.

    Args:
        name: model name
        params: dictionary with parameters
        version: version string
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private

    Raises:
        RuntimeError: if model does not exist

    """
    group_id = _group_id(name, subgroup)
    repository = _repository(private)
    if version is None:
        version = audfactory.Lookup.latest_version(
            group_id,
            params=params,
            repository=repository,
        )
    lookup = audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )
    return lookup.find(params)


def latest_version(
        name: str,
        params: typing.Dict[str, typing.Any] = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> str:
    r"""Latest available version of model.

    Args:
        name: model name
        params: dictionary with parameters
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private

    Returns:
        latest version of model

    """
    version = audfactory.Lookup.latest_version(
        _group_id(name, subgroup),
        params=params,
        repository=_repository(private),
    )
    return version


def load(
        uid: str,
        *,
        force: bool = False,
        root: str = None,
        verbose: bool = False,
) -> str:
    r"""Download a model by id and return model folder.

    .. note:: If ``root`` is not set, the model is downloaded to the default
        cache folder (see :meth:`audmodel.default_cache_root`). If the
        model already exists in the cache, the download is skipped (unless
        ``force`` is set).

    Args:
        uid: unique model identifier
        force: download model even if it exists already
        root: store model within this folder
        verbose: show verbose output

    Raises:
        RuntimeError: if model does not exist

    """
    model_url = url(uid)
    group_id = _group_id(
        name_from_url(model_url),
        subgroup_from_url(model_url),
    )
    version = version_from_url(model_url)

    root = audeer.safe_path(root or default_cache_root())
    root = os.path.join(
        root or default_cache_root(),
        audfactory.group_id_to_path(group_id),
        version,
        uid,
    )
    root = audeer.safe_path(root)

    zip_file = os.path.join(tempfile._get_default_tempdir(), f'{uid}.zip')
    if force or not os.path.exists(root):
        audeer.mkdir(root)
        audfactory.download_artifact(model_url, zip_file, verbose=verbose)
        audeer.extract_archive(
            zip_file,
            root,
            keep_archive=False,
            verbose=verbose,
        )

    return root


def name(uid: str) -> str:
    r"""Name of model.

    Args:
        uid: unique model ID

    Returns:
        model name

    Example:
        >>> name('98ccb530-b162-11ea-8427-ac1f6bac2502')
        'audgender'

    """
    model_url = url(uid)
    return name_from_url(model_url)


def parameters(uid: str) -> typing.Dict:
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
        force: bool = False,
        verbose: bool = False,
) -> str:
    r"""Zip model, publish as a new artifact and returns the model's unique id.

    .. note:: Assigns a unique id and adds an entry in the lookup table.
        If the lookup table does not exist it will be created. If an entry
        already exists, the operation will fail.

    Args:
        root: folder with model files
        name: model name
        params: dictionary with parameters
        version: version string
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private
        create: create lookup table if it does not exist
        force: publish model even if it exists already
        verbose: show verbose output

    Raises:
        RuntimeError: if an artifact exists already

    """
    group_id = _group_id(name, subgroup)
    repository = _repository(private)
    if not audfactory.Lookup.exists(group_id, version, repository=repository):
        if create:
            audfactory.Lookup.create(
                group_id,
                version,
                list(params.keys()),
                repository=repository,
            )
        else:
            raise RuntimeError(f"A lookup table for '{name}' and "
                               f"'{version}' does not exist yet.")

    lookup = audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )
    uid = lookup.append(params)
    upload_folder(root, group_id, repository,
                  uid, version, force=force, verbose=verbose)
    return uid


def remove(uid: str) -> None:
    r"""Remove a model.

    Args:
        uid: unique model ID

    """
    model_url = url(uid)
    lookup = _lookup_from_url(model_url)
    lookup.remove(lookup[uid])
    audfactory.artifactory_path(model_url).parent.parent.rmdir()


def subgroup(uid: str) -> str:
    r"""Subgroup of model.

    Args:
        uid: unique model ID

    Returns:
        model subgroup

    Example:
        >>> subgroup('98ccb530-b162-11ea-8427-ac1f6bac2502')
        'gender'

    """
    model_url = url(uid)
    return subgroup_from_url(model_url)


def url(uid: str) -> str:
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

    Example:
        >>> model_url = url('98ccb530-b162-11ea-8427-ac1f6bac2502')
        >>> '/'.join(model_url.split('/')[4:10])
        'models-public-local/com/audeering/models/gender/audgender'

    """
    # UID has '-' at position 8, 13, 18, 23
    idx = [8, 13, 18, 23]
    if len(uid) != 36 or any([uid[i] != '-' for i in idx]):
        raise ValueError('Provided unique ID not valid')
    try:
        pattern = f'artifact?name={uid}'
        for repository in [
                config.REPOSITORY_PUBLIC,
                config.REPOSITORY_PRIVATE,
        ]:
            r = audfactory.rest_api_search(pattern, repository=repository)
            if r.status_code != 200:  # pragma: no cover
                raise RuntimeError(
                    f'Error trying to find model.\n'
                    f'The REST API query was not succesful:\n'
                    f'Error code: {r.status_code}\n'
                    f'Error message: {r.text}'
                )
            urls = r.json()['results']
            if len(urls) > 1:  # pragma: no cover
                raise RuntimeError(f'Found more then one model: {urls}')
            elif len(urls) == 1:
                break
        if len(urls) == 0:
            raise RuntimeError(f"A model with ID '{uid}' does not exist")
        url = urls[0]['uri']
    except ConnectionError:  # pragma: no cover
        raise RuntimeError(
            'Artifactory is offline.\n\n'
            'Please make sure https://artifactory.audeering.com '
            'is reachable.'
        )
    # Replace beginning of URL as it includes /api/storage and port
    relative_repo_url = '/'.join(url.split('/')[6:])
    url = f'{audfactory.config.ARTIFACTORY_ROOT}/{relative_repo_url}'
    return url


def version(uid: str) -> str:
    r"""Version of model.

    Args:
        uid: unique model ID

    Returns:
        model version

    Example:
        >>> version('98ccb530-b162-11ea-8427-ac1f6bac2502')
        '1.0.0'

    """
    model_url = url(uid)
    return version_from_url(model_url)


def versions(
        name: str,
        params: typing.Dict[str, typing.Any] = None,
        *,
        subgroup: str = None,
        private: bool = False,
) -> typing.Sequence[str]:
    r"""Return a list of available versions.

    Args:
        name: model name
        params: dictionary with parameters
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private

    """
    versions = audfactory.Lookup.versions(
        _group_id(name, subgroup),
        name=config.LOOKUP_TABLE_NAME,
        params=params,
        repository=_repository(private),
    )
    return versions


def _group_id(name: str, subgroup: str) -> str:
    if subgroup is None:
        return f'{config.GROUP_ID}.{name}'
    else:
        return f'{config.GROUP_ID}.{subgroup}.{name}'


def _lookup_from_url(model_url: str) -> audfactory.Lookup:
    group_id = _group_id(
        name_from_url(model_url),
        subgroup_from_url(model_url),
    )
    version = version_from_url(model_url)
    repository = repository_from_url(model_url)
    return audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )


def _repository(private: bool) -> str:
    if private:
        return config.REPOSITORY_PRIVATE
    else:
        return config.REPOSITORY_PUBLIC
