import pytest

import audbackend
import audmodel


@pytest.fixture(autouse=True)
def docstring_examples(doctest_namespace):  # pragma: no cover
    r"""Provide access to the Artifactory repository
    required by some of the docstrings examples.
    As all the unit tests defined under ``tests/*``
    run on local file system,
    we switch to the Artifactory repository here
    with the help of the ``doctest_namespace`` fixture.
    The ``conftest.py`` file has to be in the same folder
    as the code file where the docstring is defined.
    """
    repository = audbackend.Repository(
        'models-local',
        'https://artifactory.audeering.com/artifactory',
        'artifactory',
    )
    audmodel.config.REPOSITORIES = [
        repository,
    ]
    doctest_namespace['audmodel'] = audmodel
    subgroup = 'audmodel.docstring'
    for version, meta in pytest.META.items():
        uid = audmodel.uid(
            pytest.NAME,
            pytest.PARAMS,
            version,
            subgroup=subgroup,
        )
        if not audmodel.exists(uid):
            audmodel.publish(
                pytest.MODEL_ROOT,
                pytest.NAME,
                pytest.PARAMS,
                version,
                author=pytest.AUTHOR,
                date=pytest.DATE,
                meta=meta,
                repository=repository,
                subgroup=subgroup,
            )
    yield
    audmodel.config.REPOSITORIES = pytest.REPOSITORIES
