import os
import typing
import tempfile
import uuid

import pandas as pd

import audfactory
import audeer

from .config import config


temp_name = tempfile._get_candidate_names()


class Lookup:

    def __init__(self,
                 name: str,
                 version: str = None,
                 *,
                 private: bool = False):

        self.group_id = f'{config.GROUP_ID}.{name}'
        self.repository = config.REPOSITORY_PRIVATE if private \
            else config.REPOSITORY_PUBLIC

        if version is None:
            version = Lookup.latest_version(name, private=private)
        elif not Lookup.exists(name, version, private=private):
            raise RuntimeError(f"Lookup table '{name}-{version}' "
                               f"does not exist yet.")

        self.version = version
        self.url = _url_table(self.group_id, self.repository, version)

    @property
    def table(self) -> pd.DataFrame:
        return _download(self.group_id, self.repository, self.version)

    def append(self, params: typing.Dict[str, typing.Any]) -> str:

        df = self.table

        if self.contains(params):
            raise RuntimeError(f"Entry for '{params}' already exists.")

        uid = _uid()
        s = pd.Series(params, name=uid)
        s.sort_index(inplace=True)

        if not s.index.equals(df.columns):
            raise RuntimeError(f"Table columns '{df.columns}' do "
                               f"not match parameters '{params}'.")

        df = df.append(s)
        _upload(df, self.group_id, self.repository, self.version)

        return uid

    def clear(self) -> None:

        df = self.table
        for uid in df.index:
            url = _url_entry(self.group_id, self.repository, uid, self.version)
            audfactory.artifactory_path(url).parent.parent.rmdir()
        df.drop(index=df.index, inplace=True)
        _upload(df, self.group_id, self.repository, self.version)

    def contains(self, params: typing.Dict[str, typing.Any]) -> bool:
        try:
            self.find(params)
        except RuntimeError:
            return False
        return True

    def find(self, params: typing.Dict[str, typing.Any]) -> str:

        df = self.table

        s = pd.Series(params)
        s.sort_index(inplace=True)
        for uid, row in df.iterrows():
            if row.equals(s):
                return str(uid)

        raise RuntimeError(f"Entry for '{params}' does not exist.")

    def remove(self, params: typing.Dict[str, typing.Any]) -> str:

        df = self.table
        uid = self.find(params)
        url = _url_entry(self.group_id, self.repository,
                         uid, self.version)
        audfactory.artifactory_path(url).parent.parent.rmdir()
        df.drop(index=uid, inplace=True)
        _upload(df, self.group_id, self.repository, self.version)

        return uid

    @staticmethod
    def create(name: str,
               columns: typing.Sequence[str],
               version: str,
               *,
               private: bool = False,
               force: bool = False) -> str:

        group_id = f'{config.GROUP_ID}.{name}'
        repository = config.REPOSITORY_PRIVATE if private \
            else config.REPOSITORY_PUBLIC

        if force or not Lookup.exists(name, version, private=private):
            df = pd.DataFrame(index=pd.Index([],
                                             name=config.LOOKUP_TABLE_INDEX),
                              columns=sorted(columns))
            _upload(df, group_id, repository, version)
        else:
            raise RuntimeError(f"Lookup table '{name}-{version}' "
                               f"exists already.")

        return _url_table(group_id, repository, version)

    @staticmethod
    def delete(name: str,
               version: str,
               *,
               private: bool = False,
               force: bool = True):
        lu = Lookup(name, version, private=private)
        if not lu.table.empty:
            if not force:
                raise RuntimeError(
                    f"Cannot remove lookup table '{name}-{version}' "
                    f"if it is not empty.")
            lu.clear()

        audfactory.artifactory_path(lu.url).parent.rmdir()

    @staticmethod
    def exists(name: str,
               version: str,
               *,
               private: bool = False) -> bool:

        group_id = f'{config.GROUP_ID}.{name}'
        repository = config.REPOSITORY_PRIVATE if private \
            else config.REPOSITORY_PUBLIC

        try:
            versions = audfactory.versions(group_id,
                                           config.LOOKUP_TABLE_NAME,
                                           repository=repository)
        except RuntimeError:
            versions = []

        return version in versions

    @staticmethod
    def latest_version(name: str,
                       *,
                       private: bool = False) -> str:
        return Lookup.versions(name, private=private)[-1]

    @staticmethod
    def versions(name: str,
                 *,
                 private: bool = False) -> list:
        group_id = f'{config.GROUP_ID}.{name}'
        repository = config.REPOSITORY_PRIVATE if private \
            else config.REPOSITORY_PUBLIC
        return audfactory.versions(group_id,
                                   config.LOOKUP_TABLE_NAME,
                                   repository=repository)


def _download(group_id: str,
              repository: str,
              version: str) -> pd.DataFrame:
    path = _path(version)
    url = _url_table(group_id, repository, version)
    path = audfactory.download_artifact(url, path)
    df = pd.read_csv(path, index_col=config.LOOKUP_TABLE_INDEX)
    os.remove(path)
    return df


def _path(version: str) -> str:
    root = os.path.join(tempfile._get_default_tempdir(), next(temp_name))
    audeer.mkdir(root)
    path = os.path.join(root, f'{config.LOOKUP_TABLE_NAME}-{version}'
                              f'.{config.LOOKUP_TABLE_EXT}')
    return path


def _upload(df: pd.DataFrame,
            group_id: str,
            repository: str,
            version: str) -> None:
    path = _path(version)
    df.to_csv(path)
    audfactory.upload_artifact(path,
                               repository,
                               group_id,
                               config.LOOKUP_TABLE_NAME,
                               version=version)
    os.remove(path)


def _uid() -> str:
    return str(uuid.uuid1())


def _url_table(group_id: str,
               repository: str,
               version: str) -> str:
    server_url = audfactory.server_url(group_id,
                                       name=config.LOOKUP_TABLE_NAME,
                                       repository=repository,
                                       version=version)
    url = f'{server_url}/{config.LOOKUP_TABLE_NAME}-{version}.' \
          f'{config.LOOKUP_TABLE_EXT}'
    return url


def _url_entry(group_id: str,
               repository: str,
               name: str,
               version: str) -> str:
    server_url = audfactory.server_url(group_id,
                                       name=name,
                                       repository=repository,
                                       version=version)
    url = f'{server_url}/{name}-{version}.zip'
    return url
