from typing import Tuple
from ssi_core.interfaces import BaseConstraint, BaseValidator
from ssi_core.models import ClaimNode


class PrimarySourceChainConstraint(BaseConstraint):
    constraint_id = "K-OSINT-SOURCE-01"

    def check(self, claim: ClaimNode) -> Tuple[bool, str]:
        if claim.metadata.get("anonymous_single_source", False):
            return False, "Unverified anonymous single-source leak cannot enter main ledger directly."
        if not claim.metadata.get("evidence_type"):
            return False, "OSINT claim must declare an 'evidence_type' (e.g., satellite, hash_log, filing)."
        return True, f"Evidence type '{claim.metadata['evidence_type']}' permitted."


class TelemetryCorroborationValidator(BaseValidator):
    validator_id = "V-OSINT-TELEMETRY"

    def validate(self, claim: ClaimNode) -> Tuple[bool, str]:
        independent_signals = claim.metadata.get("independent_signals", 0)
        timestamp_match = claim.metadata.get("timestamp_match", False)
        if independent_signals < 2:
            return False, f"Insufficient corroboration: {independent_signals} signal(s) found (minimum 2 required)."
        if not timestamp_match:
            return False, "Telemetry mismatch: artifact timestamps do not align."
        return True, f"Corroborated across {independent_signals} independent signals with aligned timestamps."
