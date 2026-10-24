"""Controlled budget RED, not a reproduction of DS's unavailable raw run."""
import subprocess
import sys


def test_old_fixed_wait_rejects_a_genuinely_progressing_producer():
    process = subprocess.Popen([sys.executable, '-u', '-c',
        "import time; [(print(i,flush=True),time.sleep(.05)) for i in range(12)]"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        # This deliberately fails under the old wait-only strategy.
        assert process.wait(timeout=.1) == 0
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate()
