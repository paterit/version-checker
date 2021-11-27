from behave import *
from pathlib import Path
from plumbum import local
import shutil
import yaml
from updater import plumbum_msg
import tempfile


@given("YAML file with components configuration")
def step_impl(context):
    test_file = Path.cwd() / "tests/test_files/components.yaml"
    assert Path.is_file(test_file) is True, "No components.yaml file in test dir."

    dest_file = Path(tempfile.mkdtemp()) / "components.yaml"
    assert Path.is_file(dest_file) is False, "File components.yaml already exists."
    shutil.copyfile(test_file, dest_file)
    context.config_file["components_file"] = dest_file


@when("program is started without params")
def step_impl(context):
    python = local["python"]
    ret = python[
        "check_version.py",
        f"--destination-file={str(context.config_file['components_file'])}",
        "check",
    ].run(retcode=None)
    context.response = str(ret)
    assert ret[0] == 0, f"Error returned by script:\n{plumbum_msg(ret)}"


@then("checking for new version is done for all components from file")
def step_impl(context):
    components_count = len(yaml.load(open(context.config_file["components_file"])))
    context.config_file["components_file"].unlink()
    assert f"{int(components_count)} components to check" in context.response, (
        f"Different number of components to check. "
        f"Expected was {components_count} and the answer is {context.response}"
    )
