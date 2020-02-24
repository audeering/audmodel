import pytest

import audfactory
import audmodel

from .config import config


def cleanup():
    path = audfactory.artifactory_path(
        audfactory.server_url('com.audeering.models',
                              name=config.NAME,
                              repository='models-public-local'))
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
    for params in config.DEFAULT_PARAMS:
        audmodel.publish(config.ROOT, config.NAME, params,
                         config.DEFAULT_VERSION, create=True)
    yield
