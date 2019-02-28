from behave import *
from pathlib import Path
from plumbum import local
import shutil
import yaml

python = local["python"]


@given(u"YAML file with components configuration")
def step_impl(context):
    test_file = Path.cwd() / "tests/test_files/components.yaml"
    assert Path.is_file(test_file) is True, "No components.yaml file in test dir."

    dest_file = Path.cwd() / "components.yaml"
    assert Path.is_file(dest_file) is False, "File components.yaml already exists."
    shutil.copyfile(test_file, dest_file)
    context.config_file["components_file"] = dest_file


@when(u"program is started without params")
def step_impl(context):
    ret = python["check_version.py", "check"].run(retcode=None)
    context.response = str(ret)


@then(u"checking for new version is done for all components from file")
def step_impl(context):
    components_count = len(yaml.load(open(context.config_file["components_file"])))
    context.config_file["components_file"].unlink()
    assert "%d components to check" % components_count in context.response, (
        "Different number of components to check. Expected was %r and the answer is %r"
        % (components_count, context.response)
    )
