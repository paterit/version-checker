import pprint
from pathlib import Path

import click
from loguru import logger

from updater import components


@click.group()
@click.option(
    "--file",
    type=click.Path(exists=True, writable=True),
    help="YAML file with components configuration. If not present other options for 'check' command are required.",
)
@click.option(
    "--destination-file",
    "destination_file",
    type=click.Path(),
    help="If this option is given components configuration with new versions will be wrtten here.",
)
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="If set no changes to any files are written.",
)
@click.option(
    "--print",
    "print_yaml",
    is_flag=True,
    help="Config is printed to stdout at the end.",
)
@click.pass_context
def cli(ctx, file, destination_file, dry_run, print_yaml):
    if file is not None:
        config_file = Path(file).absolute()
    elif Path.cwd().absolute().joinpath("components.yaml").is_file():
        config_file = Path.cwd().absolute().joinpath("components.yaml")
    else:
        config_file = None
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj["config"] = components.Config(components_yaml_file=config_file)
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
)
@click.option("--component", help="Component name to version veryfication.")
@click.option("--repo_name", help="Repository name if component is docker image.")
@click.option(
    "--version_tag",
    help="Version tag eg. v2.3.0 against which new version check will be run.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Print detailed info for each component about new version avaialble.",
)
@click.pass_context
def check(ctx, component_type, component, repo_name, version_tag, verbose):
    """Check if new versions of defined components are available."""
    config = ctx.obj["config"]
    # config_file = ctx.obj["config_file"]
    destination_file = ctx.obj["destination_file"]
    dry_run = ctx.obj["dry_run"]
    print_yaml = ctx.obj["print_yaml"]

    config.read_from_yaml()

    if component is not None:
        config.add(
            components.factory.get(
                component_type=component_type,
                repo_name=repo_name,
                component_name=component,
                current_version_tag=version_tag,
            )
        )

    ret_mess = []
    ret_mess.append("%d components to check" % len(config.components))
    ret_mess.append("%d components to update" % config.count_components_to_update())
    config.save_config(destination_file, dry_run, print_yaml)
    if verbose:
        ret_mess.extend(config.get_versions_info())
    click.echo("\n".join(ret_mess))


@cli.command()
@click.option(
    "--test-command",
    "test_command",
    help="Command that should be run after updating each component.",
)
@click.option(
    "--test-dir",
    "test_dir",
    type=click.Path(),
    help="If test-command param is given, this will be the context dir to run it.",
)
@click.option(
    "--git-commit",
    "git_commit",
    is_flag=True,
    help="When set after each components update, git commit is performed in active branch.",
)
@click.pass_context
def update(ctx, test_command, test_dir, git_commit):
    """Update files with version numbers, run test and commit changes."""
    config = ctx.obj["config"]
    dry_run = ctx.obj["dry_run"]
    destination_file = ctx.obj["destination_file"]
    print_yaml = ctx.obj["print_yaml"]

    config.test_command = test_command.split() if test_command is not None else None
    config.test_dir = test_dir
    config.git_commit = git_commit
    config.read_from_yaml()
    config.check()
    config.save_config(destination_file, dry_run, print_yaml)
    try:
        config.update_files(config.config_file.parent, dry_run)
    except AssertionError:
        logger.error(
            click.style("Something went wrong!!!", "red")
            + "\n"
            + "Config status:\n"
            + pprint.pformat(config.status, indent=4)
        )
    except Exception as exception:
        # Output unexpected Exceptions.
        logger.error(str(exception))


if __name__ == "__main__":
    cli(obj={})
