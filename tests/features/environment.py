BEHAVE_DEBUG_ON_ERROR = False


def before_all(context):
    context.component_check = {}
    context.config_file = {}
    context.update_versions = {}
    context.run_tests = {}
    context.git_commit = {}
