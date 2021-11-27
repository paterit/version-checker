import datetime
from abc import ABC, abstractmethod
from pathlib import Path

import requests
from cachier import cachier
from loguru import logger
from packaging.version import parse
from rex import rex


class Component(ABC):

    DEFAULT_PREFIX = None
    DEFAULT_FILTER = "/.*/"
    DEFAULT_FILES = None
    DEFAULT_EXLUDE_VERSIONS = []
    DEFAULT_REPO = None
    LATEST_TAGS = ["latest"]
    DEFAULT_VERSION_PATTERN = "{version}"

    def __init__(self, component_name, current_version_tag):
        self.component_type = None
        self.component_name = component_name
        self.current_version_tag = current_version_tag
        self.current_version = parse(current_version_tag)
        self.version_tags = []
        self.next_version = self.current_version
        self.next_version_tag = self.current_version_tag
        self.prefix = self.DEFAULT_PREFIX
        self.filter = self.DEFAULT_FILTER
        self.files = self.DEFAULT_FILES
        self.exclude_versions = self.DEFAULT_EXLUDE_VERSIONS
        self.version_pattern = self.DEFAULT_VERSION_PATTERN
        super().__init__()

    def newer_version_exists(self):
        if self.current_version_tag in self.LATEST_TAGS:
            return False
        else:
            return self.next_version > self.current_version

    @abstractmethod
    def fetch_versions():
        """should return a list of versions eg.: ('1.0.1', '2.0.2')"""

    # TODO move max statement after self.next_version= to new mehtod: get_max_version_number()
    def check(self):
        if self.current_version_tag not in self.LATEST_TAGS:
            self.version_tags = self.fetch_versions()

            self.next_version = max(
                [
                    parse(tag)
                    for tag in self.version_tags
                    if (tag == rex(self.filter)) and tag not in self.exclude_versions
                ]
            )
            self.next_version_tag = (self.prefix or "") + str(self.next_version)

        return self.newer_version_exists()

    def to_dict(self):
        ret = {
            "component-type": self.component_type,
            "current-version": self.current_version_tag,
            "next-version": self.next_version_tag,
        }

        if self.prefix != self.DEFAULT_PREFIX:
            ret["prefix"] = self.prefix
        if self.filter != self.DEFAULT_FILTER:
            ret["filter"] = self.filter
        if self.files != self.DEFAULT_FILES:
            ret["files"] = self.files
        if self.exclude_versions != self.DEFAULT_EXLUDE_VERSIONS:
            ret["exclude-versions"] = self.exclude_versions
        if self.version_pattern != self.DEFAULT_VERSION_PATTERN:
            ret["version-pattern"] = self.version_pattern
        return ret

    def name_version_tag(self, version_tag):
        d = {"version": version_tag, "component": self.component_name}
        return self.version_pattern.format(**d)

    def count_occurence(self, string_to_search):
        return string_to_search.count(self.name_version_tag(self.current_version_tag))

    def replace(self, string_to_replace):
        return string_to_replace.replace(
            self.name_version_tag(self.current_version_tag),
            self.name_version_tag(self.next_version_tag),
        )

    def update_files(self, base_dir, dry_run=False):
        counter = 0

        for file_name in self.files:
            file = Path(Path(base_dir) / file_name)
            orig_content = file.read_text()
            if self.count_occurence(orig_content) > 1:
                logger.error(
                    "Too many versions of %s occurence in %s!"
                    % (self.current_version_tag, orig_content)
                )
                raise Exception(
                    "Too many versions of %s occurence in %s!"
                    % (self.current_version_tag, orig_content)
                )

            if not dry_run:
                new_content = self.replace(orig_content)
                if new_content == orig_content:
                    logger.error(
                        "Error in version replacment for %s: no replacement done for current_version"
                        % self.component_name
                        + ": %s and next_version: %s in file: %s"
                        % (
                            self.name_version_tag(self.current_version_tag),
                            self.name_version_tag(self.next_version_tag),
                            str(file),
                        )
                    )
                    raise Exception(
                        "Error in version replacment for %s: no replacement done for current_version"
                        % self.component_name
                    )
                file.write_text(new_content)
            counter += 1
        return counter


# TODO mark as deprecated
def clear_docker_images_cache():
    clear_versions_cache()


def clear_versions_cache():
    fetch_docker_images_versions.clear_cache()
    fetch_pypi_versions.clear_cache()


@cachier(stale_after=datetime.timedelta(days=3))
def fetch_docker_images_versions(repo_name, component_name, token_url=None):
    logger.info(repo_name + ":" + component_name + " - NOT CACHED")
    payload = {
        "service": "registry.docker.io",
        "scope": "repository:{repo}/{image}:pull".format(
            repo=repo_name, image=component_name
        ),
    }
    token_url = token_url or DockerImageComponent.TOKEN_URL
    r = requests.get(token_url, params=payload)
    if not r.status_code == 200:
        print("Error status {}".format(r.status_code))
        raise Exception("Could not get auth token")

    j = r.json()
    token = j["token"]
    h = {"Authorization": "Bearer {}".format(token)}
    r = requests.get(
        "https://index.docker.io/v2/{}/{}/tags/list".format(repo_name, component_name),
        headers=h,
    )
    return r.json().get("tags", [])


@cachier(stale_after=datetime.timedelta(days=3))
def fetch_pypi_versions(component_name):
    r = requests.get("https://pypi.org/pypi/{}/json".format(component_name))
    # it returns 404 if there is no such a package
    if not r.status_code == 200:
        return list()
    else:
        return list(r.json().get("releases", {}).keys())


class DockerImageComponent(Component):

    DEFAULT_VERSION_PATTERN = "{component}:{version}"
    TOKEN_URL = "https://auth.docker.io/token"

    def __init__(self, repo_name, component_name, current_version_tag):
        super(DockerImageComponent, self).__init__(component_name, current_version_tag)
        self.repo_name = repo_name
        self.component_type = "docker-image"
        self.version_pattern = self.DEFAULT_VERSION_PATTERN

    def fetch_versions(self):
        return fetch_docker_images_versions(self.repo_name, self.component_name)

    def to_dict(self):
        ret = super(DockerImageComponent, self).to_dict()
        ret["docker-repo"] = self.repo_name
        return ret


class PypiComponent(Component):

    DEFAULT_VERSION_PATTERN = "{component}=={version}"

    def __init__(self, component_name, current_version_tag, **_ignored):
        super(PypiComponent, self).__init__(component_name, current_version_tag)
        self.component_type = "pypi"
        self.version_pattern = self.DEFAULT_VERSION_PATTERN

    def fetch_versions(self):
        return fetch_pypi_versions(self.component_name)


class ComponentFactory:
    def get(self, component_type, **args):
        if component_type == "docker-image":
            return DockerImageComponent(**args)
        elif component_type == "pypi":
            return PypiComponent(**args)
        else:
            raise ValueError("Componet type: " + component_type + " :not implemented!")


factory = ComponentFactory()
