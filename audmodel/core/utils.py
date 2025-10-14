import collections
from collections.abc import Sequence
import datetime
import getpass
import os

import audeer


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


def is_alias(uid: str) -> bool:
    r"""Check if uid is an alias name.

    An alias is any string that doesn't match the UID formats:
    - 8-character hexadecimal short ID
    - 36-character legacy ID (UUID format with dashes)
    - short-id-version format (e.g., "d4e9c65b-3.0.0")

    Additionally, strings that look like they're intended to be UIDs
    (e.g., all hex digits) are NOT treated as aliases, even if invalid.

    Args:
        uid: potential alias or UID

    Returns:
        ``True`` if the string is an alias, ``False`` if it's a UID

    """
    # If it's all hex digits (with optional dashes for UUID format),
    # treat it as a UID attempt, not an alias
    uid_clean = uid.replace("-", "")
    try:
        int(uid_clean, 16)
        # It's all hex, so it's likely meant to be a UID
        return False
    except ValueError:
        # Contains non-hex characters, continue checking
        pass

    # Legacy UID (36 chars in UUID format: 8-4-4-4-12)
    if len(uid) == 36 and uid.count("-") == 4:
        parts = uid.split("-")
        if (
            len(parts[0]) == 8
            and len(parts[1]) == 4
            and len(parts[2]) == 4
            and len(parts[3]) == 4
            and len(parts[4]) == 12
        ):
            return False

    # UID with version (short-id-version format)
    # e.g., "d4e9c65b-3.0.0" or "d4e9c65b-1.0.0-rc1"
    if "-" in uid:
        parts = uid.split("-", 1)
        if len(parts[0]) == 8:
            # Check if first part is hexadecimal
            try:
                int(parts[0], 16)
                return False
            except ValueError:
                pass

    # Everything else is an alias
    return True


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
