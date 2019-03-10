def plumbum_msg(command_exit):
    return "Exit code %d.\nCommand output: %s.\nError msg: %s\n" % (
        command_exit[0],
        command_exit[1],
        command_exit[2],
    )
