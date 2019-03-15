from updater import components
from pathlib import Path
from rex import rex
import tempfile
import shutil
import pytest


FIXTURE_DIR = Path(".").absolute() / "tests/test_files"

comp = {
    "logspout": {
        "component_type": "docker-image",
        "repo_name": "gliderlabs",
        "component_name": "logspout",
        "current_version_tag": "v3.1",
    },
    "glances": {
        "component_type": "docker-image",
        "repo_name": "nicolargo",
        "component_name": "glances",
        "current_version_tag": "v2.11.1",
    },
    "Django": {
        "component_type": "pypi",
        "component_name": "Django",
        "current_version_tag": "2.1.2",
    },
    "requests": {
        "component_type": "pypi",
        "component_name": "requests",
        "current_version_tag": "2.20.0",
    },
}


def test_save_next_version_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.add(components.factory.get(**comp["Django"]))
    to_update = config.count_components_to_update()
    assert to_update == 2
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert file_content.count("next-version:") == 2


def test_save_prefix_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].prefix = "version_prefix"
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "version_prefix" in file_content


def test_exlude_versions_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].exclude_versions = ["v3.2.6"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "exclude-versions:" in file_content
    assert "v3.2.6" in file_content


def test_save_files_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].files = ["file1", "file2"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "file1" in file_content
    assert "file2" in file_content


def test_use_filter_for_component_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].prefix = "v"
    config.components[0].filter = "/^v\d+\.\d+\.\d+$/"
    config.components[0].check()
    assert config.components[0].next_version_tag == rex(config.components[0].filter)


def test_components_list_write_read_yaml_file(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["glances"]))
    config.add(components.factory.get(**comp["logspout"]))
    dict1 = config.components_to_dict()
    config.save_to_yaml()
    config.read_from_yaml()
    dict2 = config.components_to_dict()
    assert dict1 == dict2


def test_components_to_dict(tmp_path):
    config = components.Config(tmp_path / "components.yaml")
    config.add(components.factory.get(**comp["glances"]))
    config.add(components.factory.get(**comp["logspout"]))
    config.add(components.factory.get(**comp["Django"]))
    result = {
        "glances": {
            "component-type": "docker-image",
            "current-version": "v2.11.1",
            "docker-repo": "nicolargo",
            "next-version": "v2.11.1",
        },
        "logspout": {
            "component-type": "docker-image",
            "current-version": "v3.1",
            "docker-repo": "gliderlabs",
            "next-version": "v3.1",
        },
        "Django": {
            "component-type": "pypi",
            "current-version": "2.1.2",
            "next-version": "2.1.2",
        },
    }
    assert result == config.components_to_dict()


def config_from_copy_of_test_dir():
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(FIXTURE_DIR, test_dir)
    config = components.Config(test_dir / "components.yaml")
    config.git_commit = False
    config.read_from_yaml()
    return test_dir, config


def test_update_components_files():
    (test_dir, config) = config_from_copy_of_test_dir()
    assert config.check() == [
        ("glances", True),
        ("logspout", True),
        ("Django", True),
        ("requests", True),
    ]
    assert config.update_files(test_dir) == 5


def test_save_config_dry_run():
    (test_dir, config) = config_from_copy_of_test_dir()
    content1 = config.config_file.read_text()
    config.save_config(destination_file=None, dry_run=True, print_yaml=False)
    content2 = config.config_file.read_text()
    assert content1 == content2


def test_save_config_print_yaml(capfd):
    (test_dir, config) = config_from_copy_of_test_dir()
    config.save_config(destination_file=None, dry_run=True, print_yaml=True)
    captured = capfd.readouterr()
    assert "nicolargo" in captured.out, captured.out


# TODO: Refactor access to components and its path - get rid of long components[0] things
def test_dry_run_update_file():
    (test_dir, config) = config_from_copy_of_test_dir()
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
    config.check()
    config.save_config()
    assert "next-version: v3.2.6" not in config.config_file.read_text()


def test_update_components_files_with_testing_positive(capfd):
    (test_dir, config) = config_from_copy_of_test_dir()
    config.test_command = ["make", "test"]
    assert config.check() == [
        ("glances", True),
        ("logspout", True),
        ("Django", True),
        ("requests", True),
    ]
    assert config.update_files(test_dir) == 5
    captured = capfd.readouterr()
    assert captured.out.count("Test OK") == 4, captured.out


def test_update_components_files_with_testing_negative(capfd):
    (test_dir, config) = config_from_copy_of_test_dir()
    config.test_command = ["make", "test-fail"]
    assert config.check() == [
        ("glances", True),
        ("logspout", True),
        ("Django", True),
        ("requests", True),
    ]
    with pytest.raises(AssertionError) as excinfo:
        config.update_files(test_dir)
    assert "Error" in str(excinfo.value)
    captured = capfd.readouterr()
    assert "Test KO" in captured.out, captured.out
