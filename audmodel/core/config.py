import os

import audeer

from audmodel.core.define import CONFIG_FILE
from audmodel.core.define import USER_CONFIG_FILE
from audmodel.core.repository import Repository


CWD = audeer.script_dir()
global_config_file = os.path.join(CWD, CONFIG_FILE)


def validate_config(config: dict):
    r"""Validate configuration.

    Args:
        config: configuration dictionary

    Raises:
        ValueError: if ``repositories`` section is present,
            but empty
        ValueError: if repository has no ``host``
            ``backend``, or ``name`` key

    """
    if "repositories" in config:
        if not config["repositories"]:
            raise ValueError(
                "You cannot specify an empty 'repositories:' section "
                "in a configuration file."
            )
        for repo in config["repositories"]:
            for key in ("host", "backend", "name"):
                if key not in repo:
                    raise ValueError(
                        f"Your repository is missing a '{key}' entry: '{repo}'."
                    )


def load_config() -> dict:
    """Read configuration from configuration files.

    User config values take precedence over global config values
    when the same setting exists in both files.

    """
    return audeer.load_configuration(
        global_config_file,
        audeer.path(USER_CONFIG_FILE),
        validate=validate_config,
    )


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
        >>> audmodel.config.CACHE_ROOT = "~/caches/audmodel"
        >>> audmodel.config.CACHE_ROOT
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
      e.g. ``"audmodel-public"``
    * :attr:`audmodel.Repository.backend`: backend name,
      e.g. ``"s3"``
    * :attr:`audmodel.Repository.host`: host name,
      e.g. ``"s3.dualstack.eu-north-1.amazonaws.com"``

    """
