from pathlib import Path
from plumbum import local
from behave import *
import tempfile
import shutil
from updater import plumbum_msg, components
import os


@given(u"New version of component is set in config file")
def step_impl(context):
    # clean context to not interfere between scenarios
    context.update_versions = {}
    context.update_versions["params"] = []

    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(Path.cwd() / "tests/test_files", test_dir)
    test_file = test_dir / "components.yaml"
    assert Path.is_file(test_file), "No components.yaml file in test dir."
    context.update_versions["test_config_file"] = test_file
    context.update_versions["test_dir"] = test_dir


@given(u"config file is in different location then project-dir param")
def step_impl(context):
    ctx = context.update_versions
    ctx["project_dir"] = ctx["test_dir"]
    os.makedirs(ctx["project_dir"] / "config")
    shutil.move(
        ctx["test_dir"] / "components.yaml",
        ctx["project_dir"] / "config" / "components.yaml",
    )
    ctx["test_config_file"] = ctx["project_dir"] / "config" / "components.yaml"
    ctx["params"].append("--project-dir=" + str(ctx["project_dir"]))


@given(u"script is run with --verbose param")
def step_impl(context):
    context.update_versions["params"].append("--verbose")


@when(u"script is run in update mode")
def step_impl(context):
    ctx = context.update_versions
    python = local["python"]
    params = [
        "check_version.py",
        "--file=" + str(ctx["test_config_file"]),
        "--print",
        "update",
    ]
    params.extend(ctx["params"])

    ret = python[params].run(retcode=None)
    context.response = ret
    assert ret[0] == 0, "Error returned by script:\n" + plumbum_msg(ret)


@then(u"replace version in files defined in config files")
def step_impl(context):
    origin_content1 = (
        Path.cwd().joinpath("tests/test_files/glances/Dockerfile-glances").read_text()
    )

    changed_content1 = (
        context.update_versions["test_dir"]
        .joinpath("glances/Dockerfile-glances")
        .read_text()
    )
    assert origin_content1 != changed_content1, (
        "Contents should be different:\n %r \n %r" % (origin_content1, changed_content1)
    )

    origin_content2 = (
        Path.cwd().joinpath("tests/test_files/logspout/Dockerfile-logspout").read_text()
    )

    changed_content2 = (
        context.update_versions["test_dir"]
        .joinpath("logspout/Dockerfile-logspout")
        .read_text()
    )
    assert origin_content2 != changed_content2, (
        "Contents should be different:\n %r \n %r" % (origin_content2, changed_content2)
    )


@then(u"there should status info in the script output")
def step_impl(context):
    assert components.Config.STATE_UPDATE_STARTED in str(
        context.response[1]
    ), plumbum_msg(context.response)
