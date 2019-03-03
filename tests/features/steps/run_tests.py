from pathlib import Path
from plumbum import local
from behave import *
import tempfile
import shutil

python = local["python"]


# TODO move to some tools modules from all files
def plumbum_msg(command_exit):
    return "Exit code %d.\nCommand output: %s.\nError msg: %s\n" % (
        command_exit[0],
        command_exit[1],
        command_exit[2],
    )


@given(u"New version of component is set in defined files")
def step_impl(context):
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(Path.cwd() / "tests/test_files", test_dir)
    test_file = test_dir / "components.yaml"
    assert Path.is_file(test_file) is True, "No components.yaml file in test dir."
    context.run_tests["test_config_file"] = test_file
    context.run_tests["test_dir"] = test_dir


@when(u"script is run in update mode with test parameter")
def step_impl(context):
    ret = python[
        "check_version.py",
        "--file=" + str(context.run_tests["test_config_file"]),
        "--print",
        "update",
        "--test-command=make test",
    ].run(retcode=None)
    context.response = ret
    assert ret[0] == 0, "Error returned by script: %r" % str(ret)


@then(u"run test command and stop in case of failure")
def step_impl(context):
    assert "Test OK" in context.response[1], (
        "'Test OK' is not found in output.\n" + plumbum_msg(context.response)
    )
    assert (
        context.response[1].count("Test OK") == 2
    ), "To few occurenc of 'Test OK'\n" + plumbum_msg(context.response)
