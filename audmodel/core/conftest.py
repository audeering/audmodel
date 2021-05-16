import pytest

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
    audmodel.config.BACKEND_HOST = (
        'artifactory',
        'https://artifactory.audeering.com/artifactory',
    )
    doctest_namespace['audmodel'] = audmodel
    subgroup = 'audmodel.docstring'
    uid = audmodel.uid(
        pytest.NAME,
        pytest.PARAMS,
        subgroup=subgroup,
    )
    for version, meta in pytest.META.items():
        if not audmodel.exists(uid, version=version):
            audmodel.publish(
                pytest.MODEL_ROOT,
                pytest.NAME,
                pytest.PARAMS,
                version,
                author=pytest.AUTHOR,
                date=pytest.DATE,
                meta=meta,
                subgroup=subgroup,
                private=False,
            )
    yield
    audmodel.config.BACKEND_HOST = pytest.BACKEND_HOST
