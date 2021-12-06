import copy
import datetime
from enum import Enum
from pathlib import Path
import pprint
from subprocess import run
from typing import Any, Dict, List, Optional, Tuple
import pkg_resources

import click
import yaml
from loguru import logger
from plumbum import local  # type: ignore

from updater import TPlumbumRunReturn, git_check, plumbum_msg, components
from updater.components import ComponentType, Component


class ImportType(Enum):
    PIPENV = "pipfile"
    PYPI = "requirements"
    POETRY = "poetry"


class Config:

    STATE_FILES_UPDATED = "FILES_UPDATED"
    STATE_TEST_RUN = "TEST_RUN"
    STATE_CONFIG_SAVED = "CONFIG_SAVED"
    STATE_COMMITED_CHANGES = "COMMITED_CHANGES"
    STATE_UPDATE_STARTED = "UPDATE_STARTED"
    STATE_UPDATE_SKIPPED = "UPDATE_SKIPPED"
    STATE_UPDATE_DONE = "UPDATE_DONE"

    def __init__(self, components_yaml_file: Optional[Path] = None) -> None:
        self.components: List[Component] = []
        self.config_file = components_yaml_file
        self.project_dir: Optional[
            Path
        ] = self.config_file.parent if self.config_file else None
        self.test_command: Optional[List[str]] = None
        self.test_dir: Optional[Path] = None
        self.git_commit: bool = True
        self.status: Dict[str, Dict[str, str]] = {}

    def update_status(self, component: Component, step: str) -> None:
        if component.component_name not in self.status:
            self.status[component.component_name] = {}
        comp = self.status[component.component_name]
        if step in [self.STATE_UPDATE_STARTED, self.STATE_UPDATE_SKIPPED]:
            message = f"{step} for {component.component_name} in version {component.current_version_tag}"
        elif step in [self.STATE_UPDATE_DONE]:
            message = f"{step} for {component.component_name} in version {component.next_version_tag}"
        else:
            message = step
        comp[str(datetime.datetime.now())] = message

    def get_status(self) -> str:
        return pprint.pformat(self.status, indent=4)

    def add(self, component: Component) -> int:
        self.components.append(component)
        return self.components.index(self.components[-1])

    def save_to_yaml(self, file: Optional[str] = None) -> None:
        path = file or self.config_file
        if path:
            file_to_save: Path = Path(path)
            yaml.dump(
                Component.components_to_dict(self.components), open(file_to_save, "w")
            )
        else:
            logger.error(
                f"No config file provided and no config file found in project directory."
            )
            raise FileNotFoundError(
                "No config file provided and no config file found in project directory."
            )

    def save_config(
        self,
        destination_file: Optional[str] = None,
        dry_run: bool = False,
        print_yaml: bool = False,
    ) -> None:
        if not dry_run:
            if destination_file:
                self.save_to_yaml(destination_file)
            elif self.config_file:
                self.save_to_yaml()

        if print_yaml:
            click.echo(
                pprint.pformat(
                    yaml.dump(Component.components_to_dict(self.components)), indent=4
                )
            )

    def read_from_yaml(self, file: Optional[Path] = None) -> None:
        read_file = file or self.config_file
        self.components = []

        components_dict: Dict[str, Any] = (
            yaml.safe_load(open(read_file)) if read_file and read_file.is_file() else {}
        ) or {}

        for component_name in components_dict:
            compd = components_dict[component_name]
            params: components.TDictComponent = {
                "component_name": component_name,
                "current_version_tag": compd["current-version"],
                "repo_name": compd.get("docker-repo", Component.DEFAULT_REPO),
            }
            last_index = self.add(
                components.factory.get(str(compd["component-type"]), **params)
            )
            comp = self.components[last_index]
            comp.prefix = compd.get("prefix", comp.DEFAULT_PREFIX)
            comp.filter = compd.get("filter", comp.DEFAULT_FILTER)
            comp.files = compd.get("files", comp.DEFAULT_FILES)
            comp.exclude_versions = compd.get(
                "exclude-versions", comp.DEFAULT_EXLUDE_VERSIONS
            )
            comp.version_pattern = compd.get(
                "version-pattern", comp.DEFAULT_VERSION_PATTERN
            )
            comp.files_version_pattern = compd.get(
                "files-version-pattern", comp.DEFAULT_FILES_VERSION_PATTERN
            )

    def add_from_requirements(self, req_file: str, req_source: str) -> None:

        file_to_read = Path(req_file)
        if not file_to_read.is_file():
            logger.error(f"File {file_to_read} not found.")
            raise FileNotFoundError(f"Missing file for import: {file_to_read}")
        with file_to_read.open() as requirements_txt:
            for requirement in pkg_resources.parse_requirements(requirements_txt):
                if len(requirement.specs) == 0 or requirement.specs[0][0] != "==":
                    print(
                        f"{requirement.project_name} has incompatible version specifier: {requirement.specs}"
                    )
                    continue

                name, version = (requirement.project_name, requirement.specs[0][1])
                if not any(
                    x.component_name == name and x.component_type == ComponentType.PYPI
                    for x in self.components
                ):
                    self.add(
                        components.factory.get(
                            component_type=ComponentType.PYPI.value,
                            component_name=name,
                            current_version_tag=version,
                        )
                    )
                    comp = self.components[-1]
                    if req_source == ImportType.PYPI.value:
                        comp.version_pattern = '{component} = "=={version}"'
                        comp.files = ["Pipfile"]
                    elif req_source == ImportType.PIPENV.value:
                        comp.version_pattern = "{component}=={version}"
                        comp.files = ["requirements.txt"]
                    elif req_source == ImportType.POETRY.value:
                        comp.version_pattern = '{component} = "^{version}"'
                        comp.files = ["pyproject.toml"]
                    comp.filter = (
                        "/^" + (version.count(".")) * "\\d+\\." + "\\d+$/"
                    )  # due ot backslash being forbidden in f-strings inside curly braces

    def count_components_to_update(self) -> int:
        self.check()
        return sum(
            [1 for component in self.components if component.newer_version_exists()]
        )

    def check(self) -> List[Tuple[str, bool]]:
        return [(comp.component_name, comp.check()) for comp in self.components]

    def run_tests(self, processed_component: Component) -> None:
        assert self.test_command, "No test command provided."
        ret = run(self.test_command, cwd=(self.test_dir or self.project_dir))
        if ret.returncode != 0:
            raise ValueError(
                f'{click.style("Error!", fg="red")} ( {processed_component.component_name} ) {str(ret)}'
            )

    def commit_changes(
        self, component: Component, from_version: str, to_version: str, dry_run: bool
    ) -> None:
        git = local["git"]
        assert self.config_file, "No config file found."
        # TODO shouldn't it be self.project_dir param rather?
        with local.cwd(self.config_file.parent):
            ret: TPlumbumRunReturn = git_check(
                git["diff", "--name-only"].run(retcode=None)
            )
            changed_files: List[str] = ret[1].splitlines()
            assert set(component.files).issubset(
                set(changed_files)
            ), f"Not all SRC files are in git changed files.\n{plumbum_msg(ret)}"
            if not dry_run:
                git_check(git["add", self.config_file.name].run(retcode=None))
                for file_name in component.files:
                    git_check(git["add", file_name].run(retcode=None))
                commit_message = (
                    f"{component.component_name} "
                    f"updated from: {from_version} to: {to_version}"
                )
                git_check(
                    git["commit", f"--message={commit_message}"].run(retcode=None)
                )

    def update_files(self, dry_run: bool = False) -> Tuple[int, int]:
        """Update all files for all components. Return number of updated components and number of files updated."""
        file_counter = 0
        components_counter = 0
        for component in self.components:
            if component.newer_version_exists():
                orig_current_tag = component.current_version_tag
                orig_next_tag = component.next_version_tag
                self.update_status(component, self.STATE_UPDATE_STARTED)
                prev_file_counter = file_counter
                file_counter += component.update_files(self.project_dir, dry_run)
                components_counter += 1 if file_counter > prev_file_counter else 0
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

        return components_counter, file_counter

    def get_versions_info(self) -> List[str]:
        new = [
            (
                f"{c.component_name} - current: {c.current_version_tag} "
                f"next: {click.style(c.next_version_tag, fg='green')}"
            )
            for c in self.components
            if c.newer_version_exists()
        ]
        new.sort()
        return new

