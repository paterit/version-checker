import copy
import datetime
from pathlib import Path
import pprint
from subprocess import run
import pkg_resources


import click
import yaml
from loguru import logger
from plumbum import local

from updater import git_check, plumbum_msg, components


class Config:

    STATE_FILES_UPDATED = "FILES_UPDATED"
    STATE_TEST_RUN = "TEST_RUN"
    STATE_CONFIG_SAVED = "CONFIG_SAVED"
    STATE_COMMITED_CHANGES = "COMMITED_CHANGES"
    STATE_UPDATE_STARTED = "UPDATE_STARTED"
    STATE_UPDATE_SKIPPED = "UPDATE_SKIPPED"
    STATE_UPDATE_DONE = "UPDATE_DONE"

    def __init__(self, components_yaml_file=None):
        self.components = []
        self.config_file = components_yaml_file
        if self.config_file:
            if not self.config_file.is_file():
                logger.error(
                    "Config file %s exists but it is not file." % str(self.config_file)
                )
            self.project_dir = self.config_file.parent
        else:
            self.project_dir = None
        self.test_command = None
        self.test_dir = None
        self.git_commit = True
        self.status = {}

    def update_status(self, component, step):
        if component.component_name not in self.status:
            self.status[component.component_name] = {}
        comp = self.status[component.component_name]
        if step in [self.STATE_UPDATE_STARTED, self.STATE_UPDATE_SKIPPED]:
            message = (
                step
                + " for "
                + component.component_name
                + " in version "
                + component.current_version_tag
            )
        elif step in [self.STATE_UPDATE_DONE]:
            message = (
                step
                + " for "
                + component.component_name
                + " in version "
                + component.next_version_tag
            )
        else:
            message = step
        comp[str(datetime.datetime.now())] = message

    def get_status(self):
        return pprint.pformat(self.status, indent=4)

    def add(self, component):
        self.components.append(component)
        return self.components.index(self.components[-1])

    def components_to_dict(self):
        return {
            component.component_name: component.to_dict()
            for component in self.components
        }

    def save_to_yaml(self, file=None):
        file_to_save = Path(file) if file is not None else self.config_file
        yaml.dump(self.components_to_dict(), open(file_to_save, "w"))

    def save_config(self, destination_file=None, dry_run=False, print_yaml=False):
        if not dry_run:
            if destination_file:
                self.save_to_yaml(destination_file)
            elif self.config_file:
                self.save_to_yaml()

        if print_yaml:
            click.echo(pprint.pformat(yaml.dump(self.components_to_dict()), indent=4))

    def read_from_yaml(self, file=None):
        read_file = file or self.config_file
        self.components = []

        components_dict = (
            yaml.safe_load(open(read_file)) if read_file and read_file.is_file() else {}
        ) or {}

        for component_name in components_dict:
            compd = components_dict[component_name]
            params = {
                "component_type": compd["component-type"],
                "component_name": component_name,
                "current_version_tag": compd["current-version"],
                "repo_name": compd.get(
                    "docker-repo", components.Component.DEFAULT_REPO
                ),
            }
            last_index = self.add(components.factory.get(**params))
            comp = self.components[last_index]
            comp.repo_name = compd.get("docker-repo", comp.DEFAULT_REPO)
            comp.prefix = compd.get("prefix", comp.DEFAULT_PREFIX)
            comp.filter = compd.get("filter", comp.DEFAULT_FILTER)
            comp.files = compd.get("files", comp.DEFAULT_FILES)
            comp.exclude_versions = compd.get(
                "exclude-versions", comp.DEFAULT_EXLUDE_VERSIONS
            )
            comp.version_pattern = compd.get(
                "version-pattern", comp.DEFAULT_VERSION_PATTERN
            )

    def add_from_requirements(self, req_file=None, req_source=None):
        file_to_read = Path(req_file or self.project_dir / "./requirements.txt")
        assert (
            file_to_read.is_file()
        ), f"Requirements file {str(file_to_read)} does not exist."
        with file_to_read.open() as requirements_txt:
            for requirement in pkg_resources.parse_requirements(requirements_txt):
                if len(requirement.specs) == 0 or requirement.specs[0][0] != "==":
                    print(
                        f"{requirement.project_name} has incompatible version specifier: {requirement.specs}"
                    )
                    continue

                name, version = (requirement.project_name, requirement.specs[0][1])
                if not any(
                    x.component_name == name and x.component_type == "pypi"
                    for x in self.components
                ):
                    self.add(
                        components.factory.get(
                            component_type="pypi",
                            component_name=name,
                            current_version_tag=version,
                        )
                    )
                    comp = self.components[-1]
                    if req_source == "pipfile":
                        comp.version_pattern = '{component} = "=={version}"'
                        comp.files = ["Pipfile"]
                    elif req_source == "requirements":
                        comp.version_pattern = "{component}=={version}"
                        comp.files = ["requirements.txt"]
                    comp.filter = "/^" + (version.count(".")) * "\\d+\\." + "\\d+$/"

    def count_components_to_update(self):
        self.check()
        return sum(
            [1 for component in self.components if component.newer_version_exists()]
        )

    def check(self):
        return [(comp.component_name, comp.check()) for comp in self.components]

    def run_tests(self, processed_component):
        ret = run(self.test_command, cwd=(self.test_dir or self.project_dir))
        assert ret.returncode == 0, (
            click.style("Error!", fg="red")
            + "( "
            + processed_component.component_name
            + " ) "
            + str(ret)
        )

    def commit_changes(self, component, from_version, to_version, dry_run):
        git = local["git"]
        with local.cwd(self.config_file.parent):
            ret = git_check(git["diff", "--name-only"].run(retcode=None))
            changed_files = ret[1].splitlines()
            assert set(component.files).issubset(
                set(changed_files)
            ), "Not all SRC files are in git changed files.\n" + plumbum_msg(ret)
            if not dry_run:
                git_check(git["add", self.config_file.name].run(retcode=None))
                for file_name in component.files:
                    git_check(git["add", file_name].run(retcode=None))
                commit_message = (
                    f"{component.component_name} "
                    f"updated from: {from_version} to: {to_version}"
                )
                git_check(
                    git["commit", f"--message=%s" % commit_message].run(retcode=None)
                )

    # TODO move code for updating single component outside to new methods
    def update_files(self, dry_run=False):
        counter = 0
        for component in self.components:
            if component.newer_version_exists():
                orig_current_tag = component.current_version_tag
                orig_next_tag = component.next_version_tag
                self.update_status(component, self.STATE_UPDATE_STARTED)
                counter += component.update_files(self.project_dir, dry_run)
                self.update_status(component, self.STATE_FILES_UPDATED)
                if self.test_command:
                    self.run_tests(component)
                    self.update_status(component, self.STATE_TEST_RUN)

                if not dry_run:
                    component.current_version = copy.deepcopy(component.next_version)
                    component.current_version_tag = copy.deepcopy(
                        component.next_version_tag
                    )
                self.save_config(dry_run=dry_run)
                self.update_status(component, self.STATE_CONFIG_SAVED)

                if self.git_commit:
                    self.commit_changes(
                        component, orig_current_tag, orig_next_tag, dry_run
                    )
                    self.update_status(component, self.STATE_COMMITED_CHANGES)
                self.update_status(component, self.STATE_UPDATE_DONE)
            else:
                self.update_status(component, self.STATE_UPDATE_SKIPPED)

        return counter

    def get_versions_info(self):
        new = [
            c.component_name
            + " - current: "
            + c.current_version_tag
            + " next: "
            + (click.style(c.next_version_tag, fg="green"))
            for c in self.components
            if c.newer_version_exists()
        ]
        new.sort()
        return new

