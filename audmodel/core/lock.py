from collections.abc import Sequence
import os
import types
import warnings

import filelock

import audeer


class Lock:
    def __init__(
        self,
        paths: str | Sequence[str],
        *,
        timeout: float = 86400,  # 24 h
        warning_timeout: float = 2,
    ):
        r"""Lock one or more files or folders.

        Waits until all locks can be acquired.
        While locked a path `a/b/c` is locked
        a file `a/b/.c.lock` will be created.

        Args:
            paths: path to one or more files or folders that should be locked
            timeout: maximum time in seconds
                before giving up acquiring a lock to the cache folder.
                If timeout is reached,
                an exception is raised
            warning_timeout: time in seconds
                after which a warning is shown to the user
                that the lock could not yet get acquired

        Raises:
            :class:`filelock.Timeout`: if a timeout is reached

        """
        self.lock_files = self._lock_files(paths)
        self.locks = [filelock.FileLock(file) for file in self.lock_files]
        self.timeout = timeout
        self.warning_timeout = warning_timeout

    def __enter__(self) -> "Lock":
        r"""Acquire the lock(s)."""
        for lock, lock_file in zip(self.locks, self.lock_files):
            remaining_time = self.timeout
            acquired = False
            # First try to acquire lock in warning_timeout time
            if self.warning_timeout < self.timeout:
                try:
                    lock.acquire(timeout=self.warning_timeout)
                    acquired = True
                except filelock.Timeout:
                    warnings.warn(
                        f"Lock could not be acquired immediately.\n"
                        "Another user might loading the same model.\n"
                        f"Still trying for {self.timeout - self.warning_timeout:.1f} "
                        "more seconds...\n"
                    )
                    remaining_time = self.timeout - self.warning_timeout

            if not acquired:
                try:
                    lock.acquire(timeout=remaining_time)
                except filelock.Timeout:
                    warnings.warn(
                        "Lock could not be acquired. Timeout exceeded.",
                        category=UserWarning,
                    )

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: types.TracebackType | None,
    ) -> None:
        """Release the lock(s)."""
        for lock in self.locks:
            lock.release()

    def __del__(self) -> None:
        """Called when the lock object is deleted."""
        for lock in self.locks:
            lock.release(force=True)

    def _lock_files(self, paths: list[str]) -> list[str]:
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
        paths = [audeer.path(path) for path in audeer.to_list(paths)]
        for path in paths:
            dirname = audeer.mkdir(os.path.dirname(path))
            basename = os.path.basename(path)
            lock_file = audeer.path(dirname, f".{basename}.lock")
            if not os.path.exists(lock_file):
                audeer.touch(lock_file)
            lock_files.append(lock_file)
        return lock_files
