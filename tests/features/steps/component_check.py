from behave import *
from plumbum import local
from updater import plumbum_msg

RET_CODE_SUCCESS = 0


@given(
    u"Component with {component_type}, {repo_name}, {component_name} and {version} as parameters"
)
# @given(u"Docker image name {repo_name}/{component} and {version} as parameters")
def step_impl(context, component_type, repo_name, component_name, version):
    context.component_check["component_type"] = component_type
    context.component_check["component_name"] = component_name
    context.component_check["repo_name"] = repo_name
    context.component_check["version"] = version


@when(u"check version script is run")
def step_impl(context):
    python = local["python"]
    ret = python[
        "check_version.py",
        "check",
        "--type=" + context.component_check["component_type"],
        "--component=" + context.component_check["component_name"],
        "--repo_name=" + context.component_check["repo_name"],
        "--version_tag=" + context.component_check["version"],
        "--ignore-default-file",
    ].run(retcode=None)
    context.response = ret
    assert ret[0] == 0, "Error returned by script:\n" + plumbum_msg(ret)


@then(u"there is {response} in response")
def step_impl(context, response):
    assert response in context.response[1], "%s is not found in %s" % (
        response,
        context.response[1],
    )
