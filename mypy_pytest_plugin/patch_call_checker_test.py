import textwrap

from inline_snapshot import snapshot
from mypy.nodes import CallExpr, Expression

from .patch_call_checker import PatchCallChecker
from .test_utils import dump_expr, parse


def _target_arg_test_body(defs: str) -> None:
    parse_result = parse(defs)
    parse_result.accept_all()
    patch_call_checker = PatchCallChecker(parse_result.checker)

    call = parse_result.defs["call"]
    assert isinstance(call, CallExpr)
    target_arg = patch_call_checker._target_arg(call)
    expected = parse_result.defs.get("arg", None)
    assert isinstance(expected, Expression | None)

    if expected is None:
        assert target_arg is None
    else:
        assert dump_expr(target_arg) == dump_expr(expected)


def test_target_arg_no_args() -> None:
    _target_arg_test_body(
        """
        def foo() -> int:
            return 0

        call = foo()
        """
    )


def test_target_arg_multi_arg_pos_only() -> None:
    _target_arg_test_body(
        """
        from typing import Any

        def bar(target: int, *args: Any) -> int:
            return 0

        call = bar(10, "w", (), [])
        arg = 10
        """
    )


def test_target_arg_multi_arg_variadic() -> None:
    _target_arg_test_body(
        """
        from typing import Any

        def baz(target: str, *args: Any) -> int:
            return 0

        call = baz(*("a", "b"))
        """
    )


def _string_value_test_body(defs: str, expected: str | None) -> None:
    parse_result = parse(defs)
    patch_call_checker = PatchCallChecker(parse_result.checker)

    parse_result.accept_all()

    expr = parse_result.defs["string"]
    assert isinstance(expr, Expression)
    assert patch_call_checker._string_value(expr) == expected


def test_string_value_empty_string() -> None:
    _string_value_test_body(
        """
        string = ""
        """,
        "",
    )


def test_string_value_non_empty_string() -> None:
    _string_value_test_body(
        """
        string = "string"
        """,
        "string",
    )


def test_string_value_literal_type() -> None:
    _string_value_test_body(
        """
        from typing import cast, Literal

        string = cast(Literal["foo"], "foo")
        """,
        "foo",
    )


def test_string_value_unreadable() -> None:
    _string_value_test_body(
        """
        from typing import cast, Literal

        string = cast(Literal["foo", "bar"], "foo")
        """,
        None,
    )


def _specialized_patcher_type_test_body(defs: str, expected_type: str | None) -> None:
    defs = f"import mypy_pytest_plugin_types\n{textwrap.dedent(defs)}"
    parse_result = parse(defs)
    original_type = parse_result.types["original"]
    assert original_type is not None

    patcher_type = PatchCallChecker(parse_result.checker)._specialized_patcher_type(original_type)
    if expected_type is None:
        assert patcher_type is None
    else:
        assert patcher_type is not None
        assert str(patcher_type) == expected_type


def test_specialized_patcher_type_original_any() -> None:
    _specialized_patcher_type_test_body(
        """
        from typing import Any

        original: Any
        """,
        None,
    )


def test_specialized_patcher_type_original_callable_no_args() -> None:
    _specialized_patcher_type_test_body(
        """
        from typing import Any, Callable

        original: Callable[[], Any]
        """,
        snapshot(
            "mypy_pytest_plugin_types.mock._patcher[mypy_pytest_plugin_types.mock.Mock[[], Any] | def () -> Any]"
        ),
    )


def test_specialized_patcher_type_original_callable_pos_only_args() -> None:
    _specialized_patcher_type_test_body(
        """
        def original(x: int, y: str, /) -> bool:
            return False
        """,
        snapshot(
            "mypy_pytest_plugin_types.mock._patcher[mypy_pytest_plugin_types.mock.Mock[[builtins.int, builtins.str], builtins.bool] | def (builtins.int, builtins.str) -> builtins.bool]"
        ),
    )


def test_specialized_patcher_type_original_callable_complex_signature() -> None:
    _specialized_patcher_type_test_body(
        """
        def original(x: int, /, *, y: str) -> bool:
            return False
        """,
        snapshot(
            "mypy_pytest_plugin_types.mock._patcher[mypy_pytest_plugin_types.mock.Mock[[builtins.int, *, y: builtins.str], builtins.bool] | def (builtins.int, *, y: builtins.str) -> builtins.bool]"
        ),
    )


def test_specialized_patcher_type_original_overloaded() -> None:
    _specialized_patcher_type_test_body(
        """
        from typing import Any, overload

        @overload
        def original(*, x: int) -> int:
            ...

        @overload
        def original(*, y: str) -> str:
            ...

        def original(**kwargs: Any) -> Any:
            ...
        """,
        snapshot(
            "mypy_pytest_plugin_types.mock._patcher[Overload(def (*, x: builtins.int) -> builtins.int, def (*, y: builtins.str) -> builtins.str)]"
        ),
    )
