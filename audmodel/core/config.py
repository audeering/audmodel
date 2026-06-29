import os

import oyaml as yaml

import audeer

from audmodel.core.define import CONFIG_FILE
from audmodel.core.define import USER_CONFIG_FILE
from audmodel.core.repository import Repository


CWD = audeer.script_dir()
global_config_file = os.path.join(CWD, CONFIG_FILE)


def load_configuration_file(config_file: str) -> dict:
    r"""Read configuration from YAML file.

    Args:
        config_file: path to configuration file.
            File doesn't have to exist

    Returns:
        dictionary containing configuration entries

    Raises:
        ValueError: if ``repositories`` section is present,
            but empty
        ValueError: if repository has no ``host``
            ``backend``, or ``name`` key

    """
    if not os.path.exists(config_file):
        return {}

    with open(config_file) as cf:
        config = yaml.load(cf, Loader=yaml.BaseLoader)
        if config is None:
            return {}

    # Check that we have provided a valid repositories configuration
    if "repositories" in config:
        if len(config["repositories"]) == 0:
            raise ValueError(
                "You cannot specify an empty 'repositories:' section "
                f"in the configuration file '{USER_CONFIG_FILE}'."
            )
        for repo in config["repositories"]:
            for key in ("host", "backend", "name"):
                if key not in repo:
                    raise ValueError(
                        f"Your repository is missing a '{key}' entry: '{repo}'."
                    )

    return config


def load_config() -> dict:
    """Read configuration from configuration files.

    User config values take precedence over global config values
    when the same setting exists in both files.

    """
    # Global config
    config = load_configuration_file(global_config_file)
    # User config
    user_config = load_configuration_file(audeer.path(USER_CONFIG_FILE))
    config.update(user_config)
    return config


class config:
    """Get/set configuration values for the :mod:`audmodel` module.

    The configuration values are read in during module import
    from the :ref:`configuration file <configuration>`
    :file:`~/.config/audmodel.yaml`.
    You can change the configuration values after import,
    by setting the attributes directly.
    The cache related configuration value :attr:`config.CACHE_ROOT`
    can be overridden by the ``AUDMODEL_CACHE_ROOT`` environment variable.

    Examples:
        >>> config.CACHE_ROOT = "~/caches/audmodel"
        >>> config.CACHE_ROOT
        '~/caches/audmodel'

    """

    _config = load_config()

    CACHE_ROOT = _config["cache_root"]
    r"""Default cache folder for storing models."""

    REPOSITORIES = [
        Repository(r["name"], r["host"], r["backend"]) for r in _config["repositories"]
    ]
    r"""Repositories, will be iterated in given order.

    A repository is defined by the object :class:`audmodel.Repository`,
    containing the following attributes:

    * :attr:`audmodel.Repository.name`: repository name,
      e.g. ``"models-local"``
    * :attr:`audmodel.Repository.backend`: backend name,
      e.g. ``"s3"``
    * :attr:`audmodel.Repository.host`: host name,
      e.g. ``"s3.dualstack.eu-north-1.amazonaws.com"``

    """
