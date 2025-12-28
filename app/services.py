from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import models


def assert_group_active(db: Session, group_id: int) -> models.ProductGroup:
    group = db.get(models.ProductGroup, group_id)
    if not group:
        raise ValueError("Product group not found")
    if not group.is_active:
        raise ValueError("Product group is inactive")
    return group


def assert_product_active(db: Session, product_id: int) -> models.Product:
    product = db.get(models.Product, product_id)
    if not product:
        raise ValueError("Product not found")
    if not product.is_active:
        raise ValueError("Product is inactive")
    return product


def assert_lot_active(db: Session, lot_id: int) -> models.Lot:
    lot = db.get(models.Lot, lot_id)
    if not lot:
        raise ValueError("Lot not found")
    if not lot.is_active:
        raise ValueError("Lot is inactive")
    product = db.get(models.Product, lot.product_id)
    if not product or not product.is_active:
        raise ValueError("Product is inactive")
    group = db.get(models.ProductGroup, product.group_id)
    if not group or not group.is_active:
        raise ValueError("Product group is inactive")
    return lot


def get_balance_qty(db: Session, product_id: int, lot_id: int) -> int:
    balance = db.get(models.InventoryBalance, {"product_id": product_id, "lot_id": lot_id})
    return balance.qty_on_hand if balance else 0


def recalc_balance_for_lot(db: Session, product_id: int, lot_id: int) -> int:
    in_qty = db.execute(
        select(func.coalesce(func.sum(models.InventoryTx.qty), 0))
        .where(models.InventoryTx.product_id == product_id)
        .where(models.InventoryTx.lot_id == lot_id)
        .where(models.InventoryTx.tx_type == models.TxType.IN.value)
    ).scalar_one()
    out_qty = db.execute(
        select(func.coalesce(func.sum(models.InventoryTx.qty), 0))
        .where(models.InventoryTx.product_id == product_id)
        .where(models.InventoryTx.lot_id == lot_id)
        .where(models.InventoryTx.tx_type == models.TxType.OUT.value)
    ).scalar_one()
    qty_on_hand = int(in_qty) - int(out_qty)
    balance = db.get(models.InventoryBalance, {"product_id": product_id, "lot_id": lot_id})
    if balance:
        balance.qty_on_hand = qty_on_hand
    else:
        balance = models.InventoryBalance(product_id=product_id, lot_id=lot_id, qty_on_hand=qty_on_hand)
        db.add(balance)
    return qty_on_hand


def create_audit_log(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    changed_fields: dict,
    reason: str | None = None,
    actor: str | None = None,
) -> None:
    db.add(
        models.AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changed_fields=changed_fields,
            reason=reason,
            actor=actor,
            created_at=dt.datetime.utcnow(),
        )
    )
