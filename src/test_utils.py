from collections.abc import Callable, Mapping
from dataclasses import dataclass
import textwrap
from typing import Any, Literal, cast

import mypy.build
from mypy.checker import TypeChecker
from mypy.errors import Errors
import mypy.modulefinder
import mypy.nodes
from mypy.nodes import Expression
import mypy.options
import mypy.parse
from mypy.subtypes import is_same_type
from mypy.types import CallableType, Type

from .many_items_test_signature import ManyItemsTestSignature
from .one_item_test_signature import OneItemTestSignature
from .test_info import TestInfo
from .test_signature import TestSignature


@dataclass(frozen=True)
class TypeLookup:
    _names: Mapping[str, mypy.nodes.SymbolTableNode]

    def __getitem__(self, name: str) -> Type | None:
        return self._names[name].type


def parse_types(code: str) -> tuple[TypeChecker, TypeLookup]:
    code = textwrap.dedent(code).strip()

    options = mypy.options.Options()
    options.incremental = False
    options.show_traceback = True

    result = mypy.build.build(
        sources=[mypy.modulefinder.BuildSource(path=None, module="test_module", text=code)],
        options=options,
    )

    state = result.graph["test_module"]
    tree = state.tree
    if tree is None:
        raise ValueError(f"Unable to infer types. Errors: {state.early_errors}")

    type_checker = state.type_checker()
    errors = type_checker.errors
    if errors.is_errors():
        for info in errors.error_info_map.values():
            for err in info:
                print(f"{err.file}:{err.line}: {err.message}")
        raise TypeError()
    return type_checker, TypeLookup(tree.names)


def parse_defs(code: str) -> Mapping[str, mypy.nodes.Expression]:
    code = textwrap.dedent(code).strip()

    options = mypy.options.Options()
    options.incremental = False
    options.show_traceback = True
    errors = Errors(options)

    tree = mypy.parse.parse(
        code,
        fnam="test_module.py",
        module="test_module",
        errors=errors,
        options=options,
        raise_on_error=True,
    )

    node_mapping: dict[str, mypy.nodes.Expression] = {}
    for def_ in tree.defs:
        if isinstance(def_, mypy.nodes.AssignmentStmt):
            for name in def_.lvalues:
                if isinstance(name, mypy.nodes.NameExpr):
                    node_mapping[name.name] = def_.rvalue

    return node_mapping


def test_signature_from_fn_type(
    checker: TypeChecker, fn_name: str, fn_type: CallableType
) -> TestSignature:
    assert all(name is not None for name in fn_type.arg_names)
    arg_names = tuple(cast(list[str], fn_type.arg_names))
    if any(name.endswith("1") for name in arg_names):
        [arg_name] = arg_names
        [arg_type] = fn_type.arg_types
        return OneItemTestSignature(
            checker=checker, fn_name=fn_name, arg_name=arg_name, arg_type=arg_type
        )
    else:
        return ManyItemsTestSignature(
            checker=checker,
            fn_name=fn_name,
            arg_names=arg_names,
            arg_types=tuple(fn_type.arg_types),
        )


test_signature_from_fn_type.__test__ = False  # type: ignore


def get_signature_and_vals(
    defs: str,
) -> tuple[TestSignature, Expression]:
    type_checker, fn_types = parse_types(defs)
    fn_type = fn_types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(type_checker, fn_name="test_case", fn_type=fn_type)

    nodes = parse_defs(defs)
    vals = nodes["vals"]
    return test_signature, vals


def type_checks(body: Callable[[], Any], checker: TypeChecker) -> bool:
    assert not checker.errors.is_errors()
    body()
    return not checker.errors.is_errors()


def test_signature_custom_signature_test_body(
    fn_defs: str,
    *,
    attr: Literal["items_signature", "test_case_signature", "sequence_signature"],
    extra_expected: bool,
) -> None:
    type_checker, fn_types = parse_types(fn_defs)
    fn_type = fn_types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(type_checker, fn_name="test_case", fn_type=fn_type)

    expected_key = "expected" if extra_expected else "test_case"
    expected_type = fn_types[expected_key]
    assert expected_type is not None
    assert is_same_type(getattr(test_signature, attr), expected_type)


test_signature_custom_signature_test_body.__test__ = False  # type: ignore


def test_signature_custom_check_test_body[
    T: TestSignature,
    U: Expression,
](
    defs: str,
    passes: bool,
    body: Callable[[T, U], None],
    *,
    bound: type[U] = Expression,  # type: ignore
) -> None:
    test_signature, val = get_signature_and_vals(defs)
    assert isinstance(val, bound)

    checker = test_signature.checker
    type_check_result = type_checks(
        lambda: body(cast(T, test_signature), val),
        checker=checker,
    )
    new_messages = "\n".join(checker.errors.new_messages())

    assert type_check_result == passes, new_messages


test_signature_custom_check_test_body.__test__ = False  # type: ignore


def default_test_info() -> TestInfo:
    type_checker, _ = parse_types("")
    test_info = TestInfo(checker=type_checker)
    return test_info
