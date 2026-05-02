# 项目已实现部分说明文档

> 文档生成日期：2026-05-02（全面更新版）
> 项目名称：MLAgent — AI-driven Automated Machine Learning Framework for Materials Science
> 文档用途：帮助后续 AI Coding 大模型和开发者快速理解当前项目已经完成的部分

---

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个面向材料科学领域的 AI 驱动自动化机器学习框架。其核心目标是让用户通过结构化表单提交材料机器学习任务需求，系统自动完成从**任务理解 → 数据加载 → 工作流规划 → 特征工程**的全流程自动化。当前尚未实现 Pipeline Generation 及后续阶段。

### 1.2 当前实现阶段

当前项目已完成 **五个核心业务模块** 的端到端实现：

| 模块 | 阶段 | 完成度 |
|------|------|--------|
| **模块一：Task Specification（任务规格录入与校验）** | MVP 已完成 | ~95% |
| **模块二：LLM-based Task Interpretation（基于大模型的任务理解）** | MVP 已完成 | ~90% |
| **模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）** | MVP 已完成 | ~90% |
| **模块四：Workflow Planning（LLM 驱动的工作流规划）** | MVP 已完成 | ~90% |
| **模块五：Feature Engineering（特征工程）** | MVP 已完成 | ~85% |
| **Featurizer Registry（共享能力注册表）** | MVP 已完成 | ~90% |

当前**尚未实现**的后续模块包括：Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis、Report Generation 等。

### 1.3 项目整体架构

```
用户浏览器 (React SPA — 单一 TaskSpecificationPage)
    | HTTP (axios)
FastAPI 后端 (Python, port 8000)
    | SQLModel
PostgreSQL 数据库 (port 5432)
    |
    ├── 外部 LLM API (OpenAI 兼容接口 — GPT-4.1 等)
    ├── 外部数据集 (Matbench / 用户上传 CSV/XLSX 文件)
    │       ↓
    │   Data Loaders (MatbenchLoader / FileLoader)
    │
    ├── Featurizer Registry (静态定义 + 依赖检测)
    │       ↓
    └── Featurizers (Composition / Descriptor / Structure + pymatgen + matminer)
            ↓
        Feature Artifact (parquet/csv 存储到 /app/artifacts/features/)
```

### 1.4 核心设计原则（根据当前代码分析）

1. **管道式架构**：五个模块严格按序依赖。每个下游模块的 `context_builder.py` 会校验所有上游模块的输出状态，状态不符则抛出专用异常。
2. **统一异常体系**：所有业务异常继承自 `BusinessException`，每个模块有自己的异常子类，附带有语义化的 `error_code`。
3. **LLM 输出强约束**：模块二和模块四均定义了严格的 JSON Schema，LLM 响应经过解析（`parser.py`）+ 校验（`validator.py`）两步才被认为有效。
4. **Featurizer Registry 作为共享契约**：Workflow Planning 的 Prompt 和 Validator、Feature Engineering 的 Strategy Resolver 都向 Registry 查询，而非各自维护硬编码列表。
5. **失败状态持久化**：所有模块在失败时都会将失败记录（含错误信息）写入数据库，不会静默丢失。

---

## 2. 当前目录结构说明

### 2.1 完整目录树（实际文件）

```
c:\projects\MLAgent/
├── backend/                                # 后端 FastAPI 项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI 入口，路由注册，CORS，异常处理，启动时建表
│   │   ├── modules/                       # 业务模块（五个模块 + Featurizer Registry API）
│   │   │   ├── __init__.py                # 空文件
│   │   │   ├── task_specification/        # 模块一：任务规格
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # 4 个接口（POST, GET, PUT, POST:/validate）
│   │   │   │   ├── schemas.py            # Create/Update/Response/ValidationResult
│   │   │   │   ├── service.py            # 业务编排：create → normalize → validate → build → persist
│   │   │   │   ├── model.py              # TaskSpecification (SQLModel, table=True, JSONB)
│   │   │   │   ├── repository.py         # CRUD (create/get_by_id/update/exists/list)
│   │   │   │   ├── normalizer.py         # 字段标准化映射（task_type/input_type/metric/priority）
│   │   │   │   ├── validator.py          # 必填字段校验、指标兼容性、输入一致性、警告生成
│   │   │   │   └── builder.py            # 构建 task_spec JSON dict
│   │   │   │
│   │   │   ├── task_interpretation/       # 模块二：LLM 任务理解
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # 4 个接口（POST, GET by id, GET by task, POST:/rerun）
│   │   │   │   ├── schemas.py            # InterpretedPredictionTarget, ModelingIntent 等 10+ 个子对象
│   │   │   │   ├── service.py            # 核心流程：adapt → build_prompt → LLM → parse → validate → build → persist
│   │   │   │   ├── model.py              # TaskInterpretation (JSONB + indexed status/task_id)
│   │   │   │   ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id
│   │   │   │   ├── task_spec_adapter.py  # 将 TaskSpecification DB model 转为 LLM context dict
│   │   │   │   ├── prompt_builder.py     # 构建 system/user prompt（含严格 JSON Schema）
│   │   │   │   ├── llm_client.py         # httpx 调用 OpenAI 兼容 API（含重试逻辑）
│   │   │   │   ├── parser.py             # LLM 响应 JSON 提取（正则去除 markdown 代码块）
│   │   │   │   ├── validator.py          # 对 LLM 输出进行结构/枚举值/置信度范围校验
│   │   │   │   ├── builder.py            # 构建 interpretation JSON dict
│   │   │   │   ├── enums.py              # InterpretationStatus / TargetCategory / ModelingGoal / InputModality
│   │   │   │   └── exceptions.py         # 5 个专用异常（TaskNotReady/LLMCall/Parse/Validation/NotFound）
│   │   │   │
│   │   │   ├── dataset_profile/           # 模块三：数据集加载与画像
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # 5 个接口（POST upload, POST profile, GET by id, GET by task, POST rerun, GET preview）
│   │   │   │   ├── schemas.py            # ColumnInfo, DatasetSource, Schema, ModalityCheck, TargetProfile, DataQuality 等
│   │   │   │   ├── service.py            # 编排：build_context → resolve_source → load → check_schema/modality/quality/target → build → persist
│   │   │   │   ├── model.py              # DatasetProfile (JSONB + profile_json + preview_json)
│   │   │   │   ├── repository.py         # CRUD + get_latest_by_task_id
│   │   │   │   ├── context_builder.py    # 跨库构建 context（校验 task/interpretation 状态）
│   │   │   │   ├── source_resolver.py    # 数据源识别（matbench / uploaded_file / unknown），含启发式规则
│   │   │   │   ├── profiler.py           # 质量评级 + 样本量等级 + 推荐下一步 + workflow_planning_input 构建
│   │   │   │   ├── builder.py            # 构建完整的 Dataset Profile JSON dict
│   │   │   │   ├── enums.py              # DatasetProfileStatus / DatasetSourceType 等
│   │   │   │   ├── exceptions.py         # DatasetProfileNotFound / SourceUnresolved / Load 等异常
│   │   │   │   ├── loaders/              # 数据加载器（策略模式）
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base_loader.py    # 抽象基类 BaseLoader
│   │   │   │   │   ├── matbench_loader.py# Matbench 加载（含 fallback 样本数据）
│   │   │   │   │   └── file_loader.py    # 用户上传文件加载（CSV/XLSX/XLS）
│   │   │   │   └── checkers/             # 数据检查器
│   │   │   │       ├── __init__.py
│   │   │   │       ├── schema_checker.py  # 列名检查、大小写匹配、全空列检测
│   │   │   │       ├── modality_checker.py# 输入模态检测与一致性校验（composition/structure/descriptor/text/mixed）
│   │   │   │       ├── quality_checker.py # 缺失值/重复行/无效值/常量列/高缺失率列/小样本
│   │   │   │       └── target_checker.py  # 回归（极值/均值/标准差/偏度/离群值）/分类（类别分布/不平衡）
│   │   │   │
│   │   │   ├── workflow_planning/         # 模块四：LLM 工作流规划
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # 4 个接口（POST, GET by id, GET by task, POST:/rerun）
│   │   │   │   ├── schemas.py            # TaskSummary/DataStrategy/FeatureStrategy/ModelStrategy 等 15+ 个子对象
│   │   │   │   ├── service.py            # 编排：build_context → build_prompt → LLM → parse → validate → build → persist
│   │   │   │   ├── model.py              # WorkflowPlan (JSONB + 多个索引列)
│   │   │   │   ├── repository.py         # CRUD + get_latest_by_task_id
│   │   │   │   ├── context_builder.py    # 跨4个上游模块构建context（校验 task/interpretation/profile 状态）
│   │   │   │   ├── prompt_builder.py     # 构建超长 system prompt（10 条 CRITICAL 规则 + 8 个策略维度）
│   │   │   │   ├── llm_client_adapter.py # 复用模块二的 LLMClient
│   │   │   │   ├── parser.py             # LLM 响应 JSON 提取
│   │   │   │   ├── validator.py          # 250 行严格校验：必填字段/枚举值/禁止代码/Featurizer Registry 校验
│   │   │   │   ├── builder.py            # 构建 Workflow Plan JSON dict
│   │   │   │   ├── enums.py              # WorkflowPlanStatus/SplitStrategy/HPOSearchMethod 等枚举工具类
│   │   │   │   └── exceptions.py         # WorkflowPlanNotFound/UpstreamNotReady/LLMCall/Parse/Validation
│   │   │   │
│   │   │   └── feature_engineering/       # 模块五：特征工程
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 5 个接口（POST, GET by id, GET by task, POST:/rerun, GET preview）
│   │   │       ├── registry_api.py       # Featurizer Registry 查询 API（GET list/detail/dependencies/validate）
│   │   │       ├── schemas.py            # FeatureGeneration/FeatureMatrixInfo/FeatureQuality/DownstreamInput 等
│   │   │       ├── service.py            # 编排：build_context → reload_data → resolve_strategy → run_featurizers → build_matrix → check_quality → save_artifact → persist
│   │   │       ├── model.py              # FeatureEngineering (JSONB + artifact_id/path)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id
│   │   │       ├── context_builder.py    # 跨5个上游模块构建context（校验全部前置模块状态）
│   │   │       ├── data_loader_adapter.py# 复用 Dataset Profile 的 MatbenchLoader / FileLoader 重新加载原始数据
│   │   │       ├── strategy_resolver.py  # 特征策略解析：优先级1 executable → 2 legacy recommended → 3 Registry fallback
│   │   │       ├── feature_matrix_builder.py # 构建特征矩阵（sample_id + features + target）
│   │   │       ├── artifact_manager.py   # 特征矩阵持久化（parquet/csv）+ metadata.json + 预览生成
│   │   │       ├── builder.py            # 构建 FeatureEngineering Object
│   │   │       ├── enums.py              # FeatureEngineeringStatus/FeatureType/InputModality
│   │   │       ├── exceptions.py         # 20 个细分异常类型
│   │   │       ├── featurizers/          # 特征化器实现
│   │   │       │   ├── __init__.py
│   │   │       │   ├── base_featurizer.py           # 抽象基类 BaseFeaturizer
│   │   │       │   ├── featurizer_router.py         # 注册表 ID → 可执行 Featurizer 实例的路由桥接
│   │   │       │   ├── composition_featurizer.py    # 内置轻量级 16 维元素属性描述符（103 种元素）
│   │   │       │   ├── descriptor_featurizer.py     # 已有数值描述符直通
│   │   │       │   ├── descriptor_cleaner.py        # 增强版描述符清洗器（含特征分组元数据）
│   │   │       │   ├── structure_featurizer.py      # 结构特征化器（占位符）
│   │   │       │   ├── pymatgen_composition_parser.py # pymatgen 配方解析器
│   │   │       │   ├── matminer_featurizers.py      # matminer 四大 Featurizer（Stoichiometry/ElementProperty/Magpie/ValenceOrbital）
│   │   │       │   └── matminer_structure_basic.py  # matminer 结构基本特征（planned）
│   │   │       └── checkers/            # 特征检查器
│   │   │           ├── __init__.py
│   │   │           └── feature_quality_checker.py   # 特征质量检查：缺失值/常量特征/无效特征/高缺失率
│   │   │
│   │   └── shared/                      # 公共能力
│   │       ├── __init__.py
│   │       ├── common/
│   │       │   ├── __init__.py
│   │       │   ├── response.py          # 统一响应格式：success_response / error_response / APIResponse
│   │       │   ├── exceptions.py        # 4 个基础异常（BusinessException / ValidationException / NotFoundException / DatabaseException）
│   │       │   └── enums.py             # 公共枚举：TaskStatus / TaskType / InputType / EvaluationMetric / UserPriority
│   │       ├── config/
│   │       │   ├── __init__.py
│   │       │   └── settings.py          # pydantic-settings：数据库/LLM/数据上传/特征工程/外部库 配置
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── connection.py        # SQLModel Engine 创建（单行，基于 DATABASE_URL）
│   │       │   └── session.py           # FastAPI Depends get_session 依赖注入（generator）
│   │       └── registry/               # Featurizer Registry（共享核心）
│   │           ├── __init__.py
│   │           ├── featurizer_registry.py # 12 个 FeaturizerSpec 静态定义 + 依赖检测 + ID/Alias 索引 + 查询 API + 回退逻辑
│   │           ├── schemas.py           # FeaturizerSpec / FeaturizerResolveResult / FallbackResult / DependencyCheckResult
│   │           └── exceptions.py        # 5 个 Registry 异常
│   │
│   ├── .env.example                     # 环境变量模板
│   ├── requirements.txt                 # 16 个 Python 依赖
│   └── Dockerfile                       # 后端容器化
│
├── frontend/                            # 前端 React 项目（CRA + TypeScript）
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── index.tsx                    # ReactDOM 入口，渲染 <TaskSpecificationPage />
│   │   ├── api/                         # API 客户端层（axios）
│   │   │   ├── taskApi.ts               # Task Specification API + axios 单例配置（含 request/response 拦截器，超时 120s）
│   │   │   ├── taskInterpretationApi.ts  # Task Interpretation API
│   │   │   ├── datasetProfileApi.ts     # Dataset Profile API（含文件上传）
│   │   │   ├── workflowPlanningApi.ts   # Workflow Planning API
│   │   │   └── featureEngineeringApi.ts # Feature Engineering API（超时 600s）+ Featurizer Registry API
│   │   └── modules/
│   │       ├── taskSpecification/
│   │       │   ├── pages/
│   │       │   │   └── TaskSpecificationPage.tsx  # 页面组件（蓝色 Header + 白色表单）
│   │       │   ├── components/
│   │       │   │   ├── TaskSpecificationForm.tsx  # 主表单组件（react-hook-form + Zod 校验，5 个面板嵌入）
│   │       │   │   └── TaskFieldGroup.tsx         # 表单分节容器
│   │       │   └── constants.ts          # Zod Schema + 5 组选项常量（共 35 个选项）
│   │       ├── taskInterpretation/
│   │       │   ├── components/
│   │       │   │   └── TaskInterpretationPanel.tsx # LLM 结果展示面板（含 Run/Re-run 按钮）
│   │       │   └── types.ts
│   │       ├── datasetProfile/
│   │       │   ├── components/
│   │       │   │   ├── DatasetProfilePanel.tsx    # 画像结果展示面板（含文件上传控件）
│   │       │   │   └── FileUpload.tsx              # 拖拽/点击上传组件
│   │       │   └── types.ts
│   │       ├── workflowPlanning/
│   │       │   ├── components/
│   │       │   │   └── WorkflowPlanPanel.tsx      # 工作流规划展示面板（含 Badge/Section 组件，8 个策略维度全展示）
│   │       │   └── types.ts
│   │       └── featureEngineering/
│   │           ├── components/
│   │           │   └── FeatureEngineeringPanel.tsx  # 特征工程展示面板（含多 featurizer 结果、特征组展示）
│   │           └── types.ts
│   ├── package.json                     # 12 个依赖（React 18 + axios + react-hook-form + zod 等）
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml                   # 三服务编排（db:postgres-16 + backend + frontend）
├── .gitignore
└── docs/
    ├── PROJECT_IMPLEMENTATION_OVERVIEW.md # 本文档
    ├── prd-1-mvp.md                      # 模块一 PRD
    ├── prd-1-技术栈.md
    ├── prd-1-架构.md
    ├── prd-2.md / prd-2-技术实现方案.md
    ├── prd-3.md / prd-3-技术实现方案.md
    ├── prd-4.md / prd-4-技术实现方案.md
    ├── prd-5.md / prd-5-技术实现方案.md / prd-5-FeaturizerRegistry.md
    ├── prd-5-扩展.md / prd-5-扩展技术实现方案.md
```

### 2.2 关键文件职责速查表

| 文件路径 | 核心职责 | 行数约 |
|----------|----------|--------|
| [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | FastAPI 应用入口，注册 6 个 Router，CORS，全局异常处理，启动建表 | 65 |
| [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) | 所有环境变量配置（LLM/DB/上传/特征工程/外部库） | 53 |
| [featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py) | 12 个 FeaturizerSpec 静态定义 + 依赖检测 + ID/Alias 解析 + 查询/回退 API | 500 |
| [prompt_builder.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py) | 超长 LLM prompt 构建（含完整 JSON Schema 定义 + 10 条 CRITICAL 规则 + 动态 Featurizer 列表注入） | 250 |
| [validator.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/validator.py) | 最严格的 LLM 输出校验（12 个维度的必填字段 + 枚举值 + 禁止代码 + Featurizer Registry 校验） | 236 |
| [service.py (feature_engineering)](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/service.py) | 最复杂业务编排（11 个步骤：context → load → strategy → featurize → matrix → quality → artifact → schema → status → build → persist） | 455 |
| [strategy_resolver.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/strategy_resolver.py) | 三步优先级策略解析（Featurizer Registry 驱动） | 139 |
| [featurizer_router.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/featurizer_router.py) | Registry ID → 可执行 Featurizer 实例的路由桥接 | 106 |
| [matminer_featurizers.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/matminer_featurizers.py) | 4 个 matminer 特征化器统一实现（依赖检测/配方解析/分组前缀/失败追踪） | ~500 |
| [composition_featurizer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/composition_featurizer.py) | 内置 103 元素属性表 + 16 维轻量级描述符 | 241 |
| [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) | 前端主表单（react-hook-form + Zod + 5 个下游面板嵌入） | 500 |

---

## 3. 当前系统输入与输出

### 3.1 系统输入

#### 输入一：用户通过前端表单提交任务规格

- **入口文件**：[TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx)
- **触发条件**：用户点击 "Submit Task Specification" 按钮
- **前端校验**：使用 [Zod Schema](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts) 进行表单级校验（5 个必填字段 + 类型校验）
- **核心字段**（根据 [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py) 中的 `TaskSpecificationCreateRequest`）：
  - `prediction_target`（**必填**）：预测目标，如 "experimental band gap"
  - `task_type`（**必填**）：`regression` / `classification` / `ranking`
  - `dataset_description`（**必填**）：数据集描述
  - `input_type`（**必填**）：`composition` / `structure` / `descriptor_table` / `text_features`
  - `target_column`（**必填**）：目标列名
  - `evaluation_metric`（可选）：支持 9 种指标
  - `task_name`、`task_description`、`material_system`（可选）
  - `user_priority`、`constraints`（可选）

#### 输入二：用户触发 LLM 任务理解

- **入口**：[TaskInterpretationPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskInterpretation/components/TaskInterpretationPanel.tsx) 中的 "Run Interpretation" 按钮
- **前提条件**：task_id 对应 task 状态为 `valid` 或 `valid_with_warning`（由 [task_spec_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/task_spec_adapter.py) 中的 `adapt_task_spec` 函数校验）
- **外部依赖**：LLM API（OpenAI 兼容接口，默认 `gpt-4.1`）

#### 输入三：用户上传数据集文件

- **入口**：[FileUpload.tsx](file:///c:/projects/MLAgent/frontend/src/modules/datasetProfile/components/FileUpload.tsx) 拖拽或点击上传
- **后端处理**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py) 中的 `upload_dataset_file` 接口
- **支持格式**：CSV（`.csv`）、Excel（`.xlsx`、`.xls`）
- **限制**：文件 ≤ `DATASET_MAX_FILE_SIZE_MB`（默认 100MB），由 [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) 配置
- **存储**：文件保存到 `DATASET_UPLOAD_DIR`（默认 `/app/uploads`），命名格式 `file_{uuid8}{ext}`

#### 输入四：用户触发数据集画像

- **入口**：[DatasetProfilePanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/datasetProfile/components/DatasetProfilePanel.tsx) 中的 "Run Dataset Profiling" 按钮
- **前置条件**（由 [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/context_builder.py) 校验）：
  - Task 状态为 `valid` 或 `valid_with_warning`
  - Interpretation 状态为 `interpreted` 或 `interpreted_with_warning`
  - Interpretation 中包含 `dataset_intent` 字段
- **可选输入**：`uploaded_file_id`（用户上传的文件 ID）

#### 输入五：用户触发特征工程

- **入口**：[FeatureEngineeringPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/featureEngineering/components/FeatureEngineeringPanel.tsx) 中的 "Run Feature Engineering" 按钮
- **前置条件**（由 [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/context_builder.py) 跨 5 个模块校验）：
  - Task（valid） → Interpretation（interpreted） → Profile（profiled） → Plan（planned）
  - Profile 的 `is_usable_for_ml` 为 `True`
  - Plan 的 `plan_json` 中包含 `feature_strategy`

### 3.2 系统输出

#### 输出一：Task Specification Object

根据 [builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/builder.py) 的 `build_task_specification` 函数和 [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py) 的 `TaskSpecificationResponse`：

```json
{
  "task_id": "task_{uuid8}",
  "status": "valid | valid_with_warning | incomplete | invalid",
  "task_type": "regression",
  "prediction_target": "experimental band gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE",
  "missing_fields": [],
  "validation_messages": [],
  "created_at": "...",
  "updated_at": "..."
}
```

#### 输出二：Task Interpretation Object

根据 [builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/builder.py) 和 [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/schemas.py) 的 `TaskInterpretationResponse`，包含以下关键子对象：
- `interpreted_prediction_target`（raw/normalized/category/unit/description）
- `modeling_intent`（primary_goal/secondary_goals/optimization_direction/preferred_metric）
- `dataset_intent`（dataset_reference/expected_input_columns/expected_target_column/requires_structure_file/dataset_loading_hint）
- `planning_hint`（task_family/input_representation/requires_feature_engineering 等）
- `constraint_interpretation`（hard_constraints/soft_constraints/potential_conflicts）
- `recommended_defaults`（evaluation_metric/validation_strategy/baseline_requirement）

状态值：`interpreted`（无警告）或 `interpreted_with_warning`（有 ambiguities 或 warnings）

#### 输出三：Dataset Profile Object

根据 [builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/builder.py) 的 `build_dataset_profile`（179 行输出的完整 JSON），核心子对象：
- `dataset_source`（source_type/reference/loader/loaded_from/file_name）
- `dataset_schema`（n_samples/n_columns/columns/input_columns/target_column）
- `modality_check`（expected/detected/is_consistent/messages）
- `target_profile`（回归：min/max/mean/std/skewness/outlier_count；分类：class_count/class_distribution/is_imbalanced）
- `data_quality`（missing_values/duplicates/invalid_rows/warnings/errors）
- `profiling_summary`（is_loadable/is_usable_for_ml/sample_size_level/quality_level/recommended_next_step）
- `workflow_planning_input`（为模块四准备的标准化下游输入）
- `preview`（前 N 行数据预览）

状态值：`profiled`（完美）/ `profiled_with_warning`（有警告）/ `failed`（不可用）

#### 输出四：Workflow Plan Object

根据 [builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/builder.py) 和 [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/schemas.py) 的 `WorkflowPlanResponse`，包含 **8 个策略维度** 子对象：
- `task_summary`（task_type/input_modality/prediction_target/material_domain/primary_goal）
- `data_strategy`（input_columns/target_column/required_cleaning_steps/target_handling/duplicate_handling/missing_value_strategy）
- `feature_strategy`（feature_type/executable_featurizers/semantic_featurizers/unsupported_future_featurizers/feature_selection_required/feature_scaling_required）
- `model_strategy`（candidate_model_families/baseline_models/preferred_model_bias/excluded_model_families）
- `validation_strategy`（split_strategy/n_splits/test_size/random_state/stratification_required）
- `evaluation_strategy`（primary_metric/secondary_metrics/metric_direction）
- `hpo_strategy`（enabled/search_method/budget_level/max_trials）
- `interpretability_strategy`（enabled/methods/priority）
- `pipeline_generation_input`（pipeline_steps/required_components：data_cleaner/featurizer/model_trainer/evaluator）
- `planning_warnings`、`planning_assumptions`、`llm_reasoning_summary`、`confidence_score`

状态值：`planned` / `planned_with_warning` / `failed`

#### 输出五：Feature Engineering Object

根据 [builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/builder.py) 和 [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/schemas.py) 的 `FeatureEngineeringResponse`，核心子对象：
- `feature_generation`（selected_featurizers/semantic/fallback/skipped/unsupported_future/executed_featurizers 详情）
- `feature_matrix`（artifact_id/storage_type/file_path/n_samples/n_features/target_column）
- `feature_schema`（feature_columns/feature_groups/numeric_count/categorical_count/constant_count/all_missing_count）
- `feature_quality`（missing_values/invalid_features/dropped_features/failed_samples/constant_features/is_valid_feature_matrix）
- `preprocessing_requirements`（scaling/imputation/feature_selection）
- `downstream_input`（为 Pipeline Generation 准备的标准化输入，含 `ready_for_pipeline_generation` 标志）

状态值：`completed` / `completed_with_warning` / `failed` / `blocked`

---

## 4. 当前技术栈说明

### 4.1 后端技术栈

| 技术 | 版本 | 承担作用 | 引用文件 |
|------|------|----------|----------|
| **FastAPI** | 0.115.6 | Web 框架，路由注册、CORS、异常处理、依赖注入 | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) |
| **uvicorn** | 0.34.0 | ASGI 服务器 | 启动命令 |
| **SQLModel** | 0.0.22 | ORM + 数据验证，结合 SQLAlchemy + Pydantic，创建表和数据模型 | [model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)（所有模块的 model.py 都使用 SQLModel） |
| **PostgreSQL** | 16 (Docker) | 永久化存储，使用 JSONB 存储各模块输出的完整 JSON | [docker-compose.yml](file:///c:/projects/MLAgent/docker-compose.yml) line 7 |
| **psycopg2-binary** | 2.9.10 | PostgreSQL 驱动 | [requirements.txt](file:///c:/projects/MLAgent/backend/requirements.txt) |
| **pydantic** | 2.10.4 | 请求/响应模型校验 | 所有 schemas.py 文件 |
| **pydantic-settings** | 2.7.1 | 环境变量管理，支持 .env 文件 | [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) |
| **httpx** | 0.28.1 | LLM API HTTP 调用（异步支持） | [llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py) |
| **pandas** | 2.2.3 | 数据处理核心（DataFrame 加载、清洗、特征工程、统计分析） | 所有 loader/checker/featurizer 文件 |
| **numpy** | 2.2.0 | 数值计算 | [target_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/target_checker.py) / [composition_featurizer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/composition_featurizer.py) |
| **openpyxl** | 3.1.5 | Excel 文件解析 | [file_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/file_loader.py) |
| **pymatgen** | ≥2024.0.0 | 材料学核心库，化学式解析、结构处理 | [matminer_featurizers.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/matminer_featurizers.py) |
| **matminer** | ≥0.9.0 | 材料特征工程库，提供 Stoichiometry/ElementProperty/Magpie/ValenceOrbital | [matminer_featurizers.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/matminer_featurizers.py) |
| **scikit-learn** | ≥1.3.0 | 仅用于依赖声明，当前代码中未实际大规模使用 | requirements.txt |
| **pyarrow** | ≥14.0.0 | Parquet 格式特征矩阵存储 | [artifact_manager.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/artifact_manager.py) |
| **alembic** | 1.14.1 | 数据库迁移工具（已安装，但当前项目使用 SQLModel.metadata.create_all 自动建表，未实际使用迁移） | requirements.txt |

### 4.2 前端技术栈

| 技术 | 版本 | 承担作用 | 引用文件 |
|------|------|----------|----------|
| **React** | 18.3.1 | UI 框架 | [index.tsx](file:///c:/projects/MLAgent/frontend/src/index.tsx) |
| **TypeScript** | 5.7.2 | 类型安全 | tsconfig.json |
| **react-hook-form** | 7.54.2 | 表单状态管理 | [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) |
| **zod** | 3.24.1 | 前端表单校验 Schema | [constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts) |
| **@hookform/resolvers** | 3.10.0 | react-hook-form 与 zod 的适配器 | TaskSpecificationForm.tsx |
| **axios** | 1.7.9 | HTTP 客户端，全局拦截器，超时配置 | [taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) |
| **react-scripts** | 5.0.1 | Create React App 构建工具链 | package.json |

### 4.3 基础设施

| 技术 | 承担作用 |
|------|----------|
| **Docker Compose** | 三服务编排（db + backend + frontend），PostgreSQL 健康检查，卷挂载 |
| **PostgreSQL 16 Alpine** | 轻量数据库镜像 |
| **Volumes** | postgres_data 持久化、backend/frontend 代码热挂载 |

---

## 5. 已实现功能模块

### 5.1 模块一：Task Specification（任务规格录入与校验）

**功能描述**：用户提交材料 ML 任务需求，系统进行字段标准化、完整性和合法性校验，生成规范的 Task Specification Object 入库。

**输入**：
- 用户通过 [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) 提交表单
- Zod 前端校验 5 个必填字段（prediction_target/task_type/dataset_description/input_type/target_column）

**处理逻辑**（调用链）：
1. [api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) → `POST /api/tasks` → `create_task`
2. [service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) → `create_task()` 方法
3. 生成 `task_id` → 调用 `normalize_fields()` 进行 [normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py) 中的字段标准化映射（如 `"chemical composition"` → `"composition"`，`"mae"` → `"MAE"`）
4. 调用 [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 的 `validate()` 进行四层检查：必填字段 → 指标体系兼容性 → 输入/数据集一致性 → 警告生成
5. 调用 [builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/builder.py) 的 `build_task_specification()` 构建完整 JSON dict
6. 创建 `TaskSpecification` 实例 → [repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py) → 入库

**输出**：`TaskSpecificationResponse`，状态为 `valid` / `valid_with_warning` / `incomplete` / `invalid`

**数据库表**：`task_specification`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)），包含 8 个专项列 + `task_spec_json` (JSONB) 存储完整输出

**完成度**：~95%。核心流程完整，异常处理完善。前端表单字段完整覆盖 PRD 需求。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py)、[normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py)、[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/builder.py)

---

### 5.2 模块二：LLM-based Task Interpretation（基于大模型的任务理解）

**功能描述**：将用户提交的 Task Specification 送入 LLM，生成结构化的语义理解输出（Interpretation），为下游模块提供机器可读的任务语义描述。

**输入**：
- Task Specification DB 记录（状态为 valid/valid_with_warning）
- LLM API 配置（`LLM_PROVIDER`/`LLM_MODEL`/`LLM_API_KEY`/`LLM_BASE_URL`）

**处理逻辑**（调用链）：
1. [api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py) → `POST /api/task-interpretations/{task_id}`
2. [service.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/service.py) → `create_interpretation()`
3. [task_spec_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/task_spec_adapter.py) → `adapt_task_spec()`：提取 task_summary/ml_task/data_context/user_intent 四个维度
4. [prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py) → `build_prompt()`：构建 system（含 8 条 CRITICAL RULES）+ user message（含 JSON Schema）
5. [llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py) → `LLMClient.generate()`：httpx POST 到 `{LLM_BASE_URL}/chat/completions`，含重试逻辑（`LLM_MAX_RETRIES`）
6. [parser.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/parser.py) → `parse_llm_response()`：去除 Markdown 代码块，解析 JSON
7. [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/validator.py) → `validate_interpretation()`：12 个必填字段 + 5 组枚举值 + confidence_score 范围校验
8. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/builder.py) → `build_interpretation()`：构建 interpretation JSON dict，根据 ambiguities/warnings 确定状态
9. 创建 `TaskInterpretation` → [repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/repository.py) → 入库

**输出**：`TaskInterpretationResponse`，状态为 `interpreted` 或 `interpreted_with_warning`

**数据库表**：`task_interpretation`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py)），存储 `interpretation_json` + `llm_request_json` + `llm_response_json` (JSONB)

**完成度**：~90%。LLM 调用、解析、校验链路完整。但 LLM config 中存在一些未暴露给前端的可配置性（如温度值固定 0.0）。llm_client 直接依赖模块内配置，没有抽象 Provider 工厂。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/service.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/repository.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/schemas.py)、[task_spec_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/task_spec_adapter.py)、[prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py)、[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)、[parser.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/parser.py)、[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/validator.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/builder.py)、[enums.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/enums.py)、[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/exceptions.py)

---

### 5.3 模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）

**功能描述**：根据 Task Interpretation 中的 `dataset_intent`，确定数据源→加载数据→执行四维检查（Schema/Modality/Quality/Target）→汇总画像→输出标准化 `workflow_planning_input`。

**输入**：
- Task Specification + Task Interpretation（状态校验过）
- 用户可选上传文件（`uploaded_file_id` 或 `uploaded_file_path`）

**处理逻辑**（完整的 10 步流水线）：
1. [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/context_builder.py) → `build_dataset_loading_context()`：跨 task_specification + task_interpretation 库构建统一 context，校验状态链
2. [source_resolver.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/source_resolver.py) → `resolve_source()`：优先级 1 上传文件 → 2 interpretation 的 `dataset_loading_hint` → 3 启发式匹配（matbench/CSV/XLSX 关键词）
3. [matbench_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/matbench_loader.py) 或 [file_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/file_loader.py) → 加载 DataFrame（Matbench 未安装时会生成样本数据）
4. [schema_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/schema_checker.py) → `check_schema()`：列名大小写匹配、重复列名、全空列检测
5. [modality_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/modality_checker.py) → `check_modality()`：启发式检测（composition regex/结构关键词/数值列/文本）→ 一致性校验
6. [quality_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/quality_checker.py) → `check_quality()`：缺失值/重复行/无效值/常量列/高缺失率列/小样本
7. [target_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/target_checker.py) → `check_target()`：回归（极值/IQR离群值/偏度）/分类（类别分布/不平衡检测）
8. [profiler.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/profiler.py) → `aggregate_profiling_summary()` + `build_workflow_planning_input()`：综合质量评级（good/fair/poor/unusable）、样本量等级（very_small/small/medium/large）、推荐下一步
9. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/builder.py) → `build_dataset_profile()`：汇总 179 行代码输出完整 JSON
10. 创建 `DatasetProfile` → [repository.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/repository.py) → 入库

**输出**：`DatasetProfileResponse`，状态为 `profiled` / `profiled_with_warning` / `failed`

**关键设计**：
- `MatbenchLoader` 在 matminer 未安装时会从硬编码的 `_KNOWN_DATASETS` 字典生成随机样本数据（最多 200 行），确保开发环境可运行
- `FileLoader` 支持通过 file_id 前缀匹配查找文件，增强容错性
- `workflow_planning_input` 是模块四的标准化输入，包含数据质量、预处理需求、目标分布等信息

**数据库表**：`dataset_profile`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/model.py)），包含 source_type/loader_name/n_samples/n_columns/input_modality/target_column/quality_level 等专项列 + `profile_json` + `preview_json` (JSONB)

**完成度**：~90%。四维检查逻辑完善，Matbench fallback 机制保证开发体验。但仅支持 CSV/XLSX/XLS 三种格式，不支持 JSON/TSV 等其他格式。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/service.py)、[context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/context_builder.py)、[source_resolver.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/source_resolver.py)、[profiler.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/profiler.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/builder.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/repository.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/schemas.py)、所有 loaders/ 和 checkers/ 目录下的文件

---

### 5.4 模块四：Workflow Planning（LLM 驱动的工作流规划）

**功能描述**：将前三个模块的输出（Task + Interpretation + Profile）送入 LLM，生成包含 8 个策略维度的结构化 ML 工作流规划。

**输入**：
- Task Specification（valid） + Task Interpretation（interpreted） + Dataset Profile（profiled，is_usable_for_ml=True）
- LLM API（复用模块二的 `LLMClient`）

**处理逻辑**（调用链）：
1. [api.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/api.py) → `POST /api/workflow-plans/{task_id}`
2. [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/context_builder.py) → `build_workflow_planning_context()`：跨 task_specification + task_interpretation + dataset_profile 三个表构建完整 context，校验状态链和 `is_usable_for_ml`
3. [prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py) → `build_prompt()`：**关键创新**——在运行时从 Featurizer Registry 动态获取 `available_featurizers` 和 `planned_featurizers` 列表注入 Prompt，确保 LLM 只推荐系统中实际可用的 Featurizer
4. [llm_client_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/llm_client_adapter.py) → `WorkflowPlanningLLMAdapter.generate()`：封装 `LLMClient`，提供统一接口
5. [parser.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/parser.py) → `parse_llm_response()`：JSON 提取
6. [validator.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/validator.py) → `validate_workflow_plan()`：**最严格的校验器（236 行）**，包含 4 个层面的检查：
   - **结构校验**：13 个顶级字段 + 每个子对象的必填字段
   - **枚举值校验**：task_type/input_modality/split_strategy/search_method/budget_level/metric_direction/n_splits 范围
   - **禁止内容检测**：`FORBIDDEN_CONTENT` 列表（20 个关键词如 `import pandas`, `def train`, `model.fit` 等），防止 LLM 生成代码或假指标
   - **Featurizer Registry 校验**：`_check_featurizer_registry()` —— 验证 `executable_featurizers` 中的每个名称是否能在 Registry 中解析为可用状态（三层优先级：executable → legacy recommended → fallback）
7. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/builder.py) → `build_workflow_plan()`：构建完整 Plan JSON dict

**输出**：`WorkflowPlanResponse`，包含 8 个策略维度（task_summary/data_strategy/feature_strategy/model_strategy/validation_strategy/evaluation_strategy/hpo_strategy/interpretability_strategy）+ pipeline_generation_input

**关键设计**：
- **System Prompt 10 条 CRITICAL BOUNDARY RULES**：明确禁止 LLM 生成代码、虚构训练结果、模型指标等，是约束 LLM 行为的关键设计
- **Featurizer Registry 集成**：Validator 最后一步 `_check_featurizer_registry()` 确保了 LLM 推荐的 Featurizer 一定在 Registry 中存在且可用
- **禁止内容列表**：所有 20 个关键词均为小写匹配，防止 LLM 输出代码片段或假造评估结果

**数据库表**：`workflow_plan`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/model.py)），包含 task_type/input_modality/primary_metric/feature_type/validation_strategy/hpo_enabled/interpretability_enabled/confidence_score 等专项索引列 + `plan_json` + `llm_request_json` + `llm_response_json` (JSONB)

**完成度**：~90%。LLM Prompt 设计和输出校验均非常严格。但所有规划策略均无规则化 fallback，完全依赖 LLM。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/service.py)、[context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/context_builder.py)、[prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py)、[llm_client_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/llm_client_adapter.py)、[parser.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/parser.py)、[validator.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/validator.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/builder.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/repository.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/schemas.py)、[enums.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/enums.py)、[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/exceptions.py)

---

### 5.5 模块五：Feature Engineering（特征工程）

**功能描述**：根据 Workflow Plan 中的 `feature_strategy`，重新加载原始数据，通过 Featurizer Registry + Featurizer Router 选择并执行特征化器，构建特征矩阵、质量检查、持久化 artifact，输出 `downstream_input` 供 Pipeline Generation 消费。

**输入**：
- 全部四个上游模块的输出（状态校验过）
- Workflow Plan 中的 `feature_strategy`（含 `executable_featurizers` 或 `recommended_featurizers`）

**处理逻辑**（最复杂的 11 步流水线，见 [service.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/service.py) 的 `create_feature_engineering()` 方法）：
1. [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/context_builder.py) → `build_feature_engineering_context()`：跨 5 个上游模块（Task/Interpretation/Profile/Plan）校验，提取 `feature_strategy`
2. [data_loader_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/data_loader_adapter.py) → `reload_raw_data()`：复用模块三的 `MatbenchLoader` / `FileLoader` 重新加载原始 DataFrame
3. [strategy_resolver.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/strategy_resolver.py) → `resolve_feature_strategy()`：**三层优先级**——
   - Priority 1: `feature_strategy.executable_featurizers` → 对每个名称调用 Registry 的 `resolve_to_available()` 进行 ID/Alias 解析 + 可用性校验
   - Priority 2: `feature_strategy.recommended_featurizers`（legacy 兼容）→ 通过 Registry aliases 解析
   - Priority 3: Registry fallback → 调用 `get_default_fallback()` 获取该模态下最高优先级的可用 Featurizer
4. [featurizer_router.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/featurizer_router.py) → `get_executable_featurizers()`：将解析后的 Registry ID 列表映射到实际可执行的 Featurizer 类实例（懒加载 + 单例缓存）
5. `_run_featurizers()` 方法（分两种模式）：
   - **多 Featurizer 模式**（有 `executable_featurizers` 时）：并行运行多个 Featurizer，每个列名以 `{featurizer_id}__` 为前缀避免冲突，水平合并（`pd.concat(axis=1)`），去重列名
   - **单 Featurizer 模式**（legacy fallback）：回退到按 `input_modality` 的简单分发（CompositionFeaturizer/DescriptorFeaturizer/StructureFeaturizer）
6. [feature_matrix_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/feature_matrix_builder.py) → `build_feature_matrix()`：合并 sample_id + features + target，清除非数值列
7. [feature_quality_checker.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/checkers/feature_quality_checker.py) → `check_feature_quality()`：缺失值/常量特征/无效特征/高缺失率特征
8. [artifact_manager.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/artifact_manager.py) → `save_feature_artifact()`：保存特征矩阵到 `{FEATURE_ARTIFACT_DIR}/{fe_id}/features.parquet`（或 CSV fallback），生成 `metadata.json` 和预览 JSON
9. [feature_matrix_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/feature_matrix_builder.py) → `get_feature_schema()`：特征分类统计（numeric/categorical/constant/all_missing）
10. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/builder.py) → `build_feature_engineering_object()`：构建完整的 FeatureEngineering Object（含 `downstream_input`）
11. 创建 `FeatureEngineering` → [repository.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/repository.py) → 入库

**可用 Featurizer 清单**：

| Registry ID | 实现类 | 状态 | 依赖 | 输出维度 |
|-------------|--------|------|------|----------|
| `basic_composition` | `CompositionFeaturizer` | always available | 无 | 16 |
| `pymatgen_composition_parser` | `PymatgenCompositionParserFeaturizer` | pymatgen installed | pymatgen | 0（中间件） |
| `matminer_stoichiometry` | `MatminerStoichiometryFeaturizer` | matminer+pymatgen | pymatgen, matminer | ~8 |
| `matminer_element_property` | `MatminerElementPropertyFeaturizer` | matminer+pymatgen | pymatgen, matminer | 132 |
| `matminer_magpie` | `MatminerMagpieFeaturizer` | matminer+pymatgen | pymatgen, matminer | 132 |
| `matminer_valence_orbital` | `MatminerValenceOrbitalFeaturizer` | matminer+pymatgen | pymatgen, matminer | 4 |
| `descriptor_passthrough` | `DescriptorFeaturizer` | always available | 无 | variable |
| `descriptor_cleaner` | `DescriptorCleanerFeaturizer` | always available | 无 | variable |
| `structure_placeholder` | `StructureFeaturizer` | planned | pymatgen, matminer | N/A |
| `pymatgen_structure_parser` | None | planned | pymatgen | N/A |
| `matminer_structure_basic` | `MatminerStructureBasicFeaturizer` | planned | pymatgen, matminer | ~10 |

**输出**：`FeatureEngineeringResponse`，包含 feature_generation/feature_matrix/feature_schema/feature_quality/preprocessing_requirements/downstream_input

**关键设计**：
- **多 Featurizer 并行执行**：每个 Featurizer 独立运行，即使单个失败也继续，只有全部失败才标记为 failed
- **列名前缀机制**：`{featurizer_id}__{original_name}` 避免不同 Featurizer 之间的列名冲突
- **Registry 驱动**：`featurizer_router.py` 通过懒初始化 + 单例模式管理所有 Featurizer 实例，新增 Featurizer 只需三步：1) 在 Registry 注册 2) 实现 BaseFeaturizer 子类 3) 在 `featurizer_router.py` 的 `_ROUTER` 字典中添加映射
- **Artifact 持久化**：支持 Parquet（pyarrow）和 CSV 双格式，预览 JSON 兼容 PostgreSQL JSONB（NaN/Inf 替换为 None）

**数据库表**：`feature_engineering`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/model.py)），包含 input_modality/feature_type/n_samples/n_features/target_column/artifact_id/artifact_path/is_ready_for_pipeline 等专项列 + `feature_json` + `preview_json` (JSONB)

**完成度**：~85%。5 个 Featurizer 可用（含 matminer 四个），多 Featurizer 并行执行完成。但 Structure Featurizer 仍为 planned 状态（placeholder），matminer Magpie 在未安装 pymatgen/matminer 时不可用。Descriptor clean 功能仅初步实现。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/service.py)、[context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/context_builder.py)、[data_loader_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/data_loader_adapter.py)、[strategy_resolver.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/strategy_resolver.py)、[feature_matrix_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/feature_matrix_builder.py)、[artifact_manager.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/artifact_manager.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/builder.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/repository.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/schemas.py)、[enums.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/enums.py)、[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/exceptions.py)、[registry_api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/registry_api.py)、所有 featurizers/ 目录下的文件

---

### 5.6 Featurizer Registry（共享能力注册表）

**功能描述**：作为 Workflow Planning 和 Feature Engineering 之间的**共享契约**，定义系统中所有 Featurizer 的元数据（ID/别名/状态/依赖/输入模态/预估维度），提供统一的查询、解析和回退 API。

**核心能力**（[featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py)）：
- **12 个 FeaturizerSpec 静态定义**（7 个 available + 5 个 planned）
- **依赖检测**：在模块导入时自动检测 pymatgen/matminer/scikit-learn/pyarrow/scipy 的安装状态并缓存
- **双重索引**：ID 索引 `_id_index` + 别名索引 `_alias_index`（如 `"magpie"` → `"matminer_magpie"`）
- **有效状态计算**：`get_featurizer_effective_status()` —— 即使 Registry 声明为 "available"，若依赖未安装则返回 "unavailable"
- **查询 API**：`get_available_featurizers(input_modality, task_type, feature_type)` —— 按多维过滤、按 fallback_priority 降序排序
- **名称解析**：`resolve(name)` —— 支持 ID 或 alias 输入 → `FeaturizerResolveResult`
- **三级回退**：`get_default_fallback(input_modality, task_type)` → `FeaturizerFallbackResult`

**API 端点**（[registry_api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/registry_api.py)）：
- `GET /api/registries/featurizers` — 多维度查询（input_modality/task_type/status/feature_type/requires_dependency/mvp_supported）
- `GET /api/registries/featurizers/validate` — 注册表自检
- `GET /api/registries/featurizers/{featurizer_id}` — 单个 Featurizer 详情（含 effective_status）
- `GET /api/registries/featurizers/dependencies` — 依赖安装状态查询

**完成度**：~90%。定义完整，查询 API 健全，别名解析完善。但 `get_default_fallback` 函数在 registry API 中有调用但尚未实现（当前代码中 workflow validator 调用了 `get_default_fallback` 但 featurizer_registry.py 中该函数定义待确认——根据当前代码推测该函数可能尚未完全实现或为简化版本）。

---

## 6. 系统数据流与调用链路

### 6.1 端到端数据流

```
用户操作              前端组件                      后端 API                       数据库表              外部服务
────────              ──────                       ────────                      ──────              ──────
填写表单 → TaskSpecificationForm.tsx → POST /api/tasks → task_specification ─┐
                                           │                                    │
                                     [normalizer.py]                           │
                                     [validator.py]                            │
                                     [builder.py]                              │
                                           ↓                                    │
点击 Run → TaskInterpretationPanel → POST /api/task-interpretations/ ─→ task_interpretation ─→ LLM API
                                           │                                    │
                                     [task_spec_adapter.py]                    │
                                     [prompt_builder.py]                       │
                                     [llm_client.py] ──────────────────────────────→ OpenAI
                                     [parser.py]                               │
                                     [validator.py]                            │
                                     [builder.py]                              │
                                           ↓                                    │
上传文件 → FileUpload.tsx → POST /api/dataset-profiles/upload → 本地磁盘
                                           │
点击 Run → DatasetProfilePanel → POST /api/dataset-profiles/{task_id} → dataset_profile
                                           │
                                     [context_builder.py](跨 task + interp 表)
                                     [source_resolver.py]
                                     [matbench/file_loader.py] ───→ Matbench / 本地文件
                                     [schema/modality/quality/target_checker.py]
                                     [profiler.py]
                                     [builder.py]
                                           ↓
点击 Run → WorkflowPlanPanel → POST /api/workflow-plans/{task_id} → workflow_plan ─→ LLM API
                                           │
                                     [context_builder.py](跨 task + interp + profile 表)
                                     [prompt_builder.py](动态注入 Featurizer Registry 列表)
                                     [llm_client_adapter.py] ─────────────────────────→ OpenAI
                                     [parser.py]
                                     [validator.py](含 Featurizer Registry 校验)
                                     [builder.py]
                                           ↓
点击 Run → FeatureEngineeringPanel → POST /api/feature-engineering/{task_id} → feature_engineering
                                           │
                                     [context_builder.py](跨 task+interp+profile+plan 表)
                                     [data_loader_adapter.py](复用模块三 Loader)
                                     [strategy_resolver.py](Featurizer Registry 解析)
                                     [featurizer_router.py](Registry ID→实例路由)
                                     [featurizers/*.py](执行特征化)
                                     [feature_matrix_builder.py]
                                     [feature_quality_checker.py]
                                     [artifact_manager.py] → /app/artifacts/features/
                                     [builder.py]
                                           ↓
                                   (Pipeline Generation — 尚未实现)
```

### 6.2 关键调用链细节

**模块五的 Featurizer 选择链**（核心链路）：
```
WorkflowPlan.feature_strategy.executable_featurizers
    → strategy_resolver.resolve_feature_strategy()
        → Registry.resolve_to_available(name, input_modality)
            → ID index lookup → Alias index lookup → available status check
    → featurizer_router.get_executable_featurizers(selected_ids, input_modality)
        → Registry.get_featurizer_by_id(fid) → effective_status check
        → get_featurizer_instance(fid) → lazy init + singleton cache
    → instance.featurize(raw_df, context, resolved_strategy)
        → 每个 Featurizer 独立运行，失败不阻塞其他
        → pandas.concat(axis=1) + 列去重
```

**Featurizer Registry 集成点**（三个消费方）：
1. **Workflow Planning prompt_builder.py** — 运行时获取 `get_available_featurizers()` + `get_planned_featurizers()` 列表注入 LLM Prompt
2. **Workflow Planning validator.py** — `_check_featurizer_registry()` 校验 LLM 输出的 `executable_featurizers`
3. **Feature Engineering strategy_resolver.py** — 三步优先级解析（executable → recommended → fallback）

---

## 7. 核心代码与关键设计说明

### 7.1 分层架构模式

每个业务模块遵循**完全一致的分层结构**，这是项目最重要的代码规范：

```
模块目录/
├── api.py              # API 路由层（APIRouter + HTTP 端点 + 异常→HTTP 状态码映射）
├── schemas.py          # Pydantic 请求/响应模型（BaseModel）
├── service.py          # 业务编排层（Service 类，方法拼装各组件）
├── model.py            # SQLModel 数据库表定义（table=True, JSONB 列, 索引）
├── repository.py       # 数据访问层（CRUD + 查询方法）
├── builder.py          # Object 构建器（dict → 完整 JSON 输出）
├── context_builder.py  # 上游上下文构建器（跨表查询 + 状态校验）
├── prompt_builder.py   # LLM Prompt 构建器（模块二和四特有）
├── parser.py           # LLM 响应解析器（模块二和四特有）
├── validator.py        # 输入/输出校验器
├── enums.py            # 枚举定义
└── exceptions.py       # 模块专用异常
```

### 7.2 数据库设计

- **5 张业务表**：`task_specification` / `task_interpretation` / `dataset_profile` / `workflow_plan` / `feature_engineering`
- **通用模式**：每张表都包含 `id`（格式 `{prefix}_{uuid8}`）、`task_id`（关联键）、`status`（索引列）、`created_at`/`updated_at`
- **JSONB 列**：所有表均有 `*_json` 列存储完整的模块输出。关键查询字段（如 task_type、input_modality、status）有独立列 + 索引
- **建表方式**：`main.py` 的 `on_startup` 事件中调用 `SQLModel.metadata.create_all(engine)` 自动建表，未使用 Alembic 迁移
- **Session 管理**：FastAPI `Depends(get_session)` 依赖注入，`with Session(engine) as session` 上下文管理

### 7.3 异常体系

**三层异常层次**：
```
Exception
  └── BusinessException (shared/common/exceptions.py, error_code="BUSINESS_ERROR")
        ├── ValidationException ("VALIDATION_ERROR")
        ├── NotFoundException ("NOT_FOUND")
        ├── DatabaseException ("DATABASE_ERROR")
        ├── TaskInterpretationException ("TASK_INTERPRETATION_ERROR")
        │     ├── TaskNotReadyException ("TASK_NOT_READY")
        │     ├── LLMCallException ("LLM_CALL_FAILED")
        │     ├── LLMOutputParseException ("LLM_OUTPUT_PARSE_ERROR")
        │     ├── LLMOutputValidationException ("LLM_OUTPUT_VALIDATION_ERROR")
        │     └── InterpretationNotFoundException ("INTERPRETATION_NOT_FOUND")
        ├── DatasetProfileException (类似子类)
        ├── WorkflowPlanningException (类似子类)
        ├── FeatureEngineeringException (20 个子类)
        └── FeaturizerRegistryException (5 个子类)
```

**全局异常处理**：`main.py` 中注册了两个 handler：
- `BusinessException` → HTTP 400，返回 `{"success": false, "message": ..., "error_code": ...}`
- `Exception` → HTTP 500，返回 `{"success": false, "message": "Internal server error.", "error_code": "INTERNAL_ERROR"}`

### 7.4 API 设计规范

- **统一响应格式**：所有接口返回 `ApiResponse { success: bool, message: str, data: any, error_code: str? }`
- **路由前缀**：`/api/tasks/`、`/api/task-interpretations/`、`/api/dataset-profiles/`、`/api/workflow-plans/`、`/api/feature-engineering/`、`/api/registries/`
- **每个模块的 4 个标准端点**：`POST /.../{task_id}`（创建）、`GET /.../{id}`（按 ID 查询）、`GET /api/tasks/{task_id}/...`（按 Task ID 查询最新）、`POST /.../{task_id}/rerun`（重新执行）
- **文件上传**：`POST /api/dataset-profiles/upload`（multipart/form-data）

### 7.5 LLM 集成设计

| 组件 | 角色 | 文件 |
|------|------|------|
| `LLMClient`（模块二） | 原始 httpx 封装，含重试逻辑 | [llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py) |
| `WorkflowPlanningLLMAdapter`（模块四） | 复用 `LLMClient`，添加日志和请求信息封装 | [llm_client_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/llm_client_adapter.py) |
| Prompt Builder（模块二） | 168 行 system/user prompt + 完整 JSON Schema | [prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py) |
| Prompt Builder（模块四） | 250 行 prompt + 动态 Registry 列表注入 + 10 条 BOUNDARY RULES | [prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py) |

**LLM 配置**（[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)）：
- `LLM_PROVIDER="openai"`, `LLM_MODEL="gpt-4.1"`
- `LLM_BASE_URL="https://api.openai.com/v1"`（兼容任何 OpenAI-API 兼容端点，如 Qwen/DeepSeek）
- `LLM_TIMEOUT=60`, `LLM_MAX_RETRIES=2`, `LLM_TEMPERATURE=0.0`

### 7.6 前端架构

- **单页面应用**：[index.tsx](file:///c:/projects/MLAgent/frontend/src/index.tsx) 只渲染 `<TaskSpecificationPage />`
- **面板嵌入模式**：[TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) 在表单提交成功后（`status === 'valid' || 'valid_with_warning'`）条件渲染 4 个下游面板
- **UI = 表单 + 流程**：所有 5 个面板纵向排列在同一页面，用户可顺序操作
- **API 客户端**：axios 单例，全局 request/response 拦截器用于日志，超时 120s（Feature Engineering 专属 600s）
- **前端类型**：5 个 `types.ts` 文件定义了对应的 TypeScript 类型，与后端 Pydantic Schema 对应

---

## 8. 当前未完成部分与后续开发建议

### 8.1 尚未实现的模块

| 模块 | 说明 | 优先级 |
|------|------|--------|
| **Pipeline Generation** | Feature Engineering 的 `downstream_input` 已为此准备（`ready_for_pipeline_generation` 标志），但 Pipeline Generation 业务逻辑尚未开始 | 最高 |
| **Pipeline Execution** | 将 Pipeline 转换为可执行代码或脚本 | 高 |
| **Metric Evaluation** | 对 Pipeline 执行结果进行评估 | 高 |
| **Result Diagnosis** | 对不好的结果进行诊断和重试建议 | 中 |
| **Report Generation** | 最终报告生成 | 中 |
| **用户认证/多租户** | 当前无身份验证，所有 task 对所有人可见 | 中 |
| **异步任务队列** | 模块三/四/五（特别是五的 matminer 特征化）执行时间长（可达数分钟），当前为同步 HTTP 调用，长期执行可能导致超时 | 中 |

### 8.2 半成品代码

| 位置 | 问题描述 | 建议 |
|------|----------|------|
| `featurizer_registry.py` 中的 `get_default_fallback()` | 被 validator.py 和 strategy_resolver.py 引用，但 featurizer_registry.py 中该函数的完整实现可能未完成或为简化版本 | 需要确认并完善该函数 |
| `featurizer_router.py` 中的 `pymatgen_structure_parser` | 映射到 `None`，表示该功能尚未实现 | 未来需实现对应的 Featurizer 类 |
| `structure_featurizer.py` | 占位符实现，不产生实际特征 | 需完整实现结构特征化 |
| `matminer_structure_basic.py` | 类已实现但 Registry 中标记为 `planned`，未被 router 激活 | 当需要结构特征时启用 |
| `strategy_resolver.py` 中 `get_planned_featurizers` | 被 prompt_builder.py 引用但 featurizer_registry.py 中该函数定义待确认 | 确认并完善 |

### 8.3 潜在问题

1. **LLM 完全依赖**：模块二和模块四完全依赖 LLM API，如果 LLM 不可用或返回不符合 Schema 的 JSON，整个管道将中断。建议未来增加规则化的 fallback 逻辑。

2. **同步执行瓶颈**：所有模块的创建接口均为同步 HTTP 调用，模块五的 matminer 特征化可能需要数分钟。当前前端设置了 600s 超时，但长期来看应该改为异步任务队列（如 Celery）。

3. **数据库迁移**：当前使用 `SQLModel.metadata.create_all` 自动建表（开发模式），生产环境应使用 Alembic 管理迁移。项目已安装 alembic 但未初始化。

4. **文件存储路径**：上传文件存储在 `/app/uploads`（Docker 容器内），需要后续挂载 volume 确保持久化。

5. **Featurizer Registry 硬编码**：12 个 FeaturizerSpec 均为 Python 代码中硬编码，无法通过配置文件或数据库动态添加。如果未来 Featurizer 数量大幅增长，需要考虑配置化。

6. **前端路由缺失**：当前为单一页面，所有面板都在同一页面中。当用户操作完任务规格后想直接查看某个历史任务结果时，需要刷新页面重新添加。未来需要前端路由（如 React Router）。

---

## 9. 给后续 AI Coding 大模型的开发提示

### 9.1 优先阅读的文件（按重要性排序）

| 序号 | 文件 | 理由 |
|------|------|------|
| 1 | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | 全局入口，理解路由注册和异常处理 |
| 2 | [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) | 所有配置项，控制整个系统行为 |
| 3 | [featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py) | Featurizer 共享契约，模块四、五和前端都依赖它 |
| 4 | [service.py (feature_engineering)](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/service.py) | 最复杂的业务编排，理解数据流和 Featurizer 调度 |
| 5 | [validator.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/validator.py) | 理解 LLM 输出的严格约束 |
| 6 | [prompt_builder.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py) | 理解 LLM Prompt 的设计哲学 |
| 7 | [context_builder.py (feature_engineering)](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/context_builder.py) | 理解跨模块状态校验模式 |
| 8 | [strategy_resolver.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/strategy_resolver.py) | 理解 Featurizer 选择的三层优先级逻辑 |
| 9 | [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) | 前端入口，理解 UI 结构和面板嵌入模式 |

### 9.2 继续开发时的边界注意事项

1. **新增 Featurizer 的标准流程**：
   - Step 1: 在 [featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py) 的 `_FEATURIZERS` 列表中添加 `FeaturizerSpec`
   - Step 2: 在 `featurizers/` 目录下创建 `BaseFeaturizer` 子类，实现 `featurize()` 和 `featurizer_name()` 方法
   - Step 3: 在 [featurizer_router.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/featurizer_router.py) 的 `_ROUTER` 字典中注册映射
   - **不要**在 Workflow Planning 的 prompt/validator 或 Feature Engineering 的 strategy_resolver 中硬编码新的 Featurizer 名称

2. **不要重复实现的功能**：
   - **数据加载**：已有 `MatbenchLoader` 和 `FileLoader`，新模块如需加载数据应复用模块三的 Loader（参考 `data_loader_adapter.py`）
   - **LLM 调用**：已有 `LLMClient`（模块二），新模块应复用（参考 `llm_client_adapter.py`）
   - **统一响应格式**：所有 API 接口必须使用 `success_response()` / `error_response()`
   - **异常处理**：新异常应继承 `BusinessException` 或其子类，设置语义化 `error_code`

3. **模块间数据传递规范**：
   - 模块间的数据传递通过 **数据库表** 进行，不是内存对象
   - 下游模块的 `context_builder.py` 通过 Repository 跨表查询上游数据
   - 下游模块必须在开始处理前校验上游模块的状态（如 `status in ("valid", "valid_with_warning")`）

4. **LLM 交互规范**（如果新模块需要使用 LLM）：
   - 必须定义严格的 JSON Schema
   - 必须有 parser（JSON 提取）+ validator（Schema 校验）两步
   - 禁止内容检测（`FORBIDDEN_CONTENT` 列表）应在前置 prompt rules 中声明
   - 失败时写入数据库，包含 `llm_request_json` + `llm_response_json` + `error_message`

5. **前端开发规范**：
   - 所有 API 客户端函数遵循 `{action}{Resource}` 命名（如 `createTask`, `getLatestInterpretation`）
   - 每个模块的 `types.ts` 定义完整的 TypeScript 类型
   - 面板组件以 `{Module}Panel.tsx` 命名，接受 `taskId` prop
   - axios 实例从 `taskApi.ts` 导入，不要在各自文件中创建新实例

### 9.3 建议的 Pipeline Generation 模块实现方向

根据当前项目架构和输出，Pipeline Generation 模块应该：
- 消费 Feature Engineering 的 `downstream_input`（含 `feature_matrix_artifact_id`/`target_column`/`task_type`/`primary_metric` 等）
- 消费 Workflow Plan 的 `pipeline_generation_input`（含 `pipeline_steps`/`required_components`）
- 参考 Workflow Planning 的 LLM 调用模式生成 Pipeline
- 遵循现有的 `api.py → service.py → builder.py → model.py → repository.py` 分层模式
- 输出中包含可执行的 Pipeline 描述（可能使用 scikit-learn Pipeline 或其他框架）

### 9.4 技术债务提示

- `featurizer_registry.py` 中的 `get_default_fallback()` 和 `get_planned_featurizers()` 函数需要确认完整实现
- `enums.py` 中各模块使用了不同的枚举定义风格（模块一使用 `Enum` 类，模块四使用普通类常量），后续可以统一
- 前端没有 React Router，所有面板嵌入在一个页面中，历史任务查看不便
- 缺少 API 版本管理（如 `/api/v1/` 前缀）
- 缺少请求日志中间件和性能监控