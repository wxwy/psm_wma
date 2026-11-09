"""External recorder entry: delegate to native CLI, preserve all identity checks.

Native launch_environment prepends Child to PYTHONPATH. Re-prepend this probe's
directory so its explicit startup helper is not shadowed by the server's existing
ignored helper; sitecustomize chains that helper after verifying its hash.
"""
import os
from pathlib import Path


def prepend_probe(environment):
    environment = dict(environment)
    hooks = str(Path(__file__).resolve().parent / 'hooks')
    paths = [p for p in environment.get('PYTHONPATH', '').split(os.pathsep) if p != hooks]
    environment['PYTHONPATH'] = os.pathsep.join([hooks, *paths])
    return environment


def main(argv=None):
    from robocasa_eval_v2 import identity
    from robocasa_eval_v2.cli import main as native_main

    original = identity.launch_environment
    identity.launch_environment = lambda cache: prepend_probe(original(cache))
    try:
        return native_main(argv)
    finally:
        identity.launch_environment = original


if __name__ == '__main__':
    raise SystemExit(main())
