class config:
    r"""Get/set defaults for the :mod:`audmodel` module."""

    BACKEND_HOST = (
        'artifactory',
        'https://artifactory.audeering.com/artifactory',
    )
    r"""Backend name and host address."""

    CACHE_ROOT = '~/audmodel'
    r"""Default cache folder for storing models."""

    REPOSITORY_PRIVATE = 'models-private-local'
    r"""Default private repository."""
    REPOSITORY_PUBLIC = 'models-public-local'
    r"""Default public repository."""
