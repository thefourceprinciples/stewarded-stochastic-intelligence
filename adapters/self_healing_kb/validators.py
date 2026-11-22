from typing import Tuple
from ssi_core.interfaces import BaseConstraint, BaseValidator
from ssi_core.models import ClaimNode


class DocGovernanceConstraint(BaseConstraint):
    constraint_id = "K-KB-OWNER-01"

    def check(self, claim: ClaimNode) -> Tuple[bool, str]:
        if not claim.metadata.get("owner"):
            return False, "Knowledge base node must declare an 'owner' team or maintainer."
        return True, f"Owned by {claim.metadata['owner']}."


class SchemaAnchorValidator(BaseValidator):
    validator_id = "V-KB-SCHEMA-CHECK"

    def validate(self, claim: ClaimNode) -> Tuple[bool, str]:
        expected_version = claim.metadata.get("expected_schema_version")
        actual_version = claim.metadata.get("actual_schema_version")
        if not expected_version or not actual_version:
            return False, "Missing 'expected_schema_version' or 'actual_schema_version' in metadata."
        if expected_version != actual_version:
            return False, f"Schema drift detected: doc targets {expected_version}, live spec is {actual_version}."
        return True, f"Verified alignment with schema {actual_version}."
