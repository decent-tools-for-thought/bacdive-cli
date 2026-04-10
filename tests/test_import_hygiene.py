from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_top_level_import_does_not_require_httpx() -> None:
    project_src = Path(__file__).resolve().parents[1] / "src"
    script = """\
import builtins

real_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "httpx" or name.startswith("httpx."):
        raise ModuleNotFoundError("No module named 'httpx'")
    return real_import(name, *args, **kwargs)

builtins.__import__ = guarded_import

import bacdive_cli
print(bacdive_cli.__name__)
"""

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(project_src)},
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "bacdive_cli"
