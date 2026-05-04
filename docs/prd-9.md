# PRD：Executable Pipeline Generation 模块

> 项目：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：9
> 模块名称：Executable Pipeline Generation
> 上游模块：Automated Model and HPO Search
> 下游模块：Pipeline Execution and Training
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0

---

## 1. 背景与上下文

MLAgent 当前已完成从 **Task Specification → LLM-based Task Interpretation → Dataset Loading, Checking, and Profiling → Workflow Planning → Feature Engineering → Feature Preprocessing → Model Search Context Update → Automated Model and HPO Search** 的完整链路。附件说明中明确指出，当前系统已经完成 8 个核心业务模块，尚未实现 Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis、Report Generation 等后续阶段。

模块八 **Automated Model and HPO Search** 已经生成了下游所需的 `Model Search Plan`，其中包含：

* `dataset_context`
* `candidate_model_plan`
* `hpo_plan`
* `search_space_plan`
* `validation_plan`
* `evaluation_plan`
* `system_validation_result`
* `pipeline_generation_input`

因此，**Executable Pipeline Generation** 的核心任务不是重新选择模型、重新设计 HPO，也不是训练模型，而是：

> 将上游 Model Search Plan 中的模型搜索计划、验证策略、评价策略、模型就绪特征矩阵路径、预处理管道路径等信息，转换为系统可识别、可校验、可版本化、可交给 Controlled Executor 执行的 Pipeline Spec / Pipeline Bundle。

---

## 2. 模块定位

### 2.1 模块一句话定义

**Executable Pipeline Generation** 是连接“模型搜索规划”和“模型训练执行”的桥接模块，负责把上游结构化计划转换为受控的、执行准备就绪的机器学习 Pipeline 规格文件，而不是直接运行训练。

### 2.2 在整体链路中的位置

```text
Feature Preprocessing
    ↓
Model Search Context Update
    ↓
Automated Model and HPO Search
    ↓
Executable Pipeline Generation   ← 当前模块
    ↓
Pipeline Execution and Training
    ↓
Metric Evaluation
    ↓
Result Diagnosis
    ↓
Report Generation
```

### 2.3 本模块核心产物

本模块最终产出：

```text
Pipeline Generation Result
    ├── pipeline_generation_id
    ├── task_id
    ├── model_search_plan_id
    ├── status
    ├── pipeline_bundle
    ├── pipeline_specs
    ├── trial_plan
    ├── component_binding_result
    ├── validation_result
    ├── artifact_manifest
    ├── execution_input
    └── ready_for_execution
```

其中最重要的是：

> `execution_input`：下游 Pipeline Execution and Training 模块的唯一正式输入。

---

## 3. 设计原则

### 3.1 LLM 深度参与但不直接生成可执行代码

本模块必须继续遵守 MLAgent 的核心安全原则：

* LLM 可以参与：

  * Pipeline 结构审查；
  * 模型-预处理-验证策略一致性检查；
  * Pipeline 风险提示；
  * 执行顺序建议；
  * 搜索计划合理性解释；
  * 资源风险判断；
  * fallback 建议。

* LLM 不允许：

  * 生成 Python 训练代码；
  * 生成 `model.fit()`、`Pipeline(...)` 等可执行逻辑；
  * 修改系统运行逻辑；
  * 创建动态 import；
  * 创建任意文件写入逻辑；
  * 直接实例化模型；
  * 直接指定未在 Registry 中注册的组件；
  * 绕过系统 Validator / Template / Controlled Executor。

### 3.2 系统生成最终 Pipeline

最终 Pipeline 必须由系统内置能力生成：

* `Model Registry`
* `HPO Registry`
* `Pipeline Component Registry`
* `Pipeline Template Registry`
* `Pipeline Spec Builder`
* `Pipeline Validator`
* `Artifact Resolver`
* `Execution Input Builder`

LLM 的输出只能作为辅助建议或风险提示，不能作为最终执行依据。

### 3.3 Pipeline Generation 不执行训练

本模块只做：

```text
读取计划 → 解析组件 → 绑定 Registry → 生成 Pipeline Spec → 校验 → 持久化 → 输出给执行模块
```

本模块不做：

```text
模型训练
HPO trial 执行
指标计算
最佳模型选择
训练日志采集
模型保存
结果诊断
报告生成
```

---

## 4. 产品目标

### 4.1 MVP 目标

本模块 MVP 需要实现以下目标：

1. 从最新的 `ModelSearchPlan` 中读取 `pipeline_generation_input`；
2. 校验上游 `ModelSearchPlan.ready_for_pipeline_generation = true`；
3. 解析候选模型、基线模型、HPO 计划、搜索空间、验证策略、评价策略；
4. 将每个候选模型转换为系统内部的 `PipelineSpec`；
5. 生成统一的 `PipelineBundle`；
6. 为下游执行模块生成 `execution_input`；
7. 对所有 Pipeline Spec 进行结构校验、安全校验、Registry 校验、Artifact 路径校验；
8. 将成功或失败结果持久化到数据库；
9. 前端展示 Pipeline Generation 的状态、Pipeline 列表、模型组件绑定、验证结果、下游执行输入和完整 JSON。

### 4.2 非目标

MVP 阶段不做：

1. 不执行训练；
2. 不执行 HPO；
3. 不计算 MAE、RMSE、Accuracy 等指标；
4. 不保存模型权重；
5. 不生成 sklearn 代码文件；
6. 不生成 notebook；
7. 不支持用户手动编辑 Pipeline 的底层执行逻辑；
8. 不支持自定义未注册模型；
9. 不支持动态安装依赖；
10. 不实现分布式训练。

---

## 5. 用户故事

### 5.1 研究者视角

作为材料科学研究者，我希望在模型搜索计划生成后，系统能够自动把候选模型和超参数搜索策略转换为可执行 Pipeline，使我不需要手动编写训练代码。

### 5.2 开发者视角

作为后端开发者，我希望 Pipeline Generation 的输出是严格结构化的 `PipelineSpec` 和 `execution_input`，这样后续 Pipeline Execution 模块可以稳定消费。

### 5.3 AI Agent 系统视角

作为 AI Agent 系统，我希望 LLM 能帮助判断 Pipeline 结构是否合理，但最终执行规格必须由系统 Registry 和 Validator 生成，保证安全、可控、可复现。

### 5.4 前端用户视角

作为前端用户，我希望在页面上清楚看到：

* 当前是否可以生成 Pipeline；
* 生成了哪些候选 Pipeline；
* 每个 Pipeline 对应哪个模型；
* 是否启用 HPO；
* 使用什么验证策略；
* 是否通过系统校验；
* 是否已经准备好进入训练执行阶段。

---

## 6. 模块边界

### 6.1 与上游 Automated Model and HPO Search 的边界

上游模块负责：

* 选择候选模型；
* 选择 baseline models；
* 生成 HPO 计划；
* 生成 search space；
* 生成 validation plan；
* 生成 evaluation plan；
* 生成 `pipeline_generation_input`。

本模块负责：

* 消费这些计划；
* 不重新规划模型；
* 不重新生成搜索空间；
* 不改变 HPO 方法；
* 将计划转换为执行规格；
* 校验执行规格是否符合系统约束。

### 6.2 与下游 Pipeline Execution and Training 的边界

本模块负责：

* 生成 `execution_input`；
* 生成 `PipelineSpec`；
* 生成 `TrialPlan`；
* 声明 artifact 路径；
* 声明执行顺序；
* 声明模型、预处理、验证、评价组件绑定结果。

下游模块负责：

* 加载 `execution_input`；
* 实例化模型；
* 实际执行训练；
* 执行 HPO trial；
* 保存训练结果；
* 记录日志；
* 生成训练产物；
* 将结果交给 Metric Evaluation。

### 6.3 与 Metric Evaluation 的边界

本模块可以携带 `evaluation_plan`，但不计算指标。

例如，本模块可以声明：

```text
primary_metric = MAE
metric_direction = minimize
secondary_metrics = [RMSE, R2]
```

但不产生：

```text
MAE = 0.324
RMSE = 0.512
R2 = 0.86
```

### 6.4 与 Result Diagnosis 的边界

本模块可以提示 Pipeline 风险，例如：

* 小样本数据使用复杂模型有过拟合风险；
* 特征数过少可能限制模型表达能力；
* HPO trial 数较少可能搜索不足。

但不做结果诊断，因为此时尚无训练结果。

---

## 7. 输入设计

### 7.1 创建请求输入

接口：

```text
POST /api/pipeline-generations/{task_id}
```

请求字段：

| 字段                            | 类型      | 必填 | 说明                                                          |
| ----------------------------- | ------- | -: | ----------------------------------------------------------- |
| `force_rerun`                 | boolean |  否 | 是否强制重新生成 Pipeline，默认 false                                  |
| `use_llm_reviewer`            | boolean |  否 | 是否启用 LLM 对 Pipeline 结构进行审查，默认 true                          |
| `include_baselines`           | boolean |  否 | 是否为 baseline models 生成 Pipeline，默认 true                     |
| `include_hpo_candidates`      | boolean |  否 | 是否为 HPO 候选模型生成 Pipeline，默认 true                             |
| `pipeline_profile`            | string  |  否 | Pipeline 生成模式：`compact` / `standard` / `full`，默认 `standard` |
| `max_pipeline_specs_override` | integer |  否 | 覆盖最大 Pipeline 数量，MVP 可选                                     |
| `notes`                       | string  |  否 | 用户备注，仅用于记录，不影响执行逻辑                                          |

### 7.2 上游依赖输入

本模块必须读取：

| 来源                          | 必需字段                                                                                                                                                                    |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ModelSearchPlan`           | `id`, `task_id`, `status`, `ready_for_pipeline_generation`, `plan_json`                                                                                                 |
| `ModelSearchPlan.plan_json` | `candidate_model_plan`, `hpo_plan`, `search_space_plan`, `validation_plan`, `evaluation_plan`, `pipeline_generation_input`                                              |
| `pipeline_generation_input` | `model_ready_matrix_path`, `feature_columns`, `target_column`, `task_type`, `primary_metric`, `candidate_models`, `search_spaces`, `validation_plan`, `evaluation_plan` |
| `FeaturePreprocessing`      | `model_ready_artifact_path`, `preprocessor_artifact_path`, `n_final_features`, `target_column`                                                                          |
| `Model Registry`            | 模型 ID、模型族、任务类型支持、是否需要 scaling、是否可 HPO                                                                                                                                   |
| `HPO Registry`              | HPO 方法 ID、支持任务类型、trial 范围、是否可并行                                                                                                                                         |

### 7.3 Artifact 输入

本模块不加载完整训练数据，但必须校验路径存在性和元数据一致性：

| Artifact                       | 来源                    | 用途                     |
| ------------------------------ | --------------------- | ---------------------- |
| `model_ready_features.parquet` | Feature Preprocessing | 下游训练输入矩阵               |
| `preprocessor.joblib`          | Feature Preprocessing | 后续推理或复现实验时使用           |
| `preprocessing_metadata.json`  | Feature Preprocessing | 校验特征列、target 列、预处理策略   |
| `ModelSearchPlan.plan_json`    | Model Search          | 生成 Pipeline Spec 的核心计划 |

---

## 8. 输出设计

### 8.1 核心输出：PipelineGenerationResponse

| 字段                           | 类型          | 说明                                                          |
| ---------------------------- | ----------- | ----------------------------------------------------------- |
| `pipeline_generation_id`     | string      | 本模块记录 ID，例如 `pg_xxxxxxxx`                                   |
| `task_id`                    | string      | 任务 ID                                                       |
| `model_search_plan_id`       | string      | 上游模型搜索计划 ID                                                 |
| `feature_preprocessing_id`   | string      | 上游特征预处理 ID                                                  |
| `status`                     | string      | `generated` / `generated_with_warning` / `failed`           |
| `generation_mode`            | string      | `system_template_based` / `system_template_with_llm_review` |
| `n_pipeline_specs`           | integer     | 生成的 Pipeline Spec 数量                                        |
| `n_baseline_specs`           | integer     | baseline pipeline 数量                                        |
| `n_hpo_specs`                | integer     | HPO pipeline 数量                                             |
| `pipeline_bundle`            | object      | Pipeline 总包                                                 |
| `pipeline_specs`             | array       | 每个模型对应的 Pipeline 规格                                         |
| `trial_plan`                 | object      | trial 层面的执行计划                                               |
| `component_binding_result`   | object      | 模型、HPO、验证、评价组件绑定结果                                          |
| `artifact_manifest`          | object      | 输入 artifact 和计划 artifact 的路径说明                              |
| `pipeline_validation_result` | object      | 系统校验结果                                                      |
| `llm_pipeline_review`        | object      | LLM 审查结果，可选                                                 |
| `execution_input`            | object      | 下游 Pipeline Execution 的正式输入                                 |
| `ready_for_execution`        | boolean     | 是否可以进入下游训练执行                                                |
| `warnings`                   | array       | 警告信息                                                        |
| `error_message`              | string/null | 失败原因                                                        |
| `created_at`                 | datetime    | 创建时间                                                        |
| `updated_at`                 | datetime    | 更新时间                                                        |

---

## 9. Pipeline Spec 设计

### 9.1 PipelineBundle

`PipelineBundle` 是本模块的核心结构，用于描述一次模型搜索计划下生成的所有 Pipeline。

字段设计：

| 字段                           | 类型     | 说明                           |
| ---------------------------- | ------ | ---------------------------- |
| `bundle_id`                  | string | Pipeline Bundle ID           |
| `task_id`                    | string | 任务 ID                        |
| `model_search_plan_id`       | string | 上游模型搜索计划 ID                  |
| `task_type`                  | string | regression / classification  |
| `target_column`              | string | 目标列                          |
| `feature_columns`            | array  | 特征列                          |
| `primary_metric`             | string | 主指标                          |
| `metric_direction`           | string | minimize / maximize          |
| `model_ready_matrix_path`    | string | 模型就绪特征矩阵路径                   |
| `preprocessor_artifact_path` | string | 预处理管道路径                      |
| `pipeline_specs`             | array  | PipelineSpec 列表              |
| `validation_plan`            | object | 验证策略                         |
| `evaluation_plan`            | object | 评价策略                         |
| `hpo_plan`                   | object | HPO 总计划                      |
| `execution_policy`           | object | 执行策略，不直接执行                   |
| `created_by`                 | string | `pipeline_generation_module` |

### 9.2 PipelineSpec

每个 `PipelineSpec` 对应一个模型候选或 baseline。

字段设计：

| 字段                          | 类型          | 说明                                         |
| --------------------------- | ----------- | ------------------------------------------ |
| `pipeline_spec_id`          | string      | Pipeline Spec ID，例如 `ps_ridge_xxxx`        |
| `pipeline_role`             | string      | `baseline` / `candidate` / `hpo_candidate` |
| `model_id`                  | string      | Registry 中的模型 ID                           |
| `model_family`              | string      | 模型族                                        |
| `model_display_name`        | string      | 展示名称                                       |
| `priority`                  | string      | high / medium / low                        |
| `hpo_enabled`               | boolean     | 是否启用 HPO                                   |
| `search_space_ref`          | string/null | 对应 search space 的引用                        |
| `fixed_params`              | object      | 固定参数，由系统模板提供                               |
| `search_space`              | object/null | 超参数搜索空间，由模块八提供并经系统校验                       |
| `validation_plan_ref`       | string      | 验证计划引用                                     |
| `evaluation_plan_ref`       | string      | 评价计划引用                                     |
| `input_artifact_ref`        | string      | 模型就绪矩阵引用                                   |
| `preprocessor_artifact_ref` | string      | 预处理管道引用                                    |
| `component_bindings`        | object      | 组件绑定结果                                     |
| `safety_constraints`        | object      | 安全约束                                       |
| `execution_ready`           | boolean     | 是否可交给执行模块                                  |
| `warnings`                  | array       | 警告                                         |

### 9.3 TrialPlan

`TrialPlan` 描述下游执行阶段应该如何展开训练 trial。

MVP 推荐设计为：

| 字段                       | 类型      | 说明                                         |
| ------------------------ | ------- | ------------------------------------------ |
| `trial_plan_id`          | string  | Trial Plan ID                              |
| `hpo_enabled`            | boolean | 是否启用 HPO                                   |
| `search_method`          | string  | random_search / grid_search / optuna_tpe 等 |
| `max_total_trials`       | integer | 总 trial 数                                  |
| `max_parallel_trials`    | integer | 最大并行 trial 数                               |
| `trial_allocation`       | array   | 每个模型分配多少 trial                             |
| `baseline_trial_policy`  | object  | baseline 是否只跑一次                            |
| `candidate_trial_policy` | object  | candidate 如何展开 trial                       |
| `early_stopping_policy`  | object  | 是否启用早停，仅声明不执行                              |
| `fallback_policy`        | object  | HPO 失败时回退策略                                |

### 9.4 ExecutionInput

`execution_input` 是下游模块唯一正式消费对象。

字段设计：

| 字段                           | 类型      | 说明              |
| ---------------------------- | ------- | --------------- |
| `pipeline_generation_id`     | string  | 当前模块 ID         |
| `pipeline_bundle_id`         | string  | Bundle ID       |
| `task_id`                    | string  | 任务 ID           |
| `task_type`                  | string  | 任务类型            |
| `model_ready_matrix_path`    | string  | 训练数据路径          |
| `preprocessor_artifact_path` | string  | 预处理管道路径         |
| `target_column`              | string  | 目标列             |
| `feature_columns`            | array   | 特征列             |
| `pipeline_specs`             | array   | 待执行 Pipeline 列表 |
| `trial_plan`                 | object  | trial 展开计划      |
| `validation_plan`            | object  | 验证计划            |
| `evaluation_plan`            | object  | 评价计划            |
| `execution_constraints`      | object  | 资源、安全、超时等执行约束   |
| `ready_for_execution`        | boolean | 是否允许进入执行阶段      |

---

## 10. 后端功能设计

### 10.1 推荐目录结构

建议新增目录：

```text
backend/app/modules/pipeline_generation/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── artifact_resolver.py
    ├── component_registry.py
    ├── component_binder.py
    ├── pipeline_template_registry.py
    ├── pipeline_spec_builder.py
    ├── trial_plan_builder.py
    ├── pipeline_validator.py
    ├── safety_checker.py
    ├── llm_review_prompt_builder.py
    ├── llm_pipeline_reviewer.py
    ├── llm_review_parser.py
    ├── llm_review_validator.py
    ├── execution_input_builder.py
    └── builder.py
```

说明：以上是文件职责规划，不要求一次性全部复杂实现。MVP 可以先实现核心文件，再预留扩展文件。

---

## 11. 后端核心流程

### 11.1 主流程

```text
PipelineGenerationService.create_pipeline_generation(task_id, request)
    ↓
1. context_builder.build_pipeline_generation_context()
    ↓
2. artifact_resolver.resolve_artifacts()
    ↓
3. component_binder.bind_components()
    ↓
4. pipeline_spec_builder.build_pipeline_specs()
    ↓
5. trial_plan_builder.build_trial_plan()
    ↓
6. pipeline_validator.validate_pipeline_bundle()
    ↓
7. safety_checker.check_pipeline_safety()
    ↓
8. llm_pipeline_reviewer.review()，可选
    ↓
9. execution_input_builder.build_execution_input()
    ↓
10. builder.build_pipeline_generation_response()
    ↓
11. repository.create()
```

### 11.2 步骤说明

#### Step 1：构建上下文

`context_builder` 负责：

* 根据 `task_id` 获取最新 `ModelSearchPlan`；
* 校验 `ModelSearchPlan.status = planned`；
* 校验 `ready_for_pipeline_generation = true`；
* 读取 `plan_json.pipeline_generation_input`；
* 获取关联的 `FeaturePreprocessing`；
* 校验 `model_ready_artifact_path`；
* 校验 `preprocessor_artifact_path`；
* 加载 Model Registry；
* 加载 HPO Registry。

失败情况：

| 失败场景                         | 错误码                                 |
| ---------------------------- | ----------------------------------- |
| 找不到 Model Search Plan        | `MODEL_SEARCH_PLAN_NOT_FOUND`       |
| Model Search Plan 未准备好       | `MODEL_SEARCH_PLAN_NOT_READY`       |
| 缺少 pipeline_generation_input | `PIPELINE_GENERATION_INPUT_MISSING` |
| 缺少 model_ready artifact      | `MODEL_READY_ARTIFACT_MISSING`      |
| 缺少 preprocessor artifact     | `PREPROCESSOR_ARTIFACT_MISSING`     |

#### Step 2：解析 Artifact

`artifact_resolver` 负责：

* 校验 `model_ready_features.parquet` 路径存在；
* 校验 `preprocessor.joblib` 路径存在；
* 读取 metadata；
* 确认 feature columns 和 target column 一致；
* 构造 `artifact_manifest`。

注意：MVP 阶段只做轻量 metadata 校验，不加载完整数据训练。

#### Step 3：组件绑定

`component_binder` 负责把计划中的模型和 HPO 方法绑定到系统组件。

绑定对象包括：

| 计划字段                             | 绑定目标                                   |
| -------------------------------- | -------------------------------------- |
| `model_id`                       | `Model Registry`                       |
| `hpo_method`                     | `HPO Registry`                         |
| `validation_plan.split_strategy` | `Validation Strategy Registry`，MVP 可内置 |
| `evaluation_plan.primary_metric` | `Metric Registry`，MVP 可内置              |
| `preprocessor_artifact_path`     | Artifact Manifest                      |
| `model_ready_matrix_path`        | Artifact Manifest                      |

绑定结果写入：

```text
component_binding_result
```

#### Step 4：生成 Pipeline Specs

`pipeline_spec_builder` 负责：

* 为每个 baseline model 生成 baseline PipelineSpec；
* 为每个 candidate model 生成 candidate PipelineSpec；
* 为启用 HPO 的模型挂载 search space；
* 绑定 validation plan；
* 绑定 evaluation plan；
* 绑定 input artifact；
* 绑定 preprocessor artifact；
* 标记 `execution_ready`。

MVP 推荐策略：

| 模型类型                                              | 生成方式                           |
| ------------------------------------------------- | ------------------------------ |
| `dummy_mean`                                      | 生成 baseline spec，不启用 HPO       |
| `linear_regression`                               | 可作为 strong baseline，不启用或轻量 HPO |
| `ridge/lasso/elastic_net`                         | 可启用 HPO                        |
| `random_forest/gradient_boosting/xgboost/svr/knn` | 按上游 hpo_enabled 决定             |

#### Step 5：生成 Trial Plan

`trial_plan_builder` 负责：

* 继承模块八的 `hpo_plan.trial_allocation`；
* 不重新分配 trial；
* 将 trial allocation 绑定到具体 PipelineSpec；
* 区分 baseline trial 和 HPO trial；
* 输出下游执行模块可展开的 trial plan。

#### Step 6：Pipeline 校验

`pipeline_validator` 负责：

| 校验类型        | 说明                                 |
| ----------- | ---------------------------------- |
| 结构校验        | 必填字段完整                             |
| Registry 校验 | 模型、HPO、指标、验证策略均合法                  |
| Artifact 校验 | 输入路径存在                             |
| 任务类型兼容性     | regression/classification 与模型、指标兼容 |
| 搜索空间校验      | search space 与模型 ID 对应             |
| trial 校验    | trial 数量不超过上游限制                    |
| 数据字段校验      | feature_columns、target_column 不为空  |
| 下游输入校验      | execution_input 必须完整               |

#### Step 7：安全检查

`safety_checker` 负责：

* 禁止任何代码字符串；
* 禁止 `import`；
* 禁止 `eval`；
* 禁止 `exec`；
* 禁止 shell command；
* 禁止文件删除类操作；
* 禁止任意路径写入；
* 禁止非 artifact 目录路径；
* 禁止未注册组件；
* 禁止动态类名；
* 禁止网络请求配置。

本模块允许出现的是：

```text
结构化 ID
结构化参数
Registry 引用
Artifact 引用
执行策略声明
```

不允许出现的是：

```text
可执行代码
脚本片段
动态运行逻辑
```

#### Step 8：LLM Pipeline Review，可选

如果 `use_llm_reviewer = true`，系统可以将已经由系统生成的 PipelineBundle 摘要交给 LLM 审查。

LLM 只能输出：

| 字段                       | 说明      |
| ------------------------ | ------- |
| `risk_notes`             | 风险提示    |
| `consistency_findings`   | 一致性检查意见 |
| `resource_warnings`      | 资源消耗警告  |
| `suggested_review_items` | 建议人工关注点 |
| `confidence_score`       | 审查置信度   |

LLM 不允许输出：

* pipeline 代码；
* 参数空间；
* 模型实例化逻辑；
* 执行脚本；
* 修改后的 PipelineSpec。

如果 LLM 建议与系统校验冲突：

> 以系统 Validator 为准。

#### Step 9：构建 Execution Input

`execution_input_builder` 负责生成下游唯一正式输入。

只有当以下条件都满足时：

```text
pipeline_validation_result.is_valid = true
safety_check_result.is_safe = true
artifact_manifest.is_complete = true
n_pipeline_specs > 0
```

才允许：

```text
ready_for_execution = true
```

---

## 12. 数据库设计

### 12.1 新增表：PipelineGeneration

表名建议：

```text
pipeline_generation
```

字段设计：

| 字段                         | 类型       | 索引    | 说明                                                      |
| -------------------------- | -------- | ----- | ------------------------------------------------------- |
| `id`                       | string   | PK    | `pg_{uuid8}`                                            |
| `task_id`                  | string   | index | 任务 ID                                                   |
| `model_search_plan_id`     | string   | index | 上游 Model Search Plan ID                                 |
| `feature_preprocessing_id` | string   | index | 上游 Feature Preprocessing ID                             |
| `status`                   | string   | index | generated / generated_with_warning / failed             |
| `generation_mode`          | string   |       | system_template_based / system_template_with_llm_review |
| `task_type`                | string   | index | regression / classification                             |
| `target_column`            | string   |       | 目标列                                                     |
| `primary_metric`           | string   |       | 主指标                                                     |
| `n_pipeline_specs`         | integer  |       | Pipeline 数量                                             |
| `n_baseline_specs`         | integer  |       | baseline 数量                                             |
| `n_hpo_specs`              | integer  |       | HPO Pipeline 数量                                         |
| `hpo_enabled`              | boolean  | index | 是否启用 HPO                                                |
| `ready_for_execution`      | boolean  | index | 是否可进入训练                                                 |
| `llm_review_used`          | boolean  |       | 是否使用 LLM 审查                                             |
| `llm_confidence_score`     | float    |       | LLM 审查置信度                                               |
| `pipeline_json`            | JSONB    |       | 完整 Pipeline Generation 结果                               |
| `execution_input_json`     | JSONB    |       | 下游执行输入                                                  |
| `llm_request_json`         | JSONB    |       | LLM 审查请求，可选                                             |
| `llm_response_json`        | JSONB    |       | LLM 审查响应，可选                                             |
| `error_message`            | string   |       | 错误信息                                                    |
| `created_at`               | datetime | index | 创建时间                                                    |
| `updated_at`               | datetime |       | 更新时间                                                    |

---

## 13. 状态设计

### 13.1 PipelineGenerationStatus

| 状态                       | 说明              |
| ------------------------ | --------------- |
| `generated`              | 成功生成，且可进入执行     |
| `generated_with_warning` | 成功生成，但存在警告，仍可执行 |
| `failed`                 | 生成失败，不可执行       |

### 13.2 ready_for_execution 规则

| 条件                   | ready_for_execution |
| -------------------- | ------------------- |
| 所有 PipelineSpec 通过校验 | true                |
| 存在非致命 warning        | true                |
| 缺少 artifact          | false               |
| 模型未注册                | false               |
| HPO 方法非法             | false               |
| 搜索空间与模型不匹配           | false               |
| 安全检查失败               | false               |
| 没有生成任何 PipelineSpec  | false               |

---

## 14. API 设计

### 14.1 创建 Pipeline Generation

```text
POST /api/pipeline-generations/{task_id}
```

说明：

* 根据最新 Model Search Plan 生成 PipelineBundle；
* 默认不覆盖旧记录；
* 如果已有成功记录且 `force_rerun = false`，可直接返回最新结果。

### 14.2 获取指定 Pipeline Generation

```text
GET /api/pipeline-generations/{pipeline_generation_id}
```

返回完整结果。

### 14.3 获取任务最新 Pipeline Generation

```text
GET /api/tasks/{task_id}/pipeline-generation
```

返回该任务最新的 Pipeline Generation 结果。

### 14.4 重新生成 Pipeline

```text
POST /api/pipeline-generations/{task_id}/rerun
```

等价于 `force_rerun = true`，生成新记录，不覆盖旧记录。

### 14.5 获取 Pipeline Generation 摘要

```text
GET /api/pipeline-generations/{pipeline_generation_id}/summary
```

用于前端快速展示。

建议返回：

* `pipeline_generation_id`
* `status`
* `n_pipeline_specs`
* `n_baseline_specs`
* `n_hpo_specs`
* `hpo_enabled`
* `ready_for_execution`
* `warnings`
* `created_at`

### 14.6 获取 Execution Input

```text
GET /api/pipeline-generations/{pipeline_generation_id}/execution-input
```

供后续 Pipeline Execution 模块调用或调试使用。

---

## 15. 后端 Schema 设计

### 15.1 Request Schema

建议包含：

```text
PipelineGenerationCreateRequest
    ├── force_rerun
    ├── use_llm_reviewer
    ├── include_baselines
    ├── include_hpo_candidates
    ├── pipeline_profile
    ├── max_pipeline_specs_override
    └── notes
```

### 15.2 Response Schema

建议包含：

```text
PipelineGenerationResponse
    ├── pipeline_generation_id
    ├── task_id
    ├── model_search_plan_id
    ├── feature_preprocessing_id
    ├── status
    ├── generation_mode
    ├── pipeline_bundle
    ├── pipeline_specs
    ├── trial_plan
    ├── component_binding_result
    ├── artifact_manifest
    ├── pipeline_validation_result
    ├── safety_check_result
    ├── llm_pipeline_review
    ├── execution_input
    ├── ready_for_execution
    ├── warnings
    ├── error_message
    ├── created_at
    └── updated_at
```

---

## 16. Registry 与 Template 设计

### 16.1 Pipeline Component Registry

建议新增 `Pipeline Component Registry`，用于声明系统允许使用的 Pipeline 组件。

MVP 可支持以下组件类型：

| 组件类型                  | 示例                                       |
| --------------------- | ---------------------------------------- |
| `input_loader`        | model_ready_matrix_loader                |
| `preprocessor`        | preprocessor_artifact_loader             |
| `estimator`           | model_registry_estimator                 |
| `validation_splitter` | kfold / train_test_split                 |
| `metric_evaluator`    | mae / rmse / r2 / accuracy               |
| `hpo_controller`      | random_search / grid_search / optuna_tpe |

该 Registry 只声明组件能力，不执行组件。

### 16.2 Pipeline Template Registry

建议新增 `Pipeline Template Registry`，用于定义不同任务类型下的标准 Pipeline 结构。

MVP 支持：

| 模板 ID                          | 任务类型           | 说明          |
| ------------------------------ | -------------- | ----------- |
| `tabular_regression_basic`     | regression     | 表格回归基础模板    |
| `tabular_regression_hpo`       | regression     | 表格回归 HPO 模板 |
| `tabular_classification_basic` | classification | 表格分类基础模板    |
| `tabular_classification_hpo`   | classification | 表格分类 HPO 模板 |

模板只描述结构：

```text
load model-ready matrix
select feature/target columns
apply validation split
instantiate registered estimator
optionally run HPO controller
evaluate with registered metrics
```

模板不包含可执行代码。

---

## 17. 前端功能设计

### 17.1 新增前端文件结构

建议新增：

```text
frontend/src/api/pipelineGenerationApi.ts

frontend/src/modules/pipelineGeneration/
    ├── components/
    │   ├── PipelineGenerationPanel.tsx
    │   ├── PipelineBundleCard.tsx
    │   ├── PipelineSpecTable.tsx
    │   ├── TrialPlanCard.tsx
    │   ├── ComponentBindingCard.tsx
    │   ├── ArtifactManifestCard.tsx
    │   ├── PipelineValidationCard.tsx
    │   ├── SafetyCheckCard.tsx
    │   ├── LLMPipelineReviewCard.tsx
    │   ├── ExecutionInputCard.tsx
    │   └── PipelineGenerationJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

### 17.2 页面集成方式

当前前端是单页 `TaskSpecificationPage`，已有多个模块面板。MVP 阶段建议继续沿用该模式，在 `ModelSearchPlanPanel` 后增加：

```text
PipelineGenerationPanel
```

展示顺序：

```text
Task Specification
Task Interpretation
Dataset Profile
Workflow Plan
Feature Engineering
Feature Preprocessing
Model Search Context
Model Search Plan
Pipeline Generation   ← 新增
```

### 17.3 前端主面板功能

`PipelineGenerationPanel` 应提供：

| 功能                   | 说明                                             |
| -------------------- | ---------------------------------------------- |
| Generate Pipeline    | 调用创建接口                                         |
| Re-run Generation    | 强制重新生成                                         |
| Load Latest          | 获取最新结果                                         |
| View Execution Input | 查看下游输入                                         |
| Copy JSON            | 复制完整 JSON，方便调试                                 |
| Status Tag           | 展示 generated / generated_with_warning / failed |
| Ready Tag            | 展示 ready_for_execution                         |

### 17.4 前端展示模块

#### 17.4.1 Pipeline Bundle Summary

展示：

* Bundle ID
* Task Type
* Target Column
* Primary Metric
* Pipeline 数量
* Baseline 数量
* HPO Pipeline 数量
* 是否可执行

#### 17.4.2 Pipeline Spec Table

表格字段：

| 列                | 说明                                   |
| ---------------- | ------------------------------------ |
| Pipeline Spec ID | Pipeline ID                          |
| Role             | baseline / candidate / hpo_candidate |
| Model            | 模型名称                                 |
| Priority         | 优先级                                  |
| HPO              | 是否启用                                 |
| Trial Count      | 分配 trial 数                           |
| Execution Ready  | 是否可执行                                |
| Warnings         | 警告                                   |

#### 17.4.3 Trial Plan Card

展示：

* HPO Method
* Max Total Trials
* Max Parallel Trials
* Trial Allocation
* Baseline Policy
* Candidate Policy
* Fallback Policy

#### 17.4.4 Component Binding Card

展示：

* Model Registry 绑定结果
* HPO Registry 绑定结果
* Validation Strategy 绑定结果
* Evaluation Metric 绑定结果
* Artifact 绑定结果

#### 17.4.5 Artifact Manifest Card

展示：

* model-ready matrix path
* preprocessor artifact path
* metadata path
* artifact 是否存在
* feature columns 数量
* target column

#### 17.4.6 Validation & Safety Card

展示：

* 结构校验结果；
* Registry 校验结果；
* Artifact 校验结果；
* 安全扫描结果；
* 错误和警告列表。

#### 17.4.7 LLM Review Card

如果启用 LLM Review，展示：

* 风险提示；
* 一致性检查；
* 资源消耗警告；
* 置信度；
* 注意：明确标注“LLM Review is advisory only”。

#### 17.4.8 Execution Input Card

展示下游执行输入摘要：

* pipeline_generation_id
* pipeline_bundle_id
* n_pipeline_specs
* model_ready_matrix_path
* validation strategy
* evaluation metric
* ready_for_execution

---

## 18. 前端状态与交互

### 18.1 按钮状态

| 条件                        | Generate Pipeline 按钮     |
| ------------------------- | ------------------------ |
| 无 task_id                 | disabled                 |
| 无 Model Search Plan       | disabled                 |
| Model Search Plan 未 ready | disabled                 |
| 正在请求                      | loading                  |
| 已生成且不 force rerun         | 可显示 Load Latest / Re-run |

### 18.2 状态颜色建议

| 状态                            | 颜色     |
| ----------------------------- | ------ |
| `generated`                   | green  |
| `generated_with_warning`      | orange |
| `failed`                      | red    |
| `ready_for_execution = true`  | green  |
| `ready_for_execution = false` | red    |

### 18.3 错误展示

错误应展示：

* error_code
* message
* 可能原因
* 建议操作

例如：

```text
MODEL_SEARCH_PLAN_NOT_READY
当前 Model Search Plan 尚未准备好生成 Pipeline，请先完成 Automated Model and HPO Search。
```

---

## 19. LLM 参与设计

### 19.1 是否必须调用 LLM

MVP 中，LLM Review 可选。

推荐默认：

```text
use_llm_reviewer = true
```

但即使 LLM 不可用，系统仍应能基于 Registry 和 Template 生成 Pipeline。

### 19.2 LLM 输入

LLM Review 只接收摘要，不接收完整敏感路径或可执行内容。

输入包括：

* task_type
* n_samples
* n_features
* candidate models summary
* hpo summary
* validation strategy
* evaluation metric
* generated pipeline summary
* system warnings

### 19.3 LLM 输出

LLM 只能输出结构化 JSON 建议：

| 字段                       | 类型     | 说明    |
| ------------------------ | ------ | ----- |
| `overall_assessment`     | string | 总体评价  |
| `risk_notes`             | array  | 风险提示  |
| `consistency_findings`   | array  | 一致性发现 |
| `resource_warnings`      | array  | 资源风险  |
| `suggested_review_items` | array  | 建议关注项 |
| `confidence_score`       | float  | 置信度   |

### 19.4 LLM 输出校验

`llm_review_validator` 必须检查：

* JSON 结构；
* 必填字段；
* 置信度范围；
* 禁止代码内容；
* 禁止出现 import / def / fit / shell / path write 等内容；
* 不允许新增模型；
* 不允许修改 PipelineSpec；
* 不允许修改 trial allocation；
* 不允许修改 search space。

---

## 20. 安全与可控性要求

### 20.1 禁止事项

本模块绝对禁止：

1. 让 LLM 输出 Python 代码；
2. 让 LLM 输出 sklearn Pipeline 代码；
3. 动态执行字符串；
4. 动态 import；
5. 根据 LLM 输出创建模型对象；
6. 让用户在前端编辑执行逻辑；
7. 将任意路径传入执行模块；
8. 绕过 Registry 使用模型；
9. 绕过 Validator 直接设置 ready 状态；
10. 在本模块执行训练。

### 20.2 路径安全

所有 artifact 路径必须满足：

* 位于系统允许的 artifact 根目录；
* 文件存在；
* 文件类型符合预期；
* 不包含 `..` 路径逃逸；
* 不允许绝对路径指向系统敏感目录；
* 不允许用户手动传入任意训练路径。

### 20.3 组件安全

所有组件必须来自 Registry：

* model_id 必须来自 Model Registry；
* hpo_method 必须来自 HPO Registry；
* metric 必须来自 Metric Registry 或内置指标白名单；
* validation strategy 必须来自内置验证策略白名单；
* pipeline template 必须来自 Pipeline Template Registry。

---

## 21. 异常设计

建议新增异常：

| 异常类                                       | error_code                          | 场景                           |
| ----------------------------------------- | ----------------------------------- | ---------------------------- |
| `PipelineGenerationNotFoundException`     | `PIPELINE_GENERATION_NOT_FOUND`     | 找不到记录                        |
| `ModelSearchPlanRequiredException`        | `MODEL_SEARCH_PLAN_REQUIRED`        | 缺少上游计划                       |
| `ModelSearchPlanNotReadyException`        | `MODEL_SEARCH_PLAN_NOT_READY`       | 上游未 ready                    |
| `PipelineGenerationInputMissingException` | `PIPELINE_GENERATION_INPUT_MISSING` | 缺少 pipeline_generation_input |
| `ArtifactResolveException`                | `ARTIFACT_RESOLVE_FAILED`           | artifact 解析失败                |
| `ComponentBindingException`               | `COMPONENT_BINDING_FAILED`          | 组件绑定失败                       |
| `PipelineSpecBuildException`              | `PIPELINE_SPEC_BUILD_FAILED`        | Pipeline Spec 构建失败           |
| `PipelineValidationException`             | `PIPELINE_VALIDATION_FAILED`        | 系统校验失败                       |
| `PipelineSafetyException`                 | `PIPELINE_SAFETY_CHECK_FAILED`      | 安全检查失败                       |
| `LLMPipelineReviewException`              | `LLM_PIPELINE_REVIEW_FAILED`        | LLM 审查失败                     |
| `ExecutionInputBuildException`            | `EXECUTION_INPUT_BUILD_FAILED`      | 下游输入构建失败                     |

---

## 22. MVP 验收标准

### 22.1 后端验收标准

必须满足：

1. 可以通过 `POST /api/pipeline-generations/{task_id}` 生成 Pipeline Generation 结果；
2. 必须校验最新 `ModelSearchPlan.ready_for_pipeline_generation = true`；
3. 能正确读取 `pipeline_generation_input`；
4. 能生成至少一个 `PipelineSpec`；
5. 能为 baseline 和 candidate model 区分 pipeline role；
6. 能绑定 Model Registry 和 HPO Registry；
7. 能生成 `PipelineBundle`；
8. 能生成 `TrialPlan`；
9. 能生成 `execution_input`；
10. 能设置 `ready_for_execution`；
11. 失败时必须持久化失败记录；
12. 所有 API 返回统一响应结构；
13. 不出现任何由 LLM 生成的可执行代码；
14. 不执行训练。

### 22.2 前端验收标准

必须满足：

1. 页面中新增 Pipeline Generation 面板；
2. 可以点击生成 Pipeline；
3. 可以重新生成 Pipeline；
4. 可以展示当前状态；
5. 可以展示 Pipeline 数量；
6. 可以展示 PipelineSpec 表格；
7. 可以展示 TrialPlan；
8. 可以展示 Component Binding Result；
9. 可以展示 Artifact Manifest；
10. 可以展示 Validation / Safety 结果；
11. 可以展示 Execution Input；
12. 可以查看完整 JSON；
13. 错误信息清晰可读。

### 22.3 安全验收标准

必须满足：

1. LLM 输出不可直接进入执行模块；
2. 所有模型必须来自 Model Registry；
3. 所有 HPO 方法必须来自 HPO Registry；
4. 所有 Pipeline Template 必须来自系统模板；
5. 所有 artifact 路径必须经过校验；
6. `ready_for_execution` 只能由系统 Validator 设置；
7. 本模块不得调用训练逻辑。

---

## 23. 推荐实现优先级

### P0：必须实现

1. `pipeline_generation` 后端模块目录；
2. `PipelineGeneration` 数据表；
3. `context_builder`；
4. `artifact_resolver`；
5. `component_binder`；
6. `pipeline_spec_builder`；
7. `trial_plan_builder`；
8. `pipeline_validator`；
9. `execution_input_builder`；
10. 核心 API；
11. 前端主面板；
12. PipelineSpec 表格；
13. ExecutionInput 展示。

### P1：建议实现

1. LLM Pipeline Review；
2. Safety Check 独立展示；
3. Summary API；
4. 更详细的 artifact metadata 校验；
5. Pipeline Template Registry；
6. Metric Registry。

### P2：后续迭代

1. 支持更多 Pipeline Profile；
2. 支持 Pipeline 可视化 DAG；
3. 支持资源估算；
4. 支持任务历史 Pipeline 对比；
5. 支持实验复现配置导出；
6. 支持与 Pipeline Execution 的更细粒度状态联动。

---

## 24. 与后续模块的交付契约

### 24.1 给 Pipeline Execution and Training 的输入契约

下游模块只应依赖：

```text
PipelineGeneration.execution_input_json
```

不应重新读取和拼接：

* WorkflowPlan；
* ModelSearchContext；
* ModelSearchPlan；
* FeaturePreprocessing；
* FeatureEngineering。

这样可以保证模块边界清晰。

### 24.2 下游执行模块的最小消费字段

下游至少需要：

| 字段                           | 说明              |
| ---------------------------- | --------------- |
| `pipeline_generation_id`     | 当前生成记录          |
| `pipeline_bundle_id`         | Pipeline Bundle |
| `model_ready_matrix_path`    | 训练数据            |
| `preprocessor_artifact_path` | 预处理管道           |
| `target_column`              | 目标列             |
| `feature_columns`            | 特征列             |
| `pipeline_specs`             | 待执行模型           |
| `trial_plan`                 | trial 展开规则      |
| `validation_plan`            | 验证策略            |
| `evaluation_plan`            | 指标策略            |
| `ready_for_execution`        | 是否允许执行          |

---

## 25. 风险与应对

### 25.1 风险：Pipeline Generation 和 Execution 边界混淆

应对：

* 本模块只生成 Spec；
* 训练逻辑全部放到下游；
* API 命名避免使用 `run`、`train`；
* 状态命名使用 `generated` 而不是 `executed`。

### 25.2 风险：LLM 输出越权

应对：

* LLM Review 只允许输出审查意见；
* 所有输出经过 validator；
* 不允许 LLM 修改 PipelineSpec；
* 不允许 LLM 输出代码。

### 25.3 风险：上游计划变化导致下游不兼容

应对：

* `PipelineGeneration` 记录必须绑定具体 `model_search_plan_id`；
* 重新生成产生新记录；
* 不覆盖旧记录；
* execution_input 中保留上游 plan 引用。

### 25.4 风险：Artifact 路径失效

应对：

* artifact_resolver 必须检查路径；
* 不存在则失败；
* 前端明确展示缺失路径；
* 不允许进入 ready 状态。

---

## 26. 总结

**Executable Pipeline Generation** 是 MLAgent 从“规划系统”进入“执行系统”的关键过渡模块。

它的核心价值是：

```text
把 Model Search Plan 转换为受控、可校验、可复现、可交给执行器消费的 PipelineBundle / PipelineSpec / ExecutionInput。
```

本模块必须坚持：

```text
LLM 深度参与，但不直接生成可执行代码；
系统 Registry + Validator + Template 负责最终执行规格；
Pipeline Generation 只生成，不训练；
Pipeline Execution 才执行。
```

完成本模块后，MLAgent 的链路将从：

```text
模型搜索计划生成
```

推进到：

```text
可执行训练规格生成
```

为下一步 **Pipeline Execution and Training** 奠定稳定、安全、可控的输入基础。
