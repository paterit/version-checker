from pathlib import Path
from plumbum import local
from behave import *
import tempfile
import shutil
from updater import plumbum_msg as pm, git_check


@given("New version of component is set in defined files in git repo")
def step_impl(context):

    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(Path.cwd() / "tests/test_files", test_dir)
    test_file = test_dir / "components.yaml"

    context.git_commit["test_config_file"] = test_file
    context.git_commit["test_dir"] = test_dir


@when("script is run in update mode with git-commit parameter")
def step_impl(context):
    python = local["python"]
    git = local["git"]
    with local.cwd(context.git_commit["test_dir"]):
        git_check(git["init"].run(retcode=None))
        git_check(git["add", "."].run(retcode=None))
        git_check(git["config", "user.email", "'paterit@paterit.eu'"].run(retcode=None))
        git_check(git["config", "user.name", "'paterit'"].run(retcode=None))
        git_check(git["commit", "--message=Initial commit."].run(retcode=None))

    ret = python[
        "check_version.py",
        f"--file={str(context.git_commit['test_config_file'])}",
        "update",
        "--git-commit",
    ].run(retcode=None)
    context.response = ret
    assert ret[0] == 0, f"Error returned by script.\n{pm(ret)}"


# given and when are defined in rut_tests.py
@then("there is same number of git commits than components defined")
def step_impl(context):
    git = local["git"]
    with local.cwd(context.git_commit["test_dir"]):
        ret = git["log", "--pretty=oneline", "--abbrev-commit"].run(retcode=None)
        git_check(ret)
    assert "logspout" in ret[1], f"'logspout' is not found in output.\n{pm(ret)}"
    assert "glances" in ret[1], f"'logspout' is not found in output.\n{pm(ret)}"
    assert "Django" in ret[1], f"'logspout' is not found in output.\n{pm(ret)}"
    assert "requests" in ret[1], f"'logspout' is not found in output.\n{pm(ret)}"
