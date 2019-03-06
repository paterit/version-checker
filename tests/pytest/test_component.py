from packaging.version import parse
from updater import components
import pytest
from pathlib import Path


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
    tags = components.fetch_versions(repo_name, component_name)
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
    tags = components.fetch_versions("repo_not_exists", "image_not_exists")
    assert len(tags) == 0, "Empty list returned %r" % tags


def test_component_checker_newer_version():
    glances_old = {**glances, "current_version_tag": "v2.0.0"}
    glances_new = {**glances, "current_version_tag": "v100.0.0"}
    checker = components.factory.get(**glances_old)
    assert checker.check() is True
    checker = components.factory.get(**glances_new)
    assert checker.check() is False


def test_update_file_with_version(tmpdir):
    comp = components.factory.get(**logspout)
    comp.files = ["file1"]
    comp.next_version = parse("v3.3")
    comp.next_version_tag = "v3.3"
    file1 = tmpdir / "file1"
    file1.write_text("v3.1", encoding=None)
    comp.update_files(tmpdir)
    assert "v3.3" in file1.read_text(encoding=None)


def test_update_file_with_version_wrong_file(tmpdir):
    comp = components.factory.get(**logspout)
    comp.files = ["file2"]
    comp.next_version = parse("v3.3")
    comp.next_version_tag = "v3.3"
    file1 = tmpdir / "file1"
    file1.write_text("v3.1", encoding=None)
    with pytest.raises(AssertionError) as excinfo:
        comp.update_files(tmpdir)
    assert "No such file or directory" in str(excinfo.value)


def test_update_file_with_version_not_updated(tmpdir):
    comp = components.factory.get(**logspout)
    comp.files = ["file1"]
    file1 = tmpdir / "file1"
    file1.write_text("v3.3", encoding=None)
    with pytest.raises(AssertionError) as excinfo:
        comp.update_files(tmpdir)
    assert "no replacement done for" in str(excinfo.value)
