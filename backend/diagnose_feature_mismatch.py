"""
Diagnostic script: trace why SHAP sees 13 features but model was trained on 24.

Usage:  cd backend && python diagnose_feature_mismatch.py

Focuses on filesystem analysis first (parquet + model artifacts),
then attempts DB access if available.
"""
import os
import sys
import pandas as pd
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS = os.path.join(BASE, "artifacts")
TASK_ID = "task_f702ff10"

# ── Helper ─────────────────────────────────────────────────────────────
def find_file(pattern: str, under: str = None) -> str | None:
    """Walk directory tree looking for a file matching pattern."""
    start = under or ARTIFACTS
    if not os.path.isdir(start):
        return None
    for root, dirs, files in os.walk(start):
        for f in files:
            if pattern in f:
                return os.path.join(root, f)
    return None

def find_dir(pattern: str, under: str = None) -> str | None:
    start = under or ARTIFACTS
    if not os.path.isdir(start):
        return None
    for root, dirs, files in os.walk(start):
        for d in dirs:
            if pattern in d:
                return os.path.join(root, d)
    return None


# ── 1. Find model_ready_features.parquet ───────────────────────────────
print("=" * 72)
print("1. Finding parquet and model artifacts")
print("=" * 72)

# Try specific path from log
parquet_path = os.path.normpath(
    os.path.join(ARTIFACTS, "model_ready", "fmp_7c9d28ee", "model_ready_features.parquet")
)
if not os.path.exists(parquet_path):
    parquet_path = find_file("model_ready_features.parquet")
print(f"  Parquet: {parquet_path}")
print(f"  Exists:  {os.path.exists(parquet_path)}")

# Model from log
model_path = os.path.normpath(
    os.path.join(ARTIFACTS, "training", "pe_d4f02ee7", "models",
                 "trial_lightgbm_0010_09c99f_fold_0.joblib")
)
if not os.path.exists(model_path):
    model_path = find_file("fold_0.joblib", os.path.join(ARTIFACTS, "training"))
print(f"  Model:   {model_path}")
print(f"  Exists:  {os.path.exists(model_path) if model_path else False}")

if not parquet_path or not os.path.exists(parquet_path):
    # Try listing available artifact dirs
    print("\n  Available artifact directories:")
    for d in os.listdir(ARTIFACTS):
        dpath = os.path.join(ARTIFACTS, d)
        if os.path.isdir(dpath):
            print(f"    {d}/")
            for sub in os.listdir(dpath)[:10]:
                print(f"      {sub}")
    print("\nERROR: Cannot find parquet — diagnostic cannot proceed.")
    sys.exit(1)

# ── 2. Parquet column analysis ─────────────────────────────────────────
print("\n" + "=" * 72)
print("2. Parquet: all columns and dtypes")
print("=" * 72)

df = pd.read_parquet(parquet_path)
print(f"  Shape: {df.shape[0]} rows × {df.shape[1]} cols")

# Build dtype summary
bool_cols = []
float_cols = []
int_cols = []
object_cols = []
other_cols = []

for col in df.columns:
    dtype = df[col].dtype
    if pd.api.types.is_bool_dtype(dtype):
        bool_cols.append(col)
    elif pd.api.types.is_float_dtype(dtype):
        float_cols.append(col)
    elif pd.api.types.is_integer_dtype(dtype):
        int_cols.append(col)
    elif pd.api.types.is_object_dtype(dtype):
        object_cols.append(col)
    else:
        other_cols.append((col, dtype))

print(f"\n  bool:     {len(bool_cols)} cols")
for c in bool_cols:
    vals = df[c].value_counts().to_dict()
    print(f"    {c}  → {vals}")

print(f"\n  float64:  {len(float_cols)} cols")
for c in float_cols:
    null_count = df[c].isna().sum()
    flag = f" [nulls={null_count}]" if null_count > 0 else ""
    print(f"    {c}{flag}")

print(f"\n  int64:    {len(int_cols)} cols")
for c in int_cols:
    null_count = df[c].isna().sum()
    flag = f" [nulls={null_count}]" if null_count > 0 else ""
    print(f"    {c}{flag}")

print(f"\n  object:   {len(object_cols)} cols")
for c in object_cols:
    dropped = df[c].dropna()
    unique_vals = dropped.unique()[:10]
    print(f"    {c}")
    print(f"      nunique={dropped.nunique()} sample={unique_vals.tolist()[:5]}")

print(f"\n  other:    {len(other_cols)} cols")
for c, dt in other_cols:
    print(f"    {c} → dtype={dt}")

# ── 3. select_dtypes behavior ──────────────────────────────────────────
print("\n" + "=" * 72)
print("3. select_dtypes(include=['number']) — auto-discovery result")
print("=" * 72)

numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
print(f"  Returns: {len(numeric_cols)} columns")
for c in numeric_cols:
    print(f"    {c}")

non_numeric = df.select_dtypes(exclude=["number"]).columns.tolist()
print(f"\n  select_dtypes(exclude=['number']): {len(non_numeric)} columns")
for c in non_numeric:
    print(f"    dtype={df[c].dtype}  is_bool_dtype={pd.api.types.is_bool_dtype(df[c])}  {c}")

# ── 4. is_numeric_dtype per column ─────────────────────────────────────
print("\n" + "=" * 72)
print("4. pd.api.types.is_numeric_dtype() per column")
print("=" * 72)
print(f"  {'COL':<55s} {'dtype':<12s} {'is_numeric':<12s} {'is_bool':<10s} {'in_number':<12s}")
print(f"  {'-'*55} {'-'*12} {'-'*12} {'-'*10} {'-'*12}")
in_number_set = set(numeric_cols)
for col in df.columns:
    dtype = str(df[col].dtype)
    isnum = pd.api.types.is_numeric_dtype(df[col])
    isbool = pd.api.types.is_bool_dtype(df[col])
    innum = col in in_number_set
    markers = []
    if not innum and isnum:
        markers.append(" ← MISMATCH: is_numeric_dtype=True but not in select_dtypes(number)")
    if innum and not isnum:
        markers.append(" ← MISMATCH: in select_dtypes(number) but is_numeric_dtype=False")
    if isbool:
        markers.append(" [BOOL]")
    print(f"  {col:<55s} {dtype:<12s} {str(isnum):<12s} {str(isbool):<10s} {str(innum):<12s}{''.join(markers)}")

# ── 5. _normalize_bool_columns effect ──────────────────────────────────
print("\n" + "=" * 72)
print("5. _normalize_bool_columns effect")
print("=" * 72)

sys.path.insert(0, BASE)
from app.modules.feature_engineering.feature_matrix_builder import _normalize_bool_columns

df_norm = df.copy()
print(f"  Before:       {df_norm.shape[1]} cols")
print(f"  Non-numeric:  {len(df_norm.select_dtypes(exclude=['number']).columns)} cols")

df_norm = _normalize_bool_columns(df_norm)

after_non_num = df_norm.select_dtypes(exclude=["number"]).columns.tolist()
after_num = df_norm.select_dtypes(include=["number"]).columns.tolist()
print(f"  After normalize: {df_norm.shape[1]} cols")
print(f"  Non-numeric:     {len(after_non_num)} cols")
print(f"  Numeric:         {len(after_num)} cols")
if after_non_num:
    for c in after_non_num:
        print(f"    STILL NON-NUMERIC: dtype={df_norm[c].dtype}  {c}")

# ── 6. Model feature_name_ ─────────────────────────────────────────────
print("\n" + "=" * 72)
print("6. Model feature_name_")
print("=" * 72)

if model_path and os.path.exists(model_path):
    import joblib
    model = joblib.load(model_path)
    print(f"  Type: {type(model).__name__}")

    model_features = None
    for attr in ("feature_name_", "feature_names_in_"):
        names = getattr(model, attr, None)
        if names is not None:
            model_features = list(names)
            print(f"  model.{attr}: {len(model_features)} features")
            break

    if model_features is None:
        print("  Model has no feature_name_ or feature_names_in_")
        # Try booster
        if hasattr(model, "booster_"):
            booster = model.booster_
            model_features = list(booster.feature_name())
            print(f"  model.booster_.feature_name(): {len(model_features)} features")
    else:
        for i, n in enumerate(model_features):
            markers = ""
            if n not in df.columns:
                markers = " ← NOT IN PARQUET"
            print(f"    [{i:2d}] {n}{markers}")
else:
    model_features = None
    print("  Model not found — skipping")

# ── 7. Cross-reference ─────────────────────────────────────────────────
print("\n" + "=" * 72)
print("7. Cross-reference analysis")
print("=" * 72)

parquet_cols = list(df.columns)
auto_discovery = numeric_cols  # from select_dtypes(include=["number"])

if model_features:
    model_set = set(model_features)
    parquet_set = set(parquet_cols)
    auto_set = set(auto_discovery)

    in_model_not_parquet = model_set - parquet_set
    in_parquet_not_model = parquet_set - model_set
    in_model_not_auto = model_set - auto_set
    in_auto_not_model = auto_set - model_set

    print(f"  Model features:         {len(model_features)}")
    print(f"  Parquet columns:        {len(parquet_cols)}")
    print(f"  Auto-discovery (num):   {len(auto_discovery)}")

    if in_model_not_parquet:
        print(f"\n  *** In model but NOT in parquet ({len(in_model_not_parquet)}):")
        for c in sorted(in_model_not_parquet):
            print(f"    {c}")
    if in_parquet_not_model:
        print(f"\n  In parquet but NOT in model ({len(in_parquet_not_model)}):")
        for c in sorted(in_parquet_not_model):
            print(f"    {c}")
    if in_model_not_auto:
        print(f"\n  *** In model but NOT in auto-discovery ({len(in_model_not_auto)}):")
        for c in sorted(in_model_not_auto):
            dtype = df[c].dtype if c in df.columns else "N/A"
            print(f"    dtype={dtype}  {c}")
    if in_auto_not_model:
        print(f"\n  In auto-discovery but NOT in model ({len(in_auto_not_model)}):")
        for c in sorted(in_auto_not_model):
            print(f"    {c}")

    # Key question: is execution_input_json needed, or does auto-discovery cover everything?
    if in_model_not_auto:
        print(f"\n  >> CONCLUSION: Auto-discovery misses {len(in_model_not_auto)} model training features.")
        print(f"  >> These features exist in parquet but are excluded by select_dtypes(include=['number']).")
        print(f"  >> If ia_input.feature_columns is empty, SHAP input will be incomplete.")
    else:
        print(f"\n  >> Auto-discovery covers all model features. No metadata issue expected.")

# ── 8. DB access (attempt) ────────────────────────────────────────────
print("\n" + "=" * 72)
print("8. DB access (attempt)")
print("=" * 72)

try:
    from sqlmodel import Session, create_engine, text

    for host in ("db", "localhost"):
        db_url = f"postgresql://postgres:postgres@{host}:5432/mlagent"
        try:
            engine = create_engine(db_url, echo=False, connect_args={"connect_timeout": 5})
            with Session(engine) as sess:
                sess.execute(text("SELECT 1"))
            print(f"  Connected: {db_url}")
            break
        except Exception as e:
            print(f"  Failed ({host}): {e}")
    else:
        print("  DB not accessible — skipping DB diagnostics")
        engine = None
except ImportError:
    print("  sqlmodel not importable — skipping DB diagnostics")
    engine = None

if engine:
    from app.modules.pipeline_generation.model import PipelineGeneration
    from app.modules.feature_preprocessing.model import FeaturePreprocessing

    with Session(engine) as sess:
        pg = sess.query(PipelineGeneration).filter(
            PipelineGeneration.task_id == TASK_ID
        ).order_by(PipelineGeneration.created_at.desc()).first()

        if pg:
            print(f"\n  PipelineGeneration: id={pg.id}  status={pg.status}")
            eij = pg.execution_input_json
            print(f"  execution_input_json is None: {eij is None}")
            if eij is not None:
                print(f"  execution_input_json type: {type(eij).__name__}")
                if isinstance(eij, dict):
                    fc = eij.get("feature_columns", [])
                    print(f"  execution_input_json.feature_columns: {len(fc)} features")
                    if fc:
                        print(f"    First 5: {fc[:5]}")
                    else:
                        print(f"    (empty list)")
                else:
                    print(f"    raw value: {str(eij)[:200]}")
            else:
                print(f"  *** execution_input_json IS NULL — this is the root cause! ***")

            pij = pg.pipeline_json
            print(f"\n  pipeline_json is None: {pij is None}")
            if pij and isinstance(pij, dict):
                top_fc = pij.get("feature_columns", [])
                print(f"  pipeline_json['feature_columns'] (top-level): {len(top_fc)} items")
                ei_nested = pij.get("execution_input") or {}
                nested_fc = ei_nested.get("feature_columns", [])
                print(f"  pipeline_json.execution_input.feature_columns: {len(nested_fc)} items")
                if nested_fc:
                    print(f"    First 5: {nested_fc[:5]}")

        # FeaturePreprocessing
        fp = sess.query(FeaturePreprocessing).filter(
            FeaturePreprocessing.task_id == TASK_ID
        ).order_by(FeaturePreprocessing.created_at.desc()).first()

        if fp:
            print(f"\n  FeaturePreprocessing: id={fp.id}  status={fp.status}")
            pp_json = fp.preprocessing_json or {}
            ms_input = pp_json.get("model_search_input") or {}
            ms_fc = ms_input.get("feature_columns", [])
            print(f"  model_search_input.feature_columns: {len(ms_fc)} features")
            if ms_fc:
                print(f"    First 5: {ms_fc[:5]}")
            pe = pp_json.get("preprocessing_execution") or {}
            fs = pe.get("feature_selection") or {}
            print(f"  feature_selection.retained_features: {fs.get('retained_features', '(missing)')}")
            print(f"  feature_selection.columns_dropped: {len(fs.get('columns_dropped', []))} items")
        else:
            print(f"\n  FeaturePreprocessing: NOT FOUND for {TASK_ID}")

print("\n" + "=" * 72)
print("Diagnostic complete")
