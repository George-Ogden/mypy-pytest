import abc
from collections.abc import Callable
from typing import Any, TypeGuard, overload

from mypy.checker import TypeChecker
from mypy.errorcodes import NAME_DEFINED, ErrorCode
from mypy.nodes import Context, MypyFile
from mypy.types import Type

from .fullname import Fullname


class CheckerWrapper(abc.ABC):
    checker: TypeChecker

    @abc.abstractmethod
    def __init__(self) -> None: ...

    def fail(self, msg: str, *, context: Context, code: ErrorCode) -> None:
        self.checker.fail(msg, context=context, code=code)

    def note(self, msg: str, *, context: Context, code: ErrorCode | None) -> None:
        self.checker.note(msg, context=context, code=code)

    def lookup_fullname_type(
        self,
        fullname: Fullname,
        *,
        context: Context | None = None,
    ) -> Type | None:
        result = self.lookup_fullname(
            fullname, context=context, predicate=lambda node: hasattr(node, "type")
        )
        if result is None:
            return None
        return result.type

    @overload
    def lookup_fullname[T](
        self,
        fullname: Fullname,
        *,
        context: Context | None,
        predicate: None | Callable[[Any], TypeGuard[T]] = None,
    ) -> T | None: ...

    @overload
    def lookup_fullname(
        self,
        fullname: Fullname,
        *,
        context: Context | None,
        predicate: None | Callable[[Any], bool] = None,
    ) -> Any | None: ...

    def lookup_fullname(
        self,
        fullname: Fullname,
        *,
        context: Context | None,
        predicate: None | Callable[[Any], bool] = None,
    ) -> Any | None:
        module_name, target = (
            Fullname(()),
            fullname,
        )
        while target:
            module_name = module_name.push_back(target.head)
            target = target.pop_front()
            if (module := self.checker.modules.get(str(module_name))) and (
                result := self._lookup_fullname_in_module(module, target, predicate=predicate)
            ):
                return result
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
