import pytest
import yaml

import audeer

import audmodel


@pytest.fixture()
def user_config_file(tmpdir):
    """Provide a user config file.

    The config file at ``.config/audmodel.yaml``
    sets ``cache_root`` to ``~/user``.

    Args:
        tmpdir: tmpdir fixture.
            The tmpdir is used as the home folder
            for storing the user config file

    """
    home = audeer.mkdir(tmpdir)
    current_user_config_file = audmodel.core.define.USER_CONFIG_FILE
    audmodel.core.config.USER_CONFIG_FILE = audeer.path(
        home, ".config", "audmodel.yaml"
    )
    audeer.mkdir(home, ".config")
    with open(audeer.path(home, ".config", "audmodel.yaml"), "w") as fp:
        fp.write("cache_root: ~/user\n")

    yield

    audmodel.core.config.USER_CONFIG_FILE = current_user_config_file


def test_config_file(tmpdir):
    root = audeer.mkdir(tmpdir)

    config_file = audeer.path(root, "audmodel.yaml")

    # Try loading non-existing file
    config = audmodel.core.config.load_configuration_file(config_file)
    assert config == {}

    # Add a custom cache entry
    # and check if combining with global config works
    with open(config_file, "w") as cf:
        cf.write("cache_root: ~/user\n")

    config = audmodel.core.config.load_configuration_file(config_file)
    assert config == {"cache_root": "~/user"}

    global_config = audmodel.core.config.load_configuration_file(
        audmodel.core.config.global_config_file
    )
    global_config.update(config)
    assert global_config["cache_root"] == "~/user"

    # Fail for empty repositories entry
    with open(config_file, "w") as cf:
        cf.write("repositories:\n")
    error_msg = (
        "You cannot specify an empty 'repositories:' section "
        f"in the configuration file '{config_file}'."
    )
    with pytest.raises(ValueError, match=error_msg):
        audmodel.core.config.load_configuration_file(config_file)

    # Fail for missing repository entries
    with open(config_file, "w") as cf:
        cf.write("repositories:\n")
        cf.write("  - host: some-host\n")
        cf.write("    backend: some-backend\n")
    error_msg = "Your repository is missing a 'name' entry"
    with pytest.raises(ValueError, match=error_msg):
        audmodel.core.config.load_configuration_file(config_file)

    with open(config_file, "w") as cf:
        cf.write("repositories:\n")
        cf.write("  - name: my-repo\n")
    error_msg = "Your repository is missing a 'host' entry."
    with pytest.raises(ValueError, match=error_msg):
        audmodel.core.config.load_configuration_file(config_file)

    with open(config_file, "w") as cf:
        cf.write("repositories:\n")
        cf.write("  - name: my-repo\n")
        cf.write("    host: some-host\n")
    error_msg = "Your repository is missing a 'backend' entry"
    with pytest.raises(ValueError, match=error_msg):
        audmodel.core.config.load_configuration_file(config_file)

    # Load custom repository
    with open(config_file, "w") as cf:
        cf.write("repositories:\n")
        cf.write("  - name: my-repo\n")
        cf.write("    host: some-host\n")
        cf.write("    backend: some-backend\n")
    config = audmodel.core.config.load_configuration_file(config_file)
    assert config == {
        "repositories": [
            {
                "name": "my-repo",
                "host": "some-host",
                "backend": "some-backend",
            },
        ]
    }


def test_user_config_file(user_config_file):
    """Test that user config overwrites the global config."""
    config = audmodel.core.config.load_config()
    assert config["cache_root"] == "~/user"
    # Global repositories are still present
    assert len(config["repositories"]) > 0


def test_empty_config_file(tmp_path):
    """Test loading an empty config file."""
    empty_config = tmp_path / "empty.yaml"
    empty_config.write_text("")
    config = audmodel.core.config.load_configuration_file(empty_config)
    assert config == {}


def test_invalid_config_file(tmp_path):
    """Test loading a broken config file."""
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text("{invalid: yaml: content}")
    with pytest.raises(yaml.YAMLError):
        audmodel.core.config.load_configuration_file(invalid_config)
