import fnmatch
import functools
from pathlib import Path

from _pytest.config import get_config
from _pytest.main import Session
from _pytest.pathlib import fnmatch_ex


class TestNameChecker:
    @classmethod
    def is_test_fn_name(cls, fullname: str) -> bool:
        path, function = cls._split_fullname(fullname)
        return cls.path_match(path) and cls.fn_match(function)

    @classmethod
    def _split_fullname(cls, fullname: str) -> tuple[Path, str]:
        [*path, name] = fullname.split(".")
        if path:
            path[-1] += ".py"
        return Path(*path), name

    @classmethod
    @functools.cache
    def session(cls) -> Session:
        config = get_config()
        config.parse([])
        return Session.from_config(config)

    @classmethod
    @functools.cache
    def file_patterns(cls) -> list[str]:
        return cls.session().config.getini("python_files")

    @classmethod
    @functools.cache
    def fn_patterns(cls) -> list[str]:
        return cls.session().config.getini("python_functions")

    @classmethod
    @functools.cache
    def path_match(cls, path: Path) -> bool:
        return any(fnmatch_ex(pattern, path) for pattern in cls.file_patterns())

    @classmethod
    def fn_match(cls, fn_name: str) -> bool:
        return any(
            fn_name.startswith(pattern) or fnmatch.fnmatch(pattern, fn_name)
            for pattern in cls.fn_patterns()
        )
