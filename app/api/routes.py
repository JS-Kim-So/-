from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas, services
from app.db import get_db

router = APIRouter()


def _handle_value_error(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _transaction_context(db: Session):
    return db.begin_nested() if db.in_transaction() else db.begin()


@router.get("/dashboard/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    product_count = db.scalar(select(func.count(models.Product.product_id))) or 0
    lot_count = db.scalar(select(func.count(models.Lot.lot_id))) or 0
    total_qty = db.scalar(select(func.coalesce(func.sum(models.InventoryBalance.qty_on_hand), 0))) or 0
    return schemas.DashboardSummary(product_count=product_count, lot_count=lot_count, total_qty=total_qty)

@router.post("/product-groups", response_model=schemas.ProductGroupOut, status_code=status.HTTP_201_CREATED)
def create_product_group(payload: schemas.ProductGroupCreate, db: Session = Depends(get_db)):
    group = models.ProductGroup(**payload.model_dump())
    db.add(group)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate product group") from exc
    db.refresh(group)
    return group


@router.get("/product-groups", response_model=list[schemas.ProductGroupOut])
def list_product_groups(
    is_active: bool | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.ProductGroup)
    if is_active is not None:
        stmt = stmt.where(models.ProductGroup.is_active == is_active)
    if q:
        stmt = stmt.where(models.ProductGroup.group_name.ilike(f"%{q}%"))
    return db.execute(stmt.order_by(models.ProductGroup.group_name)).scalars().all()


@router.put("/product-groups/{group_id}", response_model=schemas.ProductGroupOut)
def update_product_group(group_id: int, payload: schemas.ProductGroupUpdate, db: Session = Depends(get_db)):
    group = db.get(models.ProductGroup, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Product group not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate product group") from exc
    db.refresh(group)
    return group


@router.post("/products", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    try:
        services.assert_group_active(db, payload.group_id)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc
    product = models.Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate product code") from exc
    db.refresh(product)
    return product


@router.get("/products", response_model=list[schemas.ProductOut])
def list_products(
    group_id: int | None = None,
    product_code: str | None = None,
    is_active: bool | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.Product)
    if group_id:
        stmt = stmt.where(models.Product.group_id == group_id)
    if product_code:
        stmt = stmt.where(models.Product.product_code.ilike(f"%{product_code}%"))
    if is_active is not None:
        stmt = stmt.where(models.Product.is_active == is_active)
    if q:
        stmt = stmt.where(models.Product.product_name.ilike(f"%{q}%"))
    return db.execute(stmt.order_by(models.Product.product_code)).scalars().all()


@router.put("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = payload.model_dump(exclude_unset=True)
    if "group_id" in update_data:
        try:
            services.assert_group_active(db, update_data["group_id"])
        except ValueError as exc:
            raise _handle_value_error(exc) from exc
    for key, value in update_data.items():
        setattr(product, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate product code") from exc
    db.refresh(product)
    return product


@router.post("/lots", response_model=schemas.LotOut, status_code=status.HTTP_201_CREATED)
def create_lot(payload: schemas.LotCreate, db: Session = Depends(get_db)):
    try:
        services.assert_product_active(db, payload.product_id)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc
    lot = models.Lot(**payload.model_dump())
    db.add(lot)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate lot key") from exc
    db.refresh(lot)
    return lot


@router.get("/lots", response_model=list[schemas.LotOut])
def list_lots(
    product_id: int | None = None,
    mfg_date_from: dt.date | None = None,
    mfg_date_to: dt.date | None = None,
    lot_no: str | None = None,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.Lot)
    if product_id:
        stmt = stmt.where(models.Lot.product_id == product_id)
    if mfg_date_from:
        stmt = stmt.where(models.Lot.mfg_date >= mfg_date_from)
    if mfg_date_to:
        stmt = stmt.where(models.Lot.mfg_date <= mfg_date_to)
    if lot_no:
        stmt = stmt.where(models.Lot.lot_no.ilike(f"%{lot_no}%"))
    if is_active is not None:
        stmt = stmt.where(models.Lot.is_active == is_active)
    return db.execute(stmt.order_by(models.Lot.mfg_date.desc())).scalars().all()


@router.put("/lots/{lot_id}", response_model=schemas.LotOut)
def update_lot(lot_id: int, payload: schemas.LotUpdate, db: Session = Depends(get_db)):
    lot = db.get(models.Lot, lot_id)
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    update_data = payload.model_dump(exclude_unset=True)
    if "product_id" in update_data:
        try:
            services.assert_product_active(db, update_data["product_id"])
        except ValueError as exc:
            raise _handle_value_error(exc) from exc
    for key, value in update_data.items():
        setattr(lot, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate lot key") from exc
    db.refresh(lot)
    return lot


@router.post("/inventory/in", response_model=schemas.InventoryTxOut, status_code=status.HTTP_201_CREATED)
def create_inbound(payload: schemas.InventoryInCreate, db: Session = Depends(get_db)):
    try:
        lot = services.assert_lot_active(db, payload.lot_id)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc
    if lot.product_id != payload.product_id:
        raise HTTPException(status_code=400, detail="Lot does not match product")
    with _transaction_context(db):
        tx = models.InventoryTx(
            tx_type=models.TxType.IN.value,
            tx_datetime=dt.datetime.utcnow(),
            product_id=payload.product_id,
            lot_id=payload.lot_id,
            qty=payload.qty,
            ref_doc=payload.ref_doc,
            note=payload.note,
        )
        db.add(tx)
        db.flush()
        balance = db.get(models.InventoryBalance, {"product_id": payload.product_id, "lot_id": payload.lot_id})
        if balance:
            balance.qty_on_hand += payload.qty
        else:
            balance = models.InventoryBalance(
                product_id=payload.product_id,
                lot_id=payload.lot_id,
                qty_on_hand=payload.qty,
            )
            db.add(balance)
        services.create_audit_log(
            db,
            entity_type="inventory_tx",
            entity_id=str(tx.tx_id),
            action="CREATE",
            changed_fields={"after": payload.model_dump()},
        )
    db.refresh(tx)
    return tx


@router.post("/inventory/out", response_model=schemas.InventoryTxOut, status_code=status.HTTP_201_CREATED)
def create_outbound(payload: schemas.InventoryOutCreate, db: Session = Depends(get_db)):
    try:
        lot = services.assert_lot_active(db, payload.lot_id)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc
    if lot.product_id != payload.product_id:
        raise HTTPException(status_code=400, detail="Lot does not match product")
    current_qty = services.get_balance_qty(db, payload.product_id, payload.lot_id)
    if current_qty - payload.qty < 0 and not payload.confirm_shortage:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Insufficient stock", "current_qty": current_qty, "requires_confirm": True},
        )
    with _transaction_context(db):
        tx = models.InventoryTx(
            tx_type=models.TxType.OUT.value,
            tx_datetime=dt.datetime.utcnow(),
            product_id=payload.product_id,
            lot_id=payload.lot_id,
            qty=payload.qty,
            ref_doc=payload.ref_doc,
            note=payload.note,
        )
        db.add(tx)
        db.flush()
        balance = db.get(models.InventoryBalance, {"product_id": payload.product_id, "lot_id": payload.lot_id})
        if balance:
            balance.qty_on_hand -= payload.qty
        else:
            balance = models.InventoryBalance(
                product_id=payload.product_id,
                lot_id=payload.lot_id,
                qty_on_hand=-payload.qty,
            )
            db.add(balance)
        services.create_audit_log(
            db,
            entity_type="inventory_tx",
            entity_id=str(tx.tx_id),
            action="CREATE",
            changed_fields={"after": payload.model_dump()},
        )
    db.refresh(tx)
    return tx


@router.get("/inventory/transactions", response_model=list[schemas.InventoryTxOut])
def list_transactions(
    start_datetime: dt.datetime | None = None,
    end_datetime: dt.datetime | None = None,
    product_code: str | None = None,
    lot_id: int | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(models.InventoryTx)
    if start_datetime:
        stmt = stmt.where(models.InventoryTx.tx_datetime >= start_datetime)
    if end_datetime:
        stmt = stmt.where(models.InventoryTx.tx_datetime <= end_datetime)
    if lot_id:
        stmt = stmt.where(models.InventoryTx.lot_id == lot_id)
    if product_code:
        stmt = stmt.join(models.Product, models.InventoryTx.product_id == models.Product.product_id).where(
            models.Product.product_code.ilike(f"%{product_code}%")
        )
    return db.execute(stmt.order_by(models.InventoryTx.tx_datetime.desc())).scalars().all()


@router.put("/inventory/transactions/{tx_id}", response_model=schemas.InventoryTxOut)
def update_transaction(tx_id: int, payload: schemas.InventoryTxUpdate, db: Session = Depends(get_db)):
    tx = db.get(models.InventoryTx, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    update_data = payload.model_dump(exclude_unset=True)
    lot_id = update_data.get("lot_id", tx.lot_id)
    try:
        lot = services.assert_lot_active(db, lot_id)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc
    if lot.product_id != tx.product_id:
        raise HTTPException(status_code=400, detail="Lot does not match product")

    before = {
        "lot_id": tx.lot_id,
        "qty": tx.qty,
        "ref_doc": tx.ref_doc,
        "note": tx.note,
    }

    with _transaction_context(db):
        for key, value in update_data.items():
            if key == "reason":
                continue
            setattr(tx, key, value)
        db.flush()
        affected_lots = {before["lot_id"], tx.lot_id}
        for affected_lot in affected_lots:
            services.recalc_balance_for_lot(db, tx.product_id, affected_lot)
        after = {
            "lot_id": tx.lot_id,
            "qty": tx.qty,
            "ref_doc": tx.ref_doc,
            "note": tx.note,
        }
        services.create_audit_log(
            db,
            entity_type="inventory_tx",
            entity_id=str(tx.tx_id),
            action="UPDATE",
            changed_fields={"before": before, "after": after},
            reason=payload.reason,
        )
    db.refresh(tx)
    return tx


@router.get("/inventory/balance", response_model=list[schemas.BalanceOut])
def list_balance(
    group_id: int | None = None,
    product_code: str | None = None,
    mfg_date_from: dt.date | None = None,
    mfg_date_to: dt.date | None = None,
    lot_no: str | None = None,
    db: Session = Depends(get_db),
):
    last_tx_subq = (
        select(models.InventoryTx.lot_id, func.max(models.InventoryTx.tx_datetime).label("last_tx"))
        .group_by(models.InventoryTx.lot_id)
        .subquery()
    )

    stmt = (
        select(
            models.ProductGroup.group_name,
            models.Product.product_code,
            models.Product.product_name,
            models.Lot.mfg_date,
            models.Lot.lot_no,
            models.InventoryBalance.qty_on_hand,
            last_tx_subq.c.last_tx,
        )
        .select_from(models.InventoryBalance)
        .join(models.Product, models.InventoryBalance.product_id == models.Product.product_id)
        .join(models.ProductGroup, models.Product.group_id == models.ProductGroup.group_id)
        .join(models.Lot, models.InventoryBalance.lot_id == models.Lot.lot_id)
        .outerjoin(last_tx_subq, last_tx_subq.c.lot_id == models.InventoryBalance.lot_id)
    )

    filters = []
    if group_id:
        filters.append(models.Product.group_id == group_id)
    if product_code:
        filters.append(models.Product.product_code.ilike(f"%{product_code}%"))
    if mfg_date_from:
        filters.append(models.Lot.mfg_date >= mfg_date_from)
    if mfg_date_to:
        filters.append(models.Lot.mfg_date <= mfg_date_to)
    if lot_no:
        filters.append(models.Lot.lot_no.ilike(f"%{lot_no}%"))
    if filters:
        stmt = stmt.where(and_(*filters))

    rows = db.execute(stmt.order_by(models.Product.product_code)).all()
    return [
        schemas.BalanceOut(
            product_group=row.group_name,
            product_code=row.product_code,
            product_name=row.product_name,
            mfg_date=row.mfg_date,
            lot_no=row.lot_no,
            qty_on_hand=row.qty_on_hand,
            last_tx_datetime=row.last_tx,
        )
        for row in rows
    ]


@router.get("/audit-logs", response_model=list[schemas.AuditLogOut])
def list_audit_logs(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(models.AuditLog)
    if entity_type:
        stmt = stmt.where(models.AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(models.AuditLog.entity_id == entity_id)
    return db.execute(stmt.order_by(models.AuditLog.created_at.desc())).scalars().all()
