#!/usr/bin/env python3
"""Set Linux parent-death protection then exec the reviewed command, same PID."""

import ctypes
import os
import signal
import sys

if __name__ == "__main__":
    parent = int(sys.argv[1])
    command = sys.argv[2:]
    if not command:
        raise ValueError("missing child command")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(1, int(signal.SIGKILL), 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_PDEATHSIG")
    if os.getppid() != parent:
        os.kill(os.getpid(), signal.SIGKILL)
    os.execvpe(command[0], command, os.environ)
