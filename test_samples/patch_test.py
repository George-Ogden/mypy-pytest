import math
from typing import Any, Callable, cast, overload
from unittest import mock

mock.patch()

mock.patch("os.getcwd", lambda: "str")
mock.patch("os.getcwd", lambda: None)
mock.patch("os.getcwd", mock.Mock(return_value="dir"))
mock.patch("os.getcwd", mock.Mock(return_value=10))


def fabs_mock(x: float, /) -> float:
    return math.fabs(x)


mock.patch("math.fabs", fabs_mock)
mock.patch("math.fabs", mock.MagicMock(return_value=0.0))
mock.patch(
    "math.fabs",
    mock.MagicMock(
        side_effect=(
            cast(
                list[float | RuntimeError | type[RuntimeError]], [1.0, RuntimeError, RuntimeError()]
            )
        )
    ),
)
mock.patch("math.fabs", mock.NonCallableMagicMock())

mock.patch("unknown.unknown", lambda: None)


class Foo:
    @staticmethod
    def static(bar: str) -> None: ...

    @classmethod
    def cls(cls, bar: int) -> int:
        return bar

    def instance(self, bar: float) -> tuple[float, float]:
        return (bar, bar)


def static(bar: str) -> None: ...


def cls(cls: Any, bar: int) -> int:
    return bar


def instance(self: Any, bar: float) -> tuple[float, float]:
    return (bar, bar)


mock.patch("patch_test.Foo.static", lambda: None)
mock.patch("patch_test.Foo.static", static)
mock.patch("patch_test.Foo.cls", lambda: None)
mock.patch("patch_test.Foo.cls", cls)
mock.patch("patch_test.Foo.instance", lambda: None)
mock.patch("patch_test.Foo.instance", instance)


@overload
def foo(x: int, /) -> int: ...


@overload
def foo(y: str, /) -> str: ...


def foo(z: Any, /) -> Any: ...


mock.patch("patch_test.foo", lambda x: x)
mock.patch("patch_test.foo", mock.Mock(lambda: None))


class PropertyClass:
    x: int

    @property
    def y(self) -> int:
        return 0


mock.patch("patch_test.PropertyClass.x", 3)
mock.patch("patch_test.PropertyClass.x", "3")
mock.patch("patch_test.PropertyClass.y", 3)
mock.patch("patch_test.PropertyClass.y", mock.PropertyMock(return_value=3))
mock.patch("patch_test.PropertyClass.y", mock.PropertyMock(return_value=None))

type C = Callable[[int], int]


class TypeAliasTest:
    f: C = lambda x: x


mock.patch.object(TypeAliasTest, "f", lambda: None)
mock.patch.object(TypeAliasTest, "f", lambda n: n)

value = None
mock.patch("patch_test.value", mock.Mock(side_effect=None))
mock.patch("patch_test.value", mock.Mock(side_effect=[None]))
mock.patch("patch_test.value", mock.Mock(side_effect=[None, RuntimeError(), RuntimeError]))
mock.patch("patch_test.value", mock.Mock(side_effect=[RuntimeError]))
mock.patch("patch_test.value", mock.Mock(side_effect=[RuntimeError()]))
mock.patch("patch_test.value", mock.Mock(side_effect=RuntimeError()))
mock.patch("patch_test.value", mock.Mock(side_effect=RuntimeError))
