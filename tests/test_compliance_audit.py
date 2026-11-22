from ssi_core import ClaimLedger, ClaimNode, CustodyState
from adapters.compliance_audit.validators import (
    ComplianceThresholdValidator,
    RegulatoryStatuteConstraint,
)


def test_compliance_audit_lifecycle_and_statute_revision():
    ledger = ClaimLedger()
    ledger.register_constraint(RegulatoryStatuteConstraint())
    ledger.register_validator(ComplianceThresholdValidator())

    # 1. Active regulatory baseline reaches Q4
    statute = ClaimNode(
        claim_id="REG-101",
        statement="ISO-14971 thermal leakage limit is 0.5 mA.",
        metadata={
            "statute_id": "ISO-14971-SEC4",
            "jurisdiction": "US-FDA",
            "measured_value": 0.5,
            "max_allowed_value": 0.5,
        },
    )
    ledger.submit_proposal(statute)
    ledger.evaluate_constraints("REG-101")
    ledger.link_sources("REG-101", ["FDA-Guidance-2025.pdf"])
    ledger.run_validator("REG-101", "V-REG-THRESHOLD-CHECK")
    assert statute.custody_state == CustodyState.Q4_VALIDATED

    # 2. Device test claim depends on REG-101 and gets Q5 release clearance
    device_cert = ClaimNode(
        claim_id="CERT-404",
        statement="Batch B4 thermal leakage (0.32 mA) passes release threshold.",
        hard_premises=["REG-101"],
        metadata={
            "statute_id": "ISO-14971-SEC4",
            "jurisdiction": "US-FDA",
            "measured_value": 0.32,
            "max_allowed_value": 0.5,
        },
    )
    ledger.submit_proposal(device_cert)
    ledger.evaluate_constraints("CERT-404")
    ledger.link_sources("CERT-404", ["LabBench-Trace-991"])
    ledger.run_validator("CERT-404", "V-REG-THRESHOLD-CHECK")
    ledger.authorize_action("CERT-404", human_approver="QA Director")
    assert device_cert.custody_state == CustodyState.Q5_ACTION_QUALIFIED

    # 3. Regulator tightens standard -> CERT-404 immediately loses Q5 clearance
    affected = ledger.revoke_and_rollback("REG-101", reason="Superseded by stricter 0.25 mA limit.")
    assert affected == ["CERT-404"]
    assert device_cert.custody_state == CustodyState.Q1_TAINTED
