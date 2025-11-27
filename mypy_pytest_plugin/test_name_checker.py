from collections.abc import MutableSequence
import fnmatch
import functools
from pathlib import Path

from _pytest.pathlib import fnmatch_ex

from .pytest_config_manager import PytestConfigManager


class TestNameChecker:
    @classmethod
    def is_test_name(cls, fullname: str) -> bool:
        path, function = cls._split_fullname(fullname)
        return cls.is_test_path(path) and cls.is_test_fn_name(function)

    @classmethod
    def _split_fullname(cls, fullname: str) -> tuple[Path, str]:
        [*path, name] = fullname.split(".")
        return cls._path_from_sections(path), name

    @classmethod
    def _path_from_sections(cls, sections: MutableSequence[str]) -> Path:
        if sections:
            sections[-1] += ".py"
        return Path(*sections)

    @classmethod
    @functools.cache
    def is_test_file_name(cls, name: str) -> bool:
        path = cls._path_from_sections(name.split("."))
        return cls.is_test_path(path)

    @classmethod
    @functools.cache
    def is_test_path(cls, path: Path) -> bool:
        return any(fnmatch_ex(pattern, path) for pattern in PytestConfigManager.file_patterns())

    @classmethod
    def is_test_fn_name(cls, fn_name: str) -> bool:
        return any(
            fn_name.startswith(pattern) or fnmatch.fnmatch(pattern, fn_name)
            for pattern in PytestConfigManager.fn_patterns()
        )
