from __future__ import annotations

from __future__ import annotations

import datetime as dt
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, event, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import DDL
from sqlalchemy.types import JSON

from app.db import Base

Base.registry.dispose()
Base.metadata.clear()


class ProductGroup(Base):
    __tablename__ = "product_group"

    group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    products: Mapped[list[Product]] = relationship(back_populates="group")


class Product(Base):
    __tablename__ = "product"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("product_group.group_id"), nullable=False, index=True)
    product_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    spec: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    group: Mapped[ProductGroup] = relationship(back_populates="products")
    lots: Mapped[list[Lot]] = relationship(back_populates="product")


class Lot(Base):
    __tablename__ = "lot"
    __table_args__ = (UniqueConstraint("product_id", "mfg_date", "lot_no", name="uq_lot_key"),)

    lot_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), nullable=False, index=True)
    mfg_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    lot_no: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    product: Mapped[Product] = relationship(back_populates="lots")
    balances: Mapped[list[InventoryBalance]] = relationship(back_populates="lot")


class TxType(str, Enum):
    IN = "IN"
    OUT = "OUT"


class InventoryTx(Base):
    __tablename__ = "inventory_tx"

    tx_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tx_type: Mapped[TxType] = mapped_column(String(3), nullable=False, index=True)
    tx_datetime: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), nullable=False, index=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lot.lot_id"), nullable=False, index=True)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    ref_doc: Mapped[str | None] = mapped_column(String(200))
    note: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    is_void: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    product: Mapped[Product] = relationship()
    lot: Mapped[Lot] = relationship()


inventory_tx_delete_block = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS inventory_tx_no_delete
    BEFORE DELETE ON inventory_tx
    BEGIN
        SELECT RAISE(FAIL, 'Deletion forbidden for inventory_tx');
    END;
    """
)
event.listen(InventoryTx.__table__, "after_create", inventory_tx_delete_block)


class InventoryBalance(Base):
    __tablename__ = "inventory_balance"

    product_id: Mapped[int] = mapped_column(ForeignKey("product.product_id"), primary_key=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("lot.lot_id"), primary_key=True)
    qty_on_hand: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    product: Mapped[Product] = relationship()
    lot: Mapped[Lot] = relationship(back_populates="balances")


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_fields: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200))
    actor: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
