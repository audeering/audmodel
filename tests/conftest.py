import os
import pytest
import uuid

import audfactory
import audmodel


pytest.SUBGROUP = f'audmodel.{str(uuid.uuid1())}'
pytest.ROOT = os.path.dirname(os.path.realpath(__file__))
pytest.NAME = 'audmodel'
pytest.COLUMNS = ['property1', 'property2', 'property3']
pytest.PARAMS = [
    {
        'property1': 'foo',
        'property2': 'bar',
        'property3': idx,
    } for idx in range(3)
]
pytest.VERSION = '1.0.0'


def cleanup():
    group_id = f'{audmodel.config.GROUP_ID}.{pytest.SUBGROUP}'
    repository = f'{audmodel.config.REPOSITORY_PUBLIC}'
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
    for params in pytest.PARAMS:
        pytest.UID = audmodel.publish(pytest.ROOT, pytest.NAME, params,
                                      pytest.VERSION, subgroup=pytest.SUBGROUP,
                                      create=True)
    yield
