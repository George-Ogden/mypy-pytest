from collections.abc import Mapping
from dataclasses import dataclass
import textwrap

import mypy.build
from mypy.checker import TypeChecker
import mypy.modulefinder
import mypy.nodes
import mypy.options
from mypy.subtypes import is_same_type
from mypy.types import CallableType, Type

from .test_utils import test_signature_from_fn_type


@dataclass(frozen=True)
class TypeLookup:
    _names: Mapping[str, mypy.nodes.SymbolTableNode]

    def __getitem__(self, name: str) -> Type | None:
        return self._names[name].type


def parse_types(code: str) -> tuple[TypeChecker, TypeLookup]:
    code = textwrap.dedent(code).strip()

    options = mypy.options.Options()
    options.incremental = True
    options.show_traceback = True

    result = mypy.build.build(
        sources=[mypy.modulefinder.BuildSource(path=None, module="test_module", text=code)],
        options=options,
    )

    state = result.graph["test_module"]
    tree = state.tree
    if tree is None:
        raise ValueError(f"Unable to infer types. Errors: {state.early_errors}")
    return state.type_checker(), TypeLookup(tree.names)


def test_signature_items_signature_test_body(fn_def: str) -> None:
    type_checker, fn_types = parse_types(fn_def)
    fn_type = fn_types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(type_checker, fn_type)

    assert is_same_type(test_signature.items_signature, fn_type)


test_signature_items_signature_test_body.__test__ = False  # type: ignore


def test_test_signature_items_signature_no_names() -> None:
    test_signature_items_signature_test_body(
        """
        def test_case() -> None:
            ...
        """
    )


def test_test_signature_items_signature_one_name() -> None:
    test_signature_items_signature_test_body(
        """
        def test_case(x: int) -> None:
            ...
        """
    )


def test_test_signature_items_signature_multiple_names() -> None:
    test_signature_items_signature_test_body(
        """
        def test_case(x: int, y: float, z: str) -> None:
            ...
        """
    )


def test_signature_test_case_signature_test_body(fn_defs: str) -> None:
    type_checker, fn_types = parse_types(fn_defs)
    fn_type = fn_types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(type_checker, fn_type)

    expected_type = fn_types["expected"]
    assert expected_type is not None
    assert is_same_type(test_signature.test_case_signature, expected_type)


test_signature_test_case_signature_test_body.__test__ = False  # type: ignore


def test_test_signature_test_case_signature_no_names() -> None:
    test_signature_test_case_signature_test_body(
        """
        def test_case() -> None:
            ...

        def expected(x: tuple[()], /) -> None:
            ...
        """
    )


def test_test_signature_test_case_signature_one_name() -> None:
    test_signature_test_case_signature_test_body(
        """
        def test_case(x: float) -> None:
            ...

        def expected(x: tuple[float], /) -> None:
            ...
        """
    )


def test_test_signature_test_case_signature_multiple_names() -> None:
    test_signature_test_case_signature_test_body(
        """
        def test_case(x: float, z: bool, t: list) -> None:
            ...

        def expected(x: tuple[float, bool, list], /) -> None:
            ...
        """
    )
