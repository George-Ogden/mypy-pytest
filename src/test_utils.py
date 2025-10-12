from typing import cast

from mypy.checker import TypeChecker
from mypy.types import CallableType

from .test_signature import TestSignature


def _test_signature_from_fn_type(checker: TypeChecker, fn_type: CallableType) -> TestSignature:
    assert all(name is not None for name in fn_type.arg_names)
    return TestSignature(
        checker=checker,
        arg_names=tuple(cast(list[str], fn_type.arg_names)),
        arg_types=tuple(fn_type.arg_types),
    )
