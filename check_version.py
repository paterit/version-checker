import sys
from loguru import logger
from packaging.version import parse
import requests
from cachier import cachier
import datetime
import yaml


EXIT_CODE_ERROR = 1
EXIT_CODE_SUCCESS = 0


class ComponentsConfig:
    def __init__(self):
        self.components = []
        self.config_file_name = "components.yaml"

    def add(self, component):
        self.components.append(component)

    def components_to_dict(self):
        return {
            component.component_name: component.to_dict()
            for component in self.components
        }

    def save_to_yaml(self, file_path=None):
        yaml.dump(
            self.components_to_dict(),
            open(file_path or self.config_file_name, "w"),
            default_flow_style=False,
        )

    def read_from_yaml(self, file_path=None, clear_components=True):
        components_dict = yaml.load(open(file_path or self.config_file_name))
        if clear_components:
            self.components = []
        for component_name in components_dict:
            component = components_dict[component_name]
            self.add(
                Component(
                    repo_name=component["docker-repo"],
                    component_name=component_name,
                    current_version_tag=component["current_version"],
                )
            )

    def count_components_to_update(self):
        return sum([1 for component in self.components if component.check()])


class Component:
    def __init__(self, repo_name, component_name, current_version_tag):
        self.repo_name = repo_name
        self.component_name = component_name
        self.current_version_tag = current_version_tag
        self.current_version = parse(current_version_tag)
        self.version_tags = []
        self.highest_version = self.current_version
        super().__init__()

    def newer_version_exists(self):
        return self.highest_version > self.current_version

    def check(self):
        self.version_tags = fetch_versions(self.repo_name, self.component_name)
        self.highest_version = max([parse(tag) for tag in self.version_tags])

        return self.newer_version_exists()

    def to_dict(self):
        return {
            "docker-repo": self.repo_name,
            "current_version": self.current_version_tag,
        }


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


if __name__ == "__main__":
    config = ComponentsConfig()
    if len(sys.argv) == 4:
        component_name = sys.argv[1]
        repo_name = sys.argv[2]
        version_tag = sys.argv[3]
        config.add(Component(repo_name, component_name, version_tag))
    else:
        config.read_from_yaml()

    ret_mess = []
    ret_mess.append("%r components to check" % len(config.components))
    ret_mess.append("%r components to update" % config.count_components_to_update())

    print("\n".join(ret_mess))
