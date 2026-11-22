from collections import deque
from typing import Dict, List, Optional, Set
from .interfaces import BaseConstraint, BaseValidator
from .models import ClaimNode, CustodyState


class ClaimLedger:
    def __init__(self) -> None:
        self.nodes: Dict[str, ClaimNode] = {}
        self.constraints: Dict[str, BaseConstraint] = {}
        self.validators: Dict[str, BaseValidator] = {}

    def register_constraint(self, constraint: BaseConstraint) -> None:
        self.constraints[constraint.constraint_id] = constraint

    def register_validator(self, validator: BaseValidator) -> None:
        self.validators[validator.validator_id] = validator

    def submit_proposal(self, claim: ClaimNode, actor: str = "G-generator") -> ClaimNode:
        if claim.claim_id in self.nodes:
            raise ValueError(f"Claim ID {claim.claim_id} already exists in ledger.")
        claim.custody_state = CustodyState.Q0_PROPOSAL
        claim.record_event("PROPOSAL_SUBMITTED", actor, {"branch": claim.branch})
        self.nodes[claim.claim_id] = claim
        return claim

    def evaluate_constraints(self, claim_id: str, anomaly_signal: bool = False) -> ClaimNode:
        claim = self._get(claim_id)
        failed_constraints: List[str] = []

        for cid, constraint in self.constraints.items():
            if cid in claim.suspended_constraints:
                continue
            passed, reason = constraint.check(claim)
            if not passed:
                failed_constraints.append(f"{cid}: {reason}")

        if not failed_constraints:
            claim.custody_state = CustodyState.Q1_ADMISSIBLE
            claim.record_event("PROMOTED_Q1", "K-registry", {"status": "all_constraints_passed"})
        elif anomaly_signal:
            # Route coherent paradigm-shifting anomalies to an isolated quarantine branch
            claim.branch = f"quarantine/{claim.claim_id.lower()}"
            claim.custody_state = CustodyState.Q_QUARANTINE
            claim.suspended_constraints = [f.split(":")[0] for f in failed_constraints]
            claim.record_event(
                "ROUTED_TO_QUARANTINE",
                "K-registry",
                {"branch": claim.branch, "violated": failed_constraints},
            )
        else:
            claim.custody_state = CustodyState.Q_REVOKED
            claim.record_event("REJECTED_BY_K", "K-registry", {"violations": failed_constraints})

        return claim

    def link_sources(self, claim_id: str, sources: List[str]) -> ClaimNode:
        claim = self._get(claim_id)
        if not sources:
            raise ValueError("Cannot promote to Q2 without at least one source.")
        claim.sources.extend(sources)
        if claim.custody_state == CustodyState.Q1_ADMISSIBLE:
            claim.custody_state = CustodyState.Q2_SOURCE_LINKED
        claim.record_event("SOURCES_LINKED", "R-retriever", {"sources": sources})
        return claim

    def run_validator(self, claim_id: str, validator_id: str) -> ClaimNode:
        claim = self._get(claim_id)
        validator = self.validators[validator_id]

        # Ensure hard premises are still valid before allowing Q4 validation
        for premise_id in claim.hard_premises:
            premise = self._get(premise_id)
            if premise.custody_state in {
                CustodyState.Q_REVOKED,
                CustodyState.Q1_TAINTED,
                CustodyState.Q_QUARANTINE,
            }:
                raise RuntimeError(
                    f"Cannot validate {claim_id}: hard premise {premise_id} is in {premise.custody_state}."
                )

        passed, proof = validator.validate(claim)
        if passed:
            claim.validator_proofs.append({"validator": validator_id, "proof": proof})
            if claim.branch == "main":
                claim.custody_state = CustodyState.Q4_VALIDATED
            claim.record_event("VALIDATED_Q4", validator_id, {"proof": proof, "branch": claim.branch})
        else:
            claim.record_event("VALIDATION_FAILED", validator_id, {"reason": proof})
        return claim

    def authorize_action(self, claim_id: str, human_approver: str) -> ClaimNode:
        claim = self._get(claim_id)
        if claim.branch != "main":
            raise PermissionError("Quarantined claims are strictly blocked from Q5 Action clearance.")
        if claim.custody_state != CustodyState.Q4_VALIDATED:
            raise PermissionError(f"Claim must be Q4_VALIDATED before Q5 clearance (current: {claim.custody_state}).")

        claim.custody_state = CustodyState.Q5_ACTION_QUALIFIED
        claim.record_event("ACTION_AUTHORIZED_Q5", human_approver, {"gate": "A-gate"})
        return claim

    def revoke_and_rollback(self, root_claim_id: str, reason: str, actor: str = "H-governance") -> List[str]:
        """Revokes a root node and propagates epistemic demotion down the dependency DAG."""
        root = self._get(root_claim_id)
        root.custody_state = CustodyState.Q_REVOKED
        root.record_event("CLAIM_REVOKED", actor, {"reason": reason})

        affected: List[str] = []
        queue = deque([root_claim_id])
        visited: Set[str] = {root_claim_id}

        while queue:
            current_id = queue.popleft()
            for node in self.nodes.values():
                if node.claim_id in visited:
                    continue
                if current_id in node.hard_premises:
                    node.custody_state = CustodyState.Q1_TAINTED
                    node.record_event(
                        "DEPENDENCY_ROLLBACK_TAINTED",
                        "L-dag-engine",
                        {"revoked_premise": current_id, "root_cause": root_claim_id},
                    )
                    affected.append(node.claim_id)
                    visited.add(node.claim_id)
                    queue.append(node.claim_id)
                elif current_id in node.soft_context:
                    if node.custody_state not in {CustodyState.Q1_TAINTED, CustodyState.Q_REVOKED}:
                        node.custody_state = CustodyState.Q_REVIEW_REQUIRED
                        node.record_event(
                            "SOFT_CONTEXT_FLAGGED",
                            "L-dag-engine",
                            {"revoked_context": current_id},
                        )
                        affected.append(node.claim_id)

        return affected

    def merge_quarantine(self, claim_id: str, human_approver: str, retired_claim_ids: Optional[List[str]] = None) -> ClaimNode:
        """Promotes a validated quarantine hypothesis into main with explicit Human Governance sign-off."""
        claim = self._get(claim_id)
        if not claim.branch.startswith("quarantine/"):
            raise ValueError("Claim is not on a quarantine branch.")
        if not claim.validator_proofs:
            raise PermissionError("Quarantine claim must pass V validation before merging to main.")

        if retired_claim_ids:
            for old_id in retired_claim_ids:
                self.revoke_and_rollback(old_id, reason=f"Superseded by paradigm merge {claim_id}", actor=human_approver)

        claim.branch = "main"
        claim.custody_state = CustodyState.Q4_VALIDATED
        claim.record_event(
            "QUARANTINE_MERGED_TO_MAIN",
            human_approver,
            {"suspended_constraints_accepted": claim.suspended_constraints},
        )
        return claim

    def _get(self, claim_id: str) -> ClaimNode:
        if claim_id not in self.nodes:
            raise KeyError(f"Unknown claim_id: {claim_id}")
        return self.nodes[claim_id]
