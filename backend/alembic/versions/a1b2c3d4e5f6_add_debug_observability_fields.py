"""add debug & observability fields to interpretability_analysis

Revision ID: a1b2c3d4e5f6
Revises: 9b0c1d2e3f4a
Create Date: 2026-06-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9b0c1d2e3f4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'warnings_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'debug_trace_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'request_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'input_snapshot_json',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'current_step',
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'last_completed_step',
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'started_at',
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'finished_at',
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        'interpretability_analysis',
        sa.Column(
            'duration_seconds',
            sa.Float(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('interpretability_analysis', 'duration_seconds')
    op.drop_column('interpretability_analysis', 'finished_at')
    op.drop_column('interpretability_analysis', 'started_at')
    op.drop_column('interpretability_analysis', 'last_completed_step')
    op.drop_column('interpretability_analysis', 'current_step')
    op.drop_column('interpretability_analysis', 'input_snapshot_json')
    op.drop_column('interpretability_analysis', 'request_json')
    op.drop_column('interpretability_analysis', 'debug_trace_json')
    op.drop_column('interpretability_analysis', 'warnings_json')
