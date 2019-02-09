from behave import *
from plumbum import local

RET_CODE_SUCCESS = 0

python = local["python"]


@given(u'Docker image name "{name}" and version "{version}" as parameters')
def step_impl(context, name, version):
    context.docker_image["param"] = name
    context.docker_image["version"] = version


@when(u"check version script is run")
def step_impl(context):
    ret = python[
        "check-version.py",
        context.docker_image["param"],
        context.docker_image["version"],
    ].run(retcode=None)
    assert ret[0] == RET_CODE_SUCCESS, ret
    context.response = ret[1]


@then(u'there is "{text}" in response')
def step_impl(context, text):
    assert text in context.response, "%r is not found in %r" % (text, context.response)
