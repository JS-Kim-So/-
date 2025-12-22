from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_group",
        sa.Column("group_id", sa.Integer(), primary_key=True),
        sa.Column("group_name", sa.String(length=200), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "product",
        sa.Column("product_id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(length=100), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("spec", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["group_id"], ["product_group.group_id"]),
        sa.UniqueConstraint("product_code"),
    )
    op.create_index("ix_product_group_id", "product", ["group_id"])
    op.create_index("ix_product_code", "product", ["product_code"])

    op.create_table(
        "lot",
        sa.Column("lot_id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("mfg_date", sa.Date(), nullable=False),
        sa.Column("lot_no", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["product_id"], ["product.product_id"]),
        sa.UniqueConstraint("product_id", "mfg_date", "lot_no", name="uq_lot_key"),
    )
    op.create_index("ix_lot_product_id", "lot", ["product_id"])
    op.create_index("ix_lot_mfg_date", "lot", ["mfg_date"])

    op.create_table(
        "inventory_tx",
        sa.Column("tx_id", sa.Integer(), primary_key=True),
        sa.Column("tx_type", sa.String(length=3), nullable=False),
        sa.Column("tx_datetime", sa.DateTime(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("lot_id", sa.Integer(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("ref_doc", sa.String(length=200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("is_void", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.CheckConstraint("qty > 0", name="ck_inventory_tx_qty"),
        sa.ForeignKeyConstraint(["product_id"], ["product.product_id"]),
        sa.ForeignKeyConstraint(["lot_id"], ["lot.lot_id"]),
    )
    op.create_index("ix_inventory_tx_datetime", "inventory_tx", ["tx_datetime"])
    op.create_index("ix_inventory_tx_product", "inventory_tx", ["product_id"])
    op.create_index("ix_inventory_tx_lot", "inventory_tx", ["lot_id"])
    op.create_index("ix_inventory_tx_type", "inventory_tx", ["tx_type"])

    op.create_table(
        "inventory_balance",
        sa.Column("product_id", sa.Integer(), primary_key=True),
        sa.Column("lot_id", sa.Integer(), primary_key=True),
        sa.Column("qty_on_hand", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["product_id"], ["product.product_id"]),
        sa.ForeignKeyConstraint(["lot_id"], ["lot.lot_id"]),
    )
    op.create_index("ix_inventory_balance_product", "inventory_balance", ["product_id"])
    op.create_index("ix_inventory_balance_lot", "inventory_balance", ["lot_id"])

    op.create_table(
        "audit_log",
        sa.Column("audit_id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("changed_fields", sa.JSON(), nullable=False),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("actor", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    _create_delete_block_trigger()


def downgrade() -> None:
    _drop_delete_block_trigger()
    op.drop_table("audit_log")
    op.drop_index("ix_inventory_balance_lot", table_name="inventory_balance")
    op.drop_index("ix_inventory_balance_product", table_name="inventory_balance")
    op.drop_table("inventory_balance")
    op.drop_index("ix_inventory_tx_type", table_name="inventory_tx")
    op.drop_index("ix_inventory_tx_lot", table_name="inventory_tx")
    op.drop_index("ix_inventory_tx_product", table_name="inventory_tx")
    op.drop_index("ix_inventory_tx_datetime", table_name="inventory_tx")
    op.drop_table("inventory_tx")
    op.drop_index("ix_lot_mfg_date", table_name="lot")
    op.drop_index("ix_lot_product_id", table_name="lot")
    op.drop_table("lot")
    op.drop_index("ix_product_code", table_name="product")
    op.drop_index("ix_product_group_id", table_name="product")
    op.drop_table("product")
    op.drop_table("product_group")


def _create_delete_block_trigger() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute(
            """
            CREATE OR REPLACE FUNCTION prevent_inventory_tx_delete() RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'inventory_tx deletion is not allowed';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
        op.execute(
            """
            CREATE TRIGGER inventory_tx_no_delete
            BEFORE DELETE ON inventory_tx
            FOR EACH ROW
            EXECUTE FUNCTION prevent_inventory_tx_delete();
            """
        )
    elif dialect == "sqlite":
        op.execute(
            """
            CREATE TRIGGER inventory_tx_no_delete
            BEFORE DELETE ON inventory_tx
            BEGIN
                SELECT RAISE(ABORT, 'inventory_tx deletion is not allowed');
            END;
            """
        )


def _drop_delete_block_trigger() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS inventory_tx_no_delete ON inventory_tx;")
        op.execute("DROP FUNCTION IF EXISTS prevent_inventory_tx_delete();")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS inventory_tx_no_delete;")
