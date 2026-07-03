"""add scientific_insight_report_json

Revision ID: 9b0c1d2e3f4a
Revises: 8cd91a0f3af0
Create Date: 2026-06-24 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9b0c1d2e3f4a'
down_revision: Union[str, None] = '8cd91a0f3af0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'scientific_insight_report_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'feature_group_summary_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('interpretability_analysis', 'feature_group_summary_json')
    op.drop_column('interpretability_analysis', 'scientific_insight_report_json')
