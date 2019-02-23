from behave import *
from pathlib import Path
from plumbum import local
import yaml

python = local["python"]


@given(u"YAML file with components configuration")
def step_impl(context):
    assert (
        Path.is_file(Path.cwd().joinpath("components.yaml")) is True
    ), "No component.yaml file in current dir."
    context.config_file["components"] = yaml.load(open("components.yaml"))


@when(u"program is started without params")
def step_impl(context):
    ret = python["check_version.py"].run(retcode=None)
    context.response = ret[1]


@then(u"checking for new version is done for all components from file")
def step_impl(context):
    componetns_count = len(context.config_file["components"])
    assert "%d components to check" % componetns_count in context.response, (
        "Different number of components to check. Expected was %r and the answer is %r"
        % (componetns_count, context.response)
    )
