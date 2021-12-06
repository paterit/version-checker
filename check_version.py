from pathlib import Path
import sys
from typing import List, Optional

import click
from click.core import Context
from loguru import logger
import pkg_resources

from updater import components, config_yaml


@click.group()
@click.version_option(
    version=Path(
        pkg_resources.resource_filename(__name__, "updater/VERSION")
    ).read_text()
)  # type: ignore
@click.option(
    "--file",
    type=click.Path(exists=True, writable=True),
    help="YAML file with components configuration. If not present other options for 'check' command are required.",
)  # type: ignore
@click.option(
    "--destination-file",
    "destination_file",
    type=click.Path(),
    help="If this option is given components configuration with new versions will be written here.",
)  # type: ignore
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="If set no changes to any files are written.",
)  # type: ignore
@click.option(
    "--print",
    "print_yaml",
    is_flag=True,
    help="Config is printed to stdout at the end.",
)  # type: ignore
@click.pass_context
def cli(
    ctx: Context,
    file: Optional[Path],
    destination_file: Optional[Path],
    dry_run: bool,
    print_yaml: bool,
) -> None:
    config_file: Optional[Path] = None
    if file is not None:
        config_file = Path(file).absolute()
    elif Path.cwd().absolute().joinpath("components.yaml").is_file():
        config_file = Path.cwd().absolute().joinpath("components.yaml")

    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj["config"] = config_yaml.Config(components_yaml_file=config_file)
    ctx.obj["config_file"] = config_file
    ctx.obj["destination_file"] = destination_file
    ctx.obj["dry_run"] = dry_run
    ctx.obj["print_yaml"] = print_yaml


@cli.command()
@click.option(
    "--type",
    "component_type",
    help="Component type: docker-image or pypi package.",
    type=click.Choice(["docker-image", "pypi"]),
)  # type: ignore
@click.option(
    "--component", help="A component name for which the version should be verified."
)  # type: ignore
@click.option(
    "--repo_name", help="A repository name if component is a docker image."
)  # type: ignore
@click.option(
    "--version_tag",
    help="Version tag eg. v2.3.0 against which new version check will be run.",
)  # type: ignore
@click.option(
    "--verbose",
    is_flag=True,
    help="Print detailed info for each component about new version avaialble.",
)  # type: ignore
@click.option(
    "--clear-cache",
    "clear_cache",
    is_flag=True,
    help="Clear all the cached responses about versions in rpositories.",
)  # type: ignore
@click.option(
    "--ignore-default-file",
    "ignore_default_file",
    is_flag=True,
    help="Ignore components.yaml file in local directory if exists.",
)  # type: ignore
@click.pass_context
def check(
    ctx: Context,
    component_type: Optional[str],
    component: Optional[str],
    repo_name: Optional[str],
    version_tag: Optional[str],
    verbose: bool,
    clear_cache: bool,
    ignore_default_file: bool,
) -> None:
    """Check if new versions of ddefined components are available.
    """
    config: config_yaml.Config = ctx.obj["config"]
    destination_file = ctx.obj["destination_file"]
    dry_run = ctx.obj["dry_run"]
    print_yaml = ctx.obj["print_yaml"]

    if clear_cache:
        components.clear_versions_cache()
        sys.exit(0)

    if ignore_default_file:
        config.config_file = None

    config.read_from_yaml()

    if component is not None:
        config.add(
            components.factory.get(
                component_type=str(component_type),
                repo_name=repo_name,
                component_name=component,
                current_version_tag=version_tag,
            )
        )

    ret_mess: List[str] = []
    ret_mess.append(f"{len(config.components)} components to check")
    ret_mess.append(f"{config.count_components_to_update()} components to update")
    config.save_config(destination_file, dry_run, print_yaml)
    if verbose:
        ret_mess.extend(config.get_versions_info())
    click.echo("\n".join(ret_mess))


@cli.command()
@click.option(
    "--test-command",
    "test_command",
    help="Command that should be run after updating each component.",
)  # type: ignore
@click.option(
    "--test-dir",
    "test_dir",
    type=click.Path(),
    help="If test-command param is given, this will be the context dir to run it.",
)  # type: ignore
@click.option(
    "--git-commit",
    "git_commit",
    is_flag=True,
    help="When set after each components update, git commit is performed in active branch.",
)  # type: ignore
@click.option(
    "--project-dir",
    "project_dir",
    type=click.Path(),
    help="If given, then it will be treated as a root dir for paths in config file.",
)  # type: ignore
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Print at the end detailed info for each component about update process.",
)  # type: ignore
@click.option(
    "-vv",
    "--very-verbose",
    is_flag=True,
    help="Print at the end detailed info for each component about update process.",
)  # type: ignore
@click.pass_context
def update(
    ctx: Context,
    test_command: Optional[str],
    test_dir: Optional[Path],
    git_commit: bool,
    project_dir: Optional[Path],
    verbose: bool,
    very_verbose: bool,
) -> None:
    """Update files, run test and commit changes."""
    config: config_yaml.Config = ctx.obj["config"]
    dry_run = ctx.obj["dry_run"]
    destination_file = ctx.obj["destination_file"]
    print_yaml = ctx.obj["print_yaml"]

    config.test_command = test_command.split() if test_command is not None else None
    config.test_dir = test_dir
    config.git_commit = git_commit
    config.project_dir = Path(project_dir) if project_dir else config.project_dir
    config.read_from_yaml()
    config.check()
    config.save_config(destination_file, dry_run, print_yaml)

    try:
        components_updated, files_updated = config.update_files(dry_run)
        if verbose or very_verbose:
            click.echo(
                f"{components_updated} components updated, {files_updated} files updated"
            )
        if very_verbose:
            click.echo(config.get_status())
            logger.trace(config.get_status())
    except Exception as e:
        logger.error(
            (
                f'{click.style("Something went wrong!!!", "red")}\n'
                f"Config status:\n"
                f"{config.get_status()}\n"
                f"{e}"
            )
        )
        sys.exit(2)


@cli.command()
@click.option(
    "--source",
    help="Source of the requirement.txt file.",
    type=click.Choice(["requirements", "pipfile", "poetry"]),
    required=True,
)  # type: ignore
@click.option(
    "--requirements-file",
    "requirements_file",
    type=click.Path(exists=True),
    help="Requirements.txt file from which packages and versions will be added to components.yaml file.",
    required=True,
)  # type: ignore
@click.pass_context
def import_req(ctx: Context, source: str, requirements_file: Path) -> None:
    """Imports python packages from requirements.txt file."""
    config = ctx.obj["config"]
    dry_run = ctx.obj["dry_run"]
    destination_file = ctx.obj["destination_file"]
    print_yaml = ctx.obj["print_yaml"]

    config.read_from_yaml()
    config.add_from_requirements(requirements_file, source)
    config.save_config(destination_file, dry_run, print_yaml)


if __name__ == "__main__":
    cli(obj={})  # pragma: no cover
