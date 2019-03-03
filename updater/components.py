from loguru import logger
from packaging.version import parse
import requests
from cachier import cachier
import datetime
import yaml
from pathlib import Path
from rex import rex
from plumbum import local


class ComponentsConfig:
    def __init__(self, components_yaml_file=None):
        self.components = []
        self.config_file = components_yaml_file
        if self.config_file and not self.config_file.is_file():
            logger.info("Config file %r does not exists." % str(self.config_file))

    def add(self, component):
        self.components.append(component)

    def components_to_dict(self):
        return {
            component.component_name: component.to_dict()
            for component in self.components
        }

    def save_to_yaml(self, file=None):
        file_to_save = Path(file) if file is not None else self.config_file
        yaml.dump(self.components_to_dict(), open(file_to_save, "w"))

    def save_changes(self, destination_file=None, dry_run=False, print_yaml=False):
        if not dry_run:
            if destination_file:
                self.save_to_yaml(destination_file)
            elif self.config_file:
                self.save_to_yaml()

        if dry_run or print_yaml:
            print(yaml.dump(self.components_to_dict()))

    def read_from_yaml(self, file=None, clear_components=True):
        read_file = file or self.config_file
        if read_file and read_file.is_file():
            components_dict = yaml.safe_load(open(read_file))
        else:
            components_dict = {}

        if clear_components:
            self.components = []

        for component_name in components_dict:
            component = components_dict[component_name]
            self.add(
                Component(
                    repo_name=component["docker-repo"],
                    component_name=component_name,
                    current_version_tag=component["current-version"],
                )
            )
            self.components[-1].prefix = component.get(
                "prefix", Component.PREFIX_DEFAULT
            )
            self.components[-1].filter = component.get(
                "filter", Component.FILTER_DEFAULT
            )
            self.components[-1].files = component.get("files", Component.FILES_DEFAULT)
            self.components[-1].exclude_versions = component.get(
                "exclude-versions", Component.EXLUDE_VERSIONS_DEFAULT
            )

    def count_components_to_update(self):
        self.check()
        return sum(
            [1 for component in self.components if component.newer_version_exists()]
        )

    def check(self):
        return [(comp.component_name, comp.check()) for comp in self.components]

    def update_files(self, base_dir, dry_run=False):
        return sum(
            [
                comp.update_files(base_dir, dry_run)
                for comp in self.components
                if comp.newer_version_exists()
            ]
        )


class Component:

    PREFIX_DEFAULT = None
    FILTER_DEFAULT = "/.*/"
    FILES_DEFAULT = None
    EXLUDE_VERSIONS_DEFAULT = []

    def __init__(self, repo_name, component_name, current_version_tag):
        self.repo_name = repo_name
        self.component_name = component_name
        self.current_version_tag = current_version_tag
        self.current_version = parse(current_version_tag)
        self.version_tags = []
        self.next_version = self.current_version
        self.next_version_tag = self.current_version_tag
        self.prefix = self.PREFIX_DEFAULT
        self.filter = self.FILTER_DEFAULT
        self.files = self.FILES_DEFAULT
        self.exclude_versions = self.EXLUDE_VERSIONS_DEFAULT
        super().__init__()

    def newer_version_exists(self):
        return self.next_version > self.current_version

    def check(self):
        self.version_tags = fetch_versions(self.repo_name, self.component_name)
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
            "docker-repo": self.repo_name,
            "current-version": self.current_version_tag,
            "next-version": self.next_version_tag,
        }
        if self.prefix != self.PREFIX_DEFAULT:
            ret["prefix"] = self.prefix
        if self.filter != self.FILTER_DEFAULT:
            ret["filter"] = self.filter
        if self.files != self.FILES_DEFAULT:
            ret["files"] = self.files
        if self.exclude_versions != self.EXLUDE_VERSIONS_DEFAULT:
            ret["exclude-versions"] = self.exclude_versions
        return ret

    def update_files(self, base_dir, dry_run=False):
        sed = local["sed"]
        counter = 0

        for file_name in self.files:
            file = Path(Path(base_dir) / file_name)
            path = str(file.absolute())
            ret = sed[
                "-n",
                "s|" + self.current_version_tag + "|" + self.next_version_tag + "|p",
                path,
            ].run(retcode=None)
            assert ret[0] == 0, "Error in version replacment: sed error %r\n" % str(ret)
            assert ret[1] != "", (
                "Error in version replacment: no replacement done for current_version: %r and next_version: %r.\n %r"
                % (self.current_version_tag, self.next_version_tag, str(ret))
            )
            if not dry_run:
                ret = sed[
                    "-i",
                    "s|" + self.current_version_tag + "|" + self.next_version_tag + "|",
                    path,
                ].run(retcode=None)
            counter += 1
        return counter


@cachier(stale_after=datetime.timedelta(days=3))
def fetch_versions(repo_name, component):
    logger.info(repo_name + ":" + component + " - NOT CACHED")
    payload = {
        "service": "registry.docker.io",
        "scope": "repository:{repo}/{image}:pull".format(
            repo=repo_name, image=component
        ),
    }

    r = requests.get("https://auth.docker.io/token", params=payload)
    if not r.status_code == 200:
        print("Error status {}".format(r.status_code))
        raise Exception("Could not get auth token")

    j = r.json()
    token = j["token"]
    h = {"Authorization": "Bearer {}".format(token)}
    r = requests.get(
        "https://index.docker.io/v2/{}/{}/tags/list".format(repo_name, component),
        headers=h,
    )
    return r.json().get("tags", [])
