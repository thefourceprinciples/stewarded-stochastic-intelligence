import pytest
from ssi_core.ledger import ClaimLedger
from ssi_core.models import ClaimNode, CustodyState
from adapters.sci_workbench.validators import (
    ConservationOfEnergyConstraint,
    SymPyIdentityValidator,
)


def setup_sci_ledger() -> ClaimLedger:
    ledger = ClaimLedger()
    ledger.register_constraint(ConservationOfEnergyConstraint())
    ledger.register_validator(SymPyIdentityValidator())
    return ledger


def test_full_promotion_and_cascade_rollback():
    ledger = setup_sci_ledger()

    # 1. Foundational claim C-01 climbs Q0 -> Q4
    c1 = ClaimNode(
        claim_id="C-01",
        statement="Kinetic energy expansion identity holds for non-relativistic regime.",
        metadata={"lhs": "(m * v**2) / 2", "rhs": "0.5 * m * v**2"},
    )
    ledger.submit_proposal(c1)
    ledger.evaluate_constraints("C-01")
    ledger.link_sources("C-01", ["arXiv:2401.0001"])
    ledger.run_validator("C-01", "V-SYMPY-ALGEBRA")
    assert c1.custody_state == CustodyState.Q4_VALIDATED

    # 2. Downstream claim C-02 depends on C-01 and reaches Q5 Action Clearance
    c2 = ClaimNode(
        claim_id="C-02",
        statement="Work-energy theorem corollary for thruster calibration.",
        hard_premises=["C-01"],
        metadata={"lhs": "m*a*d", "rhs": "m*d*a"},
    )
    ledger.submit_proposal(c2)
    ledger.evaluate_constraints("C-02")
    ledger.link_sources("C-02", ["LabLog-88"])
    ledger.run_validator("C-02", "V-SYMPY-ALGEBRA")
    ledger.authorize_action("C-02", human_approver="Dr. Vance")
    assert c2.custody_state == CustodyState.Q5_ACTION_QUALIFIED

    # 3. Revoke C-01 -> C-02 must automatically lose Q5 and drop to Q1_TAINTED
    affected = ledger.revoke_and_rollback("C-01", reason="Experimental calibration flaw found.")
    assert "C-02" in affected
    assert c2.custody_state == CustodyState.Q1_TAINTED


def test_quarantine_branch_isolation_and_merge():
    ledger = setup_sci_ledger()

    # Anomaly hypothesis violates K-PHYS-ENERGY-01, but has an empirical anomaly signal
    anomaly = ClaimNode(
        claim_id="C-99",
        statement="Effective cavity vacuum resonance exhibits apparent local energy surplus.",
        metadata={
            "violates_energy_conservation": True,
            "lhs": "(E_in + delta_vac) - E_in",
            "rhs": "delta_vac",
        },
    )
    ledger.submit_proposal(anomaly)
    ledger.evaluate_constraints("C-99", anomaly_signal=True)

    # Routed to shadow quarantine branch, NOT revoked
    assert anomaly.branch == "quarantine/c-99"
    assert anomaly.custody_state == CustodyState.Q_QUARANTINE

    # Can validate mathematically inside quarantine, but CANNOT authorize Q5 action
    ledger.run_validator("C-99", "V-SYMPY-ALGEBRA")
    with pytest.raises(PermissionError):
        ledger.authorize_action("C-99", human_approver="Dr. Vance")

    # Explicit Human Governance merge promotes to main Q4
    ledger.merge_quarantine("C-99", human_approver="Dr. Vance")
    assert anomaly.branch == "main"
    assert anomaly.custody_state == CustodyState.Q4_VALIDATED
