from packaging.version import parse
from check_version import fetch_versions, Component, ComponentsConfig
import pytest
from pathlib import Path
from rex import rex


FIXTURE_DIR = Path(".").absolute() / "test_files"


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


def test_use_filter_for_component_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = ComponentsConfig(components_yaml_file=config_file)
    config.add(Component("gliderlabs", "logspout", "v3.1"))
    config.components[0].prefix = "v"
    config.components[0].filter = "/^v\d+\.\d+\.\d+$/"
    config.components[0].check()
    assert config.components[0].next_version_tag == rex(config.components[0].filter)


# @pytest.mark.datafiles(FIXTURE_DIR / "components.yaml")
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
