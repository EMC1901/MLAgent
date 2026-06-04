"""Remove final_pipeline_selection module

Revision ID: 24ed2193c844
Revises: 3578774de4dc
Create Date: 2026-05-23

- Drop table: final_pipeline_selection
- Drop columns from interpretability_analysis, final_output, iteration_decision, workflow_refinement
"""

from alembic import op
import sqlalchemy as sa


revision = "24ed2193c844"
down_revision = "3578774de4dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Drop columns that reference FPS from dependent tables FIRST

    # interpretability_analysis and final_output always exist
    with op.batch_alter_table("interpretability_analysis") as batch_op:
        batch_op.drop_column("final_pipeline_selection_id")

    with op.batch_alter_table("final_output") as batch_op:
        batch_op.drop_column("final_pipeline_selection_id")

    # iteration_decision: created in 3578774de4dc, always exists
    with op.batch_alter_table("iteration_decision") as batch_op:
        batch_op.drop_column("final_pipeline_selection_input_json")
        batch_op.drop_column("ready_for_final_selection")

    # workflow_refinement: was dropped in 3578774de4dc, may not exist.
    # Only attempt column drops if the table is present.
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'workflow_refinement'"
            ")"
        )
    )
    if result.scalar():
        with op.batch_alter_table("workflow_refinement") as batch_op:
            batch_op.drop_column("ready_for_final_pipeline_selection")
            batch_op.drop_column("final_pipeline_selection_input_json")

    # Step 2: Now safe to drop the FPS table itself
    op.drop_table("final_pipeline_selection")


def downgrade() -> None:
    # workflow_refinement may not exist (was dropped in 3578774de4dc upgrade).
    # Only restore columns if the table is present.
    conn = op.get_bind()
    wr_exists = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'workflow_refinement'"
            ")"
        )
    ).scalar()
    if wr_exists:
        with op.batch_alter_table("workflow_refinement") as batch_op:
            batch_op.add_column(
                sa.Column("final_pipeline_selection_input_json", sa.JSON(), nullable=True)
            )
            batch_op.add_column(
                sa.Column("ready_for_final_pipeline_selection", sa.Boolean(), nullable=True)
            )

    # Restore columns on iteration_decision
    with op.batch_alter_table("iteration_decision") as batch_op:
        batch_op.add_column(
            sa.Column("ready_for_final_selection", sa.Boolean(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("final_pipeline_selection_input_json", sa.JSON(), nullable=True)
        )

    # Restore column on final_output
    with op.batch_alter_table("final_output") as batch_op:
        batch_op.add_column(
            sa.Column("final_pipeline_selection_id", sa.String(255), nullable=True)
        )

    # Restore column on interpretability_analysis
    with op.batch_alter_table("interpretability_analysis") as batch_op:
        batch_op.add_column(
            sa.Column("final_pipeline_selection_id", sa.String(255), nullable=True)
        )

    # Recreate the final_pipeline_selection table
    op.create_table(
        "final_pipeline_selection",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.Column("iteration_decision_id", sa.String(255), nullable=True),
        sa.Column("metric_evaluation_id", sa.String(255), nullable=True),
        sa.Column("pipeline_execution_id", sa.String(255), nullable=True),
        sa.Column("pipeline_generation_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("selection_profile", sa.String(50), nullable=True),
        sa.Column("final_pipeline_spec_id", sa.String(255), nullable=True),
        sa.Column("final_model_id", sa.String(255), nullable=True),
        sa.Column("final_model_family", sa.String(255), nullable=True),
        sa.Column("final_trial_id", sa.String(255), nullable=True),
        sa.Column("primary_metric", sa.String(50), nullable=True),
        sa.Column("primary_metric_value", sa.Float(), nullable=True),
        sa.Column("selection_score", sa.Float(), nullable=True),
        sa.Column("ready_for_interpretability_analysis", sa.Boolean(), nullable=True),
        sa.Column("llm_used", sa.Boolean(), nullable=True),
        sa.Column("llm_confidence_level", sa.String(20), nullable=True),
        sa.Column("selection_json", sa.JSON(), nullable=True),
        sa.Column("candidate_ranking_json", sa.JSON(), nullable=True),
        sa.Column("system_selection_reason_json", sa.JSON(), nullable=True),
        sa.Column("llm_selection_explanation_json", sa.JSON(), nullable=True),
        sa.Column("candidate_difference_summary_json", sa.JSON(), nullable=True),
        sa.Column("human_review_notes_json", sa.JSON(), nullable=True),
        sa.Column("risk_notes_json", sa.JSON(), nullable=True),
        sa.Column("interpretability_analysis_input_json", sa.JSON(), nullable=True),
        sa.Column("artifact_manifest_json", sa.JSON(), nullable=True),
        sa.Column("llm_request_json", sa.JSON(), nullable=True),
        sa.Column("llm_response_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
