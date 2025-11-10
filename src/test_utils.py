from collections.abc import Callable, Mapping
from dataclasses import dataclass
import functools
import re
import textwrap
from typing import Any, Literal, cast, overload

import mypy.build
from mypy.checker import TypeChecker
import mypy.modulefinder
from mypy.nodes import AssignmentStmt, Decorator, Expression, FuncDef, NameExpr
import mypy.options
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

    @overload
    def get(self, name: str, default: None = None) -> Type | None: ...
    @overload
    def get[T](self, name: str, default: T) -> Type | T: ...

    def get(self, name: str, default: Any = None) -> Type | Any:
        try:
            return self[name]
        except KeyError:
            return default


@dataclass(frozen=True, kw_only=True)
class ParseResult:
    checker: TypeChecker
    types: TypeLookup
    defs: Mapping[str, Expression | FuncDef | Decorator]


@functools.lru_cache(maxsize=1)
def parse(code: str) -> ParseResult:
    code = textwrap.dedent(code).strip()

    options = mypy.options.Options()
    options.incremental = False
    options.show_traceback = True
    options.preserve_asts = True

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

    defs: dict[str, Expression | FuncDef | Decorator] = {}
    for def_ in tree.defs:
        if isinstance(def_, AssignmentStmt):
            for name in def_.lvalues:
                if isinstance(name, NameExpr):
                    defs[name.name] = def_.rvalue
        elif isinstance(def_, FuncDef):
            defs[def_.name] = def_
        elif isinstance(def_, Decorator):
            defs[def_.name] = def_

    return ParseResult(checker=type_checker, types=TypeLookup(tree.names), defs=defs)


def get_error_messages(checker: TypeChecker) -> str:
    return "\n".join(checker.errors.new_messages())


def check_error_messages(messages: str, *, errors: list[str] | None) -> None:
    if errors:
        error_codes = [match for match in re.findall(r"\[([a-z\-]*)\]$", messages, re.MULTILINE)]
        assert error_codes == errors, messages
    else:
        assert not errors


def test_signature_from_fn_type(
    checker: TypeChecker, fn_name: str, fn_type: CallableType
) -> TestSignature:
    assert all(name is not None for name in fn_type.arg_names)
    arg_names = cast(list[str], fn_type.arg_names)
    if any(name.endswith("_1") for name in arg_names):
        [arg_name] = arg_names
        arg_name = arg_name[:-2]
        [arg_type] = fn_type.arg_types
        return OneItemTestSignature(
            checker=checker, fn_name=fn_name, arg_name=arg_name, arg_type=arg_type
        )
    else:
        return ManyItemsTestSignature(
            checker=checker,
            fn_name=fn_name,
            arg_names=arg_names,
            arg_types=fn_type.arg_types,
        )


test_signature_from_fn_type.__test__ = False  # type: ignore


def get_signature_and_vals(
    defs: str,
) -> tuple[TestSignature, Expression]:
    parse_result = parse(defs)
    fn_type = parse_result.types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(
        parse_result.checker, fn_name="test_case", fn_type=fn_type
    )

    vals = parse_result.defs["vals"]
    assert isinstance(vals, Expression)
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
    parse_result = parse(fn_defs)
    fn_type = parse_result.types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(
        parse_result.checker, fn_name="test_case", fn_type=fn_type
    )

    expected_key = "expected" if extra_expected else "test_case"
    expected_type = parse_result.types[expected_key]
    assert expected_type is not None
    type_ = getattr(test_signature, attr)
    assert is_same_type(type_, expected_type)


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
    messages = get_error_messages(checker)

    assert type_check_result == passes, messages


test_signature_custom_check_test_body.__test__ = False  # type: ignore


def default_test_info(checker: TypeChecker) -> TestInfo:
    test_info = TestInfo(checker=checker, arguments={}, decorators=[], fn_name="test_info")
    return test_info


def test_info_from_defs(defs: str, *, name: str) -> TestInfo:
    parse_result = parse(defs)
    test_node = parse_result.defs[name]
    assert isinstance(test_node, FuncDef | Decorator)
    test_info = TestInfo.from_fn_def(test_node, checker=parse_result.checker)
    assert test_info is not None
    return test_info


test_info_from_defs.__test__ = False  # type: ignore
