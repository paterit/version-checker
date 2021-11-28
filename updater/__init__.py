from typing import Tuple


TPlumbumRunReturn = Tuple[int, str, str]


def plumbum_msg(command_exit: TPlumbumRunReturn) -> str:
    return (
        f"Exit code {command_exit[0]}.\n"
        f"Command output:\n{command_exit[1]}."
        f"\nError msg:\n{command_exit[2]}\n"
    )


def git_check(ret: TPlumbumRunReturn) -> TPlumbumRunReturn:
    assert ret[0] == 0, f"Error returned by git.\n{plumbum_msg(ret)}"
    return ret
