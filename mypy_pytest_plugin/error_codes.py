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


REPEATED_FIXTURE_ARGNAME: Final[ErrorCode] = ErrorCode(
    "repeated-fixture-argname",
    "Pytest parametrization contains an argument that is shadowed by a fixture.",
    category="Pytest",
)

MISSING_ARGNAME: Final[ErrorCode] = ErrorCode(
    "missing-argname", "Argument not included in Pytest parametrization.", category="Pytest"
)

UNREADABLE_ARGNAMES_ARGVALUES: Final[ErrorCode] = ErrorCode(
    "unreadable-argnames-argvalues",
    "Unable to read argnames or argvalues.",
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
    "var-kwarg",
    "Keyword-only positional arguments are ignored in Pytest test or fixture definitions.",
    category="Pytest",
)

DUPLICATE_FIXTURE: Final[ErrorCode] = ErrorCode(
    "duplicate-fixture",
    "Only one use of `pytest.fixture` is allowed per test.",
    category="Pytest",
)

MARKED_FIXTURE: Final[ErrorCode] = ErrorCode(
    "marked-fixture",
    "Do not use `pytest.mark` with `pytest.fixture`.",
    category="Pytest",
)

INVALID_FIXTURE_SCOPE: Final[ErrorCode] = ErrorCode(
    "invalid-fixture-scope",
    "Use literal value for the scope of a Pytest fixture.",
    category="Pytest",
)

INVERTED_FIXTURE_SCOPE: Final[ErrorCode] = ErrorCode(
    "inverted-fixture-scope",
    "Fixtures are not allowed to request other fixtures with wider scopes.",
    category="Pytest",
)

FIXTURE_ARGUMENT_TYPE: Final[ErrorCode] = ErrorCode(
    "fixture-arg-type",
    "Fixture requests a different fixture with the incorrect argument type.",
    category="Pytest",
)

REQUEST_TYPE: Final[ErrorCode] = ErrorCode(
    "request-type",
    """"request" argument always has a fixed type to fixtures and test and the provided annotation does not match that.""",
    category="Pytest",
)

REQUEST_KEYWORD: Final[ErrorCode] = ErrorCode(
    "request-keyword",
    """"request" is a reserved word in Pytest.""",
    category="Pytest",
)

UNKNOWN_MARK: Final[ErrorCode] = ErrorCode(
    "unknown-mark",
    "Mark name is not recognized as a pre-defined or user-defined mark.",
    category="Pytest",
)

PARAM_USEFIXTURES: Final[ErrorCode] = ErrorCode(
    "param-usefixtures",
    "`pytest.mark.usefixtures` is not allowed as a `pytest.param`.",
    category="Pytest",
)

ITERABLE_SEQUENCE: Final[ErrorCode] = ErrorCode(
    "iterable-sequence",
    """"Sequence" passed into a function expecting "Iterable" in a test.""",
    category="robust-testing",
)
