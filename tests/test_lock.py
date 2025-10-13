import re
import threading
import time

import filelock
import pytest

import audeer

from audmodel.core.lock import Lock


event = threading.Event()


def job(lock, wait, sleep):
    if wait:
        event.wait()  # wait for another thread to enter the lock
    with lock:
        if not wait:
            event.set()  # notify waiting threads to enter the lock
        time.sleep(sleep)
        # Finished without timeout
        return 1
    return 0


def test_lock(tmpdir):
    # create two lock folders

    lock_folders = [audeer.mkdir(tmpdir, str(idx)) for idx in range(2)]

    # lock 1 and 2

    lock_1 = Lock(lock_folders[0])
    lock_2 = Lock(lock_folders[1])

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

    lock_1 = Lock(lock_folders[0])
    lock_2 = Lock(lock_folders[1])
    lock_12 = Lock(lock_folders)

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

    lock_1 = Lock(lock_folders[0])
    lock_12 = Lock(lock_folders)

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

    lock_1 = Lock(lock_folders[0])
    lock_12 = Lock(lock_folders, timeout=0)

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

    lock_1 = Lock(lock_folders[0])
    lock_12 = Lock(lock_folders)

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

    lock_1 = Lock(lock_folders[0], timeout=0)
    lock_12 = Lock(lock_folders)

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

    lock_1 = Lock(lock_folders[0])
    lock_2 = Lock(lock_folders[1], timeout=0)
    lock_12 = Lock(lock_folders)

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
    assert result == [1, 0, 1]


def test_lock_warning_and_failure(tmpdir):
    """Test user warning and lock failure messages."""
    path = audeer.path(tmpdir, "file.txt")
    # Create lock file to force failing acquiring of lock
    lock_file = audeer.touch(tmpdir, ".file.txt.lock")
    lock_error = filelock.Timeout
    lock_error_msg = f"The file lock '{lock_file}' could not be acquired."
    warning_msg = (
        "Lock could not be acquired immediately.\n"
        "Another user might loading the same model.\n"
        "Still trying for 0.1 more seconds..."
    )
    with pytest.warns(UserWarning, match=re.escape(warning_msg)):
        with pytest.raises(lock_error, match=re.escape(lock_error_msg)):
            with Lock(path, warning_timeout=0.1, timeout=0.2):
                pass
