from updater import components
from pathlib import Path
from rex import rex
import tempfile
import shutil
import pytest


FIXTURE_DIR = Path(".").absolute() / "tests/test_files"

logspout = {
    "component_type": "docker-image",
    "repo_name": "gliderlabs",
    "component_name": "logspout",
    "current_version_tag": "v3.1",
}

glances = {
    "component_type": "docker-image",
    "repo_name": "nicolargo",
    "component_name": "glances",
    "current_version_tag": "v2.11.1",
}


def test_save_next_version_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**logspout))
    to_update = config.count_components_to_update()
    assert to_update == 1
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "next-version:" in file_content


def test_save_prefix_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**logspout))
    config.components[0].prefix = "version_prefix"
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "version_prefix" in file_content


def test_exlude_versions_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**logspout))
    config.components[0].exclude_versions = ["v3.2.6"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "exclude-versions: [v3.2.6]" in file_content


def test_save_files_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**logspout))
    config.components[0].files = ["file1", "file2"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "[file1, file2]" in file_content


def test_use_filter_for_component_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**logspout))
    config.components[0].prefix = "v"
    config.components[0].filter = "/^v\d+\.\d+\.\d+$/"
    config.components[0].check()
    assert config.components[0].next_version_tag == rex(config.components[0].filter)


def test_components_list_write_read_yaml_file(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**glances))
    config.add(components.factory.get(**logspout))
    dict1 = config.components_to_dict()
    config.save_to_yaml()
    config.read_from_yaml()
    dict2 = config.components_to_dict()
    assert dict1 == dict2


def test_components_to_dict(tmp_path):
    config = components.Config(tmp_path / "components.yaml")
    config.add(components.factory.get(**glances))
    config.add(components.factory.get(**logspout))
    result = {
        "glances": {
            "current-version": "v2.11.1",
            "docker-repo": "nicolargo",
            "next-version": "v2.11.1",
        },
        "logspout": {
            "current-version": "v3.1",
            "docker-repo": "gliderlabs",
            "next-version": "v3.1",
        },
    }
    assert result == config.components_to_dict()


def config_from_copy_of_test_dir():
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(FIXTURE_DIR, test_dir)
    return test_dir, components.Config(test_dir / "components.yaml")


def test_update_components_files():
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    assert config.check() == [("glances", True), ("logspout", True)]
    assert config.update_files(test_dir) == 3


def test_dry_run_save_config():
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    content1 = config.config_file.read_text()
    config.save_config(destination_file=None, dry_run=True, print_yaml=False)
    content2 = config.config_file.read_text()
    assert content1 == content2


# TODO: Refactor access to components and its path - get rid of long components[0] things
def test_dry_run_update_file():
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    config.check()
    assert config.components[0].current_version != config.components[0].next_version
    assert config.components[1].current_version != config.components[1].next_version
    content1 = config.config_file.parent.joinpath(
        config.components[0].files[0]
    ).read_text()
    config.update_files(base_dir=config.config_file.parent, dry_run=True)
    content2 = config.config_file.parent.joinpath(
        config.components[0].files[0]
    ).read_text()
    assert content1 == content2
    config.update_files(base_dir=config.config_file.parent, dry_run=False)
    content2 = config.config_file.parent.joinpath(
        config.components[0].files[0]
    ).read_text()
    assert content1 != content2


def test_exclude_versions_param():
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    config.check()
    config.save_config()
    assert "next-version: v3.2.6" not in config.config_file.read_text()


def test_update_components_files_with_testing_positive(capfd):
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    config.test_command = ["make", "test"]
    assert config.check() == [("glances", True), ("logspout", True)]
    assert config.update_files(test_dir) == 3
    captured = capfd.readouterr()
    assert captured.out.count("Test OK") == 2, captured.out


def test_update_components_files_with_testing_negative(capfd):
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    config.test_command = ["make", "test-fail"]
    assert config.check() == [("glances", True), ("logspout", True)]
    with pytest.raises(AssertionError) as excinfo:
        config.update_files(test_dir)
    assert "returncode=2" in str(excinfo.value)
    captured = capfd.readouterr()
    assert "Test KO" in captured.out, captured.out
