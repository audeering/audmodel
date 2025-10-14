import os
from unittest.mock import patch

import pytest

import audeer

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

SUBGROUP = f"{pytest.ID}.alias"


@pytest.fixture(scope="module")
def published_model():
    """Publish a model for testing alias functionality."""
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "1.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )
    return uid


def test_publish_with_alias():
    """Test publishing a model with an alias."""
    alias = "test-publish-alias"
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "2.0.0",
        alias=alias,
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["2.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Verify alias was created and resolves to correct UID
    assert audmodel.resolve_alias(alias) == uid

    # Verify we can load model using alias
    model_path = audmodel.load(alias)
    assert model_path.endswith(uid.replace("-", os.sep))


def test_set_alias(published_model):
    """Test setting an alias for an existing model."""
    alias = "test-set-alias"

    # Set alias for existing model
    audmodel.set_alias(alias, published_model)

    # Verify alias resolves correctly
    assert audmodel.resolve_alias(alias) == published_model

    # Verify we can use alias to access model info
    assert audmodel.name(alias) == pytest.NAME
    assert audmodel.author(alias) == pytest.AUTHOR
    assert audmodel.parameters(alias) == pytest.PARAMS
    assert audmodel.version(alias) == "1.0.0"


def test_resolve_alias_nonexistent():
    """Test resolving a non-existent alias raises error."""
    alias = "test-nonexistent-alias"
    with pytest.raises(RuntimeError, match="does not exist"):
        audmodel.resolve_alias(alias)


def test_set_alias_nonexistent_model():
    """Test setting alias for non-existent model raises error."""
    alias = "test-invalid-alias"
    with pytest.raises(RuntimeError, match="does not exist"):
        audmodel.set_alias(alias, "nonexist-1.0.0")


def test_load_with_alias(published_model):
    """Test loading a model using an alias."""
    alias = "test-load-alias"
    audmodel.set_alias(alias, published_model)

    # Load using UID
    path_uid = audmodel.load(published_model)

    # Load using alias
    path_alias = audmodel.load(alias)

    # Both should point to the same location
    assert path_uid == path_alias


def test_all_api_functions_with_alias(published_model):
    """Test that all API functions work with aliases."""
    alias = "test-api-alias"
    audmodel.set_alias(alias, published_model)

    # Test all API functions that accept uid parameter
    assert audmodel.author(alias) == pytest.AUTHOR
    assert audmodel.date(alias) == str(pytest.DATE)
    assert audmodel.exists(published_model)  # exists doesn't support aliases currently
    assert audmodel.name(alias) == pytest.NAME
    assert audmodel.parameters(alias) == pytest.PARAMS
    assert audmodel.subgroup(alias) == SUBGROUP
    assert audmodel.version(alias) == "1.0.0"

    # Test header and meta
    header = audmodel.header(alias)
    assert header["name"] == pytest.NAME
    assert header["author"] == pytest.AUTHOR

    meta = audmodel.meta(alias)
    assert meta == pytest.META["1.0.0"]


def test_update_alias(published_model):
    """Test updating an existing alias to point to a different model."""
    alias = "test-update-alias"

    # Set alias to first model
    audmodel.set_alias(alias, published_model)
    assert audmodel.resolve_alias(alias) == published_model

    # Publish a new version
    new_uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "3.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["3.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Update alias to point to new version
    audmodel.set_alias(alias, new_uid)
    assert audmodel.resolve_alias(alias) == new_uid
    assert audmodel.version(alias) == "3.0.0"


def test_is_alias():
    """Test the is_alias utility function."""
    from audmodel.core.utils import is_alias

    # UIDs should not be detected as aliases
    assert not is_alias("d4e9c65b")  # short UID (8 chars)
    assert not is_alias("d4e9c65b-1.0.0")  # UID with version
    assert not is_alias("12345678-90ab-cdef-1234-567890abcdef")  # legacy UID (36 chars)
    # Test legacy UID with proper UUID format (8-4-4-4-12), all hex
    assert not is_alias("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    # Test legacy UUID format with non-hex chars (to hit lines 62-70)
    assert not is_alias("xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    # Test 8-char hex strings (multiple cases to ensure line 76 coverage)
    assert not is_alias("abcd1234")
    assert not is_alias("deadbeef")
    assert not is_alias("cafebabe")

    # Aliases should be detected
    assert is_alias("my-model")
    assert is_alias("production-model")
    assert is_alias("test_alias")
    assert is_alias("alias123")
    assert is_alias("Cafebabe")
    # Test 8-char non-hex string (edge case for lines 73-79)
    assert is_alias("zyxwvuts")


def test_publish_with_invalid_subgroup_alias():
    """Test that publishing with subgroup='_alias' raises ValueError."""
    with pytest.raises(
        ValueError, match="It is not allowed to set subgroup to '_alias'"
    ):
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "5.0.0",
            subgroup="_alias",
            repository=audmodel.config.REPOSITORIES[0],
        )


def test_publish_with_alias_cleanup_on_failure():
    """Test that alias is cleaned up when publishing fails.

    This test verifies that if publishing fails after the alias file
    has been created, the alias file is properly removed during cleanup.
    """
    alias = "test-failed-alias"

    # Try to publish with an alias but cause a failure with unpicklable meta
    with pytest.raises(RuntimeError, match="Cannot serialize"):
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "6.0.0",
            alias=alias,
            meta={"object": pytest.CANNOT_PICKLE},
            subgroup=SUBGROUP,
            repository=audmodel.config.REPOSITORIES[0],
        )

    # Verify the alias was cleaned up and doesn't exist
    with pytest.raises(RuntimeError, match="does not exist"):
        audmodel.resolve_alias(alias)


def test_set_alias_with_uid_like_name(published_model):
    """Test that setting an alias with a UID-like name raises ValueError.

    This test covers lines 638-642 in backend.py where the alias name
    is validated to ensure it's not a UID format.
    """
    # Try to set an alias that looks like a short UID (8 hex chars)
    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("abcd1234", published_model)

    # Try to set an alias that looks like a UID with version
    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("d4e9c65b-1.0.0", published_model)

    # Try to set an alias that looks like a legacy UUID
    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", published_model)


def test_set_alias_with_invalid_characters(published_model):
    """Test that setting an alias with invalid characters raises ValueError.

    Only [A-Za-z0-9._-] characters are allowed.
    """
    # Try to set an alias with spaces
    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("my alias", published_model)

    # Try to set an alias with special characters
    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("my@alias", published_model)

    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("my!alias", published_model)

    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("my#alias", published_model)

    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("my$alias", published_model)

    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("my/alias", published_model)

    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.set_alias("my(alias)", published_model)


def test_publish_with_invalid_alias_names():
    """Test that publishing with invalid alias names raises an error."""
    # Try to publish with UID-like alias
    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "7.0.0",
            alias="deadbeef",
            subgroup=SUBGROUP,
            repository=audmodel.config.REPOSITORIES[0],
        )

    # Try to publish with alias containing special characters
    # This raises ValueError from backend path validation in cleanup code
    with pytest.raises(ValueError, match="is not an allowed alias name"):
        audmodel.publish(
            pytest.MODEL_ROOT,
            pytest.NAME,
            pytest.PARAMS,
            "8.0.0",
            alias="my@alias",
            subgroup=SUBGROUP,
            repository=audmodel.config.REPOSITORIES[0],
        )


def test_resolve_alias_with_corrupted_file(published_model):
    """Test that resolving an alias with corrupted YAML file raises error."""
    alias = "test-corrupted-alias"

    # First, create a valid alias
    audmodel.set_alias(alias, published_model)

    # Get the cache path
    cache_root = audmodel.config.CACHE_ROOT
    alias_cache_path = os.path.join(
        cache_root,
        "_alias",
        f"{alias}.alias.yaml",
    )

    # Corrupt the local alias file with invalid YAML
    audeer.mkdir(os.path.dirname(alias_cache_path))
    with open(alias_cache_path, "w") as f:
        f.write("uid: [invalid yaml syntax without closing bracket")

    # Get checksum of the corrupted file
    corrupted_checksum = audeer.md5(alias_cache_path)

    # Mock the backend checksum to match the corrupted file's checksum
    # This prevents the file from being re-downloaded
    # and forces reading of the corrupted file
    with patch("audbackend.interface.Maven.checksum", return_value=corrupted_checksum):
        # Try to resolve the alias - should raise RuntimeError about parsing failure
        with pytest.raises(RuntimeError, match="Failed to parse alias file"):
            audmodel.resolve_alias(alias)
