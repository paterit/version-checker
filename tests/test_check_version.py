from packaging.version import parse
from check_version import fetch_versions, Component, ComponentsConfig
import pytest
from pathlib import Path
from rex import rex
import tempfile
import shutil
from packaging.version import parse


FIXTURE_DIR = Path(".").absolute() / "tests/test_files"


def compare_versions(old, new):
    assert parse(old) < parse(new)


def test_parse_compare_versions():
    compare_versions(old="3.6.6-alpine3.8", new="3.6.6-alpine3.9")

    compare_versions(old="3.6.6-alpine3.8", new="3.6.7-alpine3.8")

    compare_versions(
        old="1.5.3-python3.6.6-alpine3.8", new="1.6.3-python3.6.6-alpine3.8"
    )

    compare_versions(
        old="1.5.3-python3.6.6-alpine3.8", new="1.5.3-python3.7.6-alpine3.8"
    )


def check_docker_versions(repo_name, component_name, version_tag):
    tags = fetch_versions(repo_name, component_name)
    assert len(tags) > 0, "Empty list returned %r" % tags
    assert version_tag in tags, "For %r/%r lack of version: %r in tags %r" % (
        repo_name,
        component_name,
        version_tag,
        tags,
    )


def test_fetch_docker_images_versions():
    check_docker_versions("gliderlabs", "logspout", "v3.1")
    check_docker_versions("nicolargo", "glances", "v2.11.1")


def test_fetch_versions_no_repo():
    tags = fetch_versions("repo_not_exists", "image_not_exists")
    assert len(tags) == 0, "Empty list returned %r" % tags


def test_component_checker_newer_version():
    checker = Component("nicolargo", "glances", "v2.0.0")
    assert checker.check() is True
    checker = Component("nicolargo", "glances", "v100.0.0")
    assert checker.check() is False


def test_save_next_version_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = ComponentsConfig(components_yaml_file=config_file)
    config.add(Component("gliderlabs", "logspout", "v3.1"))
    to_update = config.count_components_to_update()
    assert to_update == 1
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "next-version:" in file_content


def test_save_prefix_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = ComponentsConfig(components_yaml_file=config_file)
    config.add(Component("gliderlabs", "logspout", "v3.1"))
    config.components[0].prefix = "version_prefix"
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "version_prefix" in file_content


def test_exlude_versions_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = ComponentsConfig(components_yaml_file=config_file)
    config.add(Component("gliderlabs", "logspout", "v3.1"))
    config.components[0].exclude_versions = ["v3.2.6"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "exclude-versions: [v3.2.6]" in file_content


def test_save_files_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = ComponentsConfig(components_yaml_file=config_file)
    config.add(Component("gliderlabs", "logspout", "v3.1"))
    config.components[0].files = ["file1", "file2"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "[file1, file2]" in file_content


def test_use_filter_for_component_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = ComponentsConfig(components_yaml_file=config_file)
    config.add(Component("gliderlabs", "logspout", "v3.1"))
    config.components[0].prefix = "v"
    config.components[0].filter = "/^v\d+\.\d+\.\d+$/"
    config.components[0].check()
    assert config.components[0].next_version_tag == rex(config.components[0].filter)


def test_components_list_write_read_yaml_file(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = ComponentsConfig(components_yaml_file=config_file)
    config.add(Component("nicolargo", "glances", "v2.11.1"))
    config.add(Component("gliderlabs", "logspout", "v3.1"))
    dict1 = config.components_to_dict()
    config.save_to_yaml()
    config.read_from_yaml()
    dict2 = config.components_to_dict()
    assert dict1 == dict2


def test_components_to_dict(tmp_path):
    config = ComponentsConfig(tmp_path / "components.yaml")
    config.add(Component("nicolargo", "glances", "v2.11.1"))
    config.add(Component("gliderlabs", "logspout", "v3.1"))
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


def test_update_file_with_version(tmpdir):
    comp = Component("gliderlabs", "logspout", "v3.1")
    comp.files = ["file1"]
    comp.next_version = parse("v3.3")
    comp.next_version_tag = "v3.3"
    file1 = tmpdir / "file1"
    file1.write_text("v3.1", encoding=None)
    comp.update_files(tmpdir)
    assert "v3.3" in file1.read_text(encoding=None)


def test_update_file_with_version_wrong_file(tmpdir):
    comp = Component("gliderlabs", "logspout", "v3.1")
    comp.files = ["file2"]
    comp.next_version = parse("v3.3")
    comp.next_version_tag = "v3.3"
    file1 = tmpdir / "file1"
    file1.write_text("v3.1", encoding=None)
    with pytest.raises(AssertionError) as excinfo:
        comp.update_files(tmpdir)
    assert "No such file or directory" in str(excinfo.value)


def test_update_file_with_version_not_updated(tmpdir):
    comp = Component("gliderlabs", "logspout", "v3.1")
    comp.files = ["file1"]
    file1 = tmpdir / "file1"
    file1.write_text("v3.3", encoding=None)
    with pytest.raises(AssertionError) as excinfo:
        comp.update_files(tmpdir)
    assert "no replacement done for" in str(excinfo.value)


def config_from_copy_of_test_dir():
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(FIXTURE_DIR, test_dir)
    return test_dir, ComponentsConfig(test_dir / "components.yaml")


def test_update_components_files():
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    assert config.check() == [("glances", True), ("logspout", True)]
    assert config.update_files(test_dir) == 3


def test_dry_run_save_config():
    (test_dir, config) = config_from_copy_of_test_dir()
    config.read_from_yaml()
    content1 = config.config_file.read_text()
    config.save_changes(destination_file=None, dry_run=True, print_yaml=False)
    content2 = config.config_file.read_text()
    assert content1 == content2


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
    config.save_changes()
    assert "next-version: v3.2.6" not in config.config_file.read_text()
