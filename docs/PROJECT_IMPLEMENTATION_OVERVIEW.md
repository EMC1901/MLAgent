# 项目已实现部分说明文档

> 文档生成日期：2026-05-07（全面更新版 — 含模块十三 LLM-driven Workflow Refinement + Closed-loop Iteration）
> 项目名称：MLAgent — AI-driven Automated Machine Learning Framework for Materials Science
> 文档用途：帮助后续 AI Coding 大模型和开发者快速理解当前项目已经完成的部分

---

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个面向材料科学领域的 AI 驱动自动化机器学习框架。其核心目标是让用户通过结构化表单提交材料机器学习任务需求，系统自动完成从**任务理解 → 数据加载 → 工作流规划 → 特征工程 → 特征预处理 → 模型搜索上下文更新 → 模型搜索计划生成 → 可执行流水线生成 → 流水线执行与训练 → 指标评估 → LLM 结果诊断 → LLM 工作流精炼（含闭环迭代）**的全流程自动化。当前尚未实现 Final Pipeline Selection / Interpretability Analysis / Final Output 等后续阶段。

### 1.2 当前实现阶段

当前项目已完成 **十三个核心业务模块** 的端到端实现：

| 模块 | 阶段 | 完成度 |
|------|------|--------|
| **模块一：Task Specification（任务规格录入与校验）** | MVP 已完成 | ~95% |
| **模块二：LLM-based Task Interpretation（基于大模型的任务理解）** | MVP 已完成 | ~90% |
| **模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）** | MVP 已完成 | ~90% |
| **模块四：Workflow Planning（LLM 驱动的工作流规划）** | MVP 已完成 | ~90% |
| **模块五：Feature Engineering（特征工程）** | MVP 已完成 | ~85% |
| **模块六：Feature Preprocessing（特征预处理）** | MVP 已完成 | ~90% |
| **模块七：Model Search Context（模型搜索上下文更新）** | MVP 已完成 | ~85% |
| **模块八：Automated Model and HPO Search（自动化模型与超参数搜索规划）** | MVP 已完成 | ~85% |
| **模块九：Executable Pipeline Generation（可执行流水线生成）** | MVP 已完成 | ~85% |
| **模块十：Pipeline Execution and Training（流水线执行与训练）** | MVP 已完成 | ~85% |
| **模块十一：Metric Evaluation（指标评估）** | MVP 已完成 | ~90% |
| **模块十二：LLM-based Result Diagnosis（基于大模型的结果诊断）** | MVP 已完成 | ~90% |
| **模块十三：LLM-driven Workflow Refinement（LLM 驱动的工作流精炼与闭环迭代）** ★ 最新 | MVP 已完成 | ~90% |
| **Featurizer Registry / Model Registry / HPO Registry / Pipeline Template Registry / Metric Registry（共享能力注册表）** | MVP 已完成 | ~90% |

当前**尚未实现**的后续模块包括：Final Pipeline Selection、Interpretability Analysis、Final Output 等。**注意**：`closed_loop_refinement/` 目录仅含残留的 `__pycache__` 文件（无源码），其功能已被模块十三（`workflow_refinement/`）取代。`workflow_refinement` 内置的 `iteration_rerun_plan` + `adopt_revised_plan` + 前端 "Adopt & Rerun" 闭环迭代流程实现了原定 Closed-loop Refinement 的全部需求。

### 1.3 项目整体架构

```
用户浏览器 (React SPA — 单一 TaskSpecificationPage，含 13 个嵌入式面板)
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
            ↓
    Pipeline Generation (12 步流水线：context → artifact → bind → specs → trial → validate → safety → LLM advisory review → execution input → bundle → response → persist)
            ↓
        Pipeline Bundle + Execution Input (供下游 Pipeline Execution 消费)
            ↓
    Pipeline Execution (12 步流水线：context → load_input → load_matrix → create_splits → expand_plan → setup_dir → execute_training → collect_artifacts → build_metric_input → save_artifacts → build_response → persist)
            ↓
        Training Artifacts + Metric Evaluation Input (供下游 Metric Evaluation 消费)
            ↓
    Metric Evaluation (13 步流水线：context → load_input → load_predictions → build_trial_info → evaluate_folds → aggregate_trials → aggregate_pipelines → rank → compare_baselines → build_diagnosis_input → save_artifacts → build_response → persist)
            ↓
        Metric Results + Model Ranking + Baseline Comparison + Result Diagnosis Input
            ↓
    Result Diagnosis (15 步流水线：context → load_input → optional_context → extract_evidence → system_checks → build_llm_context → build_prompt → call_llm → parse → validate → normalize → build_refinement_input → save_artifacts → build_response → persist)
            ↓
        Diagnosis Result + Closed-loop Refinement Input (供下游 Workflow Refinement 消费)
            ↓
    Workflow Refinement (14 步流水线：context → load_input → collect_history → build_llm_context → build_prompt → call_llm → parse → validate → scan_safety → normalize → validate_revised_plan → build_delta → build_rerun_plan_or_fpsi → save_artifacts → build_response → persist)
            ↓
        ├── Decision: PROCEED_NEXT_STAGE → Final Pipeline Selection Input (供下游 Final Pipeline Selection 消费)
        └── Decision: ITERATE_REFINEMENT → Revised WorkflowPlan (新 Plan) + Iteration Rerun Plan
                ↓ (通过 Adopt & Rerun 闭环)
            Re-execute pipeline stages from revised entry point → 回到 Result Diagnosis
```

### 1.4 核心设计原则（根据当前代码分析）

1. **管道式架构**：十二个模块严格按序依赖。每个下游模块的 `context_builder.py` 会校验所有上游模块的输出状态，状态不符则抛出专用异常。
2. **统一异常体系**：所有业务异常继承自 `BusinessException`（定义于 [exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)），每个模块有自己的异常子类，附带有语义化的 `error_code`。
3. **LLM 输出强约束**：模块二、模块四、模块七、模块八、模块九和模块十二均定义了严格的 JSON Schema，LLM 响应经过解析（`parser.py`）+ 校验（`validator.py`）+ 标准化（`normalizer.py`）三步才被认为有效。模块十和模块十一为纯系统执行模块，不调用 LLM。
4. **Featurizer Registry 作为共享契约**：Workflow Planning 的 Prompt 和 Validator、Feature Engineering 的 Strategy Resolver 都向 Registry 查询，而非各自维护硬编码列表。
5. **失败状态持久化**：所有模块在失败时都会将失败记录（含错误信息）写入数据库，不会静默丢失。
6. **Artifact 传递链**：Feature Engineering 输出特征矩阵 artifact → Feature Preprocessing 加载并处理后输出 model-ready artifact + preprocessor pipeline artifact → Model Search Context 分析后输出更新后的策略 → Model Search 基于策略和 Registry 生成模型搜索计划，供下游 Pipeline Generation 消费。
7. **多 Registry 共享架构**：除 Featurizer Registry 外，还有 [model_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/model_registry.py)（10 个模型族定义）和 [hpo_registry.py](file:///c:/projects/MLAgent/backend/app/shared/registry/hpo_registry.py)（5 个 HPO 方法定义）。模块八深度消费这两个 Registry，所有 LLM 推荐的模型和 HPO 方法必须经 Registry 校验。
8. **LLM 建议 + 系统生成分离**：模块八中 LLM 仅输出结构化建议（推荐哪些模型、HPO 预算），最终候选模型、HPO 方法、搜索空间必须由系统基于 Registry、模板和校验器生成。LLM 不输出可执行代码、不直接指定参数空间。
9. **LLM Advisory Review（顾问式审查）**：模块九的 LLM 审查定位于"顾问"而非"审批者"。LLM 输出仅作为参考建议（non-blocking），`ready_for_execution` 标记由 System Validator + Safety Checker + Artifact Manifest 三者共同决定，LLM 无权批准或拒绝执行。
10. **多级安全防护**：模块九在 Safety Checker 中扫描 15+ 种危险模式（import、eval、exec、subprocess 等），LLM Review Validator 额外扫描 25+ 种禁止内容模式，且 LLM Review Normalizer 自动剥离旧式审批字段（approval_status、needs_improvement 等），确保 LLM 不能越权。
11. **Controlled Executor 作为唯一训练入口**：模块十中所有模型训练必须通过 Controlled Executor 执行，使用 Model Registry 中注册的模型（通过 model_factory.py 的显式映射实例化），禁止 LLM 生成训练代码、禁止动态 import 模型类。训练仅使用上游 Pipeline Generation 输出的 execution_input_json 中的数据。
12. **轻量合同 + JSONB 补充模式**：模块十一的 metric_evaluation_input_json 中的 trial_results 为轻量摘要（仅 6 个字段），完整的 pipeline_role / model_family / trial_type / params 等元数据从 PipelineExecution 的 execution_json JSONB 中补充。这是一种"上游发轻量合同，下游按需从完整日志中提取"的设计模式，减少了合同字段的冗余。
13. **LLM 诊断只建议不执行**：模块十二的 LLM 只能输出结构化 JSON 诊断与建议，Prompt 明确禁止代码生成，Validator 扫描 14 种危险代码模式（import / def / class / eval / exec / subprocess 等），Normalizer 将所有 LLM 输出归一化为标准 Schema。LLM 失败时降级到 system rule-based fallback，不影响上游 Metric Evaluation 结果。
14. **证据驱动诊断**：每个 DiagnosticFinding 必须包含 evidence_items（含 evidence_type / source_module / source_field / value / interpretation），证据不足时强制标记 `evidence_strength: weak`，LLM 不能凭空断言。
15. **诊断类型别名映射**：模块十二的 `DIAGNOSIS_TYPE_ALIASES`（26 条映射）将 LLM 常见近义表达（如 `baseline_improvement` / `overfitting` / `underfit`）归一化为规范枚举值，避免因 LLM 输出的微小措辞差异导致整个诊断路径失败。
16. **LLM 决策双路径**：模块十三的 LLM 输出两种决策路径：`proceed_next_stage`（进入最终 Pipeline 选择）或 `iterate_refinement`（生成修订版 WorkflowPlan + 迭代重跑计划），每条路径有独立的 Pydantic Schema 约束和一致性校验。
17. **Adopt & Rerun 闭环迭代**：模块十三的 `adopt_revised_plan` 端点将 LLM 修订的 WorkflowPlan 持久化为新 Plan 记录（`planning_mode = "refinement_adopted"`），然后前端按 `iteration_rerun_plan.rerun_stages` 顺序重新执行各 pipeline 阶段，形成完整闭环。该机制完全取代了原有设计中的独立 `closed_loop_refinement` 模块。
18. **多迭代历史追踪**：模块十三的 `experiment_history_collector` 从 5 个上游模块（WorkflowRefinement, MetricEvaluation, ResultDiagnosis, ModelSearch, PipelineExecution）收集跨迭代的历史数据（最佳指标、指标趋势、重复诊断类型、已尝试模型族、失败率、运行时成本），供 LLM 做出跨迭代比较决策。
19. **Workflow Plan Delta**：模块十三的 `workflow_plan_delta_builder` 对原始和修订版 WorkflowPlan 逐 section 计算 diff（added / removed / changed），并关联变更原因到具体诊断发现，形成可追溯的变更审计链。

---

## 2. 当前目录结构说明

### 2.1 完整目录树（实际文件）

```
c:\projects\MLAgent/
├── backend/                                # 后端 FastAPI 项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI 入口，路由注册，CORS，异常处理，启动时建表
│   │   ├── modules/                       # 业务模块（十二个模块 + Featurizer Registry API）
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
│   │   │   └── model_search/             # 模块八：自动化模型与超参数搜索规划
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
│   │   │   └── pipeline_generation/      # 模块九：可执行流水线生成
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 6 个接口（POST, GET by id, GET by task, POST:/rerun, GET summary, GET execution-input）
│   │   │       ├── schemas.py            # PipelineGenerationCreateRequest, ArtifactManifest, ComponentBinding, PipelineSpec, TrialPlan, ExecutionInput, PipelineBundle, PipelineValidationResult, SafetyCheckResult, LLMAdvisoryReview 等 20+ 个子对象
│   │   │       ├── service.py            # 12 步流水线：context → artifact → bind → specs → trial → validate → safety → LLM advisory review → execution input → bundle → response → persist
│   │   │       ├── model.py              # PipelineGeneration (JSONB + pipeline_json + execution_input_json + llm_request/response_json)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id
│   │   │       ├── context_builder.py    # 读取模块八的 ModelSearchPlan，校验 ready_for_pipeline_generation=True，加载上游全部 8 个模块
│   │   │       ├── artifact_resolver.py  # Artifact 解析器：路径存在性 + 安全性校验（白名单机制，拒绝 .. 遍历）
│   │   │       ├── component_registry.py # Pipeline 组件注册表（validation_strategies + allowed_metrics 白名单）
│   │   │       ├── component_binder.py   # 组件绑定器：model_id / hpo_method / validation_strategy / metrics 绑定到 Registry
│   │   │       ├── pipeline_template_registry.py # Pipeline 模板注册表（4 个模板：tabular_regression/tabular_classification × basic/hpo）
│   │   │       ├── pipeline_spec_builder.py # Pipeline Spec 构建器：按模型生成 PipelineSpec（baseline/candidate/hpo_candidate 角色）
│   │   │       ├── trial_plan_builder.py # Trial 计划构建器：从上游 HPO plan 构建 TrialPlan + allocation
│   │   │       ├── pipeline_validator.py # Pipeline 校验器：8 项检查（structure/registry/artifact/task_type/search_space/trial/data_fields/execution_input）
│   │   │       ├── safety_checker.py     # 安全扫描器：15+ 种危险模式检测（import/eval/exec/subprocess/.fit()/Pipeline() 等）
│   │   │       ├── llm_review_prompt_builder.py # LLM 审查 Prompt 构建器（8 维度顾问式审查，严格 NOT-approver 定位）
│   │   │       ├── llm_pipeline_reviewer.py # LLM Pipeline Reviewer（复用 LLMClient，fallback 到标准 advisory 格式）
│   │   │       ├── llm_review_parser.py  # LLM 审查响应解析器（纯 JSON 提取）
│   │   │       ├── llm_review_validator.py # LLM 审查校验器（25+ 禁止内容模式 + 禁止字段集 + 枚举值校验）
│   │   │       ├── llm_review_normalizer.py # LLM 审查标准化器（核心：剥离旧式审批字段 → 标准 LLMAdvisoryReview，映射 approval→risk_level，数值 confidence_score→confidence_level，吸收 risk_notes/consistency_findings）
│   │   │       ├── execution_input_builder.py # Execution Input 构建器（构建下游 Pipeline Execution 合同）
│   │   │       ├── builder.py            # 构建 PipelineBundle + PipelineGenerationResponse
│   │   │       ├── enums.py              # PipelineGenerationStatus / GenerationMode / PipelineRole / PipelineProfile / ComponentType / TaskType / MetricDirection / SplitStrategy / ModelPriority
│   │   │       └── exceptions.py         # 10 个专用异常（PipelineGenerationNotFound / ModelSearchPlanRequired / ArtifactResolve / ComponentBinding / PipelineSpecBuild / PipelineValidation / PipelineSafety / LLMPipelineReview / ExecutionInputBuild 等）
│   │   │
│   │   │   └── pipeline_execution/       # 模块十：流水线执行与训练 ★ 最新
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 8 个接口（POST create, GET by id, GET latest by task, POST rerun, GET summary, GET trials, GET metric-evaluation-input, GET logs）
│   │   │       ├── schemas.py            # PipelineExecutionCreateRequest, FoldResultDTO, TrialResultDTO, PipelineRunResultDTO, MetricEvaluationInputDTO, TrainingArtifactManifestDTO, PipelineExecutionResponse 等 10+ 个子对象
│   │   │       ├── service.py            # 12 步流水线：context → load_input → load_matrix → create_splits → expand_plan → setup_dir → execute_training → collect_artifacts → build_metric_input → save_artifacts → build_response → persist
│   │   │       ├── model.py              # PipelineExecution (JSONB + execution_json + metric_evaluation_input_json + runtime_log_json)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id + update
│   │   │       ├── context_builder.py    # 读取模块九的 PipelineGeneration，校验 ready_for_execution=True，验证 execution_input_json 存在
│   │   │       ├── execution_input_loader.py # 加载和解析 upstream execution_input_json，校验 pipeline_specs/trial_plan/validation_plan/evaluation_plan
│   │   │       ├── data_matrix_loader.py # 加载 model_ready_features.parquet，校验路径安全（无 .. 遍历）、特征列和目标列存在性、NaN 检测
│   │   │       ├── validation_splitter.py # 创建训练/验证数据划分（含 _normalize_strategy() 将上游 k_fold_cross_validation 映射为 k_fold），支持 train_test_split/holdout/k_fold/stratified_k_fold
│   │   │       ├── execution_planner.py  # 展开 PipelineSpecs + TrialPlan → 扁平化 trial 计划列表（baseline→1 trial, fixed_params→1 trial, hpo_candidate→multi trials）
│   │   │       ├── model_factory.py      # 通过显式 sklearn 映射（非动态 import）从 Model Registry ID 创建模型实例（regression + classification），校验任务类型兼容性
│   │   │       ├── hpo_trial_generator.py # 解析上游 SearchSpaceItem 格式，生成 HPO trial 参数组合（支持 random_search 和 grid_search，含 log_uniform/uniform/choice 采样）
│   │   │       ├── controlled_executor.py # Controlled Executor — 唯一训练入口：迭代 trial plans，按 pipeline_run 分组执行，支持 sequential/limited_parallel 模式、timeout、fail_fast
│   │   │       ├── trial_runner.py       # 单 Trial 执行器：遍历验证划分，调用 fold_runner 逐 fold 训练，聚合跨 fold 平均指标
│   │   │       ├── fold_runner.py        # 单 Fold 执行器：训练模型 → 预测 → 计算原始指标（MAE/MSE/RMSE/R2/Accuracy）→ 保存 artifacts
│   │   │       ├── prediction_writer.py  # 保存预测结果（y_true + y_pred + sample_id + metadata）为 parquet 文件
│   │   │       ├── training_artifact_manager.py # 训练 artifact 管理：创建执行目录、保存模型/预测/manifest/trial_results/split_metadata/execution_result/metric_evaluation_input
│   │   │       ├── runtime_monitor.py    # 运行时环境监测：捕获 Python/sklearn/pandas/numpy 版本，构建结构化 runtime_log
│   │   │       ├── execution_state_tracker.py # 执行状态追踪：计算 completed/failed 计数（兼容 dict 和 Pydantic 对象），判定总体状态
│   │   │       ├── metric_input_builder.py # 构建下游 Metric Evaluation 输入（含 ready 标记、artifact 路径、trial 摘要）
│   │   │       ├── builder.py            # 构建 PipelineExecutionResponse（含 pipeline_run_results, trial_results, metric_evaluation_input, artifact_manifest）
│   │   │       ├── enums.py              # PipelineExecutionStatus / TrialStatus / TrialType / ExecutionMode / PipelineRole / SplitStrategy
│   │   │       └── exceptions.py         # 11 个专用异常（PipelineExecutionNotFound / PipelineGenerationRequired / PipelineGenerationNotReady / ExecutionInputInvalid / TrainingDataLoad / ValidationSplit / ModelInstantiation / TrialGeneration / TrialExecution / TrainingArtifactSave / MetricEvaluationInputBuild）
│   │   │
│   │   │   └── metric_evaluation/        # 模块十一：指标评估 ★ 最新
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 9 个接口（POST create, GET by id, GET latest by task, POST rerun, GET summary, GET ranking, GET trials, GET folds, GET result-diagnosis-input）
│   │   │       ├── schemas.py            # MetricEvaluationCreateRequest, FoldMetricResult, TrialMetricResult, PipelineMetricResult, ModelRankingItem, BaselineComparison, MetricValidationResult, EvaluationArtifactManifest, MetricSummary, ResultDiagnosisInput, MetricEvaluationResponse, MetricEvaluationSummaryResponse 等 14 个 DTO
│   │   │       ├── service.py            # 13 步流水线：context → load_input → load_predictions → build_trial_info → evaluate_folds → aggregate_trials → aggregate_pipelines → rank → compare_baselines → build_diagnosis_input → save_artifacts → build_response → persist
│   │   │       ├── model.py              # MetricEvaluation (JSONB + evaluation_json + result_diagnosis_input_json + metric_summary_json + model_ranking_json)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id + update
│   │   │       ├── context_builder.py    # 读取模块十的 PipelineExecution，校验 ready_for_metric_evaluation=True，验证 metric_evaluation_input_json 存在
│   │   │       ├── metric_input_loader.py # 加载和校验 metric_evaluation_input_json（含 task_type/target_column/primary_metric/metric_direction 必填字段检查）
│   │   │       ├── prediction_artifact_loader.py # 加载预测 parquet artifacts（路径安全校验 + 必填列检查 + y_true/y_pred 数值校验 + NaN/Inf 检测）
│   │   │       ├── metric_registry.py    # Metric Registry（5 个回归指标 MAE/MSE/RMSE/R2/MAPE + 5 个分类指标 Accuracy/Precision/Recall/F1/ROC_AUC，含 direction 和 task_type 约束）
│   │   │       ├── metric_calculator.py  # 纯 numpy 指标计算（MAE/RMSE/R2/MSE/MAPE/Accuracy/Precision/Recall/F1），无 sklearn 依赖
│   │   │       ├── fold_metric_evaluator.py # Fold 级指标评估（遍历 trial_fold_map，逐 fold 计算 primary_metric + 状态判定）
│   │   │       ├── trial_metric_aggregator.py # Trial 级指标聚合（跨 fold 聚合 mean/std/min/max + fold_values 列表 + 状态判定）
│   │   │       ├── pipeline_metric_aggregator.py # Pipeline 级指标聚合（按 model_id 聚合 trial 结果，含 best_trial 选取）
│   │   │       ├── model_ranker.py       # 模型与 Trial 排名（primary_metric + direction 排序 + std 平局决胜 + best_trial/best_model/best_pipeline_spec 选择）
│   │   │       ├── baseline_comparator.py # 基线比较器（按 pipeline_role 筛选 baseline vs candidate trials，计算最佳基线指标和改善量）
│   │   │       ├── metric_validator.py   # 指标结果校验（6 项检查：finiteness/presence/ranking_consistency/best_trial_existence/baseline_refs/diagnosis_input）
│   │   │       ├── result_diagnosis_input_builder.py # 构建下游 Result Diagnosis 输入（含 ready_for_result_diagnosis 标记）
│   │   │       ├── evaluation_artifact_manager.py # 评估 artifact 管理：创建 /app/artifacts/evaluation/{me_id}/ 目录，保存 metric_results/fold_metrics/trial_metrics/pipeline_metrics/model_ranking/baseline_comparison/result_diagnosis_input/manifest
│   │   │       ├── builder.py            # 构建 MetricEvaluationResponse 和 MetricEvaluationSummaryResponse
│   │   │       ├── enums.py              # MetricEvaluationStatus / TrialEvaluationStatus / MetricDirection / TaskType
│   │   │       └── exceptions.py         # 13 个专用异常（MetricEvaluationException / MetricEvaluationNotFound / PipelineExecutionRequired / PipelineExecutionNotReady / MetricEvaluationInputInvalid / PredictionArtifactLoad / MetricNotSupported / MetricCalculation / MetricAggregation / ModelRanking / BaselineComparison / ResultDiagnosisInputBuild / EvaluationArtifactSave）
│   │   │
│   │   │   └── result_diagnosis/          # 模块十二：LLM-based Result Diagnosis ★ 最新
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 7 个接口（POST create, GET by id, GET latest by task, POST rerun, GET summary, GET closed-loop-refinement-input, GET needs-fresh）
│   │   │       ├── schemas.py            # ResultDiagnosisCreateRequest, EvidenceItem, DiagnosticFinding, RootCauseHypothesis, SystemActionHint, RefinementRecommendation, OverallAssessment, EvidenceSummary, SystemDiagnosticChecks, LLMDiagnosisResult, SuggestedNextIterationProfile, ClosedLoopRefinementInput, DiagnosisArtifactManifest, ResultDiagnosisResponse, ResultDiagnosisSummaryResponse 等 14 个 DTO
│   │   │       ├── service.py            # 15 步流水线：context → load_input → optional_context → extract_evidence → system_checks → build_llm_context → build_prompt → call_llm → parse → validate → normalize → build_refinement_input → save_artifacts → build_response → persist；含 needs_fresh_diagnosis() 方法
│   │   │       ├── model.py              # ResultDiagnosis (SQLModel, table=True, JSONB + diagnosis_json + closed_loop_refinement_input_json + llm_request_json + llm_response_json + system_checks_json)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id + update + count_by_task_id
│   │   │       ├── context_builder.py    # 读取模块十一的 MetricEvaluation，校验 status ∈ {evaluated,evaluated_with_warning,partially_evaluated} 且 ready_for_result_diagnosis=True
│   │   │       ├── diagnosis_input_loader.py # 加载和校验 result_diagnosis_input_json（9 个必填字段检查）
│   │   │       ├── evidence_extractor.py # 证据提取器：6 类证据（metric/baseline/fold_stability/dataset/feature/pipeline）
│   │   │       ├── system_diagnostic_checker.py # 9 项规则诊断：性能/基线/稳定性/过拟合/欠拟合/特征不足/特征噪声/HPO 不足/数据质量（含可配置阈值）
│   │   │       ├── diagnostic_context_builder.py # 构建 LLM 诊断上下文（compact/standard/full 三种 profile）
│   │   │       ├── llm_prompt_builder.py  # System prompt（14 个诊断维度 + JSON Schema）+ user message 构建
│   │   │       ├── llm_result_diagnoser.py # LLM Result Diagnoser（复用 LLMClient 调用 LLM）
│   │   │       ├── llm_response_parser.py  # LLM 响应 JSON 解析（3 种策略：direct json/代码块提取/大括号提取）
│   │   │       ├── llm_diagnosis_validator.py # 诊断校验器：结构校验 + 枚举值校验 + 安全扫描（14 种代码模式 + 9 个禁止字段 + DIAGNOSIS_TYPE_ALIASES 26 条目别名支持）
│   │   │       ├── llm_diagnosis_normalizer.py # 诊断标准化器：canonicalize diagnosis_type，coerce supporting_findings int→str，Default fill
│   │   │       ├── refinement_input_builder.py # 闭环精炼输入构建器（含 ready_for_closed_loop_refinement 标记）
│   │   │       ├── diagnosis_artifact_manager.py # 诊断 artifact 管理：创建 /app/artifacts/diagnosis/{rd_id}/，保存 7 个 JSON 文件
│   │   │       ├── builder.py            # 构建 ResultDiagnosisResponse（含 llm_diagnosis / system_checks / evidence_summary / refinement_input / artifact_manifest）
│   │   │       ├── enums.py              # ResultDiagnosisStatus / DiagnosisMode / DiagnosisType / Severity / Confidence / EvidenceStrength / EvidenceType / TargetStage / RecommendationType / RefinementTarget 等 14 个枚举
│   │   │       └── exceptions.py         # 10 个专用异常（ResultDiagnosisException / ResultDiagnosisNotFound / MetricEvaluationRequired / MetricEvaluationNotReady / DiagnosisInputInvalid / EvidenceExtraction / SystemDiagnosis / DiagnosticContextBuild / LLMDiagnosisCall / LLMDiagnosisParse / RefinementInputBuild / DiagnosisArtifact 等）
│   │   │
│   │   │   └── workflow_refinement/       # 模块十三：LLM-driven Workflow Refinement ★ 最新
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # 9 个接口（POST create, GET by id, GET latest by task, POST rerun, GET revised-workflow-plan, GET iteration-rerun-plan, GET final-pipeline-selection-input, GET iteration-context, POST adopt）
│   │   │       ├── schemas.py           # WorkflowRefinementCreateRequest, WorkflowRefinementDecisionDTO, DecisionReasoning, EvidenceUsed, RefinementMetadata, RevisedWorkflowPlanResponse, WorkflowPlanDelta, IterationRerunPlan, SelectionPolicy, FinalPipelineSelectionInput, ExperimentHistorySummary, WorkflowRefinementValidationResult, LLMWorkflowRefinementResult, ArtifactManifest, WorkflowRefinementResponse 等 15 个 DTO
│   │   │       ├── service.py            # 14 步流水线：context → load_input → collect_history → build_llm_context → build_prompt → call_llm → parse → validate → scan_safety → normalize → validate_revised_plan → build_delta → build_rerun_or_fpsi → save_artifacts → build_response → persist；含 get_iteration_context_for_diagnosis() 和 adopt_revised_plan()
│   │   │       ├── model.py              # WorkflowRefinement (JSONB + 10+ JSONB 字段 + iteration_index + decision + ready_for_iteration + ready_for_final_pipeline_selection)
│   │   │       ├── repository.py         # CRUD + get_latest_by_task_id + list_by_task_id + get_by_result_diagnosis_id + update
│   │   │       ├── context_builder.py    # 读取模块十二的最新 ResultDiagnosis，校验 status ∈ {diagnosed,diagnosed_with_warning,fallback_diagnosed} 且 ready_for_closed_loop_refinement=True
│   │   │       ├── refinement_input_loader.py  # 加载和校验 closed_loop_refinement_input_json
│   │   │       ├── experiment_history_collector.py # 跨迭代实验历史收集：5 个上游模块 → ExperimentHistorySummary（最佳指标/指标趋势/重复诊断/已尝试模型/失败率/运行时成本）
│   │   │       ├── workflow_refinement_context_builder.py  # 构建 LLM 上下文（含 experiment_history + 10 个上游模块的 lazily loaded data，每个模块独立 try/except）
│   │   │       ├── llm_prompt_builder.py   # System prompt（11 个决策问题 + 禁止代码 + JSON Schema）+ user message（22 条 CRITICAL RULES）
│   │   │       ├── llm_workflow_refiner.py  # LLM Workflow Refiner（复用 LLMClient）
│   │   │       ├── llm_response_parser.py  # LLM 响应 JSON 解析（3 种策略）
│   │   │       ├── workflow_refinement_validator.py  # 决策校验 + 递归安全扫描（15 种代码模式 + 12 个禁止字段）
│   │   │       ├── workflow_refinement_normalizer.py  # 决策标准化器（decision/confidence/stage 模糊匹配 + null-consistency 强制 + 对象→字符串列表转换 + 对象→float 转换）
│   │   │       ├── revised_workflow_plan_validator.py  # 修订版 WorkflowPlan 结构校验（必填字段/子对象/枚举值/范围）
│   │   │       ├── workflow_plan_delta_builder.py  # Workflow Plan Diff 构建器（7 个 strategy section 逐字段比较）
│   │   │       ├── iteration_rerun_plan_builder.py  # 迭代重跑计划构建器（标准化列表/阈值/推导 rerun stages）
│   │   │       ├── final_selection_input_builder.py  # Final Pipeline Selection Input 构建器（含 selection_policy 标准化）
│   │   │       ├── refinement_artifact_manager.py  # 保存 9 个 JSON artifacts 到 /app/artifacts/workflow_refinement/{wr_id}/
│   │   │       ├── builder.py            # 构建 WorkflowRefinementResponse
│   │   │       ├── enums.py              # WorkflowRefinementStatus / WorkflowRefinementDecision / DecisionConfidenceLevel / RerunStage / VALID_* 集合 / RERUN_STAGE_RECOMMENDATIONS
│   │   │       └── exceptions.py         # 13 个专用异常（WorkflowRefinementException / WorkflowRefinementNotFound / ResultDiagnosisRequired / ResultDiagnosisNotReady / WorkflowRefinementInputInvalid / WorkflowRefinementContextBuild / LLMWorkflowRefinementCall / LLMWorkflowRefinementParse / LLMWorkflowRefinementValidation / RevisedWorkflowPlanValidation / IterationRerunPlanBuild / FinalSelectionInputBuild / WorkflowRefinementArtifactSave）
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
│   │       │   └── settings.py          # pydantic-settings：数据库/LLM/数据上传/特征工程/特征预处理/模型搜索上下文/模型搜索计划/流水线生成/流水线执行/指标评估/结果诊断 配置
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
│   │   │   ├── modelSearchApi.ts        # Model Search Plan API（超时 300s，含 LLM 调用）
│   │   │   ├── pipelineGenerationApi.ts  # Pipeline Generation API（超时 300s，含 LLM 审查）
│   │   │   ├── pipelineExecutionApi.ts   # Pipeline Execution API（超时 600s，含模型训练）
│   │   │   ├── metricEvaluationApi.ts    # Metric Evaluation API（超时 300s）
│   │   │   ├── resultDiagnosisApi.ts       # Result Diagnosis API（超时 300s，含 needs-fresh + iteration-context）
│   │   │   └── workflowRefinementApi.ts   # Workflow Refinement API（超时 600s，含 adopt）
│   │   ├── modules/                     # 业务模块（13 个面板）
│   │   │   ├── taskSpecification/       # 任务规格表单
│   │   │   │   ├── pages/TaskSpecificationPage.tsx  # 页面容器（含 13 个嵌入式面板）
│   │   │   │   ├── components/TaskSpecificationForm.tsx # 主表单（react-hook-form + zod，含 13 个嵌入式面板）
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
│   │   │   └── modelSearch/              # 自动化模型与超参数搜索面板
│   │   │       ├── components/ModelSearchPlanPanel.tsx   # 主面板（含 Run/Re-run 按钮、12 个展示子区）
│   │   │       ├── constants.ts          # 状态标签 / 优先级/预算级别颜色
│   │   │       └── types.ts              # ModelSearchPlanResponse, HPOPlan, SearchSpacePlan 等 20+ 个接口
│   │   │   └── pipelineGeneration/        # 可执行流水线生成面板
│   │   │       ├── components/PipelineGenerationPanel.tsx  # 主面板（Generate/Rerun 按钮、10 个展示子区含 LLM Advisory Review）
│   │   │       ├── constants.ts           # 状态颜色 / 优先级颜色 / 角色颜色
│   │   │       └── types.ts               # PipelineGenerationResponse, PipelineSpec, TrialPlan, LLMAdvisoryReview 等 20+ 个接口
│   │   │   └── pipelineExecution/          # 流水线执行与训练面板 ★ 最新
│   │   │       ├── components/PipelineExecutionPanel.tsx  # 主面板（Run Training / Re-run Training 按钮、10 个展示子区：Summary/Pipeline Runs/Trial Results/Artifact Manifest/Metric Eval Input/Runtime/Warnings/Errors/JSON）
│   │   │       ├── constants.ts           # 状态颜色 / Trial 状态颜色 / 角色颜色 / Trial 类型颜色
│   │   │       └── types.ts               # PipelineExecutionResponse, TrialResultDTO, PipelineRunResultDTO, MetricEvaluationInputDTO 等接口
│   │   │   └── metricEvaluation/            # 指标评估面板 ★ 最新
│   │   │       ├── components/MetricEvaluationPanel.tsx  # 主面板（Run Evaluation / Re-run Evaluation 按钮、11 个展示子区：Summary/Count Boxes/Best Model/Model Ranking/Trial Metrics/Fold Metrics/Baseline Comparison/Metric Validation/Artifact Manifest/Result Diagnosis Input/Warnings & Errors/JSON）
│   │   │       ├── constants.ts           # 状态颜色 / 方向标签 / 角色颜色
│   │   │       └── types.ts               # MetricEvaluationResponse, FoldMetricResult, TrialMetricResult, ModelRankingItem, BaselineComparison 等接口
│   │   │   └── resultDiagnosis/              # LLM 结果诊断面板
│   │   │       ├── components/ResultDiagnosisPanel.tsx  # 主面板（Run/Re-run Diagnosis 按钮、9 个 Tab + Iteration Context 显示）
│   │   │       ├── constants.ts           # 状态颜色 / 诊断类型颜色 / 严重度颜色 / 置信度颜色 / 优先级颜色 / 性能等级颜色
│   │   │       └── types.ts               # ResultDiagnosisResponse, DiagnosticFinding, EvidenceItem, RootCauseHypothesis, RefinementRecommendation, IterationContext 等接口
│   │   │   └── workflowRefinement/          # LLM 工作流精炼与闭环迭代面板 ★ 最新
│   │   │       ├── components/WorkflowRefinementPanel.tsx  # 主面板（Run/Re-run 按钮 + Adopt & Rerun 按钮 + 9 个 Tab：Decision/Reasoning/Evidence/Revised Plan/Plan Delta/Rerun Plan/Final Selection/Validation/Full JSON）
│   │   │       ├── constants.ts           # 状态颜色 / 决策颜色 / 置信度颜色 / 重跑阶段颜色
│   │   │       └── types.ts               # WorkflowRefinementResponse, WorkflowRefinementDecisionDTO, DecisionReasoning, RevisedWorkflowPlanResponse, WorkflowPlanDelta, IterationRerunPlan, FinalPipelineSelectionInput, AdoptRevisedPlanResult 等接口
│   │   └── index.tsx
│   ├── Dockerfile
│   ├── package.json                     # React 18 + Ant Design 5 + react-hook-form + zod + axios
│   └── tsconfig.json
│
├── docs/                                # 项目文档
│   ├── PROJECT_IMPLEMENTATION_OVERVIEW.md  # 本文档
│   ├── prd-1-mvp.md ~ prd-10.md         # 各模块 PRD 文档
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
| Pipeline Generation | 数据库 + API 响应 | JSON | 含 pipeline_bundle (specs + trial_plan + validation/eval plan), pipeline_specs (含 baseline/hpo_candidate 角色), component_binding_result, artifact_manifest, pipeline_validation_result, safety_check_result, llm_advisory_review (顾问式审查), execution_input, ready_for_execution 标记 |
| Pipeline Execution Result | 数据库 + API 响应 + 文件系统 | JSON + Parquet + Joblib | 含 pipeline_run_results (每 pipeline run 的 trial 统计), trial_results (含 fold_results + 原始指标), training_artifact_manifest (预测/模型/日志/划分元数据路径), metric_evaluation_input (下游 Metric Evaluation 合同), runtime_environment (Python/sklearn/pandas/numpy 版本)；训练 artifacts 存储到 `/app/artifacts/training/{pe_id}/` |
| Metric Evaluation Result | 数据库 + API 响应 + 文件系统 | JSON | 含 metric_summary (均值/标准差/最小值/最大值/中位数/变异系数), trial_metric_results (跨 fold 聚合), pipeline_metric_results (按 pipeline 聚合), fold_metric_results (每 fold 指标), model_ranking (含 vs Baseline 和 Improvement %), baseline_comparison (最佳基线 vs 最佳候选 + 改善量), metric_validation_result (6 项校验), evaluation_artifact_manifest, result_diagnosis_input (下游 Result Diagnosis 合同)；评估 artifacts 存储到 `/app/artifacts/evaluation/{me_id}/` |
| Workflow Refinement Result | 数据库 + API 响应 + 文件系统 | JSON | 含 workflow_refinement_decision (proceed_next_stage / iterate_refinement), decision_reasoning (7 维度评估), evidence_used, revised_workflow_plan (修订版 WorkflowPlan), workflow_plan_delta (逐 section diff), iteration_rerun_plan (重跑阶段/可复用/不可复用 artifacts/改善目标/阈值), final_pipeline_selection_input (含 selection_policy), llm_workflow_refinement (完整 LLM 输出), validation_result (5 组件有效性 + 安全扫描结果), artifact_manifest；refinement artifacts 存储到 `/app/artifacts/workflow_refinement/{wr_id}/` |

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
        ↓ (模块九: Pipeline Generation)
    Pipeline Bundle + Execution Input (pipeline_bundle + execution_input，存入 PipelineGeneration 表)
        ↓ (模块十: Pipeline Execution)
    Training Artifacts → /app/artifacts/training/{pe_id}/
        ├── predictions/   (*.parquet — y_true + y_pred + sample_id)
        ├── models/        (*.joblib — trained sklearn models)
        ├── trial_results.json
        ├── split_metadata.json
        ├── execution_result.json
        ├── metric_evaluation_input.json
        └── logs/execution.log
            ↓ (模块十一: Metric Evaluation)
Metric Evaluation Artifacts → /app/artifacts/evaluation/{me_id}/
    ├── metric_results.json
    ├── fold_metrics.json
    ├── trial_metrics.json
    ├── pipeline_metrics.json
    ├── model_ranking.json
    ├── baseline_comparison.json
    ├── result_diagnosis_input.json
    └── manifest.json
        ↓ (模块十二: Result Diagnosis)
Result Diagnosis Artifacts → /app/artifacts/diagnosis/{rd_id}/
    ├── diagnosis_result.json
    ├── evidence_summary.json
    ├── system_checks.json
    ├── closed_loop_refinement_input.json
    ├── llm_request.json
    ├── llm_response.json
    └── manifest.json
        ↓ (模块十三: Workflow Refinement)
Workflow Refinement Artifacts → /app/artifacts/workflow_refinement/{wr_id}/
    ├── workflow_refinement_result.json
    ├── llm_refinement_context.json
    ├── llm_request.json
    ├── llm_response.json
    ├── revised_workflow_plan.json
    ├── workflow_plan_delta.json
    ├── iteration_rerun_plan.json
    ├── final_pipeline_selection_input.json
    ├── validation_result.json
    └── manifest.json
        ↓
    ┌── Decision: PROCEED_NEXT_STAGE → final_pipeline_selection_input (供 Final Pipeline Selection 消费, 尚未实现)
    └── Decision: ITERATE_REFINEMENT → Adopt Revised Plan (创建新 WorkflowPlan, mode=refinement_adopted)
            ↓ (Adopt & Rerun 闭环)
        Re-execute pipeline stages from revised entry point → 反馈回模块四/五/六/七/八/九/十/十一 → 回到模块十二 (Result Diagnosis)
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

**完成度**：~85%。核心 12 步流水线完整。LLM 深度参与策略建议但受 Registry 约束；搜索空间模板覆盖 10 个模型族；安全校验包含代码注入扫描。已通过 `pipeline_generation_input` 和 `ready_for_pipeline_generation` 标记与下游 Pipeline Generation 模块对接。

---

### 5.9 模块九：Executable Pipeline Generation（可执行流水线生成）★ 新增

**文件位置**：[backend/app/modules/pipeline_generation/](file:///c:/projects/MLAgent/backend/app/modules/pipeline_generation/)

**输入**：
- `PipelineGenerationCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_generation/schemas.py)）：force_rerun, use_llm_reviewer, include_baselines, include_hpo_candidates, pipeline_profile, max_pipeline_specs_override, notes
- 上游 ModelSearchPlan 数据（通过 `context_builder.py` 读取）+ Model Registry + HPO Registry + Pipeline Template Registry + Pipeline Component Registry

**处理逻辑**（12 步流水线）：
1. **Build Context**：`context_builder.build_pipeline_generation_context()` 读取模块八的最新 ModelSearchPlan，校验 `ready_for_pipeline_generation = true`，加载全部 8 个上游模块数据，构建包含 task_type/primary_metric/model_ready_matrix_path/feature_columns/target_column/allowed_model_families/allowed_hpo_methods 的完整 context
2. **Resolve Artifacts**：`artifact_resolver.resolve_artifacts()` 校验 model_ready_matrix_path 和 preprocessor_artifact_path 存在且安全。`_is_safe_path()` 使用白名单机制（artifacts/app/data/output/tmp），检测 `..` 路径遍历
3. **Bind Components**：`component_binder.bind_components()` 将每个候选模型的 model_id/hpo_method/validation_strategy/metrics 绑定到三个 Registry（Model/HPO/Pipeline Component）
4. **Build Pipeline Specs**：`pipeline_spec_builder.build_pipeline_specs()` 基于 Pipeline Template Registry（4 个模板：tabular_regression/tabular_classification × basic/hpo）生成每个模型的 PipelineSpec（含 pipeline_role: baseline/candidate/hpo_candidate, priority, hpo_enabled, search_space, fixed_params, validation_plan_ref 等）
5. **Build Trial Plan**：`trial_plan_builder.build_trial_plan()` 从上游 HPO Plan 构建 TrialPlan（hpo_enabled, search_method, max_total_trials, max_parallel_trials, trial_allocation, baseline_trial_policy, candidate_trial_policy, early_stopping_policy, fallback_policy）
6. **Validate Pipeline**：`pipeline_validator.validate_pipeline_bundle()` 执行 8 项检查：
   - structure_valid：结构完整性
   - registry_valid：所有组件在 Registry 中存在
   - artifact_valid：artifact 路径可用
   - task_type_compatible：模型与任务类型兼容
   - search_space_valid：搜索空间定义合法
   - trial_valid：trial 分配合理
   - data_fields_valid：数据字段匹配
   - execution_input_valid：Execution Input 构建完整
7. **Safety Check**：`safety_checker.check_pipeline_safety()` 扫描 15+ 种危险模式（import, eval, exec, subprocess, .fit(), sklearn., .train(), Pipeline() 等），确保 pipeline 中不含可执行恶意代码
8. **LLM Advisory Review**（可选，由 `use_llm_reviewer` 控制）：
   - `llm_review_prompt_builder.build_llm_review_prompt()` 构建顾问式审查 prompt（8 维度：model_task_compatibility, baseline_coverage, hpo_budget_reasonableness, validation_strategy_suitability, metric_consistency, overfitting_risk, resource_cost_risk, reproducibility_readiness），严格定位 LLM 为"ADVISORY reviewer"而非"approver"
   - `llm_pipeline_reviewer.review()` 复用 LLMClient 获取 LLM 审查结果
   - `llm_review_parser.parse_llm_review_response()` 纯 JSON 解析
   - `llm_review_validator.validate_llm_review()` 五层校验：25+ 禁止内容模式扫描 + 禁止字段集（approval_status/approved/rejected/conditional/needs_improvement 等）+ 枚举值校验 + 结构完整性 + 安全扫描
   - `llm_review_normalizer.normalize_llm_review()` 标准化为 `LLMAdvisoryReview`：
     - 剥离旧式审批字段到 `raw_llm_summary`
     - 映射旧式 overall_assessment → risk_level（approved→low, needs_improvement→medium, rejected→high）
     - 转换 numeric confidence_score → confidence_level（≥0.7→high, ≥0.3→medium）
     - 吸收 risk_notes/consistency_findings → non_blocking_risks
     - 强制执行 execution_impact="non_blocking"（系统校验器具有最终决定权）
     - 追踪所有标准化操作到 normalization_notes
9. **Build Execution Input**：`execution_input_builder.build_execution_input()` 构建下游 Pipeline Execution 合同（含 pipeline_specs, trial_plan, validation_plan, evaluation_plan, execution_constraints）
10. **Build Pipeline Bundle**：`builder.build_pipeline_bundle()` 构建完整的 PipelineBundle（含所有 specs, plans, execution_policy）
11. **Build Response**：`builder.build_pipeline_generation_response()` 构建 `PipelineGenerationResponse`：
    - status 由 errors/warnings 决定（FAILED / GENERATED_WITH_WARNING / GENERATED）
    - generation_mode 由 use_llm_reviewer 决定（SYSTEM_TEMPLATE_WITH_LLM_REVIEW / SYSTEM_TEMPLATE_BASED）
    - ready_for_execution 仅由 System Validator + Safety Checker + Artifact Manifest 决定，LLM 无权影响
12. **Persist**：将完整 pipeline_json 和 execution_input_json 以 `model_dump(mode='json')` 序列化后存入 PostgreSQL JSONB，同时记录 llm_request_json, llm_response_json, llm_confidence_score

**输出**：
- `PipelineGenerationResponse`：含 pipeline_generation_id, task_id, model_search_plan_id, feature_preprocessing_id, status, generation_mode, n_pipeline_specs (含 n_baseline_specs, n_hpo_specs), pipeline_bundle, pipeline_specs, trial_plan, component_binding_result, artifact_manifest, pipeline_validation_result, safety_check_result, llm_advisory_review, execution_input, ready_for_execution, warnings, error_message

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_generation/api.py)）：
- `POST /api/pipeline-generations/{task_id}` — 创建流水线生成
- `GET /api/pipeline-generations/{pipeline_generation_id}` — 获取流水线生成
- `GET /api/tasks/{task_id}/pipeline-generation` — 获取任务的最新流水线生成
- `POST /api/pipeline-generations/{task_id}/rerun` — 重新生成
- `GET /api/pipeline-generations/{pipeline_generation_id}/summary` — 获取摘要
- `GET /api/pipeline-generations/{pipeline_generation_id}/execution-input` — 获取 Execution Input

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_generation/model.py)）：
- `PipelineGeneration` 表：id (PK), task_id (indexed), model_search_plan_id (indexed), feature_preprocessing_id (indexed), status (indexed), generation_mode, task_type, target_column, primary_metric, n_pipeline_specs, n_baseline_specs, n_hpo_specs, hpo_enabled, ready_for_execution (indexed), llm_review_used, llm_confidence_score, pipeline_json (JSONB), execution_input_json (JSONB), llm_request_json (JSONB), llm_response_json (JSONB), error_message, created_at (indexed), updated_at

**关键设计约束**：
1. **LLM 定位于顾问而非审批者**：`ready_for_execution` 由 System Validator + Safety Checker + Artifact Manifest 三者共同决定，LLM 无权批准或拒绝执行
2. **多级安全防护**：Safety Checker（15+ 危险模式）+ LLM Review Validator（25+ 禁止模式）+ LLM Review Normalizer（自动剥离旧式审批字段）
3. **LLM 输出标准化**：Normalizer 处理非标准 LLM 输出（旧式 approval_status、numeric confidence_score、risk_notes 等），统一映射到标准 `LLMAdvisoryReview` 格式
4. **Pipeline Template Registry**：提供 4 个模板（regression/classification × basic/hpo），Pipeline Spec 由系统基于模板生成，LLM 不参与 spec 构建
5. **Component Binding 校验**：所有 model_id、hpo_method、validation_strategy、metrics 必须经对应 Registry 校验，不合法的绑定被标记并记录 errors
6. **Artifact 路径安全**：白名单机制（仅允许 artifacts/app/data/output/tmp 根目录），拒绝 `..` 遍历和不在白名单中的绝对路径

**前端面板**（[PipelineGenerationPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/pipelineGeneration/components/PipelineGenerationPanel.tsx)）：
- 提供 "Generate Pipeline" 和 "Re-run Generation" 两个按钮
- 展示 10 个子区：Pipeline Bundle Summary / Pipeline Specs 表格（Spec ID / Role / Model / Family / Priority / HPO / Exec Ready / Warnings）/ Trial Plan / Component Binding Result 表格 / Artifact Manifest / Pipeline Validation（8 项检查）/ Safety Check / LLM Advisory Review（含 Impact / Risk Level / Review Confidence / checklist 表格 / non-blocking risks / blocking issues / resource warnings / improvement suggestions / normalization notes）/ Execution Input / Warnings & Errors / Full JSON

**完成度**：~85%。核心 12 步流水线完整，LLM Advisory Review 的 parse→validate→normalize 三层处理链路完整，双 Registry 校验，多级安全防护。`ready_for_execution` 由系统权威决定。上游消费模块八的 `pipeline_generation_input`，下游输出 `execution_input` 供 Pipeline Execution 消费。

---

### 5.10 模块十：Pipeline Execution and Training（流水线执行与训练）★ 最新

**文件位置**：[backend/app/modules/pipeline_execution/](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/)

**输入**：
- `PipelineExecutionCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/schemas.py)）：pipeline_generation_id, execution_mode, max_trials_override, fail_fast, save_predictions, save_trained_models, max_runtime_seconds, force_rerun
- 上游 PipelineGeneration 的 `execution_input_json`（通过 `context_builder.py` 读取 + `execution_input_loader.py` 解析）

**处理逻辑**（12 步流水线）：
1. **Build Execution Context**：`context_builder.build_execution_context()` 读取模块九的最新 PipelineGeneration，校验 `ready_for_execution = true`，验证 `execution_input_json` 存在
2. **Load Execution Input**：`execution_input_loader.load_execution_input()` 解析 execution_input_json 为 ExecutionInput Pydantic 模型，校验 pipeline_specs（非空 + execution_ready=True）、trial_plan、validation_plan（split_strategy）、evaluation_plan（primary_metric）、feature_columns、target_column
3. **Load Model-Ready Matrix**：`data_matrix_loader.load_model_ready_matrix()` 加载 model_ready_features.parquet（路径安全校验：无 `..` 遍历），验证特征列和目标列存在、目标列无 NaN
4. **Create Validation Splits**：`validation_splitter.create_validation_splits()` 根据 validation_plan 创建训练/验证划分。`_normalize_strategy()` 将上游标准名称映射为内部标准（`k_fold_cross_validation` → `k_fold`），支持 train_test_split/holdout/k_fold/stratified_k_fold
5. **Expand Execution Plan**：`execution_planner.expand_execution_plan()` 展开 PipelineSpecs + TrialPlan → 扁平化 trial 计划列表（baseline→1 trial, fixed_params candidate→1 trial, hpo_candidate→max_trials trials from search_space）
6. **Setup Artifact Directory**：`training_artifact_manager.ensure_execution_dir()` 创建 `/app/artifacts/training/{pe_id}/` 及子目录（predictions/, models/, splits/, logs/）
7. **Execute Training (Controlled Executor)**：`controlled_executor.execute_training()` — 唯一训练入口：
   - 迭代 trial plans，按 pipeline_run（pipeline_spec）分组
   - 对每个 trial：`trial_runner.run_trial()` 遍历验证划分 → `fold_runner.run_fold()` 逐 fold 训练模型 → `_compute_raw_metrics()` 计算 MAE/MSE/RMSE/R2（回归）或 Accuracy（分类）→ `prediction_writer.save_predictions()` 保存预测结果
   - 模型实例化通过 `model_factory.create_model()` 从 Model Registry ID 映射到 sklearn 类（显式映射，非动态 import）
   - HPO 参数通过 `hpo_trial_generator.generate_hpo_trials()` 从上游 SearchSpaceItem 格式生成（支持 random_search + grid_search，log_uniform/uniform/choice 采样）
   - 支持 sequential/limited_parallel 执行模式、timeout、fail_fast
8. **Collect Artifacts**：收集所有 trial 的 prediction_artifact_path 和 model_artifact_path
9. **Build Metric Evaluation Input**：`metric_input_builder.build_metric_evaluation_input()` 构建下游 Metric Evaluation 合同（含 ready 标记、task_type、target_column、primary_metric、metric_direction、prediction/model artifacts、trial results 摘要）。Ready 条件：至少 1 个 completed trial + prediction artifacts 存在 + target_column 有效 + evaluation_plan 存在
10. **Save Artifacts**：保存 split_metadata.json, trial_results.json, manifest.json, execution_result.json, metric_evaluation_input.json
11. **Build Response**：`builder.build_response()` 组装 PipelineExecutionResponse（含 execution counts, pipeline_run_results, trial_results, metric_evaluation_input, artifact_manifest, runtime_environment）
12. **Persist**：将完整 execution_json 和 metric_evaluation_input_json 以 `model_dump(mode='json')` 序列化后存入 PostgreSQL JSONB（避免 datetime 序列化错误），同时存储 runtime_log_json

**输出**：
- `PipelineExecutionResponse`：含 pipeline_execution_id, task_id, pipeline_generation_id, status, execution_mode, n_pipeline_specs, n_trials_planned, n_trials_completed, n_trials_failed, n_models_trained, ready_for_metric_evaluation, duration_seconds, pipeline_run_results (per-pipeline-run trial 统计), trial_results (含 fold_results + 原始指标), training_artifact_manifest, metric_evaluation_input, runtime_environment, warnings, error_message

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/api.py)）：
- `POST /api/pipeline-executions/{task_id}` — 创建并执行 Pipeline Execution
- `GET /api/pipeline-executions/{pe_id}` — 获取执行详情
- `GET /api/tasks/{task_id}/pipeline-execution` — 获取任务的最新执行
- `POST /api/pipeline-executions/{task_id}/rerun` — 重新执行
- `GET /api/pipeline-executions/{pe_id}/summary` — 获取执行摘要
- `GET /api/pipeline-executions/{pe_id}/trials` — 获取 trial 结果列表
- `GET /api/pipeline-executions/{pe_id}/metric-evaluation-input` — 获取下游 Metric Evaluation 输入
- `GET /api/pipeline-executions/{pe_id}/logs` — 获取运行时日志

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/model.py)）：
- `PipelineExecution` 表：id (PK), task_id (indexed), pipeline_generation_id (indexed), status (indexed), execution_mode, task_type, target_column, primary_metric, n_pipeline_specs, n_trials_planned, n_trials_completed, n_trials_failed, n_models_trained, ready_for_metric_evaluation (indexed), training_artifact_dir, error_message, started_at, finished_at, execution_json (JSONB), metric_evaluation_input_json (JSONB), runtime_log_json (JSONB), created_at (indexed), updated_at

**关键设计约束**：
1. **Controlled Executor 为唯一训练入口**：所有模型训练必须通过 `controlled_executor.py`，禁止 LLM 生成训练代码、禁止动态 import 模型类
2. **仅消费 upstream execution_input_json**：不重新生成 PipelineSpecs、不重新规划 HPO，完全依从上游合同
3. **模型仅来自 Model Registry**：通过 `model_factory.py` 的显式 sklearn 映射实例化（不动态 import），训练前校验 task_type 兼容性和依赖可用性
4. **不执行最终模型排名**：本模块只训练模型并收集原始指标，模型排名和选择由下游 Metric Evaluation 处理
5. **失败状态持久化**：即使执行过程中抛出异常，也会将失败记录（含 error_message + traceback）写入数据库
6. **HPO 搜索空间解析**：`hpo_trial_generator.py` 专门处理上游 SearchSpaceItem 格式（`{model_id, search_space_id, parameters: [{name, param_type, low, high, choices, sampling}]}`）

**前端面板**（[PipelineExecutionPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/pipelineExecution/components/PipelineExecutionPanel.tsx)）：
- 提供 "Run Training" 和 "Re-run Training" 两个按钮
- 展示 10 个子区：Execution Summary（计数卡片：Pipeline Specs / Trials Planned / Completed / Failed / Models Trained / Duration）/ Pipeline Runs 表格（Run ID / Role / Model / Family / HPO / Trials / Status / Duration）/ Trial Results 表格（Trial ID / Model / Type / Params / Folds / Status / Prediction / Model Path / Duration / Error）/ Training Artifact Manifest / Metric Evaluation Input / Runtime Environment / Warnings / Error Message / Full JSON
- 表格卡片支持水平滚动（`overflowX: 'auto'`），解决内容溢出问题

**完成度**：~85%。核心 12 步流水线完整，Controlled Executor 训练链路（fold_runner→trial_runner→controlled_executor）完整，Model Factory 覆盖 10 个模型族的显式映射，HPO Trial Generator 支持上游 SearchSpaceItem 格式，上游 split strategy 名称自动标准化。已通过 `metric_evaluation_input` 和 `ready_for_metric_evaluation` 标记与下游 Metric Evaluation 模块对接。

---

### 5.11 模块十一：Metric Evaluation（指标评估）★ 最新

**文件位置**：[backend/app/modules/metric_evaluation/](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/)

**输入**：
- `MetricEvaluationCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/schemas.py)）：pipeline_execution_id, force_rerun
- 上游 PipelineExecution 的 `metric_evaluation_input_json` + `execution_json`（通过 `context_builder.py` 读取 + `metric_input_loader.py` 解析）

**处理逻辑**（13 步流水线）：
1. **Build Context**：`context_builder.build_metric_evaluation_context()` 读取模块十的最新 PipelineExecution，校验状态在允许范围（completed/partially_completed/evaluated_with_warning），验证 `ready_for_metric_evaluation = true`
2. **Load Metric Input**：`metric_input_loader.load_metric_evaluation_input()` 解析 metric_evaluation_input_json，校验 task_type / target_column / primary_metric / metric_direction 必填字段，提取 trial_results_raw（含 prediction_artifact_paths）
3. **Load Prediction Artifacts**：`prediction_artifact_loader.load_prediction_artifacts()` 加载每个 trial 的预测 parquet 文件，逐文件校验：路径安全（白名单 `/app/artifacts/training`，拒绝 `..` 遍历）、必填列（sample_id / trial_id / pipeline_spec_id / fold_index / y_true / y_pred / model_id）、数值列类型、NaN/Inf 检测；然后 `build_prediction_frame_map()` 构建 trial_id → {fold_index → DataFrame} 映射
4. **Build Trial Info Map（数据补充）**：从 `pe.execution_json` 中提取完整 trial 元数据：
   - 从 `pipeline_run_results` 构建 spec_id → pipeline_role / model_family 映射
   - 从 `trial_results` 构建 full_trial_map（含 pipeline_spec_id / trial_type / params）
   - 交叉引用构建 `trial_info_map`：每个 trial 获取 model_id / pipeline_spec_id / pipeline_run_id / model_family / pipeline_role / trial_type / params
   - 这是关键的补充步骤——上游 metric_evaluation_input_json 中的 trial_results 仅为轻量摘要（6 个字段），完整的 pipeline_role 等元数据从 execution_json JSONB 中按需提取
5. **Evaluate Fold Metrics**：`fold_metric_evaluator.evaluate_fold_metrics()` 遍历 trial_fold_map，逐 fold 调用 `metric_calculator.calculate_metric()` 计算 primary_metric，生成 `FoldMetricResult` 列表（含 status 判定：evaluated / failed / skipped）
6. **Aggregate Trial Metrics**：`trial_metric_aggregator.aggregate_trial_metrics()` 按 trial 聚合 fold 结果，计算跨 fold 的 mean / std / min / max / median / fold_values 列表 + cv（变异系数），生成 `TrialMetricResult` 列表（含 pipeline_role / model_family 等元数据）
7. **Aggregate Pipeline Metrics**：`pipeline_metric_aggregator.aggregate_pipeline_metrics()` 按 model_id 聚合 trial 结果，选取 best_trial（基于 primary_metric_mean），生成 `PipelineMetricResult` 列表
8. **Rank Models and Trials**：`model_ranker.rank_models_and_trials()` 基于 primary_metric + metric_direction 排名：
   - 按 primary_metric_mean 排序（minimize→升序，maximize→降序）
   - 平局时按 primary_metric_std 决胜（越小越好）
   - 返回 best_trial / best_model_id / best_trial_id / best_pipeline_spec_id / ranking_items（各含 rank / model_id / trial_id / primary_metric_value / primary_metric_std / pipeline_role）
9. **Compare Against Baselines**：`baseline_comparator.compare_against_baselines()` 按 pipeline_role 筛选：
   - baseline trials → 选取 best_baseline（最佳基线指标值 + trial/model ID）
   - candidate trials → 选取 best_candidate（最佳候选指标值 + trial/model ID）
   - 计算改善量（improvement_absolute / improvement_percentage / direction）
   - 计算排名改善（candidate_rank_improvement：最佳候选是否优于最佳基线）
   - 若无 baseline 或 candidate，`baseline_available = false`
10. **Compute Improvement for Ranking Items**（步骤 9b）：若 baseline_available 且 best_baseline_metric_value 不为 None，对每个 ranking_item 计算：
    - `improvement_over_best_baseline`：minimize → bl_val - item_val；maximize → item_val - bl_val
    - `improvement_percentage`：仅当 `abs(bl_val) > 1e-12` 时计算（避免除零）
11. **Build Result Diagnosis Input**：`result_diagnosis_input_builder.build_result_diagnosis_input()` 构建下游 Result Diagnosis 合同（含 metric_evaluation_id / pipeline_execution_id / task_id / task_type / primary_metric / metric_direction / best_trial / best_model_id / model_ranking / baseline_comparison / metric_summary / trial_results / warnings / ready_for_result_diagnosis 标记）
12. **Save Artifacts**：`evaluation_artifact_manager` 创建 `/app/artifacts/evaluation/{me_id}/` 目录，保存 8 个 JSON artifacts（metric_results / fold_metrics / trial_metrics / pipeline_metrics / model_ranking / baseline_comparison / result_diagnosis_input / manifest）和 `EvaluationArtifactManifest` DTO
13. **Build Response and Persist**：
    - 计算统计：n_trials_evaluated / n_trials_failed / n_models_evaluated
    - 判定状态：evaluated / evaluated_with_warning / partially_evaluated / failed
    - 调用 `metric_validator.validate_metric_results()` 执行 6 项校验（finiteness / presence / ranking_consistency / best_trial_existence / baseline_refs / diagnosis_input）
    - `builder.build_response()` 组装 `MetricEvaluationResponse`（含 metric_summary / trial_metric_results / pipeline_metric_results / fold_metric_results / model_ranking / baseline_comparison / metric_validation_result / evaluation_artifact_manifest / result_diagnosis_input）
    - 持久化到数据库（`evaluation_json` / `result_diagnosis_input_json` / `metric_summary_json` / `model_ranking_json` 以 `model_dump(mode='json')` 序列化为 JSONB）
    - 失败时写入失败记录（含 error_message + traceback），不丢失数据

**Metric Registry**（[metric_registry.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/metric_registry.py)）：
- 5 个回归指标：MAE（minimize）、MSE（minimize）、RMSE（minimize）、R2（maximize）、MAPE（minimize）
- 5 个分类指标：Accuracy（maximize）、Precision（maximize）、Recall（maximize）、F1（maximize）、ROC_AUC（maximize）
- 每个指标含 id / display_name / metric_type / direction / allowed_task_types / aliases
- 核心函数：`get_metric_by_name()` / `validate_metric_for_task_type()` / `get_metric_direction()` / `list_metrics_for_task_type()`

**Metric Calculator**（[metric_calculator.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/metric_calculator.py)）：
- 纯 numpy 实现，无 sklearn 依赖
- 分类指标自动识别二分类 vs 多分类
- `calculate_metric(y_true, y_pred, metric_name)` 分发器函数

**输出**：
- `MetricEvaluationResponse`：含 metric_evaluation_id, task_id, pipeline_execution_id, pipeline_generation_id, status, task_type, primary_metric, metric_direction, n_trials_evaluated, n_trials_failed, n_models_evaluated, best_trial_id, best_model_id, best_pipeline_spec_id, ready_for_result_diagnosis, metric_summary, trial_metric_results, pipeline_metric_results, fold_metric_results, model_ranking, baseline_comparison, metric_validation_result, evaluation_artifact_manifest, result_diagnosis_input, warnings, error_message
- `MetricEvaluationSummaryResponse`：摘要接口返回（含 ranking 和 trials 简要列表）
- `ModelRankingItem` 列表：排名接口返回
- `TrialMetricResult` 列表：Trial 指标接口返回
- `FoldMetricResult` 列表：Fold 指标接口返回

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/api.py)）：
- `POST /api/metric-evaluations/{task_id}` — 创建指标评估
- `GET /api/metric-evaluations/{me_id}` — 获取指标评估详情
- `GET /api/tasks/{task_id}/metric-evaluation` — 获取任务的最新指标评估
- `POST /api/metric-evaluations/{task_id}/rerun` — 重新运行指标评估
- `GET /api/metric-evaluations/{me_id}/summary` — 获取评估摘要
- `GET /api/metric-evaluations/{me_id}/ranking` — 获取模型排名
- `GET /api/metric-evaluations/{me_id}/trials` — 获取 Trial 指标列表
- `GET /api/metric-evaluations/{me_id}/folds` — 获取 Fold 指标列表
- `GET /api/metric-evaluations/{me_id}/result-diagnosis-input` — 获取下游 Result Diagnosis 输入

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/model.py)）：
- `MetricEvaluation` 表：id (PK), task_id (indexed), pipeline_execution_id (indexed), pipeline_generation_id (indexed), status (indexed), task_type, target_column, primary_metric, metric_direction, n_trials_evaluated, n_trials_failed, n_models_evaluated, best_trial_id, best_model_id, best_pipeline_spec_id, best_primary_metric_value, ready_for_result_diagnosis (indexed), evaluation_artifact_dir, evaluation_json (JSONB), result_diagnosis_input_json (JSONB), metric_summary_json (JSONB), model_ranking_json (JSONB), error_message, created_at (indexed), updated_at

**关键设计约束**：
1. **轻量合同 + JSONB 补充模式**：metric_evaluation_input_json 的 trial_results 仅为轻量摘要（6 字段），完整的 pipeline_role / model_family / trial_type / params 等元数据从 execution_json JSONB 中补充。上游发轻量合同，下游按需从完整日志中提取
2. **预测 Artifact 路径安全**：白名单机制（仅允许 `/app/artifacts/training`），拒绝 `..` 遍历、非 parquet 文件、不存在的路径
3. **预测数据完整性**：每个 parquet 文件必须含 7 个必填列，y_true/y_pred 必须为数值且不含 NaN/Inf
4. **Metric Registry 白名单**：仅 Registry 中注册的指标可被计算，拒绝未注册指标名。每个指标有明确的方向（minimize/maximize）和 task_type 约束
5. **纯 numpy 计算**：不依赖 sklearn.metrics，所有指标基于 numpy 原生实现
6. **Fold → Trial → Pipeline 三级聚合**：每级有独立的聚合器和 DTO，数据流清晰可追溯
7. **Baseline Comparator 按 pipeline_role 筛选**：依赖步骤 4 的正确补充（从 execution_json 获取 pipeline_role），否则 baseline 无法识别
8. **Result Diagnosis Input 构建**：已通过 `ready_for_result_diagnosis` 标记与下游 Result Diagnosis 模块对接

**前端面板**（[MetricEvaluationPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/metricEvaluation/components/MetricEvaluationPanel.tsx)）：
- 提供 "Run Metric Evaluation" 和 "Re-run Evaluation" 两个按钮
- 展示 11 个子区：Evaluation Summary（状态 / 方向 / 指标名称 / Trial 计数 / 模型数）/ Count Boxes（Evaluated / Failed / Models）/ Best Model（trial_id / model_id / pipeline_spec_id / metric_value）/ Model Ranking 表格（Rank / Model / Trial / Role / Metric Value / Std / vs Baseline / Improvement %）/ Trial Metrics 表格（Trial ID / Model / Role / Family / Mean / Std / CV / Status）/ Fold Metrics 表格 / Baseline Comparison（baseline_available / best_baseline / best_candidate / improvement_absolute / improvement_percentage）/ Metric Validation（6 项检查通过/失败）/ Artifact Manifest / Result Diagnosis Input / Warnings & Errors / Full JSON
- 表格支持水平滚动（`overflowX: 'auto'`）

**完成度**：~90%。核心 13 步流水线完整，Fold→Trial→Pipeline 三级聚合链路完整，Metric Registry 白名单机制就位，Baseline Comparator 按 pipeline_role 正确筛选。已通过 `result_diagnosis_input` 和 `ready_for_result_diagnosis` 标记与下游 Result Diagnosis 模块对接。Metric Calculator 覆盖 5 个回归指标和 5 个分类指标。路径安全校验跨平台兼容（Windows / Linux）。

---

### 5.12 模块十二：LLM-based Result Diagnosis（基于大模型的结果诊断）

**文件位置**：[backend/app/modules/result_diagnosis/](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/)

**输入**：
- `ResultDiagnosisCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/schemas.py)）：metric_evaluation_id（可选，不指定则自动取最新）/ force_rerun / use_llm（默认 true）/ include_dataset_context / include_pipeline_context / include_feature_context / diagnosis_profile（compact / standard / full，默认 standard）/ notes
- 上游 `MetricEvaluation`：必须满足 `status ∈ {evaluated, evaluated_with_warning, partially_evaluated}` 且 `ready_for_result_diagnosis = true`
- 必须消费 `result_diagnosis_input_json`（含 best_trial / best_model / model_ranking / baseline_comparison / metric_summary / stability_summary / failed_trials_summary / evaluation_warnings）
- 可选补充读取：DatasetProfile.profile_json / FeatureEngineering.feature_json / FeaturePreprocessing.preprocessing_json / PipelineExecution.execution_json

**处理逻辑**（15 步流水线，定义于 [service.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/service.py) `create_result_diagnosis()`）：
1. `context_builder.build_result_diagnosis_context()` 校验上游 MetricEvaluation 状态和 `ready_for_result_diagnosis` 标记
2. `diagnosis_input_loader.load_result_diagnosis_input()` 校验 `result_diagnosis_input_json` 合同完整性（9 个必填字段检查）
3. `_load_optional_context()` 按请求配置补充读取 DatasetProfile / FeatureEngineering / FeaturePreprocessing / PipelineExecution 等记录
4. `evidence_extractor.extract_evidence()` 从 6 类来源提取 EvidenceItem（metric / baseline / fold_stability / dataset / feature / pipeline）
5. `system_diagnostic_checker.run_system_diagnostic_checks()` 执行 9 条规则化系统检查（weak_baseline_improvement / high_fold_variance / all_models_weak / hpo_budget_limited / small_sample_warning / feature_count_low / many_features_dropped / candidate_underperforms_baseline / unstable_best_model）
6. `diagnostic_context_builder.build_llm_diagnostic_context()` 汇总 LLM 诊断上下文（compact / standard / full 三档可选）
7. `llm_prompt_builder.build_llm_prompt()` 构建 System Prompt（含 14 个诊断维度 + 完整 JSON Schema + 禁止代码生成声明）
8. `llm_result_diagnoser.LLMResultDiagnoser.diagnose()` 复用 `LLMClient`（定义于 [task_interpretation/llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)）调用 LLM
9. `llm_response_parser.parse_llm_response()` 解析 LLM JSON（支持裸 JSON / markdown code block / 花括号提取三种解析策略）
10. `llm_diagnosis_validator.validate_llm_diagnosis()` 执行 15 项结构校验（顶层字段 / diagnosis_type / severity / evidence_strength / confidence_level / target_stage / recommendation_type 枚举合法性 + 证据项非空检查 + 安全扫描 14 种危险代码模式 + 9 个禁止字段检查）
11. `llm_diagnosis_normalizer.normalize_llm_diagnosis()` 归一化 LLM 输出：补齐缺失字段 / 映射规范枚举值 / 调用 `canonical_diagnosis_type()` 将 LLM 变体归一化 / 将整数 `supporting_findings` 强制转为字符串 / 构建标准 `LLMDiagnosisResult`
12. `refinement_input_builder.build_closed_loop_refinement_input()` 构建下游 Closed-loop Refinement 输入：确定 refinement_focus / 排序 priority_recommendations / 生成 avoid_actions / 构建 suggested_next_iteration_profile / 判断 `ready_for_closed_loop_refinement`
13. `diagnosis_artifact_manager.save_diagnosis_artifacts()` 保存 7 个 JSON artifacts（diagnosis_result / diagnostic_context / system_diagnostic_checks / llm_diagnosis / evidence_summary / closed_loop_refinement_input / manifest）到 `/app/artifacts/diagnosis/{rd_id}/`
14. `builder.build_response()` 组装 `ResultDiagnosisResponse`
15. `persist()` 持久化到数据库：7 个 JSONB 字段（diagnosis_json / closed_loop_refinement_input_json / llm_request_json / llm_response_json / system_checks_json）+ 状态字段（status / main_issue_category / performance_level / should_refine / ready_for_closed_loop_refinement）

**LLM 安全机制**：
- **Prompt 约束**：System Prompt 声明 "You are not allowed to generate executable code / modify the workflow / start training / create new pipelines / You can only output structured JSON"
- **Validator 结构校验**：检查 diagnosis_type ∈ VALID_DIAGNOSIS_TYPES + 25 个别名映射（`DIAGNOSIS_TYPE_ALIASES`，如 `baseline_improvement` → `weak_baseline_improvement` / `overfitting` → `overfitting_risk`）
- **Validator 安全扫描**：扫描 14 种危险代码模式（import / def / class / eval( / exec( / subprocess / os.system / open( / write( / delete / remove / shutil / model.fit / model.predict / Pipeline( / optuna.create_study / __import__ / compile( / globals() / locals()）
- **Validator 禁止字段**：9 个字段（python_code / code / script / executable / workflow_patch / pipeline_patch / model_fit_code / train_code / shell_command / sql / direct_execution）
- **Normalizer 防御性转换**：`supporting_findings` 整数强制转字符串（`[str(s) for s in ...]`），防止 Pydantic 校验失败
- **Fallback 机制**：LLM 调用失败或校验失败时，使用 `system_diagnostic_checker` 输出系统规则诊断结果，状态设为 `fallback_diagnosed`，不影响上游 Metric Evaluation 结果

**LLM 输出 Schema**（[llm_prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/llm_prompt_builder.py)）：
- overall_assessment（performance_level / baseline_improvement_level / stability_level / main_issue_category / should_refine / summary / confidence_level）
- diagnostic_findings[]（diagnosis_type / severity / evidence_strength / description / evidence_items[] / affected_models / affected_trials / possible_causes / recommended_actions / refinement_targets / confidence_level）
- root_cause_hypotheses[]（root_cause_type / description / supporting_findings / likelihood / actionability）
- refinement_recommendations[]（target_stage / recommendation_type / priority / description / expected_benefit / risk / system_action_hint / requires_human_review）
- confidence_level

**输出**：
- `ResultDiagnosisResponse`：含 overall_assessment / diagnostic_findings / evidence_summary / root_cause_hypotheses / refinement_recommendations / closed_loop_refinement_input / llm_diagnosis / system_diagnostic_checks / diagnosis_artifact_manifest
- `ClosedLoopRefinementInput`：下游闭环优化正式输入（含 should_refine / refinement_focus / priority_recommendations / constraints_to_preserve / avoid_actions / suggested_next_iteration_profile / ready_for_closed_loop_refinement）
- `ResultDiagnosisSummaryResponse`：摘要（main_issue_category / performance_level / top_findings / top_recommendations）

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/api.py)）：
- `POST /api/result-diagnoses/{task_id}` — 创建/运行诊断
- `GET /api/result-diagnoses/{result_diagnosis_id}` — 获取指定诊断
- `GET /api/tasks/{task_id}/result-diagnosis` — 获取任务最新诊断
- `GET /api/tasks/{task_id}/result-diagnosis/needs-fresh` — 检查诊断是否过时（★ 2026-05 新增）
- `POST /api/result-diagnoses/{task_id}/rerun` — 重新诊断
- `GET /api/result-diagnoses/{result_diagnosis_id}/summary` — 获取诊断摘要
- `GET /api/result-diagnoses/{result_diagnosis_id}/closed-loop-refinement-input` — 获取闭环优化输入

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/model.py)）：
- `ResultDiagnosis` 表（`result_diagnosis`）：id (PK, `rd_{8hex}`), task_id (indexed), metric_evaluation_id (indexed), pipeline_execution_id (indexed), status (indexed, diagnosing / diagnosed / diagnosed_with_warning / fallback_diagnosed / failed), diagnosis_mode (llm_based / hybrid / system_rule_based), main_issue_category (indexed), performance_level (indexed), should_refine (indexed), ready_for_closed_loop_refinement (indexed), llm_used, llm_confidence_level, diagnosis_json (JSONB), closed_loop_refinement_input_json (JSONB), llm_request_json (JSONB), llm_response_json (JSONB), system_checks_json (JSONB), diagnosis_artifact_dir, error_message, created_at (indexed), updated_at

**关键设计特点**：
1. **LLM 深度参与但只输出诊断与建议**：LLM 可输出问题诊断 / 可能原因 / 证据引用 / 风险等级 / 改进方向，但禁止输出 Python 代码 / sklearn 代码 / 训练脚本 / 可执行 Pipeline / 直接修改 workflow plan / 直接修改 HPO search space
2. **诊断必须基于证据**：每个 DiagnosticFinding 必须包含 evidence_items，证据不足时强制标记 `evidence_strength: weak`
3. **LLM 不做最终决策**：本模块可建议 `should_refine: true` 和 `recommended_refinement_focus: feature_engineering`，但不能决定立即执行下一轮训练 / 直接选择最终模型 / 直接覆盖已有 Workflow Plan。下游 Closed-loop Refinement 需重新经过 System Validator / Registry / Template / Controlled Executor
4. **诊断类型别名映射**：`DIAGNOSIS_TYPE_ALIASES`（25 条）将 LLM 常见近义表达映射到规范值（如 `baseline_improvement` → `weak_baseline_improvement` / `overfitting` → `overfitting_risk` / `underfit` → `underfitting`），避免 LLM 措辞差异导致整个诊断路径失败
5. **多级安全防护**：Prompt 约束 → Validator 结构校验 → Validator 枚举值校验 → Validator 安全扫描（14 种危险模式 + 9 个禁止字段）→ Normalizer 防御性类型转换
6. **LLM 失败降级**：LLM 调用失败 → fallback_diagnosed → 仅使用 system_diagnostic_checker 输出，不影响上游 Metric Evaluation；`ready_for_closed_loop_refinement` 根据系统规则判断
7. **诊断结果是 Advisory，但进入闭环优化**：区分 diagnostic_facts（系统可验证事实）/ llm_diagnosis（LLM 诊断判断）/ refinement_hints（给下游闭环优化的建议）/ confidence_level（LLM 信心）

**前端面板**（[ResultDiagnosisPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/resultDiagnosis/components/ResultDiagnosisPanel.tsx)）：
- 提供 "Run Diagnosis" 和 "Re-run Diagnosis" 两个按钮
- 展示 9 个 Tab 子区：
  1. **Overview** — Overall Assessment（performance_level / baseline_improvement_level / stability_level / main_issue_category / should_refine / confidence_level / summary）
  2. **Findings** — Diagnostic Findings 表格（Type / Severity / Evidence / Description / Affected Models / Recommended Actions / Confidence），含 colgroup 列宽控制 + overflowX 滚动
  3. **Evidence** — 6 类证据详细展示（Metric / Baseline / Fold Stability / Dataset / Feature / Pipeline Evidence）
  4. **Hypotheses** — Root Cause Hypotheses 卡片（root_cause_type / likelihood / actionability / description / supporting_findings）
  5. **Recommendations** — Refinement Recommendations 表格（Target Stage / Type / Priority / Description / Expected Benefit / Risk / Human Review）
  6. **System Checks** — 9 条系统规则检查结果（绿色 OK / 红色 TRIGGERED）
  7. **LLM Diagnosis** — LLM 诊断状态摘要（confidence / findings 数量 / hypotheses 数量 / recommendations 数量）
  8. **Closed-loop Input** — 闭环优化输入预览（should_refine / ready / refinement_focus / constraints_to_preserve / avoid_actions / suggested_next_iteration）
  9. **Full JSON** — 完整诊断 JSON
- 状态颜色：diagnosed=green / diagnosed_with_warning=orange / fallback_diagnosed=orange / failed=red
- 诊断类型 11 种颜色映射（underfitting=orange / overfitting_risk=red / feature_insufficiency=purple 等）

**状态与枚举**（[enums.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/enums.py)）：
- ResultDiagnosisStatus：diagnosing / diagnosed / diagnosed_with_warning / fallback_diagnosed / failed
- DiagnosisMode：llm_based / hybrid / system_rule_based
- DiagnosisType（11 种）：underfitting / overfitting_risk / feature_insufficiency / feature_noise / model_mismatch / hpo_insufficient / validation_instability / weak_baseline_improvement / data_quality_limitation / metric_mismatch / limited_pipeline_gain
- Severity：low / medium / high / critical
- EvidenceStrength：weak / moderate / strong
- ConfidenceLevel：low / medium / high
- TargetStage（6 个优化环节）：workflow_planning / feature_engineering / preprocessing / model_search / hpo / validation
- RecommendationType（5 种）：expand_features / change_models / increase_hpo / adjust_validation / change_metric

**异常类**（[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/exceptions.py)）：
- ResultDiagnosisNotFoundException（RESULT_DIAGNOSIS_NOT_FOUND）/ MetricEvaluationRequiredException（METRIC_EVALUATION_REQUIRED）/ MetricEvaluationNotReadyException（METRIC_EVALUATION_NOT_READY_FOR_DIAGNOSIS）/ DiagnosisInputInvalidException（RESULT_DIAGNOSIS_INPUT_INVALID）/ DiagnosticContextBuildException（DIAGNOSTIC_CONTEXT_BUILD_FAILED）/ LLMDiagnosisCallException（LLM_DIAGNOSIS_CALL_FAILED）/ LLMDiagnosisParseException（LLM_DIAGNOSIS_PARSE_FAILED）/ LLMDiagnosisValidationException（LLM_DIAGNOSIS_VALIDATION_FAILED）/ ClosedLoopInputBuildException（CLOSED_LOOP_REFINEMENT_INPUT_BUILD_FAILED）/ DiagnosisArtifactSaveException（DIAGNOSIS_ARTIFACT_SAVE_FAILED）

**完成度**：~90%。核心 15 步流水线完整，LLM + System Rule 双轨诊断链路完整，7 个 API 端点就位，11 种诊断类型 + 26 条别名映射覆盖 PRD 需求，9 条系统规则检查完整，LLM 输出 parser→validator→normalizer 三道安全防护就位，LLM 失败降级 fallback 机制可用，closed_loop_refinement_input 构建完整，`needs_fresh_diagnosis()` 过时检测就位，前端 9 Tab 面板集成完毕（含 iteration context 实时展示）。

---

### 5.13 模块十三：LLM-driven Workflow Refinement（LLM 驱动的工作流精炼与闭环迭代）★ 最新

**文件位置**：[backend/app/modules/workflow_refinement/](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/)

**输入**：
- `WorkflowRefinementCreateRequest`（[schemas.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/schemas.py)）：result_diagnosis_id（可选）, force_rerun, use_llm, max_iterations, current_iteration_index, decision_profile（compact/balanced/full，默认 balanced）, allow_full_workflow_rerun, allow_partial_rerun, minimum_improvement_threshold, notes
- 上游 `ResultDiagnosis`：必须满足 `status ∈ {diagnosed, diagnosed_with_warning, fallback_diagnosed}` 且 `ready_for_closed_loop_refinement = true`
- 必须消费 `closed_loop_refinement_input_json`（含 should_refine / refinement_focus / priority_recommendations / constraints_to_preserve / avoid_actions / suggested_next_iteration_profile）
- 可选/自动读取 10 个上游模块数据和跨迭代实验历史

**处理逻辑**（14 步流水线）：
1. `context_builder.build_workflow_refinement_context()` — 校验上游 ResultDiagnosis 状态和 `ready_for_closed_loop_refinement` 标记。幂等性检查：若 `force_rerun=False` 且已存在相同 task+diagnosis 的 DECIDED/DECIDED_WITH_WARNING 记录，直接返回已有结果
2. `refinement_input_loader.load_closed_loop_refinement_input()` — 提取 `closed_loop_refinement_input_json`，校验 `should_refine` 和 `refinement_focus` 必填字段
3. `experiment_history_collector.collect_experiment_history()` — 从 5 个上游模块仓库收集跨迭代历史：
   - WorkflowRefinement：已完成迭代次数、历史决策
   - MetricEvaluation：各迭代最佳指标、指标趋势（improving/degrading/stable）
   - ResultDiagnosis：重复诊断类型统计（Counter）
   - ModelSearch：已尝试模型族列表
   - PipelineExecution：累计失败率和运行时成本
   - 每个数据源独立 try/except，单个失败不影响整体收集
4. `workflow_refinement_context_builder.build_llm_workflow_refinement_context()` — 组装 LLM 上下文：decision_profile + diagnosis 数据 + closed_loop_refinement_input + experiment_history + 10 个上游模块的 lazily loaded 数据（TaskSpec/TaskInterpretation/DatasetProfile/WorkflowPlan/FeatureEngineering/FeaturePreprocessing/ModelSearchContext/ModelSearch/PipelineGeneration/PipelineExecution/MetricEvaluation，每个模块独立 try/except 保护）
5. `llm_prompt_builder.build_llm_prompt()` — 构建 system prompt（LLM 角色定义 + 11 个决策问题 + 禁止代码声明）和 user message（完整 JSON 上下文 + 22 条 CRITICAL RULES + 严格输出 Schema）
6. `llm_workflow_refiner.LLMWorkflowRefiner.refine()` — 复用 `LLMClient`（定义于 [task_interpretation/llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)）调用 LLM
7. `llm_response_parser.parse_llm_response()` — 3 种策略：正则提取 `{...}` / 直接解析 / 去 markdown fence 重试
8. `workflow_refinement_validator.validate_workflow_refinement_decision()` — 结构校验 + 语义一致性校验：
   - decision ∈ {proceed_next_stage, iterate_refinement}
   - confidence ∈ {low, medium, high}
   - rerun stage ∈ VALID_RERUN_STAGES（9 个阶段）
   - 若 decision = proceed_next_stage：revised_workflow_plan 必须为 null，final_pipeline_selection_input 必须非空
   - 若 decision = iterate_refinement：revised_workflow_plan 必须非空，iteration_rerun_plan 必须非空
9. `workflow_refinement_validator.scan_for_forbidden_content()` — 递归扫描整个 LLM 响应的禁止内容：
   - 15 个危险代码模式：import / def / class / eval / exec / subprocess / os.system / model.fit / model.predict / Pipeline( / optuna.create_study / __import__ / compile / globals / locals
   - 12 个禁止字段：code / python_code / script / shell_command / sql / train_code / executable / workflow_patch / pipeline_patch / model_fit_code / direct_execution
10. `workflow_refinement_normalizer.normalize_workflow_refinement_result()` — 标准化 LLM 输出：
    - 模糊匹配 normalization：decision ("proceed"/"final"/"next" → "proceed_next_stage"; "iterate"/"refine"/"revise" → "iterate_refinement")
    - 模糊匹配 confidence level 和 rerun stage names
    - null-consistency 强制：根据 decision 类型强制设置 revised_plan / rerun_plan / final_selection_input 为 null
    - 对象→列表转换：将 LLM 输出的对象数组转为字符串列表
    - 对象→float 转换：将 LLM 输出的对象类型数值转为 float
11. `revised_workflow_plan_validator.validate_revised_workflow_plan()` — 若 decision = iterate_refinement，校验修订版 WorkflowPlan 结构：9 个必填 top-level 字段 + 各子对象的必填字段 + 枚举值 + 数值范围（n_splits: 2-10, confidence_score: 0-1）
12. `workflow_plan_delta_builder.build_workflow_plan_delta()` — 加载原始 WorkflowPlan，逐 section（7 个 strategy section）计算 diff（added / removed / changed 字段级别），关联变更原因到诊断发现，标记 rejected_or_unsafe_changes
13. 根据 decision 分支构建：
    - **PROCEED_NEXT_STAGE**：`final_selection_input_builder.build_final_selection_input()` — 构建 FinalPipelineSelectionInput（含 selection_policy 标准化：字符串→列表，workflow_refinement_id / candidate_ids / best_model/trial/pipeline IDs / constraints / ready_for_final_pipeline_selection）
    - **ITERATE_REFINEMENT**：`iteration_rerun_plan_builder.build_iteration_rerun_plan()` — 构建 IterationRerunPlan（含 next_iteration_index / rerun_stages 标准化 / reuse_artifacts / invalidate_artifacts / expected_improvement_targets / minimum_improvement_threshold / stop_after_next_iteration_if_no_gain）
14. `refinement_artifact_manager.save_refinement_artifacts()` — 保存 9 个 JSON artifacts 到 `/app/artifacts/workflow_refinement/{wr_id}/`：
    - workflow_refinement_result.json / llm_refinement_context.json / llm_request.json / llm_response.json / revised_workflow_plan.json / workflow_plan_delta.json / iteration_rerun_plan.json / final_pipeline_selection_input.json / validation_result.json / manifest.json
15. `builder.build_response()` — 组装 WorkflowRefinementResponse（含所有子 DTO：DecisionReasoning / EvidenceUsed / RevisedWorkflowPlanResponse / WorkflowPlanDelta / IterationRerunPlan / FinalPipelineSelectionInput / LLMWorkflowRefinementResult / WorkflowRefinementValidationResult / ArtifactManifest）
16. 持久化到数据库：7 个 JSONB 字段（workflow_refinement_json / revised_workflow_plan_json / workflow_plan_delta_json / iteration_rerun_plan_json / final_pipeline_selection_input_json / llm_request_json / llm_response_json / validation_result_json）+ 状态字段

**Adopt & Rerun 闭环机制**：
- `adopt_revised_plan()`（[service.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/service.py)）：
  1. 校验 decision = iterate_refinement 且 revised_workflow_plan_json 非空
  2. 调用 `validate_revised_workflow_plan()` 二次校验
  3. 调用 `WorkflowPlanningService.adopt_revised_plan()` 将修订版 Plan 持久化为新 WorkflowPlan 记录（`planning_mode = "refinement_adopted"`, `status = "planned"`）
  4. 更新 WorkflowRefinement 记录状态为 ADOPTED，记录 adopted_workflow_plan_id 和 adopted_at 时间戳
  5. 返回完整的 adopt 结果：adopted_plan_id / rerun_stages / reuse_artifacts / invalidate_artifacts / expected_improvement_targets
- 前端 `handleAdoptAndRerun()`（[WorkflowRefinementPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/workflowRefinement/components/WorkflowRefinementPanel.tsx)）：
  1. 调用 `adoptRevisedPlan()` API
  2. 按 `rerun_stages` 顺序依次调用各阶段的 create API（feature_engineering → feature_preprocessing → model_search_context → model_search → pipeline_generation → pipeline_execution → metric_evaluation）
  3. 实时进度日志显示（绿色成功 / 红色失败）
  4. 任何阶段失败则停止后续执行
  5. 全部成功后显示下一步指引：Re-run Result Diagnosis → Run Workflow Refinement again

**LLM 安全性**：
- **Prompt 约束**：System prompt 声明 "You must not output executable code. You cannot start model training. You cannot modify the data_preparation or model registry directly."
- **Validator 一致性校验**：decision 类型与是否提供 revised_plan/rerun_plan/final_selection_input 的一致性强制检查
- **递归安全扫描**：`scan_for_forbidden_content()` 递归遍历整个 JSON 响应
- **三重防护**：Prompt 约束 → Validator 结构校验 → Safety Scanner 禁止内容检测

**LLM 输出 Schema**（[llm_prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/llm_prompt_builder.py)）：
- workflow_refinement_decision（decision / decision_confidence_level / primary_reason / should_generate_revised_workflow_plan / recommended_rerun_from_stage / should_proceed_to_final_selection）
- decision_reasoning（7 维度：performance / baseline / stability / diagnosis / cost / risk / final_reasoning_summary）
- evidence_used[]（evidence_id / source_module / evidence_type / source_field / value / interpretation / supports_decision）
- revised_workflow_plan（9 个 strategy section + refinement_metadata：changed_sections / preserved_sections）
- iteration_rerun_plan（next_iteration_index / recommended_rerun_from_stage / rerun_stages / reuse_artifacts / invalidate_artifacts / expected_improvement_targets / minimum_improvement_threshold / stop_after_next_iteration_if_no_gain）
- final_pipeline_selection_input（candidate_metric_evaluation_ids / current_best_model_id / current_best_trial_id / current_best_pipeline_spec_id / selection_policy / constraints / ready_for_final_pipeline_selection）
- confidence_level

**输出**：
- `WorkflowRefinementResponse`：含 workflow_refinement_id / task_id / result_diagnosis_id / iteration_index / status / decision / decision_confidence_level / decision_reasoning / evidence_used / recommended_rerun_from_stage / revised_workflow_plan / workflow_plan_delta / iteration_rerun_plan / final_pipeline_selection_input / llm_workflow_refinement / workflow_refinement_validation_result / artifact_manifest / ready_for_iteration / ready_for_final_pipeline_selection
- `AdoptRevisedPlanResult`：adopted / workflow_refinement_id / task_id / adopted_workflow_plan_id / recommended_rerun_from_stage / rerun_stages[] / reuse_artifacts[] / invalidate_artifacts[] / expected_improvement_targets[] / reasoning
- `IterationContext`（用于前端迭代位置显示）：is_part_of_iteration / diagnosis_position / total_diagnoses / workflow_refinement_id / iteration_index / decision / status

**API 接口**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/api.py)）：
- `POST /api/workflow-refinements/{task_id}` — 运行工作流精炼（创建 LLM 决策）
- `GET /api/workflow-refinements/{workflow_refinement_id}` — 获取指定精炼记录
- `GET /api/tasks/{task_id}/workflow-refinement` — 获取任务的最新精炼
- `POST /api/workflow-refinements/{task_id}/rerun` — 强制重新精炼
- `GET /api/workflow-refinements/{workflow_refinement_id}/revised-workflow-plan` — 获取修订版 WorkflowPlan
- `GET /api/workflow-refinements/{workflow_refinement_id}/iteration-rerun-plan` — 获取迭代重跑计划
- `GET /api/workflow-refinements/{workflow_refinement_id}/final-pipeline-selection-input` — 获取最终 Pipeline 选择输入
- `GET /api/result-diagnoses/{rd_id}/iteration-context` — 获取指定诊断的迭代上下文（用于前端显示迭代位置）
- `POST /api/workflow-refinements/{workflow_refinement_id}/adopt` — 采纳修订版 Plan（持久化为新 WorkflowPlan 并返回重跑指令）

**数据模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/model.py)）：
- `WorkflowRefinement` 表（`workflow_refinement`）：id (PK, `wr_{8hex}`), task_id (indexed), result_diagnosis_id (indexed), metric_evaluation_id, pipeline_execution_id, source_workflow_plan_id, iteration_index, status (indexed, deciding/decided/decided_with_warning/adopted/failed), decision (indexed), decision_confidence_level, recommended_rerun_from_stage, ready_for_iteration (indexed), ready_for_final_pipeline_selection (indexed), workflow_refinement_json (JSONB), revised_workflow_plan_json (JSONB), workflow_plan_delta_json (JSONB), iteration_rerun_plan_json (JSONB), final_pipeline_selection_input_json (JSONB), llm_request_json (JSONB), llm_response_json (JSONB), validation_result_json (JSONB), artifact_dir, error_message, created_at (indexed), updated_at

**状态与枚举**（[enums.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/enums.py)）：
- WorkflowRefinementStatus：deciding / decided / decided_with_warning / adopted / failed
- WorkflowRefinementDecision：proceed_next_stage / iterate_refinement
- DecisionConfidenceLevel：low / medium / high
- RerunStage（9 个）：workflow_planning / feature_engineering / feature_preprocessing / model_search_context / model_search / pipeline_generation / pipeline_execution / metric_evaluation / final_pipeline_selection
- RERUN_STAGE_RECOMMENDATIONS：诊断类型 → 建议重跑入口阶段的映射（如 underfitting→workflow_planning, hpo_insufficient→model_search）

**异常类**（[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/exceptions.py)）：
- 13 个专用异常：WorkflowRefinementException / WorkflowRefinementNotFoundException / ResultDiagnosisRequiredException / ResultDiagnosisNotReadyException / WorkflowRefinementInputInvalidException / WorkflowRefinementContextBuildException / LLMWorkflowRefinementCallException / LLMWorkflowRefinementParseException / LLMWorkflowRefinementValidationException / RevisedWorkflowPlanValidationException / IterationRerunPlanBuildException / FinalSelectionInputBuildException / WorkflowRefinementArtifactSaveException

**关键设计约束**：
1. **LLM 定位于决策顾问**：LLM 输出结构化决策和建议，但不直接修改数据库、不直接训练模型、不生成可执行代码
2. **双路径输出**：LLM 输出两种互斥决策路径（proceed vs iterate），Validator 强制语义一致性（路径与提供的计划/输入必须匹配）
3. **多级安全防护**：Prompt 约束 → Validator 一致性校验 → Safety Scanner 递归禁止内容检测
4. **Normalizer 防御性处理**：处理 LLM 常见输出 quirk（模糊字符串、对象代替字符串/数字），确保 Pydantic 校验不失败
5. **Adopt & Rerun 闭环**：adopt_revised_plan 将 LLM 修订的 Plan 持久化为新 WorkflowPlan（planning_mode="refinement_adopted"），前端按 plan 顺序自动重跑 pipeline 阶段
6. **跨迭代历史**：experiment_history_collector 从 5 个模块收集完整迭代数据，供 LLM 做出跨迭代比较决策
7. **Workflow Plan Delta 可追溯**：逐 section 计算原始 vs 修订计划 diff，关联变更原因到诊断发现
8. **幂等性**：同一 task+diagnosis 的已决策记录直接返回，避免重复 LLM 调用

**前端面板**（[WorkflowRefinementPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/workflowRefinement/components/WorkflowRefinementPanel.tsx)）：
- 提供 "Run Workflow Refinement"（紫色）和 "Re-run Refinement"（橙色）两个按钮
- 决策为 iterate_refinement 且 ready_for_iteration 时显示 "Adopt & Rerun" 区域（橙色按钮 → 确认对话框 → 实时进度日志）
- 9 个 Tab 子区：
  1. **Decision** — 决策结果（decision / confidence / recommended_rerun_stage / ready_for_iteration / ready_for_final_selection）
  2. **Reasoning** — 7 维度评估（performance / baseline / stability / diagnosis / cost / risk / final summary）
  3. **Evidence** — 证据详细表格（6 列：source_module / evidence_type / source_field / value / interpretation / supports）
  4. **Revised Plan** — 修订版 WorkflowPlan（9 个 strategy section + refinement_metadata）
  5. **Plan Delta** — 原始 vs 修订 diff（changed/preserved sections + 逐字段变更 + rejected/unsafe changes）
  6. **Rerun Plan** — 迭代重跑计划（entry point badge / rerun stages badges / reuse/invalidate artifacts / expected improvements）
  7. **Final Selection** — Final Pipeline Selection Input（ready / best model/trial/pipeline IDs / candidate IDs / selection_policy）
  8. **Validation** — 5 组件有效性 + safety_scan 结果
  9. **Full JSON** — 完整精炼结果 JSON
- Adopt & Rerun 流程包含完整的用户指引（Next Steps 绿色提示框），指导用户在闭环迭代中的后续操作

**完成度**：~90%。核心 14 步流水线完整，9 个 API 端点就位，LLM 决策双路径完整，Adopt & Rerun 闭环迭代机制完整，跨迭代历史收集就位，Workflow Plan Delta 可追溯，前端 9 Tab 面板 + Adopt & Rerun 集成完毕，13 个专用异常覆盖所有故障模式。`closed_loop_refinement/` 目录已成历史残留（仅含 `__pycache__`，无源码），其全部需求已由本模块实现。

---

### 5.14 模块更新说明（相对于上一版文档）

**模块四（Workflow Planning）更新**：
- `enums.py`：新增 `PlanningMode.REFINEMENT_ADOPTED = "refinement_adopted"`
- `service.py`：新增 `adopt_revised_plan()` 方法（~90 行），将模块十三的 LLM 修订版 WorkflowPlan 持久化为新 WorkflowPlan 记录（`planning_mode = "refinement_adopted"`, `status = "planned"`），提取所有 9 个 strategy section + refinement_metadata

**模块十二（Result Diagnosis）更新**：
- `api.py`：新增 `GET /api/tasks/{task_id}/result-diagnosis/needs-fresh`（检查诊断是否过时）+ `GET /api/result-diagnoses/{rd_id}/iteration-context` 被路由到 workflow_refinement 模块
- `service.py`：新增 `needs_fresh_diagnosis()` 方法——比较现有诊断的 metric_evaluation_id 与最新 metric_evaluation_id 是否一致，若不一致则标记 `needs_fresh: true`
- `repository.py`：新增 `count_by_task_id()` 方法
- `enums.py`：`VALID_SEVERITY_VALUES` 新增 `"unknown"` 值；`DIAGNOSIS_TYPE_ALIASES` 新增 `"underfitting_risk" → DiagnosisType.UNDERFITTING` 映射（现共 26 条）

**前端更新**：
- `resultDiagnosis` 面板：新增 `iteration context` 显示——根据是否属于迭代显示紫色 `#迭代号` badge（含 analysis position 信息）
- `resultDiagnosis` API：新增 `checkNeedsFreshDiagnosis()` 和 `getIterationContextForDiagnosis()` 两个函数
- `resultDiagnosis` types：新增 `IterationContext` 接口（is_part_of_iteration / diagnosis_position / total_diagnoses / workflow_refinement_id / iteration_index / decision / status）
- `workflowRefinement` API：新增 `adoptRevisedPlan()` 函数
- `workflowRefinement` panel：新增完整 "Adopt & Rerun" 功能（含确认对话框、实时进度日志、各阶段 API 顺序调用、错误处理、下一步指引）
- `workflowRefinement` constants/type：新增 `adopted` 状态颜色/标签和 `AdoptRevisedPlanResult` 接口

---

### 5.15 Featurizer Registry / Model Registry / HPO Registry / Pipeline Template Registry（共享能力注册表）

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
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 9: 可执行流水线生成 ★ 新增                                             │
│                                                                          │
│ POST /api/pipeline-generations/{task_id}                                 │
│   └── PipelineGenerationService.create_pipeline_generation()             │
│       ├── context_builder.build_pipeline_generation_context()            │
│       │   └── 读取模块八最新 ModelSearchPlan → 校验 ready_for_pipeline_generation=true │
│       │   └── 加载 Model Registry + HPO Registry + Pipeline Template Registry │
│       ├── artifact_resolver.resolve_artifacts()                          │
│       │   └── 校验 model_ready_matrix_path + preprocessor_artifact_path  │
│       │   └── _is_safe_path() 白名单安全校验（拒绝 .. 遍历）                │
│       ├── component_binder.bind_components()                             │
│       │   └── model_id / hpo_method / validation_strategy / metrics → Registry 绑定 │
│       ├── pipeline_spec_builder.build_pipeline_specs()                   │
│       │   └── 基于 4 个 Pipeline Template 生成每模型 PipelineSpec         │
│       │   └── 角色分配: baseline / candidate / hpo_candidate              │
│       ├── trial_plan_builder.build_trial_plan()                          │
│       │   └── 从上游 HPO Plan 构建 TrialPlan + allocation                │
│       ├── pipeline_validator.validate_pipeline_bundle()                  │
│       │   └── 8 项检查: structure / registry / artifact / task_type     │
│       │        / search_space / trial / data_fields / execution_input    │
│       ├── safety_checker.check_pipeline_safety()                          │
│       │   └── 15+ 种危险模式扫描 (import/eval/exec/subprocess/.fit())   │
│       ├── [可选] LLM Advisory Review: parse → validate → normalize        │
│       │   ├── llm_review_prompt_builder → 8 维度顾问式审查 prompt         │
│       │   ├── llm_pipeline_reviewer.review() → LLMClient                 │
│       │   ├── llm_review_parser → 纯 JSON 解析                           │
│       │   ├── llm_review_validator → 25+ 禁止模式 + 禁止字段扫描          │
│       │   └── llm_review_normalizer → 标准化为 LLMAdvisoryReview         │
│       │       ├── 剥离旧式审批字段 → raw_llm_summary                       │
│       │       ├── 映射 approval → risk_level                             │
│       │       ├── 转换 confidence_score → confidence_level               │
│       │       └── 强制 execution_impact = "non_blocking"                 │
│       ├── execution_input_builder.build_execution_input()                │
│       │   └── 构建下游 Pipeline Execution 合同                            │
│       ├── builder.build_pipeline_bundle()                                │
│       │   └── 构建完整 PipelineBundle                                    │
│       ├── builder.build_pipeline_generation_response()                   │
│       │   └── status 由 errors/warnings 决定                              │
│       │   └── ready_for_execution 仅由 System Validator + Safety Checker  │
│       │       + Artifact Manifest 决定，LLM 无权影响                        │
│       └── 持久化到 PipelineGeneration 表（pipeline_json + execution_input_json │
│           + llm_request/response_json）                                     │
│                                                                          │
│ 输出: Pipeline Bundle + Execution Input (供下游 Pipeline Execution 消费)   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 10: 流水线执行与训练 ★ 最新                                            │
│                                                                          │
│ POST /api/pipeline-executions/{task_id}                                  │
│   └── PipelineExecutionService.create_pipeline_execution()               │
│       ├── context_builder.build_execution_context()                      │
│       │   └── 读取模块九最新 PipelineGeneration → 校验 ready_for_execution=true │
│       │   └── 验证 execution_input_json 存在                              │
│       ├── execution_input_loader.load_execution_input()                  │
│       │   └── 解析 execution_input_json → ExecutionInput Pydantic 模型   │
│       │   └── 校验 pipeline_specs / trial_plan / validation_plan /       │
│       │       evaluation_plan / feature_columns / target_column          │
│       ├── data_matrix_loader.load_model_ready_matrix()                   │
│       │   └── 加载 model_ready_features.parquet                           │
│       │   └── 校验路径安全（无 .. 遍历）/ 特征列 / 目标列 / NaN           │
│       ├── validation_splitter.create_validation_splits()                 │
│       │   └── _normalize_strategy() 标准化策略名                          │
│       │   └── 支持 train_test_split / holdout / k_fold / stratified_k_fold │
│       ├── execution_planner.expand_execution_plan()                      │
│       │   └── PipelineSpecs + TrialPlan → 扁平化 trial 计划              │
│       │   └── baseline → 1 trial, fixed_params → 1 trial,               │
│       │       hpo → max_trials trials from search_space                  │
│       ├── training_artifact_manager.ensure_execution_dir()               │
│       │   └── → /app/artifacts/training/{pe_id}/{predictions,models,splits,logs}/ │
│       ├── controlled_executor.execute_training()                         │
│       │   ├── 按 pipeline_run 分组迭代 trial plans                       │
│       │   ├── trial_runner.run_trial()                                   │
│       │   │   └── 遍历 validation splits → fold_runner.run_fold()        │
│       │   │       ├── model_factory.create_model() → sklearn 实例        │
│       │   │       │   └── 显式 sklearn 映射（非动态 import）              │
│       │   │       │   └── 校验 Model Registry + task_type 兼容性         │
│       │   │       ├── hpo_trial_generator.generate_hpo_trials()          │
│       │   │       │   └── 解析 SearchSpaceItem → random/grid search      │
│       │   │       ├── model.fit(X_train, y_train)                        │
│       │   │       ├── model.predict(X_val) → y_pred                      │
│       │   │       ├── _compute_raw_metrics()                             │
│       │   │       │   └── MAE/MSE/RMSE/R2 (回归) / Accuracy (分类)      │
│       │   │       └── prediction_writer.save_predictions()               │
│       │   │           └── → predictions/{trial_id}_fold_{k}.parquet      │
│       │   └── 支持 sequential / limited_parallel / timeout / fail_fast   │
│       ├── 收集 prediction_artifact_paths + model_artifact_paths          │
│       ├── metric_input_builder.build_metric_evaluation_input()           │
│       │   └── 构建下游 Metric Evaluation 合同（含 ready 标记）           │
│       ├── save_split_metadata / save_trial_results / save_manifest       │
│       │   / save_execution_result / save_metric_evaluation_input         │
│       ├── builder.build_response()                                       │
│       │   └── 组装 PipelineExecutionResponse（含 counts / pipeline_runs  │
│       │       / trials / metric_input / artifacts / runtime_env）        │
│       └── 持久化到 PipelineExecution 表（execution_json +                 │
│           metric_evaluation_input_json model_dump(mode='json')）          │
│                                                                          │
│ 输出: Pipeline Execution Result + Metric Evaluation Input                │
│        (供下游 Metric Evaluation 消费)                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 11: 指标评估 ★ 最新                                                   │
│                                                                          │
│ POST /api/metric-evaluations/{task_id}                                   │
│   └── MetricEvaluationService.create_metric_evaluation()                  │
│       ├── context_builder.build_metric_evaluation_context()              │
│       │   └── 读取模块十最新 PipelineExecution → 校验 status +             │
│       │       ready_for_metric_evaluation = true                          │
│       ├── metric_input_loader.load_metric_evaluation_input()              │
│       │   └── 解析 metric_evaluation_input_json                           │
│       │   └── 校验 task_type / target_column / primary_metric /           │
│       │       metric_direction 必填字段                                   │
│       ├── prediction_artifact_loader.load_prediction_artifacts()          │
│       │   └── 加载预测 parquet（路径安全 / 必填列 / 数值校验 / NaN/Inf）     │
│       │   └── build_prediction_frame_map() → trial_id→{fold→DataFrame}    │
│       ├── Build Trial Info Map（从 execution_json 补充元数据）              │
│       │   ├── pipeline_run_results → spec_role_map + spec_family_map      │
│       │   ├── trial_results → full_trial_map (pipeline_spec_id等)         │
│       │   └── 交叉引用 → trial_info_map (pipeline_role/model_family等)     │
│       ├── fold_metric_evaluator.evaluate_fold_metrics()                  │
│       │   └── 遍历 trial_fold_map → metric_calculator.calculate_metric()  │
│       ├── trial_metric_aggregator.aggregate_trial_metrics()               │
│       │   └── 跨 fold 聚合 → mean/std/min/max/median/cv                   │
│       ├── pipeline_metric_aggregator.aggregate_pipeline_metrics()         │
│       │   └── 按 model_id 聚合 → best_trial 选取                          │
│       ├── model_ranker.rank_models_and_trials()                           │
│       │   └── primary_metric + direction 排序 → std 平局决胜              │
│       │   └── → best_trial / best_model_id / best_trial_id /              │
│       │       best_pipeline_spec_id / ranking_items                       │
│       ├── baseline_comparator.compare_against_baselines()                 │
│       │   └── 按 pipeline_role 筛选 baseline vs candidate                 │
│       │   └── → best_baseline / best_candidate / improvement              │
│       ├── Compute improvement for ranking items                           │
│       │   └── improvement_over_best_baseline + improvement_percentage     │
│       ├── result_diagnosis_input_builder.build_result_diagnosis_input()   │
│       │   └── 构建下游 Result Diagnosis 合同（含 ready 标记）              │
│       ├── evaluation_artifact_manager → 保存 8 个 JSON artifacts          │
│       │   └── → /app/artifacts/evaluation/{me_id}/                        │
│       ├── metric_validator.validate_metric_results() → 6 项检查            │
│       ├── builder.build_response()                                        │
│       │   └── 组装 MetricEvaluationResponse（含 metric_summary /          │
│       │       trial_metrics / ranking / baseline_comparison /             │
│       │       validation / artifacts / diagnosis_input）                  │
│       └── 持久化到 MetricEvaluation 表（evaluation_json +                  │
│           result_diagnosis_input_json model_dump(mode='json')）            │
│                                                                          │
│ 输出: Metric Results + Model Ranking + Baseline Comparison               │
│        + Result Diagnosis Input (供下游 Result Diagnosis 消费)            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 12: LLM 结果诊断 ★ 最新                                               │
│                                                                          │
│ POST /api/result-diagnoses/{task_id}                                     │
│   └── ResultDiagnosisService.create_result_diagnosis()                   │
│       ├── context_builder.build_result_diagnosis_context()               │
│       │   └── 读取模块十一最新 MetricEvaluation → 校验 status +            │
│       │       ready_for_result_diagnosis = true                           │
│       ├── diagnosis_input_loader.load_result_diagnosis_input()            │
│       │   └── 解析 result_diagnosis_input_json（9 个必填字段检查）          │
│       ├── [_load_optional_context()] 可选加载上游 context                  │
│       ├── evidence_extractor.extract_evidence()                          │
│       │   └── 6 类证据提取：metric / baseline / fold_stability /          │
│       │       dataset / feature / pipeline                                │
│       ├── system_diagnostic_checker.run_system_checks()                  │
│       │   └── 9 项规则诊断（含可配置阈值）                                  │
│       ├── diagnostic_context_builder.build_llm_diagnostic_context()       │
│       │   └── compact/standard/full 三种 profile                          │
│       ├── llm_prompt_builder.build_llm_prompt()                          │
│       │   └── System prompt（14 个诊断维度 + JSON Schema）                  │
│       ├── llm_result_diagnoser.diagnose() → LLMClient                    │
│       │   └── httpx POST → 获取结构化诊断 JSON                             │
│       ├── llm_response_parser.parse_llm_diagnosis()                      │
│       │   └── 3 种策略：direct json / markdown 提取 / 大括号提取           │
│       ├── llm_diagnosis_validator.validate_llm_diagnosis()               │
│       │   ├── 结构校验：required fields + enum values + evidence 非空     │
│       │   ├── 别名支持：DIAGNOSIS_TYPE_ALIASES（25 条目）                   │
│       │   └── 安全扫描：14 种代码模式 + 9 个禁止字段                        │
│       ├── [LLM 失败 → fallback] llm_diagnosis_normalizer.normalize()      │
│       │   └── canonicalize diagnosis_type + coerce int→str + default fill │
│       ├── [LLM 成功] llm_diagnosis_normalizer.normalize()                 │
│       │   └── 标准化为 LLMDiagnosisResult Pydantic 模型                    │
│       ├── refinement_input_builder.build_closed_loop_refinement_input()   │
│       │   └── 构建 SuggestedNextIterationProfile（含 LLM 建议 +            │
│       │       system checks 交叉验证）                                     │
│       │   └── 设置 ready_for_closed_loop_refinement 标记                   │
│       ├── diagnosis_artifact_manager.save_all_artifacts()                 │
│       │   └── → /app/artifacts/diagnosis/{rd_id}/                         │
│       │       diagnosis_result.json / evidence_summary.json /              │
│       │       system_checks.json / closed_loop_refinement_input.json /     │
│       │       llm_request.json / llm_response.json / manifest.json         │
│       ├── builder.build_result_diagnosis_response()                       │
│       │   └── 组装 ResultDiagnosisResponse（含 llm_diagnosis /            │
│       │       system_checks / evidence_summary / refinement_input /       │
│       │       artifact_manifest / warnings）                               │
│       └── 持久化到 ResultDiagnosis 表（diagnosis_json +                    │
│           closed_loop_refinement_input_json + llm_request_json +           │
│           llm_response_json + system_checks_json）                         │
│                                                                          │
│ 输出: Diagnosis Result + Closed-loop Refinement Input                    │
│        (供下游 Workflow Refinement 消费)                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 13: LLM Workflow Refinement（工作流精炼与闭环迭代）★ 最新              │
│                                                                          │
│ POST /api/workflow-refinements/{task_id}                                  │
│   └── WorkflowRefinementService.create_workflow_refinement()              │
│       ├── context_builder.build_workflow_refinement_context()             │
│       │   └── 读取模块十二最新 ResultDiagnosis → 校验 status +            │
│       │       ready_for_closed_loop_refinement = true                      │
│       │   └── 幂等性检查：已决策的相同记录直接返回                           │
│       ├── refinement_input_loader → 校验 closed_loop_refinement_input     │
│       ├── experiment_history_collector → 5 个上游模块跨迭代数据收集        │
│       │   └── WorkflowRefinement / MetricEvaluation / ResultDiagnosis     │
│       │       / ModelSearch / PipelineExecution                           │
│       │   └── 每模块独立 try/except，单点失败不影响整体                     │
│       ├── workflow_refinement_context_builder → 组装 LLM 上下文            │
│       │   └── decision_profile + diagnosis + closed_loop_input            │
│       │       + experiment_history + 10 个 lazily loaded 上游模块          │
│       ├── llm_prompt_builder.build_llm_prompt()                           │
│       │   └── System prompt（11 个决策问题 + 禁止代码）                     │
│       │   └── User message（完整 JSON 上下文 + 22 条 CRITICAL RULES）      │
│       ├── LLMWorkflowRefiner.refine() → LLMClient                         │
│       │   └── httpx POST → 获取结构化 Workflow Refinement Decision JSON   │
│       ├── llm_response_parser → 3 种策略提取 JSON                          │
│       ├── workflow_refinement_validator                                   │
│       │   ├── validate_decision()：决策/置信度/重跑阶段枚举 +               │
│       │   │   语义一致性（proceed→final_selection_input非空,                │
│       │   │   iterate→revised_plan + rerun_plan 非空）                     │
│       │   └── scan_for_forbidden_content()：递归扫描 15 种代码模式          │
│       │       + 12 个禁止字段                                              │
│       ├── workflow_refinement_normalizer.normalize()                       │
│       │   ├── 模糊匹配 decision / confidence / stage names                  │
│       │   ├── 强制 null-consistency（按 decision 类型）                     │
│       │   ├── 对象→字符串列表 / 对象→float 转换                             │
│       │   └── 设置 revised_plan.status="planned_by_refinement"             │
│       ├── [若 decision=iterate_refinement]                                │
│       │   ├── validate_revised_workflow_plan() → 9 个 top-level 字段      │
│       │   │   + 子对象必填 + 枚举 + 范围                                    │
│       │   ├── build_workflow_plan_delta()                                  │
│       │   │   └── 加载原始 WorkflowPlan → 逐 section diff                  │
│       │   └── build_iteration_rerun_plan()                                 │
│       │       └── 标准化列表/阈值/推导 rerun stages                         │
│       ├── [若 decision=proceed_next_stage]                                │
│       │   └── build_final_selection_input()                                │
│       │       └── LLM FPSI + best model/trial IDs 回退                     │
│       │       └── normalize_selection_policy（字符串→列表）                │
│       ├── refinement_artifact_manager → 保存 9 个 JSON artifacts           │
│       │   └── → /app/artifacts/workflow_refinement/{wr_id}/                │
│       ├── builder.build_response() → 组装 WorkflowRefinementResponse       │
│       │   └── 含 DecisionReasoning + EvidenceUsed[] +                      │
│       │       RevisedWorkflowPlanResponse + WorkflowPlanDelta +            │
│       │       IterationRerunPlan + FinalPipelineSelectionInput +           │
│       │       LLMWorkflowRefinementResult + ValidationResult +             │
│       │       ArtifactManifest                                             │
│       └── 持久化到 WorkflowRefinement 表（7 个 JSONB 字段）                 │
│                                                                          │
│ [Closed-loop Iteration]                                                   │
│   POST /api/workflow-refinements/{wr_id}/adopt                             │
│     └── adopt_revised_plan()                                               │
│         ├── 校验 decision = iterate_refinement                             │
│         ├── validate_revised_workflow_plan() 二次校验                       │
│         ├── WorkflowPlanningService.adopt_revised_plan()                   │
│         │   └── 持久化为新 WorkflowPlan（planning_mode=refinement_adopted） │
│         ├── 更新 WorkflowRefinement status = ADOPTED                       │
│         └── 返回 rerun_stages / reuse_artifacts / invalidate_artifacts     │
│                                                                          │
│ [前端 Adopt & Rerun]                                                      │
│   └── 依次调用各 stage create API（按 rerun_stages 顺序）                   │
│       → workflow_planning (跳过，已 adopt)                                  │
│       → feature_engineering → feature_preprocessing                       │
│       → model_search_context → model_search                               │
│       → pipeline_generation → pipeline_execution                          │
│       → metric_evaluation                                                 │
│       → 提示用户: Re-run Result Diagnosis                                 │
│       → 提示用户: Run Workflow Refinement again                           │
│                                                                          │
│ 输出: Workflow Refinement Decision + Revised WorkflowPlan                 │
│        + Iteration Rerun Plan (供闭环迭代消费)                              │
│        + Final Pipeline Selection Input (供 Final Selection 消费，尚未实现)  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 关键调用链路

**LLM 调用链路**（模块二、四、七、八、九、十二、十三共享模式）：
```
Service.create_*()
  → context_builder.build_*_context()     # 校验上游 + 构建 context
  → prompt_builder.build_prompt()         # 构建 system/user prompt
  → LLMClient.generate()                  # httpx POST → OpenAI API
  → parser.parse_llm_response()           # 正则提取 JSON
  → validator.validate_*()                # 结构/枚举/安全扫描 校验
  → normalizer.normalize_*()              # 标准化（模块九/十二/十三特有）
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

PipelineGenerationService
  → context_builder.build_pipeline_generation_context()
    ← 读取 ModelSearchPlan 表中的 pipeline_generation_input
    ← 校验 ready_for_pipeline_generation = true
    ← 加载 Model/HPC/Pipeline Component/Pipeline Template Registry
  → artifact_resolver → component_binder → pipeline_spec_builder → trial_plan_builder
  → pipeline_validator (8 checks) → safety_checker (15+ patterns)
  → [可选] LLM advisory review (parse → validate → normalize)
  → execution_input_builder → builder (bundle + response)
  → 输出 Pipeline Generation (pipeline_json + execution_input_json, 存入 PipelineGeneration 表)

PipelineExecutionService
  → context_builder.build_execution_context()
    ← 读取 PipelineGeneration 表中的 execution_input_json
    ← 校验 ready_for_execution = true
  → execution_input_loader → data_matrix_loader (parquet) → validation_splitter
  → execution_planner → training_artifact_manager (setup dirs)
  → controlled_executor (→ trial_runner → fold_runner → model_factory + hpo_trial_generator)
  → metric_input_builder → save artifacts (trial_results/split_metadata/manifest/execution_result/metric_input)
  → builder (response) → persist (execution_json + metric_evaluation_input_json model_dump(mode='json'))
  → 输出 Pipeline Execution Result + Training Artifacts
    → /app/artifacts/training/{pe_id}/predictions/    (*.parquet)
    → /app/artifacts/training/{pe_id}/models/         (*.joblib)
    → /app/artifacts/training/{pe_id}/trial_results.json
    → /app/artifacts/training/{pe_id}/metric_evaluation_input.json

MetricEvaluationService
  → context_builder.build_metric_evaluation_context()
    ← 读取 PipelineExecution 表中的 metric_evaluation_input_json + execution_json
    ← 校验 ready_for_metric_evaluation = true
  → metric_input_loader → prediction_artifact_loader (parquet validation + frame map)
  → Build trial_info_map (execution_json pipeline_run_results + trial_results → pipeline_role/model_family)
  → fold_metric_evaluator → trial_metric_aggregator → pipeline_metric_aggregator (三级聚合)
  → model_ranker (primary_metric + direction → ranking + bests)
  → baseline_comparator (pipeline_role→baseline/candidate→improvement)
  → result_diagnosis_input_builder → evaluation_artifact_manager (save 8 JSON artifacts)
  → metric_validator (6 checks) → builder (response) → persist (evaluation_json + result_diagnosis_input_json model_dump(mode='json'))
  → 输出 Metric Evaluation Result + Model Ranking + Baseline Comparison
    → /app/artifacts/evaluation/{me_id}/metric_results.json
    → /app/artifacts/evaluation/{me_id}/fold_metrics.json
    → /app/artifacts/evaluation/{me_id}/trial_metrics.json
    → /app/artifacts/evaluation/{me_id}/pipeline_metrics.json
    → /app/artifacts/evaluation/{me_id}/model_ranking.json
    → /app/artifacts/evaluation/{me_id}/baseline_comparison.json
    → /app/artifacts/evaluation/{me_id}/result_diagnosis_input.json

ResultDiagnosisService
  → context_builder.build_result_diagnosis_context()
    ← 读取 MetricEvaluation 表中的 result_diagnosis_input_json + evaluation_json
    ← 校验 ready_for_result_diagnosis = true
  → diagnosis_input_loader → evidence_extractor (6 categories)
  → system_diagnostic_checker (9 rule-based checks)
  → diagnostic_context_builder → llm_prompt_builder
  → llm_result_diagnoser (LLMClient) → llm_response_parser (3 strategies)
  → llm_diagnosis_validator (structure + enum + alias + security scan)
  → [LLM success] llm_diagnosis_normalizer → refinement_input_builder
  → [LLM failure] system rule-based fallback → refinement_input_builder
  → diagnosis_artifact_manager (save 7 JSON artifacts)
  → builder (response) → persist (diagnosis_json + closed_loop_refinement_input_json + llm_request/response_json + system_checks_json)
  → 输出 Result Diagnosis + Closed-loop Refinement Input
    → /app/artifacts/diagnosis/{rd_id}/diagnosis_result.json
    → /app/artifacts/diagnosis/{rd_id}/evidence_summary.json
    → /app/artifacts/diagnosis/{rd_id}/system_checks.json
    → /app/artifacts/diagnosis/{rd_id}/closed_loop_refinement_input.json
    → /app/artifacts/diagnosis/{rd_id}/llm_request.json
    → /app/artifacts/diagnosis/{rd_id}/llm_response.json
    → /app/artifacts/diagnosis/{rd_id}/manifest.json

WorkflowRefinementService
  → context_builder.build_workflow_refinement_context()
    ← 读取 ResultDiagnosis 表中的 closed_loop_refinement_input_json + diagnosis_json
    ← 校验 ready_for_closed_loop_refinement = true
  → refinement_input_loader → experiment_history_collector (5 modules)
  → workflow_refinement_context_builder (lazy load 10 upstream)
  → llm_prompt_builder → LLMWorkflowRefiner (LLMClient)
  → llm_response_parser (3 strategies) → workflow_refinement_validator
  → workflow_refinement_normalizer → [branch: revised_plan_validator + delta_builder | fpsi_builder]
  → refinement_artifact_manager (save 9 JSON artifacts)
  → builder (response) → persist (7 JSONB fields)
  → [If ADOPT] adopt_revised_plan → WorkflowPlanningService.adopt_revised_plan()
      → 创建新 WorkflowPlan (mode=refinement_adopted)
      → 返回 rerun plan → 前端顺序重跑 pipeline 阶段
  → 输出 Workflow Refinement Decision + Revised Plan / Final Selection Input
    → /app/artifacts/workflow_refinement/{wr_id}/workflow_refinement_result.json
    → /app/artifacts/workflow_refinement/{wr_id}/llm_refinement_context.json
    → /app/artifacts/workflow_refinement/{wr_id}/llm_request.json
    → /app/artifacts/workflow_refinement/{wr_id}/llm_response.json
    → /app/artifacts/workflow_refinement/{wr_id}/revised_workflow_plan.json
    → /app/artifacts/workflow_refinement/{wr_id}/workflow_plan_delta.json
    → /app/artifacts/workflow_refinement/{wr_id}/iteration_rerun_plan.json
    → /app/artifacts/workflow_refinement/{wr_id}/final_pipeline_selection_input.json
    → /app/artifacts/workflow_refinement/{wr_id}/validation_result.json
    → /app/artifacts/workflow_refinement/{wr_id}/manifest.json
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
- 模块十一：[metric_evaluation/exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/exceptions.py) — 13 个专用异常（MetricEvaluationException / MetricEvaluationNotFound / PipelineExecutionRequired / PipelineExecutionNotReady / MetricEvaluationInputInvalid / PredictionArtifactLoad / MetricNotSupported / MetricCalculation / MetricAggregation / ModelRanking / BaselineComparison / ResultDiagnosisInputBuild / EvaluationArtifactSave）
- 模块十二：[result_diagnosis/exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/exceptions.py) — 10 个专用异常（ResultDiagnosisException / ResultDiagnosisNotFound / MetricEvaluationRequired / MetricEvaluationNotReady / DiagnosisInputInvalid / EvidenceExtraction / SystemDiagnosis / DiagnosticContextBuild / LLMDiagnosisCall / LLMDiagnosisParse / RefinementInputBuild / DiagnosisArtifact）
- 模块十三：[workflow_refinement/exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/exceptions.py) — 13 个专用异常（WorkflowRefinementException / WorkflowRefinementNotFound / ResultDiagnosisRequired / ResultDiagnosisNotReady / WorkflowRefinementInputInvalid / WorkflowRefinementContextBuild / LLMWorkflowRefinementCall / LLMWorkflowRefinementParse / LLMWorkflowRefinementValidation / RevisedWorkflowPlanValidation / IterationRerunPlanBuild / FinalSelectionInputBuild / WorkflowRefinementArtifactSave）

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
- 配置分组：数据库、LLM、数据上传、特征工程、特征预处理、模型搜索上下文、模型搜索计划、流水线生成、流水线执行、指标评估、结果诊断、工作流精炼

关键配置项：
- `DATABASE_URL` — PostgreSQL 连接字符串
- `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL` — LLM API 配置
- `UPLOAD_DIR` — 文件上传目录（默认 `/app/uploads`）
- `FEATURE_ARTIFACT_DIR` — 特征 artifact 目录（默认 `/app/artifacts/features`）
- `MODEL_READY_ARTIFACT_DIR` — 模型就绪 artifact 目录（默认 `/app/artifacts/model_ready`）
- `EVALUATION_ARTIFACT_DIR` — 评估 artifact 目录（默认 `/app/artifacts/evaluation`）
- `DIAGNOSIS_ARTIFACT_DIR` — 诊断 artifact 目录（默认 `/app/artifacts/diagnosis`）
- `WORKFLOW_REFINEMENT_ARTIFACT_DIR` — 工作流精炼 artifact 目录（默认 `/app/artifacts/workflow_refinement`）
- `LLM_MAX_TOKENS` — LLM 最大 Token 数（默认 4096）
- `LLM_TEMPERATURE` — LLM 温度（默认 0.3）
- `DEFAULT_LLM_PROFILE` — 默认 LLM 诊断上下文详细程度（默认 `standard`，可选 `compact`/`standard`/`full`）
- `WEAK_IMPROVEMENT_THRESHOLD` — 弱改善阈值（默认 0.05）
- `HIGH_CV_THRESHOLD` — 高变异系数阈值（默认 0.15）
- `SMALL_SAMPLE_THRESHOLD` — 小样本阈值（默认 200）
- `LOW_FEATURE_THRESHOLD` — 低特征数阈值（默认 10）

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
- 模块十二通过 `llm_result_diagnoser.py` 复用
- 模块十三通过 `llm_workflow_refiner.py` 复用

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

- **无全局路由**：前端只有一个页面 `TaskSpecificationPage`，13 个面板嵌入其中
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
| **Pipeline Generation** | ✅ 已实现 | 模块九已实现：12 步流水线，含 LLM Advisory Review（parse→validate→normalize），消费模块八的 pipeline_generation_input |
| **Pipeline Execution** | ✅ 已实现 | 模块十已实现：12 步流水线，Controlled Executor 训练链路，消费模块九的 execution_input，输出 training artifacts + metric_evaluation_input |
| **Metric Evaluation** | ✅ 已实现 | 模块十一已实现：13 步流水线，Fold→Trial→Pipeline 三级聚合，Metric Registry 白名单，Baseline Comparison + Model Ranking，消费模块十的 metric_evaluation_input |
| **Result Diagnosis** | ✅ 已实现 | 模块十二已实现：15 步流水线，LLM 诊断 + System Rule Fallback，消费模块十一的 result_diagnosis_input，输出 Closed-loop Refinement Input |
| **Workflow Refinement (Closed-loop)** | ✅ 已实现 | 模块十三已实现：14 步流水线，LLM 决策双路径 + Adopt & Rerun 闭环迭代，消费模块十二的 closed_loop_refinement_input。完全取代原独立 `closed_loop_refinement` 模块。 |
| **Final Pipeline Selection** | 未实现 | 需要选择最终 Pipeline（模块十三已输出 `final_pipeline_selection_input` 供其消费） |
| **Interpretability Analysis** | 未实现 | 需要对最终模型进行可解释性分析 |
| **Final Output** | 未实现 | 需要生成最终输出和报告 |

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
11. **残留目录**：`backend/app/modules/closed_loop_refinement/` 仅含 `__pycache__` 残留（`.pyc` 编译文件），所有源码文件已删除。该目录的功能已由 `workflow_refinement/` 模块完全取代。建议清理该目录以避免混淆。

### 8.4 后续开发优先级建议

1. **高优先级**：实现 Final Pipeline Selection（消费模块十三的 `final_pipeline_selection_input`）
2. **高优先级**：实现 Final Output 模块
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
8. **[model_search/service.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/service.py)** — 理解模块八（12 步流水线，代码模式最新）
9. **[model_search/search_space_builder.py](file:///c:/projects/MLAgent/backend/app/modules/model_search/search_space_builder.py)** — 理解 10 模型 × 2 任务类型的内置超参数模板
10. **[pipeline_generation/service.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_generation/service.py)** — 理解模块九（12 步流水线 + LLM Advisory Review parse→validate→normalize 链路）
11. **[pipeline_generation/llm_review_normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_generation/llm_review_normalizer.py)** — 理解 LLM 顾问式审查的标准化逻辑（旧式审批→标准 advisory 格式）
12. **[pipeline_generation/schemas.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_generation/schemas.py)** — 理解 LLMAdvisoryReview / PipelineSpec / TrialPlan / ExecutionInput 等核心数据结构
13. **[pipeline_execution/service.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/service.py)** — 理解模块十（12 步流水线 + Controlled Executor 训练链路）
14. **[pipeline_execution/controlled_executor.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/controlled_executor.py)** — 理解唯一训练入口的迭代逻辑（trial plans → pipeline_runs → trials → folds）
15. **[pipeline_execution/model_factory.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/model_factory.py)** — 理解 Model Registry ID → sklearn 类的显式映射（10 模型族 × 2 任务类型）
16. **[pipeline_execution/hpo_trial_generator.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/hpo_trial_generator.py)** — 理解上游 SearchSpaceItem 格式的解析和 HPO 参数生成
17. **[pipeline_execution/execution_input_loader.py](file:///c:/projects/MLAgent/backend/app/modules/pipeline_execution/execution_input_loader.py)** — 理解上游 execution_input_json 的加载和校验
18. **[metric_evaluation/service.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/service.py)** — 理解模块十一（13 步流水线 + Fold→Trial→Pipeline 三级聚合 + execution_json 数据补充模式）
19. **[metric_evaluation/prediction_artifact_loader.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/prediction_artifact_loader.py)** — 理解预测 parquet 加载和路径安全校验（跨平台兼容）
20. **[metric_evaluation/metric_registry.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/metric_registry.py)** — 理解 Metric Registry 白名单（5 回归 + 5 分类指标）
21. **[metric_evaluation/metric_calculator.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/metric_calculator.py)** — 理解纯 numpy 指标计算实现
22. **[metric_evaluation/baseline_comparator.py](file:///c:/projects/MLAgent/backend/app/modules/metric_evaluation/baseline_comparator.py)** — 理解 pipeline_role 筛选和基线比较逻辑
23. **[result_diagnosis/service.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/service.py)** — 理解模块十二（15 步流水线 + LLM 诊断 + System Rule Fallback + 15-step pipeline）
24. **[result_diagnosis/llm_diagnosis_validator.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/llm_diagnosis_validator.py)** — 理解 LLM 诊断三层校验（结构 + 枚举别名 + 安全扫描）
25. **[result_diagnosis/llm_diagnosis_normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/llm_diagnosis_normalizer.py)** — 理解 LLM 输出标准化（canonicalize + coerce + default fill）
26. **[result_diagnosis/system_diagnostic_checker.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/system_diagnostic_checker.py)** — 理解 9 项规则诊断（含可配置阈值）
27. **[result_diagnosis/evidence_extractor.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/evidence_extractor.py)** — 理解 6 类证据提取
28. **[result_diagnosis/refinement_input_builder.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/refinement_input_builder.py)** — 理解 ClosedLoopRefinementInput 构建（含 ready 标记）
29. **[result_diagnosis/enums.py](file:///c:/projects/MLAgent/backend/app/modules/result_diagnosis/enums.py)** — 理解 DIAGNOSIS_TYPE_ALIASES（25 条目）和 canonical_diagnosis_type() 函数
30. **[workflow_refinement/service.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/service.py)** — 理解模块十三（14 步流水线 + adopt_revised_plan + 幂等性检查）
31. **[workflow_refinement/experiment_history_collector.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/experiment_history_collector.py)** — 理解跨迭代历史收集（5 模块独立 try/except 模式）
32. **[workflow_refinement/workflow_refinement_normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/workflow_refinement_normalizer.py)** — 理解 LLM 决策标准化（模糊匹配 + null-consistency + 类型转换）
33. **[workflow_refinement/workflow_plan_delta_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_refinement/workflow_plan_delta_builder.py)** — 理解 WorkflowPlan diff 计算（7 section 逐字段比较）
34. **[workflow_planning/service.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/service.py)** — 理解 adopt_revised_plan() 方法（模块十三的持久化接收端）
35. **各模块的 `service.py`** — 理解每个模块的核心业务逻辑
36. **各模块的 `context_builder.py`** — 理解模块间依赖校验逻辑
37. **[taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts)** — 理解前端 API 配置

### 9.2 开发新模块时应遵循的模式

1. **模块结构模板**：每个模块应包含 `api.py`（路由）、`service.py`（业务逻辑）、`model.py`（数据模型）、`repository.py`（数据访问）、`schemas.py`（请求/响应 DTO）、`enums.py`（枚举）、`exceptions.py`（异常）、`builder.py`（构建响应）
2. **上游依赖校验**：新模块的 `context_builder.py` 必须校验所有上游模块的输出状态
3. **失败状态持久化**：失败时必须写入数据库（含 error_message）
4. **LLM 调用模式**：如需调用 LLM，参考模块二/四/七的 `prompt_builder → LLMClient → parser → validator` 模式；如需顾问式 LLM 审查（LLM 不能影响执行决策），参考模块九的 `prompt_builder → LLMClient → parser → validator → normalizer` 模式；如需 LLM 诊断 + Fallback（LLM 失败时降级到系统规则），参考模块十二的 `prompt_builder → LLMClient → parser → validator → normalizer → refinement_input` 链路 + `system_diagnostic_checker` fallback
5. **Artifact 管理**：如需文件持久化，参考模块五/六的 `artifact_manager.py`；如需管理训练 artifacts（模型/预测/日志/元数据），参考模块十的 `training_artifact_manager.py`
6. **Pipeline Template Registry 模式**：如需定义可执行模板（LLM 不参与生成），参考模块九的 `pipeline_template_registry.py` 和 `pipeline_spec_builder.py`
7. **非 LLM 执行模块模式**：如需实现纯系统执行模块（不调用 LLM），参考模块十的 12 步流水线模式（context → load_input → execute → collect → build → persist），以及 `controlled_executor → trial_runner → fold_runner` 三层训练链路
8. **多级聚合模块模式**：如需实现 Fold→Trial→Pipeline 等多级聚合计算链路，参考模块十一的 `fold_metric_evaluator → trial_metric_aggregator → pipeline_metric_aggregator` 三级聚合模式，每级有独立的 DTO 和聚合器文件
9. **轻量合同 + JSONB 补充模式**：若上游模块的合同数据不完整（如仅含轻量摘要），可参考模块十一从上游 `execution_json` JSONB 中按需补充元数据的模式（`spec_role_map` + `full_trial_map` 交叉引用）
10. **LLM 诊断 + Fallback 模式**：如需实现 LLM 诊断功能（LLM 调用可能失败），参考模块十二的 `prompt_builder → LLM → parser → validator → normalizer → refinement_input` 链路，以及 LLM 失败时的 `system_diagnostic_checker` fallback 策略（LLM 成功则 status=diagnosed，LLM 失败则 status=fallback_diagnosed 并附带 warnings）
11. **LLM 诊断三层安全防护模式**：如需对 LLM 输出进行安全校验，参考模块十二的 (1) Prompt 约束（4 条禁止 + JSON Schema）+ (2) Validator 校验（结构/枚举值/别名支持/evidence 非空）+ (3) Security Scan（14 种代码模式 + 9 个禁止字段）三层防护体系
12. **LLM 决策双路径模式**：如需 LLM 做出二元决策 + 每条路径有不同的数据结构要求，参考模块十三的 `workflow_refinement_validator` 的决策一致性校验（proceed_next_stage → revised_plan 必须 null + fpsi 必须非空；iterate_refinement → 反之）和 `workflow_refinement_normalizer` 的 null-consistency 强制设置
13. **跨模块历史收集模式**：如需从多个上游模块收集跨迭代历史数据，参考模块十三的 `experiment_history_collector` 的独立 try/except per module 模式，确保单模块失败不影响整体收集
14. **Adopt & Persist 模式**：如需将 LLM 修订/建议内容持久化为正式记录（而非仅 advisory），参考模块十三的 `adopt_revised_plan()` → `WorkflowPlanningService.adopt_revised_plan()` 的跨模块持久化链路
15. **前端闭环迭代模式**：如需前端实现多步骤顺序执行 + 实时进度日志，参考模块十三前端的 `handleAdoptAndRerun()` 的 `for...of` 顺序调用 + `setRerunProgress(prev => [...prev, msg])` 累加进度 + 每步独立 try/catch + 完成后的指引提示

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
10. **Model Search Plan** — 模块八已输出完整的模型搜索计划（含 pipeline_generation_input），下游模块应消费该计划而非重新规划
11. **Pipeline Generation** — 模块九已输出完整的 Pipeline Bundle + Execution Input（含 execution_input），下游 Pipeline Execution 应消费该合同而非重新构建
12. **Pipeline Execution** — 模块十已输出完整的训练结果 + Metric Evaluation Input（含 metric_evaluation_input），下游 Metric Evaluation 应消费该合同而非重新训练
13. **Model Factory** — 模块十的 `model_factory.py` 已实现 10 个模型族的 sklearn 显式映射和 task_type 兼容性校验，新模块应复用该工厂而非自行实例化模型
14. **HPO Trial Generator** — 模块十的 `hpo_trial_generator.py` 已实现上游 SearchSpaceItem 格式解析，新的 HPO 执行场景应复用该生成器
15. **LLM Advisory Review 标准化** — `llm_review_normalizer.py` 已实现完整的旧式→标准格式映射，新 LLM 审查功能应复用该标准化器
16. **Metric Registry** — 已在模块十一 `metric_registry.py` 中定义 5 个回归 + 5 个分类指标的完整注册表（含 direction 和 task_type 约束），新模块应查询该 Registry 而非硬编码指标
17. **Metric Calculator** — 模块十一的 `metric_calculator.py` 已实现纯 numpy 的指标计算（MAE/MSE/RMSE/R2/MAPE/Accuracy/Precision/Recall/F1），新模块应复用该计算器
18. **Prediction Artifact Loader** — 模块十一的 `prediction_artifact_loader.py` 已实现完整的预测 parquet 加载和校验链路（路径安全 + 必填列 + 数值校验 + NaN/Inf 检测），新的预测消费模块应复用该加载器
19. **Metric Evaluation Artifacts** — 模块十一已输出完整的评估结果（metric_results / fold_metrics / trial_metrics / pipeline_metrics / model_ranking / baseline_comparison / result_diagnosis_input），下游 Result Diagnosis 应消费这些 artifacts 而非重新计算指标
20. **Result Diagnosis Artifacts** — 模块十二已输出完整的诊断结果（diagnosis_result / evidence_summary / system_checks / closed_loop_refinement_input / llm_request / llm_response / manifest），下游 Closed-loop Refinement 应消费这些 artifacts 而非重新诊断
21. **LLM Diagnosis Validator + Normalizer** — 模块十二已实现完整的三层校验（结构 + 枚举别名 + 安全扫描）+ 标准化器（canonicalize + coerce + default fill），新的 LLM 诊断场景应复用此校验/标准化链路
22. **DIAGNOSIS_TYPE_ALIASES** — 模块十二已定义 26 个诊断类型别名映射，新的诊断类型需求应扩展此映射
23. **Workflow Refinement Decision** — 模块十三已实现完整的 LLM 决策双路径（proceed_next_stage / iterate_refinement）+ Adopt & Rerun 闭环迭代，新的闭环优化场景应复用此决策链路而非重新实现独立的 Closed-loop Refinement 模块
24. **Experiment History Collector** — 模块十三已实现从 5 个上游模块收集跨迭代历史，新的历史数据分析功能应复用或扩展此收集器
25. **Workflow Plan Delta** — 模块十三已实现原始 vs 修订 WorkflowPlan 的逐 section diff 计算，新的 Plan 比较场景应复用此 diff 构建器
26. **Revised Workflow Plan Validator** — 模块十三已实现修订版 WorkflowPlan 的结构校验（9 个 top-level + 子对象 + 枚举 + 范围），新的 Plan 校验场景应复用此校验器

### 9.4 关键边界和注意事项

1. **管道严格顺序**：模块一 → 二 → 三 → 四 → 五 → 六 → 七 → 八 → 九 → 十 → 十一 → 十二 → 十三，不可跳过或乱序。闭环迭代路径：十三（iterate_refinement）→ adopt → re-execute 四起 → 回到十二
2. **状态校验**：每个下游模块的 `context_builder.py` 会检查上游模块的状态值（如 `valid`, `interpreted`, `profiled`, `planned`, `completed`, `preprocessed`, `updated`, `planned`, `generated`, `completed`, `evaluated`, `diagnosed`, `decided`），状态不符则抛出专用异常
3. **JSONB 字段**：所有模块的核心数据存储在 JSONB 字段中（如 `task_spec_json`, `interpretation_json`, `plan_json`），读取时需注意可能为 `None`。序列化时使用 `model_dump(mode='json')` 而非普通的 `model_dump()`，否则 datetime 对象无法写入 PostgreSQL JSONB
4. **LLM 输出不可信**：所有 LLM 输出必须经过 `parser` + `validator` 两步处理；若 LLM 用于顾问式审查，还需经过 `normalizer` 标准化（剥离旧式审批字段、强制 non_blocking 执行影响）
5. **Featurizer 名称校验**：Workflow Planning 的 Validator 会校验 `executable_featurizers` 中的名称是否在 Registry 中存在，因此 LLM Prompt 必须包含当前 Registry 的 Featurizer 列表
6. **Artifact 路径**：Feature Engineering 和 Feature Preprocessing 的 artifact 存储在文件系统中，下游模块通过数据库中的 `artifact_path` 字段定位。模块十的 training artifacts 存储在 `/app/artifacts/training/{pe_id}/`，含 predictions/ 和 models/ 子目录
7. **前端超时配置**：Feature Engineering API 超时 600s，Feature Preprocessing API 超时 600s，Pipeline Execution API 超时 600s（含模型训练），Model Search Context API 超时 300s，Model Search Plan API 超时 300s，Metric Evaluation API 超时 300s，Result Diagnosis API 超时 300s，其他 API 超时 120s
8. **CORS 配置**：后端允许 `http://localhost:5173` 和 `http://localhost:3000` 的跨域请求，生产环境需调整
9. **数据库初始化**：开发环境使用 `docker-compose up` 启动，首次启动会自动建表。如需重置数据，删除 PostgreSQL 卷后重新启动
10. **测试账号**：admin/password（管理员），2024000001/password（学生），100001/password（教师）— 所有账号密码均为 `password`
11. **上游 split strategy 标准化**：上游模块（pipeline_generation/model_search/workflow_planning）使用 `k_fold_cross_validation` 作为标准名称，模块十的 `validation_splitter._normalize_strategy()` 会自动映射为内部 `k_fold`，新增下游模块时需注意此兼容逻辑
12. **SearchSpaceItem 格式**：上游搜索空间为 `{model_id, search_space_id, parameters: [{name, param_type, low, high, choices, sampling}]}` 格式，消费搜索空间的模块应参考 `hpo_trial_generator._extract_parameters()` 的解析逻辑
13. **轻量合同 + JSONB 补充**：模块十的 metric_evaluation_input_json 中 trial_results 仅为轻量摘要（6 个字段：trial_id, model_id, status, prediction_artifact_path, model_artifact_path, duration_seconds），完整元数据（pipeline_role, model_family, trial_type, params, pipeline_spec_id）需从 execution_json 的 pipeline_run_results 和 trial_results 中补充。下游模块消费上游轻量合同时，应检查是否需要从 JSONB 补充数据
14. **Metric Registry 白名单**：新增指标必须在 Metric Registry 中注册，含明确的 direction（minimize/maximize）和 allowed_task_types。Metric Calculator 仅计算 Registry 中已注册的指标
15. **预测 Artifact 路径格式**：prediction parquet 存储在 `/app/artifacts/training/{pe_id}/predictions/`，文件名格式为 `trial_{model_id}_{trial_id}_fold_{k}.parquet`。路径安全校验使用 `os.path.normpath` 实现跨平台兼容（Windows 反斜杠 vs Linux 正斜杠）
16. **Workflow Refinement 幂等性**：`create_workflow_refinement()` 在第一阶段执行幂等性检查——若同一 task+diagnosis 已存在 DECIDED/DECIDED_WITH_WARNING 记录，直接返回已有结果。使用 `force_rerun=True` 跳过此检查
17. **决策双路径 null-consistency**：Validator 和 Normalizer 都强制执行 decision 与对应输出结构的 null-consistency。proceed_next_stage → revised_workflow_plan=null + iteration_rerun_plan=null + final_selection_input≠null。iterate_refinement → 反之
18. **Adopt 前置条件**：`adopt_revised_plan()` 要求 decision 必须为 `iterate_refinement` 且 `revised_workflow_plan_json` 非空且通过 `validate_revised_workflow_plan()` 校验。adopt 后状态变为 ADOPTED，不可重复 adopt
19. **前端超时配置**：Workflow Refinement API 超时 600s（含 LLM 调用和跨模块数据收集），Adopt API 和 Rerun 也一样
20. **closed_loop_refinement 模块已废弃**：不要在该目录下开发新功能。该目录仅含 `__pycache__` 残留，所有源码已迁移至 `workflow_refinement/` 模块
21. **WorkflowPlan 的 planning_mode 枚举**：原始 LLM 规划的 Plan 为 `llm_guided`，模块十三采纳的修订版 Plan 为 `refinement_adopted`。下游模块可根据 planning_mode 区分 Plan 来源
22. **RERUN_STAGE_RECOMMENDATIONS 映射**：`enums.py` 中的 `RERUN_STAGE_RECOMMENDATIONS` 将诊断类型映射到建议的重跑入口阶段（如 underfitting→workflow_planning, feature_insufficiency→feature_engineering），LLM 建议的 rerun stage 需经过 fuzzy match normalization 后才能与枚举值比较

---

> **文档维护说明**：本文档应在每次重大功能更新后同步更新。更新时请保持章节结构不变，重点更新模块完成度、新增文件列表、数据流图和未完成部分。
