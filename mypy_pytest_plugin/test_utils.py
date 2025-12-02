from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import functools
import os
import re
import textwrap
from typing import Any, Literal, cast, overload

from debug import pprint
import mypy.build
from mypy.build import State
from mypy.checker import TypeChecker
import mypy.modulefinder
from mypy.nodes import (
    AssignmentStmt,
    Decorator,
    Expression,
    FuncDef,
    MemberExpr,
    MypyFile,
    NameExpr,
    Statement,
)
import mypy.options
from mypy.subtypes import is_same_type
from mypy.types import CallableType, Type

from .argnames_parser import ArgnamesParser
from .fixture import Fixture
from .fixture_manager import FixtureManager
from .many_items_test_signature import ManyItemsTestSignature
from .one_item_test_signature import OneItemTestSignature
from .test_info import TestInfo
from .test_signature import TestSignature
from .types_module import TYPES_MODULE


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
class _ParseResultBase:
    graph: dict[str, State]
    defs: Mapping[str, Expression | FuncDef | Decorator]
    raw_defs: list[Statement]

    def checker_accept_all(self, checker: TypeChecker) -> None:
        for def_ in self.raw_defs:
            checker.accept(def_)
        assert not checker.errors.is_errors(), get_error_messages(checker)


@dataclass(frozen=True, kw_only=True)
class ParseResult(_ParseResultBase):
    types: TypeLookup
    checker: TypeChecker

    def accept_all(self) -> None:
        self.checker_accept_all(self.checker)


@dataclass(frozen=True, kw_only=True)
class MultiParseResult(_ParseResultBase):
    checkers: dict[str, TypeChecker] = field(default_factory=dict)
    types: dict[str, TypeLookup] = field(default_factory=dict)
    defs: dict[str, Expression | FuncDef | Decorator] = field(default_factory=dict)
    raw_defs: list[Statement] = field(default_factory=list)

    def single(self, module_name: str) -> ParseResult:
        return ParseResult(
            graph=self.graph,
            checker=self.checkers[module_name],
            types=self.types[module_name],
            defs=self.defs,
            raw_defs=self.raw_defs,
        )


def parse_multiple(modules: Sequence[tuple[str, str]], *, header: str = "") -> MultiParseResult:
    modules = [
        (
            module_name,
            f"{header + '\n'}{textwrap.dedent(code)}".strip(),
        )
        for module_name, code in modules
    ]

    options = mypy.options.Options()
    options.show_traceback = True
    options.incremental = True
    options.show_traceback = True
    options.preserve_asts = True
    options.disallow_untyped_defs = False
    options.disallow_untyped_decorators = False
    options.namespace_packages = False
    options.ignore_missing_imports = True
    options.no_site_packages = True
    options.mypy_path = []
    options.cache_dir = os.devnull

    result = mypy.build.build(
        sources=[
            mypy.modulefinder.BuildSource(path=None, module=module_name, text=code)
            for module_name, code in modules
        ],
        options=options,
    )

    module_names = [module_name for module_name, _ in modules]

    parse_result = MultiParseResult(graph=result.graph)
    for module_name in module_names:
        state = result.graph[module_name]
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
                for lvalue in def_.lvalues:
                    if isinstance(lvalue, NameExpr):
                        defs[lvalue.name] = def_.rvalue
                    elif isinstance(lvalue, MemberExpr) and isinstance(lvalue.expr, NameExpr):
                        defs[f"{lvalue.expr.name}.{lvalue.name}"] = def_.rvalue

            elif isinstance(def_, FuncDef | Decorator):
                defs[def_.name] = def_

        parse_result.checkers[module_name] = type_checker
        parse_result.raw_defs.extend(tree.defs)
        parse_result.types[module_name] = TypeLookup(tree.names)
        parse_result.defs.update({f"{module_name}.{name}": def_ for name, def_ in defs.items()})
        if len(module_names) == 1:
            parse_result.defs.update(defs)
    return parse_result


@functools.lru_cache(maxsize=1)
def parse(code: str, *, header: str = "", module_name: str = "test_module") -> ParseResult:
    parse_result = parse_multiple([(module_name, code)], header=header)
    return parse_result.single(module_name)


def get_error_messages(checker: TypeChecker) -> str:
    return "\n".join(checker.errors.new_messages())


def check_error_messages(messages: str, *, errors: list[str] | None) -> None:
    if errors:
        error_codes = [match for match in re.findall(r"\[([a-z\-]*)\]$", messages, re.MULTILINE)]
        assert error_codes == errors, messages
    else:
        assert not messages, messages


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
            checker=checker,
            fn_name=fn_name,
            arg_name=arg_name,
            arg_type=arg_type,
            type_variables=fn_type.variables,
        )
    return ManyItemsTestSignature(
        checker=checker,
        fn_name=fn_name,
        arg_names=arg_names,
        arg_types=fn_type.arg_types,
        type_variables=fn_type.variables,
    )


test_signature_from_fn_type.__test__ = False  # type: ignore


def get_signature_and_vals(
    defs: str,
) -> tuple[TestSignature, Expression]:
    parse_result = parse(defs, header=f"import {TYPES_MODULE}")
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
    parse_result = parse(fn_defs, header=f"import {TYPES_MODULE}")
    fn_type = parse_result.types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(
        parse_result.checker, fn_name="test_case", fn_type=fn_type
    )

    expected_key = "expected" if extra_expected else "test_case"
    expected_type = parse_result.types[expected_key]
    assert expected_type is not None
    type_ = getattr(test_signature, attr)
    pprint((type_, expected_type))
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
    bound: type[U] = Expression,  # type: ignore  # noqa: PT028
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


def default_argnames_parser(checker: TypeChecker) -> ArgnamesParser:
    return ArgnamesParser(checker)


def test_info_from_defs(defs: str, *, name: str) -> TestInfo:
    parse_result = parse(defs)
    parse_result.accept_all()
    test_node = parse_result.defs[name]
    assert isinstance(test_node, FuncDef | Decorator)
    test_info = TestInfo.from_fn_def(test_node, checker=parse_result.checker)
    assert test_info is not None
    return test_info


test_info_from_defs.__test__ = False  # type: ignore


def simple_module_lookup(
    self: FixtureManager, module: MypyFile, request_name: str
) -> Fixture | None:
    decorator = module.names.get(request_name)
    if decorator is not None and isinstance(decorator.node, Decorator):
        return Fixture.from_decorator(decorator.node, self.checker)
    return None


@overload
def dump_expr(expr: Expression) -> tuple[type[Expression], dict[str, Any]]: ...
@overload
def dump_expr(expr: None) -> tuple[type[None], None]: ...


def dump_expr(expr: Expression | None) -> tuple[type, dict[str, Any] | None]:
    return (
        type(expr),
        None if expr is None else {attr: getattr(expr, attr) for attr in expr.__match_args__},  # type: ignore [attr-defined]
    )
