import pytest

import audmodel


@pytest.fixture(autouse=True)
def docstring_examples(doctest_namespace):  # pragma: no cover
    r"""Publish model for doctests."""
    repository = pytest.REPOSITORIES[0]
    audmodel.config.REPOSITORIES = [repository]
    subgroup = "audmodel.dummy.cnn"
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
    # Make model root and repo variables available in doctests
    doctest_namespace["model_root"] = pytest.MODEL_ROOT
    doctest_namespace["repository"] = repository
    yield
    audmodel.config.REPOSITORIES = pytest.REPOSITORIES
