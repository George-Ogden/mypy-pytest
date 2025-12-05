from dataclasses import dataclass
import enum


class DeferralReason(enum.IntEnum):
    # cannot compute value until another node has been processed
    REQUIRED_WAIT = enum.auto()
    # requires other nodes in the file to be processed to ensure correctness
    SPECULATIVE_WAIT = enum.auto()


@dataclass(eq=False)
class DeferralError(Exception):
    cause: DeferralReason
