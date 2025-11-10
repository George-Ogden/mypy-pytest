from collections.abc import Callable
import fnmatch
import functools
from pathlib import Path

from _pytest.config import get_config
from _pytest.main import Session
from _pytest.pathlib import fnmatch_ex
from mypy.checker import TypeChecker
from mypy.nodes import Decorator
from mypy.plugin import MethodContext, Plugin
from mypy.types import Type

from .test_info import TestInfo


class PytestPlugin(Plugin):
    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        if fullname.startswith("_pytest.mark.structures"):
            return self.check
        return None

    @classmethod
    def check(cls, ctx: MethodContext) -> Type:
        if (
            isinstance(ctx.context, Decorator)
            and cls.is_test_fn_name(ctx.context.fullname)
            and isinstance(ctx.api, TypeChecker)
        ):
            test_info = TestInfo.from_fn_def(ctx.context, checker=ctx.api)
            if test_info is not None:
                test_info.check()
        return ctx.default_return_type

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
