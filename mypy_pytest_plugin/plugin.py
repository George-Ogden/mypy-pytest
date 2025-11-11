from collections.abc import Callable
import fnmatch
import functools
from pathlib import Path
from typing import Final, cast

from _pytest.config import get_config
from _pytest.main import Session
from _pytest.pathlib import fnmatch_ex
from mypy.checker import TypeChecker
from mypy.nodes import Decorator, MypyFile, TypeInfo
from mypy.plugin import MethodContext, Plugin
from mypy.types import CallableType, Instance, Type

from .test_info import TestInfo


class PytestPlugin(Plugin):
    TYPES_MODULE: Final[str] = f"{__package__}.types"

    def get_additional_deps(self, file: MypyFile) -> list[tuple[int, str, int]]:
        return [(10, "typing", -1), (10, self.TYPES_MODULE, -1)]

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
            cls._update_return_type(ctx.default_return_type, ctx.api)
        return ctx.default_return_type

    @classmethod
    def _update_return_type(cls, return_type: Type, checker: TypeChecker) -> None:
        if (
            isinstance(return_type, CallableType)
            and return_type.fallback.type.fullname == "builtins.function"
        ):
            testable_symbol_table_node = checker.modules[cls.TYPES_MODULE].names[
                "Testable"
            ]  # direct lookup not working
            return_type.fallback = Instance(cast(TypeInfo, testable_symbol_table_node.node), [])

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


def plugin(version: str) -> type[PytestPlugin]:
    return PytestPlugin
