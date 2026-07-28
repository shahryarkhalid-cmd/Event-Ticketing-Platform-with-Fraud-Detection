"""add missing columns to order table

Revision ID: 31abc87424bc
Revises: 3420a1972d97
Create Date: 2026-07-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "31abc87424bc"
down_revision: Union[str, Sequence[str], None] = "3420a1972d97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order",
        sa.Column("ticket_tier_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "order",
        sa.Column("quantity", sa.Integer(), nullable=True),
    )
    op.add_column(
        "order",
        sa.Column("qr_code", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )

    op.execute(
        """
        UPDATE "order"
        SET ticket_tier_id = (
            SELECT tickettier.id
            FROM tickettier
            WHERE tickettier.event_id = "order".event_id
            LIMIT 1
        )
        WHERE ticket_tier_id IS NULL
        """
    )
    op.execute(
        'UPDATE "order" SET quantity = 1 WHERE quantity IS NULL'
    )

    op.alter_column("order", "ticket_tier_id", nullable=False)
    op.alter_column("order", "quantity", nullable=False)
    op.create_foreign_key(
        "fk_order_ticket_tier",
        "order",
        "tickettier",
        ["ticket_tier_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_order_ticket_tier", "order", type_="foreignkey")
    op.drop_column("order", "qr_code")
    op.drop_column("order", "quantity")
    op.drop_column("order", "ticket_tier_id")
