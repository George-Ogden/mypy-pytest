import abc
from collections.abc import Callable
import functools
from typing import Any, TypeGuard, cast, overload

from mypy.checker import TypeChecker
from mypy.errorcodes import NAME_DEFINED, ErrorCode
from mypy.nodes import Context, MypyFile, TypeInfo
from mypy.types import AnyType, Instance, Type, TypeOfAny

from .fullname import Fullname


class CheckerWrapper(abc.ABC):
    checker: TypeChecker

    @abc.abstractmethod
    def __init__(self) -> None: ...

    def fail(self, msg: str, *, context: Context, code: ErrorCode, file: None | str = None) -> None:
        self.checker.msg.fail(msg, context=context, code=code, file=file)

    def note(self, msg: str, *, context: Context, code: ErrorCode | None) -> None:
        self.checker.note(msg, context=context, code=code)

    @functools.lru_cache  # noqa: B019
    def named_type(self, fullname: Fullname) -> Instance:
        node = self.lookup_fullname(
            fullname,
            predicate=cast(
                Callable[[Any], TypeGuard[TypeInfo]], lambda node: isinstance(node, TypeInfo)
            ),
        )
        if node is None:
            raise KeyError()
        _module, type_info = node
        return Instance(
            type_info, [AnyType(TypeOfAny.from_omitted_generics)] * len(type_info.type_vars)
        )

    def lookup_fullname_type(
        self, fullname: Fullname, *, context: Context | None = None
    ) -> Type | None:
        result = self.lookup_fullname(
            fullname, context=context, predicate=lambda node: hasattr(node, "type")
        )
        if result is None:
            return None
        _module, node = result
        return node.type

    @overload
    def lookup_fullname[T](
        self,
        fullname: Fullname,
        *,
        context: Context | None = None,
        predicate: None | Callable[[Any], TypeGuard[T]] = None,
    ) -> tuple[MypyFile, T] | None: ...

    @overload
    def lookup_fullname(
        self,
        fullname: Fullname,
        *,
        context: Context | None = None,
        predicate: None | Callable[[Any], bool] = None,
    ) -> tuple[MypyFile, Any] | None: ...

    def lookup_fullname(
        self,
        fullname: Fullname,
        *,
        context: Context | None = None,
        predicate: None | Callable[[Any], bool] = None,
    ) -> tuple[MypyFile, Any] | None:
        module_name, target = (Fullname(()), fullname)
        while target:
            module_name = module_name.push_back(target.head)
            target = target.pop_front()
            if (module := self.checker.modules.get(str(module_name))) and (
                result := self._lookup_fullname_in_module(module, target, predicate=predicate)
            ):
                return module, result
        if context is not None:
            self.fail(f"'{fullname!s}' does not exist.", context=context, code=NAME_DEFINED)
        return None

    @overload
    def _lookup_fullname_in_module[T](
        self, module: MypyFile, target: Fullname, *, predicate: Callable[[Any], TypeGuard[T]]
    ) -> T | None: ...
    @overload
    def _lookup_fullname_in_module(
        self, module: MypyFile, target: Fullname, *, predicate: None | Callable[[Any], bool]
    ) -> Any | None: ...
    def _lookup_fullname_in_module(
        self, module: MypyFile, target: Fullname, *, predicate: None | Callable[[Any], bool]
    ) -> Any | None:
        resource: Any = module
        for name in target:
            try:
                resource = resource.names[name].node
            except (KeyError, AttributeError):
                return None
        if predicate is None or predicate(resource):
            return resource
        return None
