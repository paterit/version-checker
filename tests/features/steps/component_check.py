from behave import given, when, then  # type: ignore
from plumbum import local  # type: ignore
from updater import plumbum_msg

RET_CODE_SUCCESS = 0


@given(
    "Component with {component_type}, {repo_name}, {component_name} and {version} as parameters"
)
def step_impl(context, component_type, repo_name, component_name, version):
    context.component_check["component_type"] = component_type
    context.component_check["component_name"] = component_name
    context.component_check["repo_name"] = repo_name
    context.component_check["version"] = version


@when("check version script is run")  # type: ignore[misc]
def step_impl(context):
    python = local["python"]
    ret = python[
        "check_version.py",
        "check",
        f"--type={context.component_check['component_type']}",
        f"--component={context.component_check['component_name']}",
        f"--repo_name={context.component_check['repo_name']}",
        f"--version_tag={context.component_check['version']}",
        "--ignore-default-file",
    ].run(retcode=None)
    context.response = ret
    assert ret[0] == 0, f"Error returned by script:\n{plumbum_msg(ret)}"


@then("there is {response} in response")
def step_impl(context, response):
    assert (
        response in context.response[1]
    ), f"{response} is not found in {context.response[1]}"
