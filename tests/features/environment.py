BEHAVE_DEBUG_ON_ERROR = False


def before_all(context):
    context.component_check = {}
    context.config_file = {}
    context.update_versions = {}
    context.run_tests = {}
    context.git_commit = {}


def after_step(context, step):
    if BEHAVE_DEBUG_ON_ERROR and step.status == "failed":
        # -- ENTER DEBUGGER: Zoom in on failure location.
        # NOTE: Use IPython debugger, same for pdb (basic python debugger).
        import ipdb

        ipdb.post_mortem(step.exc_traceback)
