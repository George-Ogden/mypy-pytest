from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, Mock, NonCallableMock, PropertyMock

if TYPE_CHECKING:
    from mypy_pytest_plugin_types.mock import Mock as _Mock
    from mypy_pytest_plugin_types.mock import NonCallableMock as _NonCallableMock

string_mock: _Mock[Any, str] = Mock(return_value="string")
string_mock.return_value = 5


def increment_int(x: int) -> int:
    return x + 1


def decrement_int(x: int) -> int:
    return x - 1


def increment_float(x: float) -> float:
    return x + 1


increment_mock = Mock(wraps=increment_int)
increment_mock.side_effect = increment_float
increment_mock.side_effect = decrement_int

non_callable_mock: _NonCallableMock[[str], None] = NonCallableMock(wraps=sys.exit)
non_callable_mock.return_value = None
non_callable_mock.return_value = "None"

decrement_mock = MagicMock(wraps=decrement_int)
decrement_mock.side_effect = increment_float
decrement_mock.side_effect = decrement_int

property_mock = PropertyMock(return_value=5)
property_mock.return_value = None

Mock() + Mock()
MagicMock() + MagicMock()

if sys.version_info >= (3, 13):
    from unittest.mock import ThreadingMock

    ThreadingMock()
