from mypy.nodes import CallExpr

from .param_mark_checker import ParamMarkChecker
from .test_utils import check_error_messages, get_error_messages, parse


def _check_usefixtures_test_body(defs: str, *, errors: list[str] | None = None) -> None:
    parse_result = parse(defs, header="import _pytest.mark.structures")
    parse_result.accept_all()

    call = parse_result.defs["call"]
    assert isinstance(call, CallExpr)

    checker = parse_result.checker
    ParamMarkChecker(checker).check_param_marks(call)

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_check_usefixtures_no_marks() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        call = pytest.param("mark")
        """
    )


def test_check_usefixtures_not_a_call() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        call = pytest.param(marks=pytest.mark.usefixtures)
        """
    )


def test_check_usefixtures_direct_arg_usefixtures() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        call = pytest.param(marks=pytest.mark.usefixtures())
        """,
        errors=["param-usefixtures"],
    )


def test_check_usefixtures_direct_arg_not_usefixtures() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        call = pytest.param(marks=pytest.mark.skip)
        """
    )


def test_check_usefixtures_list_arg_usefixtures() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        call = pytest.param(marks=[pytest.mark.usefixtures("capsys")])
        """,
        errors=["param-usefixtures"],
    )


def test_check_usefixtures_set_arg_mix() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        call = pytest.param(marks={pytest.mark.skip, pytest.mark.usefixtures()})
        """,
        errors=["param-usefixtures"],
    )


def test_check_usefixtures_tuple_arg_not_usefixtures() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        call = pytest.param(marks=(pytest.mark.skip,))
        """
    )


def test_check_usefixtures_name_arg_indirect_usefixtures() -> None:
    _check_usefixtures_test_body(
        """
        import pytest
        from pytest import mark
        uf = mark.usefixtures
        call = pytest.param(marks=uf("fixture"))
        """,
        errors=["param-usefixtures"],
    )
