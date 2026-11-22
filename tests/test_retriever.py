import io
from unittest.mock import patch
from ssi_core import ClaimLedger, ClaimNode, CustodyState
from adapters.sci_workbench.retriever import link_arxiv_evidence
from adapters.sci_workbench.validators import ConservationOfEnergyConstraint


SAMPLE_ARXIV_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://w3.org">
  <entry>
    <id>arxiv:2401.12345v1</id>
    <published>2024-01-22T18:00:00Z</published>
    <title>Cavity Quantum Electrodynamics and Vacuum Fluctuations</title>
    <author><name>A. Researcher</name></author>
  </entry>
</feed>
"""


def test_arxiv_retriever_promotes_q1_to_q2():
    ledger = ClaimLedger()
    ledger.register_constraint(ConservationOfEnergyConstraint())

    claim = ClaimNode(
        claim_id="C-50",
        statement="Casimir cavity boundary conditions modify local mode density.",
    )
    ledger.submit_proposal(claim)
    ledger.evaluate_constraints("C-50")
    assert claim.custody_state == CustodyState.Q1_ADMISSIBLE

    mock_response = io.BytesIO(SAMPLE_ARXIV_XML)
    with patch("urllib.request.urlopen", return_value=mock_response):
        link_arxiv_evidence(ledger, "C-50", query="Casimir cavity mode density", max_results=1)

    assert claim.custody_state == CustodyState.Q2_SOURCE_LINKED
    first_source = next(iter(claim.sources))
    first_paper = next(iter(claim.metadata["retrieved_papers"]))
    assert "2401.12345v1" in first_source
    assert first_paper["authors"] == "A. Researcher"
