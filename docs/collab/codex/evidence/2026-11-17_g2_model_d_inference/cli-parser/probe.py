"""CPU parser-only check: disable startup init and request help, never construct service."""
from unittest.mock import patch

import tyro

with patch("cosmos_framework.inference.common.init._init_script", lambda **kwargs: None):
    from cosmos_framework.scripts.action_policy_server_robocasa import ActionServerArgs

tyro.cli(ActionServerArgs, args=["--help"])
