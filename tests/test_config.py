import pytest
import yaml

import audmodel


@pytest.fixture
def set_user_config(tmp_path, monkeypatch):
    """Provide a function to set the user config file content.

    The returned function writes the given content
    to a temporary user config file
    and points ``audmodel.core.config.USER_CONFIG_FILE`` to it.

    Args:
        tmp_path: tmp_path fixture
        monkeypatch: monkeypatch fixture

    """

    def set_content(content: str) -> str:
        config_file = tmp_path / "audmodel.yaml"
        config_file.write_text(content)
        monkeypatch.setattr(
            audmodel.core.config,
            "USER_CONFIG_FILE",
            str(config_file),
        )
        return str(config_file)

    return set_content


def test_default_config():
    """Test loading the global config shipped with the package."""
    config = audmodel.core.config.load_config()
    assert config["cache_root"] == "~/audmodel"
    assert len(config["repositories"]) > 0


def test_missing_user_config_file(monkeypatch, tmp_path):
    """Test that a non-existing user config file is ignored."""
    monkeypatch.setattr(
        audmodel.core.config,
        "USER_CONFIG_FILE",
        str(tmp_path / "non-existing.yaml"),
    )
    config = audmodel.core.config.load_config()
    assert config["cache_root"] == "~/audmodel"
    assert len(config["repositories"]) > 0


def test_user_config_file(set_user_config):
    """Test that user config overwrites the global config."""
    set_user_config("cache_root: ~/user\n")
    config = audmodel.core.config.load_config()
    assert config["cache_root"] == "~/user"
    # Global repositories are still present
    assert len(config["repositories"]) > 0


def test_user_config_repository(set_user_config):
    """Test custom repositories in the user config file."""
    set_user_config(
        "repositories:\n"
        "  - name: my-repo\n"
        "    host: some-host\n"
        "    backend: some-backend\n"
    )
    config = audmodel.core.config.load_config()
    assert config["repositories"] == [
        {
            "name": "my-repo",
            "host": "some-host",
            "backend": "some-backend",
        },
    ]
    # Global cache root is still present
    assert config["cache_root"] == "~/audmodel"


def test_empty_repositories(set_user_config):
    """Test that an empty repositories section raises an error."""
    set_user_config("repositories:\n")
    error_msg = (
        "You cannot specify an empty 'repositories:' section in a configuration file."
    )
    with pytest.raises(ValueError, match=error_msg):
        audmodel.core.config.load_config()


@pytest.mark.parametrize("missing_key", ["host", "backend", "name"])
def test_missing_repository_key(set_user_config, missing_key):
    """Test that a repository missing a required key raises an error."""
    repo = {
        "name": "my-repo",
        "host": "some-host",
        "backend": "some-backend",
    }
    del repo[missing_key]
    content = "repositories:\n  - "
    content += "\n    ".join(f"{key}: {value}" for key, value in repo.items())
    set_user_config(content + "\n")
    error_msg = f"Your repository is missing a '{missing_key}' entry"
    with pytest.raises(ValueError, match=error_msg):
        audmodel.core.config.load_config()


def test_empty_config_file(set_user_config):
    """Test loading an empty config file."""
    set_user_config("")
    config = audmodel.core.config.load_config()
    assert config["cache_root"] == "~/audmodel"
    assert len(config["repositories"]) > 0


def test_invalid_config_file(set_user_config):
    """Test loading a broken config file."""
    set_user_config("{invalid: yaml: content}")
    with pytest.raises(yaml.YAMLError):
        audmodel.core.config.load_config()
