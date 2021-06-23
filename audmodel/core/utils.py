
import os
import typing

import audeer

from audmodel.core.config import config


def is_legacy_uid(uid: str) -> bool:
    r"""Check if uid has old format."""
    return len(uid) == 36


def scan_files(root: str) -> typing.Sequence[str]:
    r"""Helper function to find all files in directory."""

    def help(root: str, sub_dir: str = ''):
        for entry in os.scandir(root):
            if entry.is_dir(follow_symlinks=False):
                yield from help(entry.path, os.path.join(sub_dir, entry.name))
            else:
                yield sub_dir, entry.name

    return [os.path.join(sub, file) for sub, file in help(root, '')]


def short_uid(
        name: str,
        params: typing.Dict[str, typing.Any],
        subgroup: typing.Optional[str],
) -> str:
    r"""Return short model ID."""
    group_id = f'{config.GROUP_ID}.{name}' if subgroup is None \
        else f'{config.GROUP_ID}.{subgroup}.{name}'
    params = {key: params[key] for key in sorted(params)}
    unique_string = group_id + str(params)
    return audeer.uid(from_string=unique_string)[-8:]


def split_uid(uid: str) -> (str, str):
    r"""Split uid into short id and version."""
    tokens = uid.split('-')
    short_id = tokens[0]
    version = '-'.join(tokens[1:])
    return short_id, version
