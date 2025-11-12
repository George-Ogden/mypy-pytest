from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Self

from mypy.nodes import Decorator, FuncDef, Statement

from .test_name_checker import TestNameChecker


@dataclass(frozen=True, slots=True)
class TestBodyRanges:
    lower: Sequence[int]
    upper: Sequence[int]

    @classmethod
    def from_defs(cls, defs: Sequence[Statement]) -> Self:
        return cls.from_ranges(
            cls.fn_range(def_)
            for def_ in defs
            if isinstance(def_, FuncDef | Decorator) and TestNameChecker.is_test_fn_name(def_.name)
        )

    @classmethod
    def from_ranges(cls, ranges: Iterable[tuple[int, int]]) -> Self:
        pairs = tuple(zip(*ranges, strict=True))
        if len(pairs) == 0:
            return cls([], [])
        return cls(*pairs)

    @classmethod
    def fn_range(cls, fn_def: FuncDef | Decorator) -> tuple[int, int]:
        if isinstance(fn_def, Decorator):
            fn_def = fn_def.func
        return fn_def.line, fn_def.end_line or fn_def.line
