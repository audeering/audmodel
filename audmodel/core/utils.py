import collections
from collections.abc import Sequence
import datetime
import getpass
import os
import re

import audeer


UID_LEGACY_PATERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
UID_SHORT_PATTERN = re.compile(r"^[0-9a-f]{8}$")
UID_VERSION_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9][A-Za-z0-9.+-]*$")
VALID_ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def create_header(
    uid: str,
    *,
    author: str | None,
    date: datetime.date | None,
    name: str,
    parameters: dict[str, object],
    subgroup: str,
    version: str,
) -> dict[str, dict[str, object]]:
    r"""Create header dictionary."""
    return {
        "author": author or getpass.getuser(),
        "date": date or datetime.date.today(),
        "name": name,
        "parameters": parameters,
        "subgroup": subgroup,
        "version": version,
    }


def valid_alias(alias: str) -> bool:
    r"""Check if alias is valid name.

    Args:
        alias: alias name

    Returns:
        ``True`` if alias is valid name

    """
    return bool(VALID_ALIAS_PATTERN.fullmatch(alias)) and is_alias(alias)


def is_alias(uid: str) -> bool:
    r"""Check if uid is an alias name.

    An alias is any string that doesn't match the UID formats:
    - 8-character hexadecimal short ID (e.g., "d4e9c65b")
    - short ID with version (e.g., "d4e9c65b-3.0.0")
    - 36-character legacy ID (UUID format with dashes)

    Additionally, strings that look like they're intended to be UIDs
    (e.g., lower case and all hex digits)
    are NOT treated as aliases, even if invalid.

    Args:
        uid: potential alias or UID

    Returns:
        ``True`` if the string is an alias, ``False`` if it's a UID

    """
    return not (
        UID_SHORT_PATTERN.fullmatch(uid)
        or UID_LEGACY_PATERN.fullmatch(uid)
        or UID_VERSION_PATTERN.fullmatch(uid)
    )


def is_legacy_uid(uid: str) -> bool:
    r"""Check if uid has old format."""
    return len(uid) == 36


def is_short_uid(uid: str) -> bool:
    r"""Check if uid is short ID."""
    return len(uid) == 8


def scan_files(root: str) -> Sequence[str]:
    r"""Helper function to find all files in directory."""

    def help(root: str, sub_dir: str = ""):
        for entry in os.scandir(root):
            if entry.is_dir(follow_symlinks=False):
                yield from help(entry.path, os.path.join(sub_dir, entry.name))
            else:
                yield sub_dir, entry.name

    return [os.path.join(sub, file) for sub, file in help(root, "")]


def short_id(
    name: str,
    params: dict[str, object],
    subgroup: str | None,
) -> str:
    r"""Return short model ID."""
    subgroup = subgroup or ""
    name = f"{subgroup}.{name}"
    params = {key: params[key] for key in sorted(params)}
    unique_string = name + str(params)
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
        if (
            (k in d_dst)
            and (isinstance(d_dst[k], dict))
            and (isinstance(d_src[k], collections.abc.Mapping))
        ):
            update_dict(d_dst[k], d_src[k])
        else:
            d_dst[k] = d_src[k]
