from .test_utils import test_info_from_defs


def _decorator_wrapper_from_node_test_body(defs: str, is_decorator: bool) -> None:
    test_info = test_info_from_defs(defs, name="test_info")
    if is_decorator:
        [decorator] = test_info.decorators
        _ = decorator.arg_names_and_arg_values
    else:
        assert test_info.decorators == []


def test_decorator_wrapper_from_default_node() -> None:
    _decorator_wrapper_from_node_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "foo",
            [1, 2, 3]
        )
        def test_info(foo: int) -> None:
            ...
        """,
        True,
    )


def test_decorator_wrapper_from_valid_obscured_node() -> None:
    _decorator_wrapper_from_node_test_body(
        """
        from pytest import mark as mach

        pmt = (lambda *_: mach.parametrize)()
        val = [1, 2, 3]

        @pmt("name", val)
        def test_info(name: str) -> None:
            ...
        """,
        True,
    )


def test_decorator_wrapper_from_not_call() -> None:
    _decorator_wrapper_from_node_test_body(
        """
        import pytest

        decorator = pytest.mark.parametrize(
            "foo",
            [1, 2, 3]
        )

        @decorator
        def test_info(foo: int) -> None:
            ...
        """,
        False,
    )


def test_decorator_wrapper_from_different_call() -> None:
    _decorator_wrapper_from_node_test_body(
        """
        import pytest
        from typing import Any

        def parametrize(argnames: str, argvals: str) -> Any:
            ...

        @parametrize("foo", "bar")
        def test_info(foo: str) -> None:
            ...
        """,
        False,
    )
