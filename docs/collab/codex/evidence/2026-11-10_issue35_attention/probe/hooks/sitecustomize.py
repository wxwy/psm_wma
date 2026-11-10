"""Issue35 opt-in recording only in an owned Policy Server, never production edits."""

import os
import sys
import builtins
import functools
import json
import hashlib
import runpy
from pathlib import Path

if os.environ.get("ISSUE35_ORIGINAL_STARTUP"):
    original_startup = Path(os.environ["ISSUE35_ORIGINAL_STARTUP"])
    if (
        hashlib.sha256(original_startup.read_bytes()).hexdigest()
        != os.environ["ISSUE35_ORIGINAL_STARTUP_SHA256"]
    ):
        raise SystemExit("Issue35 refuses changed original startup helper")
    runpy.run_path(str(original_startup), run_name="_issue35_original_startup")

if os.environ.get(
    "ISSUE35_CAPTURE_DIR"
) and "cosmos_framework.scripts.action_policy_server_robocasa" in getattr(
    sys, "orig_argv", ()
):
    directory = Path(os.environ["ISSUE35_CAPTURE_DIR"])
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    (directory / "hook_loaded.json").write_text(
        json.dumps(dict(pid=os.getpid(), probe="constructor_wrapper")) + "\n"
    )
    original_build = builtins.__build_class__

    def build(body, name, *bases, **kwargs):
        cls = original_build(body, name, *bases, **kwargs)
        if name == "ActionModelService" and body.__code__.co_filename.endswith(
            "/action_policy_server_robocasa.py"
        ):
            builtins.__build_class__ = original_build
            original_init = cls.__init__

            @functools.wraps(original_init)
            def initialized(service, *args, **kw):
                original_init(service, *args, **kw)
                from freeze_capture import install

                install(service)

            cls.__init__ = initialized
            (directory / "class_instrumented.json").write_text(
                json.dumps(dict(pid=os.getpid())) + "\n"
            )
        return cls

    builtins.__build_class__ = build
