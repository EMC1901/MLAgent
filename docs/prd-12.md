# PRD：LLM-based Result Diagnosis 模块

> 项目名称：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：12
> 模块名称：LLM-based Result Diagnosis
> 上游模块：Metric Evaluation
> 下游模块：Closed-loop Refinement
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0
> 输出格式：Markdown

---

## 1. 背景与上下文

当前 MLAgent 已经完成从 **Task Specification → LLM-based Task Interpretation → Dataset Loading, Checking, and Profiling → Workflow Planning → Feature Engineering → Feature Preprocessing → Model Search Context Update → Automated Model and HPO Search → Executable Pipeline Generation → Pipeline Execution and Training → Metric Evaluation** 的完整自动化链路。

根据附件说明，当前系统已完成 **十一个核心业务模块**，其中模块十一 **Metric Evaluation** 已实现 Fold → Trial → Pipeline 三级指标聚合、Model Ranking、Baseline Comparison，并输出 `result_diagnosis_input`，供下游 Result Diagnosis 消费。当前尚未实现的后续模块包括 Result Diagnosis 及后续阶段。

用户已明确更新后续工作流：

```text
11. Metric Evaluation
12. LLM-based Result Diagnosis
13. Closed-loop Refinement
14. Final Pipeline Selection
15. Interpretability Analysis
16. Final Output
```

因此，本模块 **LLM-based Result Diagnosis** 的职责是：

> 消费 Metric Evaluation 输出的 `result_diagnosis_input`，结合数据画像、训练日志、pipeline 记录、模型排名和 baseline 对比结果，由 LLM 进行结构化诊断，识别欠拟合、过拟合、特征不足、模型不匹配、HPO 不足、验证不稳定、数据质量限制等问题，并为下一步 Closed-loop Refinement 生成安全、结构化、不可直接执行的改进建议。

---

## 2. 模块定位

### 2.1 一句话定义

**LLM-based Result Diagnosis 是 MLAgent 中基于评估结果和实验上下文进行机器学习问题诊断的智能分析模块，用于识别模型表现不佳的潜在原因，并输出结构化的改进方向，但不直接修改 workflow、不重新训练模型、不生成可执行代码。**

---

## 3. 在整体链路中的位置

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
Metric Evaluation
  ↓
LLM-based Result Diagnosis   ← 当前模块
  ↓
Closed-loop Refinement
  ↓
Final Pipeline Selection
  ↓
Interpretability Analysis
  ↓
Final Output
```

---

## 4. 与上下游模块的关系

### 4.1 上游：Metric Evaluation

Metric Evaluation 已完成：

* 计算 fold-level metrics；
* 聚合 trial-level metrics；
* 聚合 pipeline/model-level metrics；
* 生成 model ranking；
* 生成 baseline comparison；
* 标记 best model / best trial；
* 输出 `result_diagnosis_input`；
* 设置 `ready_for_result_diagnosis`。

附件说明中明确指出，模块十一已通过 `result_diagnosis_input` 和 `ready_for_result_diagnosis` 标记与下游 Result Diagnosis 模块对接。

本模块必须消费：

```text
MetricEvaluation.result_diagnosis_input_json
MetricEvaluation.evaluation_json
MetricEvaluation.metric_summary_json
MetricEvaluation.model_ranking_json
```

可补充读取：

```text
PipelineExecution.execution_json
PipelineGeneration.pipeline_json
ModelSearchPlan.plan_json
ModelSearchContext.context_json
FeaturePreprocessing.preprocessing_json
FeatureEngineering.feature_json
DatasetProfile.profile_json
WorkflowPlan.plan_json
```

但本模块的主输入合同必须是：

```text
MetricEvaluation.result_diagnosis_input_json
```

---

### 4.2 下游：Closed-loop Refinement

本模块输出：

```text
diagnosis_result
refinement_recommendation_input
ready_for_closed_loop_refinement
```

下游 **Closed-loop Refinement** 负责：

* 根据诊断结果生成改进后的 workflow plan；
* 或生成新的 model search context；
* 或生成新的 pipeline generation request；
* 或决定是否需要扩大 HPO、调整模型族、补充特征、改变验证策略。

本模块不负责真正修改 workflow，也不负责启动下一轮训练。

---

## 5. 核心设计原则

### 5.1 LLM 深度参与，但只输出诊断与建议

LLM 可以输出：

* 问题诊断；
* 可能原因；
* 证据引用；
* 风险等级；
* 改进方向；
* 下一轮优化建议；
* 是否建议进入 closed-loop refinement；
* refinement hint。

LLM 不允许输出：

* Python 代码；
* sklearn 代码；
* 训练脚本；
* 可执行 Pipeline；
* 动态参数生成代码；
* 直接修改 workflow plan；
* 直接修改 HPO search space；
* 直接修改 Model Registry；
* 直接触发重新训练。

---

### 5.2 诊断必须基于证据

LLM 输出的每一类诊断都必须绑定 evidence。

例如：

```text
diagnosis_type: overfitting_risk
evidence:
  - train/validation gap 高
  - fold variance 高
  - candidate model 明显优于 baseline 但稳定性差
```

如果证据不足，必须输出：

```text
evidence_strength: weak
```

不能凭空断言。

---

### 5.3 LLM 不做最终决策

本模块可以建议：

```text
should_refine: true
recommended_refinement_focus: feature_engineering
```

但不能直接决定：

```text
立即执行下一轮训练
直接选择最终模型
直接覆盖已有 Workflow Plan
```

下游 Closed-loop Refinement 需要重新经过系统 Validator、Registry、Template 和 Controlled Executor。

---

### 5.4 诊断输出必须结构化

LLM 输出必须是严格 JSON，经过：

```text
Prompt Builder → LLM Client → Parser → Validator → Normalizer → Builder → Persist
```

不得直接将 LLM 原始文本作为业务结果。

---

### 5.5 诊断结果是 Advisory，但会进入闭环优化

与模块九的 LLM Advisory Review 不同，本模块的诊断结果虽然仍然是 advisory，但它会成为模块十三 Closed-loop Refinement 的重要输入。

因此，本模块输出应区分：

```text
diagnostic_facts      ← 系统可验证事实
llm_diagnosis         ← LLM 诊断判断
refinement_hints      ← 给下游闭环优化的建议
confidence_level      ← LLM 对诊断的信心
```

---

## 6. 产品目标

### 6.1 MVP 目标

MVP 阶段需要实现：

1. 从最新或指定 `MetricEvaluation` 中读取 `result_diagnosis_input_json`；
2. 校验 `ready_for_result_diagnosis = true`；
3. 汇总评估结果、baseline 对比、模型排名、fold 稳定性；
4. 可选补充读取 Dataset Profile、Feature Engineering、Feature Preprocessing、Pipeline Execution 日志；
5. 构建面向 LLM 的诊断上下文；
6. 调用 LLM 输出结构化诊断；
7. 校验 LLM 输出 JSON；
8. 过滤可执行代码和非法字段；
9. 归一化诊断结果；
10. 输出问题类型、证据、严重程度、置信度、改进建议；
11. 生成 `closed_loop_refinement_input`；
12. 设置 `ready_for_closed_loop_refinement`；
13. 持久化诊断结果；
14. 前端展示诊断摘要、问题分类、证据、改进建议和下游闭环输入。

---

### 6.2 非目标

MVP 阶段不做：

1. 不重新计算指标；
2. 不重新训练模型；
3. 不重新生成 Pipeline；
4. 不重新执行 HPO；
5. 不自动修改 Workflow Plan；
6. 不直接选择最终模型；
7. 不执行 Closed-loop Refinement；
8. 不执行 SHAP 或特征重要性分析；
9. 不生成最终报告；
10. 不让 LLM 输出可执行代码。

---

## 7. 诊断范围

### 7.1 MVP 需要支持的诊断类型

| 诊断类型             | 英文字段                        | 说明                       |
| ---------------- | --------------------------- | ------------------------ |
| 欠拟合              | `underfitting`              | 所有模型表现都差，复杂模型无明显改善       |
| 过拟合风险            | `overfitting_risk`          | fold 方差大、复杂模型不稳定         |
| 特征不足             | `feature_insufficiency`     | 特征数量少、特征表达能力弱            |
| 特征噪声             | `feature_noise`             | 特征多但模型表现不稳定              |
| 模型不匹配            | `model_mismatch`            | 当前模型族不适合数据模式             |
| HPO 不足           | `hpo_insufficient`          | trial 数少、候选模型未充分搜索       |
| 验证不稳定            | `validation_instability`    | fold 间指标波动大              |
| baseline 无明显提升   | `weak_baseline_improvement` | candidate 未显著超过 baseline |
| 数据质量限制           | `data_quality_limitation`   | 缺失、离群、小样本、不平衡等问题         |
| 指标选择风险           | `metric_mismatch`           | 指标不能充分表达目标               |
| pipeline 成功但收益有限 | `limited_pipeline_gain`     | 系统执行成功但效果提升有限            |

---

## 8. 输入设计

### 8.1 API 请求输入

接口：

```text
POST /api/result-diagnoses/{task_id}
```

请求字段：

| 字段                         | 类型      | 必填 | 说明                                                  |
| -------------------------- | ------- | -: | --------------------------------------------------- |
| `metric_evaluation_id`     | string  |  否 | 指定使用某个 MetricEvaluation；为空则使用最新 ready 记录            |
| `force_rerun`              | boolean |  否 | 是否强制重新诊断，默认 false                                   |
| `use_llm`                  | boolean |  否 | 是否调用 LLM，默认 true                                    |
| `include_dataset_context`  | boolean |  否 | 是否补充 Dataset Profile，默认 true                        |
| `include_pipeline_context` | boolean |  否 | 是否补充 Pipeline Generation / Execution 记录，默认 true     |
| `include_feature_context`  | boolean |  否 | 是否补充 Feature Engineering / Preprocessing 记录，默认 true |
| `diagnosis_profile`        | string  |  否 | `compact` / `standard` / `full`，默认 standard         |
| `notes`                    | string  |  否 | 用户备注，不影响诊断逻辑                                        |

---

### 8.2 上游主输入

必须读取：

| 来源                            | 必需字段                                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `MetricEvaluation`            | `id`, `task_id`, `status`, `ready_for_result_diagnosis`, `result_diagnosis_input_json`                                          |
| `result_diagnosis_input_json` | `best_trial`, `best_model_id`, `model_ranking`, `baseline_comparison`, `metric_summary`, `trial_results`, `evaluation_warnings` |
| `metric_summary_json`         | 指标均值、方差、min/max、CV 等                                                                                                            |
| `model_ranking_json`          | 排名列表、baseline improvement                                                                                                       |
| `evaluation_json`             | 完整 fold/trial/pipeline 指标结果                                                                                                     |

---

### 8.3 可选补充输入

| 来源                                        | 用途                                               |
| ----------------------------------------- | ------------------------------------------------ |
| `DatasetProfile.profile_json`             | 分析小样本、缺失、离群、目标分布偏斜                               |
| `FeatureEngineering.feature_json`         | 分析特征数量、特征类型、特征质量                                 |
| `FeaturePreprocessing.preprocessing_json` | 分析 dropped features、scaling、imputation、selection |
| `ModelSearchContext.context_json`         | 分析搜索前的数据和策略调整背景                                  |
| `ModelSearchPlan.plan_json`               | 分析候选模型、HPO 预算、验证策略                               |
| `PipelineGeneration.pipeline_json`        | 分析 pipeline spec、trial plan、安全检查                 |
| `PipelineExecution.execution_json`        | 分析 trial 失败、runtime、fold 失败、日志摘要                 |
| `PipelineExecution.runtime_log_json`      | 分析环境和训练异常                                        |

---

## 9. 输出设计

### 9.1 核心输出：ResultDiagnosisResponse

| 字段                                 | 类型          | 说明                                                |
| ---------------------------------- | ----------- | ------------------------------------------------- |
| `result_diagnosis_id`              | string      | 诊断记录 ID，例如 `rd_xxxxxxxx`                          |
| `task_id`                          | string      | 任务 ID                                             |
| `metric_evaluation_id`             | string      | 上游 MetricEvaluation ID                            |
| `pipeline_execution_id`            | string      | 上游 PipelineExecution ID                           |
| `status`                           | string      | `diagnosed` / `diagnosed_with_warning` / `failed` |
| `diagnosis_mode`                   | string      | `llm_based` / `system_rule_based` / `hybrid`      |
| `overall_assessment`               | object      | 总体诊断摘要                                            |
| `diagnostic_findings`              | array       | 结构化问题诊断列表                                         |
| `evidence_summary`                 | object      | 证据摘要                                              |
| `root_cause_hypotheses`            | array       | 根因假设                                              |
| `refinement_recommendations`       | array       | 改进建议                                              |
| `closed_loop_refinement_input`     | object      | 下游 Closed-loop Refinement 输入                      |
| `ready_for_closed_loop_refinement` | boolean     | 是否可进入闭环优化                                         |
| `llm_diagnosis`                    | object      | LLM 原始诊断的标准化结果                                    |
| `system_diagnostic_checks`         | object      | 系统规则检查结果                                          |
| `diagnosis_artifact_manifest`      | object      | 诊断产物路径                                            |
| `warnings`                         | array       | 警告                                                |
| `error_message`                    | string/null | 错误信息                                              |
| `created_at`                       | datetime    | 创建时间                                              |
| `updated_at`                       | datetime    | 更新时间                                              |

---

## 10. 核心数据结构设计

### 10.1 OverallAssessment

| 字段                           | 类型      | 说明                                                  |
| ---------------------------- | ------- | --------------------------------------------------- |
| `performance_level`          | string  | `excellent` / `acceptable` / `weak` / `failed`      |
| `baseline_improvement_level` | string  | `strong` / `moderate` / `weak` / `none` / `unknown` |
| `stability_level`            | string  | `stable` / `moderately_unstable` / `unstable`       |
| `main_issue_category`        | string  | 主要问题类别                                              |
| `should_refine`              | boolean | 是否建议进入闭环优化                                          |
| `summary`                    | string  | 简短总结                                                |
| `confidence_level`           | string  | `low` / `medium` / `high`                           |

---

### 10.2 DiagnosticFinding

每个问题诊断一条 finding。

| 字段                    | 类型     | 说明                                     |
| --------------------- | ------ | -------------------------------------- |
| `finding_id`          | string | 诊断项 ID                                 |
| `diagnosis_type`      | string | 诊断类型，如 underfitting / overfitting_risk |
| `severity`            | string | `low` / `medium` / `high` / `critical` |
| `evidence_strength`   | string | `weak` / `moderate` / `strong`         |
| `description`         | string | 诊断描述                                   |
| `evidence_items`      | array  | 支撑证据                                   |
| `affected_models`     | array  | 受影响模型                                  |
| `affected_trials`     | array  | 受影响 trial                              |
| `possible_causes`     | array  | 可能原因                                   |
| `recommended_actions` | array  | 建议动作                                   |
| `refinement_targets`  | array  | 下游优化目标                                 |
| `confidence_level`    | string | LLM 对该 finding 的置信度                    |

---

### 10.3 EvidenceItem

| 字段               | 类型     | 说明                                                                         |
| ---------------- | ------ | -------------------------------------------------------------------------- |
| `evidence_type`  | string | metric / ranking / baseline / fold_stability / data_profile / pipeline_log |
| `source_module`  | string | metric_evaluation / pipeline_execution / dataset_profile 等                 |
| `source_field`   | string | 来源字段                                                                       |
| `value`          | any    | 证据值                                                                        |
| `interpretation` | string | 证据解释                                                                       |

---

### 10.4 RootCauseHypothesis

| 字段                    | 类型     | 说明                  |
| --------------------- | ------ | ------------------- |
| `hypothesis_id`       | string | 假设 ID               |
| `root_cause_type`     | string | 根因类型                |
| `description`         | string | 根因描述                |
| `supporting_findings` | array  | 支撑该假设的 finding ID   |
| `likelihood`          | string | low / medium / high |
| `actionability`       | string | low / medium / high |

---

### 10.5 RefinementRecommendation

| 字段                      | 类型      | 说明                                                                                        |
| ----------------------- | ------- | ----------------------------------------------------------------------------------------- |
| `recommendation_id`     | string  | 建议 ID                                                                                     |
| `target_stage`          | string  | workflow_planning / feature_engineering / preprocessing / model_search / hpo / validation |
| `recommendation_type`   | string  | expand_features / change_models / increase_hpo / adjust_validation / change_metric        |
| `priority`              | string  | high / medium / low                                                                       |
| `description`           | string  | 建议描述                                                                                      |
| `expected_benefit`      | string  | 预期收益                                                                                      |
| `risk`                  | string  | 风险                                                                                        |
| `system_action_hint`    | object  | 给下游 Closed-loop Refinement 的结构化提示                                                         |
| `requires_human_review` | boolean | 是否建议人工确认                                                                                  |

---

### 10.6 ClosedLoopRefinementInput

下游 Closed-loop Refinement 的正式输入。

| 字段                                 | 类型      | 说明        |
| ---------------------------------- | ------- | --------- |
| `result_diagnosis_id`              | string  | 当前诊断 ID   |
| `metric_evaluation_id`             | string  | 上游评估 ID   |
| `task_id`                          | string  | 任务 ID     |
| `should_refine`                    | boolean | 是否建议优化    |
| `refinement_focus`                 | array   | 需要优化的环节   |
| `priority_recommendations`         | array   | 高优先级建议    |
| `diagnostic_findings_summary`      | array   | 诊断摘要      |
| `constraints_to_preserve`          | array   | 需要保留的约束   |
| `avoid_actions`                    | array   | 不建议采取的动作  |
| `suggested_next_iteration_profile` | object  | 下一轮迭代配置建议 |
| `ready_for_closed_loop_refinement` | boolean | 是否可进入下一步  |

---

## 11. 后端功能设计

### 11.1 推荐目录结构

建议新增：

```text
backend/app/modules/result_diagnosis/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── diagnosis_input_loader.py
    ├── diagnostic_context_builder.py
    ├── system_diagnostic_checker.py
    ├── llm_prompt_builder.py
    ├── llm_result_diagnoser.py
    ├── llm_response_parser.py
    ├── llm_diagnosis_validator.py
    ├── llm_diagnosis_normalizer.py
    ├── evidence_extractor.py
    ├── refinement_input_builder.py
    ├── diagnosis_artifact_manager.py
    └── builder.py
```

---

### 11.2 各文件职责说明

| 文件                              | 职责                                            |
| ------------------------------- | --------------------------------------------- |
| `api.py`                        | 提供 Result Diagnosis 相关 REST API               |
| `service.py`                    | 主流程编排                                         |
| `model.py`                      | SQLModel 数据表                                  |
| `repository.py`                 | 数据库 CRUD                                      |
| `schemas.py`                    | 请求、响应、内部 DTO                                  |
| `enums.py`                      | 状态、诊断类型、严重程度等枚举                               |
| `exceptions.py`                 | 专用异常                                          |
| `context_builder.py`            | 读取并校验 MetricEvaluation 及相关上游记录                |
| `diagnosis_input_loader.py`     | 加载 `result_diagnosis_input_json`              |
| `diagnostic_context_builder.py` | 汇总 LLM 诊断上下文                                  |
| `system_diagnostic_checker.py`  | 系统规则诊断，生成可验证事实                                |
| `llm_prompt_builder.py`         | 构建 LLM 诊断 Prompt                              |
| `llm_result_diagnoser.py`       | 调用 LLM                                        |
| `llm_response_parser.py`        | 解析 LLM JSON                                   |
| `llm_diagnosis_validator.py`    | 校验 LLM 输出结构和安全性                               |
| `llm_diagnosis_normalizer.py`   | 将非标准 LLM 输出归一化                                |
| `evidence_extractor.py`         | 提取 metric / baseline / fold / data profile 证据 |
| `refinement_input_builder.py`   | 构建 Closed-loop Refinement 输入                  |
| `diagnosis_artifact_manager.py` | 保存诊断 artifacts                                |
| `builder.py`                    | 构建最终响应                                        |

---

## 12. 后端主流程

### 12.1 主流程概览

```text
ResultDiagnosisService.create_result_diagnosis(task_id, request)
    ↓
1. build_result_diagnosis_context()
    ↓
2. load_result_diagnosis_input()
    ↓
3. collect_optional_context()
    ↓
4. extract_evidence()
    ↓
5. run_system_diagnostic_checks()
    ↓
6. build_llm_diagnostic_context()
    ↓
7. build_llm_prompt()
    ↓
8. call_llm_result_diagnoser()
    ↓
9. parse_llm_response()
    ↓
10. validate_llm_diagnosis()
    ↓
11. normalize_llm_diagnosis()
    ↓
12. build_closed_loop_refinement_input()
    ↓
13. save_diagnosis_artifacts()
    ↓
14. build_response()
    ↓
15. persist()
```

---

### 12.2 Step 1：构建诊断上下文

`context_builder.py` 负责：

* 根据 `task_id` 获取最新 MetricEvaluation；
* 或根据请求中的 `metric_evaluation_id` 获取指定记录；
* 校验 `MetricEvaluation.status in evaluated / evaluated_with_warning / partially_evaluated`；
* 校验 `MetricEvaluation.ready_for_result_diagnosis = true`；
* 读取 `result_diagnosis_input_json`；
* 获取必要上游 ID；
* 按配置补充读取 DatasetProfile、FeatureEngineering、FeaturePreprocessing、PipelineExecution 等记录。

失败场景：

| 场景                        | error_code                                  |
| ------------------------- | ------------------------------------------- |
| 找不到 MetricEvaluation      | `METRIC_EVALUATION_NOT_FOUND`               |
| MetricEvaluation 未 ready  | `METRIC_EVALUATION_NOT_READY_FOR_DIAGNOSIS` |
| result_diagnosis_input 缺失 | `RESULT_DIAGNOSIS_INPUT_MISSING`            |
| 上游上下文缺失                   | `DIAGNOSIS_CONTEXT_INCOMPLETE`              |

---

### 12.3 Step 2：加载 Result Diagnosis Input

`diagnosis_input_loader.py` 负责校验：

* `metric_evaluation_id` 存在；
* `pipeline_execution_id` 存在；
* `task_id` 存在；
* `task_type` 存在；
* `primary_metric` 存在；
* `metric_direction` 存在；
* `best_trial` 存在；
* `model_ranking` 非空；
* `baseline_comparison` 存在；
* `metric_summary` 存在。

---

### 12.4 Step 3：证据提取

`evidence_extractor.py` 负责从上游结果中提取可解释证据。

证据来源：

| 来源                    | 证据                                            |
| --------------------- | --------------------------------------------- |
| Metric Summary        | 主指标均值、方差、CV                                   |
| Model Ranking         | best model、排名差异                               |
| Baseline Comparison   | candidate 是否超过 baseline                       |
| Trial Metrics         | 不同 trial 的性能差异                                |
| Fold Metrics          | fold 方差和稳定性                                   |
| Dataset Profile       | 样本量、缺失、异常值、目标分布                               |
| Feature Engineering   | 特征数、特征类型、失败特征                                 |
| Feature Preprocessing | dropped features、imputation、scaling、selection |
| Pipeline Execution    | trial 失败、训练耗时、runtime warning                 |
| Pipeline Generation   | HPO trial 分配、模型覆盖情况                           |

---

### 12.5 Step 4：系统规则诊断

`system_diagnostic_checker.py` 负责生成 deterministic diagnostic facts。

MVP 可支持以下规则：

| 规则                                 | 判断逻辑                         |
| ---------------------------------- | ---------------------------- |
| `weak_baseline_improvement`        | candidate 相对 baseline 提升小于阈值 |
| `high_fold_variance`               | 主指标 CV 超过阈值                  |
| `all_models_weak`                  | 所有模型主指标均较差或无明显提升             |
| `hpo_budget_limited`               | HPO trial 数较少且模型表现差异不稳定      |
| `small_sample_warning`             | 样本量小于阈值                      |
| `feature_count_low`                | 最终特征数过低                      |
| `many_features_dropped`            | 特征预处理阶段丢弃比例过高                |
| `candidate_underperforms_baseline` | candidate 未超过 baseline       |
| `unstable_best_model`              | best model fold std 过高       |

系统规则输出不能替代 LLM 诊断，但应作为 LLM 的 evidence 输入。

---

### 12.6 Step 5：构建 LLM 诊断上下文

`diagnostic_context_builder.py` 负责将复杂上下文压缩为 LLM 可消费摘要。

建议包含：

```text
1. Task summary
2. Dataset profile summary
3. Feature engineering summary
4. Feature preprocessing summary
5. Model search summary
6. Pipeline execution summary
7. Metric evaluation summary
8. Model ranking
9. Baseline comparison
10. Fold stability summary
11. System diagnostic checks
12. Known warnings and failed trials
```

注意：不传递完整大表，只传摘要和关键证据。

---

## 13. LLM Prompt 设计

### 13.1 LLM 角色定义

Prompt 中必须明确：

```text
You are a machine learning result diagnosis advisor for an AutoML system in materials science.

You must diagnose possible causes of model performance based only on the provided evidence.

You are not allowed to generate executable code.
You are not allowed to modify the workflow.
You are not allowed to start training.
You are not allowed to create new pipelines.
You can only output structured JSON diagnosis and refinement hints.
```

---

### 13.2 LLM 诊断维度

Prompt 应要求 LLM 从以下维度诊断：

1. Performance level；
2. Baseline improvement；
3. Fold stability；
4. Overfitting risk；
5. Underfitting risk；
6. Feature insufficiency；
7. Feature noise；
8. Model mismatch；
9. HPO insufficiency；
10. Validation instability；
11. Data quality limitation；
12. Metric mismatch；
13. Pipeline search limitation；
14. Suggested refinement targets。

---

### 13.3 LLM 输出 Schema

LLM 必须输出 JSON：

```json
{
  "overall_assessment": {
    "performance_level": "weak",
    "baseline_improvement_level": "weak",
    "stability_level": "unstable",
    "main_issue_category": "feature_insufficiency",
    "should_refine": true,
    "summary": "The best candidate model only marginally improves over baseline and fold variation is high.",
    "confidence_level": "medium"
  },
  "diagnostic_findings": [
    {
      "diagnosis_type": "feature_insufficiency",
      "severity": "medium",
      "evidence_strength": "moderate",
      "description": "The feature representation may be insufficient for the target property.",
      "evidence_items": [
        {
          "evidence_type": "feature_profile",
          "source_module": "feature_preprocessing",
          "source_field": "n_final_features",
          "value": 14,
          "interpretation": "The final feature count is low for a nonlinear materials property prediction task."
        }
      ],
      "affected_models": ["ridge", "lasso", "elastic_net"],
      "affected_trials": [],
      "possible_causes": [
        "Composition descriptors may not capture enough domain information."
      ],
      "recommended_actions": [
        "Consider adding richer matminer composition descriptors or structure-aware features if structure data is available."
      ],
      "refinement_targets": ["feature_engineering", "model_search"],
      "confidence_level": "medium"
    }
  ],
  "root_cause_hypotheses": [
    {
      "root_cause_type": "limited_feature_representation",
      "description": "The current feature representation may be too simple.",
      "supporting_findings": ["feature_insufficiency"],
      "likelihood": "medium",
      "actionability": "high"
    }
  ],
  "refinement_recommendations": [
    {
      "target_stage": "feature_engineering",
      "recommendation_type": "expand_features",
      "priority": "high",
      "description": "Try richer composition descriptors and compare against the current descriptor set.",
      "expected_benefit": "May improve nonlinear property prediction.",
      "risk": "May increase feature dimensionality and require stronger regularization.",
      "system_action_hint": {
        "suggested_feature_strategy": "expanded_composition_descriptors"
      },
      "requires_human_review": false
    }
  ],
  "confidence_level": "medium"
}
```

---

## 14. LLM 输出校验与安全设计

### 14.1 Validator 规则

`llm_diagnosis_validator.py` 必须检查：

1. JSON 可解析；
2. 顶层字段完整；
3. 枚举值合法；
4. 数组字段类型正确；
5. `confidence_level` 合法；
6. `severity` 合法；
7. `diagnosis_type` 合法；
8. `target_stage` 合法；
9. 不包含可执行代码；
10. 不包含非法字段。

---

### 14.2 禁止字段

LLM 输出中禁止出现：

```text
python_code
code
script
executable
workflow_patch
pipeline_patch
model_fit_code
train_code
shell_command
sql
direct_execution
```

---

### 14.3 禁止内容扫描

必须扫描：

```text
import
def
class
eval(
exec(
subprocess
os.system
open(
write(
delete
remove
shutil
model.fit
model.predict
Pipeline(
optuna.create_study
```

如果出现，应：

* 标记 LLM 诊断输出不安全；
* 不采纳原始输出；
* 使用 fallback diagnosis；
* 记录 warning；
* 不影响已有 Metric Evaluation 结果。

---

### 14.4 Normalizer 设计

`llm_diagnosis_normalizer.py` 负责：

* 补齐缺失字段；
* 归一化 severity；
* 归一化 confidence；
* 将自由文本 findings 转为结构化 findings；
* 将非法 target_stage 丢弃或映射为 `unknown`;
* 将 LLM 旧式总结字段归入 `raw_llm_summary`;
* 保证最终输出满足 `ResultDiagnosisResponse`。

---

## 15. Closed-loop Refinement Input 设计

### 15.1 构建规则

`refinement_input_builder.py` 应将诊断结果转换为下游闭环优化输入。

示例结构：

```json
{
  "result_diagnosis_id": "rd_xxxxxxxx",
  "metric_evaluation_id": "me_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "should_refine": true,
  "refinement_focus": [
    "feature_engineering",
    "model_search",
    "hpo"
  ],
  "priority_recommendations": [
    {
      "target_stage": "feature_engineering",
      "recommendation_type": "expand_features",
      "priority": "high",
      "system_action_hint": {
        "suggested_feature_strategy": "expanded_composition_descriptors"
      }
    }
  ],
  "constraints_to_preserve": [
    "task_type",
    "target_column",
    "primary_metric"
  ],
  "avoid_actions": [
    "do_not_reduce_validation_folds",
    "do_not_remove_best_baseline"
  ],
  "suggested_next_iteration_profile": {
    "model_search_budget": "moderate",
    "hpo_trials": "increase_if_runtime_allows",
    "feature_strategy": "expand_or_refine"
  },
  "ready_for_closed_loop_refinement": true
}
```

---

### 15.2 ready_for_closed_loop_refinement 规则

| 条件                                       | ready |
| ---------------------------------------- | ----- |
| 至少一个 high/medium priority recommendation | true  |
| `should_refine = true` 且有明确 target_stage | true  |
| 诊断失败                                     | false |
| LLM 输出不安全且无 fallback                     | false |
| 没有可操作建议                                  | false |

---

## 16. 数据库设计

### 16.1 新增表：ResultDiagnosis

表名建议：

```text
result_diagnosis
```

字段设计：

| 字段                                  | 类型       | 索引    | 说明                                          |
| ----------------------------------- | -------- | ----- | ------------------------------------------- |
| `id`                                | string   | PK    | `rd_{uuid8}`                                |
| `task_id`                           | string   | index | 任务 ID                                       |
| `metric_evaluation_id`              | string   | index | 上游 MetricEvaluation ID                      |
| `pipeline_execution_id`             | string   | index | PipelineExecution ID                        |
| `status`                            | string   | index | diagnosed / diagnosed_with_warning / failed |
| `diagnosis_mode`                    | string   | index | llm_based / hybrid / system_rule_based      |
| `main_issue_category`               | string   | index | 主要问题类别                                      |
| `performance_level`                 | string   | index | excellent / acceptable / weak / failed      |
| `should_refine`                     | boolean  | index | 是否建议闭环优化                                    |
| `ready_for_closed_loop_refinement`  | boolean  | index | 是否可进入闭环优化                                   |
| `llm_used`                          | boolean  |       | 是否使用 LLM                                    |
| `llm_confidence_level`              | string   |       | low / medium / high                         |
| `diagnosis_json`                    | JSONB    |       | 完整诊断结果                                      |
| `closed_loop_refinement_input_json` | JSONB    |       | 下游闭环输入                                      |
| `llm_request_json`                  | JSONB    |       | LLM 请求                                      |
| `llm_response_json`                 | JSONB    |       | LLM 原始响应                                    |
| `system_checks_json`                | JSONB    |       | 系统规则诊断结果                                    |
| `diagnosis_artifact_dir`            | string   |       | 诊断产物目录                                      |
| `error_message`                     | string   |       | 错误信息                                        |
| `created_at`                        | datetime | index | 创建时间                                        |
| `updated_at`                        | datetime |       | 更新时间                                        |

---

## 17. 状态设计

### 17.1 ResultDiagnosisStatus

| 状态                       | 说明              |
| ------------------------ | --------------- |
| `diagnosing`             | 正在诊断            |
| `diagnosed`              | 诊断成功            |
| `diagnosed_with_warning` | 诊断成功但存在警告       |
| `fallback_diagnosed`     | LLM 失败后使用系统规则诊断 |
| `failed`                 | 诊断失败            |

---

### 17.2 DiagnosisMode

| 模式                  | 说明                        |
| ------------------- | ------------------------- |
| `llm_based`         | 主要由 LLM 诊断                |
| `hybrid`            | 系统规则 + LLM 共同诊断，推荐 MVP 默认 |
| `system_rule_based` | LLM 不可用时使用系统规则 fallback   |

---

## 18. Artifact 设计

### 18.1 诊断产物目录

建议根目录：

```text
/app/artifacts/diagnosis/{result_diagnosis_id}/
```

目录结构：

```text
diagnosis/{result_diagnosis_id}/
    ├── manifest.json
    ├── diagnosis_result.json
    ├── diagnostic_context.json
    ├── system_diagnostic_checks.json
    ├── llm_diagnosis.json
    ├── evidence_summary.json
    └── closed_loop_refinement_input.json
```

---

## 19. API 设计

### 19.1 创建 Result Diagnosis

```text
POST /api/result-diagnoses/{task_id}
```

说明：

* 根据最新或指定 MetricEvaluation 生成诊断；
* 如果已有诊断且 `force_rerun = false`，返回最新结果；
* 如果 `force_rerun = true`，创建新记录。

---

### 19.2 获取指定诊断结果

```text
GET /api/result-diagnoses/{result_diagnosis_id}
```

---

### 19.3 获取任务最新诊断结果

```text
GET /api/tasks/{task_id}/result-diagnosis
```

---

### 19.4 重新诊断

```text
POST /api/result-diagnoses/{task_id}/rerun
```

---

### 19.5 获取诊断摘要

```text
GET /api/result-diagnoses/{result_diagnosis_id}/summary
```

建议返回：

* diagnosis id；
* status；
* main issue category；
* performance level；
* should refine；
* ready for closed-loop refinement；
* top findings；
* top recommendations。

---

### 19.6 获取 Closed-loop Refinement Input

```text
GET /api/result-diagnoses/{result_diagnosis_id}/closed-loop-refinement-input
```

供下游模块和调试使用。

---

## 20. 前端功能设计

### 20.1 新增前端文件结构

建议新增：

```text
frontend/src/api/resultDiagnosisApi.ts

frontend/src/modules/resultDiagnosis/
    ├── components/
    │   ├── ResultDiagnosisPanel.tsx
    │   ├── DiagnosisSummaryCard.tsx
    │   ├── OverallAssessmentCard.tsx
    │   ├── DiagnosticFindingTable.tsx
    │   ├── EvidenceSummaryCard.tsx
    │   ├── RootCauseHypothesisCard.tsx
    │   ├── RefinementRecommendationTable.tsx
    │   ├── SystemDiagnosticChecksCard.tsx
    │   ├── LLMDiagnosisCard.tsx
    │   ├── ClosedLoopRefinementInputCard.tsx
    │   └── ResultDiagnosisJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

---

### 20.2 页面集成位置

当前前端是单页嵌入式面板结构，附件说明当前 `TaskSpecificationPage` 已含 11 个嵌入式面板。

建议在 `MetricEvaluationPanel` 后增加：

```text
ResultDiagnosisPanel
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
Metric Evaluation
LLM-based Result Diagnosis   ← 新增
```

---

### 20.3 主面板功能

`ResultDiagnosisPanel` 应提供：

| 功能                     | 说明        |
| ---------------------- | --------- |
| Run Diagnosis          | 启动诊断      |
| Re-run Diagnosis       | 重新诊断      |
| Load Latest            | 加载最新诊断    |
| View Findings          | 查看问题诊断    |
| View Evidence          | 查看证据      |
| View Recommendations   | 查看改进建议    |
| View Closed-loop Input | 查看闭环优化输入  |
| View Full JSON         | 查看完整 JSON |

---

### 20.4 前端展示区域

#### 20.4.1 Diagnosis Summary

展示：

* Result Diagnosis ID；
* 状态；
* diagnosis mode；
* performance level；
* main issue category；
* should refine；
* ready for Closed-loop Refinement；
* confidence level。

---

#### 20.4.2 Overall Assessment

展示：

* 总体表现；
* baseline improvement；
* stability level；
* 主问题类别；
* 简短总结。

---

#### 20.4.3 Diagnostic Findings Table

表格字段：

| 列                   | 说明   |
| ------------------- | ---- |
| Type                | 问题类型 |
| Severity            | 严重程度 |
| Evidence Strength   | 证据强度 |
| Description         | 描述   |
| Affected Models     | 影响模型 |
| Recommended Actions | 建议动作 |
| Confidence          | 置信度  |

---

#### 20.4.4 Evidence Summary

展示：

* metric evidence；
* baseline evidence；
* fold stability evidence；
* dataset evidence；
* feature evidence；
* pipeline execution evidence。

---

#### 20.4.5 Refinement Recommendations

表格字段：

| 列                | 说明       |
| ---------------- | -------- |
| Target Stage     | 优化环节     |
| Type             | 建议类型     |
| Priority         | 优先级      |
| Description      | 描述       |
| Expected Benefit | 预期收益     |
| Risk             | 风险       |
| Human Review     | 是否需要人工确认 |

---

#### 20.4.6 Closed-loop Refinement Input

展示：

* should_refine；
* refinement_focus；
* priority_recommendations；
* constraints_to_preserve；
* avoid_actions；
* suggested_next_iteration_profile；
* ready_for_closed_loop_refinement。

---

## 21. 前端状态与交互

### 21.1 按钮启用规则

| 条件                                            | Run Diagnosis           |
| --------------------------------------------- | ----------------------- |
| 无 task_id                                     | disabled                |
| 无 MetricEvaluation                            | disabled                |
| MetricEvaluation 未 ready_for_result_diagnosis | disabled                |
| 正在诊断                                          | loading                 |
| 已 diagnosed 且 force_rerun=false               | 显示 Load Latest / Re-run |
| 上游 ready_for_result_diagnosis=true            | enabled                 |

---

### 21.2 状态颜色建议

| 状态                                       | 颜色      |
| ---------------------------------------- | ------- |
| `diagnosing`                             | blue    |
| `diagnosed`                              | green   |
| `diagnosed_with_warning`                 | orange  |
| `fallback_diagnosed`                     | orange  |
| `failed`                                 | red     |
| `ready_for_closed_loop_refinement=true`  | green   |
| `ready_for_closed_loop_refinement=false` | default |

---

### 21.3 诊断类型颜色建议

| 类型                          | 颜色      |
| --------------------------- | ------- |
| `underfitting`              | orange  |
| `overfitting_risk`          | red     |
| `feature_insufficiency`     | purple  |
| `model_mismatch`            | volcano |
| `hpo_insufficient`          | gold    |
| `validation_instability`    | magenta |
| `data_quality_limitation`   | cyan    |
| `weak_baseline_improvement` | blue    |

---

## 22. LLM 安全与可控性要求

### 22.1 禁止事项

本模块绝对禁止：

1. 让 LLM 输出训练代码；
2. 让 LLM 修改 workflow；
3. 让 LLM 修改 pipeline；
4. 让 LLM 生成 search space 代码；
5. 让 LLM 直接决定最终模型；
6. 让 LLM 直接触发 closed-loop execution；
7. 让 LLM 覆盖系统指标；
8. 让 LLM 访问任意文件路径；
9. 让 LLM 输出 shell command；
10. 将 LLM 原始输出直接写入业务结果。

---

### 22.2 LLM 失败降级

如果 LLM 调用失败：

* 不应破坏上游 Metric Evaluation 结果；
* 可使用 `system_diagnostic_checker` 输出 fallback diagnosis；
* 状态设为 `fallback_diagnosed`；
* `ready_for_closed_loop_refinement` 根据系统规则判断；
* 前端展示 LLM unavailable，但系统诊断仍可用。

---

## 23. 异常设计

建议新增异常：

| 异常类                                 | error_code                                  | 场景               |
| ----------------------------------- | ------------------------------------------- | ---------------- |
| `ResultDiagnosisNotFoundException`  | `RESULT_DIAGNOSIS_NOT_FOUND`                | 找不到诊断记录          |
| `MetricEvaluationRequiredException` | `METRIC_EVALUATION_REQUIRED`                | 缺少上游评估           |
| `MetricEvaluationNotReadyException` | `METRIC_EVALUATION_NOT_READY_FOR_DIAGNOSIS` | 上游未 ready        |
| `DiagnosisInputInvalidException`    | `RESULT_DIAGNOSIS_INPUT_INVALID`            | 输入合同无效           |
| `DiagnosticContextBuildException`   | `DIAGNOSTIC_CONTEXT_BUILD_FAILED`           | 上下文构建失败          |
| `LLMDiagnosisCallException`         | `LLM_DIAGNOSIS_CALL_FAILED`                 | LLM 调用失败         |
| `LLMDiagnosisParseException`        | `LLM_DIAGNOSIS_PARSE_FAILED`                | LLM 输出解析失败       |
| `LLMDiagnosisValidationException`   | `LLM_DIAGNOSIS_VALIDATION_FAILED`           | LLM 输出校验失败       |
| `ClosedLoopInputBuildException`     | `CLOSED_LOOP_REFINEMENT_INPUT_BUILD_FAILED` | 下游输入构建失败         |
| `DiagnosisArtifactSaveException`    | `DIAGNOSIS_ARTIFACT_SAVE_FAILED`            | 诊断 artifact 保存失败 |

---

## 24. MVP 验收标准

### 24.1 后端验收标准

必须满足：

1. 可以通过 API 启动 Result Diagnosis；
2. 必须校验上游 `ready_for_result_diagnosis = true`；
3. 必须读取 `result_diagnosis_input_json`；
4. 可以补充读取 metric evaluation / pipeline execution / dataset profile 等上下文；
5. 能构建 LLM 诊断 prompt；
6. LLM 输出必须为结构化 JSON；
7. LLM 输出必须经过 parser、validator、normalizer；
8. 能识别至少 6 类问题：欠拟合、过拟合风险、特征不足、模型不匹配、HPO 不足、验证不稳定；
9. 每个 finding 必须包含 evidence；
10. 能生成 refinement recommendations；
11. 能生成 `closed_loop_refinement_input_json`；
12. 能持久化诊断结果；
13. LLM 调用失败时能 fallback 到 system rule-based diagnosis；
14. 不能输出或执行代码；
15. 不能修改任何上游 artifact 或 pipeline。

---

### 24.2 前端验收标准

必须满足：

1. 新增 Result Diagnosis 面板；
2. 可以点击 Run Diagnosis；
3. 可以点击 Re-run Diagnosis；
4. 可以展示 overall assessment；
5. 可以展示 diagnostic findings；
6. 可以展示 evidence；
7. 可以展示 root cause hypotheses；
8. 可以展示 refinement recommendations；
9. 可以展示 closed-loop refinement input；
10. 可以展示 LLM diagnosis 状态；
11. 可以展示 warnings / errors；
12. 可以查看完整 JSON。

---

### 24.3 安全验收标准

必须满足：

1. LLM 不得输出可执行代码；
2. LLM 不得修改 workflow；
3. LLM 不得修改 pipeline；
4. LLM 不得覆盖 metric result；
5. LLM 不得决定最终模型；
6. LLM 输出必须经过安全扫描；
7. Closed-loop input 只能是结构化建议，不是执行指令；
8. 所有失败必须持久化。

---

## 25. 推荐实现优先级

### P0：必须完成

1. 后端 `result_diagnosis` 模块目录；
2. `ResultDiagnosis` 数据表；
3. `context_builder`；
4. `diagnosis_input_loader`；
5. `diagnostic_context_builder`；
6. `system_diagnostic_checker`；
7. `llm_prompt_builder`；
8. `llm_result_diagnoser`；
9. `llm_response_parser`；
10. `llm_diagnosis_validator`；
11. `llm_diagnosis_normalizer`；
12. `refinement_input_builder`；
13. 核心 API；
14. 前端主面板；
15. Diagnostic Findings 表；
16. Refinement Recommendations 表；
17. Closed-loop Input 展示。

---

### P1：建议完成

1. Evidence Summary 细分展示；
2. Root Cause Hypothesis 卡片；
3. LLM fallback 展示；
4. 诊断 artifact 保存；
5. 系统规则诊断阈值配置；
6. 更完整的 prompt profile：compact / standard / full。

---

### P2：后续迭代

1. 多轮 LLM 诊断；
2. 历史实验对比诊断；
3. 与 Closed-loop Refinement 深度联动；
4. 自动生成 refinement proposal；
5. 支持跨实验诊断；
6. 支持论文风格分析摘要；
7. 支持材料领域知识增强诊断。

---

## 26. 总结

**LLM-based Result Diagnosis** 是 MLAgent 从“模型评估”进入“自我改进闭环”的关键模块。

它的核心价值是：

```text
把 Metric Evaluation 输出的评估事实，转化为结构化、可解释、可进入闭环优化的机器学习问题诊断。
```

本模块必须坚持：

```text
只诊断，不训练；
只建议，不修改；
LLM 深度参与，但不直接执行；
所有 LLM 输出必须结构化、可校验、可追踪；
Closed-loop Refinement 才负责生成下一轮改进方案。
```

完成本模块后，MLAgent 将具备从自动训练评估到智能诊断的能力，并为下一步 **Closed-loop Refinement** 提供稳定、结构化、可控的输入基础。
