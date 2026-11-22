import json
from pathlib import Path
from typing import Union
from .ledger import ClaimLedger
from .models import ClaimNode, CustodyState, LedgerEvent


def save_ledger(ledger: ClaimLedger, filepath: Union[str, Path]) -> None:
    """Serializes the ClaimLedger DAG and full event history to a JSON file."""
    payload = {
        "nodes": {
            cid: {
                "claim_id": node.claim_id,
                "statement": node.statement,
                "branch": node.branch,
                "custody_state": node.custody_state.value,
                "hard_premises": node.hard_premises,
                "soft_context": node.soft_context,
                "sources": node.sources,
                "validator_proofs": node.validator_proofs,
                "suspended_constraints": node.suspended_constraints,
                "metadata": node.metadata,
                "history": [
                    {
                        "timestamp": ev.timestamp,
                        "event_type": ev.event_type,
                        "actor": ev.actor,
                        "details": ev.details,
                    }
                    for ev in node.history
                ],
            }
            for cid, node in ledger.nodes.items()
        }
    }
    Path(filepath).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_ledger(filepath: Union[str, Path], ledger: ClaimLedger | None = None) -> ClaimLedger:
    """Loads a saved JSON ledger into a new or existing ClaimLedger instance."""
    target = ledger if ledger is not None else ClaimLedger()
    raw = json.loads(Path(filepath).read_text(encoding="utf-8"))

    for cid, data in raw.get("nodes", {}).items():
        node = ClaimNode(
            claim_id=data["claim_id"],
            statement=data["statement"],
            branch=data["branch"],
            custody_state=CustodyState(data["custody_state"]),
            hard_premises=data.get("hard_premises", []),
            soft_context=data.get("soft_context", []),
            sources=data.get("sources", []),
            validator_proofs=data.get("validator_proofs", []),
            suspended_constraints=data.get("suspended_constraints", []),
            metadata=data.get("metadata", {}),
            history=[
                LedgerEvent(
                    timestamp=ev["timestamp"],
                    event_type=ev["event_type"],
                    actor=ev["actor"],
                    details=ev["details"],
                )
                for ev in data.get("history", [])
            ],
        )
        target.nodes[cid] = node

    return target
