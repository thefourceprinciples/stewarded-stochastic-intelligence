import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List
from ssi_core.ledger import ClaimLedger
from ssi_core.models import ClaimNode


ATOM_NS = {"atom": "http://w3.org"}


def search_arxiv(query: str, max_results: int = 3) -> List[Dict[str, str]]:
    """Queries the public arXiv API and returns structured primary source records."""
    encoded_query = urllib.parse.quote(query)
    url = f"http://arxiv.org:{encoded_query}&start=0&max_results={max_results}"

    req = urllib.request.Request(url, headers={"User-Agent": "SSI-SciWorkbench/0.3"})
    with urllib.request.urlopen(req, timeout=10) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    results: List[Dict[str, str]] = []

    for entry in root.findall("atom:entry", ATOM_NS):
        paper_id = (entry.findtext("atom:id", default="", namespaces=ATOM_NS) or "").strip()
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").split())
        published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        authors = [
            (author.findtext("atom:name", default="", namespaces=ATOM_NS) or "").strip()
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        results.append(
            {
                "source_id": paper_id,
                "title": title,
                "published": published,
                "authors": ", ".join(authors),
            }
        )

    return results


def link_arxiv_evidence(ledger: ClaimLedger, claim_id: str, query: str, max_results: int = 2) -> ClaimNode:
    """Fetches arXiv papers for a query and promotes a Q1 claim to Q2 with full metadata."""
    papers = search_arxiv(query, max_results=max_results)
    if not papers:
        raise LookupError(f"No arXiv sources found for query: '{query}'")

    source_refs = [f"{p['source_id']} ({p['title']})" for p in papers]
    claim = ledger.link_sources(claim_id, source_refs)
    claim.metadata.setdefault("retrieved_papers", []).extend(papers)
    return claim
