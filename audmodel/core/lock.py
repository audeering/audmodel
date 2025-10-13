from contextlib import ExitStack
from contextlib import contextmanager
import os
import warnings

from filelock import FileLock
from filelock import Timeout

import audeer


@contextmanager
def lock(paths, *, timeout=86400, warning_timeout=2):
    # reuse your existing function
    lock_files = _lock_files(paths)
    locks = [FileLock(f, timeout=timeout) for f in lock_files]
    with ExitStack() as stack:
        for lock, f in zip(locks, lock_files):
            remaining_time = timeout
            acquired = False
            if warning_timeout < timeout:
                try:
                    lock.acquire(timeout=warning_timeout)
                    acquired = True
                except Timeout:
                    remaining_time = timeout - warning_timeout
                    warnings.warn(
                        f"Lock '{f}' delayed; retrying for {remaining_time}s."
                    )
            if not acquired:
                lock.acquire(timeout=remaining_time)
            stack.enter_context(lock)
        yield


def _lock_files(paths: list[str]) -> list[str]:
    """Create lock files if not existent.

    The lock files are created outside the folder,
    to allow to delete/overwrite the folder
    by the process.

    Args:
        paths: files or folders that should be locked

    Returns:
        path to lock files

    """
    lock_files = []
    paths = [audeer.path(path) for path in sorted(audeer.to_list(paths))]
    for path in paths:
        dirname = audeer.mkdir(os.path.dirname(path))
        basename = os.path.basename(path)
        lock_file = audeer.path(dirname, f".{basename}.lock")
        if not os.path.exists(lock_file):
            audeer.touch(lock_file)
        lock_files.append(lock_file)
    return lock_files
