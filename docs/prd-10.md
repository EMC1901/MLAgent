# PRD：Pipeline Execution and Training 模块

> 项目名称：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：10
> 模块名称：Pipeline Execution and Training
> 上游模块：Executable Pipeline Generation
> 下游模块：Metric Evaluation
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0
> 输出格式：Markdown

---

## 1. 背景与上下文

当前 MLAgent 已经完成 9 个核心模块，系统已经能够从用户任务规格出发，依次完成任务理解、数据集画像、工作流规划、特征工程、特征预处理、模型搜索上下文更新、模型与 HPO 搜索规划，以及可执行 Pipeline 生成。附件中明确说明，当前尚未实现的后续模块包括 **Pipeline Execution、Metric Evaluation、Result Diagnosis、Report Generation**，其中下一步高优先级任务是实现 **Pipeline Execution**，并且该模块应直接消费模块九输出的 `execution_input`，而不是重新构建 Pipeline。

模块九 **Executable Pipeline Generation** 已经输出完整的 `Pipeline Bundle + Execution Input`，其中包含 `pipeline_specs`、`trial_plan`、`validation_plan`、`evaluation_plan` 和 `execution_constraints` 等下游执行所需信息。附件也明确指出，Pipeline Generation 的 `ready_for_execution` 由 System Validator、Safety Checker、Artifact Manifest 决定，LLM Advisory Review 不参与执行审批。

因此，本模块的核心职责是：

> 在系统受控执行器中，读取 Pipeline Generation 输出的 `execution_input`，按 PipelineSpec 和 TrialPlan 执行模型训练与 HPO trial，记录训练过程、保存训练产物，并将结构化训练结果交给下一步 Metric Evaluation 模块。

---

## 2. 模块定位

### 2.1 一句话定义

**Pipeline Execution and Training** 是 MLAgent 中负责实际执行模型训练和 HPO trial 的受控执行模块，它消费上游 `execution_input`，在系统内置 Executor、Model Factory、HPO Runner、Validation Splitter 和 Artifact Manager 的控制下完成训练，但不负责最终指标裁决、结果诊断和报告生成。

---

### 2.2 在整体链路中的位置

```text
Task Specification
  ↓
LLM-based Task Interpretation
  ↓
Dataset Loading, Checking, and Profiling
  ↓
LLM-guided Workflow Planning
  ↓
Automated Feature Engineering
  ↓
Feature Preprocessing
  ↓
Model Search Context Update
  ↓
Automated Model and HPO Search
  ↓
Executable Pipeline Generation
  ↓
Pipeline Execution and Training   ← 当前模块
  ↓
Metric Evaluation
  ↓
Result Diagnosis
  ↓
Report Generation
```

---

### 2.3 当前模块与上游模块的关系

上游模块九已经完成：

* 生成 Pipeline Bundle；
* 生成 PipelineSpec；
* 生成 TrialPlan；
* 绑定模型、HPO、验证策略、评价策略；
* 校验 artifact 路径；
* 完成 Safety Check；
* 生成下游 `execution_input`；
* 设置 `ready_for_execution`。

当前模块只消费：

```text
PipelineGeneration.execution_input_json
```

当前模块不重新执行：

* 模型搜索；
* HPO 搜索空间生成；
* Pipeline Spec 构建；
* LLM Advisory Review；
* Pipeline 安全审查；
* Pipeline Template 绑定。

---

## 3. 核心设计原则

### 3.1 Controlled Executor 是唯一执行入口

本模块是第一个真正执行训练逻辑的模块，因此必须严格保证：

```text
只有系统内置 Controlled Executor 可以执行训练。
```

不允许：

* LLM 生成训练代码；
* LLM 直接调用模型；
* LLM 直接运行 HPO；
* 用户输入任意 Python 代码；
* 根据字符串动态执行训练逻辑；
* 绕过 Registry 实例化模型；
* 绕过 `execution_input` 自行拼接训练流程。

---

### 3.2 LLM 深度参与但不直接执行

本模块中 LLM 的定位可以是：

* 训练前风险提示；
* trial 执行策略解释；
* 训练失败原因辅助归类；
* 异常日志总结；
* 后续优化建议生成。

但 LLM 不能：

* 返回可执行代码；
* 修改训练逻辑；
* 动态创建模型；
* 动态修改 HPO trial；
* 修改 artifact 路径；
* 修改 `ready_for_metric_evaluation`；
* 直接决定最佳模型；
* 直接写入训练结果。

---

### 3.3 本模块负责训练，不负责评价裁决

本模块可以在训练过程中产生验证集预测值、fold 结果、trial 结果、训练耗时、模型 artifact 等数据，但不负责最终模型排名和指标裁决。

本模块可以记录：

```text
trial_id
pipeline_spec_id
model_id
fold_index
train_status
prediction_path
model_artifact_path
raw_metric_values
```

但最终统一指标计算、排序、best model 选择，应由下游 **Metric Evaluation** 模块完成。

---

### 3.4 训练结果必须可复现

每一次执行必须记录：

* 上游 `pipeline_generation_id`；
* 使用的 `execution_input` 快照；
* 数据 artifact 路径；
* PipelineSpec 快照；
* TrialPlan 快照；
* random_state；
* train/validation split 信息；
* 模型参数；
* HPO 参数；
* 训练开始时间和结束时间；
* 运行环境元信息；
* 产物路径；
* 异常信息。

---

## 4. 产品目标

### 4.1 MVP 目标

本模块 MVP 需要实现：

1. 从最新或指定 `PipelineGeneration` 中读取 `execution_input_json`；
2. 校验 `ready_for_execution = true`；
3. 加载 `model_ready_features.parquet`；
4. 根据 `target_column` 和 `feature_columns` 构建 X / y；
5. 根据 `validation_plan` 生成训练/验证 split；
6. 根据 `pipeline_specs` 执行 baseline 和候选模型训练；
7. 根据 `trial_plan` 执行 HPO trial；
8. 为每个 trial 保存训练结果；
9. 为每个 trial 保存预测结果；
10. 为每个成功 trial 保存模型 artifact；
11. 记录每个 pipeline、trial、fold 的状态；
12. 生成 `PipelineExecutionResult`；
13. 生成下游 `metric_evaluation_input`；
14. 前端展示执行状态、进度、trial 列表、训练日志、产物路径和错误信息。

---

### 4.2 非目标

MVP 阶段不做：

1. 不重新生成 PipelineSpec；
2. 不重新选择模型；
3. 不重新设计 HPO 搜索空间；
4. 不修改 Feature Preprocessing 产物；
5. 不执行特征工程；
6. 不做最终指标排名；
7. 不做最终 best model 决策；
8. 不做 Result Diagnosis；
9. 不生成最终报告；
10. 不支持用户上传自定义训练脚本；
11. 不支持任意 Python 代码执行；
12. 不支持分布式训练；
13. 不支持 GPU 训练调度；
14. 不支持在线推理服务部署。

---

## 5. 用户故事

### 5.1 材料科学研究者视角

作为材料科学研究者，我希望系统能够自动执行上一步生成的候选 Pipeline，完成 baseline、候选模型和 HPO trial 的训练，让我无需手写训练代码。

---

### 5.2 后端开发者视角

作为后端开发者，我希望本模块只依赖 `execution_input`，避免重复读取和拼接上游多个模块的数据，从而保证模块边界清晰、调试简单。

---

### 5.3 前端用户视角

作为用户，我希望在界面上看到：

* 当前是否可以开始训练；
* 正在执行哪些模型；
* 每个模型训练是否成功；
* HPO trial 执行了多少；
* 哪些 trial 失败；
* 失败原因是什么；
* 训练产物保存在哪里；
* 是否可以进入 Metric Evaluation。

---

### 5.4 AI Agent 系统视角

作为 AI Agent 系统，我希望 LLM 可以辅助解释训练过程和失败原因，但不能直接控制执行逻辑，真正的训练必须由系统内置 Controlled Executor 完成。

---

## 6. 模块边界

### 6.1 与 Pipeline Generation 的边界

Pipeline Generation 负责：

* 生成 PipelineBundle；
* 生成 PipelineSpec；
* 生成 TrialPlan；
* 生成 ExecutionInput；
* 完成 Pipeline 校验和安全检查；
* 设置 `ready_for_execution`。

Pipeline Execution 负责：

* 消费 ExecutionInput；
* 加载训练数据；
* 实例化注册模型；
* 执行训练；
* 执行 trial；
* 保存模型 artifact；
* 保存预测结果；
* 输出训练执行结果。

Pipeline Execution 不负责：

* 重新生成 PipelineSpec；
* 修改 TrialPlan；
* 修改 PipelineBundle；
* 修改上游 `ready_for_execution`。

---

### 6.2 与 Metric Evaluation 的边界

Pipeline Execution 可以产生：

* 验证集预测值；
* fold predictions；
* trial predictions；
* 基础 raw metrics；
* 训练耗时；
* 模型产物；
* trial 状态。

Metric Evaluation 负责：

* 标准化计算指标；
* 聚合 cross-validation 指标；
* 进行模型排序；
* 标记 best trial / best model；
* 生成 metric summary；
* 输出下游 Result Diagnosis 输入。

当前模块不直接做最终排名。

---

### 6.3 与 Result Diagnosis 的边界

Pipeline Execution 可以记录训练失败、过慢、收敛异常、预测异常等原始事实。

Result Diagnosis 负责：

* 分析为什么某些模型表现差；
* 判断是否欠拟合/过拟合；
* 提出下一轮优化建议；
* 生成 LLM 诊断报告。

当前模块不做主观诊断。

---

### 6.4 与 Report Generation 的边界

Pipeline Execution 不生成用户最终报告。

它只提供结构化训练数据和 artifact manifest。

---

## 7. 输入设计

### 7.1 API 请求输入

接口：

```text
POST /api/pipeline-executions/{task_id}
```

请求字段：

| 字段                       | 类型      | 必填 | 说明                                                  |
| ------------------------ | ------- | -: | --------------------------------------------------- |
| `force_rerun`            | boolean |  否 | 是否强制重新执行，默认 false                                   |
| `pipeline_generation_id` | string  |  否 | 指定使用某个 PipelineGeneration；为空则使用最新 ready 的记录         |
| `execution_mode`         | string  |  否 | `sequential` / `limited_parallel`，MVP 默认 sequential |
| `max_trials_override`    | integer |  否 | 可选，仅允许小于等于上游 trial 上限                               |
| `max_runtime_seconds`    | integer |  否 | 单次执行最大耗时限制                                          |
| `fail_fast`              | boolean |  否 | 某个 trial 失败后是否立即停止，默认 false                         |
| `save_trained_models`    | boolean |  否 | 是否保存每个成功 trial 的模型，默认 true                          |
| `save_predictions`       | boolean |  否 | 是否保存验证集预测结果，默认 true                                 |
| `notes`                  | string  |  否 | 用户备注，不影响执行逻辑                                        |

---

### 7.2 上游依赖输入

必须读取：

| 来源                     | 必需字段                                                                                                                                |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `PipelineGeneration`   | `id`, `task_id`, `status`, `ready_for_execution`, `execution_input_json`                                                            |
| `execution_input_json` | `pipeline_specs`, `trial_plan`, `validation_plan`, `evaluation_plan`, `model_ready_matrix_path`, `target_column`, `feature_columns` |
| `pipeline_specs`       | `pipeline_spec_id`, `model_id`, `model_family`, `hpo_enabled`, `search_space`, `fixed_params`, `execution_ready`                    |
| `trial_plan`           | `hpo_enabled`, `search_method`, `max_total_trials`, `trial_allocation`, `baseline_trial_policy`, `candidate_trial_policy`           |
| `validation_plan`      | `split_strategy`, `n_splits`, `random_state`, `shuffle`, `stratification_required`                                                  |
| `evaluation_plan`      | `primary_metric`, `secondary_metrics`, `metric_direction`                                                                           |

---

### 7.3 Artifact 输入

| Artifact                       | 来源                    | 用途                           |
| ------------------------------ | --------------------- | ---------------------------- |
| `model_ready_features.parquet` | Feature Preprocessing | 训练数据输入                       |
| `preprocessor.joblib`          | Feature Preprocessing | 记录和复现使用，MVP 训练可不重复 transform |
| `execution_input_json`         | Pipeline Generation   | 执行合同                         |
| `pipeline_bundle`              | Pipeline Generation   | 训练计划参考                       |

---

## 8. 输出设计

### 8.1 核心输出：PipelineExecutionResponse

字段建议：

| 字段                            | 类型          | 说明                                                                                 |
| ----------------------------- | ----------- | ---------------------------------------------------------------------------------- |
| `pipeline_execution_id`       | string      | 执行记录 ID，例如 `pe_xxxxxxxx`                                                           |
| `task_id`                     | string      | 任务 ID                                                                              |
| `pipeline_generation_id`      | string      | 上游 PipelineGeneration ID                                                           |
| `status`                      | string      | `running` / `completed` / `completed_with_warning` / `failed` / `partially_failed` |
| `execution_mode`              | string      | sequential / limited_parallel                                                      |
| `n_pipeline_specs`            | integer     | 待执行 Pipeline 数                                                                     |
| `n_trials_planned`            | integer     | 计划 trial 数                                                                         |
| `n_trials_completed`          | integer     | 成功完成 trial 数                                                                       |
| `n_trials_failed`             | integer     | 失败 trial 数                                                                         |
| `n_models_trained`            | integer     | 成功训练模型数量                                                                           |
| `started_at`                  | datetime    | 开始时间                                                                               |
| `finished_at`                 | datetime    | 结束时间                                                                               |
| `duration_seconds`            | float       | 总耗时                                                                                |
| `execution_summary`           | object      | 执行摘要                                                                               |
| `pipeline_run_results`        | array       | 每个 PipelineSpec 的执行结果                                                              |
| `trial_results`               | array       | 每个 trial 的执行结果                                                                     |
| `training_artifact_manifest`  | object      | 模型、预测、日志等产物路径                                                                      |
| `runtime_environment`         | object      | 运行环境信息                                                                             |
| `metric_evaluation_input`     | object      | 下游 Metric Evaluation 输入                                                            |
| `ready_for_metric_evaluation` | boolean     | 是否可进入指标评估                                                                          |
| `warnings`                    | array       | 警告                                                                                 |
| `error_message`               | string/null | 错误信息                                                                               |
| `created_at`                  | datetime    | 创建时间                                                                               |
| `updated_at`                  | datetime    | 更新时间                                                                               |

---

## 9. 核心数据结构设计

### 9.1 PipelineExecutionResult

用于描述一次完整执行。

```text
PipelineExecutionResult
  ├── pipeline_execution_id
  ├── task_id
  ├── pipeline_generation_id
  ├── execution_status
  ├── execution_summary
  ├── pipeline_run_results
  ├── trial_results
  ├── artifact_manifest
  ├── metric_evaluation_input
  └── ready_for_metric_evaluation
```

---

### 9.2 PipelineRunResult

每个 PipelineSpec 对应一个 PipelineRunResult。

字段建议：

| 字段                          | 类型          | 说明                                               |
| --------------------------- | ----------- | ------------------------------------------------ |
| `pipeline_run_id`           | string      | Pipeline 执行 ID                                   |
| `pipeline_spec_id`          | string      | 对应上游 PipelineSpec                                |
| `pipeline_role`             | string      | baseline / candidate / hpo_candidate             |
| `model_id`                  | string      | 模型 ID                                            |
| `model_family`              | string      | 模型族                                              |
| `status`                    | string      | pending / running / completed / failed / skipped |
| `hpo_enabled`               | boolean     | 是否执行 HPO                                         |
| `n_trials_planned`          | integer     | 计划 trial 数                                       |
| `n_trials_completed`        | integer     | 成功 trial 数                                       |
| `n_trials_failed`           | integer     | 失败 trial 数                                       |
| `best_trial_id`             | string/null | 本模块可选记录，但最终 best 由 Metric Evaluation 确认          |
| `model_artifact_paths`      | array       | 模型产物路径                                           |
| `prediction_artifact_paths` | array       | 预测结果路径                                           |
| `duration_seconds`          | float       | 执行耗时                                             |
| `warnings`                  | array       | 警告                                               |
| `error_message`             | string/null | 错误信息                                             |

---

### 9.3 TrialResult

每个具体训练试验对应一个 TrialResult。

字段建议：

| 字段                         | 类型          | 说明                                               |
| -------------------------- | ----------- | ------------------------------------------------ |
| `trial_id`                 | string      | Trial ID，例如 `trial_ridge_0001`                   |
| `pipeline_spec_id`         | string      | 所属 PipelineSpec                                  |
| `pipeline_run_id`          | string      | 所属 PipelineRun                                   |
| `model_id`                 | string      | 模型 ID                                            |
| `trial_index`              | integer     | trial 序号                                         |
| `trial_type`               | string      | baseline / fixed_params / hpo                    |
| `params`                   | object      | 本 trial 使用的模型参数                                  |
| `status`                   | string      | pending / running / completed / failed / skipped |
| `fold_results`             | array       | 每个 fold 的训练结果                                    |
| `prediction_artifact_path` | string/null | 预测结果路径                                           |
| `model_artifact_path`      | string/null | 模型保存路径                                           |
| `raw_metric_values`        | object      | 可选原始指标，仅供参考，最终以 Metric Evaluation 为准             |
| `started_at`               | datetime    | 开始时间                                             |
| `finished_at`              | datetime    | 结束时间                                             |
| `duration_seconds`         | float       | 耗时                                               |
| `error_message`            | string/null | 错误信息                                             |

---

### 9.4 FoldResult

如果使用 K-Fold 或交叉验证，应记录 fold 级结果。

| 字段                         | 类型          | 说明                 |
| -------------------------- | ----------- | ------------------ |
| `fold_index`               | integer     | fold 序号            |
| `train_size`               | integer     | 训练样本数              |
| `validation_size`          | integer     | 验证样本数              |
| `status`                   | string      | completed / failed |
| `prediction_artifact_path` | string      | 当前 fold 预测文件路径     |
| `model_artifact_path`      | string/null | 当前 fold 模型路径，可选    |
| `raw_metric_values`        | object      | 可选原始指标             |
| `duration_seconds`         | float       | fold 耗时            |
| `error_message`            | string/null | 错误信息               |

---

### 9.5 MetricEvaluationInput

下游 Metric Evaluation 的正式输入。

字段建议：

| 字段                            | 类型      | 说明                          |
| ----------------------------- | ------- | --------------------------- |
| `pipeline_execution_id`       | string  | 当前执行 ID                     |
| `pipeline_generation_id`      | string  | 上游生成 ID                     |
| `task_id`                     | string  | 任务 ID                       |
| `task_type`                   | string  | regression / classification |
| `target_column`               | string  | 目标列                         |
| `primary_metric`              | string  | 主指标                         |
| `metric_direction`            | string  | minimize / maximize         |
| `evaluation_plan`             | object  | 上游评价计划                      |
| `validation_plan`             | object  | 验证计划                        |
| `trial_results`               | array   | trial 级结果摘要                 |
| `prediction_artifacts`        | array   | 预测文件路径                      |
| `model_artifacts`             | array   | 模型文件路径                      |
| `ready_for_metric_evaluation` | boolean | 是否可进入评估                     |

---

## 10. 后端功能设计

### 10.1 推荐目录结构

建议新增：

```text
backend/app/modules/pipeline_execution/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── execution_input_loader.py
    ├── data_matrix_loader.py
    ├── execution_planner.py
    ├── validation_splitter.py
    ├── model_factory.py
    ├── hpo_trial_generator.py
    ├── controlled_executor.py
    ├── trial_runner.py
    ├── fold_runner.py
    ├── prediction_writer.py
    ├── training_artifact_manager.py
    ├── runtime_monitor.py
    ├── execution_state_tracker.py
    ├── metric_input_builder.py
    └── builder.py
```

---

### 10.2 各文件职责说明

| 文件                             | 职责                                             |
| ------------------------------ | ---------------------------------------------- |
| `api.py`                       | 提供 Pipeline Execution 相关 REST API              |
| `service.py`                   | 编排主流程                                          |
| `model.py`                     | 定义 PipelineExecution 数据表                       |
| `repository.py`                | 数据库 CRUD                                       |
| `schemas.py`                   | 请求、响应和内部 DTO                                   |
| `enums.py`                     | 状态、执行模式、trial 类型等枚举                            |
| `exceptions.py`                | 专用异常                                           |
| `context_builder.py`           | 校验上游 PipelineGeneration 并构建执行上下文               |
| `execution_input_loader.py`    | 读取并校验 execution_input_json                     |
| `data_matrix_loader.py`        | 加载 model-ready parquet                         |
| `execution_planner.py`         | 将 PipelineSpec + TrialPlan 展开为 executable runs |
| `validation_splitter.py`       | 根据 validation_plan 生成 split                    |
| `model_factory.py`             | 根据 Model Registry 安全创建模型实例                     |
| `hpo_trial_generator.py`       | 根据 search_space 和 HPO 方法生成 trial 参数            |
| `controlled_executor.py`       | 唯一训练执行入口                                       |
| `trial_runner.py`              | 执行单个 trial                                     |
| `fold_runner.py`               | 执行单个 fold                                      |
| `prediction_writer.py`         | 保存预测结果                                         |
| `training_artifact_manager.py` | 保存模型、日志、manifest                               |
| `runtime_monitor.py`           | 记录耗时、资源、状态                                     |
| `execution_state_tracker.py`   | 维护 running/completed/failed 状态                 |
| `metric_input_builder.py`      | 构建下游 Metric Evaluation 输入                      |
| `builder.py`                   | 构建最终响应对象                                       |

---

## 11. 后端主流程

### 11.1 主流程概览

```text
PipelineExecutionService.create_pipeline_execution(task_id, request)
    ↓
1. build_execution_context()
    ↓
2. load_execution_input()
    ↓
3. validate_execution_readiness()
    ↓
4. load_model_ready_matrix()
    ↓
5. build_X_y()
    ↓
6. create_validation_splits()
    ↓
7. expand_execution_plan()
    ↓
8. execute_pipeline_runs()
    ↓
9. run_trials_and_folds()
    ↓
10. save_models_and_predictions()
    ↓
11. build_training_artifact_manifest()
    ↓
12. build_metric_evaluation_input()
    ↓
13. persist_execution_result()
```

---

### 11.2 Step 1：构建执行上下文

`context_builder.py` 负责：

* 根据 `task_id` 获取最新 PipelineGeneration；
* 或根据请求中的 `pipeline_generation_id` 获取指定记录；
* 校验 `PipelineGeneration.status in generated / generated_with_warning`；
* 校验 `PipelineGeneration.ready_for_execution = true`；
* 读取 `execution_input_json`；
* 记录上游 ID 快照；
* 构建执行上下文。

失败场景：

| 场景                         | error_code                      |
| -------------------------- | ------------------------------- |
| 找不到 PipelineGeneration     | `PIPELINE_GENERATION_NOT_FOUND` |
| PipelineGeneration 未 ready | `PIPELINE_GENERATION_NOT_READY` |
| execution_input 缺失         | `EXECUTION_INPUT_MISSING`       |
| execution_input 格式错误       | `EXECUTION_INPUT_INVALID`       |

---

### 11.3 Step 2：加载 Execution Input

`execution_input_loader.py` 负责：

* 校验必填字段；
* 校验 `pipeline_specs` 非空；
* 校验 `trial_plan` 存在；
* 校验 `validation_plan` 存在；
* 校验 `evaluation_plan` 存在；
* 校验 `feature_columns` 和 `target_column` 非空；
* 校验每个 PipelineSpec 的 `execution_ready = true`。

注意：该步骤只校验结构，不做训练。

---

### 11.4 Step 3：加载 Model-ready Matrix

`data_matrix_loader.py` 负责：

* 从 `model_ready_matrix_path` 加载 parquet；
* 校验文件存在；
* 校验路径安全；
* 校验 feature columns 存在；
* 校验 target column 存在；
* 校验 X/y 样本数一致；
* 校验没有明显非法值；
* 返回内存中的训练矩阵。

MVP 可直接使用 pandas DataFrame，但必须注意：

* 不修改原始 artifact；
* 不覆盖上游文件；
* 不在原路径写入训练结果。

---

### 11.5 Step 4：构建验证 split

`validation_splitter.py` 根据 `validation_plan` 生成 split：

MVP 支持：

| split_strategy      | 说明                          |
| ------------------- | --------------------------- |
| `train_test_split`  | 单次训练验证划分                    |
| `k_fold`            | K 折交叉验证                     |
| `stratified_k_fold` | 分类任务分层 K 折                  |
| `holdout`           | 与 train_test_split 类似，可作为别名 |

需要保证：

* 使用上游 `random_state`；
* 分类任务支持 stratification；
* 回归任务不使用 stratified split；
* 每个 fold 记录 train indices 和 validation indices 的摘要；
* MVP 不建议保存完整 index 列表到前端，但可保存在 artifact metadata 中以便复现。

---

### 11.6 Step 5：展开执行计划

`execution_planner.py` 负责将：

```text
pipeline_specs + trial_plan
```

展开为：

```text
PipelineRunPlan + TrialRunPlan
```

例如：

```text
ridge hpo_candidate
    ├── trial_0001
    ├── trial_0002
    └── trial_0003

dummy_mean baseline
    └── trial_0001
```

规则：

* baseline 默认执行 1 次；
* fixed params candidate 默认执行 1 次；
* hpo_candidate 根据 `trial_allocation` 执行多个 trial；
* 如果 `max_trials_override` 存在，只能减少，不能超过上游计划；
* 如果某个 PipelineSpec `execution_ready = false`，必须跳过并记录原因；
* 如果 `include_baselines` 在上游已关闭，则不额外补 baseline。

---

### 11.7 Step 6：模型实例化

`model_factory.py` 负责根据 `model_id` 创建模型实例。

必须遵守：

* 只能实例化 Model Registry 中存在的模型；
* 只能使用系统内置模型映射；
* 参数只能来自 `fixed_params` 或 trial generator；
* 不接受 LLM 输出代码；
* 不接受用户传入类名；
* 不使用动态 import；
* 不使用 eval/exec；
* 对不支持的模型返回明确错误。

MVP 支持模型建议：

| model_id                       | MVP 支持建议  |
| ------------------------------ | --------- |
| `dummy_mean`                   | 支持        |
| `linear_regression` / `linear` | 支持        |
| `ridge`                        | 支持        |
| `lasso`                        | 支持        |
| `elastic_net`                  | 支持        |
| `random_forest`                | 支持        |
| `gradient_boosting`            | 支持        |
| `xgboost`                      | 可选，依赖安装状态 |
| `svr`                          | 支持        |
| `knn`                          | 支持        |

如果某个模型依赖缺失，应：

* 标记该 trial skipped 或 failed；
* 记录 `DEPENDENCY_MISSING`；
* 不影响其他模型继续执行，除非 `fail_fast = true`。

---

### 11.8 Step 7：HPO Trial 生成

`hpo_trial_generator.py` 负责根据上游 search space 生成 trial 参数。

MVP 支持：

| HPO 方法               | MVP 策略       |
| -------------------- | ------------ |
| `random_search`      | 必须支持         |
| `grid_search`        | 可支持，注意组合数量上限 |
| `optuna_tpe`         | 可作为后续增强      |
| `bayesian`           | 后续增强         |
| `successive_halving` | 后续增强         |

建议 MVP 先实现：

```text
random_search + grid_search
```

其他方法可以：

* 标记为 planned；
* 或 fallback 到 random_search；
* 但必须在结果中记录 fallback_reason。

注意：

当前模块执行 HPO trial，但不直接最终裁决“最佳模型”。它可以记录每个 trial 的 raw result，供 Metric Evaluation 统一裁决。

---

### 11.9 Step 8：执行 trial 和 fold

`controlled_executor.py` 是唯一执行入口。

每个 trial 执行流程：

```text
读取 trial 参数
    ↓
创建模型实例
    ↓
遍历 validation splits
    ↓
训练 fold model
    ↓
生成 validation predictions
    ↓
保存 fold prediction
    ↓
记录 fold result
    ↓
汇总 trial result
    ↓
保存 trial model artifact，可选
```

注意：

* 对 K-Fold，建议每个 fold 保存预测；
* 是否保存每个 fold 模型可配置；
* 对 holdout，可保存单个模型；
* 模型 artifact 用于复现和后续报告；
* predictions 是下游 Metric Evaluation 的核心输入。

---

### 11.10 Step 9：保存训练产物

`training_artifact_manager.py` 负责保存：

| 产物                 | 建议路径                                                                                      |
| ------------------ | ----------------------------------------------------------------------------------------- |
| execution manifest | `/app/artifacts/training/{pipeline_execution_id}/manifest.json`                           |
| trial results      | `/app/artifacts/training/{pipeline_execution_id}/trial_results.json`                      |
| predictions        | `/app/artifacts/training/{pipeline_execution_id}/predictions/{trial_id}_fold_{k}.parquet` |
| trained models     | `/app/artifacts/training/{pipeline_execution_id}/models/{trial_id}_fold_{k}.joblib`       |
| logs               | `/app/artifacts/training/{pipeline_execution_id}/logs/execution.log`                      |
| split metadata     | `/app/artifacts/training/{pipeline_execution_id}/splits/split_metadata.json`              |

路径要求：

* 必须位于 training artifact 根目录；
* 不允许路径逃逸；
* 不覆盖其他 execution 产物；
* 每次执行生成独立目录。

---

### 11.11 Step 10：构建 Metric Evaluation Input

`metric_input_builder.py` 负责生成下游输入。

只有满足以下条件时：

```text
n_trials_completed > 0
至少存在一个 prediction_artifact
target_column 有效
evaluation_plan 有效
```

才设置：

```text
ready_for_metric_evaluation = true
```

---

## 12. 数据库设计

### 12.1 新增表：PipelineExecution

表名建议：

```text
pipeline_execution
```

字段设计：

| 字段                             | 类型       | 索引    | 说明                                                                       |
| ------------------------------ | -------- | ----- | ------------------------------------------------------------------------ |
| `id`                           | string   | PK    | `pe_{uuid8}`                                                             |
| `task_id`                      | string   | index | 任务 ID                                                                    |
| `pipeline_generation_id`       | string   | index | 上游 PipelineGeneration ID                                                 |
| `status`                       | string   | index | running / completed / completed_with_warning / partially_failed / failed |
| `execution_mode`               | string   |       | sequential / limited_parallel                                            |
| `task_type`                    | string   | index | regression / classification                                              |
| `target_column`                | string   |       | 目标列                                                                      |
| `primary_metric`               | string   |       | 主指标                                                                      |
| `n_pipeline_specs`             | integer  |       | Pipeline 数量                                                              |
| `n_trials_planned`             | integer  |       | 计划 trial 数                                                               |
| `n_trials_completed`           | integer  |       | 成功 trial 数                                                               |
| `n_trials_failed`              | integer  |       | 失败 trial 数                                                               |
| `n_models_trained`             | integer  |       | 成功训练模型数量                                                                 |
| `ready_for_metric_evaluation`  | boolean  | index | 是否可进入指标评估                                                                |
| `training_artifact_dir`        | string   |       | 训练产物目录                                                                   |
| `execution_json`               | JSONB    |       | 完整执行结果                                                                   |
| `metric_evaluation_input_json` | JSONB    |       | 下游输入                                                                     |
| `runtime_log_json`             | JSONB    |       | 运行日志摘要                                                                   |
| `error_message`                | string   |       | 失败原因                                                                     |
| `started_at`                   | datetime | index | 开始时间                                                                     |
| `finished_at`                  | datetime |       | 结束时间                                                                     |
| `created_at`                   | datetime | index | 创建时间                                                                     |
| `updated_at`                   | datetime |       | 更新时间                                                                     |

---

## 13. 状态设计

### 13.1 PipelineExecutionStatus

| 状态                       | 说明                         |
| ------------------------ | -------------------------- |
| `pending`                | 已创建执行记录，尚未开始               |
| `running`                | 正在执行                       |
| `completed`              | 全部计划 trial 成功              |
| `completed_with_warning` | 执行成功，但存在非致命警告              |
| `partially_failed`       | 部分 trial 失败，但至少一个 trial 成功 |
| `failed`                 | 全部失败或关键准备失败                |
| `cancelled`              | 预留，MVP 可不实现                |

---

### 13.2 TrialStatus

| 状态          | 说明             |
| ----------- | -------------- |
| `pending`   | 待执行            |
| `running`   | 执行中            |
| `completed` | 成功完成           |
| `failed`    | 执行失败           |
| `skipped`   | 因依赖缺失或配置不支持被跳过 |

---

### 13.3 ready_for_metric_evaluation 规则

| 条件                     | ready_for_metric_evaluation |
| ---------------------- | --------------------------- |
| 至少一个 trial 成功，且预测文件存在  | true                        |
| 所有 trial 均失败           | false                       |
| prediction artifact 缺失 | false                       |
| evaluation_plan 缺失     | false                       |
| target 信息缺失            | false                       |
| 训练被中断                  | false                       |

---

## 14. API 设计

### 14.1 创建 Pipeline Execution

```text
POST /api/pipeline-executions/{task_id}
```

说明：

* 根据最新或指定 PipelineGeneration 执行训练；
* 如果已有 completed 记录且 `force_rerun = false`，可返回最新结果；
* 如果 `force_rerun = true`，创建新执行记录。

---

### 14.2 获取指定执行结果

```text
GET /api/pipeline-executions/{pipeline_execution_id}
```

返回完整执行结果。

---

### 14.3 获取任务最新执行结果

```text
GET /api/tasks/{task_id}/pipeline-execution
```

返回该任务最新执行记录。

---

### 14.4 重新执行

```text
POST /api/pipeline-executions/{task_id}/rerun
```

等价于 `force_rerun = true`。

---

### 14.5 获取执行摘要

```text
GET /api/pipeline-executions/{pipeline_execution_id}/summary
```

用于前端快速展示。

建议返回：

* execution id；
* status；
* n trials planned；
* n trials completed；
* n trials failed；
* ready_for_metric_evaluation；
* duration；
* warnings。

---

### 14.6 获取 trial 结果列表

```text
GET /api/pipeline-executions/{pipeline_execution_id}/trials
```

用于前端展示 trial table。

---

### 14.7 获取 Metric Evaluation Input

```text
GET /api/pipeline-executions/{pipeline_execution_id}/metric-evaluation-input
```

供下游 Metric Evaluation 或调试使用。

---

### 14.8 获取训练日志摘要

```text
GET /api/pipeline-executions/{pipeline_execution_id}/logs
```

MVP 可返回结构化日志摘要，不直接返回超长文本日志。

---

## 15. 后端安全设计

### 15.1 禁止动态代码执行

本模块绝对禁止：

```text
eval
exec
动态 import
执行用户脚本
执行 LLM 代码
执行 shell command
从字符串创建类
从任意路径加载模块
```

---

### 15.2 模型实例化安全

模型只能来自：

```text
Model Registry → Model Factory → Controlled Executor
```

不允许：

* 用户直接输入模型类名；
* LLM 输出模型类名；
* 使用未知模型；
* 使用未安装依赖但未检查的模型；
* 使用不支持当前 task_type 的模型。

---

### 15.3 路径安全

所有输入路径必须：

* 来自上游 artifact；
* 位于允许目录；
* 文件存在；
* 文件类型匹配；
* 不包含 `..`；
* 不允许写入上游 artifact 原目录。

所有输出路径必须：

```text
/app/artifacts/training/{pipeline_execution_id}/...
```

---

### 15.4 资源安全

MVP 应支持：

| 限制项                      | 说明               |
| ------------------------ | ---------------- |
| `max_total_trials`       | 不得超过上游 TrialPlan |
| `max_runtime_seconds`    | 超时停止或标记失败        |
| `max_parallel_trials`    | MVP 可固定为 1       |
| `memory warning`         | 可记录，不强制实现硬限制     |
| `model dependency check` | 依赖缺失时跳过或失败       |

---

## 16. LLM 参与设计

### 16.1 MVP 建议

MVP 阶段建议本模块 **默认不调用 LLM**，保证训练链路稳定。

可预留：

```text
LLM Execution Observer
```

用于未来：

* 总结失败原因；
* 解释 trial 异常；
* 生成非阻塞训练建议；
* 给 Result Diagnosis 提供上下文。

---

### 16.2 LLM 不允许参与的内容

即使未来启用 LLM，也不允许它：

* 修改 trial 参数；
* 修改 search space；
* 修改模型；
* 修改 split；
* 执行代码；
* 直接判定 best model；
* 修改 `ready_for_metric_evaluation`。

---

## 17. 前端功能设计

### 17.1 新增前端文件结构

建议新增：

```text
frontend/src/api/pipelineExecutionApi.ts

frontend/src/modules/pipelineExecution/
    ├── components/
    │   ├── PipelineExecutionPanel.tsx
    │   ├── ExecutionSummaryCard.tsx
    │   ├── PipelineRunTable.tsx
    │   ├── TrialResultTable.tsx
    │   ├── TrainingProgressCard.tsx
    │   ├── ArtifactManifestCard.tsx
    │   ├── RuntimeLogCard.tsx
    │   ├── MetricEvaluationInputCard.tsx
    │   └── PipelineExecutionJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

---

### 17.2 页面集成位置

当前前端为单页嵌入式面板结构。建议在 Pipeline Generation 面板之后增加：

```text
PipelineExecutionPanel
```

顺序：

```text
Task Specification
Task Interpretation
Dataset Profile
Workflow Plan
Feature Engineering
Feature Preprocessing
Model Search Context
Model Search Plan
Pipeline Generation
Pipeline Execution and Training   ← 新增
```

---

### 17.3 主面板功能

`PipelineExecutionPanel` 应提供：

| 功能                 | 说明          |
| ------------------ | ----------- |
| Run Training       | 开始执行训练      |
| Re-run Training    | 重新执行        |
| Load Latest        | 加载最新执行结果    |
| View Trial Results | 查看 trial 结果 |
| View Artifacts     | 查看模型与预测文件   |
| View Metric Input  | 查看下游输入      |
| View Full JSON     | 查看完整 JSON   |

---

### 17.4 前端展示区域

#### 17.4.1 Execution Summary

展示：

* Execution ID；
* 状态；
* PipelineGeneration ID；
* 计划 trial 数；
* 成功 trial 数；
* 失败 trial 数；
* 是否可进入 Metric Evaluation；
* 总耗时。

---

#### 17.4.2 Training Progress

MVP 可以采用静态刷新，不一定需要实时 WebSocket。

展示：

* pending；
* running；
* completed；
* failed；
* partially failed。

后续可升级为轮询或 SSE。

---

#### 17.4.3 Pipeline Run Table

表格字段：

| 列                | 说明                                   |
| ---------------- | ------------------------------------ |
| Pipeline Run ID  | 执行 ID                                |
| Pipeline Spec ID | 上游 Spec                              |
| Role             | baseline / candidate / hpo_candidate |
| Model            | 模型                                   |
| HPO              | 是否启用                                 |
| Planned Trials   | 计划 trial                             |
| Completed Trials | 完成 trial                             |
| Failed Trials    | 失败 trial                             |
| Status           | 状态                                   |
| Duration         | 耗时                                   |

---

#### 17.4.4 Trial Result Table

表格字段：

| 列               | 说明             |
| --------------- | -------------- |
| Trial ID        | Trial ID       |
| Model           | 模型             |
| Type            | baseline / hpo |
| Params          | 参数摘要           |
| Folds           | fold 数         |
| Status          | 状态             |
| Prediction Path | 预测文件           |
| Model Path      | 模型文件           |
| Duration        | 耗时             |
| Error           | 错误信息           |

---

#### 17.4.5 Artifact Manifest

展示：

* training artifact dir；
* model artifacts；
* prediction artifacts；
* logs；
* split metadata；
* manifest path。

---

#### 17.4.6 Metric Evaluation Input

展示：

* ready_for_metric_evaluation；
* prediction artifacts；
* trial results；
* evaluation plan；
* primary metric；
* metric direction。

---

## 18. 前端状态与交互

### 18.1 按钮启用规则

| 条件                              | Run Training            |
| ------------------------------- | ----------------------- |
| 无 task_id                       | disabled                |
| 无 PipelineGeneration            | disabled                |
| PipelineGeneration 未 ready      | disabled                |
| 已 running                       | loading / disabled      |
| 已 completed 且 force_rerun=false | 显示 Load Latest / Re-run |
| 上游 ready_for_execution=true     | enabled                 |

---

### 18.2 状态颜色建议

| 状态                                  | 颜色          |
| ----------------------------------- | ----------- |
| `pending`                           | default     |
| `running`                           | blue        |
| `completed`                         | green       |
| `completed_with_warning`            | orange      |
| `partially_failed`                  | orange      |
| `failed`                            | red         |
| `ready_for_metric_evaluation=true`  | green       |
| `ready_for_metric_evaluation=false` | red/default |

---

## 19. Artifact 设计

### 19.1 训练产物目录

建议根目录：

```text
/app/artifacts/training/{pipeline_execution_id}/
```

目录结构：

```text
training/{pipeline_execution_id}/
    ├── manifest.json
    ├── execution_result.json
    ├── metric_evaluation_input.json
    ├── trial_results.json
    ├── predictions/
    ├── models/
    ├── logs/
    └── splits/
```

---

### 19.2 Prediction Artifact

预测文件建议包含：

| 字段                 | 说明              |
| ------------------ | --------------- |
| `sample_id`        | 样本 ID           |
| `trial_id`         | trial ID        |
| `pipeline_spec_id` | PipelineSpec ID |
| `fold_index`       | fold            |
| `y_true`           | 真实值             |
| `y_pred`           | 预测值             |
| `split`            | validation/test |
| `model_id`         | 模型 ID           |

分类任务可扩展：

* `y_pred_label`
* `y_pred_proba`
* `class_labels`

---

### 19.3 Model Artifact

模型 artifact 建议使用 joblib 保存。

注意：

* 每个模型路径必须记录；
* 如果不保存模型，也要记录 `save_trained_models=false`；
* 如果某个模型无法序列化，应记录 warning，不应导致整个执行失败，除非没有任何有效结果。

---

## 20. 异常设计

建议新增异常：

| 异常类                                   | error_code                             | 场景                      |
| ------------------------------------- | -------------------------------------- | ----------------------- |
| `PipelineExecutionNotFoundException`  | `PIPELINE_EXECUTION_NOT_FOUND`         | 找不到执行记录                 |
| `PipelineGenerationRequiredException` | `PIPELINE_GENERATION_REQUIRED`         | 缺少上游 PipelineGeneration |
| `PipelineGenerationNotReadyException` | `PIPELINE_GENERATION_NOT_READY`        | 上游未 ready               |
| `ExecutionInputInvalidException`      | `EXECUTION_INPUT_INVALID`              | execution_input 格式错误    |
| `TrainingDataLoadException`           | `TRAINING_DATA_LOAD_FAILED`            | 训练数据加载失败                |
| `ValidationSplitException`            | `VALIDATION_SPLIT_FAILED`              | 数据划分失败                  |
| `ModelInstantiationException`         | `MODEL_INSTANTIATION_FAILED`           | 模型实例化失败                 |
| `TrialGenerationException`            | `TRIAL_GENERATION_FAILED`              | trial 参数生成失败            |
| `TrialExecutionException`             | `TRIAL_EXECUTION_FAILED`               | 单个 trial 执行失败           |
| `TrainingArtifactSaveException`       | `TRAINING_ARTIFACT_SAVE_FAILED`        | 训练产物保存失败                |
| `MetricEvaluationInputBuildException` | `METRIC_EVALUATION_INPUT_BUILD_FAILED` | 下游输入构建失败                |

---

## 21. MVP 验收标准

### 21.1 后端验收标准

必须满足：

1. 可以通过 API 启动 Pipeline Execution；
2. 必须校验上游 `ready_for_execution = true`；
3. 必须只消费 `execution_input_json`；
4. 能加载 model-ready parquet；
5. 能根据 feature columns 和 target column 构建训练数据；
6. 能执行至少 baseline 模型训练；
7. 能执行至少 ridge / lasso / elastic_net 等基础模型训练；
8. 能执行 random_search HPO trial；
9. 能保存预测结果；
10. 能保存模型 artifact；
11. 能记录 trial 成功和失败；
12. 能生成 `metric_evaluation_input`；
13. 失败时必须持久化失败记录；
14. 不允许 LLM 生成或执行训练代码；
15. 不允许动态执行代码；
16. 不允许重新生成 PipelineSpec。

---

### 21.2 前端验收标准

必须满足：

1. 新增 Pipeline Execution 面板；
2. 可以点击 Run Training；
3. 可以点击 Re-run Training；
4. 可以展示执行状态；
5. 可以展示 trial 计划和结果；
6. 可以展示模型训练成功/失败数量；
7. 可以展示 artifact 路径；
8. 可以展示是否 ready for Metric Evaluation；
9. 可以展示错误信息；
10. 可以查看完整 JSON。

---

### 21.3 安全验收标准

必须满足：

1. 模型只能来自 Model Registry；
2. HPO trial 只能来自上游 search space；
3. 不允许 eval/exec/import 动态逻辑；
4. 不允许执行用户脚本；
5. 不允许 LLM 修改执行逻辑；
6. 不允许写入未授权目录；
7. 不允许覆盖上游 artifact；
8. 训练失败必须可追踪。

---

## 22. 推荐实现优先级

### P0：必须完成

1. 后端 `pipeline_execution` 模块目录；
2. `PipelineExecution` 数据表；
3. `context_builder`；
4. `execution_input_loader`；
5. `data_matrix_loader`；
6. `validation_splitter`；
7. `model_factory`；
8. `controlled_executor`；
9. `trial_runner`；
10. `training_artifact_manager`；
11. `metric_input_builder`；
12. 核心 API；
13. 前端主面板；
14. Trial Result 表格；
15. Artifact 展示。

---

### P1：建议完成

1. limited_parallel 执行模式；
2. grid_search；
3. 训练日志摘要；
4. 运行耗时统计；
5. 简单资源监控；
6. trial 失败后继续执行；
7. 支持跳过依赖缺失模型；
8. 支持前端轮询刷新。

---

### P2：后续迭代

1. Optuna TPE；
2. Successive Halving；
3. SSE 实时日志；
4. 任务取消；
5. 断点续跑；
6. 分布式训练；
7. GPU 支持；
8. 更细粒度资源限制；
9. LLM Execution Observer；
10. 与 Result Diagnosis 深度联动。

---

## 23. 总结

**Pipeline Execution and Training** 是 MLAgent 从“生成可执行规格”进入“真实训练执行”的关键模块。

它的核心价值是：

```text
把 PipelineGeneration 输出的 execution_input 转换为真实、可追踪、可复现的模型训练结果。
```

本模块必须坚持：

```text
只消费 execution_input；
只由 Controlled Executor 执行；
只使用 Registry 中的模型；
只保存结构化训练产物；
不重新规划；
不让 LLM 直接执行；
不做最终指标裁决。
```

完成本模块后，MLAgent 将具备从任务输入到模型训练产物生成的完整自动化能力，并为下一步 **Metric Evaluation** 提供稳定、结构化、可复现的输入基础。
