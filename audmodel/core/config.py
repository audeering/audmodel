import audbackend


class config:
    r"""Get/set defaults for the :mod:`audmodel` module."""

    CACHE_ROOT = '~/audmodel'
    r"""Default cache folder for storing models."""

    LEGACY_REPOSITORY_PRIVATE = 'models-private-local'
    r"""Default private repository for legacy models."""
    LEGACY_REPOSITORY_PUBLIC = 'models-public-local'
    r"""Default public repository for legacy models."""

    REPOSITORIES = [
        audbackend.Repository(
            'models-local',
            'https://artifactory.audeering.com/artifactory',
            'artifactory',
        ),
    ]
    r"""Default repositories (will be searched in given order)."""
