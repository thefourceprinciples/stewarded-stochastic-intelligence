from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List


class CustodyState(str, Enum):
    Q0_PROPOSAL = "Q0"
    Q1_ADMISSIBLE = "Q1"
    Q2_SOURCE_LINKED = "Q2"
    Q3_CORROBORATED = "Q3"
    Q4_VALIDATED = "Q4"
    Q5_ACTION_QUALIFIED = "Q5"
    Q1_TAINTED = "Q1_TAINTED"
    Q_REVIEW_REQUIRED = "Q_REVIEW_REQUIRED"
    Q_QUARANTINE = "Q_QUARANTINE"
    Q_REVOKED = "Q_REVOKED"


@dataclass
class LedgerEvent:
    timestamp: str
    event_type: str
    actor: str
    details: Dict[str, Any]


@dataclass
class ClaimNode:
    claim_id: str
    statement: str
    branch: str = "main"
    custody_state: CustodyState = CustodyState.Q0_PROPOSAL
    hard_premises: List[str] = field(default_factory=list)
    soft_context: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    validator_proofs: List[Dict[str, Any]] = field(default_factory=list)
    suspended_constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    history: List[LedgerEvent] = field(default_factory=list)

    def record_event(self, event_type: str, actor: str, details: Dict[str, Any]) -> None:
        self.history.append(
            LedgerEvent(
                timestamp=datetime.now(timezone.utc).isoformat(),
                event_type=event_type,
                actor=actor,
                details=details,
            )
        )
