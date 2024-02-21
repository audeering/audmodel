import audbackend


class config:
    r"""Get/set defaults for the :mod:`audmodel` module."""

    CACHE_ROOT = "~/audmodel"
    r"""Default cache folder for storing models."""

    REPOSITORIES = [
        audbackend.Repository(
            "models-local",
            "https://artifactory.audeering.com/artifactory",
            "artifactory",
        ),
    ]
    r"""Default repositories (will be searched in given order)."""
