import pytest

import audmodel


@pytest.fixture(autouse=True)
def add_audb_with_public_data(doctest_namespace):
    r"""Provide access to the Artifactory repository
    required by some of the docstrings examples.
    As all the unit tests defined under ``tests/*``
    run on local file system,
    we switch to the Artifactory repository here
    with the help of the ``doctest_namespace`` fixture.
    The ``conftest.py`` file has to be in the same folder
    as the code file where the docstring is defined.
    """
    audmodel.config.BACKEND_HOST = (
        'artifactory',
        'https://artifactory.audeering.com/artifactory',
    )
    doctest_namespace['audmodel'] = audmodel
    yield
    audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
