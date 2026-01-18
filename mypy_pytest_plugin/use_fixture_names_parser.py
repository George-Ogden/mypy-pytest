from dataclasses import dataclass
from typing import override

from mypy.checker import TypeChecker
from mypy.nodes import (
    Context,
)

from .error_codes import (
    INVALID_USEFIXTURES,
    REQUEST_KEYWORD,
    UNREADABLE_USEFIXTURES,
)
from .names_parser import NamesParser


@dataclass(frozen=True)
class UseFixtureNamesParser(NamesParser):
    checker: TypeChecker

    @override
    def _fail_invalid_identifier(self, name: str, context: Context) -> None:
        self.fail(
            f"Invalid identifier {name!r} for fixture name.",
            context=context,
            code=INVALID_USEFIXTURES,
        )

    @override
    def _fail_keyword_identifier(self, name: str, context: Context) -> None:
        self.fail(
            f"Keyword {name!r} used as a fixture name.",
            context=context,
            code=INVALID_USEFIXTURES,
        )

    @override
    def _fail_unreadable_identifier(self, context: Context) -> None:
        self.fail(
            "Unable to read fixture name. (Use string literals instead.)",
            context=context,
            code=UNREADABLE_USEFIXTURES,
        )

    @override
    def _fail_request_identifier(self, name: str, context: Context) -> None:
        self.fail(
            f"{name!r} is not allowed as a fixture name; it is a reserved word in Pytest.",
            context=context,
            code=REQUEST_KEYWORD,
        )
