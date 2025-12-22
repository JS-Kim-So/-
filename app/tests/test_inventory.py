from __future__ import annotations

import datetime as dt
import importlib

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from app import db as db_module

    importlib.reload(db_module)

    from app import models as models_module

    importlib.reload(models_module)

    from app import services as services_module

    importlib.reload(services_module)

    from app.api import routes as routes_module

    importlib.reload(routes_module)

    from app import main as main_module

    importlib.reload(main_module)

    db_module.Base.metadata.create_all(bind=db_module.engine)

    with TestClient(main_module.app) as test_client:
        yield test_client


@pytest.fixture()
def master_data(client: TestClient):
    group = client.post("/product-groups", json={"group_name": "Food"}).json()
    product = client.post(
        "/products",
        json={
            "group_id": group["group_id"],
            "product_code": "P001",
            "product_name": "Apple",
            "spec": "Spec",
        },
    ).json()
    lot = client.post(
        "/lots",
        json={
            "product_id": product["product_id"],
            "mfg_date": dt.date.today().isoformat(),
            "lot_no": "L001",
        },
    ).json()
    return {"group": group, "product": product, "lot": lot}


def _get_balance(client: TestClient) -> int:
    response = client.get("/inventory/balance")
    assert response.status_code == 200
    return response.json()[0]["qty_on_hand"]


def test_inventory_flow(client: TestClient, master_data):
    product_id = master_data["product"]["product_id"]
    lot_id = master_data["lot"]["lot_id"]

    inbound = client.post(
        "/inventory/in",
        json={"product_id": product_id, "lot_id": lot_id, "qty": 10, "ref_doc": "IN-1"},
    )
    assert inbound.status_code == 201
    inbound_tx_id = inbound.json()["tx_id"]

    assert _get_balance(client) == 10

    outbound = client.post(
        "/inventory/out",
        json={"product_id": product_id, "lot_id": lot_id, "qty": 3, "ref_doc": "OUT-1"},
    )
    assert outbound.status_code == 201
    assert _get_balance(client) == 7

    shortage = client.post(
        "/inventory/out",
        json={"product_id": product_id, "lot_id": lot_id, "qty": 20, "ref_doc": "OUT-2"},
    )
    assert shortage.status_code == 409

    confirm = client.post(
        "/inventory/out",
        json={
            "product_id": product_id,
            "lot_id": lot_id,
            "qty": 20,
            "ref_doc": "OUT-2",
            "confirm_shortage": True,
        },
    )
    assert confirm.status_code == 201
    assert _get_balance(client) == -13

    update = client.put(
        f"/inventory/transactions/{inbound_tx_id}",
        json={"qty": 8, "reason": "Fix quantity"},
    )
    assert update.status_code == 200
    assert _get_balance(client) == -15

    audit_logs = client.get(
        "/audit-logs",
        params={"entity_type": "inventory_tx", "entity_id": str(inbound_tx_id)},
    )
    assert audit_logs.status_code == 200
    assert any(log["action"] == "UPDATE" for log in audit_logs.json())

    from app import db as db_module

    with pytest.raises(Exception):
        with db_module.engine.begin() as conn:
            conn.execute(sa.text("DELETE FROM inventory_tx WHERE tx_id = :tx_id"), {"tx_id": inbound_tx_id})

    client.put(f"/lots/{lot_id}", json={"is_active": False})
    inactive = client.post(
        "/inventory/in",
        json={"product_id": product_id, "lot_id": lot_id, "qty": 1},
    )
    assert inactive.status_code == 400
