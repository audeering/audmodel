import os
import pytest
import uuid

import audeer
import audfactory
import audmodel


audmodel.config.REPOSITORY_PRIVATE = 'unittests-public-local'

pytest.SUBGROUP = f'audmodel.{audeer.uid()}'
pytest.ROOT = os.path.dirname(os.path.realpath(__file__))
pytest.NAME = 'audmodel'
pytest.PRIVATE = True
pytest.COLUMNS = [
    'property1',
    'property2',
    'property3',
]
pytest.PARAMS = [
    {
        pytest.COLUMNS[0]: 'foo',
        pytest.COLUMNS[1]: 'bar',
        pytest.COLUMNS[2]: idx,
    } for idx in range(3)
]
pytest.VERSION = '1.0.0'


def cleanup():
    group_id = f'{audmodel.config.GROUP_ID}.{pytest.SUBGROUP}'
    repository = f'{audmodel.config.REPOSITORY_PRIVATE}'
    path = audfactory.artifactory_path(
        audfactory.server_url(group_id, name=pytest.NAME,
                              repository=repository)).parent
    if path.exists():
        path.rmdir()


@pytest.fixture(scope='session', autouse=True)
def cleanup_session():
    cleanup()
    yield


@pytest.fixture(scope='module', autouse=True)
def cleanup_test():
    yield
    cleanup()


@pytest.fixture(scope='module')
def create():
    uids = []
    for params in pytest.PARAMS:
        uid = audmodel.publish(
            pytest.ROOT,
            pytest.NAME,
            params,
            pytest.VERSION,
            subgroup=pytest.SUBGROUP,
            private=pytest.PRIVATE,
            create=True,
        )
        uids.append(uid)
    pytest.UIDS = uids
    yield
