"""add cascade to downloadtoken fks

Revision ID: 8327332772e7
Revises: 81ba0466dcb1
Create Date: ...

"""
from typing import Sequence, Union

from alembic import op

revision: str = "8327332772e7"
down_revision: Union[str, Sequence[str], None] = "81ba0466dcb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

REGISTRY_FK = "downloadtoken_registry_id_fkey"
USER_FK = "downloadtoken_user_id_fkey"


def upgrade() -> None:
    # registry_id -> registry.id, ON DELETE CASCADE
    op.drop_constraint(REGISTRY_FK, "downloadtoken", type_="foreignkey")
    op.create_foreign_key(
        REGISTRY_FK,
        "downloadtoken",
        "registry",
        ["registry_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # user_id -> user.id, ON DELETE CASCADE
    op.drop_constraint(USER_FK, "downloadtoken", type_="foreignkey")
    op.create_foreign_key(
        USER_FK,
        "downloadtoken",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(REGISTRY_FK, "downloadtoken", type_="foreignkey")
    op.create_foreign_key(
        REGISTRY_FK,
        "downloadtoken",
        "registry",
        ["registry_id"],
        ["id"],
    )

    op.drop_constraint(USER_FK, "downloadtoken", type_="foreignkey")
    op.create_foreign_key(
        USER_FK,
        "downloadtoken",
        "user",
        ["user_id"],
        ["id"],
    )