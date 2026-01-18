from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast, override

from mypy.nodes import (
    Context,
    Expression,
    ListExpr,
    StrExpr,
    TupleExpr,
)

from .error_codes import (
    DUPLICATE_ARGNAME,
    INVALID_ARGNAME,
    REQUEST_KEYWORD,
    UNREADABLE_ARGNAME,
    UNREADABLE_ARGNAMES,
)
from .names_parser import NamesParser
from .utils import cache_by_id


@dataclass(frozen=True)
class ArgnamesParser(NamesParser):
    def __post_init__(self) -> None:
        object.__setattr__(self, "parse_names", cache_by_id(self.parse_names))

    def parse_names(self, expression: Expression) -> str | list[str] | None:
        match expression:
            case StrExpr():
                argnames = self.parse_names_string(expression)
            case ListExpr() | TupleExpr():
                argnames = self.parse_names_sequence(expression)
            case _:
                self._fail_unreadable_argnames(expression)
                return None
        argnames = self._check_duplicate_argnames(argnames, expression)
        return argnames

    def _fail_unreadable_argnames(self, context: Context) -> None:
        self.fail(
            "Unable to identify argnames. (Use a comma-separated string, list of strings or tuple of strings).",
            context=context,
            code=UNREADABLE_ARGNAMES,
        )

    def parse_names_string(self, expression: StrExpr) -> str | list[str] | None:
        individual_names = [name.strip() for name in expression.value.split(",")]
        filtered_names = [name for name in individual_names if name]
        if any([not self._check_valid_identifier(name, expression) for name in filtered_names]):
            return None
        if len(filtered_names) == 1:
            [name] = filtered_names
            return name
        return filtered_names

    def parse_names_sequence(self, expr: TupleExpr | ListExpr) -> list[str] | None:
        names = [self.parse_name(item) for item in expr.items]
        if all([isinstance(name, str) for name in names]):
            return cast(list[str], names)
        return None

    def _check_duplicate_argnames(
        self, argnames: str | list[str] | None, context: Context
    ) -> str | list[str] | None:
        if isinstance(argnames, list):
            return self._check_duplicate_argnames_sequence(argnames, context)
        return argnames

    def _check_duplicate_argnames_sequence(
        self, argnames: list[str], context: Context
    ) -> None | list[str]:
        argname_counts = Counter(argnames)
        duplicates = [argname for argname, count in argname_counts.items() if count > 1]
        if duplicates:
            self._warn_duplicate_argnames(duplicates, context)
            return None
        return argnames

    def _warn_duplicate_argnames(self, duplicates: Iterable[str], context: Context) -> None:
        for argname in duplicates:
            self.fail(
                f"Duplicated argname {argname!r}.",
                context=context,
                code=DUPLICATE_ARGNAME,
            )

    @override
    def _fail_invalid_identifier(self, name: str, context: Context) -> None:
        self.fail(
            f"Invalid identifier {name!r} for argname.",
            context=context,
            code=INVALID_ARGNAME,
        )

    @override
    def _fail_keyword_identifier(self, name: str, context: Context) -> None:
        self.fail(
            f"Keyword {name!r} used as an argname.",
            context=context,
            code=INVALID_ARGNAME,
        )

    @override
    def _fail_unreadable_identifier(self, context: Context) -> None:
        self.fail(
            "Unable to read argname. (Use string literals instead.)",
            context=context,
            code=UNREADABLE_ARGNAME,
        )

    @override
    def _fail_request_identifier(self, name: str, context: Context) -> None:
        self.fail(
            f"{name!r} is not allowed as an argname; it is a reserved word in Pytest.",
            context=context,
            code=REQUEST_KEYWORD,
        )
