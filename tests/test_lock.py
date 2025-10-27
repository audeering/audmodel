import re
import threading
import time

import filelock
import pytest

import audeer

from audmodel.core.lock import lock


event = threading.Event()


def job(lock, wait, sleep):
    if wait:
        event.wait()  # wait for another thread to enter the lock
    try:
        with lock:
            if not wait:
                event.set()  # notify waiting threads to enter the lock
            time.sleep(sleep)
    except filelock.Timeout:
        return 0
    return 1


def test_lock(tmpdir):
    # create two lock folders

    lock_folders = [audeer.mkdir(tmpdir, str(idx)) for idx in range(2)]

    # lock 1 and 2

    lock_1 = lock(lock_folders[0], warn=False)
    lock_2 = lock(lock_folders[1], warn=False)

    event.clear()
    result = audeer.run_tasks(
        job,
        [
            ([lock_1, False, 0], {}),
            ([lock_2, False, 0], {}),
        ],
        num_workers=2,
    )
    assert result == [1, 1]

    # lock 1, 2 and 1+2

    lock_1 = lock(lock_folders[0], warn=False)
    lock_2 = lock(lock_folders[1], warn=False)
    lock_12 = lock(lock_folders, warn=False)

    result = audeer.run_tasks(
        job,
        [
            ([lock_1, False, 0], {}),
            ([lock_2, False, 0], {}),
            ([lock_12, False, 0], {}),
        ],
        num_workers=3,
    )
    assert result == [1, 1, 1]

    # lock 1, then 1+2 + wait

    lock_1 = lock(lock_folders[0], warn=False)
    lock_12 = lock(lock_folders, warn=False)

    event.clear()
    result = audeer.run_tasks(
        job,
        [
            ([lock_1, False, 0.2], {}),
            ([lock_12, True, 0], {}),
        ],
        num_workers=2,
    )
    assert result == [1, 1]

    # lock 1, then 1+2 + timeout

    lock_1 = lock(lock_folders[0], warn=False)
    lock_12 = lock(lock_folders, warn=False, timeout=0)

    event.clear()
    result = audeer.run_tasks(
        job,
        [
            ([lock_1, False, 0.2], {}),
            ([lock_12, True, 0], {}),
        ],
        num_workers=2,
    )
    assert result == [1, 0]

    # lock 1+2, then 1 + wait

    lock_1 = lock(lock_folders[0], warn=False)
    lock_12 = lock(lock_folders, warn=False)

    event.clear()
    result = audeer.run_tasks(
        job,
        [
            ([lock_1, True, 0], {}),
            ([lock_12, False, 0.2], {}),
        ],
        num_workers=2,
    )
    assert result == [1, 1]

    # lock 1+2, then 1 + timeout

    lock_1 = lock(lock_folders[0], warn=False, timeout=0)
    lock_12 = lock(lock_folders, warn=False)

    event.clear()
    result = audeer.run_tasks(
        job,
        [
            ([lock_1, True, 0], {}),
            ([lock_12, False, 0.2], {}),
        ],
        num_workers=2,
    )
    assert result == [0, 1]

    # lock 1+2, then 1 + wait and 2 + timeout

    lock_1 = lock(lock_folders[0], warn=False)
    lock_2 = lock(lock_folders[1], warn=False, timeout=0)
    lock_12 = lock(lock_folders)

    event.clear()
    result = audeer.run_tasks(
        job,
        [
            ([lock_1, True, 0], {}),
            ([lock_2, True, 0], {}),
            ([lock_12, 0, 0.2], {}),
        ],
        num_workers=3,
    )
    assert set(result) == {0, 1}


def test_lock_warning_and_failure(tmpdir):
    """Test user warning and lock failure messages."""
    path = audeer.path(tmpdir, "file.txt")
    lock_file = audeer.touch(tmpdir, ".file.txt.lock")
    lock_error = filelock.Timeout
    lock_error_msg = f"The file lock '{lock_file}' could not be acquired."
    warning_msg = f"Could not acquire lock '{lock_file}'; retrying for 0.2s."
    # Acquire first lock to force failing second lock
    with lock(path):
        with pytest.warns(UserWarning, match=re.escape(warning_msg)):
            with pytest.raises(lock_error, match=re.escape(lock_error_msg)):
                with lock(path, warn=True, timeout=0.2):
                    pass
