from audmodel.core.repository import Repository


class config:
    r"""Get/set defaults for the :mod:`audmodel` module."""

    CACHE_ROOT = "~/audmodel"
    r"""Default cache folder for storing models."""

    REPOSITORIES = [
        Repository(
            "...",
            "...",
            "s3",
        ),
        Repository(
            "audmodel-internal",
            "s3.dualstack.eu-north-1.amazonaws.com",
            "s3",
        ),
    ]
    r"""Default repositories (will be searched in given order)."""
