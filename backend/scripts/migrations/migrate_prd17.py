"""
Add missing columns to existing database tables for PRD-17.

Run once from the backend directory:
    python -m scripts.migrations.migrate_prd17
"""
import sys
import psycopg2
from app.shared.config.settings import settings


MIGRATIONS = {
    "workflow_plan": [
        ("fe_registry_snapshot_version", "VARCHAR(50)"),
        ("feature_strategy_json", "JSONB"),
        ("preprocessing_intent_json", "JSONB"),
        ("workflow_rationale_json", "JSONB"),
    ],
    "feature_engineering": [
        ("executed_feature_strategy_id", "VARCHAR(255)"),
        ("feature_groups_json", "JSONB"),
        ("quality_profile_json", "JSONB"),
        ("execution_report_json", "JSONB"),
        ("provenance_json", "JSONB"),
        ("preprocessing_decision_input_json", "JSONB"),
    ],
    "feature_preprocessing": [
        ("preprocessing_plan_json", "JSONB"),
        ("execution_report_json", "JSONB"),
        ("removed_features_json", "JSONB"),
        ("feature_lineage_json", "JSONB"),
        ("explainability_report_json", "JSONB"),
        ("provenance_json", "JSONB"),
        ("registry_snapshot_version", "VARCHAR(50)"),
    ],
}


def run():
    db_url = settings.DATABASE_URL
    # parse psycopg2 DSN from SQLAlchemy URL, or use settings directly
    print(f"Connecting to: {db_url}")

    conn = psycopg2.connect(db_url)
    conn.autocommit = False

    try:
        cur = conn.cursor()

        for table, columns in MIGRATIONS.items():
            for col_name, col_type in columns:
                print(f"  ALTER TABLE {table} ADD COLUMN {col_name} {col_type};")
                try:
                    cur.execute(
                        f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}'
                    )
                    print(f"    OK")
                except Exception as e:
                    print(f"    SKIPPED: {e}")

        conn.commit()
        print("Migration complete.")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    run()
