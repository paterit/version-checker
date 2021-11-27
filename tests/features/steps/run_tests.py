from pathlib import Path
from plumbum import local
from behave import *
import tempfile
import shutil
from updater import plumbum_msg


@given("New version of component is set in defined files")
def step_impl(context):
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(Path.cwd() / "tests/test_files", test_dir)
    test_file = test_dir / "components.yaml"
    assert Path.is_file(test_file) is True, "No components.yaml file in test dir."
    context.run_tests["test_config_file"] = test_file
    context.run_tests["test_dir"] = test_dir


@when("script is run in update mode with test parameter")
def step_impl(context):
    python = local["python"]
    ret = python[
        "check_version.py",
        f"--file={str(context.run_tests['test_config_file'])}",
        "--print",
        "update",
        "--test-command=make test",
    ].run(retcode=None)
    context.response = ret
    assert ret[0] == 0, f"Error returned by script: {str(ret)!r}"


@then("run test command and stop in case of failure")
def step_impl(context):
    assert (
        "Test OK" in context.response[1]
    ), f"'Test OK' is not found in output.\n{plumbum_msg(context.response)}"
    assert (
        context.response[1].count("Test OK") == 5
    ), f"To few occurenc of 'Test OK'\n{plumbum_msg(context.response)}"
