# 项目已实现部分说明文档

> 文档生成日期：2026-05-04（全面更新版 — 含模块八 Automated Model and HPO Search）
> 项目名称：MLAgent — AI-driven Automated Machine Learning Framework for Materials Science
> 文档用途：帮助后续 AI Coding 大模型和开发者快速理解当前项目已经完成的部分

---

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个面向材料科学领域的 AI 驱动自动化机器学习框架。其核心目标是让用户通过结构化表单提交材料机器学习任务需求，系统自动完成从**任务理解 → 数据加载 → 工作流规划 → 特征工程 → 特征预处理 → 模型搜索上下文更新 → 模型搜索计划生成**的全流程自动化。当前尚未实现 Pipeline Generation / Pipeline Execution / Metric Evaluation 及后续阶段。

### 1.2 当前实现阶段

当前项目已完成 **八个核心业务模块** 的端到端实现：

| 模块 | 阶段 | 完成度 |
|------|------|--------|
| **模块一：Task Specification（任务规格录入与校验）** | MVP 已完成 | ~95% |
| **模块二：LLM-based Task Interpretation（基于大模型的任务理解）** | MVP 已完成 | ~90% |
| **模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）** | MVP 已完成 | ~90% |
| **模块四：Workflow Planning（LLM 驱动的工作流规划）** | MVP 已完成 | ~90% |
| **模块五：Feature Engineering（特征工程）** | MVP 已完成 | ~85% |
| **模块六：Feature Preprocessing（特征预处理）** | MVP 已完成 | ~90% |
| **模块七：Model Search Context（模型搜索上下文更新）** | MVP 已完成 | ~85% |
| **模块八：Automated Model and HPO Search（自动化模型与超参数搜索规划）** ★ 新增 | MVP 已完成 | ~85% |
| **Featurizer Registry / Model Registry / HPO Registry（共享能力注册表）** | MVP 已完成 | ~90% |

当前**尚未实现**的后续模块包括：Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis、Report Generation 等。

### 1.3 项目整体架构

```
用户浏览器 (React SPA — 单一 TaskSpecificationPage，含 8 个嵌入式面板)
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
    ├── Feature Preprocessing (Imputation → Scaling → Feature Selection)
    │       ↓
    │   Model-Ready Artifact (parquet + joblib pipeline 存储到 /app/artifacts/model_ready/)
    │
    ├── Model Search Context (数据集分析 → 特征组分析 → LLM 策略建议 → 策略合并)
    │       ↓
    │   Updated Strategies (供下游 Model Search 消费)
    │
    └── Model Search (LLM 模型搜索建议 → Registry 校验 → 候选模型/HPO/搜索空间 → Trial 分配 → Pipeline Generation Input)
            ↓
        Model Search Plan (供下游 Pipeline Generation 消费)
```

### 1.4 核心设计原则（根据当前代码分析）

1. **管道式架构**：八个模块严格按序依赖。每个下游模块的 `context_builder.py` 会校验所有上游模块的输出状态，状态不符则抛出专用异常。
2. **统一异常体系**：所有业务异常继承自 `BusinessException`（定义于 [exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)），每个模块有自己的异常子类，附带有语义化的 `error_code`。
3. **LLM 输出强约束**：模块二、模块四、模块七和模块八均定义了严格的 JSON Schema，LLM 响应经过解析（`parser.py`）+ 校验（`validator.py`）两步才被认为有效。
4. **Featurizer Registry 作为共享契约**：Workflow Planning 的 Prompt 和 Validator、Feature Engineering 的 Strategy Resolver 都向 Registry 查询，而非各自维护硬编码列表。
5. **失败状态持久化**：所有模块在失败时都会将失败记录（含错误信息）写入数据库，不会静默丢失。
6. **Artifact 传递链**：Feature Engineering 输出特征矩阵 artifact → Feature Preprocessing 加载并处理后输出 model-ready artifact + preprocessor pipeline artifact → Model Search Context 分析后输出更新后的策略 → Model Search 基于策略和 Registry 生成模型搜索计划，供下游 Pipeline Generation 消费。
7. **多 Registry 共享架构**：除 Featurizer Registry 外，还有 [model_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/model_registry.py)（10 个模型族定义）和 [hpo_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/hpo_registry.py)（5 个 HPO 方法定义）。模块八深度消费这两个 Registry，所有 LLM 推荐的模型和 HPO 方法必须经 Registry 校验。
8. **LLM 建议 + 系统生成分离**：模块八中 LLM 仅输出结构化建议（推荐哪些模型、HPO 预算），最终候选模型、HPO 方法、搜索空间必须由系统基于 Registry、模板和校验器生成。LLM 不输出可执行代码、不直接指定参数空间。

---

## 2. 当前目录结构说明

### 2.1 完整目录树（实际文件）

```
c:\projects\MLAgent/
├── backend/                                # 后端 FastAPI 项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI 入口，路由注册，CORS，异常处理，启动时建表
│   │   ├── modules/                       # 业务模块（八个模块 + Featurizer Registry API）
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
│   │   │   │   ├── api.py                # 6 个接口（POST upload, POST profile, GET by id, GET by task, POST rerun, GET preview）
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
│   │   │   ├── feature_preprocessing/    # 模块六：特征预处理
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # 5 个接口（POST, GET by id, GET by task, POST:/rerun, GET preview）
│   │   │   │   ├── schemas.py            # FeaturePreprocessingCreateRequest, ValidationSummary, ModelSearchInput 等 15+ 个子对象
│   │   │   │   ├── service.py            # 10 步流水线：build_context → load_artifact → filter → validate_groups → execute → build_pipeline → save → build → persist
│   │   │   │   ├── model.py              # FeaturePreprocessing (JSONB + 15 个专项列 + 5 个上游 ID 索引)
│   │   │   │   ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id
│   │   │   │   ├── context_builder.py    # 跨 5 个上游模块构建 context（校验全部前置模块状态 + artifact_path 存在性）
│   │   │   │   ├── artifact_loader.py    # 加载 Feature Engineering 输出的特征矩阵 artifact（parquet/csv）
│   │   │   │   ├── column_validator.py   # 列级校验：无效列/全空列/常量列/高缺失列/Inf值检测
│   │   │   │   ├── feature_filter.py     # 特征过滤编排：顺序执行 5 类过滤（invalid → all_missing → constant → high_missing → inf）
│   │   │   │   ├── feature_group_validator.py # 特征组校验：按组统计保留/丢弃状态
│   │   │   │   ├── preprocessing_executor.py  # 预处理执行器：Imputation → Scaling → Feature Selection 三步流水线
│   │   │   │   ├── preprocessing_pipeline_builder.py # PreprocessingPipeline 复合管道类（可 joblib 序列化，含 transform 方法）
│   │   │   │   ├── artifact_manager.py   # Model-ready artifact 持久化（parquet + joblib pipeline + metadata.json + preview.json）
│   │   │   │   ├── builder.py            # 构建 FeaturePreprocessingResponse（含 model_search_input）
│   │   │   │   ├── enums.py              # FeaturePreprocessingStatus / ImputationStrategy / ScalingStrategy / FeatureSelectionStrategy 等
│   │   │   │   ├── exceptions.py         # 12 个专用异常（UpstreamNotReady/ArtifactLoad/ImputationFailed/ScalingFailed 等）
│   │   │   │   └── preprocessors/        # 预处理器实现
│   │   │   │       ├── __init__.py
│   │   │   │       ├── imputer.py        # sklearn SimpleImputer 封装（median/mean/most_frequent）
│   │   │   │       ├── scaler.py         # sklearn Scaler 封装（Standard/Robust/MinMax）
│   │   │   │       ├── encoder.py        # 编码器（占位，当前未启用）
│   │   │   │       └── feature_selector.py # sklearn VarianceThreshold 封装
│   │   │   │
│   │   │   └── model_search_context/     # 模块七：模型搜索上下文更新
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 4 个接口（POST, GET by id, GET by task, POST:/rerun）
│   │   │       ├── schemas.py            # DatasetEffectiveProfile, FeatureGroupSummary, LLMStrategyAdvice, StrategyAdjustment 等
│   │   │       ├── service.py            # 12 步流水线：build_context → analyze_dataset → analyze_feature_groups → analyze_preprocessing → build_llm_context → LLM → parse → validate → merge_strategies → build → persist
│   │   │       ├── model.py              # ModelSearchContext (JSONB + 多个上游 ID 索引 + ready_for_model_search_plan)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id
│   │   │       ├── context_builder.py    # 跨 6 个上游模块构建 context（校验全部前置模块状态）
│   │   │       ├── dataset_profile_analyzer.py  # 有效数据集画像分析（样本量/特征数/降维比）
│   │   │       ├── feature_group_analyzer.py    # 特征组分析（保留/丢弃/部分保留组统计）
│   │   │       ├── preprocessing_analyzer.py    # 预处理执行分析（imputation/scaling/selection 状态）
│   │   │       ├── llm_context_builder.py       # 构建 LLM 上下文 prompt
│   │   │       ├── llm_strategy_advisor.py      # LLM 策略顾问（调用 LLM 获取策略建议）
│   │   │       ├── llm_response_parser.py       # LLM 响应 JSON 解析
│   │   │       ├── llm_advice_validator.py      # LLM 建议校验器（模型族/HPO方法/验证策略合法性检查）
│   │   │       ├── strategy_merger.py           # 策略合并器（原始策略 + LLM建议 + 数据分析 → 最终策略）
│   │   │       ├── model_strategy_adjuster.py   # 模型策略调整器
│   │   │       ├── hpo_strategy_adjuster.py     # HPO 策略调整器
│   │   │       ├── validation_strategy_adjuster.py # 验证策略调整器
│   │   │       ├── evaluation_strategy_adjuster.py # 评估策略调整器
│   │   │       ├── builder.py            # 构建 ModelSearchContextResponse
│   │   │       ├── enums.py              # ModelSearchContextStatus / UpdateMode / HPOBudgetLevel 等
│   │   │       └── exceptions.py         # ModelSearchContextNotFound / UpstreamNotReady / LLMCall 等
│   │   │
│   │   │   └── model_search/             # 模块八：自动化模型与超参数搜索规划 ★ 新增
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 5 个接口（POST, GET by id, GET by task, POST:/rerun, GET summary）
│   │   │       ├── schemas.py            # ModelSearchPlanCreateRequest, DatasetContext, CandidateModelPlanGroup, HPOPlan, SearchSpacePlan, ValidationPlan, EvaluationPlan 等 20+ 个子对象
│   │   │       ├── service.py            # 12 步流水线：build_context → build_llm_prompt → LLM → parse → validate → select_candidate_models → build_hpo_plan → build_search_space → build_validation/eval → build → persist
│   │   │       ├── model.py              # ModelSearchPlan (JSONB + 18 个专项列 + 4 个上游 ID 索引 + ready_for_pipeline_generation)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id
│   │   │       ├── context_builder.py    # 读取模块七的 ModelSearchContext，校验 ready_for_model_search_plan=True，加载 Model/HPC Registry
│   │   │       ├── llm_prompt_builder.py # 构建 LLM 模型搜索 prompt（含严格 JSON Schema + 禁止代码规则）
│   │   │       ├── llm_model_search_advisor.py  # LLM 模型搜索顾问（复用 LLMClient 调用 LLM）
│   │   │       ├── llm_response_parser.py       # LLM 响应 JSON 解析（去除 markdown + Pydantic 校验）
│   │   │       ├── llm_advice_validator.py      # LLM 建议校验器（Model/HPC Registry 校验 + 代码注入扫描 + 14 种模式检测）
│   │   │       ├── candidate_model_selector.py  # 候选模型选择器（LLM 建议 + Registry + 优先级权重 + include/exclude 过滤）
│   │   │       ├── hpo_plan_builder.py          # HPO 计划构建器（搜索方法/预算级别/trial 分配/并行度/early stopping/fallback）
│   │   │       ├── search_space_builder.py      # 超参数搜索空间构建器（10 个模型 × 2 种任务类型的内置模板 + space_width 自适应调整）
│   │   │       ├── trial_allocator.py           # Trial 分配器（按优先级权重分配，小样本偏向简单模型）
│   │   │       ├── validation_plan_builder.py   # 验证计划构建器
│   │   │       ├── evaluation_plan_builder.py   # 评价计划构建器（指标方向映射 + 二级指标默认值）
│   │   │       ├── pipeline_input_builder.py    # 下游 Pipeline Generation Input 构建器
│   │   │       ├── builder.py            # 构建 ModelSearchPlanResponse（含 plan_json）
│   │   │       ├── enums.py              # ModelSearchPlanStatus / PlanningMode / HPOBudgetLevel / SearchSpaceProfile / ModelPriority 等
│   │   │       └── exceptions.py         # 13 个专用异常（ModelSearchPlanNotFound / ModelSearchContextRequired / LLMCall / Parse / Validation 等）
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
│   │       │   └── settings.py          # pydantic-settings：数据库/LLM/数据上传/特征工程/特征预处理/模型搜索上下文 配置
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── connection.py        # SQLModel Engine 创建（单行，基于 DATABASE_URL）
│   │       │   └── session.py           # FastAPI Depends get_session 依赖注入（generator）
│   │       └── registry/               # 多 Registry 共享核心
│   │           ├── __init__.py
│   │           ├── featurizer_registry.py # 11 个 FeaturizerSpec 静态定义 + 依赖检测 + ID/Alias 索引 + 查询 API + 回退逻辑
│   │           ├── model_registry.py     # 10 个模型族定义（dummy_mean/linear/ridge/lasso/elastic_net/rf/gb/xgb/svr/knn）
│   │           ├── hpo_registry.py       # 5 个 HPO 方法定义（random_search/grid_search/optuna_tpe/bayesian/successive_halving）
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
│   │   │   ├── featurePreprocessingApi.ts # Feature Preprocessing API（超时 600s）
│   │   │   ├── modelSearchContextApi.ts # Model Search Context API（超时 300s）
│   │   │   └── modelSearchApi.ts        # Model Search Plan API（超时 300s，含 LLM 调用）★ 新增
│   │   ├── modules/                     # 业务模块（8 个面板）
│   │   │   ├── taskSpecification/       # 任务规格表单
│   │   │   │   ├── pages/TaskSpecificationPage.tsx  # 页面容器（含 8 个嵌入式面板）
│   │   │   │   ├── components/TaskSpecificationForm.tsx # 主表单（react-hook-form + zod）
│   │   │   │   ├── components/TaskFieldGroup.tsx    # 字段分组容器
│   │   │   │   └── constants.ts         # Zod Schema + 下拉选项常量
│   │   │   ├── taskInterpretation/      # 任务理解面板
│   │   │   │   ├── components/TaskInterpretationPanel.tsx
│   │   │   │   └── types.ts
│   │   │   ├── datasetProfile/          # 数据集画像面板
│   │   │   │   ├── components/DatasetProfilePanel.tsx
│   │   │   │   ├── components/FileUpload.tsx
│   │   │   │   └── types.ts
│   │   │   ├── workflowPlanning/        # 工作流规划面板
│   │   │   │   ├── components/WorkflowPlanPanel.tsx
│   │   │   │   └── types.ts
│   │   │   ├── featureEngineering/      # 特征工程面板
│   │   │   │   ├── components/FeatureEngineeringPanel.tsx
│   │   │   │   └── types.ts
│   │   │   ├── featurePreprocessing/    # 特征预处理面板
│   │   │   │   ├── components/FeaturePreprocessingPanel.tsx
│   │   │   │   ├── components/ColumnFilteringCard.tsx
│   │   │   │   ├── components/ValidationSummaryCard.tsx
│   │   │   │   ├── components/PreprocessingExecutionCard.tsx
│   │   │   │   ├── components/ModelReadyArtifactCard.tsx
│   │   │   │   ├── constants.ts
│   │   │   │   └── types.ts
│   │   │   └── modelSearchContext/      # 模型搜索上下文面板
│   │   │       ├── components/ModelSearchContextPanel.tsx
│   │   │       ├── components/EffectiveDatasetProfileCard.tsx
│   │   │       ├── components/FeatureGroupSummaryCard.tsx
│   │   │       ├── components/PreprocessingSummaryCard.tsx
│   │   │       ├── components/LLMAdviceCard.tsx
│   │   │       ├── components/LLMAdviceValidationCard.tsx
│   │   │       ├── components/StrategyAdjustmentCard.tsx
│   │   │       ├── components/UpdatedModelStrategyCard.tsx
│   │   │       ├── components/UpdatedHPOStrategyCard.tsx
│   │   │       ├── components/ModelSearchContextJsonViewer.tsx
│   │   │       ├── constants.ts
│   │   │       └── types.ts
│   │   │   └── modelSearch/              # 自动化模型与超参数搜索面板 ★ 新增
│   │   │       ├── components/ModelSearchPlanPanel.tsx   # 主面板（含 Run/Re-run 按钮、12 个展示子区）
│   │   │       ├── constants.ts          # 状态标签 / 优先级/预算级别颜色
│   │   │       └── types.ts              # ModelSearchPlanResponse, HPOPlan, SearchSpacePlan 等 20+ 个接口
│   │   └── index.tsx
│   ├── Dockerfile
│   ├── package.json                     # React 18 + Ant Design 5 + react-hook-form + zod + axios
│   └── tsconfig.json
│
├── docs/                                # 项目文档
│   ├── PROJECT_IMPLEMENTATION_OVERVIEW.md  # 本文档
│   ├── prd-1-mvp.md ~ prd-8.md          # 各模块 PRD 文档
│   └── prd-*-技术实现方案.md             # 各模块技术实现方案
│
├── docker-compose.yml                   # 三服务编排（db + backend + frontend）
└── .gitignore
```

---

## 3. 当前系统输入与输出

### 3.1 系统输入

| 输入项 | 来源 | 格式 | 说明 |
|--------|------|------|------|
| 任务规格表单 | 用户浏览器 | JSON (HTTP POST) | 包含 task_name, prediction_target, task_type, dataset_description, input_type, target_column, evaluation_metric, user_priority, constraints 等字段 |
| 数据集文件 | 用户上传 | CSV / XLSX / XLS | 通过 `/api/dataset-profiles/upload` 上传，存储到 `/app/uploads/` |
| Matbench 数据集引用 | 用户在表单中指定 | 字符串 (如 "matbench_expt_gap") | 通过 MatbenchLoader 从 matbench Python 包加载，若包未安装则使用内置样本数据 |
| LLM API 配置 | 环境变量 / .env 文件 | 字符串 | LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL 等 |

### 3.2 系统输出

| 输出项 | 目标 | 格式 | 说明 |
|--------|------|------|------|
| Task Specification | 数据库 + API 响应 | JSON | 含校验结果（status, missing_fields, validation_messages） |
| Task Interpretation | 数据库 + API 响应 | JSON | LLM 输出的结构化任务理解（含 prediction_target, modeling_intent, planning_hint 等） |
| Dataset Profile | 数据库 + API 响应 | JSON | 含 schema, modality_check, target_profile, data_quality, profiling_summary, workflow_planning_input |
| Workflow Plan | 数据库 + API 响应 | JSON | LLM 输出的工作流规划（含 task_summary, data_strategy, feature_strategy, model_strategy, validation_strategy, hpo_strategy 等） |
| Feature Engineering Result | 数据库 + API 响应 + 文件系统 | JSON + Parquet/CSV | 特征矩阵存储到 `/app/artifacts/features/{fe_id}/features.parquet` |
| Feature Preprocessing Result | 数据库 + API 响应 + 文件系统 | JSON + Parquet + Joblib | Model-ready 矩阵存储到 `/app/artifacts/model_ready/{fmp_id}/model_ready_features.parquet`，预处理管道存储为 `preprocessor.joblib` |
| Model Search Context | 数据库 + API 响应 | JSON | 含 dataset_effective_profile, feature_group_summary, preprocessing_summary, llm_strategy_advice, updated strategies, model_search_context_input |
| Model Search Plan | 数据库 + API 响应 | JSON | 含 dataset_context, candidate_model_plan (baseline + candidate + excluded), hpo_plan (method/budget/trial_allocation), search_space_plan (每模型参数空间), validation_plan, evaluation_plan, llm_model_search_advice, system_validation_result, pipeline_generation_input |

### 3.3 中间产物（Artifact 传递链）

```
用户上传文件 / Matbench 引用
    ↓ (模块三: Dataset Profile)
原始数据 DataFrame (内存中)
    ↓ (模块五: Feature Engineering)
特征矩阵 Artifact → /app/artifacts/features/{fe_id}/features.parquet
    ↓ (模块六: Feature Preprocessing)
Model-Ready Artifact → /app/artifacts/model_ready/{fmp_id}/model_ready_features.parquet
Preprocessor Pipeline → /app/artifacts/model_ready/{fmp_id}/preprocessor.joblib
    ↓ (模块七: Model Search Context)
Updated Strategies (JSON, 存入数据库)
    ↓ (模块八: Model Search)
Model Search Plan (含 candidate_model_plan + hpo_plan + search_space_plan + pipeline_generation_input，存入数据库)
    ↓ (尚未实现: Pipeline Generation)
```

---

## 4. 当前技术栈说明

### 4.1 后端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **Python** | 3.11+ | 主编程语言 |
| **FastAPI** | 0.115.6 | Web 框架，提供 REST API、自动 OpenAPI 文档、依赖注入 |
| **Uvicorn** | 0.34.0 | ASGI 服务器，运行 FastAPI 应用 |
| **SQLModel** | 0.0.22 | ORM 框架（结合 SQLAlchemy + Pydantic），用于数据库模型定义和查询 |
| **PostgreSQL** | 16 (Docker) | 主数据库，通过 JSONB 字段存储非结构化数据 |
| **Psycopg2** | 2.9.10 | PostgreSQL 数据库驱动 |
| **Pydantic** | 2.10.4 | 数据校验和序列化（请求/响应 Schema） |
| **pydantic-settings** | 2.7.1 | 环境变量和配置文件管理 |
| **httpx** | 0.28.1 | HTTP 客户端，用于调用外部 LLM API（OpenAI 兼容接口） |
| **Pandas** | 2.2.3 | 数据处理和特征矩阵构建 |
| **NumPy** | 2.2.0 | 数值计算 |
| **scikit-learn** | >=1.3.0 | 机器学习预处理（SimpleImputer, StandardScaler, RobustScaler, MinMaxScaler, VarianceThreshold） |
| **pymatgen** | >=2024.0.0 | 材料科学工具包，用于化学式解析和 Composition 对象 |
| **matminer** | >=0.9.0 | 材料数据挖掘工具包，提供 Stoichiometry, ElementProperty, Magpie, ValenceOrbital 等 Featurizer |
| **pyarrow** | >=14.0.0 | Parquet 文件读写支持 |
| **joblib** | (scikit-learn 依赖) | 预处理管道序列化 |
| **openpyxl** | 3.1.5 | Excel 文件读取支持 |
| **python-dotenv** | 1.0.1 | .env 文件加载 |
| **Alembic** | 1.14.1 | 数据库迁移工具（已安装，但当前使用 SQLModel.metadata.create_all 自动建表） |

### 4.2 前端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **React** | 18.3.1 | UI 框架 |
| **TypeScript** | 5.7.2 | 类型安全 |
| **Ant Design** | 5.24.8 | UI 组件库（@ant-design/icons 5.6.1） |
| **react-hook-form** | 7.54.2 | 表单状态管理和校验 |
| **zod** | 3.24.1 | 前端表单数据 Schema 校验 |
| **@hookform/resolvers** | 3.10.0 | react-hook-form 与 zod 的桥接 |
| **axios** | 1.7.9 | HTTP 客户端，含请求/响应拦截器 |
| **ajv** | 8.20.0 | JSON Schema 校验器（用于 LLM 输出校验） |
| **react-scripts** | 5.0.1 | Create React App 构建工具链 |

### 4.3 基础设施

| 技术 | 作用 |
|------|------|
| **Docker Compose** | 三服务编排：db (PostgreSQL 16) + backend (FastAPI) + frontend (React) |
| **PostgreSQL 16 Alpine** | 数据库服务，含健康检查和持久化卷 |
| **Dockerfile (backend)** | 基于 Python 3.11-slim，安装依赖并运行 uvicorn |
| **Dockerfile (frontend)** | 基于 Node 18-alpine，运行 react-scripts start |

---

## 5. 已实现功能模块

### 5.1 模块一：Task Specification（任务规格录入与校验）

**文件位置**：[backend/app/modules/task_specification/](file:///c:/projects/MLAgent/backend/app/modules/task_specification/)

**输入**：
- `TaskSpecificationCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py)）：task_name, task_description, material_system, prediction_target, task_type, dataset_description, input_type, target_column, evaluation_metric, user_priority, constraints

**处理逻辑**：
1. `TaskSpecificationService.create_task()` 生成 task_id（格式 `task_{uuid8}`）
2. `normalizer.normalize_fields()` 对 task_type/input_type/evaluation_metric/user_priority 进行标准化映射（如 "mean absolute error" → "MAE"）
3. `validator.validate()` 执行四步校验：
   - `check_required_fields()`：检查 prediction_target, task_type, dataset_description, input_type, target_column 是否填写
   - `check_evaluation_metric_compatibility()`：检查评估指标与任务类型是否匹配（如 classification 不能用 MAE）
   - `check_input_dataset_consistency()`：检查输入类型与数据集描述是否一致
   - `check_evaluation_metric_provided()`：若未指定评估指标则生成警告
4. `builder.build_task_specification()` 构建完整的 task_spec JSON dict
5. 通过 `TaskSpecificationRepository` 持久化到 PostgreSQL

**输出**：
- `TaskSpecificationResponse`：含 task_id, status（valid/invalid/incomplete/valid_with_warning）, missing_fields, validation_messages
- `ValidationResultResponse`：单独校验接口返回

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)）：
- `POST /api/tasks` — 创建任务规格
- `GET /api/tasks/{task_id}` — 获取任务规格
- `PUT /api/tasks/{task_id}` — 更新任务规格
- `POST /api/tasks/{task_id}/validate` — 校验任务规格

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)）：
- `TaskSpecification` 表：id (PK), task_name, task_type, prediction_target, dataset_description, input_type, target_column, evaluation_metric, status, task_spec_json (JSONB), created_at, updated_at

**完成度**：~95%。核心 CRUD 和校验逻辑完整。缺少批量任务列表查询的前端界面。

---

### 5.2 模块二：Task Interpretation（LLM 任务理解）

**文件位置**：[backend/app/modules/task_interpretation/](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/)

**输入**：
- `TaskInterpretationCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/schemas.py)）：force_rerun, llm_provider, model_name
- 上游 TaskSpecification 数据（通过 `task_spec_adapter.adapt_task_spec()` 转换）

**处理逻辑**：
1. `TaskInterpretationService.create_interpretation()` 获取 TaskSpecification
2. `task_spec_adapter.adapt_task_spec()` 将 DB model 转为 LLM context dict
3. `prompt_builder.build_prompt()` 构建 system prompt（含 9 条 CRITICAL 规则）和 user message（含完整 JSON Schema 定义）
4. `LLMClient.generate()` 通过 httpx 调用 OpenAI 兼容 API（含最多 2 次重试）
5. `parser.parse_llm_response()` 用正则去除 markdown 代码块后解析 JSON
6. `validator.validate_interpretation()` 校验必填字段、枚举值、置信度范围
7. 失败时写入失败记录到数据库（含 llm_request_json 和 error_message）
8. `builder.build_interpretation()` 构建完整 interpretation JSON

**LLM 输出 Schema**（[prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py) 中的 `_OUTPUT_SCHEMA`）：
- interpreted_task_type（regression/classification/ranking/unknown）
- interpreted_input_modality（composition/structure/descriptor/text/mixed）
- interpreted_material_domain
- interpreted_prediction_target（含 raw_target, normalized_target, target_category, target_unit）
- modeling_intent（含 primary_goal, secondary_goals, optimization_direction, preferred_metric）
- dataset_intent（含 dataset_reference, expected_input_columns, expected_target_column, dataset_loading_hint）
- planning_hint（含 task_family, input_representation, requires_feature_engineering 等）
- constraint_interpretation（含 hard_constraints, soft_constraints, potential_conflicts）
- recommended_defaults（含 evaluation_metric, validation_strategy, baseline_requirement）
- ambiguities, warnings, llm_reasoning_summary, confidence_score

**输出**：
- `TaskInterpretationResponse`：含 interpretation_id, status, 以及上述所有 LLM 输出子对象

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py)）：
- `POST /api/task-interpretations/{task_id}` — 创建任务理解
- `GET /api/task-interpretations/{interpretation_id}` — 获取任务理解
- `GET /api/tasks/{task_id}/interpretation` — 获取任务的最新理解
- `POST /api/task-interpretations/{task_id}/rerun` — 重新运行任务理解

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py)）：
- `TaskInterpretation` 表：id (PK), task_id (indexed), status (indexed), interpreted_task_type, interpreted_input_modality, interpreted_material_domain, confidence_score, interpretation_json (JSONB), llm_request_json (JSONB), llm_response_json (JSONB), error_message, created_at (indexed), updated_at

**完成度**：~90%。核心 LLM 调用和校验逻辑完整。`TaskNotReadyException` 已定义但 `create_interpretation` 中未强制校验 task_spec 状态（根据当前代码推测，仅检查了 task_spec 是否存在）。

---

### 5.3 模块三：Dataset Profile（数据集加载与画像）

**文件位置**：[backend/app/modules/dataset_profile/](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/)

**输入**：
- `DatasetProfileCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/schemas.py)）：uploaded_file_id, uploaded_file_path, max_preview_rows
- 上游 TaskSpecification + TaskInterpretation 数据

**处理逻辑**：
1. `context_builder.build_dataset_loading_context()` 校验 task_spec 状态（需 valid/valid_with_warning）和 interpretation 状态（需 interpreted/interpreted_with_warning），构建完整 context
2. `source_resolver.resolve_source()` 识别数据源类型：
   - 优先级1：有 uploaded_file_id/path → "uploaded_file"
   - 优先级2：dataset_loading_hint.source_type == "public_benchmark" → "public_benchmark"
   - 优先级3：dataset_reference 或 description 含 "matbench" → "public_benchmark"
   - 优先级4：description 含 csv/xlsx/excel/file/upload → "uploaded_file"
   - 否则 → "unknown"（抛出异常）
3. 选择对应 Loader（MatbenchLoader 或 FileLoader）加载数据
   - `MatbenchLoader`（[matbench_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/matbench_loader.py)）：优先使用 matbench Python 包，若未安装则使用内置 4 个数据集的样本数据（最多 200 行随机生成）
   - `FileLoader`（[file_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/file_loader.py)）：从 `/app/uploads/` 读取 CSV/XLSX/XLS 文件
4. 四个 Checker 依次执行：
   - `schema_checker.check_schema()`：列名检查、大小写匹配、全空列检测
   - `modality_checker.check_modality()`：输入模态检测与一致性校验
   - `quality_checker.check_quality()`：缺失值/重复行/无效值/常量列/高缺失率列/小样本
   - `target_checker.check_target()`：回归（极值/均值/标准差/偏度/离群值）/分类（类别分布/不平衡）
5. `profiler.py` 进行质量评级 + 样本量等级 + 推荐下一步 + workflow_planning_input 构建
6. `builder.build_dataset_profile()` 构建完整 profile JSON

**输出**：
- `DatasetProfileResponse`：含 dataset_source, dataset_schema, modality_check, target_profile, data_quality, profiling_summary, workflow_planning_input
- `DatasetFileUploadResponse`：文件上传接口返回
- `DatasetPreviewResponse`：数据预览接口返回

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py)）：
- `POST /api/dataset-profiles/upload` — 上传数据集文件
- `POST /api/dataset-profiles/{task_id}` — 创建数据集画像
- `GET /api/dataset-profiles/{dataset_profile_id}` — 获取数据集画像
- `GET /api/tasks/{task_id}/dataset-profile` — 获取任务的最新画像
- `POST /api/dataset-profiles/{task_id}/rerun` — 重新运行画像
- `GET /api/dataset-profiles/{dataset_profile_id}/preview` — 获取数据预览

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/model.py)）：
- `DatasetProfile` 表：id (PK), task_id (indexed), interpretation_id (indexed), status (indexed), source_type (indexed), dataset_reference, loader_name, n_samples, n_columns, input_modality, target_column, quality_level, is_usable_for_ml, profile_json (JSONB), preview_json (JSONB), error_message, created_at (indexed), updated_at

**完成度**：~90%。核心加载和检查逻辑完整。Matbench 的 fallback 样本数据仅覆盖 4 个已知数据集。

---

### 5.4 模块四：Workflow Planning（LLM 工作流规划）

**文件位置**：[backend/app/modules/workflow_planning/](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/)

**输入**：
- `WorkflowPlanCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/schemas.py)）：force_rerun
- 上游 TaskSpecification + TaskInterpretation + DatasetProfile 数据

**处理逻辑**：
1. `context_builder.build_workflow_planning_context()` 校验三个上游模块状态，构建包含 task_context, interpretation_context, data_context 的完整 context
2. `prompt_builder.build_prompt()` 构建超长 system prompt（含 10 条 CRITICAL 规则 + 8 个策略维度）
3. `llm_client_adapter.WorkflowPlanningLLMAdapter` 复用模块二的 `LLMClient` 调用 LLM
4. `parser.parse_llm_response()` 提取 JSON
5. `validator.validate_workflow_plan()` 执行 250 行严格校验：
   - 13 个必填顶层字段检查
   - 8 个子对象必填字段检查
   - 枚举值校验（task_type, input_modality, split_strategy, search_method, budget_level, metric_direction）
   - n_splits 范围检查（2-10）
   - confidence_score 范围检查（0-1）
   - 数组类型检查
   - **禁止代码内容检查**（FORBIDDEN_CONTENT 含 20+ 个模式，如 "import pandas", "def train", "model.fit"）
   - **Featurizer Registry 校验**：验证 executable_featurizers 中的每个名称都在 Registry 中存在且状态为 available
6. 失败时写入失败记录（含 llm_request_json, llm_response_json, error_message）
7. `builder.build_workflow_plan()` 构建完整 plan JSON

**LLM 输出 Schema**（[prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py)）：
- task_summary（task_type, input_modality, prediction_target, material_domain, primary_goal）
- data_strategy（input_columns, target_column, required_cleaning_steps, target_handling, duplicate_handling, missing_value_strategy）
- feature_strategy（feature_type, executable_featurizers, recommended_featurizers, requires_structure_features, feature_selection_required, feature_scaling_required）
- model_strategy（candidate_model_families, baseline_models, preferred_model_bias, excluded_model_families）
- validation_strategy（split_strategy, n_splits, random_state, stratification_required）
- evaluation_strategy（primary_metric, secondary_metrics, metric_direction）
- hpo_strategy（enabled, search_method, budget_level, max_trials）
- interpretability_strategy（enabled, methods, priority）
- pipeline_generation_input（pipeline_steps, required_components）
- planning_warnings, planning_assumptions, llm_reasoning_summary, confidence_score

**输出**：
- `WorkflowPlanResponse`：含 workflow_plan_id, status, 以及上述所有策略子对象

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/api.py)）：
- `POST /api/workflow-plans/{task_id}` — 创建工作流规划
- `GET /api/workflow-plans/{workflow_plan_id}` — 获取工作流规划
- `GET /api/tasks/{task_id}/workflow-plan` — 获取任务的最新规划
- `POST /api/workflow-plans/{task_id}/rerun` — 重新运行规划

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/model.py)）：
- `WorkflowPlan` 表：id (PK), task_id (indexed), interpretation_id (indexed), dataset_profile_id (indexed), status (indexed), planning_mode, task_type, input_modality, primary_metric, feature_type, validation_strategy, hpo_enabled, interpretability_enabled, confidence_score, plan_json (JSONB), llm_request_json (JSONB), llm_response_json (JSONB), error_message, created_at (indexed), updated_at

**完成度**：~90%。核心 LLM 调用和校验逻辑完整。Validator 中的 Featurizer Registry 校验是关键的架构约束。

---

### 5.5 模块五：Feature Engineering（特征工程）

**文件位置**：[backend/app/modules/feature_engineering/](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/)

**输入**：
- `FeatureEngineeringCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/schemas.py)）：force_rerun
- 上游 TaskSpecification + TaskInterpretation + DatasetProfile + WorkflowPlan 数据

**处理逻辑**：
1. `context_builder.build_feature_engineering_context()` 校验四个上游模块状态
2. `data_loader_adapter.reload_raw_data()` 复用 Dataset Profile 的 Loader 重新加载原始数据
3. `strategy_resolver.resolve_feature_strategy()` 按三级优先级解析：
   - **优先级1**：`executable_featurizers`（通过 Registry 的 `resolve_to_available()` 校验）
   - **优先级2**：`recommended_featurizers`（legacy 字段，通过 Registry aliases 解析）
   - **优先级3**：Registry fallback（`get_default_fallback()` 返回最高优先级的可用 Featurizer）
4. `featurizer_router.get_executable_featurizers()` 将 Registry ID 映射到 Featurizer 实例
5. 运行 Featurizers（通过 `_run_featurizers()` 方法）：
   - **CompositionFeaturizer**（[composition_featurizer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/composition_featurizer.py)）：内置 103 种元素的属性表，生成 16 维描述符（原子序数/原子量/电负性的均值/最大/最小 + 元素计数 + 化学计量熵 + 元素比例 + 金属/过渡金属标记）
   - **DescriptorFeaturizer**（[descriptor_featurizer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/descriptor_featurizer.py)）：已有数值描述符直通
   - **DescriptorCleanerFeaturizer**（[descriptor_cleaner.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/descriptor_cleaner.py)）：增强版清洗器，含特征分组元数据
   - **PymatgenCompositionParserFeaturizer**（[pymatgen_composition_parser.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/pymatgen_composition_parser.py)）：使用 pymatgen 解析化学式
   - **Matminer Featurizers**（[matminer_featurizers.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/matminer_featurizers.py)）：四个 Featurizer（Stoichiometry ~8维, ElementProperty ~132维, Magpie ~132维, ValenceOrbital ~4维），含列名前缀 `{featurizer_id}__`、逐样本失败追踪、执行时间测量
   - **StructureFeaturizer**（[structure_featurizer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/structure_featurizer.py)）：占位符
6. `feature_matrix_builder.build_feature_matrix()` 构建特征矩阵（sample_id + features + target）
7. `feature_quality_checker.check_feature_quality()` 检查缺失值/常量特征/无效特征/高缺失率
8. `artifact_manager.save_feature_artifact()` 持久化特征矩阵（parquet/csv）+ metadata.json + 预览 JSON

**输出**：
- `FeatureEngineeringResponse`：含 feature_engineering_id, status, input_modality, feature_type, n_samples, n_features, artifact_id, artifact_path, feature_schema, feature_quality, downstream_input

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/api.py)）：
- `POST /api/feature-engineering/{task_id}` — 运行特征工程
- `GET /api/feature-engineering/{feature_engineering_id}` — 获取特征工程结果
- `GET /api/tasks/{task_id}/feature-engineering` — 获取任务的最新特征工程
- `POST /api/feature-engineering/{task_id}/rerun` — 重新运行
- `GET /api/feature-engineering/{feature_engineering_id}/preview` — 获取特征预览

**Featurizer Registry API**（[registry_api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/registry_api.py)）：
- `GET /api/registries/featurizers` — 列出所有 Featurizers（支持按 modality/task_type/status 过滤）
- `GET /api/registries/featurizers/{featurizer_id}` — 获取 Featurizer 详情
- `GET /api/registries/featurizers/dependencies` — 获取依赖状态
- `POST /api/registries/featurizers/validate` — 校验 Featurizer 名称

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/model.py)）：
- `FeatureEngineering` 表：id (PK), task_id (indexed), interpretation_id (indexed), dataset_profile_id (indexed), workflow_plan_id (indexed), status (indexed), input_modality, feature_type, n_samples, n_features, target_column, artifact_id, artifact_path, is_ready_for_pipeline, feature_json (JSONB), preview_json (JSONB), error_message, created_at (indexed), updated_at

**完成度**：~85%。核心 Featurizer 实现完整。Structure Featurizer 为占位符；matminer 依赖检测在 Registry 层面完成但 Featurizer 实例化时依赖懒加载。

---

### 5.6 模块六：Feature Preprocessing（特征预处理）

**文件位置**：[backend/app/modules/feature_preprocessing/](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/)

**输入**：
- `FeaturePreprocessingCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/schemas.py)）：force_rerun, max_missing_ratio, imputation_strategy, scaling_strategy, feature_selection_strategy
- 上游 TaskSpecification + TaskInterpretation + DatasetProfile + WorkflowPlan + FeatureEngineering 数据

**处理逻辑**（10 步流水线）：
1. `context_builder.build_preprocessing_context()` 校验五个上游模块状态 + artifact_path 存在性
2. `artifact_loader.load_raw_feature_matrix()` 加载 Feature Engineering 输出的 parquet/csv artifact
3. `feature_filter.filter_features()` 顺序执行 5 类过滤：
   - invalid（无效列）
   - all_missing（全空列）
   - constant（常量列）
   - high_missing（高缺失率列，阈值可配）
   - inf（Inf 值列）
4. `column_validator.py` 列级校验（无效列/全空列/常量列/高缺失列/Inf值检测）
5. `feature_group_validator.validate_feature_groups()` 按特征组统计保留/丢弃状态
6. `preprocessing_executor.execute_preprocessing()` 三步流水线：
   - **Imputation**（[imputer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/imputer.py)）：sklearn SimpleImputer 封装（median/mean/most_frequent）
   - **Scaling**（[scaler.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/scaler.py)）：sklearn Scaler 封装（Standard/Robust/MinMax）
   - **Feature Selection**（[feature_selector.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/feature_selector.py)）：sklearn VarianceThreshold 封装
7. `preprocessing_pipeline_builder.build_pipeline()` 构建 `PreprocessingPipeline` 复合管道类（可 joblib 序列化，含 `transform()` 方法）
8. `artifact_manager.save_model_ready_artifact()` 持久化：
   - `model_ready_features.parquet`（模型就绪特征矩阵）
   - `preprocessor.joblib`（预处理管道）
   - `preprocessing_metadata.json`
   - `validation_report.json`
   - `preview.json`
9. `builder.build_preprocessing_object()` 构建完整响应（含 model_search_input）
10. 持久化到数据库

**输出**：
- `FeaturePreprocessingResponse`：含 preprocessing_id, status, n_samples, n_raw_features, n_valid_features, n_final_features, n_dropped_features, model_ready_artifact_id/path, preprocessor_artifact_id/path, is_ready_for_model_search, validation_summary, column_filtering, feature_group_validation, preprocessing_execution, model_search_input

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/api.py)）：
- `POST /api/feature-preprocessing/{task_id}` — 运行特征预处理
- `GET /api/feature-preprocessing/{preprocessing_id}` — 获取预处理结果
- `GET /api/tasks/{task_id}/feature-preprocessing` — 获取任务的最新预处理
- `POST /api/feature-preprocessing/{task_id}/rerun` — 重新运行
- `GET /api/feature-preprocessing/{preprocessing_id}/preview` — 获取模型就绪数据预览

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/model.py)）：
- `FeaturePreprocessing` 表：id (PK), task_id (indexed), interpretation_id (indexed), dataset_profile_id (indexed), workflow_plan_id (indexed), feature_engineering_id (indexed), status (indexed), n_samples, n_raw_features, n_valid_features, n_final_features, n_dropped_features, target_column, model_ready_artifact_id/path, preprocessor_artifact_id/path, is_ready_for_model_search (indexed), preprocessing_json (JSONB), preview_json (JSONB), error_message, created_at (indexed), updated_at

**完成度**：~90%。核心预处理流水线完整。Categorical encoding 功能尚未实现（[encoder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/encoder.py) 为占位）；Feature Selection 仅支持 VarianceThreshold。

---

### 5.7 模块七：Model Search Context（模型搜索上下文更新）★ 新增

**文件位置**：[backend/app/modules/model_search_context/](file:///c:/projects/MLAgent/backend/app/modules/model_search_context/)

**输入**：
- `ModelSearchContextCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/model_search_context/schemas.py)）：force_rerun, use_llm_advisor, adjust_model_strategy, adjust_hpo_strategy, adjust_validation_strategy, adjust_evaluation_strategy
- 上游全部六个模块的数据

**处理逻辑**（12 步流水线）：
1. `context_builder.build_model_search_context()` 校验全部六个上游模块状态（task/interpretation/profile/plan/feature_engineering/feature_preprocessing），构建完整 context
2. `dataset_profile_analyzer.analyze_effective_dataset()` 分析有效数据集画像（样本量/原始特征数/最终特征数/丢弃特征数/特征降维比）
3. `feature_group_analyzer.analyze_feature_groups()` 分析特征组（保留组/丢弃组/部分保留组/低有效特征警告）
4. `preprocessing_analyzer.analyze_preprocessing()` 分析预处理执行状态（imputation/scaling/selection 是否执行）
5. 获取原始策略（model_strategy, hpo_strategy, validation_strategy, evaluation_strategy）
6. `llm_context_builder.build_llm_context()` 构建 LLM 上下文 prompt（含任务类型、目标列、主指标、数据集分析、特征组分析、预处理分析、原始策略）
7. `llm_strategy_advisor.LLMStrategyAdvisor.generate()` 调用 LLM 获取策略建议
8. `llm_response_parser.parse_llm_response()` 解析 LLM 响应 JSON
9. `llm_advice_validator.validate_llm_advice()` 校验 LLM 建议：
   - 模型族是否在 Model Registry 中存在
   - HPO 方法是否在 HPO Registry 中存在
   - 验证策略是否合法
   - 拒绝不合法的建议并记录
10. `strategy_merger.merge_strategies()` 合并策略（原始策略 + LLM 建议 + 数据分析结果 → 最终策略）
11. `builder.build_model_search_context_response()` 构建完整响应
12. 持久化到数据库

**LLM 输出 Schema**（[llm_context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/model_search_context/llm_context_builder.py)）：
- candidate_model_families（候选模型族列表）
- baseline_models（基线模型列表）
- preferred_model_bias（模型偏好）
- hpo_search_method（HPO 搜索方法）
- hpo_budget_level（HPO 预算级别：low/moderate/high）
- max_trials（最大试验次数）
- validation_split_strategy（验证分割策略）
- n_splits（分割数）
- adjustment_reasons（调整原因列表）
- risk_notes（风险提示列表）
- confidence_score（置信度）

**输出**：
- `ModelSearchContextResponse`：含 context_id, status, update_mode, dataset_effective_profile, feature_group_summary, preprocessing_summary, llm_strategy_advice, system_validation_result, strategy_adjustment, updated_model_strategy, updated_hpo_strategy, updated_validation_strategy, updated_evaluation_strategy, model_search_context_input

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/model_search_context/api.py)）：
- `POST /api/model-search-contexts/{task_id}` — 创建模型搜索上下文
- `GET /api/model-search-contexts/{context_id}` — 获取模型搜索上下文
- `GET /api/tasks/{task_id}/model-search-context` — 获取任务的最新上下文
- `POST /api/model-search-contexts/{task_id}/rerun` — 重新运行

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/model_search_context/model.py)）：
- `ModelSearchContext` 表：id (PK), task_id (indexed), workflow_plan_id (indexed), feature_engineering_id (indexed), feature_preprocessing_id (indexed), status (indexed), update_mode, task_type, target_column, n_samples, n_final_features, primary_metric, model_strategy_adjusted, hpo_strategy_adjusted, llm_used, llm_confidence_score, ready_for_model_search_plan (indexed), context_json (JSONB), llm_request_json (JSONB), llm_response_json (JSONB), error_message, created_at (indexed), updated_at

**完成度**：~85%。核心分析和策略合并逻辑完整。LLM 建议校验器依赖 Model Registry 和 HPO Registry；`evaluation_strategy_adjuster.py` 已创建但默认 `adjust_evaluation_strategy=False`。

---

### 5.8 模块八：Automated Model and HPO Search（自动化模型与超参数搜索规划）★ 新增

**文件位置**：[backend/app/modules/model_search/](file:///c:/projects/MLAgent/backend/app/modules/model_search/)

**输入**：
- `ModelSearchPlanCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/schemas.py)）：force_rerun, use_llm_advisor, max_total_trials_override, preferred_search_method, include_models, exclude_models
- 上游 ModelSearchContext 的 `model_search_context_input` + Model Registry + HPO Registry

**处理逻辑**（12 步流水线）：
1. `context_builder.build_model_search_context()` 读取模块七的最新 ModelSearchContext，校验 `ready_for_model_search_plan = true`，加载 Model Registry 和 HPO Registry，构建包含 task_type/primary_metric/n_samples/n_features/allowed_model_families/allowed_hpo_methods 的完整 context
2. `llm_prompt_builder.build_llm_model_search_prompt()` 构建 LLM prompt（含 10 条 CRITICAL 安全规则 + 严格 JSON Schema + allowed lists）
3. `llm_model_search_advisor.LLMModelSearchAdvisor.generate()` 复用模块二的 `LLMClient` 调用 LLM 获取结构化模型搜索建议
4. `llm_response_parser.parse_llm_model_search_response()` 解析 LLM 响应：去除 markdown 代码块 → JSON 解析 → Pydantic `LLMModelSearchSuggestion` Schema 校验
5. `llm_advice_validator.validate_llm_advice()` 执行五层校验：
   - **安全扫描**：14 种代码模式检测（`import`, `def`, `.fit(`, `optuna.create_study`, `sklearn.` 等）
   - **Model Registry 校验**：recommended_model_ids 和 baseline_model_ids 是否在 Registry 中存在
   - **HPO Registry 校验**：hpo_recommendation.search_method 是否在 HPO Registry 中存在
   - **trial 数上限检查**：`max_total_trials` 不超过 `settings.MODEL_SEARCH_MAX_TOTAL_TRIALS`（默认 50）
   - **置信度范围检查**：`confidence_score` 在 [0, 1] 范围内
   - 记录 rejected_models / rejected_hpo_methods / fallback_applied
6. `candidate_model_selector.select_candidate_models()` 根据 LLM 建议 + Registry + 用户 include/exclude 覆盖，生成三类模型的列表：
   - **baseline_models**：dummy_mean（non-HPO baseline）、ridge（strong_baseline，启用 HPO）
   - **candidate_models**：每个候选模型含 model_id, model_family, priority（high/medium/low）、hpo_enabled, reason
   - **excluded_models**：被排除的模型及原因
7. `hpo_plan_builder.build_hpo_plan()` 生成 HPO 计划：
   - search_method（优先用户指定 > LLM 建议 > 默认 random_search）
   - budget_level（基于样本量和特征数推断：< 200/low, < 1000/moderate, >= 1000/high）
   - max_total_trials / max_parallel_trials
   - trial_allocation（按 priority 权重分配：high=3, medium=2, low=1）
   - early_stopping 标记 / fallback_method
8. `search_space_builder.build_search_space_plan()` 基于内置模板生成每个模型的超参数搜索空间：
   - 内置 10 个模型 × 2 种任务类型的参数模板（ridge, lasso, elastic_net, random_forest, gradient_boosting, xgboost, svr, knn, linear_regression, dummy_mean）
   - 支持 space_width 自适应调整（narrow→缩窄范围，wide→扩大范围）
   - LLM 只能建议 `search_space_profile`，最终参数空间由系统模板生成
9. `validation_plan_builder.build_validation_plan()` 从上游策略继承验证计划（split_strategy, n_splits, random_state, shuffle 等）
10. `evaluation_plan_builder.build_evaluation_plan()` 从上游策略继承评价计划（primary_metric, metric_direction, secondary_metrics），含 14 个常见指标的 metric_direction 映射
11. `pipeline_input_builder.build_pipeline_generation_input()` 构建下游 Pipeline Generation 的输入对象（含 model_ready_matrix_path, feature_columns, 所有计划的 dict + ready_for_pipeline_generation 标记）
12. `builder.build_model_search_plan_response()` 构建完整响应（含 plan_json），持久化到数据库

**LLM 输出 Schema**（[llm_prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/llm_prompt_builder.py)）：
- `recommended_model_ids`（候选模型 ID 列表，只能在 allowed_model_families 中选择）
- `baseline_model_ids`（基线模型 ID 列表）
- `excluded_model_ids`（排除模型及原因）
- `hpo_recommendation`（enabled, search_method, budget_level, max_total_trials）
- `search_space_profile`（space_width: narrow/moderate/wide, prefer_conservative_ranges）
- `model_priority_notes`（每模型的优先级和原因）
- `risk_notes`（风险提示列表）
- `confidence_score`（置信度 0-1）

**输出**：
- `ModelSearchPlanResponse`：含 model_search_plan_id, status, planning_mode, dataset_context, candidate_model_plan（baseline/candidate/excluded 三组）, hpo_plan（method/budget/trial_allocation）, search_space_plan（每模型参数空间）, validation_plan, evaluation_plan, llm_model_search_advice, system_validation_result, pipeline_generation_input
- `ModelSearchPlanSummaryResponse`：摘要接口返回

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/api.py)）：
- `POST /api/model-search-plans/{task_id}` — 创建模型搜索计划
- `GET /api/model-search-plans/{model_search_plan_id}` — 获取模型搜索计划
- `GET /api/tasks/{task_id}/model-search-plan` — 获取任务的最新模型搜索计划
- `POST /api/model-search-plans/{task_id}/rerun` — 重新生成（不覆盖旧记录）
- `GET /api/model-search-plans/{model_search_plan_id}/summary` — 获取计划摘要（前端快速展示）

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/model.py)）：
- `ModelSearchPlan` 表：id (PK), task_id (indexed), model_search_context_id (indexed), feature_preprocessing_id (indexed), workflow_plan_id (indexed), status (indexed), planning_mode, task_type, target_column, primary_metric, n_samples, n_features, n_candidate_models, hpo_enabled, hpo_method, max_total_trials, ready_for_pipeline_generation (indexed), llm_used, llm_confidence_score, plan_json (JSONB), llm_request_json (JSONB), llm_response_json (JSONB), error_message, created_at (indexed), updated_at

**关键设计约束**：
1. **LLM 只输出结构化 JSON**：LLM 不输出任何代码、不直接指定参数空间、不训练模型、不执行 HPO
2. **系统生成最终计划**：候选模型必须经 Registry 校验；HPO 方法必须经 HPO Registry 校验；搜索空间必须由系统内置模板生成；trial 分配由系统按优先级权重计算
3. **安全扫描**：`llm_advice_validator.py` 含 14 个正则模式扫描 LLM 输出中的可执行代码
4. **不倒置职责**：本模块生成计划，不训练模型、不执行 HPO、不计算指标、不生成 Pipeline 代码

**前端面板**（[ModelSearchPlanPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/modelSearch/components/ModelSearchPlanPanel.tsx)）：
- 提供 "Generate Model Search Plan" 和 "Re-run Plan" 两个按钮
- 展示 12 个子区：Dataset Context / Candidate Model Plan（baseline + candidate 表格 + excluded） / HPO Plan（method/budget/trial allocation 表格） / Search Space Plan（每模型参数表格） / Validation Plan / Evaluation Plan / LLM Advice / System Validation Result / Pipeline Generation Input / Warnings / Errors / Full JSON

**完成度**：~85%。核心 12 步流水线完整。LLM 深度参与策略建议但受 Registry 约束；搜索空间模板覆盖 10 个模型族；安全校验包含代码注入扫描。尚未与 Pipeline Generation 模块对接（该模块尚未实现）。

---

### 5.9 Featurizer Registry（共享能力注册表）

**文件位置**：[backend/app/shared/registry/](file:///c:/projects/MLAgent/backend/app/shared/registry/)

**Featurizer Registry**（[featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py)）：
- 11 个 `FeaturizerSpec` 静态定义（含 id, display_name, description, input_modalities, feature_type, supported_task_types, aliases, status, mvp_supported, requires_dependencies, dependency_status, output_feature_kind, estimated_feature_count, fallback_priority）
- 核心 Featurizer 列表：
  1. `basic_composition` — 内置 16 维元素属性描述符（103 种元素），fallback_priority=100
  2. `pymatgen_composition_parser` — pymatgen 配方解析器
  3. `matminer_stoichiometry` — Stoichiometry 特征（~8 维），依赖 pymatgen+matminer
  4. `matminer_element_property` — ElementProperty 特征（~132 维），依赖 pymatgen+matminer
  5. `matminer_magpie` — Magpie 特征（~132 维），依赖 pymatgen+matminer
  6. `matminer_valence_orbital` — ValenceOrbital 特征（~4 维），依赖 pymatgen+matminer
  7. `descriptor_cleaner` — 增强版描述符清洗器（含特征分组元数据）
  8. `descriptor_direct` — 已有数值描述符直通
  9. `structure_basic` — 结构基本特征（planned，尚未实现）
  10. `matminer_structure_basic` — matminer 结构基本特征（planned，尚未实现）
  11. `text_embedding` — 文本嵌入特征（planned，尚未实现）
- 核心函数：
  - `get_featurizer_by_id(featurizer_id)` — 按 ID 精确查找
  - `resolve_featurizer_name(name)` — 按 ID 或 alias 模糊查找
  - `resolve_to_available(names)` — 批量解析并过滤到仅 available 的 Featurizer
  - `get_default_fallback(input_modality, task_type)` — 获取最高 fallback_priority 的可用 Featurizer
  - `check_dependencies()` — 检测 pymatgen/matminer 等外部依赖是否安装
  - `list_featurizers(filters)` — 按条件过滤列表

**Model Registry**（[model_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/model_registry.py)）：
- 10 个模型族定义：dummy_mean, linear, ridge, lasso, elastic_net, random_forest, gradient_boosting, xgboost, svr, knn
- 每个模型族含：id, display_name, model_family, supported_task_types, requires_scaling, handles_missing, interpretability_level, typical_n_features_range, typical_n_samples_range, training_cost, hpo_importance, is_baseline_candidate, aliases
- 核心函数：`get_model_by_id()`, `resolve_model_name()`, `list_models()`, `get_baseline_candidates()`

**HPO Registry**（[hpo_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/hpo_registry.py)）：
- 5 个 HPO 方法定义：random_search, grid_search, optuna_tpe, bayesian, successive_halving
- 每个方法含：id, display_name, method_type, supported_task_types, typical_budget_level, parallelizable, requires_gradient, min_trials, max_trials, aliases
- 核心函数：`get_hpo_method_by_id()`, `resolve_hpo_method_name()`, `list_hpo_methods()`, `get_methods_by_budget_level()`

**完成度**：~90%。三个 Registry 的静态定义和查询 API 完整。Featurizer Registry 的依赖检测在运行时执行；Model Registry 和 HPO Registry 目前仅被模块七的 LLM 建议校验器使用。

---

## 6. 系统数据流与调用链路

### 6.1 完整端到端数据流

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 1: 用户输入                                                          │
│                                                                          │
│ 用户浏览器 ──POST /api/tasks──→ TaskSpecificationService.create_task()    │
│   ├── 生成 task_id (task_{uuid8})                                        │
│   ├── normalize_fields() 标准化                                          │
│   ├── validate() 四步校验                                                │
│   └── 持久化到 TaskSpecification 表                                      │
│                                                                          │
│ 用户浏览器 ──POST /api/dataset-profiles/upload──→ 文件上传到 /app/uploads/ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 2: LLM 任务理解                                                      │
│                                                                          │
│ POST /api/task-interpretations/{task_id}                                 │
│   └── TaskInterpretationService.create_interpretation()                  │
│       ├── task_spec_adapter.adapt_task_spec() → LLM context              │
│       ├── prompt_builder.build_prompt() → system + user messages         │
│       ├── LLMClient.generate() → httpx POST to OpenAI API                │
│       ├── parser.parse_llm_response() → 提取 JSON                        │
│       ├── validator.validate_interpretation() → 结构/枚举/置信度校验      │
│       ├── builder.build_interpretation() → 完整 interpretation JSON      │
│       └── 持久化到 TaskInterpretation 表                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 3: 数据集加载与画像                                                   │
│                                                                          │
│ POST /api/dataset-profiles/{task_id}                                     │
│   └── DatasetProfileService.create_dataset_profile()                     │
│       ├── context_builder.build_dataset_loading_context()                │
│       │   └── 校验 task_spec.status + interpretation.status              │
│       ├── source_resolver.resolve_source() → 数据源类型识别               │
│       ├── MatbenchLoader / FileLoader.load() → pandas DataFrame          │
│       ├── schema_checker.check_schema()                                  │
│       ├── modality_checker.check_modality()                              │
│       ├── quality_checker.check_quality()                                │
│       ├── target_checker.check_target()                                  │
│       ├── profiler.py → 质量评级 + 推荐下一步                              │
│       ├── builder.build_dataset_profile() → 完整 profile JSON            │
│       └── 持久化到 DatasetProfile 表                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 4: LLM 工作流规划                                                    │
│                                                                          │
│ POST /api/workflow-plans/{task_id}                                       │
│   └── WorkflowPlanService.create_workflow_plan()                         │
│       ├── context_builder.build_workflow_planning_context()              │
│       │   └── 校验 task + interpretation + profile 状态                  │
│       ├── prompt_builder.build_prompt() → 超长 system prompt             │
│       ├── WorkflowPlanningLLMAdapter → 复用 LLMClient                    │
│       ├── parser.parse_llm_response() → 提取 JSON                        │
│       ├── validator.validate_workflow_plan() → 250 行严格校验             │
│       │   ├── 13 个必填字段 + 8 个子对象                                  │
│       │   ├── 枚举值 + 范围校验                                           │
│       │   ├── 禁止代码内容检查 (20+ 模式)                                  │
│       │   └── Featurizer Registry 校验                                   │
│       ├── builder.build_workflow_plan() → 完整 plan JSON                 │
│       └── 持久化到 WorkflowPlan 表                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 5: 特征工程                                                          │
│                                                                          │
│ POST /api/feature-engineering/{task_id}                                  │
│   └── FeatureEngineeringService.create_feature_engineering()             │
│       ├── context_builder.build_feature_engineering_context()            │
│       │   └── 校验 task + interpretation + profile + plan 状态           │
│       ├── data_loader_adapter.reload_raw_data() → 重新加载原始数据        │
│       ├── strategy_resolver.resolve_feature_strategy()                   │
│       │   ├── 优先级1: executable_featurizers → Registry 校验            │
│       │   ├── 优先级2: recommended_featurizers → aliases 解析            │
│       │   └── 优先级3: Registry fallback                                 │
│       ├── featurizer_router → ID → Featurizer 实例                       │
│       ├── _run_featurizers() → 逐个执行 Featurizer.featurize()           │
│       ├── feature_matrix_builder.build_feature_matrix()                  │
│       ├── feature_quality_checker.check_feature_quality()                │
│       ├── artifact_manager.save_feature_artifact()                       │
│       │   └── → /app/artifacts/features/{fe_id}/features.parquet         │
│       └── 持久化到 FeatureEngineering 表                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 6: 特征预处理                                                        │
│                                                                          │
│ POST /api/feature-preprocessing/{task_id}                                │
│   └── FeaturePreprocessingService.create_feature_preprocessing()         │
│       ├── context_builder → 校验 5 个上游模块 + artifact_path 存在性      │
│       ├── artifact_loader → 加载 features.parquet                        │
│       ├── feature_filter → 5 类过滤 (invalid/all_missing/constant/...)   │
│       ├── column_validator → 列级校验                                    │
│       ├── feature_group_validator → 特征组统计                           │
│       ├── preprocessing_executor → Imputation → Scaling → Selection      │
│       ├── preprocessing_pipeline_builder → PreprocessingPipeline         │
│       ├── artifact_manager.save_model_ready_artifact()                   │
│       │   ├── → /app/artifacts/model_ready/{fmp_id}/model_ready_features.parquet │
│       │   └── → /app/artifacts/model_ready/{fmp_id}/preprocessor.joblib  │
│       └── 持久化到 FeaturePreprocessing 表                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 7: 模型搜索上下文更新 ★ 新增                                          │
│                                                                          │
│ POST /api/model-search-contexts/{task_id}                                │
│   └── ModelSearchContextService.create_model_search_context()            │
│       ├── context_builder → 校验 6 个上游模块状态                         │
│       ├── dataset_profile_analyzer → 有效数据集画像分析                   │
│       ├── feature_group_analyzer → 特征组分析                            │
│       ├── preprocessing_analyzer → 预处理执行分析                         │
│       ├── llm_context_builder → 构建 LLM 上下文 prompt                   │
│       ├── llm_strategy_advisor → 调用 LLM 获取策略建议                    │
│       ├── llm_response_parser → 解析 LLM 响应                            │
│       ├── llm_advice_validator → 校验 LLM 建议                           │
│       │   ├── 模型族 ∈ Model Registry                                    │
│       │   └── HPO 方法 ∈ HPO Registry                                    │
│       ├── strategy_merger → 合并策略                                     │
│       ├── builder → 构建完整响应                                          │
│       └── 持久化到 ModelSearchContext 表                                 │
│                                                                          │
│ 输出: Updated Strategies (供下游 Model Search 消费)                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 8: 自动化模型与超参数搜索规划 ★ 新增                                  │
│                                                                          │
│ POST /api/model-search-plans/{task_id}                                   │
│   └── ModelSearchService.create_model_search_plan()                      │
│       ├── context_builder.build_model_search_context()                   │
│       │   └── 读取模块七最新 MSC → 校验 ready_for_model_search_plan=true   │
│       │   └── 加载 Model Registry + HPO Registry                         │
│       ├── llm_prompt_builder.build_llm_model_search_prompt()             │
│       │   └── 构建 system prompt（10 条安全规则）+ user message（JSON Schema） │
│       ├── LLMModelSearchAdvisor.generate() → LLMClient                   │
│       │   └── httpx POST → 获取 structured model search advice           │
│       ├── llm_response_parser.parse_llm_model_search_response()          │
│       │   └── 去 markdown → JSON 解析 → Pydantic Schema 校验              │
│       ├── llm_advice_validator.validate_llm_advice()                     │
│       │   ├── 安全扫描（14 种代码模式检测）                                 │
│       │   ├── Model Registry 校验（recommended + baseline IDs）           │
│       │   ├── HPO Registry 校验（search_method + max_trials 上限）         │
│       │   └── → 拒绝不合法的建议，记录 rejected_models/hpo_methods          │
│       ├── candidate_model_selector.select_candidate_models()             │
│       │   └── LLM advice + Registry + include/exclude → baseline/candidate/excluded │
│       ├── hpo_plan_builder.build_hpo_plan()                              │
│       │   └── method/budget/trial_allocation/parallel/fallback           │
│       ├── search_space_builder.build_search_space_plan()                 │
│       │   └── 基于内置模板（10 模型 × 2 任务类型）生成每模型参数空间          │
│       ├── validation_plan_builder / evaluation_plan_builder              │
│       │   └── 从上游策略继承并规范化                                       │
│       ├── pipeline_input_builder.build_pipeline_generation_input()       │
│       │   └── 构建下游 Pipeline Generation 输入（含 ready 标记）            │
│       ├── builder.build_model_search_plan_response() → 完整 plan JSON    │
│       └── 持久化到 ModelSearchPlan 表                                     │
│                                                                          │
│ 输出: Model Search Plan (供下游 Pipeline Generation 消费)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 关键调用链路

**LLM 调用链路**（模块二、四、七、八共享模式）：
```
Service.create_*()
  → context_builder.build_*_context()     # 校验上游 + 构建 context
  → prompt_builder.build_prompt()         # 构建 system/user prompt
  → LLMClient.generate()                  # httpx POST → OpenAI API
  → parser.parse_llm_response()           # 正则提取 JSON
  → validator.validate_*()                # 结构/枚举/Registry 校验
  → builder.build_*()                     # 构建完整 JSON
  → repository.create()                   # 持久化
```

**Artifact 传递链路**：
```
FeatureEngineeringService
  → artifact_manager.save_feature_artifact()
    → /app/artifacts/features/{fe_id}/features.parquet

FeaturePreprocessingService
  → artifact_loader.load_raw_feature_matrix()
    ← /app/artifacts/features/{fe_id}/features.parquet
  → preprocessing_executor.execute_preprocessing()
  → artifact_manager.save_model_ready_artifact()
    → /app/artifacts/model_ready/{fmp_id}/model_ready_features.parquet
    → /app/artifacts/model_ready/{fmp_id}/preprocessor.joblib

ModelSearchContextService
  → context_builder.build_model_search_context()
    ← 读取 FeaturePreprocessing 表中的 artifact_path
  → 分析后输出 Updated Strategies (JSON, 存入数据库)

ModelSearchService
  → context_builder.build_model_search_context()
    ← 读取 ModelSearchContext 表中的 model_search_context_input
    ← 加载 Model Registry + HPO Registry
  → LLM advisor → validator → candidate_selector → hpo_builder → search_space_builder
  → 输出 Model Search Plan (JSON, 存入 ModelSearchPlan 表)
```

---

## 7. 核心代码与关键设计说明

### 7.1 统一异常体系

**基础异常类**（[shared/common/exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)）：

```python
class BusinessException(Exception):
    """所有业务异常的基类"""
    def __init__(self, message: str, error_code: str = "BUSINESS_ERROR"):
        self.message = message
        self.error_code = error_code

class ValidationException(BusinessException): ...
class NotFoundException(BusinessException): ...
class DatabaseException(BusinessException): ...
```

每个模块有自己的异常子类，例如：
- 模块二：[task_interpretation/exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/exceptions.py) — `TaskNotReadyException`, `LLMCallException`, `ParseException`, `ValidationException`, `TaskInterpretationNotFoundException`
- 模块五：[feature_engineering/exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/exceptions.py) — 20 个细分异常类型
- 模块六：[feature_preprocessing/exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/exceptions.py) — 12 个专用异常
- 模块七：[model_search_context/exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/model_search_context/exceptions.py) — `ModelSearchContextNotFoundException`, `UpstreamNotReadyException`, `LLMCallException` 等

**全局异常处理**（[main.py](file:///c:/projects/MLAgent/backend/app/main.py)）：
```python
@app.exception_handler(BusinessException)
async def business_exception_handler(request, exc: BusinessException):
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": exc.message, "error_code": exc.error_code}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"}
    )
```

### 7.2 统一响应格式

**定义**（[shared/common/response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py)）：

```python
class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str = ""
    data: Optional[T] = None

def success_response(data=None, message="Success") -> dict:
    return {"success": True, "message": message, "data": data}

def error_response(message="Error", error_code="UNKNOWN_ERROR") -> dict:
    return {"success": False, "message": message, "error_code": error_code}
```

所有 API 接口返回格式统一为 `{"success": bool, "message": str, "data": ...}`。

### 7.3 数据库设计

**连接管理**（[shared/database/connection.py](file:///c:/projects/MLAgent/backend/app/shared/database/connection.py)）：
```python
engine = create_engine(settings.DATABASE_URL, echo=settings.DEBUG)
```

**会话管理**（[shared/database/session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py)）：
```python
def get_session():
    with Session(engine) as session:
        yield session
```

**建表策略**（[main.py](file:///c:/projects/MLAgent/backend/app/main.py)）：
```python
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)
```

所有数据模型使用 SQLModel 定义，核心字段使用 JSONB 存储非结构化数据（如 `task_spec_json`, `interpretation_json`, `plan_json`, `feature_json`, `preprocessing_json`, `context_json`）。

### 7.4 配置管理

**Settings 类**（[shared/config/settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)）：
- 使用 `pydantic-settings` 的 `BaseSettings`
- 所有配置项有默认值，可通过环境变量覆盖
- 配置分组：数据库、LLM、数据上传、特征工程、特征预处理、模型搜索上下文

关键配置项：
- `DATABASE_URL` — PostgreSQL 连接字符串
- `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL` — LLM API 配置
- `UPLOAD_DIR` — 文件上传目录（默认 `/app/uploads`）
- `FEATURE_ARTIFACT_DIR` — 特征 artifact 目录（默认 `/app/artifacts/features`）
- `MODEL_READY_ARTIFACT_DIR` — 模型就绪 artifact 目录（默认 `/app/artifacts/model_ready`）

### 7.5 Repository 模式

所有模块的数据访问层使用统一的 Repository 模式：
- 每个模块有独立的 `repository.py`
- 提供标准 CRUD 方法：`create()`, `get_by_id()`, `update()`, `delete()`
- 提供模块特有方法：`get_latest_by_task_id()`, `list_by_task_id()`, `exists()`
- 使用 MyBatis-Plus 风格的 `LambdaQueryWrapper` 构建查询条件

### 7.6 LLM 客户端设计

**LLMClient**（[task_interpretation/llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)）：
- 使用 `httpx` 调用 OpenAI 兼容 API
- 支持最多 2 次重试（指数退避）
- 记录 `llm_request_json` 和 `llm_response_json` 到数据库
- 模块四通过 `llm_client_adapter.py` 复用
- 模块七通过 `llm_strategy_advisor.py` 独立实现（含自己的重试逻辑）

### 7.7 策略模式应用

**Data Loaders**（[dataset_profile/loaders/](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/)）：
- `BaseLoader` 抽象基类
- `MatbenchLoader` — Matbench 数据集加载
- `FileLoader` — 用户上传文件加载

**Featurizers**（[feature_engineering/featurizers/](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/)）：
- `BaseFeaturizer` 抽象基类（含 `featurize()` 和 `featurizer_name()` 两个抽象方法）
- 6 个具体实现 + 2 个占位符

**Preprocessors**（[feature_preprocessing/preprocessors/](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/)）：
- `Imputer`, `Scaler`, `Encoder`（占位）, `FeatureSelector`

### 7.8 前端状态管理

- **无全局路由**：前端只有一个页面 `TaskSpecificationPage`，7 个面板嵌入其中
- **无 Pinia Store 的实际使用**：虽然定义了 `user.js` store，但各面板组件直接调用 API 并管理本地状态（`useState`）
- **API 层**：每个模块有独立的 API 文件，统一使用 `taskApi.ts` 中的 axios 单例（含 request/response 拦截器）
- **表单校验**：使用 `react-hook-form` + `zod` 进行前端校验

### 7.9 日志

- 所有模块使用 Python 标准 `logging` 模块
- 日志级别通过 `settings.DEBUG` 控制
- 关键操作（LLM 调用、Featurizer 执行、异常）均有日志记录

---

## 8. 当前未完成部分与后续开发建议

### 8.1 尚未实现的后续模块

| 模块 | 状态 | 说明 |
|------|------|------|
| **Model Search** | ✅ 已实现 | 模块八已实现：基于 Updated Strategies + Registry + LLM 建议生成 Model Search Plan |
| **Pipeline Generation** | 未实现 | 需要根据 Model Search Plan 生成可执行的 ML Pipeline |
| **Pipeline Execution** | 未实现 | 需要执行 Pipeline 并收集结果 |
| **Metric Evaluation** | 未实现 | 需要对模型结果进行评估 |
| **Result Diagnosis** | 未实现 | 需要对结果进行诊断分析 |
| **Report Generation** | 未实现 | 需要生成最终报告 |

### 8.2 半成品代码和占位符

| 文件 | 状态 | 说明 |
|------|------|------|
| [structure_featurizer.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/structure_featurizer.py) | 占位符 | 结构特征化器未实现 |
| [matminer_structure_basic.py](file:///c:/projects/MLAgent/backend/app/modules/feature_engineering/featurizers/matminer_structure_basic.py) | planned | matminer 结构基本特征未实现 |
| [encoder.py](file:///c:/projects/MLAgent/backend/app/modules/feature_preprocessing/preprocessors/encoder.py) | 占位符 | Categorical encoding 未实现 |
| `text_embedding` Featurizer | planned | Featurizer Registry 中定义为 planned |
| `structure_basic` Featurizer | planned | Featurizer Registry 中定义为 planned |
| `matminer_structure_basic` Featurizer | planned | Featurizer Registry 中定义为 planned |

### 8.3 潜在问题和改进建议

1. **模块二未强制校验 task_spec 状态**：`TaskNotReadyException` 已定义但 `create_interpretation()` 中未调用。建议在调用 `task_spec_adapter.adapt_task_spec()` 前添加状态校验。

2. **Matbench fallback 数据有限**：仅覆盖 4 个已知数据集（matbench_expt_gap, matbench_steels, matbench_dielectric, matbench_phonons），其他数据集引用会失败。

3. **前端无 React Router**：所有面板嵌入在一个页面中，历史任务查看不便。建议添加路由支持。

4. **缺少 API 版本管理**：建议添加 `/api/v1/` 前缀。

5. **缺少请求日志中间件和性能监控**：建议添加请求耗时日志。

6. **Feature Selection 仅支持 VarianceThreshold**：可扩展更多策略（如 SelectKBest, RFE, L1-based 等）。

7. **模块七的 evaluation_strategy_adjuster.py**：已创建但默认 `adjust_evaluation_strategy=False`，功能未启用。

8. **数据库迁移**：当前使用 `SQLModel.metadata.create_all` 自动建表，Alembic 已安装但未配置迁移脚本。生产环境建议使用 Alembic 管理数据库版本。

9. **并发和异步**：当前所有 Service 方法为同步方法，LLM 调用和特征工程可能阻塞。建议将耗时操作改为异步。

10. **测试覆盖**：项目中未发现单元测试或集成测试代码。

### 8.4 后续开发优先级建议

1. **高优先级**：实现 Pipeline Generation 和 Pipeline Execution（消费模块八的 pipeline_generation_input）
2. **高优先级**：实现 Metric Evaluation 和 Result Diagnosis 模块
3. **中优先级**：补全占位符功能（Structure Featurizer, Categorical Encoder）
4. **中优先级**：添加前端路由和任务列表页面
5. **低优先级**：添加 API 版本管理、请求日志、性能监控
6. **低优先级**：扩展 Feature Selection 策略、配置 Alembic 迁移

---

## 9. 给后续 AI Coding 大模型的开发提示

### 9.1 优先阅读的文件（按重要性排序）

1. **[main.py](file:///c:/projects/MLAgent/backend/app/main.py)** — 理解路由注册、CORS、异常处理
2. **[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)** — 理解所有配置项
3. **[featurizer_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/featurizer_registry.py)** — 理解 Featurizer 共享契约
4. **[model_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/model_registry.py)** — 理解模型族定义
5. **[hpo_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/hpo_registry.py)** — 理解 HPO 方法定义
6. **[exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)** — 理解异常体系
7. **[response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py)** — 理解统一响应格式
8. **[model_search/service.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/service.py)** — 理解最新的模块八（12 步流水线，代码模式最新）
9. **[model_search/search_space_builder.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/search_space_builder.py)** — 理解 10 模型 × 2 任务类型的内置超参数模板
10. **各模块的 `service.py`** — 理解每个模块的核心业务逻辑
11. **各模块的 `context_builder.py`** — 理解模块间依赖校验逻辑
12. **[taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts)** — 理解前端 API 配置

### 9.2 开发新模块时应遵循的模式

1. **模块结构模板**：每个模块应包含 `api.py`（路由）、`service.py`（业务逻辑）、`model.py`（数据模型）、`repository.py`（数据访问）、`schemas.py`（请求/响应 DTO）、`enums.py`（枚举）、`exceptions.py`（异常）、`builder.py`（构建响应）
2. **上游依赖校验**：新模块的 `context_builder.py` 必须校验所有上游模块的输出状态
3. **失败状态持久化**：失败时必须写入数据库（含 error_message）
4. **LLM 调用模式**：如需调用 LLM，参考模块二/四/七的 `prompt_builder → LLMClient → parser → validator` 模式
5. **Artifact 管理**：如需文件持久化，参考模块五/六的 `artifact_manager.py`

### 9.3 不要重复实现的功能

1. **Featurizer Registry** — 已在 `shared/registry/` 中实现，不要在各模块中硬编码 Featurizer 列表
2. **Model Registry** — 已定义 10 个模型族，新模块应查询 Registry 而非硬编码
3. **HPO Registry** — 已定义 5 个 HPO 方法，新模块应查询 Registry 而非硬编码
4. **超参数搜索空间模板** — 已在模块八 `search_space_builder.py` 中定义 10 模型 × 2 任务类型的模板，下游模块应查询 Model Search Plan 而非重新构建
5. **LLM 客户端** — 模块二的 `LLMClient` 可复用，不要重新实现 HTTP 调用逻辑
6. **统一异常处理** — 已在 `main.py` 中全局注册，新模块只需定义异常子类
7. **统一响应格式** — 使用 `success_response()` / `error_response()`，不要自定义响应格式
8. **数据库连接/会话管理** — 使用 `get_session()` 依赖注入
9. **Data Loaders** — 模块三的 `MatbenchLoader` / `FileLoader` 可复用
10. **Model Search Plan** — 模块八已输出完整的模型搜索计划（含 pipeline_generation_input），下游 Pipeline Generation 应消费该计划而非重新规划

### 9.4 关键边界和注意事项

1. **管道严格顺序**：模块一 → 二 → 三 → 四 → 五 → 六 → 七 → 八，不可跳过或乱序
2. **状态校验**：每个下游模块的 `context_builder.py` 会检查上游模块的状态值（如 `valid`, `interpreted`, `profiled`, `planned`, `completed`, `preprocessed`, `updated`, `planned`），状态不符则抛出专用异常
3. **JSONB 字段**：所有模块的核心数据存储在 JSONB 字段中（如 `task_spec_json`, `interpretation_json`, `plan_json`），读取时需注意可能为 `None`
4. **LLM 输出不可信**：所有 LLM 输出必须经过 `parser` + `validator` 两步处理
5. **Featurizer 名称校验**：Workflow Planning 的 Validator 会校验 `executable_featurizers` 中的名称是否在 Registry 中存在，因此 LLM Prompt 必须包含当前 Registry 的 Featurizer 列表
6. **Artifact 路径**：Feature Engineering 和 Feature Preprocessing 的 artifact 存储在文件系统中，下游模块通过数据库中的 `artifact_path` 字段定位
7. **前端超时配置**：Feature Engineering API 超时 600s，Feature Preprocessing API 超时 600s，Model Search Context API 超时 300s，Model Search Plan API 超时 300s，其他 API 超时 120s
8. **CORS 配置**：后端允许 `http://localhost:5173` 的跨域请求，生产环境需调整
9. **数据库初始化**：开发环境使用 `docker-compose up` 启动，首次启动会自动建表。如需重置数据，删除 PostgreSQL 卷后重新启动
10. **测试账号**：admin/password（管理员），2024000001/password（学生），100001/password（教师）— 所有账号密码均为 `password`

---

> **文档维护说明**：本文档应在每次重大功能更新后同步更新。更新时请保持章节结构不变，重点更新模块完成度、新增文件列表、数据流图和未完成部分。
