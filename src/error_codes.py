from typing import Final

from mypy.errorcodes import ErrorCode

INVALID_ARGNAME: Final[ErrorCode] = ErrorCode(
    "invalid-argname", "Invalid Python identifier used in argname.", category="Pytest"
)

UNREADABLE_ARGNAME: Final[ErrorCode] = ErrorCode(
    "unreadable-argname", "Unable to parse Pytest argname.", category="Pytest"
)
