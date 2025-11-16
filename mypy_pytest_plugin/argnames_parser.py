from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

from mypy.checker import TypeChecker
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
    UNREADABLE_ARGNAME,
    UNREADABLE_ARGNAMES,
)


@dataclass(frozen=True)
class ArgnamesParser:
    checker: TypeChecker

    def parse_names(self, node: Expression) -> str | list[str] | None:
        match node:
            case StrExpr():
                argnames = self.parse_names_string(node)
            case ListExpr() | TupleExpr():
                argnames = self.parse_names_sequence(node)
            case _:
                self.checker.fail(
                    "Unable to identify argnames. (Use a comma-separated string, list of strings or tuple of strings).",
                    context=node,
                    code=UNREADABLE_ARGNAMES,
                )
                return None
        argnames = self._check_duplicate_argnames(argnames, node)
        return argnames

    def _check_valid_identifier(self, name: str, context: StrExpr) -> bool:
        if not (valid_identifier := name.isidentifier()):
            self.checker.fail(
                f"Invalid identifier {name!r}.", context=context, code=INVALID_ARGNAME
            )
        return valid_identifier

    def parse_names_string(self, node: StrExpr) -> str | list[str] | None:
        individual_names = [name.strip() for name in node.value.split(",")]
        filtered_names = [name for name in individual_names if name]
        if any([not self._check_valid_identifier(name, node) for name in filtered_names]):
            return None
        if len(filtered_names) == 1:
            [name] = filtered_names
            return name
        return filtered_names

    def _parse_name(self, node: Expression) -> str | None:
        if isinstance(node, StrExpr):
            name = node.value
            if self._check_valid_identifier(name, node):
                return name
        else:
            self.checker.fail(
                "Unable to read identifier. (Use a sequence of strings instead.)",
                context=node,
                code=UNREADABLE_ARGNAME,
            )
        return None

    def parse_names_sequence(self, node: TupleExpr | ListExpr) -> list[str] | None:
        names = [self._parse_name(item) for item in node.items]
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
            self.checker.fail(
                f"Duplicated argname {argname!r}.", context=context, code=DUPLICATE_ARGNAME
            )
