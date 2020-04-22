import typing
import os

import pandas as pd

import audeer
import audfactory

from .config import config
from .lookup import Lookup
from . import utils


def create_lookup_table(name: str,
                        params: typing.Sequence[str],
                        version: str,
                        *,
                        subgroup: str = None,
                        private: bool = False,
                        force: bool = False,
                        verbose: bool = False) -> str:
    r"""Create lookup table and return url.

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
        verbose: show debug messages

    Raises:
        RuntimeError: if table exists already

    """
    return Lookup.create(name, params, version, subgroup=subgroup,
                         private=private, force=force, verbose=verbose)


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
    Lookup.delete(name, version, subgroup=subgroup,
                  private=private, force=force)


def extend_params(name: str,
                  version: str,
                  new_params: typing.Union[
                      str,
                      typing.Sequence[str],
                      typing.Dict[str, typing.Any],
                  ],
                  *,
                  subgroup: str = None,
                  private: bool = False,
                  verbose: bool = False) -> pd.DataFrame:
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
        verbose: show debug messages

    """
    lu = Lookup(name, version, subgroup=subgroup,
                private=private, verbose=verbose)
    return lu.extend(new_params)


def get_lookup_table(name: str,
                     version: str = None,
                     *,
                     subgroup: str = None,
                     private: bool = False,
                     verbose: bool = False) -> pd.DataFrame:
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
        verbose: show debug messages

    Raises:
        RuntimeError: if table does not exist

    """
    return Lookup(name, version, subgroup=subgroup,
                  private=private, verbose=verbose).table


def get_model_id(name: str,
                 params: typing.Dict[str, typing.Any],
                 version: str = None,
                 *,
                 subgroup: str = None,
                 private: bool = False,
                 verbose: bool = False) -> str:
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
        verbose: show debug messages

    Raises:
        RuntimeError: if model does not exist

    """
    if version is None:
        version = latest_version(name, params,
                                 subgroup=subgroup, private=private)
    return Lookup(name, version, subgroup=subgroup,
                  private=private, verbose=verbose).find(params)


def get_model_url(name: str,
                  uid: str,
                  *,
                  subgroup: str = None,
                  private: bool = False,
                  verbose: bool = False) -> str:
    group_id, repository = Lookup.server(name, subgroup, private)
    versions = Lookup.versions(name, subgroup=subgroup, private=private)
    for version in versions:
        lu = Lookup(name, version, subgroup=subgroup, private=private)
        if uid in lu.table.index.to_list():
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
               private: bool = False,
               verbose: bool = False) -> typing.List[str]:
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
        verbose: show debug messages

    Raises:
        RuntimeError: if table does not exist

    """
    return list(get_lookup_table(name, version, subgroup=subgroup,
                                 private=private, verbose=verbose).columns)


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
    return Lookup.latest_version(name, params,
                                 subgroup=subgroup, private=private)


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
        verbose: show debug messages

    Raises:
        RuntimeError: if model does not exist

    """
    if version is None:
        version = latest_version(name, params,
                                 subgroup=subgroup, private=private)
    group_id, repository = Lookup.server(name, subgroup, private)
    lu = Lookup(name, version, subgroup=subgroup,
                private=private, verbose=verbose)
    uid = lu.find(params)
    root = audeer.safe_path(root or get_default_cache_root())
    root = os.path.join(root, audfactory.group_id_to_path(group_id),
                        lu.version)
    root = utils.download_folder(root, group_id, repository, uid,
                                 lu.version, force=force, verbose=verbose)
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
        verbose: show debug messages

    Raises:
        RuntimeError: if model does not exist

    """
    group_id, repository = Lookup.server(name, subgroup, private)

    versions = Lookup.versions(name, subgroup=subgroup, private=private)
    for version in versions:
        lu = Lookup(name, version, subgroup=subgroup, private=private)
        if uid in lu.table.index.to_list():
            root = audeer.safe_path(root or get_default_cache_root())
            root = os.path.join(root, audfactory.group_id_to_path(group_id),
                                lu.version)
            root = utils.download_folder(root, group_id, repository, uid,
                                         lu.version, force=force,
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
        verbose: show debug messages

    Raises:
        RuntimeError: if an artifact exists already

    """
    if not Lookup.exists(name, version, subgroup=subgroup, private=private):
        if create:
            create_lookup_table(name, list(params.keys()), version,
                                subgroup=subgroup, private=private,
                                verbose=verbose)
        else:
            raise RuntimeError(f"A lookup table for '{name}' and "
                               f"'{version}' does not exist yet.")

    lu = Lookup(name, version, subgroup=subgroup,
                private=private, verbose=verbose)
    uid = lu.append(params)
    utils.upload_folder(root, lu.group_id, lu.repository,
                        uid, version, force=force, verbose=verbose)
    return uid


def remove(name: str,
           params: typing.Dict[str, typing.Any],
           version: str,
           *,
           subgroup: str = None,
           private: bool = False,
           verbose: bool = False) -> str:
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
        verbose: show debug messages

    Raises:
        RuntimeError: if model does not exist

    """
    return Lookup(name, version, subgroup=subgroup,
                  private=private, verbose=verbose).remove(params)


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
    return Lookup.versions(name, params, subgroup=subgroup, private=private)
