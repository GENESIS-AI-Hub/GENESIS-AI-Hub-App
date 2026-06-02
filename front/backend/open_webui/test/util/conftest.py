"""conftest.py for open_webui/test/util/ — ensures utils.privacy can be
imported even when the router test conftest (in test/apps/webui/routers/)
has overwritten open_webui.utils with a MagicMock.

This conftest is loaded before the router conftest for tests in this directory,
so it can pre-register the real module in sys.modules first.
"""

import os
import sys
import types
import importlib.util as _ilu

_BACKEND = os.path.abspath(
    # util/ -> test/ -> open_webui/ -> backend/
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Pre-register open_webui.utils.privacy so it's available regardless of
# whether open_webui.utils later becomes a MagicMock (from the router conftest).
if "open_webui.utils.privacy" not in sys.modules:
    _privacy_path = os.path.join(_BACKEND, "open_webui", "utils", "privacy.py")
    if os.path.exists(_privacy_path):
        _spec = _ilu.spec_from_file_location("open_webui.utils.privacy", _privacy_path)
        _mod = _ilu.module_from_spec(_spec)
        sys.modules["open_webui.utils.privacy"] = _mod
        _spec.loader.exec_module(_mod)
