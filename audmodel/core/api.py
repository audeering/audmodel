import typing
import os

import pandas as pd

import audeer

from .config import config
from .lookup import Lookup
from . import utils


def create_lookup_table(name: str,
                        columns: typing.Sequence[str],
                        version: str,
                        *,
                        private: bool = False,
                        force: bool = False) -> str:
    return Lookup.create(name, columns, version, private=private, force=force)


def get_default_cache_root() -> str:
    return os.environ.get('AUDMODEL_CACHE_ROOT') or config.AUDMODEL_CACHE_ROOT


def delete_lookup_table(name: str,
                        version: str,
                        *,
                        private: bool = False,
                        force: bool = False) -> None:
    Lookup.delete(name, version, private=private, force=force)


def get_lookup_table(name: str,
                     version: str = None,
                     *,
                     private: bool = False) -> pd.DataFrame:
    return Lookup(name, version, private=private).table


def get_model_id(name: str,
                 params: typing.Dict[str, typing.Any],
                 version: str = None,
                 *,
                 private: bool = False) -> str:
    return Lookup(name, version, private=private).find(params)


def latest_version(name: str,
                   *,
                   private: bool = False) -> str:
    return Lookup.latest_version(name, private=private)


def load(name: str,
         params: typing.Dict[str, typing.Any],
         version: str = None,
         *,
         private: bool = False,
         force: bool = False,
         root: str = None) -> str:
    group_id = f'{config.GROUP_ID}.{name}'
    repository = config.REPOSITORY_PRIVATE if private \
        else config.REPOSITORY_PUBLIC
    lu = Lookup(name, version, private=private)
    uid = lu.find(params)
    root = audeer.safe_path(root or get_default_cache_root())
    root = os.path.join(root, name, lu.version)
    root = utils.download_folder(root,
                                 group_id,
                                 repository,
                                 uid,
                                 lu.version,
                                 force=force)
    return root


def load_by_id(name: str,
               uid: str,
               *,
               private: bool = False,
               force: bool = False,
               root: str = None) -> str:
    group_id = f'{config.GROUP_ID}.{name}'
    repository = config.REPOSITORY_PRIVATE if private \
        else config.REPOSITORY_PUBLIC

    versions = Lookup.versions(name, private=private)
    for version in versions:
        lu = Lookup(name, version, private=private)
        if uid in lu.table.index.to_list():
            root = audeer.safe_path(root or get_default_cache_root())
            root = os.path.join(root, name, lu.version)
            root = utils.download_folder(root,
                                         group_id,
                                         repository,
                                         uid,
                                         lu.version,
                                         force=force)
            return root

    raise RuntimeError(f"A model with id '{uid}' does not exist")


def publish(root: str,
            name: str,
            params: typing.Dict[str, typing.Any],
            version: str,
            *,
            create: bool = True,
            private: bool = False,
            force: bool = False) -> str:

    if not Lookup.exists(name, version, private=private):
        if create:
            create_lookup_table(name, list(params.keys()), version,
                                private=private)
        else:
            raise RuntimeError(f"A lookup table for '{name}' and "
                               f"'{version}' does not exist yet.")

    lu = Lookup(name, version, private=private)
    uid = lu.append(params)
    url = utils.upload_folder(root, lu.group_id, lu.repository,
                              uid, version, force=force)
    return url


def remove(name: str,
           params: typing.Dict[str, typing.Any],
           version: str,
           *,
           private: bool = False) -> str:
    return Lookup(name, version, private=private).remove(params)


def versions(name: str,
             *,
             private: bool = False) -> typing.Sequence[str]:
    return Lookup.versions(name, private=private)
