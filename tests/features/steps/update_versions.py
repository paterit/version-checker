from pathlib import Path
from plumbum import local
from behave import *
import tempfile
import shutil
from updater import plumbum_msg

python = local["python"]


@given(u"New version of component is set in config file")
def step_impl(context):
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(Path.cwd() / "tests/test_files", test_dir)
    test_file = test_dir / "components.yaml"
    assert Path.is_file(test_file) is True, "No components.yaml file in test dir."
    context.update_versions["test_config_file"] = test_file
    context.update_versions["test_dir"] = test_dir


@when(u"script is run in update mode")
def step_impl(context):
    ret = python[
        "check_version.py",
        "--file=" + str(context.update_versions["test_config_file"]),
        "--print",
        "update",
    ].run(retcode=None)
    context.response = str(ret)
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
