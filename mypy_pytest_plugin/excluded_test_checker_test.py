from .excluded_test_checker import ExcludedTestChecker
from .test_utils import parse
from .types_module import TYPES_MODULE


def test_ignored_names() -> None:
    parse_result = parse(
        f"""
        from {TYPES_MODULE} import Testable
        from typing import Literal

        @Testable
        def test_1() -> None: ...

        @Testable
        def test_2() -> None: ...

        @Testable
        def test_3() -> None: ...

        @Testable
        def test_4() -> None: ...

        @Testable
        def test_5() -> None: ...

        @Testable
        def test_6() -> None: ...

        test_1.__test__ = False

        f: Literal[False] = False

        test_3.__test__ = f

        b: bool = False

        test_4.__test__ = b

        test_5.__test__ = test_6.__test__ = False
        """
    )

    parse_result.accept_all()
    ignored_tests = ExcludedTestChecker(parse_result.checker).ignored_test_names(
        parse_result.raw_defs
    )
    assert ignored_tests == {"test_1", "test_3", "test_5", "test_6"}
