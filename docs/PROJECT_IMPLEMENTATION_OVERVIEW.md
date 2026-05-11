# 项目已实现部分说明文档

> 文档生成日期：2026-05-11（全面更新版 — 含 Final Pipeline Selection + Interpretability Analysis + Final Output 三个新模块）
> 项目名称：MLAgent — AI-driven Automated Machine Learning Framework for Materials Science
> 文档用途：帮助后续 AI Coding 大模型和开发者快速理解当前项目已经完成的部分

---

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个面向材料科学领域的 AI 驱动自动化机器学习框架。其核心目标是让用户通过结构化表单提交材料机器学习任务需求，系统自动完成从**任务理解 → 数据加载 → 工作流规划 → 特征工程 → 特征预处理 → 模型搜索上下文更新 → 模型搜索计划生成 → 可执行流水线生成 → 流水线执行与训练 → 指标评估 → LLM 结果诊断 → LLM 工作流精炼（含闭环迭代）→ 最终流水线选择 → 可解释性分析 → 最终报告输出**的全流程自动化。当前所有 16 个核心模块均已实现 MVP。

### 1.2 当前实现阶段

当前项目已完成 **十六个核心业务模块** 的端到端实现：

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
| **模块十三：LLM-driven Workflow Refinement（LLM 驱动的工作流精炼与闭环迭代）** | MVP 已完成 | ~90% |
| **模块十四：Final Pipeline Selection（最终流水线选择）** ★ 新增 | MVP 已完成 | ~85% |
| **模块十五：Interpretability Analysis（可解释性分析）** ★ 新增 | MVP 已完成 | ~80% |
| **模块十六：Final Output（最终输出与报告生成）** ★ 新增 | MVP 已完成 | ~85% |
| **Featurizer Registry / Model Registry / HPO Registry / Pipeline Template Registry / Metric Registry（共享能力注册表）** | MVP 已完成 | ~90% |

**注意**：`closed_loop_refinement/` 目录仅含残留的 `__pycache__` 文件（无源码），其功能已被模块十三（`workflow_refinement/`）完全取代。`workflow_refinement` 内置的 `adopt_revised_plan` + 前端 "Adopt & Rerun" 闭环迭代流程实现了原定 Closed-loop Refinement 的全部需求。

### 1.3 项目整体架构

```
用户浏览器 (React SPA — 单一 TaskSpecificationPage，含 16 个嵌入式面板)
    | HTTP (axios)
FastAPI 后端 (Python, port 8000)
    | SQLModel
PostgreSQL 数据库 (port 5432)
    |
    ├── 外部 LLM API (OpenAI 兼容接口 — 默认配置为智谱 GLM-5)
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
    ├── Model Search (LLM 模型搜索建议 → Registry 校验 → 候选模型/HPO/搜索空间 → Trial 分配)
    │       ↓
    │   Model Search Plan (供下游 Pipeline Generation 消费)
    │
    ├── Pipeline Generation (12 步流水线生成)
    │       ↓
    │   Pipeline Bundle + Execution Input (供下游 Pipeline Execution 消费)
    │
    ├── Pipeline Execution (12 步流水线执行)
    │       ↓
    │   Training Artifacts + Metric Evaluation Input (供下游 Metric Evaluation 消费)
    │
    ├── Metric Evaluation (13 步流水线评估)
    │       ↓
    │   Metric Results + Model Ranking + Baseline Comparison + Result Diagnosis Input
    │
    ├── Result Diagnosis (15 步流水线诊断)
    │       ↓
    │   Diagnosis Result + Closed-loop Refinement Input (供下游 Workflow Refinement 消费)
    │
    ├── Workflow Refinement (14 步流水线决策)
    │       ↓
    │   ├── Decision: PROCEED_NEXT_STAGE → Final Pipeline Selection Input
    │   └── Decision: ITERATE_REFINEMENT → Revised WorkflowPlan + Iteration Rerun Plan
    │           ↓ (通过 Adopt & Rerun 闭环)
    │       Re-execute pipeline stages from revised entry point → 回到 Result Diagnosis
    │
    ├── Final Pipeline Selection (候选收集 → 约束校验 → 评分 → 排名 → LLM 解释)
    │       ↓
    │   Selected Pipeline + Artifact Manifest + Interpretability Analysis Input
    │
    ├── Interpretability Analysis (系数分析 / 排列重要度 / SHAP → LLM 材料学洞察总结)
    │       ↓
    │   Feature Importance + Material Insight + Final Output Input
    │
    └── Final Output (工作流追踪 → 可重复性摘要 → LLM 报告撰写 → JSON/Markdown 渲染 → 下载包)
            ↓
        Final Report + Download Links + Output Package Manifest
```

### 1.4 核心设计原则（根据当前代码分析）

1. **管道式架构**：十六个模块严格按序依赖。每个下游模块的 `context_builder.py` 会校验所有上游模块的输出状态，状态不符则抛出专用异常。
2. **统一异常体系**：所有业务异常继承自 `BusinessException`（定义于 `backend/app/shared/common/exceptions.py`），每个模块有自己的异常子类，附带有语义化的 `error_code`。
3. **LLM 输出强约束**：模块二、四、七、八、九、十二、十三、十四、十五、十六均定义了严格的 JSON Schema，LLM 响应经过 `parser.py` → `validator.py` → `normalizer.py` 三步才被认为有效。模块十和十一为纯系统执行模块，不调用 LLM。
4. **Featurizer Registry 作为共享契约**：Workflow Planning 的 Prompt 和 Validator、Feature Engineering 的 Strategy Resolver 都向 Registry 查询，而非各自维护硬编码列表。
5. **失败状态持久化**：所有模块在失败时都会将失败记录（含错误信息）写入数据库，不会静默丢失。
6. **Artifact 传递链**：Feature Engineering 输出特征矩阵 → Feature Preprocessing 输出 model-ready 矩阵 + preprocessor pipeline → Model Search Context 输出更新策略 → Model Search 输出搜索计划 → Pipeline Generation 输出 execution input → Pipeline Execution 输出训练结果 → Metric Evaluation 输出指标 → Result Diagnosis 输出诊断 → Workflow Refinement 输出决策 → Final Pipeline Selection 输出选定流水线 → Interpretability Analysis 输出可解释性结果 → Final Output 输出最终报告。
7. **多 Registry 共享架构**：Featurizer Registry（`backend/app/shared/registry/featurizer_registry.py`，11 个 featurizer 定义）、Model Registry（`backend/app/shared/registry/model_registry.py`，10 个模型族定义）和 HPO Registry（`backend/app/shared/registry/hpo_registry.py`，5 个 HPO 方法定义）。所有 LLM 推荐的模型和 HPO 方法必须经 Registry 校验。
8. **LLM 建议 + 系统生成分离**：模块八中 LLM 仅输出结构化建议，最终候选模型、HPO 方法、搜索空间必须由系统基于 Registry、模板和校验器生成。
9. **LLM Advisory Review（顾问式审查）**：模块九的 LLM 审查定位于"顾问"而非"审批者"。`ready_for_execution` 标记由 System Validator + Safety Checker + Artifact Manifest 三者共同决定。
10. **多级安全防护**：模块九 Safety Checker 扫描 15+ 种危险模式，LLM Review Validator 额外扫描 25+ 种禁止内容模式。
11. **Controlled Executor 作为唯一训练入口**：模块十中所有模型训练必须通过 Controlled Executor 执行，使用 Model Registry 中注册的模型，禁止 LLM 生成训练代码。
12. **LLM 诊断只建议不执行**：模块十二的 LLM 只能输出结构化 JSON 诊断与建议，Validator 扫描 14 种危险代码模式。
13. **LLM 决策双路径**：模块十三的 LLM 输出两种决策路径：`proceed_next_stage` 或 `iterate_refinement`。
14. **Adopt & Rerun 闭环迭代**：模块十三的 `adopt_revised_plan` 端点将 LLM 修订的 WorkflowPlan 持久化为新 Plan，前端按 `iteration_rerun_plan.rerun_stages` 顺序重新执行。
15. **LLM 解释器可降级**：模块十四、十五、十六的 LLM 调用均为非阻塞：LLM 失败时降级到系统 rule-based fallback，不影响主流程。

---

## 2. 当前目录结构说明

### 2.1 完整目录树（实际文件）

```
C:\projects\MLAgent/
├── .gitignore
├── docker-compose.yml                      # 三服务编排（db + backend + frontend）
├── docs/
│   ├── PROJECT_IMPLEMENTATION_OVERVIEW.md  # 本文档
│   ├── prd-1-mvp.md                        # PRD 系列文档
│   ├── prd-1-技术栈.md
│   ├── prd-1-架构.md
│   ├── prd-2.md / prd-2-技术实现方案.md
│   ├── prd-3.md / prd-3-技术实现方案.md
│   ├── prd-4.md / prd-4-技术实现方案.md
│   ├── prd-5.md / prd-5-FeaturizerRegistry.md / prd-5-扩展.md
│   ├── prd-6.md / prd-6-技术实现方案.md
│   ├── prd-7.md / prd-7-技术实现方案.md
│   ├── prd-8.md
│   ├── prd-9.md / prd-9-LLM_Advisory_Review.md
│   ├── prd-10.md ~ prd-16.md              # PRD 10-16
│   └── prd-5-技术实现方案.md / prd-5-扩展技术实现方案.md
│
├── backend/                                # FastAPI 后端
│   ├── Dockerfile                          # Python 3.12-slim 基础镜像
│   ├── requirements.txt                    # Python 依赖
│   ├── .env                                # 环境变量（LLM 配置等）
│   ├── .env.example                        # 示例环境变量
│   └── app/
│       ├── __init__.py
│       ├── main.py                         # FastAPI 入口（路由注册 / CORS / 异常处理 / 启动建表 / 健康检查）
│       │
│       ├── modules/                        # 16 个业务模块
│       │   ├── __init__.py
│       │   │
│       │   ├── task_specification/         # 模块一：任务规格
│       │   │   ├── api.py                  # 4 个接口（POST / GET / PUT / POST:validate）
│       │   │   ├── schemas.py              # Create/Update/Response/ValidationResult
│       │   │   ├── service.py              # 业务编排：create → normalize → validate → build → persist
│       │   │   ├── model.py                # TaskSpecification (SQLModel, table=True, JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── normalizer.py           # 字段标准化映射
│       │   │   ├── validator.py            # 必填字段校验 / 指标兼容性 / 警告生成
│       │   │   └── builder.py              # 构建 task_spec JSON dict
│       │   │
│       │   ├── task_interpretation/        # 模块二：LLM 任务理解
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # 10+ 个子对象（InterpretedPredictionTarget 等）
│       │   │   ├── service.py              # adapt → build_prompt → LLM → parse → validate → build → persist
│       │   │   ├── model.py                # TaskInterpretation (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── task_spec_adapter.py    # TaskSpecification DB model → LLM context dict
│       │   │   ├── prompt_builder.py       # system/user prompt（含严格 JSON Schema）
│       │   │   ├── llm_client.py           # httpx 调用 OpenAI 兼容 API（含重试逻辑）
│       │   │   ├── parser.py               # JSON 提取（正则去除 markdown 代码块）
│       │   │   ├── validator.py            # 结构/枚举值/置信度校验
│       │   │   ├── builder.py              # 构建 interpretation JSON dict
│       │   │   ├── enums.py                # InterpretationStatus 等枚举
│       │   │   └── exceptions.py           # 5 个专用异常
│       │   │
│       │   ├── dataset_profile/            # 模块三：数据集加载与画像
│       │   │   ├── api.py                  # 6 个接口（upload / profile / get / preview 等）
│       │   │   ├── schemas.py              # ColumnInfo / DatasetSource / Schema 等
│       │   │   ├── service.py              # build_context → resolve_source → load → check → build → persist
│       │   │   ├── model.py                # DatasetProfile (JSONB + profile_json + preview_json)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨库构建 context
│       │   │   ├── source_resolver.py      # 数据源识别（含启发式规则）
│       │   │   ├── profiler.py             # 质量评级 / 样本量等级 / 推荐下一步
│       │   │   ├── builder.py              # 构建 Dataset Profile JSON dict
│       │   │   ├── enums.py                # DatasetProfileStatus 等
│       │   │   ├── exceptions.py           # 专用异常
│       │   │   ├── loaders/                # 数据加载器（策略模式）
│       │   │   │   ├── base_loader.py      # 抽象基类 BaseLoader
│       │   │   │   ├── matbench_loader.py  # Matbench 加载（含 fallback 样本数据）
│       │   │   │   └── file_loader.py      # 用户上传文件加载（CSV/XLSX/XLS）
│       │   │   └── checkers/               # 数据检查器
│       │   │       ├── schema_checker.py   # 列名检查 / 大小写匹配 / 全空列检测
│       │   │       ├── modality_checker.py # 输入模态检测与一致性校验
│       │   │       ├── quality_checker.py  # 缺失值 / 重复行 / 无效值 / 常量列
│       │   │       └── target_checker.py   # 回归/分类目标分布分析
│       │   │
│       │   ├── workflow_planning/          # 模块四：LLM 工作流规划
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # 15+ 个子对象
│       │   │   ├── service.py              # build_context → build_prompt → LLM → parse → validate → build → persist
│       │   │   ├── model.py                # WorkflowPlan (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨 4 个上游模块构建 context
│       │   │   ├── prompt_builder.py       # 超长 system prompt（10 条 CRITICAL 规则）
│       │   │   ├── llm_client_adapter.py   # 复用模块二的 LLMClient
│       │   │   ├── parser.py               # LLM 响应 JSON 提取
│       │   │   ├── validator.py            # 250 行严格校验（含 Featurizer Registry 校验）
│       │   │   ├── builder.py              # 构建 Workflow Plan JSON dict
│       │   │   ├── enums.py                # WorkflowPlanStatus 等枚举
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── feature_engineering/        # 模块五：特征工程
│       │   │   ├── api.py                  # 5 个接口（含 registry API 路由在 registry_api.py）
│       │   │   ├── registry_api.py         # Featurizer Registry 查询接口（3 个端点）
│       │   │   ├── schemas.py              # FeatureEngineeringCreateRequest/Response 等
│       │   │   ├── service.py              # build_context → resolve_strategies → featurize → build → persist
│       │   │   ├── model.py                # FeatureEngineering (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── strategy_resolver.py    # 解析 WorkflowPlan 中的特征策略
│       │   │   ├── data_loader_adapter.py  # 从 DatasetProfile 加载原始数据
│       │   │   ├── feature_matrix_builder.py # 构建特征矩阵
│       │   │   ├── artifact_manager.py     # 特征矩阵 artifact 存储（parquet/csv）
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # FeatureEngineeringStatus 等
│       │   │   ├── exceptions.py           # 专用异常
│       │   │   ├── checkers/
│       │   │   │   └── feature_quality_checker.py  # 特征质量检查
│       │   │   └── featurizers/            # 特征提取器（策略模式）
│       │   │       ├── base_featurizer.py              # 抽象基类
│       │   │       ├── featurizer_router.py            # 按策略路由到具体 Featurizer
│       │   │       ├── composition_featurizer.py       # 组合物成分特征
│       │   │       ├── descriptor_cleaner.py           # 描述符清洗器
│       │   │       ├── descriptor_featurizer.py        # 描述符直通
│       │   │       ├── pymatgen_composition_parser.py  # pymatgen 成分解析
│       │   │       ├── structure_featurizer.py         # 结构特征（占位）
│       │   │       ├── matminer_featurizers.py         # matminer 组合特征
│       │   │       └── matminer_structure_basic.py     # matminer 结构特征（占位）
│       │   │
│       │   ├── feature_preprocessing/      # 模块六：特征预处理
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # Create/Response 等
│       │   │   ├── service.py              # build_context → load → validate → build_pipeline → execute → build → persist
│       │   │   ├── model.py                # FeaturePreprocessing (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── artifact_loader.py      # 加载上游特征 artifact
│       │   │   ├── column_validator.py     # 列校验
│       │   │   ├── feature_group_validator.py # 特征组校验
│       │   │   ├── feature_filter.py       # 特征过滤器
│       │   │   ├── preprocessing_pipeline_builder.py # 构建 sklearn pipeline
│       │   │   ├── preprocessing_executor.py  # 执行预处理 pipeline
│       │   │   ├── artifact_manager.py     # model-ready artifact 存储
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # 枚举
│       │   │   ├── exceptions.py           # 专用异常
│       │   │   └── preprocessors/          # 预处理器组件
│       │   │       ├── imputer.py          # 缺失值插补（median/mean/mode）
│       │   │       ├── scaler.py           # 标准化（standard/minmax/robust）
│       │   │       ├── encoder.py          # 分类变量编码
│       │   │       └── feature_selector.py # 特征选择（variance_threshold 等）
│       │   │
│       │   ├── model_search_context/       # 模块七：模型搜索上下文
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # ModelSearchContextResponse 等
│       │   │   ├── service.py              # build_context → analyze → LLM → merge → build → persist
│       │   │   ├── model.py                # ModelSearchContext (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── dataset_profile_analyzer.py    # 数据集分析
│       │   │   ├── feature_group_analyzer.py      # 特征组分析
│       │   │   ├── preprocessing_analyzer.py      # 预处理分析
│       │   │   ├── model_strategy_adjuster.py     # 模型策略调整
│       │   │   ├── hpo_strategy_adjuster.py       # HPO 策略调整
│       │   │   ├── evaluation_strategy_adjuster.py # 评估策略调整
│       │   │   ├── validation_strategy_adjuster.py # 验证策略调整
│       │   │   ├── strategy_merger.py             # 策略合并
│       │   │   ├── llm_strategy_advisor.py        # LLM 策略建议
│       │   │   ├── llm_context_builder.py         # LLM 上下文构建
│       │   │   ├── llm_response_parser.py         # LLM 响应解析
│       │   │   ├── llm_advice_validator.py        # LLM 建议校验
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # 枚举
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── model_search/               # 模块八：自动化模型与 HPO 搜索
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # ModelSearchPlanResponse 等
│       │   │   ├── service.py              # build_context → LLM → validate → select → build → persist
│       │   │   ├── model.py                # ModelSearchPlan (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── llm_prompt_builder.py   # LLM prompt 构建
│       │   │   ├── llm_model_search_advisor.py # LLM 模型搜索建议
│       │   │   ├── llm_response_parser.py  # LLM 响应解析
│       │   │   ├── llm_advice_validator.py # LLM 建议校验（含 Registry 校验）
│       │   │   ├── candidate_model_selector.py # 候选模型选择
│       │   │   ├── search_space_builder.py # 搜索空间构建
│       │   │   ├── hpo_plan_builder.py     # HPO 计划构建
│       │   │   ├── evaluation_plan_builder.py # 评估计划构建
│       │   │   ├── validation_plan_builder.py # 验证计划构建
│       │   │   ├── trial_allocator.py      # Trial 分配
│       │   │   ├── pipeline_input_builder.py # Pipeline Generation 输入构建
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # 枚举
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── pipeline_generation/        # 模块九：可执行流水线生成
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # PipelineGenerationResponse 等
│       │   │   ├── service.py              # 12 步流水线生成
│       │   │   ├── model.py                # PipelineGeneration (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── artifact_resolver.py    # 上游 artifact 解析
│       │   │   ├── component_registry.py   # 组件注册表
│       │   │   ├── component_binder.py     # 组件绑定
│       │   │   ├── pipeline_spec_builder.py # Pipeline spec 构建
│       │   │   ├── pipeline_template_registry.py # Pipeline 模板注册表
│       │   │   ├── trial_plan_builder.py   # Trial 计划构建
│       │   │   ├── pipeline_validator.py   # Pipeline 校验
│       │   │   ├── safety_checker.py       # 安全扫描（15+ 种危险模式）
│       │   │   ├── execution_input_builder.py # 执行输入构建
│       │   │   ├── llm_pipeline_reviewer.py   # LLM 流水线审查
│       │   │   ├── llm_review_prompt_builder.py # LLM 审查 prompt
│       │   │   ├── llm_review_parser.py     # LLM 审查响应解析
│       │   │   ├── llm_review_validator.py  # LLM 审查校验（25+ 种禁止模式）
│       │   │   ├── llm_review_normalizer.py  # LLM 审查标准化
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # 枚举
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── pipeline_execution/         # 模块十：流水线执行与训练
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # PipelineExecutionResponse 等
│       │   │   ├── service.py              # 12 步流水线执行
│       │   │   ├── model.py                # PipelineExecution (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── execution_input_loader.py # 加载执行输入
│       │   │   ├── data_matrix_loader.py   # 加载数据矩阵
│       │   │   ├── execution_planner.py    # 执行计划
│       │   │   ├── execution_state_tracker.py # 执行状态追踪
│       │   │   ├── controlled_executor.py  # 受控执行器（唯一训练入口）
│       │   │   ├── model_factory.py        # 模型工厂（显式映射实例化）
│       │   │   ├── validation_splitter.py  # 验证集划分
│       │   │   ├── hpo_trial_generator.py  # HPO Trial 生成
│       │   │   ├── trial_runner.py         # Trial 运行器
│       │   │   ├── fold_runner.py          # Fold 运行器
│       │   │   ├── prediction_writer.py    # 预测结果写入
│       │   │   ├── metric_input_builder.py # Metric Evaluation 输入构建
│       │   │   ├── training_artifact_manager.py # 训练 artifact 管理
│       │   │   ├── runtime_monitor.py      # 运行时监控
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # 枚举
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── metric_evaluation/          # 模块十一：指标评估
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # MetricEvaluationResponse 等
│       │   │   ├── service.py              # 13 步流水线评估
│       │   │   ├── model.py                # MetricEvaluation (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── metric_input_loader.py  # 加载指标评估输入
│       │   │   ├── prediction_artifact_loader.py # 加载预测 artifact
│       │   │   ├── metric_registry.py      # 指标注册表
│       │   │   ├── metric_calculator.py    # 指标计算器
│       │   │   ├── metric_validator.py     # 指标校验器
│       │   │   ├── fold_metric_evaluator.py # Fold 级评估
│       │   │   ├── trial_metric_aggregator.py # Trial 级聚合
│       │   │   ├── pipeline_metric_aggregator.py # Pipeline 级聚合
│       │   │   ├── model_ranker.py         # 模型排名
│       │   │   ├── baseline_comparator.py  # 基线比较
│       │   │   ├── evaluation_artifact_manager.py # 评估 artifact 管理
│       │   │   ├── result_diagnosis_input_builder.py # Result Diagnosis 输入构建
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # 枚举
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── result_diagnosis/           # 模块十二：LLM 结果诊断
│       │   │   ├── api.py                  # 4 个接口
│       │   │   ├── schemas.py              # ResultDiagnosisResponse 等
│       │   │   ├── service.py              # 15 步流水线诊断
│       │   │   ├── model.py                # ResultDiagnosis (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── diagnosis_input_loader.py # 加载诊断输入
│       │   │   ├── evidence_extractor.py   # 证据提取
│       │   │   ├── diagnostic_context_builder.py # 诊断上下文构建
│       │   │   ├── system_diagnostic_checker.py  # 系统规则诊断
│       │   │   ├── llm_prompt_builder.py   # LLM prompt 构建
│       │   │   ├── llm_result_diagnoser.py # LLM 诊断调用
│       │   │   ├── llm_response_parser.py  # LLM 响应解析
│       │   │   ├── llm_diagnosis_validator.py # LLM 诊断校验（14 种危险模式）
│       │   │   ├── llm_diagnosis_normalizer.py # LLM 诊断标准化（26 条类型别名映射）
│       │   │   ├── refinement_input_builder.py  # Workflow Refinement 输入构建
│       │   │   ├── diagnosis_artifact_manager.py # 诊断 artifact 管理
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # 枚举（含 DIAGNOSIS_TYPE_ALIASES 26 条映射）
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── workflow_refinement/        # 模块十三：LLM 工作流精炼
│       │   │   ├── api.py                  # 7 个接口（含 adopt_revised_plan + 5 个 GET 子资源）
│       │   │   ├── schemas.py              # WorkflowRefinementResponse 等
│       │   │   ├── service.py              # 14 步流水线 + adopt_revised_plan
│       │   │   ├── model.py                # WorkflowRefinement (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── refinement_input_loader.py    # 加载 closed_loop_refinement_input
│       │   │   ├── experiment_history_collector.py # 跨 5 个上游模块收集实验历史
│       │   │   ├── workflow_refinement_context_builder.py # LLM 上下文构建
│       │   │   ├── llm_prompt_builder.py   # LLM prompt 构建
│       │   │   ├── llm_workflow_refiner.py # LLM 工作流精炼调用
│       │   │   ├── llm_response_parser.py  # LLM 响应解析
│       │   │   ├── workflow_refinement_validator.py  # 决策校验 + 安全扫描
│       │   │   ├── workflow_refinement_normalizer.py # 标准化
│       │   │   ├── revised_workflow_plan_validator.py # 修订版 WorkflowPlan 校验
│       │   │   ├── workflow_plan_delta_builder.py     # Workflow Plan Delta 计算
│       │   │   ├── iteration_rerun_plan_builder.py    # 迭代重跑计划构建
│       │   │   ├── final_selection_input_builder.py   # Final Pipeline Selection 输入构建
│       │   │   ├── refinement_artifact_manager.py     # Artifact 管理
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # WorkflowRefinementStatus / Decision 枚举
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── final_pipeline_selection/   # 模块十四：最终流水线选择 ★
│       │   │   ├── api.py                  # 7 个接口
│       │   │   ├── schemas.py              # FinalPipelineSelectionResponse 等
│       │   │   ├── service.py              # 多步骤选择流程
│       │   │   ├── model.py                # FinalPipelineSelection (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── selection_input_loader.py     # 加载选择输入
│       │   │   ├── candidate_collector.py        # 候选实验收集
│       │   │   ├── candidate_validator.py        # 候选校验（模型/预测 artifact 要求）
│       │   │   ├── selection_policy_builder.py   # 选择策略构建
│       │   │   ├── constraint_checker.py         # 约束检查
│       │   │   ├── candidate_scorer.py           # 候选评分
│       │   │   ├── final_ranker.py               # 最终排名与选择
│       │   │   ├── artifact_resolver.py          # artifact 解析
│       │   │   ├── selection_reason_builder.py   # 系统选择理由构建
│       │   │   ├── llm_selection_prompt_builder.py # LLM 解释 prompt
│       │   │   ├── llm_selection_explainer.py    # LLM 选择解释
│       │   │   ├── llm_selection_explanation_parser.py    # LLM 解释解析
│       │   │   ├── llm_selection_explanation_validator.py  # LLM 解释校验
│       │   │   ├── llm_selection_explanation_normalizer.py # LLM 解释标准化
│       │   │   ├── interpretability_input_builder.py # Interpretability Analysis 输入构建
│       │   │   ├── final_selection_artifact_manager.py    # Artifact 管理
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # FinalPipelineSelectionStatus / CandidateStatus
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── interpretability_analysis/  # 模块十五：可解释性分析 ★
│       │   │   ├── api.py                  # 7 个接口
│       │   │   ├── schemas.py              # InterpretabilityAnalysisResponse 等
│       │   │   ├── service.py              # 多步骤分析流程
│       │   │   ├── model.py                # InterpretabilityAnalysis (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── interpretability_input_loader.py   # 加载分析输入
│       │   │   ├── model_artifact_loader.py           # 模型 artifact 加载
│       │   │   ├── feature_matrix_loader.py           # 特征矩阵加载
│       │   │   ├── prediction_artifact_loader.py      # 预测 artifact 加载
│       │   │   ├── interpretability_method_selector.py # 可解释性方法选择
│       │   │   ├── coefficient_importance_analyzer.py  # 系数重要度分析
│       │   │   ├── native_importance_analyzer.py       # 原生重要度分析
│       │   │   ├── permutation_importance_analyzer.py  # 排列重要度分析（含 fallback）
│       │   │   ├── shap_analyzer.py                    # SHAP 分析
│       │   │   ├── local_explanation_builder.py        # 局部解释构建
│       │   │   ├── high_error_sample_analyzer.py       # 高误差样本分析
│       │   │   ├── feature_group_analyzer.py           # 特征组分析
│       │   │   ├── llm_interpretability_prompt_builder.py # LLM 解释 prompt
│       │   │   ├── llm_interpretability_summarizer.py  # LLM 解释总结
│       │   │   ├── llm_interpretability_parser.py      # LLM 解释解析
│       │   │   ├── llm_interpretability_validator.py   # LLM 解释校验
│       │   │   ├── llm_interpretability_normalizer.py  # LLM 解释标准化
│       │   │   ├── final_output_input_builder.py       # Final Output 输入构建
│       │   │   ├── interpretability_artifact_manager.py # Artifact 管理
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # InterpretabilityAnalysisStatus / MethodStatus
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   ├── final_output/               # 模块十六：最终输出与报告 ★
│       │   │   ├── api.py                  # 7 个接口
│       │   │   ├── schemas.py              # FinalOutputResponse 等
│       │   │   ├── service.py              # 21 步最终输出流程
│       │   │   ├── model.py                # FinalOutput (JSONB)
│       │   │   ├── repository.py           # CRUD
│       │   │   ├── context_builder.py      # 跨模块构建 context
│       │   │   ├── final_output_input_loader.py       # 加载最终输出输入
│       │   │   ├── workflow_trace_collector.py        # 工作流追踪收集
│       │   │   ├── final_artifact_resolver.py         # 最终 artifact 解析
│       │   │   ├── reproducibility_summary_builder.py # 可重复性摘要构建
│       │   │   ├── final_summary_builder.py           # 系统事实摘要构建
│       │   │   ├── llm_report_prompt_builder.py       # LLM 报告 prompt
│       │   │   ├── llm_report_writer.py               # LLM 报告撰写
│       │   │   ├── llm_report_parser.py               # LLM 报告解析
│       │   │   ├── llm_report_validator.py            # LLM 报告校验
│       │   │   ├── llm_report_normalizer.py           # LLM 报告标准化
│       │   │   ├── report_renderer.py                 # 报告渲染（JSON/Markdown + fallback）
│       │   │   ├── output_package_builder.py          # 输出包构建
│       │   │   ├── final_output_artifact_manager.py   # Artifact 管理
│       │   │   ├── builder.py              # 构建响应
│       │   │   ├── enums.py                # FinalOutputStatus
│       │   │   └── exceptions.py           # 专用异常
│       │   │
│       │   └── closed_loop_refinement/     # [已废弃] 仅含 __pycache__ 残留，无源码
│       │
│       └── shared/                         # 共享基础设施
│           ├── __init__.py
│           ├── common/
│           │   ├── __init__.py
│           │   ├── enums.py                # TaskStatus / TaskType / InputType / EvaluationMetric / UserPriority
│           │   ├── exceptions.py           # BusinessException + Validation/NotFound/Database 子类
│           │   └── response.py             # APIResponse / success_response() / error_response()
│           ├── config/
│           │   ├── __init__.py
│           │   └── settings.py             # pydantic_settings BaseSettings — 60+ 配置项
│           ├── database/
│           │   ├── __init__.py
│           │   ├── connection.py           # SQLModel engine 创建
│           │   └── session.py              # get_session() generator
│           └── registry/
│               ├── __init__.py
│               ├── schemas.py              # FeaturizerSpec / FeaturizerResolveResult 等
│               ├── exceptions.py           # Registry 专用异常
│               ├── featurizer_registry.py  # 11 个 Featurizer 定义 + 依赖检测 + 查询 API
│               ├── model_registry.py       # 10 个 Model Family 定义
│               └── hpo_registry.py         # 5 个 HPO Method 定义
│
└── frontend/                               # React 前端
    ├── Dockerfile                          # Node 20-alpine 基础镜像
    ├── package.json                        # React 18 + Ant Design 5 + axios + react-hook-form + zod
    ├── tsconfig.json
    ├── public/
    │   └── index.html
    ├── build/                              # 生产构建产物
    │   ├── asset-manifest.json
    │   ├── index.html
    │   └── static/js/main.d319c015.js
    └── src/
        ├── index.tsx                       # React 入口（渲染 TaskSpecificationPage）
        ├── api/                            # 16 个 API 模块（每个后端模块对应一个）
        │   ├── taskApi.ts                  # axios 实例 + Task CRUD 接口
        │   ├── taskInterpretationApi.ts
        │   ├── datasetProfileApi.ts
        │   ├── workflowPlanningApi.ts
        │   ├── featureEngineeringApi.ts
        │   ├── featurePreprocessingApi.ts
        │   ├── modelSearchContextApi.ts
        │   ├── modelSearchApi.ts
        │   ├── pipelineGenerationApi.ts
        │   ├── pipelineExecutionApi.ts
        │   ├── metricEvaluationApi.ts
        │   ├── resultDiagnosisApi.ts
        │   ├── workflowRefinementApi.ts
        │   ├── finalPipelineSelectionApi.ts
        │   ├── interpretabilityAnalysisApi.ts
        │   └── finalOutputApi.ts
        └── modules/                        # 16 个前端模块（每个后端模块对应一个）
            ├── taskSpecification/          # 表单 + 16 个嵌入式面板
            │   ├── pages/TaskSpecificationPage.tsx
            │   ├── components/TaskSpecificationForm.tsx  # 主表单（嵌入所有 16 个面板）
            │   ├── components/TaskFieldGroup.tsx
            │   └── constants.ts            # Zod schema + 选项列表
            ├── taskInterpretation/
            │   ├── components/TaskInterpretationPanel.tsx
            │   └── types.ts
            ├── datasetProfile/
            │   ├── components/DatasetProfilePanel.tsx
            │   ├── components/FileUpload.tsx
            │   └── types.ts
            ├── workflowPlanning/
            │   ├── components/WorkflowPlanPanel.tsx
            │   └── types.ts
            ├── featureEngineering/
            │   ├── components/FeatureEngineeringPanel.tsx
            │   └── types.ts
            ├── featurePreprocessing/
            │   ├── components/FeaturePreprocessingPanel.tsx
            │   ├── components/ColumnFilteringCard.tsx
            │   ├── components/ModelReadyArtifactCard.tsx
            │   ├── components/PreprocessingExecutionCard.tsx
            │   ├── components/ValidationSummaryCard.tsx
            │   ├── types.ts
            │   └── constants.ts
            ├── modelSearchContext/
            │   ├── components/ModelSearchContextPanel.tsx  # 含 7 个子卡片
            │   ├── types.ts
            │   └── constants.ts
            ├── modelSearch/
            │   ├── components/ModelSearchPlanPanel.tsx
            │   ├── types.ts
            │   └── constants.ts
            ├── pipelineGeneration/
            │   ├── components/PipelineGenerationPanel.tsx
            │   ├── types.ts
            │   └── constants.ts
            ├── pipelineExecution/
            │   ├── components/PipelineExecutionPanel.tsx
            │   ├── types.ts
            │   └── constants.ts
            ├── metricEvaluation/
            │   ├── components/MetricEvaluationPanel.tsx
            │   ├── types.ts
            │   └── constants.ts
            ├── resultDiagnosis/
            │   ├── components/ResultDiagnosisPanel.tsx
            │   ├── types.ts
            │   └── constants.ts
            ├── workflowRefinement/
            │   ├── components/WorkflowRefinementPanel.tsx  # 含 Adopt & Rerun 逻辑
            │   ├── types.ts
            │   └── constants.ts
            ├── finalPipelineSelection/
            │   ├── components/FinalPipelineSelectionPanel.tsx
            │   ├── types.ts
            │   └── constants.ts
            ├── interpretabilityAnalysis/
            │   ├── components/InterpretabilityAnalysisPanel.tsx
            │   ├── types.ts
            │   └── constants.ts
            └── finalOutput/
                ├── components/FinalOutputPanel.tsx
                ├── types.ts
                └── constants.ts
```

---

## 3. 当前系统输入与输出

### 3.1 用户输入

用户通过 React 前端表单（`frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx`）提交以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_name` | string | 任务名称（可选） |
| `task_description` | string | 自然语言任务描述 |
| `material_system` | string | 材料体系 |
| `prediction_target` | string | 预测目标属性 |
| `task_type` | enum | regression / classification |
| `dataset_description` | string | 数据集描述 |
| `input_type` | enum | composition / structure / descriptor_table |
| `target_column` | string | 目标列名 |
| `evaluation_metric` | enum | MAE / RMSE / R2 / Accuracy / F1 等 |
| `user_priority` | string[] | accuracy / interpretability / speed / robustness |
| `constraints` | string[] | 用户约束（自然语言列表） |
| `上传文件` | file | CSV / XLSX / XLS（可选，通过 DatasetProfilePanel 的 FileUpload 组件） |
| `dataset_reference` | string | Matbench 数据集引用（可选） |

### 3.2 系统处理

系统按照 16 个模块的管道顺序逐步处理，每个模块的输入是上游模块的输出（详见第 6 节数据流）。

### 3.3 系统输出

1. **最终报告**：JSON + Markdown 格式的完整分析报告（含材料学洞察、模型解释、可重复性摘要）
2. **模型 Artifact**：训练好的最优模型文件（joblib 格式）
3. **特征重要度**：全局特征重要度排名（含 SHAP / 排列重要度 / 系数分析）
4. **工作流追踪**：完整的 15 步工作流执行记录
5. **下载包清单**：包含所有输出文件的目录结构和下载链接
6. **数据库记录**：所有 16 个模块的执行结果均持久化到 PostgreSQL

---

## 4. 当前技术栈说明

### 4.1 后端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **Python** | 3.12 | 运行时 |
| **FastAPI** | 0.115.6 | Web 框架，路由、中间件、依赖注入、异常处理 |
| **Uvicorn** | 0.34.0 | ASGI 服务器 |
| **SQLModel** | 0.0.22 | ORM（基于 SQLAlchemy + Pydantic），模型定义和数据库操作 |
| **Psycopg2-binary** | 2.9.10 | PostgreSQL 数据库驱动 |
| **Pydantic** | 2.10.4 | 数据校验和序列化 |
| **pydantic-settings** | 2.7.1 | 环境变量管理和配置类 |
| **httpx** | 0.28.1 | LLM API 异步 HTTP 客户端 |
| **pandas** | 2.2.3 | 数据处理和特征矩阵操作 |
| **numpy** | 2.2.0 | 数值计算 |
| **scikit-learn** | >=1.3.0 | 机器学习模型、预处理、指标计算 |
| **scipy** | >=1.11.0 | 科学计算（统计检验等） |
| **pyarrow** | >=14.0.0 | Parquet 文件读写 |
| **openpyxl** | 3.1.5 | Excel 文件读取 |
| **pymatgen** | >=2024.0.0 | 材料科学计算库（成分解析） |
| **matminer** | >=0.9.0 | 材料特征工程库（元素属性/化学计量特征） |
| **python-dotenv** | 1.0.1 | .env 文件加载 |
| **alembic** | 1.14.1 | 数据库迁移（已配置但尚未深度使用） |

### 4.2 前端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **React** | 18.3.1 | UI 框架 |
| **TypeScript** | 5.7.2 | 类型安全 |
| **Ant Design** | 5.24.8 | UI 组件库（表单、卡片、标签、按钮等） |
| **@ant-design/icons** | 5.6.1 | 图标库 |
| **axios** | 1.7.9 | HTTP 客户端（含请求/响应拦截器） |
| **react-hook-form** | 7.54.2 | 表单状态管理 |
| **zod** | 3.24.1 | 前端表单校验 Schema |
| **@hookform/resolvers** | 3.10.0 | react-hook-form 与 zod 集成 |
| **ajv** | 8.20.0 | JSON Schema 校验 |

### 4.3 基础设施

| 技术 | 作用 |
|------|------|
| **PostgreSQL 16** | 主数据库（Docker 容器） |
| **Docker Compose** | 三服务编排（db + backend + frontend） |
| **OpenAI 兼容 LLM API** | LLM 推理服务（默认配置为智谱 GLM-5，通过 `LLM_BASE_URL` 配置） |

### 4.4 配置管理

所有配置通过 `backend/app/shared/config/settings.py` 中的 `Settings` 类集中管理，使用 `pydantic_settings.BaseSettings` 从 `.env` 文件和系统环境变量加载。关键配置项包括：

- `DATABASE_URL`：PostgreSQL 连接串
- `LLM_PROVIDER` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_BASE_URL`：LLM 配置
- `LLM_TIMEOUT` / `LLM_MAX_RETRIES` / `LLM_TEMPERATURE`：LLM 调用参数
- `DATASET_UPLOAD_DIR` / `FEATURE_ARTIFACT_DIR` / `MODEL_READY_ARTIFACT_DIR`：文件存储路径
- `ENABLE_COMPOSITION_FEATURIZER` / `ENABLE_DESCRIPTOR_FEATURIZER` / `ENABLE_STRUCTURE_FEATURIZER`：特征器开关
- `ENABLE_PYMATGEN` / `ENABLE_MATMINER` 等相关开关：外部库启用控制
- `FEATURE_PREPROCESSING_*` 系列：预处理策略配置（插补/缩放/特征选择策略）

---

## 5. 已实现功能模块

### 5.1 模块一：Task Specification（任务规格录入与校验）

- **输入**：用户通过前端表单提交的任务参数（`TaskSpecificationCreateRequest`）
- **处理逻辑**：
  1. `normalizer.py` 对用户输入进行字段标准化（如 `task_type` 缩写展开、`evaluation_metric` 统一）
  2. `validator.py` 对必填字段校验、指标与任务类型兼容性校验、输入类型一致性校验、警告生成
  3. `builder.py` 构建完整的 `task_spec_json`（含 `task_description`、`material_system`、`user_priority`、`constraints` 等）
  4. `service.py` 编排上述流程并调用 `repository.py` 持久化
- **输出**：`TaskSpecificationResponse`（含 `task_id`、`status`、`missing_fields`、`validation_messages`）
- **核心文件**：`task_specification/api.py`、`service.py`、`normalizer.py`、`validator.py`、`builder.py`、`model.py`
- **完成度**：~95%。基本 CRUD 和校验逻辑完整。

### 5.2 模块二：LLM-based Task Interpretation（基于大模型的任务理解）

- **输入**：模块一的 `TaskSpecification` 数据库记录
- **处理逻辑**：
  1. `task_spec_adapter.py` 将 TaskSpecification 转为 LLM context dict
  2. `prompt_builder.py` 构建含严格 JSON Schema 的 system prompt
  3. `llm_client.py` 通过 httpx 调用 OpenAI 兼容 LLM API（含 2 次重试）
  4. `parser.py` 从 LLM 响应中提取 JSON（正则去除 markdown 代码块包裹）
  5. `validator.py` 校验 LLM 输出结构完整性、枚举值合法性、置信度评分范围
  6. 校验失败则写 `status=failed` 记录并抛 `LLMOutputValidationException`
- **输出**：`TaskInterpretationResponse`（含 `InterpretedPredictionTarget`、`ModelingIntent`、`DatasetIntent`、`PlanningHint`、`ConstraintInterpretation`、`RecommendedDefaults`、`AmbiguityItem[]`）
- **核心文件**：`task_interpretation/api.py`、`service.py`、`prompt_builder.py`、`llm_client.py`、`parser.py`、`validator.py`、`builder.py`、`schemas.py`
- **完成度**：~90%。LLM 调用链路和降级逻辑完整。

### 5.3 模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）

- **输入**：`task_id` + 可选的 `uploaded_file_id` / `uploaded_file_path`
- **处理逻辑**：
  1. `context_builder.py` 跨库构建 context（校验 TaskSpecification 和 TaskInterpretation 状态）
  2. `source_resolver.py` 识别数据源（matbench / uploaded_file / unknown），含启发式规则
  3. 根据数据源选择 Loader（`MatbenchLoader` 或 `FileLoader`，策略模式）
  4. 四个 Checker 依次执行：`schema_checker` → `modality_checker` → `quality_checker` → `target_checker`
  5. `profiler.py` 进行质量评级、样本量等级、推荐下一步
  6. `builder.py` 构建包含 `workflow_planning_input` 的完整 profile JSON
- **输出**：`DatasetProfileResponse`（含 `DatasetSource`、`DatasetSchema`、`ModalityCheck`、`TargetProfile`、`DataQuality`、`ProfilingSummary`、`WorkflowPlanningInput`）
- **核心文件**：`dataset_profile/api.py`、`service.py`、`context_builder.py`、`source_resolver.py`、`profiler.py`、`builder.py`、`loaders/`、`checkers/`
- **完成度**：~90%。两种 Loader 和四种 Checker 均实现。

### 5.4 模块四：Workflow Planning（LLM 驱动的工作流规划）

- **输入**：模块一、二、三的数据库记录
- **处理逻辑**：
  1. `context_builder.py` 跨 4 个上游模块构建 context
  2. `prompt_builder.py` 构建超长 system prompt（10 条 CRITICAL 规则 + 8 个策略维度）
  3. 复用模块二的 `LLMClient` 调用 LLM
  4. `validator.py` 进行 250 行严格校验（含 Featurizer Registry 校验）
- **输出**：`WorkflowPlanResponse`（含 `TaskSummary`、`DataStrategy`、`FeatureStrategy`、`ModelStrategy`、`HPOStrategy`、`EvaluationStrategy`、`ValidationStrategy` 等 15+ 个子对象）
- **核心文件**：`workflow_planning/api.py`、`service.py`、`prompt_builder.py`、`validator.py`、`context_builder.py`、`schemas.py`
- **完成度**：~90%。

### 5.5 模块五：Feature Engineering（特征工程）

- **输入**：WorkflowPlan 中的 `FeatureStrategy` + DatasetProfile 中的原始数据
- **处理逻辑**：
  1. `strategy_resolver.py` 从 WorkflowPlan 中解析特征策略，查询 Featurizer Registry
  2. `data_loader_adapter.py` 从 DatasetProfile 加载原始数据
  3. `featurizer_router.py` 按策略路由到具体 Featurizer（composition / descriptor / structure）
  4. 特征提取结果经 `feature_matrix_builder.py` 构建特征矩阵
  5. `feature_quality_checker.py` 检查特征质量
  6. `artifact_manager.py` 将特征矩阵存储为 parquet/csv 到 `/app/artifacts/features/`
- **输出**：`FeatureEngineeringResponse`（含特征矩阵路径、特征列表、特征组信息）
- **核心文件**：`feature_engineering/api.py`、`service.py`、`strategy_resolver.py`、`featurizer_router.py`、`feature_matrix_builder.py`、`artifact_manager.py`、`featurizers/`
- **完成度**：~85%。Composition 和 Descriptor 路径完整，Structure 路径为 placeholder。

### 5.6 模块六：Feature Preprocessing（特征预处理）

- **输入**：模块五的特征矩阵 + WorkflowPlan 中的预处理策略
- **处理逻辑**：
  1. `artifact_loader.py` 加载特征矩阵
  2. `column_validator.py` + `feature_group_validator.py` 进行列和特征组校验
  3. `feature_filter.py` 过滤无效特征
  4. `preprocessing_pipeline_builder.py` 构建 sklearn Pipeline（Imputer → Scaler → FeatureSelector）
  5. `preprocessing_executor.py` 执行预处理
  6. `artifact_manager.py` 存储 model-ready 矩阵（parquet）+ preprocessor pipeline（joblib）
- **输出**：`FeaturePreprocessingResponse`（含 model-ready 矩阵路径、preprocessor 路径、特征摘要）
- **核心文件**：`feature_preprocessing/api.py`、`service.py`、`preprocessing_pipeline_builder.py`、`preprocessing_executor.py`、`artifact_manager.py`、`preprocessors/`
- **完成度**：~90%。

### 5.7 模块七：Model Search Context（模型搜索上下文更新）

- **输入**：DatasetProfile + FeatureEngineering + FeaturePreprocessing 的结果 + 原始 WorkflowPlan
- **处理逻辑**：
  1. 系统分析器依次分析：`dataset_profile_analyzer` → `feature_group_analyzer` → `preprocessing_analyzer`
  2. `llm_strategy_advisor.py` 通过 LLM 获取策略调整建议
  3. `model_strategy_adjuster` / `hpo_strategy_adjuster` / `evaluation_strategy_adjuster` / `validation_strategy_adjuster` 分别调整四类策略
  4. `strategy_merger.py` 合并系统分析和 LLM 建议
  5. `llm_advice_validator.py` 对 LLM 建议进行校验
- **输出**：`ModelSearchContextResponse`（含更新后的四类策略）
- **核心文件**：`model_search_context/api.py`、`service.py`、`strategy_merger.py`、`llm_strategy_advisor.py`、`*_analyzer.py`、`*_adjuster.py`
- **完成度**：~85%。

### 5.8 模块八：Automated Model and HPO Search（自动化模型与超参数搜索）

- **输入**：模块七的更新策略 + Model Registry + HPO Registry
- **处理逻辑**：
  1. `llm_model_search_advisor.py` 通过 LLM 获取模型搜索建议
  2. `llm_advice_validator.py` 对 LLM 推荐进行 Registry 校验
  3. `candidate_model_selector.py` 基于校验结果选择候选模型
  4. `search_space_builder.py` 为每个候选模型构建超参数搜索空间
  5. `trial_allocator.py` 分配 HPO Trial 预算
  6. `hpo_plan_builder.py` / `evaluation_plan_builder.py` / `validation_plan_builder.py` 构建子计划
  7. `pipeline_input_builder.py` 构建下游 Pipeline Generation 所需输入
- **输出**：`ModelSearchPlanResponse`（含候选模型列表、HPO 计划、搜索空间、Trial 分配）
- **核心文件**：`model_search/api.py`、`service.py`、`candidate_model_selector.py`、`search_space_builder.py`、`trial_allocator.py`
- **完成度**：~85%。

### 5.9 模块九：Executable Pipeline Generation（可执行流水线生成）

- **输入**：模块八的 Model Search Plan + 上游 Artifacts
- **处理逻辑**（12 步流水线）：
  1. context → 2. artifact_resolver → 3. component_binder → 4. pipeline_spec_builder → 5. trial_plan_builder → 6. pipeline_validator → 7. safety_checker（15+ 危险模式） → 8. LLM advisory review（非阻塞） → 9. execution_input_builder → 10. bundle → 11. response → 12. persist
- **输出**：`PipelineGenerationResponse`（含 pipeline_spec、execution_input_json、LLM review）
- **核心文件**：`pipeline_generation/api.py`、`service.py`、`safety_checker.py`、`pipeline_validator.py`、`execution_input_builder.py`、`llm_pipeline_reviewer.py`
- **完成度**：~85%。

### 5.10 模块十：Pipeline Execution and Training（流水线执行与训练）

- **输入**：模块九的 `execution_input_json`
- **处理逻辑**（12 步流水线）：
  1. context → 2. load_input → 3. load_matrix → 4. create_splits → 5. expand_plan → 6. setup_dir → 7. execute_training（通过 Controlled Executor） → 8. collect_artifacts → 9. build_metric_input → 10. save_artifacts → 11. build_response → 12. persist
- **关键设计**：`controlled_executor.py` 作为唯一训练入口，`model_factory.py` 提供显式模型映射，禁止 LLM 生成训练代码
- **输出**：`PipelineExecutionResponse`（含训练结果、Trial 结果、metric_input_json）
- **核心文件**：`pipeline_execution/api.py`、`service.py`、`controlled_executor.py`、`model_factory.py`、`trial_runner.py`、`fold_runner.py`
- **完成度**：~85%。

### 5.11 模块十一：Metric Evaluation（指标评估）

- **输入**：模块十的 `metric_input_json` + prediction artifacts
- **处理逻辑**（13 步流水线）：
  1. context → 2. load_input → 3. load_predictions → 4. build_trial_info → 5. evaluate_folds → 6. aggregate_trials → 7. aggregate_pipelines → 8. rank → 9. compare_baselines → 10. build_diagnosis_input → 11. save_artifacts → 12. build_response → 13. persist
- **输出**：`MetricEvaluationResponse`（含模型排名、基线比较、best_model_id、best_trial_id、diagnosis_input）
- **核心文件**：`metric_evaluation/api.py`、`service.py`、`model_ranker.py`、`baseline_comparator.py`、`metric_calculator.py`、`metric_registry.py`
- **完成度**：~90%。

### 5.12 模块十二：LLM-based Result Diagnosis（基于大模型的结果诊断）

- **输入**：模块十一的 metric evaluation 结果
- **处理逻辑**（15 步流水线）：
  1. context → 2. load_input → 3. optional_context → 4. extract_evidence → 5. system_checks → 6. build_llm_context → 7. build_prompt → 8. call_llm → 9. parse → 10. validate（14 种危险代码模式） → 11. normalize（26 条 `DIAGNOSIS_TYPE_ALIASES` 映射） → 12. build_refinement_input → 13. save_artifacts → 14. build_response → 15. persist
- **关键设计**：LLM 仅建议不执行，失败时降级到 system rule-based fallback
- **输出**：`ResultDiagnosisResponse`（含 `DiagnosticFinding[]`、`evidence_strength`、`refinement_input`）
- **核心文件**：`result_diagnosis/api.py`、`service.py`、`evidence_extractor.py`、`system_diagnostic_checker.py`、`llm_diagnosis_validator.py`、`llm_diagnosis_normalizer.py`
- **完成度**：~90%。

### 5.13 模块十三：LLM-driven Workflow Refinement（LLM 驱动的工作流精炼）

- **输入**：模块十二的诊断结果 + 历史迭代数据
- **处理逻辑**（14 步流水线）：
  1. context → 2. load_input → 3. collect_history → 4. build_llm_context → 5. build_prompt → 6. call_llm → 7. parse → 8. validate → 9. scan_safety → 10. normalize → 11. validate_revised_plan → 12. build_delta → 13. build_rerun_plan_or_fpsi → 14. save_artifacts + persist
- **关键设计**：`experiment_history_collector.py` 从 5 个上游模块收集跨迭代历史数据；`adopt_revised_plan` 端点实现 Adopt & Rerun 闭环
- **输出**：`WorkflowRefinementResponse`（含 `decision`：`proceed_next_stage` 或 `iterate_refinement`、`revised_workflow_plan`、`iteration_rerun_plan`、`final_pipeline_selection_input`）
- **核心文件**：`workflow_refinement/api.py`、`service.py`、`experiment_history_collector.py`、`workflow_plan_delta_builder.py`、`iteration_rerun_plan_builder.py`、`revised_workflow_plan_validator.py`
- **完成度**：~90%。

### 5.14 模块十四：Final Pipeline Selection（最终流水线选择）★

- **输入**：模块十三的 `final_pipeline_selection_input`（通过 WorkflowRefinement 的 `proceed_next_stage` 决策触发）
- **处理逻辑**：
  1. `context_builder.py` 校验上游 WorkflowRefinement 状态
  2. `selection_input_loader.py` 加载 `final_pipeline_selection_input`
  3. `candidate_collector.py` 收集所有候选实验（从 MetricEvaluation + PipelineExecution）
  4. `candidate_validator.py` 校验候选（模型 artifact / 预测 artifact 可用性）
  5. `selection_policy_builder.py` 构建选择策略（balanced / performance_first / interpretability_first / robust）
  6. `constraint_checker.py` 应用约束过滤
  7. `candidate_scorer.py` 按策略评分
  8. `final_ranker.py` 排名并选择最终 Pipeline（`select_final_pipeline`）
  9. `artifact_resolver.py` 解析最终 artifact 路径
  10. `selection_reason_builder.py` 构建系统选择理由
  11. `llm_selection_explainer.py` 通过 LLM 生成选择解释（可选，非阻塞）
  12. `interpretability_input_builder.py` 构建 Interpretability Analysis 输入
- **输出**：`FinalPipelineSelectionResponse`（含 `final_pipeline_spec_id`、`final_model_id`、`final_model_family`、`final_trial_id`、`primary_metric_value`、`candidate_ranking`、`system_selection_reason`、`llm_selection_explanation`、`interpretability_analysis_input`）
- **核心文件**：`final_pipeline_selection/api.py`、`service.py`、`candidate_collector.py`、`candidate_scorer.py`、`final_ranker.py`、`selection_policy_builder.py`、`constraint_checker.py`、`artifact_resolver.py`
- **关键设计**：
  - `CandidateStatus` 枚举（ELIGIBLE / REJECTED / INCOMPLETE_ARTIFACTS）
  - 选择策略为 `SelectionPolicy` Pydantic model（含 `selection_profile`、`metric_weights`、`constraints`）
  - LLM 解释为非阻塞：失败时降级，不影响主选择流程
  - 零候选时写 `status=failed` 并返回详细拒绝原因
- **完成度**：~85%。

### 5.15 模块十五：Interpretability Analysis（可解释性分析）★

- **输入**：模块十四的 `interpretability_analysis_input`（含 `model_artifact_path`、`model_ready_matrix_path`、`prediction_artifact_paths`）
- **处理逻辑**：
  1. `context_builder.py` 校验上游 FinalPipelineSelection 状态
  2. `interpretability_input_loader.py` 加载分析输入
  3. 路径安全校验（`_validate_artifact_paths`：禁止 `..` 路径穿越）
  4. `model_artifact_loader.py` 加载训练好的模型（joblib）
  5. `feature_matrix_loader.py` 加载特征矩阵（parquet），自动派生 `feature_columns`
  6. `prediction_artifact_loader.py` 加载预测结果
  7. `interpretability_method_selector.py` 按模型族智能选择可解释性方法：
     - 线性模型 → coefficient importance
     - 树模型 → native importance（feature_importances_）
     - 通用 → permutation importance + SHAP
  8. 四种分析器依次执行：`coefficient_importance_analyzer` → `native_importance_analyzer` → `permutation_importance_analyzer` → `shap_analyzer`
  9. 排列重要度作为通用 fallback（其他方法全失败时自动触发）
  10. `feature_group_analyzer.py` 对特征进行分组和归类（`classify_feature_group`）
  11. `local_explanation_builder.py` 构建局部解释
  12. `high_error_sample_analyzer.py` 分析高误差样本
  13. `llm_interpretability_summarizer.py` 通过 LLM 生成材料学洞察（可选，非阻塞）
  14. `final_output_input_builder.py` 构建 Final Output 输入
- **输出**：`InterpretabilityAnalysisResponse`（含 `global_feature_importance`（Top 30）、`permutation_importance`、`shap_summary`、`local_explanations`、`high_error_sample_analysis`、`feature_group_summary`、`material_insight_summary`、`final_output_input`）
- **核心文件**：`interpretability_analysis/api.py`、`service.py`、`interpretability_method_selector.py`、`permutation_importance_analyzer.py`、`shap_analyzer.py`、`feature_group_analyzer.py`、`llm_interpretability_summarizer.py`
- **关键设计**：
  - `InterpretabilityMethodStatus` 枚举（COMPUTED / FAILED / FALLBACK_USED）
  - 每种分析方法有独立的 try-except，失败不中断整体流程
  - SHAP 含 explainer_type 自动选择（tree / linear / kernel）
  - `max_shap_samples` 限制 SHAP 计算样本量（性能控制）
  - LLM 总结器失败不影响主流程（`use_llm_summarizer` 为可选）
- **完成度**：~80%。核心分析逻辑完整，LLM 材料学洞察为可选增强。

### 5.16 模块十六：Final Output（最终输出与报告生成）★

- **输入**：模块十五的 `final_output_input`
- **处理逻辑**（21 步最终输出流程）：
  1. context → 2. load_input → 3. collect_workflow_trace（跨 15 个模块收集执行轨迹） → 4. resolve_final_artifacts → 5. build_reproducibility_summary → 6. build_system_summaries（任务/数据/特征/模型/指标/解释摘要） → 7. build_llm_report_context → 8-12. LLM report writer（parse → validate → normalize，非阻塞） → 13. determine status → 14. generate IDs + artifact_dir → 15. render JSON report → 16. render Markdown report → 17. build_output_package → 18. build_download_links → 19. determine ready_for_delivery → 20. persist → 21. save_artifacts
- **输出**：`FinalOutputResponse`（含 `final_report_json`、`final_report_markdown`、`workflow_trace`、`reproducibility_summary`、`artifact_manifest`、`output_package_manifest`、`download_links`）
- **核心文件**：`final_output/api.py`、`service.py`、`workflow_trace_collector.py`、`reproducibility_summary_builder.py`、`final_summary_builder.py`、`report_renderer.py`、`output_package_builder.py`、`llm_report_writer.py`
- **关键设计**：
  - `report_renderer.py` 支持 JSON 和 Markdown 双格式渲染
  - `build_fallback_report()` 在 LLM 失败时生成系统规则报告
  - `_make_json_safe()` 递归转换 datetime 等不可序列化对象
  - `workflow_trace_collector.py` 跨所有 15 个上游模块收集执行记录
  - `output_package_builder.py` 构建下载包和链接
- **完成度**：~85%。核心报告生成完整，LLM 报告为可选增强。

### 5.17 共享能力注册表

#### Featurizer Registry

- **文件**：`backend/app/shared/registry/featurizer_registry.py`
- **内容**：11 个 FeaturizerSpec 定义（6 个 available + 5 个 planned）
- **核心 API**：
  - `get_available_featurizers(input_modality, task_type, feature_type)` — 按条件过滤
  - `resolve(name)` — 按 id 或别名查找
  - `resolve_to_available(name, input_modality)` — 解析并检查可用性
  - `get_default_fallback(input_modality, task_type)` — 返回最高优先级 fallback
  - `validate_registry()` — 启动时自检（去重、别名冲突、状态合法性）
- **依赖检测**：在 import 时自动检测 pymatgen / matminer / scikit-learn / pyarrow / scipy 的安装状态

#### Model Registry

- **文件**：`backend/app/shared/registry/model_registry.py`
- **内容**：10 个 Model Family 定义
  - baseline: `dummy_mean`
  - simple: `linear_regression`、`ridge`、`lasso`、`knn`
  - moderate: `elastic_net`、`random_forest`、`svr`
  - high: `gradient_boosting`、`xgboost`
- **API**：`get_all_model_families()`、`get_model_families_for_task_type()`、`is_valid_model_family()`、`get_model_spec()`、`get_baseline_models()`

#### HPO Registry

- **文件**：`backend/app/shared/registry/hpo_registry.py`
- **内容**：5 个 HPO Method 定义
  - `random_search`、`grid_search`、`optuna_tpe`、`bayesian_search`、`successive_halving`
- **API**：`get_all_hpo_methods()`、`is_valid_hpo_method()`、`get_hpo_method_spec()`

---

## 6. 系统数据流与调用链路

### 6.1 完整数据流（端到端）

```
用户提交表单 (React → FastAPI POST /api/tasks)
    │
    ▼ TaskSpecificationResponse (含 task_id)
模块二：LLM Task Interpretation
    │ POST /api/task-interpretations/{task_id}
    ▼ TaskInterpretationResponse (含 modeling_intent / dataset_intent / planning_hint)
模块三：Dataset Profile
    │ POST /api/dataset-profiles/{task_id}
    ▼ DatasetProfileResponse (含 workflow_planning_input)
模块四：Workflow Planning
    │ POST /api/workflow-plans/{task_id}
    ▼ WorkflowPlanResponse (含 feature_strategy / model_strategy / hpo_strategy)
模块五：Feature Engineering
    │ POST /api/feature-engineerings/{task_id}
    ▼ FeatureEngineeringResponse (含 feature_matrix_path / feature_groups)
模块六：Feature Preprocessing
    │ POST /api/feature-preprocessings/{task_id}
    ▼ FeaturePreprocessingResponse (含 model_ready_matrix_path / preprocessor_path)
模块七：Model Search Context
    │ POST /api/model-search-contexts/{task_id}
    ▼ ModelSearchContextResponse (含 updated strategies)
模块八：Model Search
    │ POST /api/model-search-plans/{task_id}
    ▼ ModelSearchPlanResponse (含 candidates / hpo_plans / search_spaces)
模块九：Pipeline Generation
    │ POST /api/pipeline-generations/{task_id}
    ▼ PipelineGenerationResponse (含 execution_input_json)
模块十：Pipeline Execution
    │ POST /api/pipeline-executions/{task_id}
    ▼ PipelineExecutionResponse (含 training_results / metric_input_json)
模块十一：Metric Evaluation
    │ POST /api/metric-evaluations/{task_id}
    ▼ MetricEvaluationResponse (含 model_ranking / best_model_id / diagnosis_input)
模块十二：Result Diagnosis
    │ POST /api/result-diagnoses/{task_id}
    ▼ ResultDiagnosisResponse (含 diagnostic_findings / refinement_input)
模块十三：Workflow Refinement
    │ POST /api/workflow-refinements/{task_id}
    ▼ WorkflowRefinementResponse
    ├── decision = "proceed_next_stage"
    │       │
    │       ▼ final_pipeline_selection_input
    │ 模块十四：Final Pipeline Selection
    │       │ POST /api/final-pipeline-selections/{task_id}
    │       ▼ FinalPipelineSelectionResponse (含 interpretability_analysis_input)
    │ 模块十五：Interpretability Analysis
    │       │ POST /api/interpretability-analyses/{task_id}
    │       ▼ InterpretabilityAnalysisResponse (含 final_output_input)
    │ 模块十六：Final Output
    │       │ POST /api/final-outputs/{task_id}
    │       ▼ FinalOutputResponse (含 final_report + download_links)
    │
    └── decision = "iterate_refinement"
            │ POST /api/workflow-refinements/{wr_id}/adopt
            ▼ AdoptRevisedPlanResult (含 rerun_stages / reuse_artifacts)
            │ 前端按 rerun_stages 顺序重新执行对应 pipeline 阶段
            ▼ 回到模块十二 Result Diagnosis（进入新一轮诊断）
```

### 6.2 前端 Adopt & Rerun 闭环（WorkflowRefinementPanel）

`frontend/src/modules/workflowRefinement/components/WorkflowRefinementPanel.tsx` 中的 `handleAdoptAndRerun` 函数实现了完整的闭环迭代：

1. 调用 `adoptRevisedPlan(wrId)` 获取 `rerun_stages`
2. 按 `rerun_stages` 顺序依次调用各模块的 create API：`featureEngineering` → `featurePreprocessing` → `modelSearchContext` → `modelSearch` → `pipelineGeneration` → `pipelineExecution` → `metricEvaluation`
3. 自动触发新一轮 `resultDiagnosis` 和 `workflowRefinement`
4. 每个阶段的结果和错误单独展示在进度面板中

### 6.3 API 路由汇总

| 模块 | 路由前缀 | 主要端点 |
|------|---------|---------|
| Task Specification | `/api/tasks` | POST `/`, GET `/{id}`, PUT `/{id}`, POST `/{id}/validate` |
| Task Interpretation | `/api/task-interpretations` | POST `/{task_id}`, GET `/{id}`, GET by task, POST `/{task_id}/rerun` |
| Dataset Profile | `/api/dataset-profiles` | POST `/{task_id}`, GET `/{id}`, GET by task, POST rerun, GET preview |
| Workflow Planning | `/api/workflow-plans` | POST `/{task_id}`, GET `/{id}`, GET by task, POST rerun |
| Feature Engineering | `/api/feature-engineerings` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun, preview |
| Featurizer Registry | — (注册在 feature_engineering) | GET `/api/featurizer-registry/...` |
| Feature Preprocessing | `/api/feature-preprocessings` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun |
| Model Search Context | `/api/model-search-contexts` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun |
| Model Search | `/api/model-search-plans` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun |
| Pipeline Generation | `/api/pipeline-generations` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun |
| Pipeline Execution | `/api/pipeline-executions` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun |
| Metric Evaluation | `/api/metric-evaluations` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun |
| Result Diagnosis | `/api/result-diagnoses` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun |
| Workflow Refinement | `/api/workflow-refinements` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun, GET revised-plan/rerun-plan/fpsi, POST `/{id}/adopt` |
| Final Pipeline Selection | `/api/final-pipeline-selections` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun, candidate-ranking, llm-explanation, artifact-manifest, ia-input |
| Interpretability Analysis | `/api/interpretability-analyses` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun, feature-importance, shap-summary, local-explanations, fo-input |
| Final Output | `/api/final-outputs` | POST `/{task_id}`, GET `/{id}`, GET by task, rerun, report, workflow-trace, artifact-manifest, download-links |

---

## 7. 核心代码与关键设计说明

### 7.1 数据模型设计模式

所有模块的数据模型遵循统一模式（以 `TaskSpecification` 为例）：

```python
# backend/app/modules/task_specification/model.py
class TaskSpecification(SQLModel, table=True):
    __tablename__ = "task_specification"
    id: Optional[str] = Field(default=None, primary_key=True)
    # 关键业务字段平铺（用于索引和快速查询）
    task_name: Optional[str]
    task_type: Optional[str]
    status: Optional[str]
    # 完整 JSONB 存储（用于灵活扩展）
    task_spec_json: Optional[dict] = Field(sa_column=Column(JSONB))
    created_at / updated_at: Optional[datetime]
```

**设计原则**：关键业务字段平铺用于 SQL 索引，完整结构存储在 JSONB 列中用于灵活扩展。这种"平铺 + JSONB"混合模式贯穿全部 16 个模块。

### 7.2 服务层编排模式

每个模块的 `service.py` 遵循统一的编排模式：

1. `build_context()` — 校验上游模块状态
2. 核心处理（LLM 调用 / 算法执行 / 数据转换）
3. `build_response()` — 构建标准化响应
4. `persist` — 持久化到数据库

以模块二 `TaskInterpretationService.create_interpretation()` 为例（`backend/app/modules/task_interpretation/service.py`）：

```python
def create_interpretation(self, session, task_id, request):
    context = adapt_task_spec(task_spec)          # 1. 适配
    system_prompt, user_message = build_prompt(context)  # 2. 构建 prompt
    raw_response = self.llm_client.generate(...)  # 3. LLM 调用
    llm_output = parse_llm_response(raw_response) # 4. 解析
    validation_result = validate_interpretation(llm_output)  # 5. 校验
    interpretation_dict = build_interpretation(...) # 6. 构建
    interp_model = TaskInterpretation(...)        # 7. 实例化
    created = self.interp_repo.create(session, interp_model)  # 8. 持久化
    return self._to_response(created)             # 9. 返回
```

### 7.3 异常处理体系

所有异常继承自 `BusinessException`（`backend/app/shared/common/exceptions.py`）：

```
BusinessException (message, error_code)
├── ValidationException (error_code="VALIDATION_ERROR")
├── NotFoundException (error_code="NOT_FOUND")
├── DatabaseException (error_code="DATABASE_ERROR")
└── [各模块专用异常] (如 LLMCallException, LLMOutputParseException, ...)
```

`main.py` 中注册了全局异常处理器：
- `BusinessException` → 400（特殊 error_code 返回 404）
- `Exception` → 500（通用兜底）

### 7.4 LLM 调用客户端

`backend/app/modules/task_interpretation/llm_client.py` 中的 `LLMClient` 封装了统一的 LLM 调用逻辑：
- 使用 `httpx` 客户端
- 支持 OpenAI 兼容 API（通过 `LLM_BASE_URL` 配置切换提供商）
- 默认 2 次重试（`LLM_MAX_RETRIES`）
- 120 秒超时（`LLM_TIMEOUT`）
- Temperature 固定为 0.0（`LLM_TEMPERATURE`）

各模块通过直接实例化 `LLMClient` 或通过适配器（如 `llm_client_adapter.py`、`llm_workflow_refiner.py` 等）复用此客户端。

### 7.5 数据库会话管理

`backend/app/shared/database/session.py` 中的 `get_session()` 通过 FastAPI 的 `Depends` 机制注入数据库会话：

```python
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

所有 API 端点的 `session: Session = Depends(get_session)` 均使用此注入模式。

### 7.6 API 统一响应格式

所有 API 返回统一 JSON 结构（`backend/app/shared/common/response.py`）：

```json
{
    "success": true/false,
    "message": "...",
    "data": { ... },
    "error_code": null 或 "ERROR_CODE"
}
```

### 7.7 安全设计要点

1. **路径穿越防护**：模块十五的 `_validate_artifact_paths()` 函数检查 `..` 并限制在 `/app/artifacts` 目录下
2. **代码注入防护**：模块九的 `safety_checker.py` 扫描 15+ 种危险模式（`import`、`eval`、`exec`、`subprocess`、`os.system` 等）
3. **LLM 输出安全**：所有调用 LLM 的模块都经过 `parser → validator → normalizer` 三步清理
4. **LLM 无执行权限**：LLM 只能输出结构化建议，不能生成可执行代码

### 7.8 日志系统

所有模块使用 Python 标准 `logging` 模块，按模块名获取 logger：

```python
logger = logging.getLogger(__name__)
```

日志级别使用 `logger.info()` / `logger.warning()` / `logger.error()` 三级。

### 7.9 CORS 配置

`main.py` 中通过 `CORSMiddleware` 配置跨域，允许 `settings.CORS_ORIGINS` 中列出的来源（默认 `http://localhost:3000`）。

---

## 8. 当前未完成部分与后续开发建议

### 8.1 尚未实现的功能

1. **测试体系**：项目中没有任何测试文件（`.pytest_cache/` 仅含缓存文件，无实际测试代码）。需要在每个模块下建立 `tests/` 目录。
2. **数据库迁移管理**：`alembic` 已在 requirements.txt 中但未初始化（无 `alembic.ini` 或 `migrations/` 目录）。当前依赖 `SQLModel.metadata.create_all()` 自建表，不适合生产环境。
3. **Structure Featurizer**：Featurizer Registry 中标记为 `status="planned"` 的 5 个 structure featurizer 仅有 spec 定义和占位代码，不可执行。
4. **Optuna TPE / Bayesian Search**：HPO Registry 中定义了 `optuna_tpe` 和 `bayesian_search` 方法，但 optuna 不在 requirements.txt 中，可能存在运行时依赖缺失。
5. **Successive Halving**：HPO Registry 中定义了该方法，但实际执行逻辑可能不完整（需阅读 `pipeline_execution/hpo_trial_generator.py` 确认）。
6. **LLM API Key 管理**：`.env` 中包含真实的 API key，需要迁移到更安全的密钥管理方案。
7. **前端路由**：当前仅有一个页面（`TaskSpecificationPage`），无 React Router。所有面板嵌入在 TaskSpecificationForm 中，无独立页面对每个模块。
8. **前端错误处理**：前端各组件的错误处理较为基础（`catch` 后直接 `setError`），缺少统一的错误处理中间件。
9. **身份认证与授权**：完全没有用户认证系统，所有 API 端点均为公开访问。
10. **速率限制**：无 API 速率限制。
11. **Docker 生产部署**：Dockerfile 使用开发模式（`npm start` / `uvicorn`），没有生产级别的反向代理（如 nginx）。
12. **监控与告警**：没有健康检查之外的监控（仅 `GET /health` 端点）。
13. **数据校验深度**：模块十五和十六中的部分数据字段使用了 `_safe_get_id` 等简单 pass-through 函数，校验不够严格。

### 8.2 半成品代码和潜在问题

1. **`closed_loop_refinement/` 目录**：`backend/app/modules/closed_loop_refinement/` 仅含 `__pycache__` 文件（无 `.py` 源码），是旧模块的残留。已完全被 `workflow_refinement/` 取代。建议清理此目录。
2. **`_safe_dump()` 函数重复**：`final_pipeline_selection/service.py`、`interpretability_analysis/service.py`、`final_output/service.py` 中各自定义了 `_safe_dump()` 函数，逻辑基本相同。建议提取到 `shared/common/` 作为公共工具函数。
3. **硬编码路径**：多处使用 `/app/artifacts/` 开头的硬编码路径（如 `final_output/service.py` 中的 `artifact_dir`），建议统一从 `settings` 配置。
4. **LLM Client 不一致**：模块二定义了 `LLMClient`，但后续模块（十三、十四、十五、十六）使用各自封装的 LLM 类（如 `LLMWorkflowRefiner`、`LLMSelectionExplainer`、`LLMInterpretabilitySummarizer`、`LLMReportWriter`），造成 LLM 调用逻辑分散。
5. **Feature Group 分析器重复**：`model_search_context/feature_group_analyzer.py` 和 `interpretability_analysis/feature_group_analyzer.py` 功能相似但独立存在，有潜在的逻辑不一致风险。
6. **WorkflowPlan 的 `adopt_revised_plan` 方法**：模块四的 `WorkflowPlanningService` 必须实现 `adopt_revised_plan` 方法（被模块十三调用），需确认该方法存在并功能完整。

### 8.3 后续开发建议

1. **优先级最高**：建立测试体系（pytest + FastAPI TestClient）。每个模块至少需要有 service 层的单元测试和 API 层的集成测试。
2. **优先级高**：初始化 alembic 并创建首次迁移脚本，将 `create_all()` 替换为迁移管理。
3. **优先级高**：清理 `closed_loop_refinement/` 目录的残留文件。
4. **优先级中**：统一 LLM 客户端：提取 `LLMClient` 到 `shared/` 作为公共组件，各模块的 LLM 封装类继承或组合之。
5. **优先级中**：提取公共工具函数（`_safe_dump()`、`_make_json_safe()` 等）到 `shared/common/utils.py`。
6. **优先级中**：将硬编码路径替换为 `settings` 配置项。
7. **优先级中**：实现 Structure Featurizer（需 pymatgen Structure 解析 + matminer 结构特征提取）。
8. **优先级中**：在 requirements.txt 中添加 `optuna` 依赖（如确实使用 optuna TPE）。
9. **优先级低**：添加 React Router，为每个模块创建独立页面路由。
10. **优先级低**：添加用户认证（JWT + OAuth2）、API 速率限制、生产级 Docker 部署配置。

---

## 9. 给后续 AI Coding 大模型的开发提示

### 9.1 优先阅读的文件（按顺序）

1. **`docs/PROJECT_IMPLEMENTATION_OVERVIEW.md`**（本文档）— 全局理解项目
2. **`backend/app/main.py`** — 路由注册、异常处理、中间件配置
3. **`backend/app/shared/config/settings.py`** — 所有配置项的定义和默认值
4. **`backend/app/shared/common/exceptions.py`** — 异常体系入口
5. **`backend/app/shared/common/response.py`** — API 响应格式
6. **`backend/app/shared/registry/featurizer_registry.py`** — Featurizer 共享契约（被多个模块消费）
7. **`backend/app/shared/registry/model_registry.py`** — Model 共享契约
8. **`backend/app/shared/registry/hpo_registry.py`** — HPO 共享契约
9. **`backend/app/modules/task_specification/service.py`** — 第一个模块的完整实现模式（可作为参考模板）
10. **`backend/app/modules/task_interpretation/service.py`** — LLM 调用 + 解析 + 校验 + 持久化的标准模式
11. **`backend/app/modules/pipeline_execution/controlled_executor.py`** — 训练执行的安全边界
12. **`backend/app/modules/workflow_refinement/service.py`** — 闭环迭代的核心逻辑
13. **`frontend/src/index.tsx`** — 前端入口
14. **`frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx`** — 前端主组件（含所有面板嵌入）

### 9.2 重要注意事项

1. **不要重新实现已有功能**：16 个模块的核心流程均已实现。如需修改某个模块，优先在现有文件上增量修改，而非创建新模块。
2. **不要绕过安全机制**：所有训练必须通过 `controlled_executor.py`；LLM 输出必须经过 `parser → validator → normalizer` 三步；文件路径必须校验 `..` 防止路径穿越。
3. **不要破坏管道依赖**：每个模块的 `context_builder.py` 依赖特定上游模块的输出状态。新增或修改模块时确保管道顺序不被破坏。
4. **不要混用 LLM 客户端**：修改 LLM 调用逻辑时，先检查 `shared/` 中是否有统一客户端。如果添加新的 LLM 调用场景，优先提取到共享层。
5. **不要硬编码路径**：文件路径应从 `settings` 对象获取，而非硬编码 `/app/artifacts/`。
6. **不要忽略异常处理**：所有 API 端点的异常应继承 `BusinessException` 并在 API 层捕获。不要让原始异常泄漏到响应中。
7. **注意 JSONB 字段的序列化**：存储到 JSONB 的 dict 中的值必须是 JSON 可序列化的（注意 `datetime`、`date`、`Decimal` 等类型）。
8. **注意模块间的 ID 引用链**：下游模块通过 `*_id` 字段引上游模块记录。如果需要"向上追溯"，必须通过 repository 查询。
9. **`closed_loop_refinement/` 是已废弃的残留目录**：不要尝试修复或恢复此目录中的代码。所有 Closed-loop Refinement 功能已在 `workflow_refinement/` 中实现。
10. **前端 Adopt & Rerun 的关键路径**：`WorkflowRefinementPanel.tsx` 中的 `handleAdoptAndRerun` 函数包含前端闭环迭代的完整逻辑。修改此流程时需同时更新该函数和对应的后端 `adopt_revised_plan` 端点。
11. **前后端类型同步**：前端 `src/api/` 中的 TypeScript 接口定义应与后端 `schemas.py` 中的 Pydantic model 保持一致。修改后端 Schema 时需同步更新前端类型定义。

### 9.3 开发环境启动

```bash
# 启动全部服务
docker-compose up -d

# 仅启动数据库（本地开发后端）
docker-compose up -d db

# 启动后端（需要先启动 db）
cd backend && uvicorn app.main:app --reload --port 8000

# 启动前端
cd frontend && npm start
```

前端访问地址：`http://localhost:3000`
后端 API 文档：`http://localhost:8000/docs`（FastAPI 自动生成 Swagger UI）
健康检查：`GET http://localhost:8000/health`
