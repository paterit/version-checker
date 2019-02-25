from loguru import logger
from packaging.version import parse
import requests
from cachier import cachier
import datetime
import yaml
from pathlib import Path
import click
from rex import rex


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
        yaml.dump(
            self.components_to_dict(), open(file_to_save, "w"), default_flow_style=False
        )

    def read_from_yaml(self, file=None, clear_components=True):
        read_file = file or self.config_file
        if read_file and read_file.is_file():
            components_dict = yaml.load(open(read_file))
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

    def count_components_to_update(self):
        return sum([1 for component in self.components if component.check()])


class Component:

    PREFIX_DEFAULT = None
    FILTER_DEFAULT = "/.*/"

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
        super().__init__()

    def newer_version_exists(self):
        return self.next_version > self.current_version

    def check(self):
        self.version_tags = fetch_versions(self.repo_name, self.component_name)
        self.next_version = max(
            [parse(tag) for tag in self.version_tags if (tag == rex(self.filter))]
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
        return ret


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


@click.command()
@click.option(
    "--file",
    type=click.Path(exists=True, writable=True),
    help="YAML file with components configuration. If not present other options need to be given.",
)
@click.option(
    "--destination-file",
    "destination_file",
    type=click.Path(),
    help="If this option is given components configuration will be wrtten here.",
)
@click.option("--component", help="Component name to version veryfication.")
@click.option("--repo_name", help="Repository name if component is docker image.")
@click.option(
    "--version_tag",
    help="Version tag eg. v2.3.0 against which new version check will be run.",
)
@click.option("--dry-run", "dry_run", is_flag=True)
def main(file, component, repo_name, version_tag, destination_file, dry_run):
    if file is not None:
        config_file = Path(file).absolute()
    elif Path.cwd().absolute().joinpath("components.yaml").is_file():
        config_file = Path.cwd().absolute().joinpath("components.yaml")
    else:
        config_file = None

    config = ComponentsConfig(components_yaml_file=config_file)
    config.read_from_yaml()

    if component is not None:
        config.add(
            Component(
                repo_name=repo_name,
                component_name=component,
                current_version_tag=version_tag,
            )
        )

    ret_mess = []
    ret_mess.append("%r components to check" % len(config.components))
    ret_mess.append("%r components to update" % config.count_components_to_update())

    if not dry_run:
        if destination_file:
            config.save_to_yaml(destination_file)
        elif config_file:
            config.save_to_yaml(config_file)
    else:
        print(yaml.dump(config.components_to_dict(), default_flow_style=False))

    print("\n".join(ret_mess))


if __name__ == "__main__":
    main()
