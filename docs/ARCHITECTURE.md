# MLAgent architecture

## Overview

MLAgent is a full-stack materials machine-learning workflow application. The
React frontend presents a stage-based workbench, the FastAPI backend executes
each stage, PostgreSQL stores task state and structured results, and the local
artifact directories store uploaded datasets, feature matrices, trained models,
predictions, reports, and downloadable output packages.

## Runtime flow

The current product flow contains fourteen stages:

```text
Task Specification -> Task Interpretation -> Dataset Profile -> Workflow Plan
  -> Feature Engineering -> Data Preprocessing -> Model Search Plan
  -> Pipeline Generation -> Pipeline Execution -> Metric Evaluation
  -> Iteration Decision -> Interpretability -> Visualization -> Final Output
```

`Iteration Decision` owns the closed-loop decision and rerun plan. Metric
evaluation still emits a `result_diagnosis_input` payload; despite its historical
name, that payload is now consumed as evidence by the iteration-decision module.

## Backend layout

- `app/main.py` creates the FastAPI application, configures middleware and error
  handling, initializes the database, and registers the active API routers.
- `app/modules/` contains one package per workflow stage. Most packages separate
  HTTP routes (`api.py`), orchestration (`service.py`), persistence (`model.py`
  and `repository.py`), transport types (`schemas.py`), and focused builders or
  validators.
- `app/shared/` contains configuration, database connections, common responses,
  exceptions, and model/feature/HPO registries shared across stages.
- `alembic/` contains the versioned database schema migration chain.
- `scripts/` contains optional, manually invoked maintenance utilities.
- `tests/` mirrors the backend module structure for automated verification.

Large runtime data is intentionally kept outside source control. Its location is
configured through `DATASET_UPLOAD_DIR`, `FEATURE_ARTIFACT_DIR`, and
`MODEL_READY_ARTIFACT_DIR`.

## Frontend layout

- `src/index.tsx` is the React entry point and installs the Ant Design theme.
- `src/modules/` groups UI components and TypeScript types by workflow stage.
- `src/api/` contains the HTTP client for each active backend module.
- `src/components/shared/` contains reusable status, error, warning, panel, and
  JSON display components.
- `src/theme/` centralizes colors, typography, spacing, and pipeline accents.
- `public/` contains the static HTML shell.

`TaskPanelOrchestrator.tsx` is the authoritative frontend stage registry and
controls which stage panel is rendered for an active task.

## Deployment files

- `docker-compose.yml` supports local development.
- `docker-compose.prod.yml`, the Dockerfiles, and `frontend/nginx.conf` define the
  production container deployment.
- `.env.production.example` and `backend/.env.example` document required runtime
  configuration without storing secrets.
