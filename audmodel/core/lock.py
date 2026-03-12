from contextlib import ExitStack
from contextlib import contextmanager
import os
import warnings

from filelock import FileLock
from filelock import Timeout

import audeer


def _acquire_with_umask(lock, *, timeout):
    """Acquire lock with group-write friendly umask.

    ``filelock.FileLock`` may create the lock file
    during acquisition.
    We set umask to ``0o002``
    to ensure the lock file is created
    with group-write permissions,
    which is needed in shared caches.

    """
    old_mask = os.umask(0o002)
    try:
        lock.acquire(timeout=timeout)
    finally:
        os.umask(old_mask)


@contextmanager
def lock(
    paths: list[str],
    *,
    timeout: float = 10,
    warn: bool = True,
):
    """Create lock for given paths.

    Args:
        paths: files or folders to acquire lock
        timeout: maximum time in seconds
            before giving up acquiring a lock.
            If timeout is reached,
            an exception is raised
        warn: if ``True``
            a warning is shown to the user
            if the lock cannot be acquired
    Raises:
        :class:`filelock.Timeout`: if a timeout is reached

    """
    lock_files = _lock_files(paths)
    locks = [FileLock(f, timeout=timeout) for f in lock_files]
    with ExitStack() as stack:
        for lock, f in zip(locks, lock_files):
            acquired = False
            if warn:
                try:
                    _acquire_with_umask(lock, timeout=0)
                    acquired = True
                except Timeout:
                    warnings.warn(
                        f"Could not acquire lock '{f}'; retrying for {timeout}s."
                    )
            if not acquired:
                _acquire_with_umask(lock, timeout=timeout)
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
            old_mask = os.umask(0o002)
            try:
                audeer.touch(lock_file)
            finally:
                os.umask(old_mask)
        lock_files.append(lock_file)
    return lock_files
