# PRD：Metric Evaluation 模块

> 项目名称：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：11
> 模块名称：Metric Evaluation
> 上游模块：Pipeline Execution and Training
> 下游模块：Result Diagnosis
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0
> 输出格式：Markdown

---

## 1. 背景与上下文

当前 MLAgent 已完成从 **Task Specification → LLM-based Task Interpretation → Dataset Loading, Checking, and Profiling → Workflow Planning → Feature Engineering → Feature Preprocessing → Model Search Context Update → Automated Model and HPO Search → Executable Pipeline Generation → Pipeline Execution and Training** 的完整链路。根据附件说明，当前项目已完成十个核心业务模块，尚未实现的后续模块包括 **Metric Evaluation、Result Diagnosis、Report Generation**。其中，Metric Evaluation 需要消费模块十输出的 `metric_evaluation_input`，对模型训练结果进行统一、标准化、可复现的指标评估。

模块十 **Pipeline Execution and Training** 已经完成真实训练执行，输出内容包括：

* `PipelineExecutionResponse`
* `pipeline_run_results`
* `trial_results`
* `fold_results`
* `training_artifact_manifest`
* `prediction_artifact_paths`
* `model_artifact_paths`
* `runtime_environment`
* `metric_evaluation_input`
* `ready_for_metric_evaluation`

附件中明确指出，模块十的 `metric_input_builder.build_metric_evaluation_input()` 会构建下游 Metric Evaluation 合同，包含 `task_type`、`target_column`、`primary_metric`、`metric_direction`、prediction/model artifacts 和 trial results 摘要；其 ready 条件为至少 1 个 completed trial、prediction artifacts 存在、target column 有效、evaluation plan 存在。

因此，本模块的核心职责是：

> 读取 Pipeline Execution 产生的 `metric_evaluation_input_json` 和预测结果 artifacts，按照 evaluation_plan 统一计算、聚合、排序和校验模型指标，生成可供 Result Diagnosis 使用的结构化评估结果。

---

## 2. 模块定位

### 2.1 一句话定义

**Metric Evaluation** 是 MLAgent 中负责对已完成训练的 trial、fold、pipeline run 进行统一指标计算、交叉验证聚合、模型排序和最佳 trial 候选选择的评估模块。

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
Pipeline Execution and Training
  ↓
Metric Evaluation   ← 当前模块
  ↓
Result Diagnosis
  ↓
Report Generation
```

---

### 2.3 当前模块与上游模块的关系

上游 Pipeline Execution 已完成：

* 模型训练；
* HPO trial 执行；
* fold-level 训练；
* prediction artifact 保存；
* model artifact 保存；
* raw metric 初步计算；
* `metric_evaluation_input_json` 构建；
* `ready_for_metric_evaluation` 标记。

当前 Metric Evaluation 模块只消费：

```text
PipelineExecution.metric_evaluation_input_json
Training prediction artifacts
Trial results summary
Evaluation plan
Validation plan
```

当前模块不重新执行：

* 数据加载；
* 特征工程；
* 特征预处理；
* Pipeline 生成；
* 模型训练；
* HPO trial；
* 模型实例化；
* 预测生成。

附件也明确指出，下游 Metric Evaluation 应消费模块十输出的 `metric_evaluation_input`，而不是重新训练或重新构建执行逻辑。

---

## 3. 核心设计原则

### 3.1 只评估，不训练

本模块只负责指标计算和评估聚合，不执行任何训练逻辑。

允许：

* 读取 prediction artifacts；
* 计算 MAE / RMSE / R2 / Accuracy 等指标；
* 聚合 fold-level 指标；
* 比较 trial；
* 标记 best trial candidate；
* 生成模型排名；
* 构建 Result Diagnosis 输入。

禁止：

* 调用 `model.fit()`；
* 调用 `model.predict()`；
* 修改模型参数；
* 重新生成 HPO trial；
* 重新划分训练集；
* 重新训练模型；
* 修改上游预测文件；
* 修改上游 training artifacts。

---

### 3.2 系统指标计算器是唯一评估入口

所有指标必须由系统内置 Metric Registry / Metric Calculator 计算。

不允许：

* LLM 计算指标；
* LLM 决定最佳模型；
* 用户提交自定义指标代码；
* 动态执行 Python 公式；
* 从字符串构造评价函数；
* 使用未经注册的 metric。

---

### 3.3 LLM 可以解释，不可以裁决

本模块可以预留 LLM Evaluation Observer，用于：

* 解释指标表现；
* 总结模型排名；
* 提醒指标异常；
* 为 Result Diagnosis 提供分析线索。

但 LLM 不允许：

* 修改 metric values；
* 修改 ranking；
* 修改 best trial；
* 修改 metric direction；
* 修改 evaluation status；
* 输出可执行代码；
* 直接写入最终评估结论。

MVP 阶段建议默认 **不调用 LLM**，保持评估链路 deterministic、可复现、可测试。

---

### 3.4 指标计算必须可复现

每次 Metric Evaluation 必须记录：

* 上游 `pipeline_execution_id`；
* 使用的 `metric_evaluation_input` 快照；
* prediction artifact 路径；
* evaluation plan 快照；
* validation plan 快照；
* metric definitions；
* metric direction；
* fold-level metric；
* trial-level metric；
* pipeline-level metric；
* ranking 规则；
* best trial 选择依据；
* 指标计算时间；
* 异常信息。

---

## 4. 产品目标

### 4.1 MVP 目标

本模块 MVP 需要实现：

1. 从最新或指定 `PipelineExecution` 中读取 `metric_evaluation_input_json`；
2. 校验 `ready_for_metric_evaluation = true`；
3. 加载 prediction artifacts；
4. 校验预测文件中的 `y_true`、`y_pred`、`trial_id`、`fold_index` 等字段；
5. 根据 `task_type` 和 `evaluation_plan` 选择指标；
6. 对每个 fold 计算指标；
7. 对每个 trial 聚合 cross-validation 指标；
8. 对每个 pipeline run 聚合 trial 表现；
9. 按 `primary_metric` 和 `metric_direction` 排序；
10. 生成 best trial candidate；
11. 生成 best pipeline candidate；
12. 生成 baseline comparison；
13. 生成 metric summary；
14. 生成 `result_diagnosis_input`；
15. 持久化完整评估结果；
16. 前端展示指标表格、排名、最佳候选、baseline 对比、fold 级表现和完整 JSON。

---

### 4.2 非目标

MVP 阶段不做：

1. 不重新训练模型；
2. 不重新生成预测；
3. 不做模型诊断；
4. 不解释为什么模型表现好或差；
5. 不生成最终报告；
6. 不做 SHAP / permutation importance；
7. 不做不确定性估计；
8. 不做 learning curve；
9. 不做模型部署；
10. 不支持用户提交自定义 Python metric；
11. 不支持 LLM 直接修改评估结果；
12. 不做实验论文级统计显著性检验，可作为后续增强。

---

## 5. 用户故事

### 5.1 材料科学研究者视角

作为材料科学研究者，我希望系统能自动汇总所有模型和 HPO trial 的表现，告诉我哪个模型在当前任务上表现最好，以及它相对 baseline 提升了多少。

---

### 5.2 后端开发者视角

作为后端开发者，我希望 Metric Evaluation 只消费 `metric_evaluation_input_json` 和 prediction artifacts，不重新读取和拼接所有上游模块，保证模块边界清晰。

---

### 5.3 前端用户视角

作为用户，我希望看到：

* 每个模型的主指标；
* 每个 trial 的指标；
* 每个 fold 的指标；
* 模型排名；
* 最佳模型候选；
* 与 baseline 的对比；
* 是否可以进入 Result Diagnosis。

---

### 5.4 AI Agent 系统视角

作为 AI Agent 系统，我希望评估结果由系统严格计算，LLM 只在后续诊断阶段解释结果，而不是参与指标计算和排序裁决。

---

## 6. 模块边界

### 6.1 与 Pipeline Execution and Training 的边界

Pipeline Execution 负责：

* 执行训练；
* 生成预测；
* 保存 prediction artifacts；
* 保存 model artifacts；
* 输出 trial results；
* 输出 `metric_evaluation_input`。

Metric Evaluation 负责：

* 读取预测结果；
* 标准化计算指标；
* 聚合 fold 和 trial 表现；
* 生成排名；
* 标记最佳候选；
* 生成下游诊断输入。

Metric Evaluation 不负责：

* 训练；
* 预测；
* HPO 执行；
* 模型保存；
* 修改上游 artifact。

---

### 6.2 与 Result Diagnosis 的边界

Metric Evaluation 输出事实型评估结果：

* 哪个模型最好；
* 指标是多少；
* baseline 提升多少；
* fold 方差多大；
* 哪些 trial 失败；
* 排名如何。

Result Diagnosis 负责解释性分析：

* 为什么某个模型表现好；
* 是否过拟合；
* 是否欠拟合；
* 是否 HPO 搜索不足；
* 是否特征不足；
* 下一轮优化建议；
* LLM 诊断总结。

---

### 6.3 与 Report Generation 的边界

Metric Evaluation 不生成最终报告。

它只输出结构化结果，供 Report Generation 引用。

---

## 7. 输入设计

### 7.1 API 请求输入

接口：

```text
POST /api/metric-evaluations/{task_id}
```

请求字段：

| 字段                            | 类型      | 必填 | 说明                                      |
| ----------------------------- | ------- | -: | --------------------------------------- |
| `force_rerun`                 | boolean |  否 | 是否强制重新评估，默认 false                       |
| `pipeline_execution_id`       | string  |  否 | 指定某个 PipelineExecution；为空则使用最新 ready 记录 |
| `include_fold_metrics`        | boolean |  否 | 是否输出 fold 级指标，默认 true                   |
| `include_baseline_comparison` | boolean |  否 | 是否输出 baseline 对比，默认 true                |
| `include_ranking_details`     | boolean |  否 | 是否输出排序细节，默认 true                        |
| `metric_profile`              | string  |  否 | `standard` / `full`，默认 standard         |
| `notes`                       | string  |  否 | 用户备注，不影响评估逻辑                            |

---

### 7.2 上游依赖输入

必须读取：

| 来源                             | 必需字段                                                                                                                                                                 |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PipelineExecution`            | `id`, `task_id`, `status`, `ready_for_metric_evaluation`, `metric_evaluation_input_json`                                                                             |
| `metric_evaluation_input_json` | `task_type`, `target_column`, `primary_metric`, `metric_direction`, `evaluation_plan`, `validation_plan`, `trial_results`, `prediction_artifacts`, `model_artifacts` |
| `prediction_artifacts`         | 每个 trial/fold 的预测文件路径                                                                                                                                                |
| `trial_results`                | trial_id, model_id, pipeline_spec_id, fold_results, status                                                                                                           |
| `evaluation_plan`              | primary_metric, secondary_metrics, metric_direction                                                                                                                  |
| `validation_plan`              | split_strategy, n_splits, random_state                                                                                                                               |

---

### 7.3 Artifact 输入

| Artifact                     | 来源                 | 用途               |
| ---------------------------- | ------------------ | ---------------- |
| prediction parquet files     | Pipeline Execution | 计算指标             |
| trial_results.json           | Pipeline Execution | 交叉校验 trial 元数据   |
| metric_evaluation_input.json | Pipeline Execution | 下游正式输入合同         |
| model artifacts              | Pipeline Execution | 只记录引用，不加载模型      |
| split metadata               | Pipeline Execution | 可选，用于 fold 校验和复现 |

---

## 8. 输出设计

### 8.1 核心输出：MetricEvaluationResponse

| 字段                             | 类型          | 说明                                                |
| ------------------------------ | ----------- | ------------------------------------------------- |
| `metric_evaluation_id`         | string      | 评估记录 ID，例如 `me_xxxxxxxx`                          |
| `task_id`                      | string      | 任务 ID                                             |
| `pipeline_execution_id`        | string      | 上游执行 ID                                           |
| `pipeline_generation_id`       | string      | 上游 PipelineGeneration ID                          |
| `status`                       | string      | `evaluated` / `evaluated_with_warning` / `failed` |
| `task_type`                    | string      | regression / classification                       |
| `primary_metric`               | string      | 主指标                                               |
| `metric_direction`             | string      | minimize / maximize                               |
| `n_trials_evaluated`           | integer     | 已评估 trial 数                                       |
| `n_trials_failed`              | integer     | 评估失败 trial 数                                      |
| `n_models_evaluated`           | integer     | 参与评估模型数                                           |
| `best_trial_id`                | string/null | 最佳 trial                                          |
| `best_model_id`                | string/null | 最佳模型                                              |
| `best_pipeline_spec_id`        | string/null | 最佳 PipelineSpec                                   |
| `metric_summary`               | object      | 总体指标摘要                                            |
| `trial_metric_results`         | array       | trial 级指标                                         |
| `pipeline_metric_results`      | array       | pipeline/model 级指标                                |
| `fold_metric_results`          | array       | fold 级指标，可选                                       |
| `model_ranking`                | array       | 模型排名                                              |
| `baseline_comparison`          | object      | baseline 对比                                       |
| `metric_validation_result`     | object      | 指标校验结果                                            |
| `evaluation_artifact_manifest` | object      | 评估产物路径                                            |
| `result_diagnosis_input`       | object      | 下游 Result Diagnosis 输入                            |
| `ready_for_result_diagnosis`   | boolean     | 是否可进入诊断                                           |
| `warnings`                     | array       | 警告                                                |
| `error_message`                | string/null | 错误信息                                              |
| `created_at`                   | datetime    | 创建时间                                              |
| `updated_at`                   | datetime    | 更新时间                                              |

---

## 9. 核心数据结构设计

### 9.1 MetricEvaluationResult

```text
MetricEvaluationResult
  ├── metric_evaluation_id
  ├── task_id
  ├── pipeline_execution_id
  ├── status
  ├── metric_summary
  ├── fold_metric_results
  ├── trial_metric_results
  ├── pipeline_metric_results
  ├── model_ranking
  ├── baseline_comparison
  ├── evaluation_artifact_manifest
  ├── result_diagnosis_input
  └── ready_for_result_diagnosis
```

---

### 9.2 FoldMetricResult

每个 fold 的指标结果。

| 字段                         | 类型          | 说明                 |
| -------------------------- | ----------- | ------------------ |
| `fold_metric_id`           | string      | fold 指标 ID         |
| `trial_id`                 | string      | trial ID           |
| `pipeline_spec_id`         | string      | PipelineSpec ID    |
| `model_id`                 | string      | 模型 ID              |
| `fold_index`               | integer     | fold 序号            |
| `n_samples`                | integer     | 验证样本数              |
| `metrics`                  | object      | 指标字典               |
| `primary_metric_value`     | float       | 主指标值               |
| `prediction_artifact_path` | string      | 对应预测文件             |
| `status`                   | string      | evaluated / failed |
| `warnings`                 | array       | 警告                 |
| `error_message`            | string/null | 错误信息               |

---

### 9.3 TrialMetricResult

每个 trial 的聚合指标结果。

| 字段                    | 类型      | 说明                                   |
| --------------------- | ------- | ------------------------------------ |
| `trial_id`            | string  | trial ID                             |
| `pipeline_spec_id`    | string  | PipelineSpec ID                      |
| `pipeline_run_id`     | string  | PipelineRun ID                       |
| `model_id`            | string  | 模型 ID                                |
| `model_family`        | string  | 模型族                                  |
| `pipeline_role`       | string  | baseline / candidate / hpo_candidate |
| `trial_type`          | string  | baseline / fixed_params / hpo        |
| `params`              | object  | trial 参数                             |
| `n_folds`             | integer | fold 数                               |
| `fold_metrics`        | array   | fold 指标摘要                            |
| `aggregated_metrics`  | object  | 聚合指标                                 |
| `primary_metric_mean` | float   | 主指标均值                                |
| `primary_metric_std`  | float   | 主指标标准差                               |
| `primary_metric_min`  | float   | 主指标最优 fold 值                         |
| `primary_metric_max`  | float   | 主指标最差 fold 值                         |
| `rank`                | integer | trial 排名                             |
| `is_best_trial`       | boolean | 是否最佳 trial                           |
| `status`              | string  | evaluated / failed                   |
| `warnings`            | array   | 警告                                   |

---

### 9.4 PipelineMetricResult

按 PipelineSpec / model 聚合的结果。

| 字段                          | 类型      | 说明                                   |
| --------------------------- | ------- | ------------------------------------ |
| `pipeline_spec_id`          | string  | PipelineSpec ID                      |
| `pipeline_run_id`           | string  | PipelineRun ID                       |
| `model_id`                  | string  | 模型 ID                                |
| `model_family`              | string  | 模型族                                  |
| `pipeline_role`             | string  | baseline / candidate / hpo_candidate |
| `n_trials_evaluated`        | integer | 已评估 trial 数                          |
| `best_trial_id`             | string  | 当前模型下最佳 trial                        |
| `best_primary_metric_value` | float   | 当前模型最佳主指标                            |
| `mean_primary_metric_value` | float   | trial 平均表现                           |
| `std_primary_metric_value`  | float   | trial 稳定性                            |
| `best_trial_params`         | object  | 最佳 trial 参数                          |
| `rank`                      | integer | 模型级排名                                |
| `is_best_model`             | boolean | 是否最佳模型                               |
| `warnings`                  | array   | 警告                                   |

---

### 9.5 ModelRankingItem

```text
ModelRankingItem
  ├── rank
  ├── model_id
  ├── model_family
  ├── pipeline_spec_id
  ├── best_trial_id
  ├── primary_metric
  ├── primary_metric_value
  ├── metric_direction
  ├── improvement_over_best_baseline
  ├── improvement_percentage
  ├── stability_score
  └── ranking_reason
```

---

### 9.6 BaselineComparison

用于展示候选模型相对 baseline 的提升。

| 字段                                | 类型          | 说明                |
| --------------------------------- | ----------- | ----------------- |
| `baseline_available`              | boolean     | 是否存在 baseline     |
| `best_baseline_model_id`          | string/null | 最佳 baseline 模型    |
| `best_baseline_trial_id`          | string/null | 最佳 baseline trial |
| `best_baseline_metric_value`      | float/null  | baseline 主指标      |
| `best_candidate_model_id`         | string/null | 最佳候选模型            |
| `best_candidate_trial_id`         | string/null | 最佳候选 trial        |
| `best_candidate_metric_value`     | float/null  | 候选模型主指标           |
| `absolute_improvement`            | float/null  | 绝对提升              |
| `relative_improvement_percentage` | float/null  | 相对提升百分比           |
| `candidate_beats_baseline`        | boolean     | 候选是否超过 baseline   |
| `comparison_notes`                | array       | 对比说明              |

---

### 9.7 ResultDiagnosisInput

下游 Result Diagnosis 的正式输入。

| 字段                           | 类型      | 说明          |
| ---------------------------- | ------- | ----------- |
| `metric_evaluation_id`       | string  | 当前评估 ID     |
| `pipeline_execution_id`      | string  | 上游执行 ID     |
| `task_id`                    | string  | 任务 ID       |
| `task_type`                  | string  | 任务类型        |
| `primary_metric`             | string  | 主指标         |
| `metric_direction`           | string  | 指标方向        |
| `best_trial`                 | object  | 最佳 trial 摘要 |
| `best_model`                 | object  | 最佳模型摘要      |
| `model_ranking`              | array   | 模型排名        |
| `baseline_comparison`        | object  | baseline 对比 |
| `metric_summary`             | object  | 指标摘要        |
| `failed_trials_summary`      | object  | 失败 trial 摘要 |
| `stability_summary`          | object  | fold 稳定性摘要  |
| `evaluation_warnings`        | array   | 评估警告        |
| `ready_for_result_diagnosis` | boolean | 是否可诊断       |

---

## 10. 后端功能设计

### 10.1 推荐目录结构

建议新增：

```text
backend/app/modules/metric_evaluation/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── metric_input_loader.py
    ├── prediction_artifact_loader.py
    ├── metric_registry.py
    ├── metric_calculator.py
    ├── fold_metric_evaluator.py
    ├── trial_metric_aggregator.py
    ├── pipeline_metric_aggregator.py
    ├── model_ranker.py
    ├── baseline_comparator.py
    ├── metric_validator.py
    ├── evaluation_artifact_manager.py
    ├── result_diagnosis_input_builder.py
    └── builder.py
```

---

### 10.2 各文件职责说明

| 文件                                  | 职责                                 |
| ----------------------------------- | ---------------------------------- |
| `api.py`                            | Metric Evaluation REST API         |
| `service.py`                        | 业务主流程编排                            |
| `model.py`                          | 数据库模型                              |
| `repository.py`                     | CRUD 和 latest 查询                   |
| `schemas.py`                        | DTO 和响应结构                          |
| `enums.py`                          | 状态、指标方向、任务类型枚举                     |
| `exceptions.py`                     | 专用异常                               |
| `context_builder.py`                | 校验上游 PipelineExecution             |
| `metric_input_loader.py`            | 加载并校验 metric_evaluation_input_json |
| `prediction_artifact_loader.py`     | 加载 prediction parquet              |
| `metric_registry.py`                | 指标白名单和方向定义                         |
| `metric_calculator.py`              | 统一指标计算入口                           |
| `fold_metric_evaluator.py`          | fold 级指标计算                         |
| `trial_metric_aggregator.py`        | trial 级指标聚合                        |
| `pipeline_metric_aggregator.py`     | pipeline/model 级聚合                 |
| `model_ranker.py`                   | 排名和 best trial 选择                  |
| `baseline_comparator.py`            | baseline 对比                        |
| `metric_validator.py`               | 评估结果一致性校验                          |
| `evaluation_artifact_manager.py`    | 保存评估产物                             |
| `result_diagnosis_input_builder.py` | 构建下游诊断输入                           |
| `builder.py`                        | 构建最终响应                             |

---

## 11. 后端主流程

### 11.1 主流程概览

```text
MetricEvaluationService.create_metric_evaluation(task_id, request)
    ↓
1. build_metric_evaluation_context()
    ↓
2. load_metric_evaluation_input()
    ↓
3. validate_metric_readiness()
    ↓
4. load_prediction_artifacts()
    ↓
5. evaluate_fold_metrics()
    ↓
6. aggregate_trial_metrics()
    ↓
7. aggregate_pipeline_metrics()
    ↓
8. rank_models_and_trials()
    ↓
9. compare_against_baselines()
    ↓
10. validate_metric_results()
    ↓
11. save_metric_artifacts()
    ↓
12. build_result_diagnosis_input()
    ↓
13. build_response()
    ↓
14. persist()
```

---

### 11.2 Step 1：构建评估上下文

`context_builder.py` 负责：

* 根据 `task_id` 获取最新 PipelineExecution；
* 或根据请求中的 `pipeline_execution_id` 获取指定记录；
* 校验 `PipelineExecution.status in completed / completed_with_warning / partially_failed`；
* 校验 `PipelineExecution.ready_for_metric_evaluation = true`；
* 读取 `metric_evaluation_input_json`；
* 构建评估上下文。

失败场景：

| 场景                         | error_code                                           |
| -------------------------- | ---------------------------------------------------- |
| 找不到 PipelineExecution      | `PIPELINE_EXECUTION_NOT_FOUND`                       |
| PipelineExecution 未 ready  | `PIPELINE_EXECUTION_NOT_READY_FOR_METRIC_EVALUATION` |
| metric_evaluation_input 缺失 | `METRIC_EVALUATION_INPUT_MISSING`                    |
| prediction artifacts 缺失    | `PREDICTION_ARTIFACTS_MISSING`                       |

---

### 11.3 Step 2：加载 Metric Evaluation Input

`metric_input_loader.py` 负责校验：

* `task_type` 是否存在；
* `target_column` 是否存在；
* `primary_metric` 是否存在；
* `metric_direction` 是否存在；
* `evaluation_plan` 是否存在；
* `trial_results` 是否非空；
* `prediction_artifacts` 是否非空；
* 至少一个 trial 状态为 completed。

注意：

该模块只消费上游合同，不回溯重建 Pipeline Execution 的内部执行逻辑。

---

### 11.4 Step 3：加载预测结果

`prediction_artifact_loader.py` 负责：

* 加载每个 prediction parquet；
* 校验路径安全；
* 校验文件存在；
* 校验字段完整；
* 校验 `y_true` 和 `y_pred` 长度一致；
* 校验无不可计算值；
* 分类任务校验 label/proba 字段；
* 返回结构化 PredictionFrame。

MVP 必需字段：

| 字段                 | 说明              |
| ------------------ | --------------- |
| `sample_id`        | 样本 ID           |
| `trial_id`         | trial ID        |
| `pipeline_spec_id` | PipelineSpec ID |
| `fold_index`       | fold 序号         |
| `y_true`           | 真实值             |
| `y_pred`           | 预测值             |
| `model_id`         | 模型 ID           |

---

### 11.5 Step 4：Metric Registry

`metric_registry.py` 维护可用指标白名单。

MVP 支持回归指标：

| 指标     | 方向       | 说明           |
| ------ | -------- | ------------ |
| `MAE`  | minimize | 平均绝对误差       |
| `MSE`  | minimize | 均方误差         |
| `RMSE` | minimize | 均方根误差        |
| `R2`   | maximize | 决定系数         |
| `MAPE` | minimize | 平均绝对百分比误差，可选 |

MVP 支持分类指标：

| 指标          | 方向       | 说明            |
| ----------- | -------- | ------------- |
| `Accuracy`  | maximize | 准确率           |
| `Precision` | maximize | 精确率           |
| `Recall`    | maximize | 召回率           |
| `F1`        | maximize | F1 score      |
| `ROC_AUC`   | maximize | AUC，可选，需要概率输出 |

指标要求：

* 必须根据 task_type 过滤；
* 不允许使用任务类型不兼容指标；
* 不允许使用未注册指标；
* 指标方向必须由系统定义或 evaluation_plan 继承后校验；
* 若上游 metric_direction 与 Registry 冲突，应记录 warning 并以系统 Registry 为准。

---

### 11.6 Step 5：Fold 级指标计算

`fold_metric_evaluator.py` 负责：

* 对每个 prediction artifact 计算指标；
* 每个 fold 输出一个 `FoldMetricResult`；
* 捕获单个 fold 评估失败；
* 支持部分 fold 失败但 trial 仍可聚合；
* 记录每个指标的计算状态。

回归任务计算：

```text
MAE, MSE, RMSE, R2
```

分类任务计算：

```text
Accuracy, Precision, Recall, F1
```

MVP 分类指标可先支持 binary / multiclass 的基本 average 策略，例如 weighted average，但必须在结果中记录 `average_method`。

---

### 11.7 Step 6：Trial 级指标聚合

`trial_metric_aggregator.py` 负责：

* 将同一 trial 下多个 fold 的指标聚合；
* 计算 mean / std / min / max；
* 生成 `TrialMetricResult`；
* 标记 trial 是否可参与 ranking。

聚合规则：

| 字段                    | 说明        |
| --------------------- | --------- |
| `primary_metric_mean` | 排名主值      |
| `primary_metric_std`  | 稳定性指标     |
| `primary_metric_min`  | 最优 fold   |
| `primary_metric_max`  | 最差 fold   |
| `n_successful_folds`  | 成功 fold 数 |
| `n_failed_folds`      | 失败 fold 数 |

若某个 trial 无成功 fold，则标记为 evaluation failed。

---

### 11.8 Step 7：Pipeline / Model 级聚合

`pipeline_metric_aggregator.py` 负责：

* 按 `pipeline_spec_id` 聚合 trial；
* 按 `model_id` 聚合表现；
* 识别每个模型下最佳 trial；
* 计算模型稳定性；
* 输出 `PipelineMetricResult`。

对于 HPO 模型：

* 取最佳 trial 作为该模型主要表现；
* 记录平均 trial 表现作为参考；
* 保留最佳参数。

对于 baseline：

* 通常只有一个 trial；
* 直接作为 baseline 表现。

---

### 11.9 Step 8：模型和 Trial 排名

`model_ranker.py` 负责：

* 根据 `primary_metric` 和 `metric_direction` 排序；
* 标记 `best_trial_id`；
* 标记 `best_model_id`；
* 标记 `best_pipeline_spec_id`；
* 生成 `model_ranking`。

排序规则：

| metric_direction | 规则                  |
| ---------------- | ------------------- |
| `minimize`       | primary metric 越小越好 |
| `maximize`       | primary metric 越大越好 |

Tie-breaker 建议：

1. 主指标更优；
2. 主指标标准差更小；
3. 模型优先级更高；
4. 模型训练成本更低；
5. baseline 不优先于 candidate，除非 candidate 未明显超过 baseline。

注意：MVP 可实现前两项 tie-breaker。

---

### 11.10 Step 9：Baseline 对比

`baseline_comparator.py` 负责：

* 找出最佳 baseline；
* 找出最佳 candidate；
* 计算 absolute improvement；
* 计算 relative improvement percentage；
* 判断 candidate 是否超过 baseline；
* 生成 comparison notes。

回归 minimize 指标：

```text
improvement = baseline_metric - candidate_metric
relative_improvement = improvement / baseline_metric
```

分类 maximize 指标：

```text
improvement = candidate_metric - baseline_metric
relative_improvement = improvement / baseline_metric
```

需要处理：

* baseline 不存在；
* baseline metric 为 0；
* candidate 不存在；
* 所有 candidate 失败。

---

### 11.11 Step 10：Metric 结果校验

`metric_validator.py` 负责：

* 检查指标是否为有限数；
* 检查主指标是否存在；
* 检查排名是否与 metric direction 一致；
* 检查 best trial 是否存在于 trial results；
* 检查 baseline comparison 是否引用合法模型；
* 检查 result_diagnosis_input 是否完整。

---

### 11.12 Step 11：保存评估产物

`evaluation_artifact_manager.py` 负责保存：

| 产物                     | 建议路径                                                                           |
| ---------------------- | ------------------------------------------------------------------------------ |
| metric results         | `/app/artifacts/evaluation/{metric_evaluation_id}/metric_results.json`         |
| trial metrics          | `/app/artifacts/evaluation/{metric_evaluation_id}/trial_metrics.json`          |
| fold metrics           | `/app/artifacts/evaluation/{metric_evaluation_id}/fold_metrics.json`           |
| model ranking          | `/app/artifacts/evaluation/{metric_evaluation_id}/model_ranking.json`          |
| baseline comparison    | `/app/artifacts/evaluation/{metric_evaluation_id}/baseline_comparison.json`    |
| result diagnosis input | `/app/artifacts/evaluation/{metric_evaluation_id}/result_diagnosis_input.json` |
| manifest               | `/app/artifacts/evaluation/{metric_evaluation_id}/manifest.json`               |

---

### 11.13 Step 12：构建 Result Diagnosis Input

`result_diagnosis_input_builder.py` 负责构建下游正式输入。

只有满足以下条件时：

```text
n_trials_evaluated > 0
best_trial_id 不为空
model_ranking 非空
metric_summary 有效
```

才设置：

```text
ready_for_result_diagnosis = true
```

---

## 12. 数据库设计

### 12.1 新增表：MetricEvaluation

表名建议：

```text
metric_evaluation
```

字段设计：

| 字段                            | 类型       | 索引    | 说明                                          |
| ----------------------------- | -------- | ----- | ------------------------------------------- |
| `id`                          | string   | PK    | `me_{uuid8}`                                |
| `task_id`                     | string   | index | 任务 ID                                       |
| `pipeline_execution_id`       | string   | index | 上游 PipelineExecution ID                     |
| `pipeline_generation_id`      | string   | index | 上游 PipelineGeneration ID                    |
| `status`                      | string   | index | evaluated / evaluated_with_warning / failed |
| `task_type`                   | string   | index | regression / classification                 |
| `target_column`               | string   |       | 目标列                                         |
| `primary_metric`              | string   | index | 主指标                                         |
| `metric_direction`            | string   |       | minimize / maximize                         |
| `n_trials_evaluated`          | integer  |       | 已评估 trial 数                                 |
| `n_trials_failed`             | integer  |       | 评估失败 trial 数                                |
| `n_models_evaluated`          | integer  |       | 已评估模型数                                      |
| `best_trial_id`               | string   | index | 最佳 trial                                    |
| `best_model_id`               | string   | index | 最佳模型                                        |
| `best_pipeline_spec_id`       | string   | index | 最佳 PipelineSpec                             |
| `best_primary_metric_value`   | float    |       | 最佳主指标值                                      |
| `ready_for_result_diagnosis`  | boolean  | index | 是否可进入结果诊断                                   |
| `evaluation_artifact_dir`     | string   |       | 评估产物目录                                      |
| `evaluation_json`             | JSONB    |       | 完整评估结果                                      |
| `result_diagnosis_input_json` | JSONB    |       | 下游诊断输入                                      |
| `metric_summary_json`         | JSONB    |       | 指标摘要                                        |
| `model_ranking_json`          | JSONB    |       | 排名摘要                                        |
| `error_message`               | string   |       | 错误信息                                        |
| `created_at`                  | datetime | index | 创建时间                                        |
| `updated_at`                  | datetime |       | 更新时间                                        |

---

## 13. 状态设计

### 13.1 MetricEvaluationStatus

| 状态                       | 说明                    |
| ------------------------ | --------------------- |
| `evaluating`             | 正在评估                  |
| `evaluated`              | 评估成功                  |
| `evaluated_with_warning` | 评估成功但存在警告             |
| `partially_evaluated`    | 部分 trial 评估失败，但存在有效结果 |
| `failed`                 | 评估失败                  |

---

### 13.2 TrialEvaluationStatus

| 状态          | 说明                   |
| ----------- | -------------------- |
| `evaluated` | trial 评估成功           |
| `failed`    | trial 评估失败           |
| `skipped`   | trial 未完成或无预测文件，跳过评估 |

---

### 13.3 ready_for_result_diagnosis 规则

| 条件                             | ready_for_result_diagnosis |
| ------------------------------ | -------------------------- |
| 至少一个 trial 成功评估，且存在 best trial | true                       |
| 所有 trial 评估失败                  | false                      |
| model ranking 为空               | false                      |
| primary metric 缺失              | false                      |
| result_diagnosis_input 构建失败    | false                      |

---

## 14. API 设计

### 14.1 创建 Metric Evaluation

```text
POST /api/metric-evaluations/{task_id}
```

说明：

* 根据最新或指定 PipelineExecution 执行指标评估；
* 如果已有 evaluated 记录且 `force_rerun = false`，可返回最新结果；
* 如果 `force_rerun = true`，创建新评估记录。

---

### 14.2 获取指定评估结果

```text
GET /api/metric-evaluations/{metric_evaluation_id}
```

返回完整评估结果。

---

### 14.3 获取任务最新评估结果

```text
GET /api/tasks/{task_id}/metric-evaluation
```

返回该任务最新评估结果。

---

### 14.4 重新评估

```text
POST /api/metric-evaluations/{task_id}/rerun
```

等价于 `force_rerun = true`。

---

### 14.5 获取评估摘要

```text
GET /api/metric-evaluations/{metric_evaluation_id}/summary
```

建议返回：

* evaluation id；
* status；
* primary metric；
* best model；
* best trial；
* best metric value；
* baseline improvement；
* ready_for_result_diagnosis。

---

### 14.6 获取模型排名

```text
GET /api/metric-evaluations/{metric_evaluation_id}/ranking
```

用于前端展示 ranking table。

---

### 14.7 获取 trial 指标

```text
GET /api/metric-evaluations/{metric_evaluation_id}/trials
```

用于前端展示 trial-level metrics。

---

### 14.8 获取 fold 指标

```text
GET /api/metric-evaluations/{metric_evaluation_id}/folds
```

用于前端展示 fold-level metrics。

---

### 14.9 获取 Result Diagnosis Input

```text
GET /api/metric-evaluations/{metric_evaluation_id}/result-diagnosis-input
```

供下游 Result Diagnosis 或调试使用。

---

## 15. 后端安全设计

### 15.1 禁止动态指标代码

本模块绝对禁止：

```text
eval
exec
动态 import
用户自定义 Python metric
LLM 生成 metric 函数
字符串公式执行
shell command
```

---

### 15.2 指标白名单机制

所有 metric 必须来自：

```text
Metric Registry → Metric Calculator → Evaluation Result
```

不允许：

* 上游传入未注册 metric 后直接执行；
* 用户提交自定义 metric 函数；
* LLM 定义 metric；
* 动态从字符串映射函数。

---

### 15.3 路径安全

所有输入 prediction artifacts 必须：

* 来自上游 `metric_evaluation_input_json`；
* 位于 `/app/artifacts/training/{pe_id}/predictions/` 或允许目录；
* 文件存在；
* 文件类型为 parquet；
* 不包含 `..`；
* 不允许覆盖。

所有输出 evaluation artifacts 必须写入：

```text
/app/artifacts/evaluation/{metric_evaluation_id}/
```

---

## 16. LLM 参与设计

### 16.1 MVP 建议

MVP 阶段建议 Metric Evaluation **不调用 LLM**。

原因：

* 指标计算应 deterministic；
* 排名应由系统规则决定；
* LLM 不应参与数值计算；
* 后续 Result Diagnosis 才是 LLM 更适合参与的位置。

---

### 16.2 预留 LLM Evaluation Observer

后续可增加非阻塞 LLM Observer，用于：

* 总结排名现象；
* 识别指标异常；
* 给 Result Diagnosis 提供先验提示；
* 解释 baseline improvement。

但该 Observer 只能输出：

* advisory notes；
* risk notes；
* diagnosis hints。

不能输出：

* metric values；
* ranking；
* best model；
* execution decision；
* executable code。

---

## 17. 前端功能设计

### 17.1 新增前端文件结构

建议新增：

```text
frontend/src/api/metricEvaluationApi.ts

frontend/src/modules/metricEvaluation/
    ├── components/
    │   ├── MetricEvaluationPanel.tsx
    │   ├── MetricSummaryCard.tsx
    │   ├── BestModelCard.tsx
    │   ├── ModelRankingTable.tsx
    │   ├── TrialMetricTable.tsx
    │   ├── FoldMetricTable.tsx
    │   ├── BaselineComparisonCard.tsx
    │   ├── MetricValidationCard.tsx
    │   ├── EvaluationArtifactManifestCard.tsx
    │   ├── ResultDiagnosisInputCard.tsx
    │   └── MetricEvaluationJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

---

### 17.2 页面集成位置

当前前端是单页嵌入式面板结构，附件说明前端已有一个 `TaskSpecificationPage`，其中嵌入 10 个模块面板，各面板直接调用 API 并管理本地状态。

建议在 `PipelineExecutionPanel` 后增加：

```text
MetricEvaluationPanel
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
Pipeline Generation
Pipeline Execution and Training
Metric Evaluation   ← 新增
```

---

### 17.3 主面板功能

`MetricEvaluationPanel` 应提供：

| 功能                    | 说明          |
| --------------------- | ----------- |
| Run Metric Evaluation | 开始指标评估      |
| Re-run Evaluation     | 重新评估        |
| Load Latest           | 加载最新评估结果    |
| View Ranking          | 查看模型排名      |
| View Trial Metrics    | 查看 trial 指标 |
| View Fold Metrics     | 查看 fold 指标  |
| View Diagnosis Input  | 查看下游诊断输入    |
| View Full JSON        | 查看完整 JSON   |

---

### 17.4 前端展示区域

#### 17.4.1 Metric Summary Card

展示：

* Metric Evaluation ID；
* 状态；
* primary metric；
* metric direction；
* trials evaluated；
* models evaluated；
* best model；
* best trial；
* best metric value；
* ready for Result Diagnosis。

---

#### 17.4.2 Best Model Card

展示：

* best model id；
* best model family；
* best pipeline spec；
* best trial id；
* best params；
* primary metric value；
* secondary metrics；
* fold std；
* ranking reason。

---

#### 17.4.3 Model Ranking Table

表格字段：

| 列              | 说明                                   |
| -------------- | ------------------------------------ |
| Rank           | 排名                                   |
| Model          | 模型                                   |
| Role           | baseline / candidate / hpo_candidate |
| Best Trial     | 最佳 trial                             |
| Primary Metric | 主指标                                  |
| Metric Value   | 指标值                                  |
| Std            | fold 标准差                             |
| Improvement    | 相对 baseline 提升                       |
| Status         | 状态                                   |

---

#### 17.4.4 Trial Metric Table

表格字段：

| 列                 | 说明                     |
| ----------------- | ---------------------- |
| Trial ID          | trial                  |
| Model             | 模型                     |
| Type              | baseline / fixed / hpo |
| Params            | 参数摘要                   |
| Primary Mean      | 主指标均值                  |
| Primary Std       | 主指标标准差                 |
| Secondary Metrics | 二级指标                   |
| Rank              | trial 排名               |
| Status            | 状态                     |

---

#### 17.4.5 Fold Metric Table

展示：

* trial_id；
* model_id；
* fold_index；
* n_samples；
* MAE / RMSE / R2 或 Accuracy / F1；
* status；
* warning。

---

#### 17.4.6 Baseline Comparison Card

展示：

* best baseline；
* best candidate；
* absolute improvement；
* relative improvement；
* candidate 是否超过 baseline；
* comparison notes。

---

#### 17.4.7 Result Diagnosis Input Card

展示：

* ready_for_result_diagnosis；
* best model summary；
* ranking summary；
* baseline comparison；
* evaluation warnings；
* diagnosis input JSON 摘要。

---

## 18. 前端状态与交互

### 18.1 按钮启用规则

| 条件                                              | Run Metric Evaluation   |
| ----------------------------------------------- | ----------------------- |
| 无 task_id                                       | disabled                |
| 无 PipelineExecution                             | disabled                |
| PipelineExecution 未 ready_for_metric_evaluation | disabled                |
| 正在评估                                            | loading / disabled      |
| 已 evaluated 且 force_rerun=false                 | 显示 Load Latest / Re-run |
| 上游 ready_for_metric_evaluation=true             | enabled                 |

---

### 18.2 状态颜色建议

| 状态                                 | 颜色          |
| ---------------------------------- | ----------- |
| `evaluating`                       | blue        |
| `evaluated`                        | green       |
| `evaluated_with_warning`           | orange      |
| `partially_evaluated`              | orange      |
| `failed`                           | red         |
| `ready_for_result_diagnosis=true`  | green       |
| `ready_for_result_diagnosis=false` | default/red |

---

## 19. Artifact 设计

### 19.1 评估产物目录

建议根目录：

```text
/app/artifacts/evaluation/{metric_evaluation_id}/
```

目录结构：

```text
evaluation/{metric_evaluation_id}/
    ├── manifest.json
    ├── metric_results.json
    ├── fold_metrics.json
    ├── trial_metrics.json
    ├── pipeline_metrics.json
    ├── model_ranking.json
    ├── baseline_comparison.json
    └── result_diagnosis_input.json
```

---

### 19.2 Manifest 内容

`manifest.json` 建议包含：

* metric_evaluation_id；
* pipeline_execution_id；
* input prediction artifacts；
* output metric artifacts；
* primary metric；
* metric direction；
* best trial id；
* best model id；
* created_at；
* artifact versions。

---

## 20. 异常设计

建议新增异常：

| 异常类                                     | error_code                                           | 场景                     |
| --------------------------------------- | ---------------------------------------------------- | ---------------------- |
| `MetricEvaluationNotFoundException`     | `METRIC_EVALUATION_NOT_FOUND`                        | 找不到评估记录                |
| `PipelineExecutionRequiredException`    | `PIPELINE_EXECUTION_REQUIRED`                        | 缺少上游 PipelineExecution |
| `PipelineExecutionNotReadyException`    | `PIPELINE_EXECUTION_NOT_READY_FOR_METRIC_EVALUATION` | 上游未 ready              |
| `MetricEvaluationInputInvalidException` | `METRIC_EVALUATION_INPUT_INVALID`                    | 输入合同无效                 |
| `PredictionArtifactLoadException`       | `PREDICTION_ARTIFACT_LOAD_FAILED`                    | 预测文件加载失败               |
| `MetricNotSupportedException`           | `METRIC_NOT_SUPPORTED`                               | 指标不支持                  |
| `MetricCalculationException`            | `METRIC_CALCULATION_FAILED`                          | 指标计算失败                 |
| `MetricAggregationException`            | `METRIC_AGGREGATION_FAILED`                          | 指标聚合失败                 |
| `ModelRankingException`                 | `MODEL_RANKING_FAILED`                               | 排名失败                   |
| `BaselineComparisonException`           | `BASELINE_COMPARISON_FAILED`                         | baseline 对比失败          |
| `ResultDiagnosisInputBuildException`    | `RESULT_DIAGNOSIS_INPUT_BUILD_FAILED`                | 下游输入构建失败               |
| `EvaluationArtifactSaveException`       | `EVALUATION_ARTIFACT_SAVE_FAILED`                    | 评估产物保存失败               |

---

## 21. MVP 验收标准

### 21.1 后端验收标准

必须满足：

1. 可以通过 API 启动 Metric Evaluation；
2. 必须校验上游 `ready_for_metric_evaluation = true`；
3. 必须只消费 `metric_evaluation_input_json` 和 prediction artifacts；
4. 不重新训练模型；
5. 能加载 prediction parquet；
6. 能计算 regression 指标：MAE、MSE、RMSE、R2；
7. 能计算 classification 基础指标：Accuracy，建议支持 Precision、Recall、F1；
8. 能生成 fold-level metric；
9. 能生成 trial-level aggregated metric；
10. 能生成 pipeline/model-level metric；
11. 能按 primary_metric 和 metric_direction 排名；
12. 能标记 best trial 和 best model；
13. 能生成 baseline comparison；
14. 能生成 `result_diagnosis_input_json`；
15. 能持久化完整评估结果；
16. 失败时必须持久化失败记录；
17. 不允许 LLM 计算指标；
18. 不允许用户自定义 Python metric；
19. 不允许动态执行代码。

---

### 21.2 前端验收标准

必须满足：

1. 新增 Metric Evaluation 面板；
2. 可以点击 Run Metric Evaluation；
3. 可以点击 Re-run Evaluation；
4. 可以展示评估状态；
5. 可以展示 best model；
6. 可以展示 model ranking；
7. 可以展示 trial metrics；
8. 可以展示 fold metrics；
9. 可以展示 baseline comparison；
10. 可以展示 ready_for_result_diagnosis；
11. 可以展示 evaluation artifacts；
12. 可以查看完整 JSON；
13. 错误信息清晰可读。

---

### 21.3 安全验收标准

必须满足：

1. 指标只能来自 Metric Registry；
2. 不允许 eval / exec；
3. 不允许动态 import；
4. 不允许执行用户 metric 代码；
5. 不允许 LLM 修改指标结果；
6. 不允许 LLM 参与 ranking 裁决；
7. 不允许写入未授权目录；
8. 不允许覆盖上游 prediction artifacts。

---

## 22. 推荐实现优先级

### P0：必须完成

1. 后端 `metric_evaluation` 模块目录；
2. `MetricEvaluation` 数据表；
3. `context_builder`；
4. `metric_input_loader`；
5. `prediction_artifact_loader`；
6. `metric_registry`；
7. `metric_calculator`；
8. `fold_metric_evaluator`；
9. `trial_metric_aggregator`；
10. `model_ranker`；
11. `baseline_comparator`；
12. `result_diagnosis_input_builder`；
13. 核心 API；
14. 前端主面板；
15. Model Ranking 表；
16. Trial Metric 表；
17. Baseline Comparison 展示。

---

### P1：建议完成

1. Fold Metric 表；
2. metric validation result；
3. evaluation artifact manifest；
4. result diagnosis input 展示；
5. 支持 Precision / Recall / F1；
6. 支持 classification weighted average；
7. 支持部分 trial 失败后的 partial evaluation；
8. 支持前端 JSON 折叠展示。

---

### P2：后续迭代

1. ROC-AUC；
2. PR-AUC；
3. calibration metrics；
4. ranking stability analysis；
5. statistical significance test；
6. confidence interval；
7. bootstrapping；
8. metric visualization charts；
9. LLM Evaluation Observer；
10. 与 Result Diagnosis 深度联动。

---

## 23. 给 AI Coding 工具的实现提示词

```text
请基于当前 MLAgent 项目实现 Metric Evaluation 模块。开发前先阅读 PROJECT_IMPLEMENTATION_OVERVIEW.md，重点理解模块十 Pipeline Execution and Training 的 metric_evaluation_input 输出合同。

实现要求：
1. 新增 backend/app/modules/metric_evaluation 模块，结构遵循现有模块模式：api.py、service.py、model.py、repository.py、schemas.py、enums.py、exceptions.py、context_builder.py、builder.py 等；
2. 本模块只消费 PipelineExecution.metric_evaluation_input_json 和 prediction artifacts，不要重新训练模型，不要重新生成预测，不要重新构建 Pipeline；
3. 必须校验 PipelineExecution.ready_for_metric_evaluation=true；
4. 加载 prediction parquet，校验 y_true、y_pred、trial_id、pipeline_spec_id、fold_index 等字段；
5. 实现 Metric Registry 和 Metric Calculator，MVP 至少支持 regression: MAE/MSE/RMSE/R2，classification: Accuracy，建议支持 Precision/Recall/F1；
6. 实现 fold-level metric、trial-level aggregation、pipeline/model-level aggregation；
7. 根据 primary_metric 和 metric_direction 生成 model ranking，标记 best_trial_id、best_model_id、best_pipeline_spec_id；
8. 实现 baseline_comparator，计算候选模型相对 baseline 的 absolute improvement 和 relative improvement；
9. 构建 result_diagnosis_input_json，供下一步 Result Diagnosis 使用；
10. 保存 evaluation artifacts 到 /app/artifacts/evaluation/{metric_evaluation_id}/；
11. 前端新增 MetricEvaluationPanel，展示 summary、best model、model ranking、trial metrics、fold metrics、baseline comparison、result diagnosis input 和完整 JSON；
12. 严禁 LLM 计算指标，严禁用户自定义 Python metric，严禁 eval/exec/dynamic import，严禁修改上游训练 artifact。
```

---

## 24. 总结

**Metric Evaluation** 是 MLAgent 从“训练产物生成”进入“模型结果判断”的关键模块。

它的核心价值是：

```text
把 Pipeline Execution 输出的 predictions 和 trial results 转换为统一、标准、可复现、可排序的模型评估结果。
```

本模块必须坚持：

```text
只消费 metric_evaluation_input；
只读取 prediction artifacts；
只由系统 Metric Calculator 计算指标；
不重新训练；
不让 LLM 计算指标；
不做结果诊断；
不生成最终报告。
```

完成本模块后，MLAgent 将具备从任务输入到模型训练与标准化评估的完整自动化闭环，并为下一步 **Result Diagnosis** 提供稳定、结构化、可解释的输入基础。
