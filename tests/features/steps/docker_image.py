from behave import *
from plumbum import local

RET_CODE_SUCCESS = 0

python = local["python"]


@given(u"Docker image name {repo_name}/{component} and {version} as parameters")
def step_impl(context, repo_name, component, version):
    context.docker_image["component"] = component
    context.docker_image["repo_name"] = repo_name
    context.docker_image["version"] = version


@when(u"check version script is run")
def step_impl(context):
    ret = python[
        "check_version.py",
        "--component=" + context.docker_image["component"],
        "--repo_name=" + context.docker_image["repo_name"],
        "--version_tag=" + context.docker_image["version"],
    ].run(retcode=None)
    context.response = str(ret)


@then(u"there is {response} in response")
def step_impl(context, response):
    assert response in context.response, "%r is not found in %r" % (
        response,
        context.response,
    )
