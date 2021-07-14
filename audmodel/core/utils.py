import collections
import datetime
import getpass
import os
import typing

import audeer


def create_header(
        uid: str,
        *,
        author: typing.Optional[str],
        date: typing.Optional[datetime.date],
        meta: typing.Optional[typing.Dict[str, typing.Any]],
        name: str,
        parameters: typing.Dict[str, typing.Any],
        subgroup: str,
        version: str,
) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
    r"""Create header dictionary."""
    return {
        uid: {
            'author': author or getpass.getuser(),
            'date': date or datetime.date.today(),
            'meta': meta or {},
            'name': name,
            'parameters': parameters,
            'subgroup': subgroup,
            'version': version,
        }
    }


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


def short_id(
        name: str,
        params: typing.Dict[str, typing.Any],
        subgroup: typing.Optional[str],
) -> str:
    r"""Return short model ID."""
    group_id = name if subgroup is None \
        else f'{subgroup}.{name}'
    params = {key: params[key] for key in sorted(params)}
    unique_string = group_id + str(params)
    return audeer.uid(from_string=unique_string)[-8:]


def update_dict(
        d_dst: dict,
        d_src: dict,
):
    """Recursive dictionary update.

    Like standard dict.update(),
    but also updates nested keys.

    """
    for k, v in d_src.items():
        if (k in d_dst)\
                and (isinstance(d_dst[k], dict)) \
                and (isinstance(d_src[k], collections.Mapping)):
            update_dict(d_dst[k], d_src[k])
        else:
            d_dst[k] = d_src[k]
