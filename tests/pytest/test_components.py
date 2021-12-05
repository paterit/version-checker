from packaging.version import parse
from updater import components
import pytest
from pathlib import Path


FIXTURE_DIR = Path(".").absolute() / "tests/test_files"

COMP = {
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


def compare_versions(old: str, new: str):
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


def check_docker_images_versions(repo_name: str, component_name: str, version_tag: str):
    tags = components.fetch_docker_images_versions(repo_name, component_name)
    assert len(tags) > 0, f"Empty list returned {tags}"
    assert (
        version_tag in tags
    ), f"For {repo_name}/{component_name} lack of version: {version_tag} in tags {tags}"


def check_pypi_versions(component_name: str, version_tag: str):
    tags = components.fetch_pypi_versions(component_name)
    assert len(tags) > 0, f"Empty list returned {tags}"
    assert (
        version_tag in tags
    ), f"For {component_name} lack of version: {version_tag} in tags {tags}"


def test_fetch_docker_images_versions():
    check_docker_images_versions("gliderlabs", "logspout", "v3.1")
    check_docker_images_versions("nicolargo", "glances", "v2.11.1")
    check_docker_images_versions("library", "python", "3.6.6-alpine3.8")


def test_fetch_pypi_versions():
    check_pypi_versions("Django", "2.1.2")
    check_pypi_versions("requests", "2.20.0")


def test_fetch_docker_images_versions_no_repo():
    tags = components.fetch_docker_images_versions(
        "repo_not_exists", "image_not_exists"
    )
    assert len(tags) == 0, f"Empty list returned {tags}"


def test_fetch_pypi_versions_no_repo():
    tags = components.fetch_pypi_versions("package_not_exists")
    assert len(tags) == 0, f"Empty list returned {tags}"


def test_component_checker_newer_version():
    glances_old = {**COMP["glances"], "current_version_tag": "v2.0.0"}
    glances_new = {**COMP["glances"], "current_version_tag": "v100.0.0"}
    glances_latest = {**COMP["glances"], "current_version_tag": "latest"}
    checker = components.factory.get(**glances_old)
    assert checker.check() is True
    checker = components.factory.get(**glances_new)
    assert checker.check() is False
    checker = components.factory.get(**glances_latest)
    assert checker.check() is False


def test_update_file_with_version(tmpdir: Path):
    comp = components.factory.get(**COMP["logspout"])
    comp.files = ["file1"]
    comp.next_version = parse("v3.3")
    comp.next_version_tag = "v3.3"
    file1 = tmpdir / "file1"
    file1.write_text("gliderlabs/logspout:v3.1", encoding=None)
    comp.update_files(tmpdir)
    assert "v3.3" in file1.read_text(encoding=None)


def test_update_file_with_wrong_dir():
    comp = components.factory.get(**COMP["logspout"])
    with pytest.raises(FileNotFoundError) as excinfo:
        comp.update_files(None)
        assert "base_dir is None" in str(excinfo.value)


def test_update_file_with_version_wrong_file(tmpdir: Path):
    comp = components.factory.get(**COMP["logspout"])
    comp.files = ["file2"]
    with pytest.raises(FileNotFoundError) as excinfo:
        comp.update_files(tmpdir)
        assert "No such file or directory" in str(excinfo.value)


def test_update_file_with_double_entry_for_component(tmpdir: Path):
    comp = components.factory.get(**COMP["logspout"])
    comp.files = ["file1"]
    comp.next_version = parse("v3.3")
    comp.next_version_tag = "v3.3"
    file1 = tmpdir / "file1"
    file1.write_text(
        "gliderlabs/logspout:v3.1\ngliderlabs/logspout:v3.1", encoding=None
    )
    with pytest.raises(Exception) as excinfo:
        comp.update_files(tmpdir)
        assert "Too many versions of" in str(excinfo.value)


def test_update_file_with_version_not_updated(tmpdir: Path):
    comp = components.factory.get(**COMP["logspout"])
    comp.files = ["file1"]
    file1 = tmpdir / "file1"
    file1.write_text("v3.3", encoding=None)
    with pytest.raises(Exception) as excinfo:
        comp.update_files(tmpdir)
        assert "no replacement done for" in str(excinfo.value)


def test_update_file_with_two_components_with_same_version_tag_pypi(tmpdir: Path):
    comp = components.factory.get(**COMP["Django"])
    comp.next_version_tag = "2.2.2"
    comp.files = ["file1"]
    file1 = tmpdir / "file1"
    file1.write_text("Django==2.1.2\nrequests==2.1.2", encoding=None)
    comp.update_files(tmpdir)
    assert "requests==2.1.2" in file1.read_text(encoding=None)


def test_docker_image_name_version_tag():
    comp = components.factory.get(**COMP["glances"])
    assert comp.name_version_tag(comp.current_version_tag) == "glances:v2.11.1"


def test_wrong_component_type():
    glances = {**COMP["glances"], "component_type": "not_exists"}
    with pytest.raises(ValueError) as excinfo:
        components.factory.get(**glances)
        assert "not implemented" in str(excinfo.value)


@pytest.mark.slow
def test_clear_versions_cache():
    check_pypi_versions("Django", "2.1.2")
    check_docker_images_versions("gliderlabs", "logspout", "v3.1")
    components.clear_versions_cache()
    check_pypi_versions("Django", "2.1.2")
    check_docker_images_versions("gliderlabs", "logspout", "v3.1")
    assert True


@pytest.mark.slow
def test_error_in_getting_token_for_docker_image_version_info():
    with pytest.raises(Exception) as excinfo:
        components.fetch_docker_images_versions(
            "gliderlabs",
            "logspout",
            token_url="https://auth.docker.io/token_get_400_error",
        )
        assert "Could not get auth token" in str(excinfo.value)


def test_components_to_dict(tmp_path: Path):

    components_list = []
    components_list.append(components.factory.get(**COMP["glances"]))
    components_list.append(components.factory.get(**COMP["logspout"]))
    components_list.append(components.factory.get(**COMP["Django"]))
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
    assert result == components.Component.components_to_dict(components_list)
