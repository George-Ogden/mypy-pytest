import fnmatch
import functools
from pathlib import Path

from _pytest.config import get_config
from _pytest.main import Session
from _pytest.pathlib import fnmatch_ex


class TestNameChecker:
    @classmethod
    def is_test_name(cls, fullname: str) -> bool:
        path, function = cls._split_fullname(fullname)
        return cls.is_test_path(path) and cls.is_test_fn_name(function)

    @classmethod
    def _split_fullname(cls, fullname: str) -> tuple[Path, str]:
        [*path, name] = fullname.split(".")
        if path:
            path[-1] += ".py"
        return Path(*path), name

    @classmethod
    @functools.cache
    def _session(cls) -> Session:
        config = get_config()
        config.parse(["-s"])
        return Session.from_config(config)

    @classmethod
    @functools.cache
    def _file_patterns(cls) -> list[str]:
        return cls._session().config.getini("python_files")

    @classmethod
    @functools.cache
    def _fn_patterns(cls) -> list[str]:
        return cls._session().config.getini("python_functions")

    @classmethod
    @functools.cache
    def is_test_path(cls, path: Path) -> bool:
        return any(fnmatch_ex(pattern, path) for pattern in cls._file_patterns())

    @classmethod
    def is_test_fn_name(cls, fn_name: str) -> bool:
        return any(
            fn_name.startswith(pattern) or fnmatch.fnmatch(pattern, fn_name)
            for pattern in cls._fn_patterns()
        )
