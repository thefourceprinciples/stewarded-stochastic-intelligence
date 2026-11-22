from ssi_core import ClaimLedger, ClaimNode, CustodyState
from adapters.osint_verify.validators import (
    PrimarySourceChainConstraint,
    TelemetryCorroborationValidator,
)


def test_osint_poison_pill_and_leak_quarantine():
    ledger = ClaimLedger()
    ledger.register_constraint(PrimarySourceChainConstraint())
    ledger.register_validator(TelemetryCorroborationValidator())

    # 1. Verified satellite/AIS telemetry claim reaches Q4
    intel = ClaimNode(
        claim_id="INTEL-01",
        statement="Vessel V-77 transited Strait X at 04:15 UTC.",
        metadata={
            "evidence_type": "satellite_ais",
            "independent_signals": 3,
            "timestamp_match": True,
        },
    )
    ledger.submit_proposal(intel)
    ledger.evaluate_constraints("INTEL-01")
    ledger.link_sources("INTEL-01", ["Sentinel2-Tile-88A", "AIS-Log-402"])
    ledger.run_validator("INTEL-01", "V-OSINT-TELEMETRY")
    assert intel.custody_state == CustodyState.Q4_VALIDATED

    # 2. Downstream publication brief reaches Q5 clearance
    brief = ClaimNode(
        claim_id="BRIEF-01",
        statement="Sanctions evasion route confirmed for Vessel V-77.",
        hard_premises=["INTEL-01"],
        metadata={
            "evidence_type": "analytical_synthesis",
            "independent_signals": 2,
            "timestamp_match": True,
        },
    )
    ledger.submit_proposal(brief)
    ledger.evaluate_constraints("BRIEF-01")
    ledger.link_sources("BRIEF-01", ["Editorial-Dossier-12"])
    ledger.run_validator("BRIEF-01", "V-OSINT-TELEMETRY")
    ledger.authorize_action("BRIEF-01", human_approver="Managing Editor")
    assert brief.custody_state == CustodyState.Q5_ACTION_QUALIFIED

    # 3. Spoofed AIS log discovered -> BRIEF-01 immediately loses publication clearance
    affected = ledger.revoke_and_rollback("INTEL-01", reason="AIS transponder spoofing detected.")
    assert affected == ["BRIEF-01"]
    assert brief.custody_state == CustodyState.Q1_TAINTED

    # 4. Anonymous leak enters Quarantine, gets corroborated, and merges cleanly
    leak = ClaimNode(
        claim_id="LEAK-99",
        statement="Port authority manifest alteration logged internally.",
        metadata={
            "anonymous_single_source": True,
            "evidence_type": "leaked_manifest",
            "independent_signals": 2,
            "timestamp_match": True,
        },
    )
    ledger.submit_proposal(leak)
    ledger.evaluate_constraints("LEAK-99", anomaly_signal=True)
    assert leak.branch == "quarantine/leak-99"
    assert leak.custody_state == CustodyState.Q_QUARANTINE

    ledger.run_validator("LEAK-99", "V-OSINT-TELEMETRY")
    ledger.merge_quarantine("LEAK-99", human_approver="Managing Editor")
    assert leak.branch == "main"
    assert leak.custody_state == CustodyState.Q4_VALIDATED
