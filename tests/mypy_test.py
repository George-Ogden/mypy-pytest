from glob import glob
import operator
from pathlib import Path
import shutil
import sys

import mypy
import mypy.api
import pytest
from pytest_snapshot.plugin import Snapshot

TEST_FILES = list(filter(Path.exists, map(Path, glob("test_samples/**/*.py", recursive=True))))


@pytest.fixture
def remove_mypy_cache() -> None:
    shutil.rmtree(".mypy_cache", ignore_errors=True)


@pytest.mark.parametrize("filepath", TEST_FILES, ids=map(operator.attrgetter("stem"), TEST_FILES))
def test_check_files(
    filepath: Path,
    snapshot: Snapshot,  # type: ignore
    remove_mypy_cache: None,
) -> None:
    sys.modules.pop("plugin", None)  # required for plugin to work correctly
    stdout, stderr, _exit_code = mypy.api.run([str(filepath)])
    assert stderr == "", stderr
    stdout_snapshot_file = f"{filepath.stem}.out"
    snapshot.assert_match(stdout, stdout_snapshot_file)
