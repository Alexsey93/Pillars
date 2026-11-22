"""change cnt fields to varchar

Revision ID: 81ba0466dcb1
Revises: b0a8026a8cdb
Create Date: ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "81ba0466dcb1"
down_revision: Union[str, Sequence[str], None] = "b0a8026a8cdb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CNT_FIELDS = [
    "cnt_fastening", "cnt_vok_not_ab", "cnt_mzhk_not_ab", "cnt_ab_vok_mzhk",
    "cnt_o_coup", "cnt_vols_upmk", "cnt_m_coup", "cnt_mzhk_upmk",
    "cnt_shk", "cnt_ork", "cnt_rk", "cnt_out_on_earth",
]


def upgrade() -> None:
    for f in CNT_FIELDS:
        op.alter_column(
            "pillar", f,
            existing_type=sa.Integer(),
            type_=sa.String(),
            existing_nullable=False,
            postgresql_using=f"{f}::text",
        )


def downgrade() -> None:
    for f in CNT_FIELDS:
        op.alter_column(
            "pillar", f,
            existing_type=sa.String(),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using=f"{f}::integer",
        )