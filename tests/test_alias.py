import os

import pytest

import audmodel


audmodel.config.CACHE_ROOT = pytest.CACHE_ROOT
audmodel.config.REPOSITORIES = pytest.REPOSITORIES

SUBGROUP = f"{pytest.ID}.alias"


@pytest.fixture(scope="module")
def published_model():
    """Publish a model for testing alias functionality."""
    return audmodel.publish(
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
    assert audmodel.versions(alias) == ["1.0.0", "2.0.0"]


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
    assert audmodel.exists(alias)
    assert audmodel.name(alias) == pytest.NAME
    assert audmodel.parameters(alias) == pytest.PARAMS
    assert audmodel.subgroup(alias) == SUBGROUP
    assert audmodel.version(alias) == "1.0.0"
    assert audmodel.versions(alias) == ["1.0.0", "2.0.0"]

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
    assert audmodel.versions(alias) == ["1.0.0", "2.0.0", "3.0.0"]
    assert audmodel.aliases(new_uid) == [alias]
    assert alias not in audmodel.aliases(published_model)


def test_is_alias():
    """Test the is_alias utility function."""
    from audmodel.core.utils import is_alias

    # UIDs should not be detected as aliases
    assert not is_alias("d4e9c65b")  # short UID (8 chars)
    assert not is_alias("d4e9c65b-1.0.0")  # UID with version
    assert not is_alias("12345678-90ab-cdef-1234-567890abcdef")  # legacy UID (36 chars)
    # Test legacy UID with proper UUID format (8-4-4-4-12), all hex
    assert not is_alias("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
    # Test 8-char hex strings
    assert not is_alias("abcd1234")
    assert not is_alias("deadbeef")
    assert not is_alias("cafebabe")

    # Aliases should be detected
    assert is_alias("my-model")
    assert is_alias("production-model")
    assert is_alias("test_alias")
    assert is_alias("alias123")
    assert is_alias("Cafebabe")
    # Test 8-char non-hex string
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


def test_aliases_no_aliases():
    """Test aliases() returns empty list when no aliases are set."""
    # Publish a fresh model without any aliases
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "13.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Get aliases for a model without any aliases
    alias_list = audmodel.aliases(uid)
    assert alias_list == []


def test_aliases_single_alias():
    """Test aliases() returns a single alias correctly."""
    # Publish a fresh model
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "14.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    alias = "test-single-alias"
    audmodel.set_alias(alias, uid)

    # Get aliases for the model
    alias_list = audmodel.aliases(uid)
    assert alias_list == [alias]


def test_aliases_multiple_aliases():
    """Test aliases() returns multiple aliases correctly."""
    # Publish a fresh model
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "15.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    alias1 = "test-multi-alias-1"
    alias2 = "test-multi-alias-2"
    alias3 = "test-multi-alias-3"

    # Set multiple aliases
    audmodel.set_alias(alias1, uid)
    audmodel.set_alias(alias2, uid)
    audmodel.set_alias(alias3, uid)

    # Get aliases for the model
    alias_list = audmodel.aliases(uid)

    # Should be sorted
    assert alias_list == sorted([alias1, alias2, alias3])


def test_aliases_publish_with_alias():
    """Test that publish with alias creates the aliases file."""
    alias = "test-publish-aliases"
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "9.0.0",
        alias=alias,
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Verify the alias is in the aliases list
    alias_list = audmodel.aliases(uid)
    assert alias_list == [alias]


def test_aliases_with_short_id():
    """Test that aliases() works with short ID (gets latest version)."""
    # Publish a fresh model with unique params to get unique short_id
    unique_params = pytest.PARAMS.copy()
    unique_params["test_param"] = "short_id_test"

    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        unique_params,
        "1.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    alias = "test-short-id-alias"
    audmodel.set_alias(alias, uid)

    # Extract short ID from full UID
    short_id = uid.split("-")[0]

    # Get aliases using short ID (should get latest version's aliases)
    alias_list = audmodel.aliases(short_id)
    assert alias in alias_list


def test_aliases_update_existing():
    """Test that setting an alias twice doesn't duplicate it."""
    alias = "test-duplicate-alias"
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "10.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Set the same alias twice
    audmodel.set_alias(alias, uid)
    audmodel.set_alias(alias, uid)

    # Should only appear once
    alias_list = audmodel.aliases(uid)
    assert alias_list.count(alias) == 1


def test_aliases_different_versions():
    """Test that different versions can have different aliases."""
    alias1 = "test-version-1-alias"
    alias2 = "test-version-2-alias"

    uid1 = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "11.0.0",
        alias=alias1,
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    uid2 = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "12.0.0",
        alias=alias2,
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["2.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Each version should have its own alias
    assert audmodel.aliases(uid1) == [alias1]
    assert audmodel.aliases(uid2) == [alias2]


def test_aliases_nonexistent_model():
    """Test that aliases() raises error for non-existent model."""
    with pytest.raises(RuntimeError, match="does not exist"):
        audmodel.aliases("nonexist-1.0.0")


def test_aliases_with_alias_as_input():
    """Test that aliases() works when given an alias as input."""
    # Publish a fresh model
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "17.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    alias1 = "test-input-alias-1"
    alias2 = "test-input-alias-2"

    # Set two aliases
    audmodel.set_alias(alias1, uid)
    audmodel.set_alias(alias2, uid)

    # Get aliases using one of the aliases as input
    alias_list = audmodel.aliases(alias1)
    assert sorted(alias_list) == sorted([alias1, alias2])


def test_resolve_alias_with_corrupted_yaml():
    """Test that resolving an alias with corrupted YAML raises RuntimeError.

    This test covers lines 591-592 in backend.py where YAML parsing errors
    are caught and re-raised as RuntimeError.
    """
    alias = "test-corrupted-yaml-alias"
    uid = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "18.0.0",
        alias=alias,
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Verify alias works before corruption
    assert audmodel.resolve_alias(alias) == uid

    # Corrupt the alias file on the backend by writing invalid YAML
    repository = audmodel.config.REPOSITORIES[0]
    backend_interface = repository.create_backend_interface()
    alias_path = backend_interface.join(
        "/",
        "_alias",
        f"{alias}.alias.yaml",
    )

    # Write corrupted YAML directly to the backend
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_root:
        corrupt_file = os.path.join(tmp_root, "corrupt.yaml")
        # Write invalid YAML (unbalanced brackets, invalid syntax)
        with open(corrupt_file, "w") as f:
            f.write("uid: {this is not valid yaml: [[[")

        with backend_interface.backend:
            backend_interface.put_file(
                corrupt_file,
                alias_path,
                "1.0.0",
                verbose=False,
            )

    # Clear the cache to force re-download
    # (aliases are fetched from backend each time, not cached)

    # Now resolving the alias should raise RuntimeError due to YAML parsing error
    with pytest.raises(RuntimeError, match="Failed to parse alias file"):
        audmodel.resolve_alias(alias)


def test_aliases_with_malformed_aliases_file():
    """Test that aliases() returns empty list when aliases file is malformed.

    This test covers line 720 in backend.py where we return an empty list
    when aliases_data is None or doesn't contain the 'aliases' key.
    """
    # Test case 1: aliases file exists but is empty (aliases_data is None)
    uid1 = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "19.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["1.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    # Create an empty/malformed aliases file on the backend
    repository = audmodel.config.REPOSITORIES[0]
    backend_interface = repository.create_backend_interface()
    short_id = uid1.split("-")[0]
    version = "-".join(uid1.split("-")[1:])
    aliases_path = backend_interface.join(
        "/",
        "_uid",
        f"{short_id}.aliases.yaml",
    )

    # Write empty YAML file (will parse as None)
    import tempfile

    with tempfile.TemporaryDirectory() as tmp_root:
        empty_file = os.path.join(tmp_root, "empty.yaml")
        with open(empty_file, "w") as f:
            f.write("")  # Empty file

        with backend_interface.backend:
            backend_interface.put_file(
                empty_file,
                aliases_path,
                version,
                verbose=False,
            )

    # Should return empty list when file is empty
    assert audmodel.aliases(uid1) == []

    # Test case 2: aliases file exists but doesn't have 'aliases' key
    uid2 = audmodel.publish(
        pytest.MODEL_ROOT,
        pytest.NAME,
        pytest.PARAMS,
        "20.0.0",
        author=pytest.AUTHOR,
        date=pytest.DATE,
        meta=pytest.META["2.0.0"],
        subgroup=SUBGROUP,
        repository=audmodel.config.REPOSITORIES[0],
    )

    short_id2 = uid2.split("-")[0]
    version2 = "-".join(uid2.split("-")[1:])
    aliases_path2 = backend_interface.join(
        "/",
        "_uid",
        f"{short_id2}.aliases.yaml",
    )

    # Write YAML file with wrong structure (missing 'aliases' key)
    with tempfile.TemporaryDirectory() as tmp_root:
        wrong_structure_file = os.path.join(tmp_root, "wrong.yaml")
        with open(wrong_structure_file, "w") as f:
            f.write("wrong_key: some_value\n")

        with backend_interface.backend:
            backend_interface.put_file(
                wrong_structure_file,
                aliases_path2,
                version2,
                verbose=False,
            )

    # Should return empty list when 'aliases' key is missing
    assert audmodel.aliases(uid2) == []
