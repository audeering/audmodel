import os

import pytest

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

SUBGROUP = f"{pytest.ID}.update"
CACHE_ROOT_ALT = os.path.join(pytest.ROOT, "cache2")


def test_update():
    # publish without meta

    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "1.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        repository=pytest.REPOSITORIES[0],
        subgroup=SUBGROUP,
    )
    assert audmodel.meta(uid) == {}

    # download header to alternate cache

    meta_alt = audmodel.meta(uid, cache_root=CACHE_ROOT_ALT)
    assert meta_alt == {}

    # insert new fields

    meta = {
        "data": {
            "emodb": {
                "version": "1.0.0",
                "format": "wav",
                "mixdown": True,
            }
        },
        "melspec64": {
            "win_dur": "32ms",
            "hop_dur": "10ms",
            "num_fft": 512,
        },
    }
    assert audmodel.update_meta(uid, meta) == meta
    assert audmodel.meta(uid) == meta

    # update existing field

    assert audmodel.meta(uid)["data"]["emodb"]["version"] == "1.0.0"
    meta = {
        "data": {
            "emodb": {
                "version": "2.0.0",
            }
        }
    }
    audmodel.update_meta(uid, meta)
    assert audmodel.meta(uid)["data"]["emodb"]["version"] == "2.0.0"

    # replace meta

    meta = {"replace": "meta"}
    assert audmodel.update_meta(uid, meta, replace=True) == meta
    assert audmodel.meta(uid) == meta

    # verify header is updated in alternate cache

    meta_alt = audmodel.meta(uid, cache_root=CACHE_ROOT_ALT)
    assert meta_alt == meta
