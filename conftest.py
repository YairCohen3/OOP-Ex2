"""pytest setup: run the tests against a fresh, empty database in a temporary folder.

This file is loaded by pytest before test_main.py imports the app, so the real
smartclass.db, uploads and attendance reports are never touched by the tests.
"""
import os
import tempfile
from pathlib import Path

_test_data_dir = Path(tempfile.mkdtemp(prefix="smartclass-test-"))
# An existing (empty) file stops database.py from copying the bundled smartclass.db.
(_test_data_dir / "smartclass.db").touch()

os.environ["SMARTCLASS_DATA_DIR"] = str(_test_data_dir)
os.environ["SMARTCLASS_QR_SECRET"] = "smartclass-test-secret"
# AI features must report "not configured" in tests – they must never invent results.
os.environ.pop("GEMINI_API_KEY", None)
os.environ.pop("GOOGLE_API_KEY", None)
