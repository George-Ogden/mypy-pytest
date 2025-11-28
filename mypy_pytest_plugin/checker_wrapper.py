import abc
from typing import Any

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

    def note(self, msg: str, *, context: Context, code: ErrorCode) -> None:
        self.checker.note(msg, context=context, code=code)

    def _lookup_fullname_type(
        self, fullname: Fullname, *, context: Context, fail_on_error: bool = False
    ) -> Type | None:
        module_name, target = (
            Fullname(()),
            fullname,
        )
        while target:
            module_name = module_name.push_back(target.head)
            target = target.pop_front()
            if (module := self.checker.modules.get(str(module_name))) and (
                type_ := self._lookup_fullname_type_in_module(module, target)
            ):
                return type_
        if fail_on_error:
            self.fail(f"'{fullname!s}' does not exist.", context=context, code=NAME_DEFINED)
        return None

    def _lookup_fullname_type_in_module(self, module: MypyFile, target: Fullname) -> Type | None:
        resource: Any = module
        for name in target:
            try:
                resource = resource.names[name].node
            except KeyError:
                return None
        try:
            return resource.type
        except AttributeError:
            return None
