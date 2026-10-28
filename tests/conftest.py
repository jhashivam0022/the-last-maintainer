import shutil
import subprocess
from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parent.parent / "examples" / "sample-spring-app"


def _git(cwd, *args):
    subprocess.run(
        ["git", "-c", "user.name=Dev", "-c", "user.email=dev@example.com", *args],
        cwd=cwd, check=True, capture_output=True,
    )


@pytest.fixture()
def sample_repo(tmp_path):
    """A copy of the sample app with a small, real Git history."""
    dest = tmp_path / "legacy-shop"
    shutil.copytree(SAMPLE, dest)
    _git(dest, "init", "-q")
    _git(dest, "add", ".")
    _git(dest, "commit", "-q", "-m", "Initial import of legacy shop")
    controller = dest / "src/main/java/com/example/legacy/web/AuthController.java"
    controller.write_text(controller.read_text() + "\n// touched\n")
    _git(dest, "commit", "-q", "-am", "Add register endpoint")
    return dest
