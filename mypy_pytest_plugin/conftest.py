from .test_body_ranges import TestBodyRanges
from .test_case import TestCase
from .test_info import TestInfo
from .test_signature import TestSignature

TestSignature.__test__ = False  # type: ignore[attr-defined]
TestCase.__test__ = False  # type: ignore[attr-defined]
TestInfo.__test__ = False  # type: ignore[attr-defined]
TestBodyRanges.__test__ = False  # type: ignore[attr-defined]
