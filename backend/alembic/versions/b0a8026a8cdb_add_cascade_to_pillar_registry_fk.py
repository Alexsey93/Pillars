"""add cascade to pillar registry fk

Revision ID: <b0a8026a8cdb>
Revises: 7bd9c1a908a2
Create Date: ...

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b0a8026a8cdb"
down_revision: Union[str, Sequence[str], None] = "7bd9c1a908a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NAME = "pillar_registry_id_fkey"


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(FK_NAME, "pillar", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        "pillar",
        "registry",
        ["registry_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(FK_NAME, "pillar", type_="foreignkey")
    op.create_foreign_key(
        FK_NAME,
        "pillar",
        "registry",
        ["registry_id"],
        ["id"],
    )
