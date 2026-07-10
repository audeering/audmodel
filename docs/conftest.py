from doctest import ELLIPSIS
from doctest import NORMALIZE_WHITESPACE
import os

import pytest
import sybil
from sybil.parsers.rest import DocTestParser
from sybil.parsers.rest import PythonCodeBlockParser
from sybil.parsers.rest import SkipParser

import audmodel
from audmodel.core.config import global_config_file
from audmodel.core.config import load_configuration_file


def imports(namespace):
    """Make :mod:`audmodel` available inside the documentation namespace."""
    namespace["audmodel"] = audmodel


@pytest.fixture(scope="module")
def run_in_tmpdir(tmpdir_factory):
    """Execute the whole documentation file inside a persistent tmpdir."""
    tmpdir = tmpdir_factory.mktemp("tmp")
    current_dir = os.getcwd()
    os.chdir(tmpdir)

    yield

    os.chdir(current_dir)


@pytest.fixture(scope="module")
def reset_config():
    """Restore config values that are changed inside the documentation."""
    cache_root = audmodel.config.CACHE_ROOT
    repositories = list(audmodel.config.REPOSITORIES)
    # Other tests set ``AUDMODEL_CACHE_ROOT``,
    # which would take precedence over ``config.CACHE_ROOT``.
    # Remove it here, so the cache folder used in the documentation
    # is the one configured via ``config.CACHE_ROOT``.
    env_cache_root = os.environ.pop("AUDMODEL_CACHE_ROOT", None)

    yield

    audmodel.config.CACHE_ROOT = cache_root
    audmodel.config.REPOSITORIES = repositories
    if env_cache_root is not None:
        os.environ["AUDMODEL_CACHE_ROOT"] = env_cache_root


@pytest.fixture(scope="module")
def default_configuration():
    """Provide the default configuration values.

    Other tests change the values of :class:`audmodel.config`,
    so we restore the default values from the config file here,
    and reset them afterwards.

    """
    cache_root = audmodel.config.CACHE_ROOT
    repositories = audmodel.config.REPOSITORIES

    default = load_configuration_file(global_config_file)
    audmodel.config.CACHE_ROOT = default["cache_root"]
    audmodel.config.REPOSITORIES = [
        audmodel.Repository(repo["name"], repo["host"], repo["backend"])
        for repo in default["repositories"]
    ]

    yield

    audmodel.config.CACHE_ROOT = cache_root
    audmodel.config.REPOSITORIES = repositories


# Collect doctests and code blocks from the documentation.
#
# We use several ``sybil.Sybil`` instances
# to pass different fixtures to different files.
parsers = [
    DocTestParser(optionflags=ELLIPSIS | NORMALIZE_WHITESPACE),
    PythonCodeBlockParser(),
    SkipParser(),
]
pytest_collect_file = sybil.sybil.SybilCollection(
    (
        sybil.Sybil(
            parsers=parsers,
            filenames=["usage.rst"],
            fixtures=["run_in_tmpdir", "reset_config"],
        ),
        sybil.Sybil(
            parsers=parsers,
            filenames=["configuration.rst"],
            fixtures=["default_configuration"],
            setup=imports,
        ),
    )
).pytest()
