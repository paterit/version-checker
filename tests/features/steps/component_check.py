from behave import *
from plumbum import local

RET_CODE_SUCCESS = 0

python = local["python"]


def plumbum_msg(command_exit):
    return "Exit code %d.\nCommand output: %s.\nError msg: %s\n" % (
        command_exit[0],
        command_exit[1],
        command_exit[2],
    )

@given(u"Component with {component_type}, {repo_name}, {component_name} and {version} as parameters")
# @given(u"Docker image name {repo_name}/{component} and {version} as parameters")
def step_impl(context, component_type, repo_name, component_name, version):
    context.docker_image["component_type"] = component_type
    context.docker_image["component_name"] = component_name
    context.docker_image["repo_name"] = repo_name
    context.docker_image["version"] = version


@when(u"check version script is run")
def step_impl(context):
    ret = python[
        "check_version.py",
        "check",
        "--type=" + context.docker_image["component_type"],
        "--component=" + context.docker_image["component_name"],
        "--repo_name=" + context.docker_image["repo_name"],
        "--version_tag=" + context.docker_image["version"],
    ].run(retcode=None)
    context.response = ret
    assert ret[0] == 0, "Error returned by script:\n" + plumbum_msg(ret)


@then(u"there is {response} in response")
def step_impl(context, response):
    assert response in context.response[1], "%s is not found in %s" % (
        response,
        context.response[1],
    )
