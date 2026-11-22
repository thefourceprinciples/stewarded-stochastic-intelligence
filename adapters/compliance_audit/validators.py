from typing import Tuple
from ssi_core.interfaces import BaseConstraint, BaseValidator
from ssi_core.models import ClaimNode


class RegulatoryStatuteConstraint(BaseConstraint):
    constraint_id = "K-REG-STATUTE-01"

    def check(self, claim: ClaimNode) -> Tuple[bool, str]:
        statute_id = claim.metadata.get("statute_id")
        jurisdiction = claim.metadata.get("jurisdiction")
        if not statute_id or not jurisdiction:
            return False, "Compliance claim must declare both 'statute_id' and 'jurisdiction'."
        return True, f"Bound to {statute_id} ({jurisdiction})."


class ComplianceThresholdValidator(BaseValidator):
    validator_id = "V-REG-THRESHOLD-CHECK"

    def validate(self, claim: ClaimNode) -> Tuple[bool, str]:
        measured = claim.metadata.get("measured_value")
        max_allowed = claim.metadata.get("max_allowed_value")
        if measured is None or max_allowed is None:
            return False, "Missing 'measured_value' or 'max_allowed_value' in audit metadata."
        if measured > max_allowed:
            return False, f"Audit failed: measured {measured} exceeds statutory limit {max_allowed}."
        return True, f"Compliant: measured {measured} <= limit {max_allowed}."
