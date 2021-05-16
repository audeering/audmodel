import datetime
import os

import pytest

import audfactory
import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORY_PUBLIC = 'unittests-public-local'

PARAMS = {'foo': 'bar'}
SUBGROUP = f'{pytest.ID}.legacy'
VERSION = '1.0.0'


def test_legacy():

    audmodel.config.BACKEND_HOST = (
        'artifactory',
        'https://artifactory.audeering.com/artifactory',
    )

    uid = audmodel.core.legacy.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        PARAMS,
        VERSION,
        subgroup=SUBGROUP,
    )

    assert isinstance(audmodel.author(uid), str)
    assert isinstance(audmodel.date(uid), datetime.date)
    assert audmodel.exists(uid)
    assert audmodel.latest_version(uid) == VERSION
    assert audmodel.meta(uid) == {}
    assert audmodel.parameters(uid) == PARAMS
    assert audmodel.versions(uid) == [VERSION]

    root = audmodel.load(uid)
    assert os.path.exists(root)

    url = audmodel.url(uid)
    path = audfactory.path(url).parent
    if path.exists():
        path.rmdir()

    audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
