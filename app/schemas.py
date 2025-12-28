from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, Field


class ProductGroupBase(BaseModel):
    group_name: str
    is_active: bool = True


class ProductGroupCreate(ProductGroupBase):
    pass


class ProductGroupUpdate(BaseModel):
    group_name: str | None = None
    is_active: bool | None = None


class ProductGroupOut(ProductGroupBase):
    group_id: int
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    group_id: int
    product_code: str
    product_name: str
    spec: str | None = None
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    group_id: int | None = None
    product_code: str | None = None
    product_name: str | None = None
    spec: str | None = None
    is_active: bool | None = None


class ProductOut(ProductBase):
    product_id: int
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


class LotBase(BaseModel):
    product_id: int
    mfg_date: dt.date
    lot_no: str
    is_active: bool = True


class LotCreate(LotBase):
    pass


class LotUpdate(BaseModel):
    product_id: int | None = None
    mfg_date: dt.date | None = None
    lot_no: str | None = None
    is_active: bool | None = None


class LotOut(LotBase):
    lot_id: int
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


class InventoryTxBase(BaseModel):
    product_id: int
    lot_id: int
    qty: int = Field(..., ge=1)
    ref_doc: str | None = None
    note: str | None = None


class InventoryInCreate(InventoryTxBase):
    pass


class InventoryOutCreate(InventoryTxBase):
    confirm_shortage: bool = False


class InventoryTxUpdate(BaseModel):
    lot_id: int | None = None
    qty: int | None = Field(default=None, ge=1)
    ref_doc: str | None = None
    note: str | None = None
    reason: str | None = None


class InventoryTxOut(BaseModel):
    tx_id: int
    tx_type: str
    tx_datetime: dt.datetime
    product_id: int
    lot_id: int
    qty: int
    ref_doc: str | None
    note: str | None
    created_at: dt.datetime
    updated_at: dt.datetime

    class Config:
        from_attributes = True


class BalanceOut(BaseModel):
    product_group: str
    product_code: str
    product_name: str
    mfg_date: dt.date
    lot_no: str
    qty_on_hand: int
    last_tx_datetime: dt.datetime | None


class AuditLogOut(BaseModel):
    audit_id: int
    entity_type: str
    entity_id: str
    action: str
    changed_fields: dict[str, Any]
    reason: str | None
    actor: str | None
    created_at: dt.datetime

    class Config:
        from_attributes = True
