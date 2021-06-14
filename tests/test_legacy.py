import datetime
import os

import pytest

import audfactory
import audmodel


PARAMS = {'foo': 'bar'}
SUBGROUP = f'{pytest.ID}.legacy'
VERSION = '1.0.0'


def test_legacy():

    audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
    audmodel.config.BACKEND_HOST = (
        'artifactory',
        'https://artifactory.audeering.com/artifactory',
    )
    audmodel.config.REPOSITORY_PUBLIC = 'unittests-public-local'

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

    assert isinstance(audmodel.author(uid), str)
    assert isinstance(audmodel.date(uid), str)
    assert audmodel.exists(uid)
    assert audmodel.latest_version(uid) == VERSION
    assert audmodel.meta(uid) == {}
    assert audmodel.parameters(uid) == PARAMS
    assert audmodel.version(uid) == VERSION
    assert audmodel.versions(uid) == [VERSION]

    root = audmodel.load(uid)
    assert os.path.exists(root)

    url = audmodel.url(uid)
    path = audfactory.path(url).parent
    if path.exists():
        path.rmdir()

    audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
    audmodel.config.REPOSITORY_PUBLIC = 'models-public-local'
