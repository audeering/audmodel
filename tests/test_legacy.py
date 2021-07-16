import os

import pytest

import audbackend
import audfactory
import audmodel


PARAMS = {'foo': 'bar'}
SUBGROUP = f'{pytest.ID}.legacy'
VERSION = '1.0.0'


def test_legacy():

    audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
    audmodel.config.LEGACY_REPOSITORY_PUBLIC = 'unittests-public-local'
    audmodel.config.REPOSITORIES = [
        audbackend.Repository(
            'unittests-public-local',
            'https://artifactory.audeering.com/artifactory',
            'artifactory',
        ),
    ]

    uid = audmodel.core.legacy.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        PARAMS,
        VERSION,
        subgroup=SUBGROUP,
    )
    assert uid == audmodel.legacy_uid(
        pytest.NAME,
        PARAMS,
        VERSION,
        subgroup=SUBGROUP,
    )

    # read from backend
    assert audmodel.version(uid) == VERSION
    assert audmodel.versions(uid) == [VERSION]
    assert audmodel.latest_version(uid) == VERSION

    # download to cache and read from there
    assert isinstance(audmodel.author(uid), str)
    assert isinstance(audmodel.date(uid), str)
    assert audmodel.exists(uid)
    assert audmodel.latest_version(uid) == VERSION
    assert audmodel.meta(uid) == {}
    assert audmodel.parameters(uid) == PARAMS
    assert audmodel.url(uid, header=True)
    assert audmodel.version(uid) == VERSION
    assert audmodel.versions(uid) == [VERSION]

    root = audmodel.load(uid)
    assert os.path.exists(root)

    url = audmodel.url(uid)
    path = audfactory.path(url).parent
    if path.exists():
        path.rmdir()

    audmodel.config.REPOSITORIES = pytest.REPOSITORIES
