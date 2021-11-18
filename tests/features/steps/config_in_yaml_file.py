from behave import *
from pathlib import Path
from plumbum import local
import shutil
import yaml
from updater import plumbum_msg
import tempfile


@given(u"YAML file with components configuration")
def step_impl(context):
    test_file = Path.cwd() / "tests/test_files/components.yaml"
    assert Path.is_file(test_file) is True, "No components.yaml file in test dir."

    dest_file = Path(tempfile.mkdtemp()) / "components.yaml"
    assert Path.is_file(dest_file) is False, "File components.yaml already exists."
    shutil.copyfile(test_file, dest_file)
    context.config_file["components_file"] = dest_file


@when(u"program is started without params")
def step_impl(context):
    python = local["python"]
    ret = python[
        "check_version.py",
        "--destination-file=" + str(context.config_file["components_file"]),
        "check",
    ].run(retcode=None)
    context.response = str(ret)
    assert ret[0] == 0, "Error returned by script:\n" + plumbum_msg(ret)


@then(u"checking for new version is done for all components from file")
def step_impl(context):
    components_count = len(yaml.load(open(context.config_file["components_file"])))
    context.config_file["components_file"].unlink()
    assert "%d components to check" % components_count in context.response, (
        "Different number of components to check. Expected was %d and the answer is %s"
        % (components_count, context.response)
    )
