from collections.abc import Mapping
from dataclasses import dataclass
import textwrap
from typing import cast

import mypy.build
from mypy.checker import TypeChecker
from mypy.errors import Errors
import mypy.modulefinder
import mypy.nodes
import mypy.options
import mypy.parse
from mypy.types import CallableType, Type

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
    errors = type_checker.msg.errors
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
    return TestSignature(
        checker=checker,
        fn_name=fn_name,
        arg_names=tuple(cast(list[str], fn_type.arg_names)),
        arg_types=tuple(fn_type.arg_types),
    )


test_signature_from_fn_type.__test__ = False  # type: ignore
