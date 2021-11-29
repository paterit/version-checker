import datetime
from abc import ABCMeta, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from cachier import cachier  # type: ignore
from loguru import logger
from packaging.version import LegacyVersion, Version, parse
from requests.models import Response
from rex import rex  # type: ignore

TVer = Union[LegacyVersion, Version]
TVerList = List[TVer]
TFileNameList = List[str]
TDictComponent = Dict[str, Union[Optional[str], TVer, TFileNameList, List[TVer]]]


class ComponentType(Enum):
    DOCKER = "docker-image"
    PYPI = "pypi"


class Component(metaclass=ABCMeta):

    DEFAULT_PREFIX: Optional[str] = None
    DEFAULT_FILTER: str = "/.*/"
    DEFAULT_FILES: TFileNameList = []
    DEFAULT_EXLUDE_VERSIONS: List[str] = []
    DEFAULT_REPO: Optional[str] = None
    LATEST_TAGS: List[str] = ["latest"]
    DEFAULT_VERSION_PATTERN: str = "{version}"

    def __init__(
        self,
        component_type: ComponentType,
        component_name: str,
        current_version_tag: str,
    ) -> None:
        self.component_type = component_type
        self.component_name: str = component_name
        self.current_version_tag: str = current_version_tag
        self.current_version: TVer = parse(current_version_tag)
        self.version_tags: List[str] = []
        self.next_version: TVer = self.current_version
        self.next_version_tag: str = self.current_version_tag
        self.prefix: Optional[str] = self.DEFAULT_PREFIX
        self.filter: str = self.DEFAULT_FILTER
        self.files: TFileNameList = self.DEFAULT_FILES
        self.exclude_versions: List[str] = self.DEFAULT_EXLUDE_VERSIONS
        self.version_pattern = self.DEFAULT_VERSION_PATTERN
        super().__init__()

    def newer_version_exists(self) -> bool:
        if self.current_version_tag in self.LATEST_TAGS:
            return False
        else:
            return self.next_version > self.current_version

    @abstractmethod
    def fetch_versions_tags(self) -> List[str]:
        """should return a list of versions eg.: ('1.0.1', '2.0.2')"""
        pass  # pragma: no cover

    # TODO move max statement after self.next_version= to new mehtod: get_max_version_number()
    def check(self) -> bool:
        if self.current_version_tag not in self.LATEST_TAGS:
            self.version_tags = self.fetch_versions_tags()

            self.next_version = max(
                [
                    parse(tag)
                    for tag in self.version_tags
                    if (tag == rex(self.filter)) and tag not in self.exclude_versions
                ]
            )
            self.next_version_tag = f"{(self.prefix or '')}{str(self.next_version)}"

        return self.newer_version_exists()

    def to_dict(self) -> TDictComponent:
        ret: TDictComponent = {
            "component-type": self.component_type.value,
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

    def name_version_tag(self, version_tag: str) -> str:
        d: Dict[str, str] = {"version": version_tag, "component": self.component_name}
        return self.version_pattern.format(**d)

    def count_occurence(self, string_to_search: str) -> int:
        return string_to_search.count(self.name_version_tag(self.current_version_tag))

    def replace(self, string_to_replace: str) -> str:
        return string_to_replace.replace(
            self.name_version_tag(self.current_version_tag),
            self.name_version_tag(self.next_version_tag),
        )

    def update_files(self, base_dir: Optional[Path], dry_run: bool = False) -> int:
        counter: int = 0
        if base_dir is None:
            raise FileNotFoundError("base_dir is None")
        for file_name in self.files:
            file = Path(base_dir / file_name)
            orig_content: str = file.read_text()
            if self.count_occurence(orig_content) > 1:
                logger.error(
                    f"Too many versions of {self.current_version_tag} occurence in {orig_content}!"
                )
                raise Exception(
                    f"Too many versions of {self.current_version_tag} occurence in {orig_content}!"
                )

            if not dry_run:
                new_content: str = self.replace(orig_content)
                if new_content == orig_content:
                    logger.error(
                        (
                            f"Error in version replacment for {self.component_name}: "
                            f"no replacement done for current_version"
                            f": {self.name_version_tag(self.current_version_tag)} "
                            f"and next_version: {self.name_version_tag(self.next_version_tag)} "
                            f"in file: {str(file)}"
                        )
                    )
                    raise Exception(
                        f"Error in version replacment for {self.component_name}: no replacement done for current_version"
                    )
                file.write_text(new_content)
            counter += 1
        return counter


def clear_versions_cache() -> None:
    fetch_docker_images_versions.clear_cache()  # type: ignore
    fetch_pypi_versions.clear_cache()  # type: ignore


@cachier(stale_after=datetime.timedelta(days=3))  # type: ignore[misc]
def fetch_docker_images_versions(
    repo_name: str, component_name: str, token_url: Optional[str] = None
) -> List[str]:
    logger.info(f"{repo_name}:{component_name} - NOT CACHED")
    payload: Dict[str, str] = {
        "service": "registry.docker.io",
        "scope": f"repository:{repo_name}/{component_name}:pull",
    }
    r: Response = requests.get(
        token_url or DockerImageComponent.TOKEN_URL, params=payload
    )
    if not r.status_code == 200:
        print(f"Error status {r.status_code}")
        raise Exception("Could not get auth token")

    token: str = r.json()["token"]
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(
        f"https://index.docker.io/v2/{repo_name}/{component_name}/tags/list", headers=h
    )
    ret: List[str] = r.json().get("tags", [])
    return ret


@cachier(stale_after=datetime.timedelta(days=3))  # type: ignore[misc]
def fetch_pypi_versions(component_name: str) -> List[str]:
    r: Response = requests.get(f"https://pypi.org/pypi/{component_name}/json")
    # it returns 404 if there is no such a package
    if not r.status_code == 200:
        return list()
    else:
        return list(r.json().get("releases", {}).keys())


class DockerImageComponent(Component):

    DEFAULT_VERSION_PATTERN: str = "{component}:{version}"
    TOKEN_URL: str = "https://auth.docker.io/token"

    def __init__(
        self, repo_name: str, component_name: str, current_version_tag: str
    ) -> None:
        super(DockerImageComponent, self).__init__(
            ComponentType.DOCKER, component_name, current_version_tag
        )
        self.repo_name = repo_name
        self.version_pattern = self.DEFAULT_VERSION_PATTERN

    def fetch_versions_tags(self) -> List[str]:
        return fetch_docker_images_versions(self.repo_name, self.component_name)

    def to_dict(self) -> TDictComponent:
        ret: TDictComponent = super(DockerImageComponent, self).to_dict()
        ret["docker-repo"] = self.repo_name
        return ret


class PypiComponent(Component):

    DEFAULT_VERSION_PATTERN: str = "{component}=={version}"

    def __init__(
        self, component_name: str, current_version_tag: str, **_ignored: Any
    ) -> None:
        super(PypiComponent, self).__init__(
            ComponentType.PYPI, component_name, current_version_tag
        )
        self.version_pattern = self.DEFAULT_VERSION_PATTERN

    def fetch_versions_tags(self) -> List[str]:
        return fetch_pypi_versions(self.component_name)


class ComponentFactory:
    def get(self, component_type: str, **args: Any) -> Component:
        if component_type == ComponentType.DOCKER.value:
            return DockerImageComponent(**args)
        elif component_type == ComponentType.PYPI.value:
            return PypiComponent(**args)
        else:
            raise ValueError(f"Componet type: {component_type} :not implemented!")


factory = ComponentFactory()
