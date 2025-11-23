from typing import Any, cast

from mypy.nodes import CallExpr, Expression

from .argmapper import ArgMapper
from .test_utils import parse


def _named_arg_mapping_test_body(defs: str, expected_keys: list[str]) -> None:
    parse_result = parse(defs)
    parse_result.accept_all()

    call = parse_result.defs["call"]
    assert isinstance(call, CallExpr)

    raw_arg_map = ArgMapper.named_arg_mapping(call, parse_result.checker)

    def dump_arg_map(
        arg_map: dict[str, Expression],
    ) -> dict[str, tuple[type[Expression], dict[str, Any]]]:
        return {
            key: (
                type(expr),
                {attr: getattr(expr, attr) for attr in expr.__match_args__},  # type: ignore
            )
            for key, expr in arg_map.items()
        }

    assert dump_arg_map(raw_arg_map) == dump_arg_map(
        {key: cast(Expression, parse_result.defs[key]) for key in expected_keys}
    )


def test_named_arg_mapping_no_args() -> None:
    _named_arg_mapping_test_body(
        """
        def main() -> int:
            return 0

        call = main()
        """,
        [],
    )


def test_named_arg_mapping_no_named_args() -> None:
    _named_arg_mapping_test_body(
        """
        def main(x: int, y: str, /, *args: bool) -> int:
            return 0

        call = main(3, "2", True, False)
        """,
        [],
    )


def test_named_arg_mapping_named_args_only() -> None:
    _named_arg_mapping_test_body(
        """
        def main(x: int, y: bool, *, z: str) -> int:
            return 0

        call = main(0, z="1", y=False)
        x = 0
        y = False
        z = "1"
        """,
        ["x", "y", "z"],
    )


def test_named_arg_mapping_arg_mix() -> None:
    _named_arg_mapping_test_body(
        """
        from typing import Any

        def main(a: int, /, b: bool, *args: Any, c: float, **kwargs: dict) -> int:
            return 0

        call = main(0, True, 2j, c=3.0, d={}, e=dict())
        b = True
        c = 3.0
        """,
        ["b", "c"],
    )


def test_named_arg_mapping_simple_overload() -> None:
    _named_arg_mapping_test_body(
        """
        from typing import overload

        @overload
        def foo(x: int) -> int:
            ...

        @overload
        def foo(x: str) -> str:
            ...

        def foo(x: str | int) -> str | int:
            return x

        call = foo(x="str")
        x = "str"
        """,
        ["x"],
    )


def test_named_arg_mapping_complex_overload() -> None:
    _named_arg_mapping_test_body(
        """
        from typing import overload

        @overload
        def foo(x: int, y: str, *, z: bool) -> int:
            ...

        @overload
        def foo(x: int, y: str) -> int:
            ...

        def foo(x: int, y: str, **kwargs: bool) -> int:
            return 0

        call = foo(y="0", z=False, x=2)
        x = 2
        y = "0"
        """,
        ["x", "y"],
    )


def test_named_arg_mapping_varargs_varkwargs_overload() -> None:
    _named_arg_mapping_test_body(
        """
        from typing import overload

        @overload
        def foo(x: int, y: str, **kwargs: bool) -> int:
            ...

        @overload
        def foo(x: int, y: str, **kwargs: int) -> int:
            ...

        def foo(x: int, y: str, **kwargs: bool | int) -> int:
            return 0

        call = foo(*(1, "2"), z=True)
        """,
        [],
    )


def test_named_arg_mapping_instance_method() -> None:
    _named_arg_mapping_test_body(
        """
        from typing import overload

        class Foo:
            def bar(self, x: str, y: str, *args: str) -> str:
                return x + y

        foo = Foo()
        call = foo.bar("a", "b", "c")
        x = "a"
        y = "b"
        """,
        ["x", "y"],
    )


def test_named_arg_mapping_call_method() -> None:
    _named_arg_mapping_test_body(
        """
        from typing import overload

        class Foo:
            def __call__(self, x: str, y: str, *args: str) -> str:
                return x + y

        foo = Foo()
        call = foo("a", "b", "c")
        x = "a"
        y = "b"
        """,
        ["x", "y"],
    )
