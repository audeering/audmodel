import pytest
import uuid

import audfactory
import audmodel

from .default import default


# create a unique group id to not interrupt
# with other tests running in parallel
audmodel.config.config.GROUP_ID += '.audmodel.' + str(uuid.uuid1())


def cleanup():
    path = audfactory.artifactory_path(
        audfactory.server_url(audmodel.config.config.GROUP_ID,
                              name=default.NAME,
                              repository='models-public-local')).parent
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
    for params in default.PARAMS:
        audmodel.publish(default.ROOT, default.NAME, params,
                         default.VERSION, create=True)
    yield
