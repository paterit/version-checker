from packaging.version import parse
from check_version import fetch_versions


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


def test_fetch_versions():
    tags = fetch_versions("gliderlabs", "logspout")
    assert len(tags) > 0, "Empty list returned %r" % tags


def test_fetch_versions_no_repo():
    tags = fetch_versions("repo_not_exists", "image_not_exists")
    assert len(tags) == 0, "Empty list returned %r" % tags
