"""
Diagnostic script: trace why SHAP sees 13 features but model was trained on 24.
Connects to DB at localhost:5432 (docker).
"""
import os
import sys
import json

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mlagent")

from sqlmodel import Session, create_engine, text
from sqlalchemy import create_engine as sa_create_engine

TASK_ID = "task_f702ff10"

# ── DB connection ──────────────────────────────────────────────────────
db_url = os.environ.get("DATABASE_URL")
engine = sa_create_engine(db_url, echo=False, connect_args={"connect_timeout": 5})

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
print(f"  Connected: {db_url}")

# ── 1. PipelineGeneration ──────────────────────────────────────────────
print("\n" + "=" * 72)
print(f"1. PipelineGeneration records for {TASK_ID}")
print("=" * 72)

rows = []
with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT id, status, ready_for_execution, "
        "execution_input_json IS NULL as eij_null, "
        "pg_column_size(execution_input_json::text) as eij_size, "
        "pipeline_json IS NULL as pij_null, "
        "pg_column_size(pipeline_json::text) as pij_size, "
        "created_at "
        "FROM pipeline_generation WHERE task_id = :tid ORDER BY created_at DESC"
    ), {"tid": TASK_ID})
    rows = result.fetchall()

if not rows:
    print(f"  No PipelineGeneration records for {TASK_ID}")
else:
    for r in rows:
        print(f"\n  id={r[0]}  status={r[1]}  ready={r[2]}")
        print(f"  execution_input_json: NULL={r[3]}  size={r[4]}")
        print(f"  pipeline_json:        NULL={r[5]}  size={r[6]}")
        print(f"  created_at: {r[7]}")

    # Get latest record details
    latest_id = rows[0][0]
    with engine.connect() as conn:
        # Get execution_input_json.feature_columns
        result = conn.execute(text(
            "SELECT execution_input_json->'feature_columns' as fc "
            "FROM pipeline_generation WHERE id = :id"
        ), {"id": latest_id})
        fc_raw = result.fetchone()[0]
        if fc_raw:
            import json
            fc_list = json.loads(fc_raw) if isinstance(fc_raw, str) else fc_raw
            print(f"\n  execution_input_json.feature_columns: {len(fc_list)} features")
            for i, f in enumerate(fc_list):
                print(f"    [{i:2d}] {f}")
        else:
            print(f"\n  execution_input_json.feature_columns: NULL/EMPTY *** ROOT CAUSE ***")

        # Check pipeline_json nested path
        result = conn.execute(text(
            "SELECT pipeline_json->'execution_input'->'feature_columns' as fc "
            "FROM pipeline_generation WHERE id = :id"
        ), {"id": latest_id})
        fc_nested = result.fetchone()[0]
        if fc_nested:
            fc_list2 = json.loads(fc_nested) if isinstance(fc_nested, str) else fc_nested
            print(f"\n  pipeline_json.execution_input.feature_columns: {len(fc_list2)} features")
            for i, f in enumerate(fc_list2):
                print(f"    [{i:2d}] {f}")
        else:
            print(f"\n  pipeline_json.execution_input.feature_columns: NULL/EMPTY")

        # Check pipeline_json top-level
        result = conn.execute(text(
            "SELECT pipeline_json->'feature_columns' as fc "
            "FROM pipeline_generation WHERE id = :id"
        ), {"id": latest_id})
        fc_top = result.fetchone()[0]
        print(f"\n  pipeline_json['feature_columns'] (top-level): {fc_top}")

        # Check model_ready_matrix_path
        result = conn.execute(text(
            "SELECT execution_input_json->'model_ready_matrix_path' as mp "
            "FROM pipeline_generation WHERE id = :id"
        ), {"id": latest_id})
        mp = result.fetchone()[0]
        print(f"\n  model_ready_matrix_path: {mp}")

# ── 2. FeaturePreprocessing ───────────────────────────────────────────
print("\n" + "=" * 72)
print(f"2. FeaturePreprocessing records for {TASK_ID}")
print("=" * 72)

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT id, status, "
        "preprocessing_json IS NULL as pp_null, "
        "pg_column_size(preprocessing_json::text) as pp_size, "
        "model_ready_artifact_path, "
        "created_at "
        "FROM feature_preprocessing WHERE task_id = :tid ORDER BY created_at DESC"
    ), {"tid": TASK_ID})
    fp_rows = result.fetchall()

if not fp_rows:
    print(f"  No FeaturePreprocessing records for {TASK_ID}")
else:
    for r in fp_rows:
        print(f"\n  id={r[0]}  status={r[1]}")
        print(f"  preprocessing_json: NULL={r[2]}  size={r[3]}")
        print(f"  model_ready_artifact_path: {r[4]}")
        print(f"  created_at: {r[5]}")

    fp_id = fp_rows[0][0]
    with engine.connect() as conn:
        # model_search_input.feature_columns
        result = conn.execute(text(
            "SELECT preprocessing_json->'model_search_input'->'feature_columns' as fc "
            "FROM feature_preprocessing WHERE id = :id"
        ), {"id": fp_id})
        ms_fc = result.fetchone()[0]
        if ms_fc:
            fc_list3 = json.loads(ms_fc) if isinstance(ms_fc, str) else ms_fc
            print(f"\n  model_search_input.feature_columns: {len(fc_list3)} features")
            for i, f in enumerate(fc_list3):
                print(f"    [{i:2d}] {f}")

        # preprocessing_execution.feature_selection
        result = conn.execute(text(
            "SELECT preprocessing_json->'preprocessing_execution'->'feature_selection' as fs "
            "FROM feature_preprocessing WHERE id = :id"
        ), {"id": fp_id})
        fs = result.fetchone()[0]
        if fs:
            fs_dict = json.loads(fs) if isinstance(fs, str) else fs
            retained = fs_dict.get("retained_features")
            dropped = fs_dict.get("columns_dropped", [])
            print(f"\n  feature_selection.retained_features: {retained}")
            print(f"  feature_selection.columns_dropped ({len(dropped)}):")
            for d in dropped[:10]:
                print(f"    {d}")
            if len(dropped) > 10:
                print(f"    ... and {len(dropped) - 10} more")

        # validation_summary
        result = conn.execute(text(
            "SELECT preprocessing_json->'validation_summary' as vs "
            "FROM feature_preprocessing WHERE id = :id"
        ), {"id": fp_id})
        vs = result.fetchone()[0]
        if vs:
            vs_dict = json.loads(vs) if isinstance(vs, str) else vs
            print(f"\n  validation_summary:")
            for k, v in vs_dict.items():
                print(f"    {k}: {v}")

# ── 3. PipelineExecution ──────────────────────────────────────────────
print("\n" + "=" * 72)
print(f"3. PipelineExecution records for {TASK_ID}")
print("=" * 72)

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT id, status, pipeline_generation_id, training_artifact_dir, "
        "execution_input_json IS NULL as eij_null, "
        "pg_column_size(execution_input_json::text) as eij_size, "
        "created_at "
        "FROM pipeline_execution WHERE task_id = :tid ORDER BY created_at DESC"
    ), {"tid": TASK_ID})
    pe_rows = result.fetchall()

if not pe_rows:
    print(f"  No PipelineExecution records for {TASK_ID}")
else:
    for r in pe_rows:
        print(f"\n  id={r[0]}  status={r[1]}  pg_id={r[2]}")
        print(f"  training_artifact_dir: {r[3]}")
        print(f"  execution_input_json: NULL={r[4]}  size={r[5]}")

    pe_id = pe_rows[0][0]
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT execution_input_json->'feature_columns' as fc "
            "FROM pipeline_execution WHERE id = :id"
        ), {"id": pe_id})
        pe_fc = result.fetchone()[0]
        if pe_fc:
            fc_list4 = json.loads(pe_fc) if isinstance(pe_fc, str) else pe_fc
            print(f"\n  PipelineExecution.execution_input_json.feature_columns: {len(fc_list4)} features")
            for i, f in enumerate(fc_list4):
                print(f"    [{i:2d}] {f}")
        else:
            print(f"\n  PipelineExecution.execution_input_json.feature_columns: NULL")

# ── 4. ModelSearchContext ──────────────────────────────────────────────
print("\n" + "=" * 72)
print(f"4. ModelSearchContext records for {TASK_ID}")
print("=" * 72)

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT id, status, "
        "context_json IS NULL as cj_null, "
        "pg_column_size(context_json::text) as cj_size, "
        "created_at "
        "FROM model_search_context WHERE task_id = :tid ORDER BY created_at DESC"
    ), {"tid": TASK_ID})
    msc_rows = result.fetchall()

if not msc_rows:
    print(f"  No ModelSearchContext records for {TASK_ID}")
else:
    for r in msc_rows:
        print(f"\n  id={r[0]}  status={r[1]}")
        print(f"  context_json: NULL={r[2]}  size={r[3]}")

    msc_id = msc_rows[0][0]
    with engine.connect() as conn:
        # pg_input.feature_columns
        result = conn.execute(text(
            "SELECT context_json->'pipeline_generation_input'->'feature_columns' as fc "
            "FROM model_search_context WHERE id = :id"
        ), {"id": msc_id})
        pg_fc = result.fetchone()[0]
        if pg_fc:
            fc_list5 = json.loads(pg_fc) if isinstance(pg_fc, str) else pg_fc
            print(f"\n  pipeline_generation_input.feature_columns: {len(fc_list5)} features")
            for i, f in enumerate(fc_list5):
                print(f"    [{i:2d}] {f}")
        else:
            print(f"\n  pipeline_generation_input.feature_columns: NULL/EMPTY")

# ── 5. Can we find the parquet? ────────────────────────────────────────
print("\n" + "=" * 72)
print("5. Parquet file location")
print("=" * 72)

if fp_rows:
    mp = fp_rows[0][4]  # model_ready_artifact_path
    print(f"  FeaturePreprocessing.model_ready_artifact_path: {mp}")
    # Convert Docker path to potential host path
    if mp and mp.startswith("/app/"):
        host_path = mp.replace("/app/", os.path.join(os.path.dirname(os.path.abspath(__file__)), ""))
        host_path = os.path.normpath(host_path)
        print(f"  Mapped to host path: {host_path}")
        print(f"  Exists on host: {os.path.exists(host_path)}")

# See if there's a path in PipelineGeneration's execution_input
if rows:
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT execution_input_json->'model_ready_matrix_path' as mp "
            "FROM pipeline_generation WHERE id = :id"
        ), {"id": rows[0][0]})
        pg_mp = result.fetchone()[0]
        if pg_mp:
            print(f"\n  PG execution_input.model_ready_matrix_path: {pg_mp}")

print("\n" + "=" * 72)
print("Diagnostic complete")
