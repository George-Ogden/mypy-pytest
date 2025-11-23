from mypy.nodes import CallExpr, Expression

from .object_patch_call_checker import ObjectPatchCallChecker
from .test_utils import dump_expr, parse


def _attribute_arg_test_body(defs: str) -> None:
    parse_result = parse(defs)
    parse_result.accept_all()
    patch_call_checker = ObjectPatchCallChecker(parse_result.checker)

    call = parse_result.defs["call"]
    assert isinstance(call, CallExpr)
    attribute_arg = patch_call_checker._attribute_arg(call)
    expected = parse_result.defs.get("arg", None)
    assert isinstance(expected, Expression | None)

    if expected is None:
        assert attribute_arg is None
    else:
        assert dump_expr(attribute_arg) == dump_expr(expected)


def test_attribute_arg_unreadable() -> None:
    _attribute_arg_test_body(
        """
        from typing import Any, overload

        @overload
        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int) -> int:
            ...

        @overload
        def foo[T](target: Any, attribute: str, test: T) -> int:
            ...

        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int = 0) -> int:
            return extra_arg

        call = foo(foo, "bar", 10, extra_arg=0)
        arg = "bar"
        """
    )


def test_attribute_arg_readable() -> None:
    _attribute_arg_test_body(
        """
        from typing import Any, overload

        @overload
        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int) -> int:
            ...

        @overload
        def foo[T](target: Any, attribute: str, test: T) -> int:
            ...

        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int = 0) -> int:
            return extra_arg

        call = foo(*(foo, "bar", 10))
        """
    )
