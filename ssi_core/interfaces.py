from abc import ABC, abstractmethod
from typing import Tuple
from .models import ClaimNode


class BaseConstraint(ABC):
    constraint_id: str

    @abstractmethod
    def check(self, claim: ClaimNode) -> Tuple[bool, str]:
        """Returns (passed, reason)."""


class BaseValidator(ABC):
    validator_id: str

    @abstractmethod
    def validate(self, claim: ClaimNode) -> Tuple[bool, str]:
        """Runs deterministic or empirical validation. Returns (passed, proof_summary)."""
