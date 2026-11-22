from pathlib import Path
from ssi_core import ClaimLedger, ClaimNode, CustodyState, load_ledger, save_ledger
from adapters.sci_workbench.validators import (
    ConservationOfEnergyConstraint,
    SymPyIdentityValidator,
)


def test_ledger_json_persistence_and_post_reload_rollback(tmp_path: Path):
    ledger_file = tmp_path / "test_ledger.json"

    # 1. Build and populate an initial ledger
    ledger = ClaimLedger()
    ledger.register_constraint(ConservationOfEnergyConstraint())
    ledger.register_validator(SymPyIdentityValidator())

    c1 = ClaimNode(
        claim_id="C-10",
        statement="Momentum conservation identity holds.",
        metadata={"lhs": "m*v1 + m*v2", "rhs": "m*(v1 + v2)"},
    )
    c2 = ClaimNode(
        claim_id="C-11",
        statement="Elastic collision corollary.",
        hard_premises=["C-10"],
        metadata={"lhs": "2*p", "rhs": "p + p"},
    )

    for claim in (c1, c2):
        ledger.submit_proposal(claim)
        ledger.evaluate_constraints(claim.claim_id)
        ledger.link_sources(claim.claim_id, ["arXiv:2401.9999"])
        ledger.run_validator(claim.claim_id, "V-SYMPY-ALGEBRA")

    ledger.authorize_action("C-11", human_approver="Dr. Vance")
    save_ledger(ledger, ledger_file)

    # 2. Reload into a brand-new ClaimLedger instance
    reloaded = ClaimLedger()
    reloaded.register_constraint(ConservationOfEnergyConstraint())
    reloaded.register_validator(SymPyIdentityValidator())
    load_ledger(ledger_file, reloaded)

    assert reloaded.nodes["C-11"].custody_state == CustodyState.Q5_ACTION_QUALIFIED
    assert len(reloaded.nodes["C-11"].history) == 5

    # 3. Verify that dependency rollbacks still work after reloading from disk
    affected = reloaded.revoke_and_rollback("C-10", reason="Retracted after audit.")
    assert affected == ["C-11"]
    assert reloaded.nodes["C-11"].custody_state == CustodyState.Q1_TAINTED
