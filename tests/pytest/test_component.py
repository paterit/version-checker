from packaging.version import parse
from updater.components import fetch_versions, Component
import pytest
from pathlib import Path


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
