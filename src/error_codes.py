from typing import Final

from mypy.errorcodes import ErrorCode

INVALID_ARGNAME: Final[ErrorCode] = ErrorCode(
    "invalid-argname", "Invalid Python identifier used in argname.", category="Pytest"
)

UNREADABLE_ARGNAME: Final[ErrorCode] = ErrorCode(
    "unreadable-argname", "Unable to parse Pytest argname.", category="Pytest"
)

UNREADABLE_ARGNAMES: Final[ErrorCode] = ErrorCode(
    "unreadable-argnames", "Unable to parse Pytest argnames.", category="Pytest"
)


POSITIONAL_ONLY_ARGUMENT: Final[ErrorCode] = ErrorCode(
    "pos-only-arg",
    "Positional only arguments not allowed in Pytest test definitions.",
    category="Pytest",
)


VARIADIC_POSITIONAL_ARGUMENT: Final[ErrorCode] = ErrorCode(
    "var-pos-arg",
    "Variadic positional arguments not allowed in Pytest test definitions.",
    category="Pytest",
)


VARIADIC_KEYWORD_ARGUMENT: Final[ErrorCode] = ErrorCode(
    "var-keyword-arg",
    "Keyword-only positional arguments not allowed in Pytest test definitions.",
    category="Pytest",
)
