from unittest import mock

from mypy.nodes import FuncDef
from mypy.types import CallableType
import pytest

from .fixture_manager import FixtureManager
from .test_info import TestInfo
from .test_utils import (
    check_error_messages,
    get_error_messages,
    parse,
    simple_module_lookup,
    test_info_from_defs,
    test_signature_from_fn_type,
)


def _test_info_from_fn_def_test_body(source: str, *, errors: list[str] | None = None) -> None:
    parse_result = parse(source)
    checker = parse_result.checker

    test_node = parse_result.defs["test_info"]
    assert isinstance(test_node, FuncDef)

    assert not checker.errors.is_errors()

    test_info = TestInfo.from_fn_def(test_node, checker=checker)

    messages = get_error_messages(checker)
    assert test_info is not None, messages

    check_error_messages(messages, errors=errors)


def test_test_info_from_fn_def_no_args() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info() -> None:
            ...
        """
    )


def test_test_info_from_fn_def_one_arg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(x: int):
            ...
        """
    )


def test_test_info_from_fn_def_keyword_arg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(*, x: int) -> None:
            ...
        """
    )


def test_test_info_from_fn_def_many_args() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info[T: int](x: T, y: T, z: int = 4) -> None:
            ...
        """,
        errors=["opt-arg"],
    )


def test_test_info_from_fn_def_pos_only_arg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(x, /) -> None:
            ...
        """,
        errors=["pos-only-arg"],
    )


def test_test_info_from_fn_def_vararg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(arg: object, *args: object) -> None:
            ...
        """,
        errors=["var-pos-arg"],
    )


def test_test_info_from_fn_def_varkwarg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(arg: object, **kwargs: object) -> None:
            ...
        """,
        errors=["var-kwarg"],
    )


def test_test_info_from_fn_def_vararg_and_varkwarg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(*args: object, **kwargs: object) -> None:
            ...
        """,
        errors=["var-pos-arg", "var-kwarg"],
    )


def test_test_info_from_fn_def_request_arg_any_type() -> None:
    _test_info_from_fn_def_test_body(
        """
        from typing import Any

        def test_info(request: Any) -> None:
            ...
        """,
    )


def test_test_info_from_fn_def_request_arg_wrong_type() -> None:
    _test_info_from_fn_def_test_body(
        """
        from _pytest.fixtures import SubRequest

        def test_info(request: SubRequest) -> None:
            ...
        """,
        errors=["request-type"],
    )


def test_test_info_from_fn_def_request_arg_correct_type() -> None:
    _test_info_from_fn_def_test_body(
        """
        from _pytest.fixtures import FixtureRequest

        def test_info(request: FixtureRequest) -> None:
            ...
        """,
    )


def _test_info_sub_signature_test_body(
    defs: str, argnames: str | list[str], *, errors: list[str] | None = None
) -> None:
    parse_result = parse(defs)
    checker = parse_result.checker

    fn_type = parse_result.types.get("sub_signature")
    assert isinstance(fn_type, CallableType | None)
    expected_signature = (
        None
        if fn_type is None
        else test_signature_from_fn_type(checker, fn_name="test_info", fn_type=fn_type)
    )

    test_info = test_info_from_defs(defs, name="test_info")

    assert not checker.errors.is_errors()
    sub_signature = test_info.sub_signature(argnames)

    messages = get_error_messages(checker)
    assert sub_signature == expected_signature, messages

    check_error_messages(messages, errors=errors)


def test_test_info_sub_signature_no_args() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info() -> None:
            ...

        def sub_signature() -> None:
            ...
        """,
        argnames=[],
    )


def test_test_info_sub_signature_single_arg() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info(x: int, y: bool) -> None:
            ...

        def sub_signature(x_1: int) -> None:
            ...
        """,
        argnames="x",
    )


def test_test_info_sub_signature_single_arg_sequence() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info(x: int, y: bool) -> None:
            ...

        def sub_signature(y: bool) -> None:
            ...
        """,
        argnames=["y"],
    )


def test_test_info_sub_signature_multiple_args() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info(x: int, y: bool, z: str) -> None:
            ...

        def sub_signature(z: str, x: int) -> None:
            ...
        """,
        argnames=["z", "x"],
    )


def _test_info_check_decorator_test_body(defs: str, *, errors: list[str] | None = None) -> None:
    test_info = test_info_from_defs(defs, name="test_info")
    assert test_info is not None
    [decorator] = test_info.decorators
    checker = test_info.checker

    assert not checker.errors.is_errors()
    test_info.check_decorator(decorator)

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_test_info_check_decorator_no_errors() -> None:
    _test_info_check_decorator_test_body("""
        import pytest

        @pytest.mark.parametrize(
            "x", [1, 2, 3, 4]
        )
        def test_info(x: int) -> None:
            ...
        """)


def test_test_info_check_decorator_no_errors_flipped_args() -> None:
    _test_info_check_decorator_test_body("""
        import pytest

        @pytest.mark.parametrize(
            argvalues="abcd",
            argnames="x",
            ids="dcba",
        )
        def test_info(x: str) -> None:
            ...
        """)


def test_test_info_check_decorator_shared_argnames() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            *("x", [])
        )
        def test_info(x: float) -> None:
            ...
        """,
        errors=["variadic-argnames-argvalues"],
    )


def test_test_info_check_decorator_shared_argnames_beyond_limit() -> None:
    with pytest.raises(TypeError):
        _test_info_check_decorator_test_body(
            """
            import pytest

            @pytest.mark.parametrize(
                "x", *((), ())
            )
            def test_info(x: float) -> None:
                ...
            """,
            errors=["variadic-argnames-argvalues"],
        )


def test_test_info_check_decorator_shared_argnames_as_dict() -> None:
    with pytest.raises(TypeError):
        _test_info_check_decorator_test_body(
            """
            import pytest

            @pytest.mark.parametrize(
                argvalues=[True, False],
                **dict(argnames="x", ids=[1, 0])
            )
            def test_info(x: bool) -> None:
                ...
            """,
            errors=["variadic-argnames-argvalues"],
        )


def test_test_info_check_decorator_wrapped_argvalues() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "x", *([True, False],)
        )
        def test_info(x: bool) -> None:
            ...
        """,
        errors=["variadic-argnames-argvalues"],
    )


def test_test_info_check_decorator_no_errors_unusual_types() -> None:
    _test_info_check_decorator_test_body("""
        import pytest

        @pytest.mark.parametrize(
            "x", iter([True, False])
        )
        def test_info(x: bool) -> None:
            ...
    """)


def test_test_info_check_decorator_no_errors_generic_type() -> None:
    _test_info_check_decorator_test_body("""
        import pytest

        @pytest.mark.parametrize(
            "x", iter([True, False])
        )
        def test_info[T: bool](x: T) -> None:
            ...
    """)


def test_test_info_check_decorator_no_errors_extra_generic_types() -> None:
    _test_info_check_decorator_test_body("""
        import pytest
        from typing import Iterable

        @pytest.mark.parametrize(
            "t", iter([True, False])
        )
        def test_info[I: Iterable, T: bool](i: I, t: T) -> None:
            ...
    """)


def test_test_info_check_decorator_invalid_argname() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "foo", [1, 2, 3]
        )
        def test_info(bar: int) -> None:
            ...
        """,
        errors=["unknown-argname"],
    )


def test_test_info_check_decorator_invalid_type() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "x", [1, 2, 3]
        )
        def test_info(x: str) -> None:
            ...
        """,
        errors=["arg-type"],
    )


def _test_info_check_test_body(defs: str, *, errors: list[str] | None = None) -> None:
    test_info = test_info_from_defs(defs, name="test_info")
    assert test_info is not None
    checker = test_info.checker

    parse_result = parse(defs)
    for def_ in parse_result.raw_defs:
        def_.accept(checker)

    assert not checker.errors.is_errors()

    with mock.patch.object(FixtureManager, "_module_lookup", simple_module_lookup):
        test_info.check()

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_test_info_check_no_decorators_no_arguments() -> None:
    _test_info_check_test_body(
        """
        def test_info() -> None:
            ...
        """
    )


def test_test_info_check_no_decorators_missing_argnames() -> None:
    _test_info_check_test_body(
        """
        def test_info(foo) -> None:
            ...
        """,
        errors=["missing-argname"],
    )


def test_test_info_check_single_decorator_valid_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ("foo",),
            [
                ("bar",),
                (10,),
                (False,),
            ]
        )
        def test_info(foo) -> None:
            ...
        """
    )


def test_test_info_check_multiple_decorators_valid_split_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "y",
            "abcdefg"
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """
    )


def test_test_info_check_multiple_decorators_missing_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "y",
            "abcdefg"
        )
        def test_info(x: int, y: str, z: float, missing1, missing2) -> None:
            ...
        """,
        errors=["missing-argname", "missing-argname"],
    )


def test_test_info_check_multiple_decorators_missing_optional_argname() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "y",
            "abcdefg"
        )
        def test_info(x: int, y: str, missing: bool, z: float) -> None:
            ...
        """,
        errors=["missing-argname"],
    )


def test_test_info_check_multiple_decorators_repeated_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "x, y",
            [
                (1, "1"),
                (5, "2"),
            ]
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """,
        errors=["repeated-argname"],
    )


def test_test_info_check_multiple_decorators_single_type_error() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "y",
            [["abcde"]]
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """,
        errors=["arg-type"],
    )


def test_test_info_check_multiple_decorators_multiple_type_errors() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "x",
            [1, 2, 8.0]
        )
        @pytest.mark.parametrize(
            "y",
            ["a", "b", False]
        )
        @pytest.mark.parametrize(
            "z",
            [object(), 1.0, "no", 2.0]
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """,
        errors=["arg-type"] * 4,
    )


def test_test_info_check_used_fixture_argument() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture(arg: int) -> str:
            return str(arg)

        @pytest.mark.parametrize(
            "arg",
            range(3)
        )
        def test_info(fixture: str) -> None:
            ...
        """
    )


def test_test_info_check_unused_fixture_argument() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture(arg: int) -> str:
            return str(arg)

        def test_info(fixture: str) -> None:
            ...
        """,
        errors=["missing-argname"],
    )


def test_test_info_check_double_used_fixture_argument() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture(arg: int) -> str:
            return str(arg)

        @pytest.mark.parametrize(
            "arg", [1, 2, 3]
        )
        @pytest.mark.parametrize(
            "fixture", "bar"
        )
        def test_info(fixture: str) -> None:
            ...
        """,
        errors=["repeated-fixture-argname"],
    )


def test_test_info_check_cyclic_fixture() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture
        def cycle_2(cycle_1: int) -> int:
            return cycle_1 + 1

        @pytest.fixture
        def cycle_1(cycle_2: int) -> int:
            return cycle_2 + 1

        def test_info(cycle_1: int) -> None:
            ...
        """
    )


def test_test_info_check_fixture_valid_scopes() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture(scope="class")
        def class_fixture() -> None:
            ...

        @pytest.fixture(scope="function")
        def function_fixture(class_fixture: None) -> None:
            ...

        def test_info(function_fixture: None) -> None:
            ...
        """
    )


def test_test_info_check_fixture_invalid_scopes() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture(scope="class")
        def class_fixture(function_fixture: None) -> None:
            ...

        @pytest.fixture(scope="function")
        def function_fixture() -> None:
            ...

        def test_info(class_fixture: None) -> None:
            ...
        """,
        errors=["inverted-fixture-scope"],
    )


def test_test_info_check_fixture_shadowed_scope() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture(scope="class")
        def class_fixture(function_fixture: None) -> None:
            ...

        @pytest.fixture(scope="function")
        def function_fixture() -> None:
            ...

        @pytest.mark.parametrize("function_fixture", [None])
        def test_info(class_fixture: None) -> None:
            ...
        """,
    )


def test_test_info_check_fixture_unknown_scope() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Literal

        scope: Literal["module", "class"] = "module"

        @pytest.fixture(scope=scope)
        def unknown_fixture(function_fixture: None) -> None:
            ...

        @pytest.fixture(scope="function")
        def function_fixture(unknown_fixture: None) -> None:
            ...

        def test_info(unknown_fixture: None) -> None:
            ...
        """,
        errors=["invalid-fixture-scope"],
    )


def test_test_info_check_fixture_invalid_types() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Literal

        @pytest.fixture
        def indirect_fixture() -> Literal[0]:
            return 0

        @pytest.fixture
        def direct_fixture(indirect_fixture: Literal[1]) -> Literal[1]:
            return indirect_fixture

        def test_info(direct_fixture: Literal[2]) -> None:
            ...
        """,
        errors=["fixture-arg-type"] * 2,
    )


def test_test_info_check_fixture_and_arg_both_supplied() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture(arg: None) -> None:
            return arg

        @pytest.mark.parametrize(
            "arg, fixture", [(None, None)]
        )
        def test_info(fixture: None, arg: None) -> None:
            ...
        """,
    )


def test_test_info_check_fixture_and_arg_one_supplied() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture(arg: None) -> None:
            return arg

        @pytest.mark.parametrize(
            "arg", [None]
        )
        def test_info(fixture: None, arg: None) -> None:
            ...
        """,
    )


def test_test_info_check_fixture_valid_argname_generic_types() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Any

        @pytest.fixture
        def fixture[T](arg: T) -> T:
            return arg

        @pytest.mark.parametrize(
            "arg", [1, 2, 3]
        )
        def test_info(fixture: Any) -> None:
            ...
        """,
    )


def test_test_info_check_fixture_valid_subtype() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Literal

        @pytest.fixture
        def true_fixture() -> Literal[True]:
            return True

        def test_info(true_fixture: bool) -> None:
            ...
        """,
    )


def test_test_info_check_valid_argument_subtype() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Literal

        @pytest.fixture
        def true_fixture() -> Literal[True]:
            return True

        @pytest.fixture
        def fixture(true_fixture: bool) -> None:
            ...

        def test_info(fixture: None) -> None:
            ...
        """,
    )


def test_test_info_check_fixture_invalid_subtype() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Literal

        @pytest.fixture
        def bool_fixture() -> bool:
            return True

        def test_info(bool_fixture: Literal[True]) -> None:
            ...
        """,
        errors=["fixture-arg-type"],
    )


def test_test_info_check_invalid_argument_subtypes() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Literal

        @pytest.fixture
        def bool_fixture() -> bool:
            return True

        @pytest.fixture
        def fixture(bool_fixture: Literal[True]) -> None:
            ...

        def test_info(fixture: None) -> None:
            ...
        """,
        errors=["fixture-arg-type"],
    )


def test_test_info_check_valid_shadowed_subtypes() -> None:
    _test_info_check_test_body(
        """
        import pytest
        from typing import Literal

        @pytest.fixture
        def bool_fixture() -> bool:
            return True

        @pytest.fixture
        def int_fixture(bool_fixture: int) -> int:
            return bool_fixture

        @pytest.mark.parametrize(
            "int_fixture", [1]
        )
        @pytest.mark.parametrize(
            "bool_fixture", [0]
        )
        def test_info(int_fixture: int, bool_fixture: int) -> None:
            ...
        """
    )
