"""Add Phase 2 interpretability analysis columns

Revision ID: d4e5f6a7b8c9
Revises: 24ed2193c844
Create Date: 2026-05-23

- Add cross_method_consensus_json to interpretability_analysis
- Add partial_dependence_json to interpretability_analysis
- Add residual_analysis_json to interpretability_analysis
- Add correlation_analysis_json to interpretability_analysis
- Add physics_constraint_check_json to interpretability_analysis
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "24ed2193c844"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("interpretability_analysis") as batch_op:
        batch_op.add_column(
            sa.Column("cross_method_consensus_json", sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("partial_dependence_json", sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("residual_analysis_json", sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("correlation_analysis_json", sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("physics_constraint_check_json", sa.JSON(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("interpretability_analysis") as batch_op:
        batch_op.drop_column("physics_constraint_check_json")
        batch_op.drop_column("correlation_analysis_json")
        batch_op.drop_column("residual_analysis_json")
        batch_op.drop_column("partial_dependence_json")
        batch_op.drop_column("cross_method_consensus_json")
