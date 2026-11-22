from ssi_core import ClaimLedger, ClaimNode
from adapters.sci_workbench.validators import (
    ConservationOfEnergyConstraint,
    SymPyIdentityValidator,
)


def print_status(ledger: ClaimLedger, title: str) -> None:
    print(f"\n=== {title} ===")
    for cid, node in ledger.nodes.items():
        print(f"  [{node.branch}] {cid}: {node.custody_state.value} | {node.statement}")


def main() -> None:
    ledger = ClaimLedger()
    ledger.register_constraint(ConservationOfEnergyConstraint())
    ledger.register_validator(SymPyIdentityValidator())

    # 1. Foundational claim C-01 climbs Q0 -> Q4
    c1 = ClaimNode(
        claim_id="C-01",
        statement="Non-relativistic kinetic energy identity holds.",
        metadata={"lhs": "(m * v**2) / 2", "rhs": "0.5 * m * v**2"},
    )
    ledger.submit_proposal(c1)
    ledger.evaluate_constraints("C-01")
    ledger.link_sources("C-01", ["arXiv:2401.0001"])
    ledger.run_validator("C-01", "V-SYMPY-ALGEBRA")

    # 2. Downstream claim C-02 depends on C-01 and reaches Q5
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
    print_status(ledger, "1. Initial Validated & Action-Qualified State")

    # 3. Trigger Blast-Radius Dependency Rollback
    affected = ledger.revoke_and_rollback("C-01", reason="Calibration flaw discovered.")
    print(f"\n[!] Revoked C-01 -> Cascade affected: {affected}")
    print_status(ledger, "2. After Blast-Radius Rollback")

    # 4. Quarantine Branching for Paradigm-Shifting Anomaly
    anomaly = ClaimNode(
        claim_id="C-99",
        statement="Cavity vacuum resonance exhibits apparent local energy surplus.",
        metadata={
            "violates_energy_conservation": True,
            "lhs": "(E_in + delta_vac) - E_in",
            "rhs": "delta_vac",
        },
    )
    ledger.submit_proposal(anomaly)
    ledger.evaluate_constraints("C-99", anomaly_signal=True)
    ledger.run_validator("C-99", "V-SYMPY-ALGEBRA")
    print_status(ledger, "3. Anomaly Isolated & Validated in Quarantine")

    # 5. Human Governance Merge
    ledger.merge_quarantine("C-99", human_approver="Dr. Vance")
    print_status(ledger, "4. After Human Governance Merge to Main")


if __name__ == "__main__":
    main()
