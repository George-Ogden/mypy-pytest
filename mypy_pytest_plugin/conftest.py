import pytest

from .logger import Logger
from .test_body_ranges import TestBodyRanges
from .test_case import TestCase
from .test_info import TestArgument, TestInfo
from .test_signature import TestSignature

TestSignature.__test__ = False  # type: ignore
TestCase.__test__ = False  # type: ignore
TestInfo.__test__ = False  # type: ignore
TestArgument.__test__ = False  # type: ignore
TestBodyRanges.__test__ = False  # type: ignore


@pytest.fixture(autouse=True)
def reset_logger_errors() -> None:
    Logger._errors = {}
