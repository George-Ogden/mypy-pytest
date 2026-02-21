from glob import glob
import operator
import os
from pathlib import Path
import sys

from inline_snapshot import external_file
import mypy.api
import pytest

TEST_FILES = list(filter(Path.exists, map(Path, glob("test_samples/**/*.py", recursive=True))))


@pytest.mark.parametrize("filepath", TEST_FILES, ids=map(operator.attrgetter("stem"), TEST_FILES))
def test_check_files(filepath: Path) -> None:
    sys.modules.pop("plugin", None)  # required for plugin to work correctly
    stdout, stderr, _exit_code = mypy.api.run(
        [str(filepath), "--cache-dir", os.devnull, "--show-traceback"]
    )
    assert stderr == "", stderr
    stdout_snapshot_file = "snapshots" / filepath.with_suffix(".txt")
    assert stdout == external_file(stdout_snapshot_file)
