"""Contract-file lineage tests (A37): every figure resolves.

No model calls: the solicitation builder re-checks stored output in
code. Doc lineage must name files that exist in the repo.
"""

from fastapi.testclient import TestClient

from app.config import REPO_ROOT, Settings
from app.lineage import build_contract_file
from app.main import app
from app.order_store import reset

client = TestClient(app)

EXPECTED_SECTIONS = [
    "requirements",
    "quotes",
    "cost_bid",
    "award",
    "order",
    "events",
    "cash",
]

SPOT_VALUES = {
    "CLIN 0001 quantity": "58 EA",
    "Quoted total": "82070.00",
    "Landed cost": "82070.00",
    "Lowest safe bid": "91189.92",
    "Margin at safe bid": "10.00",
    "Deposit due with PO": "41035.00",
    "Award total": "91880.12",
    "Offers received": "26",
    "Bid price": "91189.92",
    "Cash exposure": "82070.00",
}


def load_file() -> object:
    """The linked picture for the demo order from a reset."""
    reset()
    return build_contract_file("ORD-001", Settings())


def test_sections_arrive_in_chain_order() -> None:
    """Solicitation to cash, every section present."""
    contract_file = load_file()
    assert contract_file.order_id == "ORD-001"
    assert contract_file.solicitation_id == "1232SA26Q0557"
    assert [section.name for section in contract_file.sections] == EXPECTED_SECTIONS


def test_every_figure_resolves() -> None:
    """Doc figures name real files; calc figures name code with inputs."""
    contract_file = load_file()
    count = 0
    for section in contract_file.sections:
        for figure in section.figures:
            count += 1
            assert figure.value, figure.label
            lineage = figure.lineage
            if lineage.kind == "doc":
                assert lineage.file, figure.label
                assert (REPO_ROOT / lineage.file).is_file(), lineage.file
            else:
                assert lineage.calculation, figure.label
                assert lineage.inputs, figure.label
    assert count >= 20, count


def test_spot_values_match_the_demo() -> None:
    """Key figures equal the stored records and the cost engine."""
    contract_file = load_file()
    values = {
        figure.label: figure.value
        for section in contract_file.sections
        for figure in section.figures
    }
    for label, expected in SPOT_VALUES.items():
        assert values[label] == expected, label


def test_unknown_order_404s() -> None:
    """The router translates an unknown order to 404."""
    response = client.get("/orders/ORD-999/contract-file")
    assert response.status_code == 404


def test_endpoint_serves_the_chain() -> None:
    """GET serves the same resolved picture the builder returns."""
    reset()
    response = client.get("/orders/ORD-001/contract-file")
    assert response.status_code == 200
    body = response.json()
    assert [section["name"] for section in body["sections"]] == EXPECTED_SECTIONS
