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

UNKNOWN_ARGNAME: Final[ErrorCode] = ErrorCode(
    "unknown-argname",
    "Pytest parametrize contains argname not used in test signature.",
    category="Pytest",
)

DUPLICATE_ARGNAME: Final[ErrorCode] = ErrorCode(
    "duplicate-argname", "Pytest parametrize contains duplicate argnames.", category="Pytest"
)

REPEATED_ARGNAME: Final[ErrorCode] = ErrorCode(
    "repeated-argname", "Pytest parametrizations contain repeated argname.", category="Pytest"
)

MISSING_ARGNAME: Final[ErrorCode] = ErrorCode(
    "missing-argname", "Argument not included in Pytest parametrization.", category="Pytest"
)

VARIADIC_ARGNAMES_ARGVALUES: Final[ErrorCode] = ErrorCode(
    "variadic-argnames-argvalues",
    "Unable to parse variadic argnames or argvalues.",
    category="Pytest",
)


UNRECOGNIZED_ARGNAME: Final[ErrorCode] = ErrorCode(
    "unrecognized-argname",
    "Pytest parametrize contains an argument not in the function.",
    category="Pytest",
)


POSITIONAL_ONLY_ARGUMENT: Final[ErrorCode] = ErrorCode(
    "pos-only-arg",
    "Positional only arguments are ignored in Pytest test or fixture definitions.",
    category="Pytest",
)

OPTIONAL_ARGUMENT: Final[ErrorCode] = ErrorCode(
    "opt-arg",
    "Optionalarguments are ignored in Pytest test or fixture definitions.",
    category="Pytest",
)

VARIADIC_POSITIONAL_ARGUMENT: Final[ErrorCode] = ErrorCode(
    "var-pos-arg",
    "Variadic positional arguments are ignored in Pytest test or fixture definitions.",
    category="Pytest",
)


VARIADIC_KEYWORD_ARGUMENT: Final[ErrorCode] = ErrorCode(
    "var-keyword-arg",
    "Keyword-only positional arguments are ignored in Pytest test or fixture definitions.",
    category="Pytest",
)

ITERABLE_SEQUENCE: Final[ErrorCode] = ErrorCode(
    "iterable-sequence",
    """"Sequence" passed into a function expecting "Iterable" in a test.""",
    category="robust-testing",
)
