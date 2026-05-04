# 项目已实现部分说明文档

> 文档生成日期：2026-05-04（全面更新版）
> 项目名称：MLAgent — AI-driven Automated Machine Learning Framework for Materials Science
> 文档用途：帮助后续 AI Coding 大模型和开发者快速理解当前项目已经完成的部分

---

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个面向材料科学领域的 AI 驱动自动化机器学习框架。其核心目标是让用户通过结构化表单提交材料机器学习任务需求，系统自动完成从**任务理解 → 数据加载 → 工作流规划 → 特征工程 → 特征预处理**的全流程自动化。当前尚未实现 Model Search / Pipeline Generation 及后续阶段。

### 1.2 当前实现阶段

当前项目已完成 **六个核心业务模块** 的端到端实现：

| 模块 | 阶段 | 完成度 |
|------|------|--------|
| **模块一：Task Specification（任务规格录入与校验）** | MVP 已完成 | ~95% |
| **模块二：LLM-based Task Interpretation（基于大模型的任务理解）** | MVP 已完成 | ~90% |
| **模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）** | MVP 已完成 | ~90% |
| **模块四：Workflow Planning（LLM 驱动的工作流规划）** | MVP 已完成 | ~90% |
| **模块五：Feature Engineering（特征工程）** | MVP 已完成 | ~85% |
| **模块六：Feature Preprocessing（特征预处理）** | MVP 已完成 | ~90% |
| **Featurizer Registry（共享能力注册表）** | MVP 已完成 | ~90% |

当前**尚未实现**的后续模块包括：Model Search、Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis、Report Generation 等。

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
    ├── Featurizers (Composition / Descriptor / Structure + pymatgen + matminer)
    │       ↓
    │   Feature Artifact (parquet/csv 存储到 /app/artifacts/features/)
    │
    └── Feature Preprocessing (Imputation → Scaling → Feature Selection)
            ↓
        Model-Ready Artifact (parquet + joblib pipeline 存储到 /app/artifacts/model_ready/)
```

### 1.4 核心设计原则（根据当前代码分析）

1. **管道式架构**：六个模块严格按序依赖。每个下游模块的 `context_builder.py` 会校验所有上游模块的输出状态，状态不符则抛出专用异常。
2. **统一异常体系**：所有业务异常继承自 `BusinessException`，每个模块有自己的异常子类，附带有语义化的 `error_code`。
3. **LLM 输出强约束**：模块二和模块四均定义了严格的 JSON Schema，LLM 响应经过解析（`parser.py`）+ 校验（`validator.py`）两步才被认为有效。
4. **Featurizer Registry 作为共享契约**：Workflow Planning 的 Prompt 和 Validator、Feature Engineering 的 Strategy Resolver 都向 Registry 查询，而非各自维护硬编码列表。
5. **失败状态持久化**：所有模块在失败时都会将失败记录（含错误信息）写入数据库，不会静默丢失。
6. **Artifact 传递链**：Feature Engineering 输出特征矩阵 artifact → Feature Preprocessing 加载并处理后输出 model-ready artifact + preprocessor pipeline artifact，供下游 Model Search 消费。

---

## 2. 当前目录结构说明

### 2.1 完整目录树（实际文件）

```
c:\projects\MLAgent/
├── backend/                                # 后端 FastAPI 项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI 入口，路由注册，CORS，异常处理，启动时建表
│   │   ├── modules/                       # 业务模块（六个模块 + Featurizer Registry API）
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
│   │   │   ├── feature_engineering/       # 模块五：特征工程
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # 5 个接口（POST, GET by id, GET by task, POST:/rerun, GET preview）
│   │   │   │   ├── registry_api.py       # Featurizer Registry 查询 API（GET list/detail/dependencies/validate）
│   │   │   │   ├── schemas.py            # FeatureGeneration/FeatureMatrixInfo/FeatureQuality/DownstreamInput 等
│   │   │   │   ├── service.py            # 编排：build_context → reload_data → resolve_strategy → run_featurizers → build_matrix → check_quality → save_artifact → persist
│   │   │   │   ├── model.py              # FeatureEngineering (JSONB + artifact_id/path)
│   │   │   │   ├── repository.py         # CRUD + get_latest_by_task_id
│   │   │   │   ├── context_builder.py    # 跨5个上游模块构建context（校验全部前置模块状态）
│   │   │   │   ├── data_loader_adapter.py# 复用 Dataset Profile 的 MatbenchLoader / FileLoader 重新加载原始数据
│   │   │   │   ├── strategy_resolver.py  # 特征策略解析：优先级1 executable → 2 legacy recommended → 3 Registry fallback
│   │   │   │   ├── feature_matrix_builder.py # 构建特征矩阵（sample_id + features + target）
│   │   │   │   ├── artifact_manager.py   # 特征矩阵持久化（parquet/csv）+ metadata.json + 预览生成
│   │   │   │   ├── builder.py            # 构建 FeatureEngineering Object
│   │   │   │   ├── enums.py              # FeatureEngineeringStatus/FeatureType/InputModality
│   │   │   │   ├── exceptions.py         # 20 个细分异常类型
│   │   │   │   ├── featurizers/          # 特征化器实现
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base_featurizer.py           # 抽象基类 BaseFeaturizer
│   │   │   │   │   ├── featurizer_router.py         # 注册表 ID → 可执行 Featurizer 实例的路由桥接
│   │   │   │   │   ├── composition_featurizer.py    # 内置轻量级 16 维元素属性描述符（103 种元素）
│   │   │   │   │   ├── descriptor_featurizer.py     # 已有数值描述符直通
│   │   │   │   │   ├── descriptor_cleaner.py        # 增强版描述符清洗器（含特征分组元数据）
│   │   │   │   │   ├── structure_featurizer.py      # 结构特征化器（占位符）
│   │   │   │   │   ├── pymatgen_composition_parser.py # pymatgen 配方解析器
│   │   │   │   │   ├── matminer_featurizers.py      # matminer 四大 Featurizer（Stoichiometry/ElementProperty/Magpie/ValenceOrbital）
│   │   │   │   │   └── matminer_structure_basic.py  # matminer 结构基本特征（planned）
│   │   │   │   └── checkers/            # 特征检查器
│   │   │   │       ├── __init__.py
│   │   │   │       └── feature_quality_checker.py   # 特征质量检查：缺失值/常量特征/无效特征/高缺失率
│   │   │   │
│   │   │   └── feature_preprocessing/    # 模块六：特征预处理
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 5 个接口（POST, GET by id, GET by task, POST:/rerun, GET preview）
│   │   │       ├── schemas.py            # FeaturePreprocessingCreateRequest, ValidationSummary, ModelSearchInput 等 15+ 个子对象
│   │   │       ├── service.py            # 10 步流水线：build_context → load_artifact → filter → validate_groups → execute → build_pipeline → save → build → persist
│   │   │       ├── model.py              # FeaturePreprocessing (JSONB + 15 个专项列 + 5 个上游 ID 索引)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id
│   │   │       ├── context_builder.py    # 跨 5 个上游模块构建 context（校验全部前置模块状态 + artifact_path 存在性）
│   │   │       ├── artifact_loader.py    # 加载 Feature Engineering 输出的特征矩阵 artifact（parquet/csv）
│   │   │       ├── column_validator.py   # 列级校验：无效列/全空列/常量列/高缺失列/Inf值检测
│   │   │       ├── feature_filter.py     # 特征过滤编排：顺序执行 5 类过滤（invalid → all_missing → constant → high_missing → inf）
│   │   │       ├── feature_group_validator.py # 特征组校验：按组统计保留/丢弃状态
│   │   │       ├── preprocessing_executor.py  # 预处理执行器：Imputation → Scaling → Feature Selection 三步流水线
│   │   │       ├── preprocessing_pipeline_builder.py # PreprocessingPipeline 复合管道类（可 joblib 序列化，含 transform 方法）
│   │   │       ├── artifact_manager.py   # Model-ready artifact 持久化（parquet + joblib pipeline + metadata.json + preview.json）
│   │   │       ├── builder.py            # 构建 FeaturePreprocessingResponse（含 model_search_input）
│   │   │       ├── enums.py              # FeaturePreprocessingStatus / ImputationStrategy / ScalingStrategy / FeatureSelectionStrategy 等
│   │   │       ├── exceptions.py         # 12 个专用异常（UpstreamNotReady/ArtifactLoad/ImputationFailed/ScalingFailed 等）
│   │   │       └── preprocessors/        # 预处理器实现
│   │   │           ├── __init__.py
│   │   │           ├── imputer.py        # sklearn SimpleImputer 封装（median/mean/most_frequent）
│   │   │           ├── scaler.py         # sklearn Scaler 封装（Standard/Robust/MinMax）
│   │   │           ├── encoder.py        # 编码器（占位，当前未启用）
│   │   │           └── feature_selector.py # sklearn VarianceThreshold 封装
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
│   │       │   └── settings.py          # pydantic-settings：数据库/LLM/数据上传/特征工程/特征预处理/外部库 配置
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── connection.py        # SQLModel Engine 创建（单行，基于 DATABASE_URL）
│   │       │   └── session.py           # FastAPI Depends get_session 依赖注入（generator）
│   │       └── registry/               # Featurizer Registry（共享核心）
│   │           ├── __init__.py
│   │           ├── featurizer_registry.py # 11 个 FeaturizerSpec 静态定义 + 依赖检测 + ID/Alias 索引 + 查询 API + 回退逻辑
│   │           ├── schemas.py           # FeaturizerSpec / FeaturizerResolveResult / FallbackResult / DependencyCheckResult
│   │           └── exceptions.py        # 5 个 Registry 异常
│   │
│   ├── .env.example                     # 环境变量模板
│   ├── requirements.txt                 # Python 依赖
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
│   │   │   ├── featureEngineeringApi.ts # Feature Engineering API（超时 600s）+ Featurizer Registry API
│   │   │   └── featurePreprocessingApi.ts # Feature Preprocessing API（超时 600s）
│   │   └── modules/
│   │       ├── taskSpecification/
│   │       │   ├── pages/
│   │       │   │   └── TaskSpecificationPage.tsx  # 页面组件（蓝色 Header + 白色表单）
│   │       │   ├── components/
│   │       │   │   ├── TaskSpecificationForm.tsx  # 主表单组件（react-hook-form + Zod 校验，6 个面板嵌入）
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
│   │       ├── featureEngineering/
│   │       │   ├── components/
│   │       │   │   └── FeatureEngineeringPanel.tsx  # 特征工程展示面板（含多 featurizer 结果、特征组展示）
│   │       │   └── types.ts
│   │       └── featurePreprocessing/
│   │           ├── components/
│   │           │   ├── FeaturePreprocessingPanel.tsx  # 特征预处理主面板（含 Run/Re-run/Refresh 按钮）
│   │           │   ├── ValidationSummaryCard.tsx      # 验证摘要卡片（样本数/特征数/丢弃数/就绪状态）
│   │           │   ├── ColumnFilteringCard.tsx        # 列过滤详情卡片（5 类丢弃原因分组展示）
│   │           │   ├── PreprocessingExecutionCard.tsx # 预处理执行详情卡片（Imputation/Scaling/Selection 状态）
│   │           │   └── ModelReadyArtifactCard.tsx     # Model-ready artifact 卡片（含预览按钮）
│   │           ├── constants.ts          # 状态标签/颜色/丢弃原因映射
│   │           └── types.ts              # 完整的 TypeScript 类型定义（与后端 Pydantic Schema 对应）
│   ├── package.json                     # 依赖（React 18 + axios + react-hook-form + zod + antd 等）
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
    ├── prd-6.md / prd-6-技术实现方案.md
```

### 2.2 关键文件职责速查表

| 文件路径 | 核心职责 | 行数约 |
|----------|----------|--------|
| [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | FastAPI 应用入口，注册 7 个 Router，CORS，全局异常处理，启动建表 | 67 |
| [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) | 所有环境变量配置（LLM/DB/上传/特征工程/特征预处理/外部库） | 70 |
| [featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py) | 11 个 FeaturizerSpec 静态定义 + 依赖检测 + ID/Alias 解析 + 查询/回退 API | ~500 |
| [prompt_builder.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py) | 超长 LLM prompt 构建（含完整 JSON Schema 定义 + 10 条 CRITICAL 规则 + 动态 Featurizer 列表注入） | ~250 |
| [validator.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/validator.py) | 最严格的 LLM 输出校验（12 个维度的必填字段 + 枚举值 + 禁止代码 + Featurizer Registry 校验） | ~236 |
| [service.py (feature_engineering)](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/service.py) | 最复杂的业务编排（11 步流水线），理解数据流和 Featurizer 调度 | ~300 |
| [service.py (feature_preprocessing)](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/service.py) | 特征预处理 10 步流水线编排（含失败即入库的错误处理模式） | ~300 |
| [context_builder.py (feature_preprocessing)](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/context_builder.py) | 跨 5 个上游模块状态校验 + artifact_path 存在性检查 | ~141 |
| [preprocessing_executor.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_executor.py) | Imputation → Scaling → Feature Selection 三步执行器 | ~145 |
| [preprocessing_pipeline_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_pipeline_builder.py) | PreprocessingPipeline 复合管道类（可序列化 + transform 推理方法） | ~81 |
| [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) | 前端入口表单，提交后条件渲染 5 个下游面板 | ~300 |

---

## 3. 当前系统输入与输出

### 3.1 系统输入

| 输入项 | 来源 | 格式 | 说明 |
|--------|------|------|------|
| 任务规格表单 | 用户通过 Web UI 填写 | JSON（12 个字段） | 包含 task_name, task_description, material_system, prediction_target, task_type, dataset_description, input_type, target_column, evaluation_metric, user_priority, constraints |
| 数据集文件（可选） | 用户上传 | CSV / XLSX / XLS | 通过 Dataset Profile 模块的 FileUpload 组件上传 |
| 外部数据集名称 | 用户输入或 LLM 推断 | 字符串 | 如 "matbench_expt_gap"，由 MatbenchLoader 加载 |
| LLM API 响应 | 外部 LLM 服务 | JSON（符合预定义 Schema） | 模块二和模块四依赖 LLM 生成结构化输出 |

### 3.2 系统输出

| 输出项 | 目标 | 格式 | 说明 |
|--------|------|------|------|
| TaskSpecificationResponse | 前端展示 + 下游模块 | JSON | 含 task_id, status, validation_warnings, task_spec_json |
| TaskInterpretationResponse | 前端展示 + 下游模块 | JSON | 含 interpreted_task_type, input_modality, modeling_intent, dataset_intent 等 |
| DatasetProfileResponse | 前端展示 + 下游模块 | JSON | 含 data_quality, target_profile, workflow_planning_input, preview_json |
| WorkflowPlanResponse | 前端展示 + 下游模块 | JSON | 含 8 个策略维度 + pipeline_generation_input |
| FeatureEngineeringResponse | 前端展示 + 下游模块 | JSON + Parquet/CSV 文件 | 含 feature_matrix, feature_quality, downstream_input + artifact 文件 |
| FeaturePreprocessingResponse | 前端展示 + 下游模块 | JSON + Parquet + Joblib 文件 | 含 validation_summary, model_search_input + model_ready artifact + preprocessor pipeline |
| Featurizer Registry 查询结果 | 前端展示 + 内部模块 | JSON | 含 11 个 FeaturizerSpec 的元数据、状态、依赖信息 |

---

## 4. 当前技术栈说明

### 4.1 后端技术栈

| 技术 | 版本（根据当前代码推测） | 承担作用 |
|------|--------------------------|----------|
| **Python** | 3.11+ | 主编程语言 |
| **FastAPI** | 0.100+ | Web 框架，提供路由、依赖注入、自动 OpenAPI 文档 |
| **SQLModel** | 0.0.14+ | ORM，统一 SQLAlchemy + Pydantic，用于数据库模型定义和查询 |
| **Pydantic** | 2.0+ | 数据校验和序列化（Request/Response Schema） |
| **pydantic-settings** | 2.0+ | 环境变量管理（Settings 类） |
| **httpx** | 0.24+ | 异步 HTTP 客户端，用于调用 LLM API |
| **Pandas** | 2.0+ | 数据处理核心（DataFrame 操作、数据加载、特征矩阵构建） |
| **scikit-learn** | 1.3+ | 机器学习预处理（SimpleImputer, StandardScaler, VarianceThreshold 等） |
| **joblib** | 1.3+ | 预处理器 Pipeline 序列化/反序列化 |
| **pymatgen** | 2024+ | 材料科学工具包（配方解析、元素属性查询），可选依赖 |
| **matminer** | 0.9+ | 材料数据挖掘（Stoichiometry/ElementProperty/Magpie/ValenceOrbital Featurizer），可选依赖 |
| **pyarrow** | 14+ | Parquet 格式读写，可选依赖 |
| **PostgreSQL** | 16 | 关系型数据库，存储所有模块的运行结果 |
| **psycopg2-binary** | 2.9+ | PostgreSQL 数据库驱动 |
| **Uvicorn** | 0.24+ | ASGI 服务器，运行 FastAPI 应用 |
| **alembic** | 1.13+ | 数据库迁移工具（已安装但未初始化） |

### 4.2 前端技术栈

| 技术 | 版本（根据当前代码推测） | 承担作用 |
|------|--------------------------|----------|
| **React** | 18 | UI 框架 |
| **TypeScript** | 5.x | 类型安全 |
| **axios** | 1.6+ | HTTP 客户端，含 request/response 拦截器 |
| **react-hook-form** | 7.x | 表单状态管理和校验 |
| **zod** | 3.x | Schema 校验（前端表单校验） |
| **@hookform/resolvers** | 3.x | 连接 zod 和 react-hook-form |
| **antd** | 5.x | UI 组件库（Card, Button, Tag, Descriptions, Spin, Alert, Table 等） |
| **@ant-design/icons** | 5.x | 图标库 |

### 4.3 基础设施

| 技术 | 承担作用 |
|------|----------|
| **Docker** | 容器化（backend + frontend + db 三服务） |
| **Docker Compose** | 多服务编排 |
| **PostgreSQL 16** | 数据库（docker-compose 中的 db 服务） |

---

## 5. 已实现功能模块

### 5.1 模块一：Task Specification（任务规格录入与校验）

**功能描述**：接收用户通过 Web 表单提交的材料 ML 任务需求，进行标准化、校验、构建和持久化。

**输入**：
- 用户通过 [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) 提交的 12 个字段（task_name, task_description, material_system, prediction_target, task_type, dataset_description, input_type, target_column, evaluation_metric, user_priority, constraints）

**处理逻辑**（调用链）：
1. [api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) → `POST /api/tasks`
2. [service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) → `create_task()` 方法编排 5 步流程
3. [normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py) → `normalize_task_specification()`：字段标准化映射（task_type/input_type/metric/priority 的别名映射）
4. [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) → `validate_task_specification()`：必填字段校验、指标兼容性校验、输入一致性校验、警告生成
5. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/builder.py) → `build_task_specification()`：构建 task_spec JSON dict
6. [repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py) → 入库

**输出**：`TaskSpecificationResponse`，状态为 `valid` / `valid_with_warning` / `invalid` / `incomplete`

**数据库表**：`task_specification`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)），包含 task_name/task_type/input_type/target_column/evaluation_metric/status 等专项列 + `task_spec_json` (JSONB)

**完成度**：~95%。表单校验完善，标准化映射覆盖常见别名。但 constraints 字段仅做字符串数组存储，未做结构化解析。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py)、[normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py)、[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/builder.py)

---

### 5.2 模块二：LLM-based Task Interpretation（基于大模型的任务理解）

**功能描述**：将 Task Specification 送入 LLM，生成结构化的任务理解结果，包括预测目标分类、建模意图、数据需求等。

**输入**：
- Task Specification（状态为 `valid` 或 `valid_with_warning`）
- LLM API（OpenAI 兼容接口）

**处理逻辑**（调用链）：
1. [api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py) → `POST /api/task-interpretations/{task_id}`
2. [task_spec_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/task_spec_adapter.py) → `adapt_task_specification()`：将 DB model 转为 LLM context dict
3. [prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py) → `build_prompt()`：构建 system + user prompt（含严格 JSON Schema）
4. [llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py) → `LLMClient.generate()`：httpx 调用 OpenAI 兼容 API（含重试逻辑，max_retries=2）
5. [parser.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/parser.py) → `parse_llm_response()`：正则去除 markdown 代码块，提取 JSON
6. [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/validator.py) → `validate_interpretation()`：结构/枚举值/置信度范围校验
7. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/builder.py) → `build_interpretation()`：构建 interpretation JSON dict
8. [repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/repository.py) → 入库

**输出**：`TaskInterpretationResponse`，状态为 `interpreted` / `interpreted_with_warning` / `failed`

**数据库表**：`task_interpretation`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py)），包含 interpreted_task_type/interpreted_input_modality/confidence_score/status 等专项索引列 + `interpretation_json` + `llm_request_json` + `llm_response_json` (JSONB)

**完成度**：~90%。LLM 调用、解析、校验链路完整。但完全依赖 LLM，无规则化 fallback。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/service.py)、[task_spec_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/task_spec_adapter.py)、[prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py)、[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)、[parser.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/parser.py)、[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/validator.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/builder.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/repository.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/schemas.py)、[enums.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/enums.py)、[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/exceptions.py)

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
9. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/builder.py) → `build_dataset_profile()`：汇总输出完整 JSON
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

**功能描述**：根据 Workflow Plan 中的 `feature_strategy`，重新加载原始数据，通过 Featurizer Registry + Featurizer Router 选择并执行特征化器，构建特征矩阵、质量检查、持久化 artifact，输出 `downstream_input` 供下游消费。

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

### 5.6 模块六：Feature Preprocessing（特征预处理）

**功能描述**：加载 Feature Engineering 输出的特征矩阵 artifact，执行特征过滤（无效列/全空列/常量列/高缺失列/Inf值）、特征组校验、预处理流水线（Imputation → Scaling → Feature Selection），最终输出 model-ready artifact 和可序列化的 preprocessor pipeline，同时生成 `model_search_input` 供下游 Model Search 模块消费。

**输入**：
- 全部五个上游模块的输出（状态校验过）
- Feature Engineering 的 `artifact_path`（指向特征矩阵 parquet/csv 文件）
- 用户可选配置参数（通过 `FeaturePreprocessingCreateRequest`）

**处理逻辑**（完整的 10 步流水线，见 [service.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/service.py) 的 `create_feature_preprocessing()` 方法）：

1. [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/context_builder.py) → `build_preprocessing_context()`：跨 5 个上游模块（Task/Interpretation/Profile/Plan/FeatureEngineering）构建统一 context，校验每个上游模块的状态（valid/interpreted/profiled/planned/completed），并检查 `artifact_path` 是否存在。状态不符则抛出 `FeaturePreprocessingUpstreamNotReadyException` 并写入 BLOCKED 状态记录。

2. [artifact_loader.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/artifact_loader.py) → `load_raw_feature_matrix()`：从 Feature Engineering 的 artifact 路径加载原始特征矩阵（支持 parquet 和 csv 格式），自动识别 target_column（最后一列）和 candidate_feature_columns（排除 sample_id 和 target 后的所有列）。

3. [feature_filter.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/feature_filter.py) → `filter_features()`：顺序执行 5 类特征过滤：
   - **无效特征**（[column_validator.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/column_validator.py) → `identify_invalid_features()`）：丢弃非数值对象列（object/datetime/dict/list 类型）和已知中间列（如 `_pymatgen_composition`）
   - **全空特征**（`identify_all_missing_features()`）：丢弃所有值均为 NaN 的列
   - **常量特征**（`identify_constant_features()`）：丢弃只有单一非空值的列
   - **高缺失特征**（`identify_high_missing_features()`）：丢弃缺失率超过 `max_missing_ratio`（默认 0.5）的列
   - **Inf值处理**（`handle_invalid_inf_values()`）：丢弃包含 Inf/-Inf 值的列

4. [feature_group_validator.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/feature_group_validator.py) → `validate_feature_groups()`：按特征组（来自 Feature Engineering 的 `feature_schema.feature_groups`）统计保留/丢弃状态，生成每组的状态（retained/retained_with_warning/dropped）。

5. [preprocessing_executor.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_executor.py) → `execute_preprocessing()`：执行三步预处理流水线：
   - **Step 1 - Imputation**：使用 [imputer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/imputer.py) 的 `Imputer` 类（封装 sklearn `SimpleImputer`），支持 median/mean/most_frequent 策略，仅对有缺失值的列执行
   - **Step 2 - Scaling**：使用 [scaler.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/scaler.py) 的 `Scaler` 类（封装 sklearn `StandardScaler`/`RobustScaler`/`MinMaxScaler`），支持 standard_scaler/robust_scaler/minmax_scaler/none 策略
   - **Step 3 - Feature Selection**：使用 [feature_selector.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/feature_selector.py) 的 `FeatureSelector` 类（封装 sklearn `VarianceThreshold`），丢弃零方差特征
   - 每步失败都会立即返回错误，不会静默跳过

6. [preprocessing_pipeline_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_pipeline_builder.py) → `build_pipeline()`：构建 `PreprocessingPipeline` 复合管道对象，包含所有 fitted 的预处理器组件（imputer/scaler/encoder/feature_selector），提供 `transform()` 方法用于对新数据进行相同的预处理。该管道可通过 joblib 序列化到磁盘。

7. [artifact_manager.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/artifact_manager.py) → `save_model_ready_artifact()`：持久化两个 artifact：
   - **Model-ready 特征矩阵**：`/app/artifacts/model_ready/{fmp_id}/model_ready_features.parquet`
   - **Preprocessor pipeline**：`/app/artifacts/model_ready/{fmp_id}/preprocessor.joblib`
   - 同时生成 `preprocessing_metadata.json`、`validation_report.json`、`preview.json`

8. [builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/builder.py) → `build_preprocessing_object()`：构建完整的 `FeaturePreprocessingResponse`，包含 9 个子对象：
   - `input_artifact`：输入特征矩阵信息
   - `validation_summary`：验证摘要（样本数/特征数/丢弃数/就绪状态）
   - `column_validation`：列校验详情（5 类丢弃原因分组）
   - `feature_group_validation`：特征组校验结果
   - `preprocessing_execution`：预处理执行详情（每步的策略和状态）
   - `model_ready_artifact`：Model-ready artifact 信息
   - `preprocessing_pipeline_artifact`：Pipeline artifact 信息
   - `model_search_input`：供下游 Model Search 模块消费的标准化输入（含 artifact 路径、特征列、策略配置、`ready_for_model_search` 标志）

9. 确定最终状态：`preprocessed` / `preprocessed_with_warning` / `failed` / `blocked`

10. 创建 `FeaturePreprocessing` → [repository.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/repository.py) → 入库

**输出**：`FeaturePreprocessingResponse`，状态为 `preprocessed` / `preprocessed_with_warning` / `failed` / `blocked`

**关键设计**：
- **失败即入库**：每一步失败时都会立即创建数据库记录（含错误信息），不会静默丢失。这是与模块五（仅在最后入库）不同的设计选择。
- **PreprocessingPipeline 可序列化**：[preprocessing_pipeline_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_pipeline_builder.py) 中的 `PreprocessingPipeline` 类通过 joblib 序列化，包含 `transform()` 方法用于推理时对新数据应用相同的预处理。
- **特征过滤分层**：5 类过滤按固定顺序执行（invalid → all_missing → constant → high_missing → inf），每步过滤后更新候选特征列表，确保后续步骤基于已过滤的结果。
- **Model Search Input 标准化**：`model_search_input` 是下游 Model Search 模块的标准化输入，包含 model_ready 矩阵路径、preprocessor pipeline 路径、特征列列表、任务类型、评估指标、以及从 Workflow Plan 继承的 model/validation/evaluation/hpo 策略。
- **特征组追踪**：通过 `feature_group_validator.py` 追踪每个特征组（来自 Feature Engineering）在过滤后的存活状态，便于后续分析和调试。

**数据库表**：`feature_preprocessing`（[model.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/model.py)），包含 15 个专项列（n_samples/n_raw_features/n_valid_features/n_final_features/n_dropped_features/target_column/model_ready_artifact_id/model_ready_artifact_path/preprocessor_artifact_id/preprocessor_artifact_path/is_ready_for_model_search）+ 5 个上游 ID 索引列（task_id/interpretation_id/dataset_profile_id/workflow_plan_id/feature_engineering_id）+ `preprocessing_json` + `preview_json` (JSONB)

**API 端点**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/api.py)）：
- `POST /api/feature-preprocessing/{task_id}` — 创建特征预处理（接受 `FeaturePreprocessingCreateRequest`，含 10 个可选配置参数）
- `GET /api/feature-preprocessing/{preprocessing_id}` — 获取单个预处理结果
- `GET /api/tasks/{task_id}/feature-preprocessing` — 获取任务的最新预处理结果
- `POST /api/feature-preprocessing/{task_id}/rerun` — 重新运行预处理
- `GET /api/feature-preprocessing/{preprocessing_id}/preview` — 获取 model-ready 数据预览

**前端组件**（[FeaturePreprocessingPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/featurePreprocessing/components/FeaturePreprocessingPanel.tsx)）：
- 主面板含 Run/Re-run/Refresh 三个操作按钮
- 4 个子卡片组件：
  - [ValidationSummaryCard.tsx](file:///c:/projects/MLAgent/frontend/src/modules/featurePreprocessing/components/ValidationSummaryCard.tsx)：展示样本数、原始特征数、有效特征数、最终特征数、丢弃特征数、就绪状态
  - [ColumnFilteringCard.tsx](file:///c:/projects/MLAgent/frontend/src/modules/featurePreprocessing/components/ColumnFilteringCard.tsx)：按 5 类丢弃原因分组展示被丢弃的特征列
  - [PreprocessingExecutionCard.tsx](file:///c:/projects/MLAgent/frontend/src/modules/featurePreprocessing/components/PreprocessingExecutionCard.tsx)：展示 Imputation/Scaling/Feature Selection 每步的执行状态和策略
  - [ModelReadyArtifactCard.tsx](file:///c:/projects/MLAgent/frontend/src/modules/featurePreprocessing/components/ModelReadyArtifactCard.tsx)：展示 model-ready artifact 和 pipeline artifact 信息，含预览按钮

**完成度**：~90%。10 步流水线完整，异常处理覆盖所有失败场景，artifact 持久化支持 parquet + joblib 双格式。但 categorical encoding 功能尚未启用（encoder.py 为占位），feature_selection 仅支持 VarianceThreshold 一种策略。

**相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/api.py)、[service.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/service.py)、[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/schemas.py)、[model.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/repository.py)、[context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/context_builder.py)、[artifact_loader.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/artifact_loader.py)、[column_validator.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/column_validator.py)、[feature_filter.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/feature_filter.py)、[feature_group_validator.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/feature_group_validator.py)、[preprocessing_executor.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_executor.py)、[preprocessing_pipeline_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_pipeline_builder.py)、[artifact_manager.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/artifact_manager.py)、[builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/builder.py)、[enums.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/enums.py)、[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/exceptions.py)、所有 preprocessors/ 目录下的文件

---

### 5.7 Featurizer Registry（共享能力注册表）

**功能描述**：作为 Workflow Planning 和 Feature Engineering 之间的**共享契约**，定义系统中所有 Featurizer 的元数据（ID/别名/状态/依赖/输入模态/预估维度），提供统一的查询、解析和回退 API。

**核心能力**（[featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py)）：
- **11 个 FeaturizerSpec 静态定义**（3 个 always available + 5 个 conditionally available（依赖 pymatgen/matminer）+ 3 个 planned）
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

**完成度**：~90%。定义完整，查询 API 健全，别名解析完善。但 `get_default_fallback` 函数在 registry API 中有调用但 featurizer_registry.py 中该函数的完整实现待确认（根据当前代码推测该函数可能尚未完全实现或为简化版本）。

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
                                           │                                    │
                                     ← TaskSpecificationResponse              │
                                           │                                    │
点击 Run → TaskInterpretationPanel → POST /api/task-interpretations/{id} ─────┤
                                           │                                    │
                                     [task_spec_adapter.py]                    │
                                     [prompt_builder.py]                       │
                                     [llm_client.py] ─────────────────────────────→ LLM API
                                     [parser.py]                               │
                                     [validator.py]                            │
                                     [builder.py]                              │
                                           │                                    │
                                     ← TaskInterpretationResponse             │
                                           │                                    │
点击 Run → DatasetProfilePanel → POST /api/dataset-profiles/{id} ─────────────┤
                                           │                                    │
                                     [context_builder.py]                      │
                                     [source_resolver.py]                      │
                                     [matbench_loader.py / file_loader.py] ──────→ Matbench / 文件系统
                                     [schema_checker.py]                       │
                                     [modality_checker.py]                     │
                                     [quality_checker.py]                      │
                                     [target_checker.py]                       │
                                     [profiler.py]                             │
                                     [builder.py]                              │
                                           │                                    │
                                     ← DatasetProfileResponse                 │
                                           │                                    │
点击 Run → WorkflowPlanPanel → POST /api/workflow-plans/{id} ─────────────────┤
                                           │                                    │
                                     [context_builder.py]                      │
                                     [prompt_builder.py] ← [featurizer_registry.py]
                                     [llm_client_adapter.py] ─────────────────────→ LLM API
                                     [parser.py]                               │
                                     [validator.py] ← [featurizer_registry.py] │
                                     [builder.py]                              │
                                           │                                    │
                                     ← WorkflowPlanResponse                   │
                                           │                                    │
点击 Run → FeatureEngineeringPanel → POST /api/feature-engineering/{id} ──────┤
                                           │                                    │
                                     [context_builder.py]                      │
                                     [data_loader_adapter.py] ────────────────────→ 复用模块三 Loader
                                     [strategy_resolver.py] ← [featurizer_registry.py]
                                     [featurizer_router.py]                    │
                                     [_run_featurizers()] ────────────────────────→ pymatgen / matminer
                                     [feature_matrix_builder.py]               │
                                     [feature_quality_checker.py]              │
                                     [artifact_manager.py] ───────────────────────→ 文件系统 (parquet/csv)
                                     [builder.py]                              │
                                           │                                    │
                                     ← FeatureEngineeringResponse             │
                                           │                                    │
点击 Run → FeaturePreprocessingPanel → POST /api/feature-preprocessing/{id} ──┤
                                           │                                    │
                                     [context_builder.py]                      │
                                     [artifact_loader.py] ────────────────────────→ 文件系统 (加载 FE artifact)
                                     [feature_filter.py]                       │
                                     [feature_group_validator.py]              │
                                     [preprocessing_executor.py] ─────────────────→ sklearn (Imputer/Scaler/Selector)
                                     [preprocessing_pipeline_builder.py]       │
                                     [artifact_manager.py] ───────────────────────→ 文件系统 (parquet + joblib)
                                     [builder.py]                              │
                                           │                                    │
                                     ← FeaturePreprocessingResponse           │
```

### 6.2 模块间数据传递机制

模块间的数据传递通过 **数据库表 + 文件系统 artifact** 两种方式进行：

1. **数据库传递**：下游模块的 `context_builder.py` 通过 Repository 跨表查询上游数据。例如：
   - 模块三的 [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/context_builder.py) 查询 `task_specification` + `task_interpretation` 表
   - 模块六的 [context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/context_builder.py) 查询全部 5 个上游表

2. **文件系统传递**：
   - 模块五 → 模块六：通过 `artifact_path` 字段传递特征矩阵文件路径
   - 模块六 → 下游 Model Search：通过 `model_ready_artifact_path` + `preprocessor_artifact_path` 传递

3. **状态校验链**：每个下游模块在处理前必须校验上游模块的状态：
   - 模块一：`valid` / `valid_with_warning`
   - 模块二：`interpreted` / `interpreted_with_warning`
   - 模块三：`profiled` / `profiled_with_warning`
   - 模块四：`planned` / `planned_with_warning`
   - 模块五：`completed` / `completed_with_warning`
   - 模块六：`preprocessed` / `preprocessed_with_warning`

---

## 7. 核心代码与关键设计说明

### 7.1 统一异常体系

所有业务异常继承自 [exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py) 中的 `BusinessException`：

```python
class BusinessException(Exception):
    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        self.message = message
        self.error_code = error_code
```

每个模块有自己的异常子类，例如：
- 模块六的 [exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/exceptions.py) 定义了 12 个专用异常（`FeaturePreprocessingNotFoundException`, `FeaturePreprocessingUpstreamNotReadyException`, `FeatureArtifactLoadException`, `ImputationFailedException`, `ScalingFailedException` 等）

### 7.2 统一响应格式

所有 API 接口使用 [response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py) 中的 `success_response()` / `error_response()`：

```python
def success_response(message: str = "Success", data: Any = None) -> dict:
    return {"success": True, "message": message, "data": data}

def error_response(message: str = "Error", error_code: str = "UNKNOWN_ERROR") -> dict:
    return {"success": False, "message": message, "error_code": error_code}
```

### 7.3 数据库设计

- **ORM**：SQLModel（统一 SQLAlchemy + Pydantic）
- **连接管理**：[connection.py](file:///c:/projects/MLAgent/backend/app/shared/database/connection.py) 创建 Engine，[session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py) 通过 FastAPI Depends 提供 generator 风格的 session 依赖注入
- **JSONB 字段**：所有模块的主数据存储在 `*_json` (JSONB) 列中，同时提取高频查询字段作为专项索引列
- **建表方式**：开发模式使用 `SQLModel.metadata.create_all(engine)` 自动建表（[main.py](file:///c:/projects/MLAgent/backend/app/main.py) 的 `on_startup` 事件）
- **数据库表清单**（6 张业务表）：
  - `task_specification`
  - `task_interpretation`
  - `dataset_profile`
  - `workflow_plan`
  - `feature_engineering`
  - `feature_preprocessing`

### 7.4 配置管理

**配置来源**（[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)）：
- 使用 `pydantic-settings` 的 `BaseSettings`，自动从环境变量和 `.env` 文件加载
- 配置分为 6 大类：应用基础、LLM、数据上传、特征工程、外部库、特征预处理

**特征预处理配置**（[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) 第 55-68 行）：
- `MODEL_READY_ARTIFACT_DIR="/app/artifacts/model_ready"`
- `MODEL_READY_ARTIFACT_FORMAT="parquet"`
- `PREPROCESSOR_ARTIFACT_FORMAT="joblib"`
- `FEATURE_PREPROCESSING_PREVIEW_ROWS=20`
- `FEATURE_PREPROCESSING_MAX_MISSING_RATIO=0.5`
- `FEATURE_PREPROCESSING_IMPUTATION_STRATEGY="median"`
- `FEATURE_PREPROCESSING_SCALING_STRATEGY="standard_scaler"`
- `FEATURE_PREPROCESSING_FEATURE_SELECTION_STRATEGY="variance_threshold"`

**LLM 配置**（[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)）：
- `LLM_PROVIDER="openai"`, `LLM_MODEL="gpt-4.1"`
- `LLM_BASE_URL="https://api.openai.com/v1"`（兼容任何 OpenAI-API 兼容端点，如 Qwen/DeepSeek）
- `LLM_TIMEOUT=60`, `LLM_MAX_RETRIES=2`, `LLM_TEMPERATURE=0.0`

### 7.5 前端架构

- **单页面应用**：[index.tsx](file:///c:/projects/MLAgent/frontend/src/index.tsx) 只渲染 `<TaskSpecificationPage />`
- **面板嵌入模式**：[TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) 在表单提交成功后（`status === 'valid' || 'valid_with_warning'`）条件渲染 5 个下游面板（Interpretation → Profile → Plan → Feature Engineering → Feature Preprocessing）
- **UI = 表单 + 流程**：所有 6 个面板纵向排列在同一页面，用户可顺序操作
- **API 客户端**：axios 单例，全局 request/response 拦截器用于日志，超时 120s（Feature Engineering 和 Feature Preprocessing 专属 600s）
- **前端类型**：6 个 `types.ts` 文件定义了对应的 TypeScript 类型，与后端 Pydantic Schema 对应

---

## 8. 当前未完成部分与后续开发建议

### 8.1 尚未实现的模块

| 模块 | 说明 | 优先级 |
|------|------|--------|
| **Model Search** | Feature Preprocessing 的 `model_search_input` 已为此准备（含 `ready_for_model_search` 标志、model_ready 矩阵路径、preprocessor pipeline 路径、策略配置），但 Model Search 业务逻辑尚未开始 | 最高 |
| **Pipeline Generation** | 将 Model Search 结果转换为可执行 Pipeline | 高 |
| **Pipeline Execution** | 将 Pipeline 转换为可执行代码或脚本 | 高 |
| **Metric Evaluation** | 对 Pipeline 执行结果进行评估 | 高 |
| **Result Diagnosis** | 对不好的结果进行诊断和重试建议 | 中 |
| **Report Generation** | 最终报告生成 | 中 |
| **用户认证/多租户** | 当前无身份验证，所有 task 对所有人可见 | 中 |
| **异步任务队列** | 模块三/四/五/六（特别是五的 matminer 特征化和六的大矩阵预处理）执行时间长（可达数分钟），当前为同步 HTTP 调用，长期执行可能导致超时 | 中 |

### 8.2 半成品代码

| 位置 | 问题描述 | 建议 |
|------|----------|------|
| `featurizer_router.py` 中的 `pymatgen_structure_parser` | 映射到 `None`，表示该功能尚未实现 | 未来需实现对应的 Featurizer 类 |
| `structure_featurizer.py` | 占位符实现，不产生实际特征 | 需完整实现结构特征化 |
| `matminer_structure_basic.py` | 类已实现但 Registry 中标记为 `planned`，未被 router 激活 | 当需要结构特征时启用 |
| `feature_preprocessing/preprocessors/encoder.py` | 编码器占位，当前未启用 categorical encoding | 当需要处理分类特征时实现 |
| `feature_preprocessing/preprocessors/feature_selector.py` | 仅支持 VarianceThreshold 一种策略 | 可扩展更多选择策略（如 SelectKBest、RFE 等） |

### 8.3 潜在问题

1. **LLM 完全依赖**：模块二和模块四完全依赖 LLM API，如果 LLM 不可用或返回不符合 Schema 的 JSON，整个管道将中断。建议未来增加规则化的 fallback 逻辑。

2. **同步执行瓶颈**：所有模块的创建接口均为同步 HTTP 调用，模块五的 matminer 特征化和模块六的大矩阵预处理可能需要数分钟。当前前端设置了 600s 超时，但长期来看应该改为异步任务队列（如 Celery）。

3. **数据库迁移**：当前使用 `SQLModel.metadata.create_all` 自动建表（开发模式），生产环境应使用 Alembic 管理迁移。项目已安装 alembic 但未初始化。

4. **文件存储路径**：上传文件和 artifact 存储在 `/app/uploads` 和 `/app/artifacts/`（Docker 容器内），需要后续挂载 volume 确保持久化。

5. **Featurizer Registry 硬编码**：11 个 FeaturizerSpec 均为 Python 代码中硬编码，无法通过配置文件或数据库动态添加。如果未来 Featurizer 数量大幅增长，需要考虑配置化。

6. **前端路由缺失**：当前为单一页面，所有面板都在同一页面中。当用户操作完任务规格后想直接查看某个历史任务结果时，需要刷新页面重新添加。未来需要前端路由（如 React Router）。

7. **Categorical Encoding 缺失**：模块六的 encoder.py 为占位实现，当前系统假设所有特征均为数值型。如果数据中包含分类特征（如材料类型、晶体结构标签等），将无法正确处理。

---

## 9. 给后续 AI Coding 大模型的开发提示

### 9.1 优先阅读的文件（按重要性排序）

| 序号 | 文件 | 理由 |
|------|------|------|
| 1 | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | 全局入口，理解路由注册和异常处理 |
| 2 | [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) | 所有配置项，控制整个系统行为 |
| 3 | [featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py) | Featurizer 共享契约，模块四、五和前端都依赖它 |
| 4 | [service.py (feature_engineering)](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/service.py) | 最复杂的业务编排，理解数据流和 Featurizer 调度 |
| 5 | [service.py (feature_preprocessing)](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/service.py) | 特征预处理 10 步流水线，理解 artifact 传递和失败处理模式 |
| 6 | [context_builder.py (feature_preprocessing)](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/context_builder.py) | 理解跨 5 个上游模块的状态校验模式 |
| 7 | [validator.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/validator.py) | 理解 LLM 输出的严格约束 |
| 8 | [prompt_builder.py (workflow)](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py) | 理解 LLM Prompt 的设计哲学 |
| 9 | [preprocessing_executor.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_executor.py) | 理解 Imputation → Scaling → Feature Selection 三步执行模式 |
| 10 | [preprocessing_pipeline_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_pipeline_builder.py) | 理解 PreprocessingPipeline 复合管道设计（可序列化 + transform） |
| 11 | [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) | 前端入口，理解 UI 结构和面板嵌入模式 |

### 9.2 继续开发时的边界注意事项

1. **新增 Featurizer 的标准流程**：
   - Step 1: 在 [featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py) 的 `_FEATURIZERS` 列表中添加 `FeaturizerSpec`
   - Step 2: 在 `featurizers/` 目录下创建 `BaseFeaturizer` 子类，实现 `featurize()` 和 `featurizer_name()` 方法
   - Step 3: 在 [featurizer_router.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/featurizer_router.py) 的 `_ROUTER` 字典中注册映射
   - **不要**在 Workflow Planning 的 prompt/validator 或 Feature Engineering 的 strategy_resolver 中硬编码新的 Featurizer 名称

2. **新增预处理器的标准流程**：
   - Step 1: 在 `feature_preprocessing/preprocessors/` 目录下创建新的预处理器类
   - Step 2: 在 [preprocessing_executor.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_executor.py) 的 `execute_preprocessing()` 中添加新的处理步骤
   - Step 3: 在 [preprocessing_pipeline_builder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessing_pipeline_builder.py) 的 `PreprocessingPipeline` 类中添加对应的组件和 transform 逻辑
   - Step 4: 在 [enums.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/enums.py) 中添加新的策略常量
   - Step 5: 在 [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/schemas.py) 的 `FeaturePreprocessingCreateRequest` 中添加新的配置参数

3. **不要重复实现的功能**：
   - **数据加载**：已有 `MatbenchLoader` 和 `FileLoader`，新模块如需加载数据应复用模块三的 Loader（参考 `data_loader_adapter.py`）
   - **LLM 调用**：已有 `LLMClient`（模块二），新模块应复用（参考 `llm_client_adapter.py`）
   - **统一响应格式**：所有 API 接口必须使用 `success_response()` / `error_response()`
   - **异常处理**：新异常应继承 `BusinessException` 或其子类，设置语义化 `error_code`
   - **特征过滤**：模块六已实现完整的 5 类特征过滤逻辑，新模块不应重复实现

4. **模块间数据传递规范**：
   - 模块间的数据传递通过 **数据库表 + 文件系统 artifact** 进行，不是内存对象
   - 下游模块的 `context_builder.py` 通过 Repository 跨表查询上游数据
   - 下游模块必须在开始处理前校验上游模块的状态（如 `status in ("valid", "valid_with_warning")`）
   - Artifact 路径通过数据库字段传递（如 `artifact_path`, `model_ready_artifact_path`）

5. **LLM 交互规范**（如果新模块需要使用 LLM）：
   - 必须定义严格的 JSON Schema
   - 必须有 parser（JSON 提取）+ validator（Schema 校验）两步
   - 禁止内容检测（`FORBIDDEN_CONTENT` 列表）应在前置 prompt rules 中声明
   - 失败时写入数据库，包含 `llm_request_json` + `llm_response_json` + `error_message`

6. **前端开发规范**：
   - 所有 API 客户端函数遵循 `{action}{Resource}` 命名（如 `createTask`, `getLatestFeaturePreprocessing`）
   - 每个模块的 `types.ts` 定义完整的 TypeScript 类型
   - 面板组件以 `{Module}Panel.tsx` 命名，接受 `taskId` prop
   - axios 实例从 `taskApi.ts` 导入，不要在各自文件中创建新实例
   - 长时间运行的操作设置合理的超时时间（参考 featurePreprocessingApi.ts 的 600s）

### 9.3 建议的 Model Search 模块实现方向

根据当前项目架构和输出，Model Search 模块应该：
- 消费 Feature Preprocessing 的 `model_search_input`（含 `model_ready_artifact_id`/`model_ready_matrix_path`/`preprocessing_pipeline_artifact_id`/`target_column`/`feature_columns`/`task_type`/`primary_metric`/`model_strategy`/`validation_strategy`/`evaluation_strategy`/`hpo_strategy`）
- 消费 Workflow Plan 的 `pipeline_generation_input`（含 `pipeline_steps`/`required_components`）
- 遵循现有的 `api.py → service.py → context_builder.py → builder.py → model.py → repository.py` 分层模式
- 参考 Feature Preprocessing 的 artifact 管理模式（加载上游 artifact → 处理 → 保存下游 artifact）
- 输出中包含最佳模型 artifact 和 model search 结果

### 9.4 技术债务提示

- `featurizer_registry.py` 中的 `get_default_fallback()` 和 `get_planned_featurizers()` 函数已完整实现，被 validator.py / strategy_resolver.py / prompt_builder.py 正常引用
- `enums.py` 中各模块使用了不同的枚举定义风格（模块一使用 `Enum` 类，模块四使用普通类常量，模块六使用普通类常量），后续可以统一
- 前端没有 React Router，所有面板嵌入在一个页面中，历史任务查看不便
- 缺少 API 版本管理（如 `/api/v1/` 前缀）
- 缺少请求日志中间件和性能监控
- 模块六的 categorical encoding 功能尚未实现（encoder.py 为占位）
- 模块六的 feature_selection 仅支持 VarianceThreshold，可扩展更多策略