import pytest

import audmodel
from audmodel.core import backend


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES


def test_header_path_empty_version():
    """Test header_path with empty version string.

    When version is empty or None,
    the function should break out of the repository loop
    and raise a RuntimeError indicating the model does not exist.

    """
    short_id = "00000000"
    version = ""

    error_msg = f"A model with ID '{short_id}' does not exist."
    with pytest.raises(RuntimeError, match=error_msg):
        backend.header_path(short_id, version)

    # Also test with None
    with pytest.raises(RuntimeError, match=error_msg):
        backend.header_path(short_id, None)
