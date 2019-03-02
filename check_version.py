from pathlib import Path
import click
from components import ComponentsConfig, Component


@click.group()
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
@click.option(
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="If set no changes to config files are written.",
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

    ctx.obj["config"] = ComponentsConfig(components_yaml_file=config_file)
    ctx.obj["config_file"] = config_file
    ctx.obj["destination_file"] = destination_file
    ctx.obj["dry_run"] = dry_run
    ctx.obj["print_yaml"] = print_yaml


@cli.command()
@click.option("--component", help="Component name to version veryfication.")
@click.option("--repo_name", help="Repository name if component is docker image.")
@click.option(
    "--version_tag",
    help="Version tag eg. v2.3.0 against which new version check will be run.",
)
@click.pass_context
def check(ctx, component, repo_name, version_tag):
    config = ctx.obj["config"]
    # config_file = ctx.obj["config_file"]
    destination_file = ctx.obj["destination_file"]
    dry_run = ctx.obj["dry_run"]
    print_yaml = ctx.obj["print_yaml"]

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
    config.save_changes(destination_file, dry_run, print_yaml)
    print("\n".join(ret_mess))


@cli.command()
@click.option(
    "--test-command",
    "test_command",
    help="Command that should be run after updating each component.",
)
@click.pass_context
def update(ctx, test_command):
    config = ctx.obj["config"]
    dry_run = ctx.obj["dry_run"]
    destination_file = ctx.obj["destination_file"]
    print_yaml = ctx.obj["print_yaml"]

    print(test_command)

    config.read_from_yaml()
    config.check()
    config.save_changes(destination_file, dry_run, print_yaml)
    config.update_files(config.config_file.parent, dry_run)


if __name__ == "__main__":
    cli(obj={})
