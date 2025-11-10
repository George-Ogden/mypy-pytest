from glob import glob
import operator
from pathlib import Path
import sys

import mypy
import mypy.api
import pytest
from pytest_snapshot.plugin import Snapshot

TEST_FILES = list(map(Path, glob("test_samples/*.py")))


@pytest.mark.parametrize("filepath", TEST_FILES, ids=map(operator.attrgetter("stem"), TEST_FILES))
def test_check_files(
    filepath: Path,
    snapshot: Snapshot,  # type: ignore
) -> None:
    sys.modules.pop("plugin", None)  # required for plugin to work correctly
    stdout, stderr, _exit_code = mypy.api.run([str(filepath)])
    print(stderr)
    stdout_snapshot_file = f"{filepath.stem}.out"
    snapshot.assert_match(stdout, stdout_snapshot_file)
