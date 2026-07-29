"""add role_selected flag to user, make role nullable

Revision ID: c7a1f4e9d2b3
Revises: 31abc87424bc, e84556ca1f2b
Create Date: 2026-07-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "c7a1f4e9d2b3"
down_revision: Union[str, Sequence[str], None] = "f76671a61214"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New flag: has this user completed the one-time role selection?
    op.add_column(
        "user",
        sa.Column("role_selected", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Existing accounts already had a role (default was "organizer") -
    # treat them as already having selected it so they aren't sent back
    # through the role-selection screen.
    op.execute('UPDATE "user" SET role_selected = TRUE WHERE role IS NOT NULL')

    # Role must now be nullable: a brand new signup has no role until
    # they pick one on the role-selection page.
    op.alter_column("user", "role", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.execute('UPDATE "user" SET role = \'organizer\' WHERE role IS NULL')
    op.alter_column("user", "role", existing_type=sa.String(), nullable=False)
    op.drop_column("user", "role_selected")
