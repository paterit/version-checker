from packaging.version import parse
from check_version import fetch_versions, ComponentChecker


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
    check_docker_versions("buildbot", "buildbot-master", "v1.1.0")


def test_fetch_versions_no_repo():
    tags = fetch_versions("repo_not_exists", "image_not_exists")
    assert len(tags) == 0, "Empty list returned %r" % tags


def test_component_checker_newer_version():
    checker = ComponentChecker("nicolargo", "glances", "v2.0.0")
    assert checker.check() is True
    checker = ComponentChecker("nicolargo", "glances", "v100.0.0")
    assert checker.check() is False
