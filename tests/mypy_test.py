from glob import glob
import operator
from pathlib import Path
import sys

import mypy
import mypy.api
import pytest
from pytest_snapshot.plugin import Snapshot

TEST_FILES = list(filter(Path.exists, map(Path, glob("test_samples/**/*.py", recursive=True))))


@pytest.mark.parametrize("filepath", TEST_FILES, ids=map(operator.attrgetter("stem"), TEST_FILES))
def test_check_files(filepath: Path, snapshot: Snapshot) -> None:
    sys.modules.pop("plugin", None)  # required for plugin to work correctly
    stdout, stderr, _exit_code = mypy.api.run([str(filepath), "--cache-dir", "/dev/null"])
    assert stderr == "", stderr
    stdout_snapshot_file = f"{filepath.stem}.out"
    snapshot.assert_match(stdout, stdout_snapshot_file)
