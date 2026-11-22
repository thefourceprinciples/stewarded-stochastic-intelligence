from ssi_core import ClaimLedger, ClaimNode, CustodyState
from adapters.self_healing_kb.validators import (
    DocGovernanceConstraint,
    SchemaAnchorValidator,
)


def test_self_healing_kb_cascades_spec_deprecation():
    ledger = ClaimLedger()
    ledger.register_constraint(DocGovernanceConstraint())
    ledger.register_validator(SchemaAnchorValidator())

    # 1. Core API Spec v1 reaches Q4
    spec = ClaimNode(
        claim_id="SPEC-01",
        statement="Authentication endpoint accepts legacy static API keys.",
        metadata={
            "owner": "platform-security",
            "expected_schema_version": "v1.0",
            "actual_schema_version": "v1.0",
        },
    )
    ledger.submit_proposal(spec)
    ledger.evaluate_constraints("SPEC-01")
    ledger.link_sources("SPEC-01", ["openapi-v1.yaml"])
    ledger.run_validator("SPEC-01", "V-KB-SCHEMA-CHECK")
    assert spec.custody_state == CustodyState.Q4_VALIDATED

    # 2. Support Bot Macro depends on SPEC-01 and is cleared for live Q5 responses
    macro = ClaimNode(
        claim_id="BOT-01",
        statement="Auto-reply instructing users to generate a static API key.",
        hard_premises=["SPEC-01"],
        metadata={
            "owner": "support-ops",
            "expected_schema_version": "v1.0",
            "actual_schema_version": "v1.0",
        },
    )
    ledger.submit_proposal(macro)
    ledger.evaluate_constraints("BOT-01")
    ledger.link_sources("BOT-01", ["helpcenter/auth-guide.md"])
    ledger.run_validator("BOT-01", "V-KB-SCHEMA-CHECK")
    ledger.authorize_action("BOT-01", human_approver="Lead Tech Writer")
    assert macro.custody_state == CustodyState.Q5_ACTION_QUALIFIED

    # 3. Security deprecates static API keys -> BOT-01 automatically loses Q5 clearance
    affected = ledger.revoke_and_rollback("SPEC-01", reason="Deprecated in favor of OAuth2 tokens.")
    assert affected == ["BOT-01"]
    assert macro.custody_state == CustodyState.Q1_TAINTED
