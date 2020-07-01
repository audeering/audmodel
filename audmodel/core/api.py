import typing
import os

import audeer
import audfactory

from .config import config
from . import utils


def create_lookup_table(name: str,
                        params: typing.Sequence[str],
                        version: str,
                        *,
                        subgroup: str = None,
                        private: bool = False,
                        force: bool = False,
                        verbose: bool = False) -> str:
    r"""Create lookup table.

    Args:
        name: model name
        params: list with model parameters
        version: version string
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private
        force: create the lookup table even if it exists

    Returns:
        URL to lookup table

    Raises:
        RuntimeError: if table exists already

    """
    group_id, repository = _server(name, subgroup, private)
    url = audfactory.Lookup.create(
        group_id,
        version,
        params,
        repository=repository,
        force=force,
    )
    return url


def get_default_cache_root() -> str:
    r"""Return the default path under which models will be stored.

    """
    return os.environ.get('AUDMODEL_CACHE_ROOT') or config.AUDMODEL_CACHE_ROOT


def delete_lookup_table(name: str,
                        version: str,
                        *,
                        subgroup: str = None,
                        private: bool = False,
                        force: bool = False) -> None:
    r"""Delete a lookup table.

    .. note:: Unless ``force`` is set, the operation will fail if the lookup
        table is not empty. Use :meth:`audmodel.remove` to remove entries
        first.

    Args:
        name: model name
        version: version string
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private
        force: delete lookup table even if it is not empty

    Raises:
        RuntimeError: if table is not empty

    """
    group_id, repository = _server(name, subgroup, private)
    lookup = audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )
    table = lookup.table
    if len(table) > 1:
        if not force:
            raise RuntimeError(
                f"Cannot delete lookup table '{name}-{version}' "
                f"if it is not empty.")
        for uid in [row[0] for row in table[1:]]:
            url = _url_entry(group_id, repository, uid, version)
            audfactory.artifactory_path(url).parent.parent.rmdir()
        lookup.clear()
    audfactory.artifactory_path(lookup.url).parent.rmdir()


def extend_params(name: str,
                  version: str,
                  new_params: typing.Union[
                      str,
                      typing.Sequence[str],
                      typing.Dict[str, typing.Any],
                  ],
                  *,
                  subgroup: str = None,
                  private: bool = False) -> audfactory.Lookup:
    r"""Extend table with new parameters and return it.

    Args:
        name: model name
        version: version string
        new_params: a dictionary with parameters (keys) and default values.
            If a list of parameter names is given instead, the default value
            will be `None`
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private

    """
    group_id, repository = _server(name, subgroup, private)
    lookup = audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )
    lookup.extend(new_params)
    return lookup


def get_lookup_table(name: str,
                     version: str = None,
                     *,
                     subgroup: str = None,
                     private: bool = False) -> audfactory.Lookup:
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
    group_id, repository = _server(name, subgroup, private)
    lookup = audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )
    return lookup


def get_model_id(name: str,
                 params: typing.Dict[str, typing.Any],
                 version: str = None,
                 *,
                 subgroup: str = None,
                 private: bool = False) -> str:
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
    group_id, repository = _server(name, subgroup, private)
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


def get_model_url(name: str,
                  uid: str,
                  *,
                  subgroup: str = None,
                  private: bool = False) -> str:
    r"""Return model url.

    Args:
        name: model name
        uid: unique model identifier
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private

    """
    group_id, repository = _server(name, subgroup, private)
    versions = audfactory.Lookup.versions(
        group_id,
        repository=repository,
    )
    for version in versions:
        lookup = audfactory.Lookup(
            group_id,
            version=version,
            repository=repository,
        )
        if uid in [row[0] for row in lookup.table[1:]]:
            server_url = audfactory.server_url(group_id,
                                               name=uid,
                                               repository=repository,
                                               version=version)
            return f'{server_url}/{uid}-{version}.zip'

    raise RuntimeError(f"A model with id '{uid}' does not exist")


def get_params(name: str,
               version: str = None,
               *,
               subgroup: str = None,
               private: bool = False) -> typing.List[str]:
    r"""Return list of parameters.

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
    group_id, repository = _server(name, subgroup, private)
    lookup = audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )
    return lookup.columns


def latest_version(name: str,
                   params: typing.Dict[str, typing.Any] = None,
                   *,
                   subgroup: str = None,
                   private: bool = False) -> str:
    r"""Return latest version.

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
    group_id, repository = _server(name, subgroup, private)
    version = audfactory.Lookup.latest_version(
        group_id,
        params=params,
        repository=repository,
    )
    return version


def load(name: str,
         params: typing.Dict[str, typing.Any],
         version: str = None,
         *,
         subgroup: str = None,
         private: bool = False,
         force: bool = False,
         root: str = None,
         verbose: bool = False) -> str:
    r"""Download a model and return folder.

    .. note:: If ``root`` is not set, the model is downloaded to the default
        cache folder (see :meth:`audmodel.get_default_cache_root`). If the
        model already exists in the cache, the download is skipped (unless
        ``force`` is set).

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
        force: download model even if it exists already
        root: store model within this folder
        verbose: show verbose output

    Raises:
        RuntimeError: if model does not exist

    """
    group_id, repository = _server(name, subgroup, private)
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
    uid = lookup.find(params)
    root = audeer.safe_path(root or get_default_cache_root())
    root = os.path.join(root, audfactory.group_id_to_path(group_id),
                        lookup.version)
    root = utils.download_folder(root, group_id, repository, uid,
                                 lookup.version, force=force, verbose=verbose)
    return root


def load_by_id(name: str,
               uid: str,
               *,
               subgroup: str = None,
               private: bool = False,
               force: bool = False,
               root: str = None,
               verbose: bool = False) -> str:
    r"""Download a model by id and return model folder.

    .. note:: If ``root`` is not set, the model is downloaded to the default
        cache folder (see :meth:`audmodel.get_default_cache_root`). If the
        model already exists in the cache, the download is skipped (unless
        ``force`` is set).

    Args:
        name: name of model
        uid: unique model identifier
        subgroup: extend group id to
            :attr:`audmodel.config.GROUP_ID`.<subgroup>. You can increase
            the depth by using dot-notation, e.g. setting
            ``subgroup=foo.bar`` will result in
            `com.audeering.models.foo.bar`
        private: repository is private
        force: download model even if it exists already
        root: store model within this folder
        verbose: show verbose output

    Raises:
        RuntimeError: if model does not exist

    """
    group_id, repository = _server(name, subgroup, private)

    versions = audfactory.Lookup.versions(
        group_id,
        repository=repository,
    )
    for version in versions:
        lookup = audfactory.Lookup(
            group_id,
            version=version,
            repository=repository,
        )
        if uid in [row[0] for row in lookup.table[1:]]:
            root = audeer.safe_path(root or get_default_cache_root())
            root = os.path.join(root, audfactory.group_id_to_path(group_id),
                                lookup.version)
            root = utils.download_folder(root, group_id, repository, uid,
                                         lookup.version, force=force,
                                         verbose=verbose)
            return root

    raise RuntimeError(f"A model with id '{uid}' does not exist")


def publish(root: str,
            name: str,
            params: typing.Dict[str, typing.Any],
            version: str,
            *,
            subgroup: str = None,
            private: bool = False,
            create: bool = True,
            force: bool = False,
            verbose: bool = False) -> str:
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
    group_id, repository = _server(name, subgroup, private)
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
    utils.upload_folder(root, group_id, repository,
                        uid, version, force=force, verbose=verbose)
    return uid


def remove(name: str,
           params: typing.Dict[str, typing.Any],
           version: str,
           *,
           subgroup: str = None,
           private: bool = False) -> str:
    r"""Remove a model and return its unique model identifier.

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
    group_id, repository = _server(name, subgroup, private)
    lookup = audfactory.Lookup(
        group_id,
        version=version,
        repository=repository,
    )
    uid = lookup.remove(params)
    url = _url_entry(group_id, repository, uid, version)
    audfactory.artifactory_path(url).parent.parent.rmdir()
    return uid


def versions(name: str,
             params: typing.Dict[str, typing.Any] = None,
             *,
             subgroup: str = None,
             private: bool = False) -> typing.Sequence[str]:
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
    group_id, repository = _server(name, subgroup, private)
    versions = audfactory.Lookup.versions(
        group_id,
        name=config.LOOKUP_TABLE_NAME,
        params=params,
        repository=repository,
    )
    return versions


def _server(name: str, subgroup: str, private: bool) -> (str, str):
    group_id = f'{config.GROUP_ID}.{subgroup}.{name}' \
        if subgroup is not None else f'{config.GROUP_ID}.{name}'
    repository = config.REPOSITORY_PRIVATE if private \
        else config.REPOSITORY_PUBLIC
    return group_id, repository


def _url_entry(group_id: str, repository: str, name: str, version: str) -> str:
    server_url = audfactory.server_url(group_id,
                                       name=name,
                                       repository=repository,
                                       version=version)
    return f'{server_url}/{name}-{version}.zip'
