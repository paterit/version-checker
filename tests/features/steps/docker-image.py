from behave import *


# TODO: get those data from code, from def file
@given(u"Current version and name of the docker image")
def step_impl(context):
    context.docker_image["name"] = "buildbot-master"
    context.docker_image["current_version"] = "v1.1.0"


@when(u"API to docker repository is called")
def step_impl(context):
    raise NotImplementedError(u"STEP: When API to docker repository is called")


@then(u"newest version is returned")
def step_impl(context):
    raise NotImplementedError(u"STEP: Then new version is returned")


@given(u"filter for version as a regular experssion")
def step_impl(context):
    raise NotImplementedError(u"STEP: Given filter for version as a regular experssion")


@then(u"new version is returned that fit to filter")
def step_impl(context):
    raise NotImplementedError(u"STEP: Then new version is returned that fit to filter")


@given(u"a list of excluded versions si given")
def step_impl(context):
    raise NotImplementedError(u"STEP: Given a list of excluded versions si given")


@then(u"new version is returned that not exits in excluded list")
def step_impl(context):
    raise NotImplementedError(
        u"STEP: Then new version is returned that not exits in excluded list"
    )
