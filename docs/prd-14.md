# PRD：Final Pipeline Selection 模块

> 项目名称：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：14
> 模块名称：Final Pipeline Selection
> 中文名称：最终 Pipeline 选择
> 上游模块：LLM-driven Workflow Refinement
> 下游模块：Interpretability Analysis
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0
> 输出格式：Markdown

---

## 1. 背景与上下文

当前 MLAgent 已完成从任务输入到闭环工作流精炼的核心链路：

```text
1. Task Specification
2. LLM-based Task Interpretation
3. Dataset Loading, Checking, and Profiling
4. LLM-guided Workflow Planning
5. Automated Feature Engineering
6. Feature Preprocessing
7. Model Search Context Update
8. Automated Model and HPO Search
9. Executable Pipeline Generation
10. Pipeline Execution and Training
11. Metric Evaluation
12. LLM-based Result Diagnosis
13. LLM-driven Workflow Refinement
```

模块 13 **LLM-driven Workflow Refinement** 已经根据诊断结果做出闭环决策：

```text
decision = proceed_next_stage
```

或：

```text
decision = iterate_refinement
```

当模块 13 判断当前实验结果已经足够进入最终选择阶段时，会输出：

```text
final_pipeline_selection_input_json
```

本模块 **Final Pipeline Selection** 的核心任务是：

> 在所有候选实验、评价指标、训练产物、Pipeline 记录、用户约束和 Workflow Refinement 决策基础上，选择唯一的最终 Pipeline、最终模型、最佳 trial 和最佳参数，并生成下游 Interpretability Analysis 的正式输入。

同时，MVP 阶段必须引入 **LLM Selection Explainer**。LLM 不参与最终选择本身，但需要在系统完成选择后：

1. 解释为什么选择该 pipeline；
2. 总结候选 pipeline 差异；
3. 生成自然语言选择理由；
4. 提醒人类关注潜在风险。

---

## 2. 模块定位

### 2.1 一句话定义

**Final Pipeline Selection 是 MLAgent 中负责从多轮实验结果中选择最终 Pipeline 的系统决策模块。系统基于指标、稳定性、baseline improvement、约束、artifact 完整性、可解释性和成本完成最终选择；LLM 在系统选择完成后负责解释选择理由、总结候选差异并提示潜在风险。**

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
LLM-based Result Diagnosis
  ↓
LLM-driven Workflow Refinement
  ↓
Final Pipeline Selection   ← 当前模块
  ↓
Interpretability Analysis
  ↓
Final Output
```

---

## 4. 模块核心职责

Final Pipeline Selection 需要完成以下工作：

1. 消费模块 13 输出的 `final_pipeline_selection_input_json`；
2. 校验 `WorkflowRefinement.decision = proceed_next_stage`；
3. 校验 `ready_for_final_pipeline_selection = true`；
4. 收集候选 Metric Evaluation 记录；
5. 收集候选 Pipeline Execution 记录；
6. 收集候选 Pipeline Generation 记录；
7. 构建 trial-level candidate list；
8. 校验候选 trial、model、pipeline spec 和 artifact 完整性；
9. 根据 selection policy 计算综合选择分数；
10. 生成候选排序；
11. 选择最终 pipeline；
12. 选择最终 model；
13. 选择最终 trial；
14. 选择最终 hyperparameters；
15. 生成系统结构化选择理由；
16. 调用 LLM Selection Explainer 生成自然语言解释；
17. 总结候选 pipeline 差异；
18. 生成 human review notes 和 risk notes；
19. 生成 final artifact manifest；
20. 生成 `interpretability_analysis_input_json`；
21. 持久化完整选择结果；
22. 前端展示最终选择、候选排序、选择理由、LLM 解释、风险提示、artifact 清单和下游输入。

---

## 5. 与上下游模块的边界

### 5.1 与 LLM-driven Workflow Refinement 的边界

Workflow Refinement 负责：

* 判断是否进入最终选择；
* 输出 `final_pipeline_selection_input_json`；
* 提供候选 metric evaluation ids；
* 提供候选 pipeline execution ids；
* 提供当前 best model / trial / pipeline spec；
* 提供 selection policy 和 constraints。

Final Pipeline Selection 负责：

* 消费 `final_pipeline_selection_input_json`；
* 收集候选实验完整结果；
* 执行最终选择；
* 生成最终 pipeline selection result；
* 生成 Interpretability Analysis 输入；
* 调用 LLM 解释系统选择结果。

Final Pipeline Selection 不负责：

* 重新判断是否需要迭代；
* 重新生成 WorkflowPlan；
* 重新触发前序模块；
* 修改 Workflow Refinement 决策。

---

### 5.2 与 Metric Evaluation 的边界

Metric Evaluation 负责：

* fold-level metrics；
* trial-level metrics；
* pipeline/model-level metrics；
* model ranking；
* baseline comparison；
* best trial / best model 初步标记。

Final Pipeline Selection 负责：

* 跨实验轮次比较候选；
* 综合指标、稳定性、成本、可解释性和约束；
* 最终确定唯一 pipeline；
* 生成最终选择理由。

Final Pipeline Selection 不重新计算指标。

---

### 5.3 与 Pipeline Execution 的边界

Pipeline Execution 负责：

* 训练模型；
* 生成预测；
* 保存 model artifact；
* 保存 prediction artifact；
* 记录 runtime 和 trial 状态。

Final Pipeline Selection 负责：

* 校验最终候选的 model artifact 是否存在；
* 校验 prediction artifact 是否存在；
* 引用训练产物；
* 生成最终 artifact manifest。

Final Pipeline Selection 不重新训练模型，不重新预测。

---

### 5.4 与 Interpretability Analysis 的边界

Final Pipeline Selection 输出：

```text
interpretability_analysis_input_json
```

Interpretability Analysis 负责：

* 加载最终模型；
* 加载最终特征矩阵；
* 执行 feature importance / SHAP 分析；
* 生成材料规律解释。

Final Pipeline Selection 不执行解释性分析。

---

## 6. 核心设计原则

### 6.1 系统负责最终选择，LLM 负责解释

本模块采用：

```text
System Selector + LLM Selection Explainer
```

其中：

```text
System Selector
```

负责：

* 候选收集；
* 候选校验；
* 约束检查；
* scoring；
* ranking；
* final selection；
* artifact 校验；
* 下游输入构建。

```text
LLM Selection Explainer
```

负责：

* 解释为什么选择该 pipeline；
* 总结候选 pipeline 差异；
* 生成自然语言选择理由；
* 提醒人类关注潜在风险。

LLM 不允许：

* 修改最终选择；
* 修改 candidate ranking；
* 修改 selection score；
* 修改 metric values；
* 修改 artifact path；
* 选择未被系统选中的 pipeline；
* 重新排序候选；
* 重新计算指标；
* 触发训练、评估或解释性分析；
* 输出可执行代码。

---

### 6.2 最终选择必须可复现

本模块必须记录：

* selection policy；
* candidate list；
* candidate ranking；
* scoring components；
* constraint check result；
* final selected pipeline；
* final model；
* final trial；
* final hyperparameters；
* final artifact manifest；
* system selection reason；
* LLM selection explanation；
* LLM raw request / response；
* 上游 WorkflowRefinement / MetricEvaluation / PipelineExecution / PipelineGeneration ID。

---

### 6.3 不能只看单一最优指标

最终选择不能简单等同于 primary metric 最优。

需要综合考虑：

```text
primary metric
stability
baseline improvement
interpretability
runtime cost
artifact completeness
user constraints
task constraints
```

例如：

* 某模型 MAE 最低，但 fold variance 很高，可能不适合作为最终选择；
* 某复杂模型略优于 ridge，但解释性弱、成本高，可能不符合 interpretability priority；
* 某 trial 指标优秀，但 model artifact 缺失，不能作为最终 pipeline。

---

### 6.4 Final Selection 不触发新一轮迭代

进入本模块的前提是：

```text
WorkflowRefinement.decision = proceed_next_stage
```

因此，本模块不再触发迭代。

如果发现候选不完整或 artifact 缺失，应：

* 标记失败；
* 或 `selected_with_warning`；
* 或要求人工处理；

但不自动回到前序模块。

---

## 7. 产品目标

### 7.1 MVP 目标

MVP 阶段需要实现：

1. 读取最新或指定 `WorkflowRefinement`；
2. 校验 `decision = proceed_next_stage`；
3. 校验 `ready_for_final_pipeline_selection = true`；
4. 加载 `final_pipeline_selection_input_json`；
5. 收集候选 Metric Evaluation；
6. 收集候选 Pipeline Execution；
7. 收集候选 Pipeline Generation；
8. 构建 trial-level candidates；
9. 校验候选完整性；
10. 构建 selection policy；
11. 执行 constraint check；
12. 计算 candidate selection score；
13. 输出 candidate ranking；
14. 选择 final pipeline / model / trial / params；
15. 解析 final artifact manifest；
16. 构建 system selection reason；
17. 调用 LLM Selection Explainer；
18. 生成 LLM natural language explanation；
19. 生成 candidate difference summary；
20. 生成 human review notes；
21. 生成 risk notes；
22. 构建 `interpretability_analysis_input_json`；
23. 持久化完整结果；
24. 前端展示所有核心结果。

---

### 7.2 非目标

MVP 阶段不做：

1. 不重新训练模型；
2. 不重新预测；
3. 不重新计算指标；
4. 不重新运行 HPO；
5. 不重新生成 PipelineSpec；
6. 不重新生成 WorkflowPlan；
7. 不执行 SHAP；
8. 不执行 feature importance；
9. 不生成最终报告；
10. 不部署模型；
11. 不允许用户手动修改最终选择结果；
12. 不允许 LLM 覆盖系统选择。

---

## 8. 输入设计

### 8.1 API 请求输入

接口：

```text
POST /api/final-pipeline-selections/{task_id}
```

请求字段：

| 字段                                  | 类型      | 必填 | 说明                                                                        |
| ----------------------------------- | ------- | -: | ------------------------------------------------------------------------- |
| `workflow_refinement_id`            | string  |  否 | 指定 WorkflowRefinement；为空则使用最新 ready 记录                                    |
| `force_rerun`                       | boolean |  否 | 是否强制重新选择，默认 false                                                         |
| `selection_profile`                 | string  |  否 | `metric_first` / `balanced` / `interpretable` / `efficient`，默认 `balanced` |
| `use_llm_explainer`                 | boolean |  否 | 是否调用 LLM 解释器，MVP 默认 true                                                  |
| `allow_baseline_as_final`           | boolean |  否 | 是否允许 baseline 成为最终模型，默认 true                                              |
| `min_baseline_improvement_required` | boolean |  否 | 是否要求候选必须超过 baseline，默认 false                                              |
| `stability_weight`                  | float   |  否 | 稳定性权重                                                                     |
| `interpretability_weight`           | float   |  否 | 可解释性权重                                                                    |
| `cost_weight`                       | float   |  否 | 成本权重                                                                      |
| `require_model_artifact`            | boolean |  否 | 是否要求模型 artifact 存在，默认 true                                                |
| `require_prediction_artifact`       | boolean |  否 | 是否要求 prediction artifact 存在，默认 true                                       |
| `notes`                             | string  |  否 | 用户备注                                                                      |

---

### 8.2 必需上游输入

| 来源                                    | 必需字段                                                                                                                                                                                        |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WorkflowRefinement`                  | `id`, `task_id`, `decision`, `ready_for_final_pipeline_selection`, `final_pipeline_selection_input_json`                                                                                    |
| `final_pipeline_selection_input_json` | `candidate_metric_evaluation_ids`, `candidate_pipeline_execution_ids`, `current_best_model_id`, `current_best_trial_id`, `current_best_pipeline_spec_id`, `selection_policy`, `constraints` |
| `MetricEvaluation`                    | `evaluation_json`, `metric_summary_json`, `model_ranking_json`, `best_trial_id`, `best_model_id`, `best_pipeline_spec_id`, `best_primary_metric_value`                                      |
| `PipelineExecution`                   | `execution_json`, `training_artifact_manifest`, `trial_results`, `pipeline_run_results`                                                                                                     |
| `PipelineGeneration`                  | `pipeline_json`, `pipeline_specs`, `pipeline_bundle`, `execution_input_json`                                                                                                                |
| `ModelSearchPlan`                     | `plan_json`, `candidate_model_plan`, `hpo_plan`, `search_space_plan`                                                                                                                        |
| `FeaturePreprocessing`                | `model_ready_artifact_path`, `preprocessor_artifact_path`, `preprocessing_json`                                                                                                             |
| `FeatureEngineering`                  | `artifact_path`, `feature_json`                                                                                                                                                             |
| `DatasetProfile`                      | `profile_json`                                                                                                                                                                              |
| `TaskSpecification`                   | `task_spec_json`                                                                                                                                                                            |

---

## 9. 输出设计

### 9.1 核心输出：FinalPipelineSelectionResponse

| 字段                                    | 类型          | 说明                                                  |
| ------------------------------------- | ----------- | --------------------------------------------------- |
| `final_pipeline_selection_id`         | string      | 最终选择记录 ID，例如 `fps_xxxxxxxx`                         |
| `task_id`                             | string      | 任务 ID                                               |
| `workflow_refinement_id`              | string      | 上游 WorkflowRefinement ID                            |
| `metric_evaluation_id`                | string      | 最终候选所属 MetricEvaluation                             |
| `pipeline_execution_id`               | string      | 最终候选所属 PipelineExecution                            |
| `pipeline_generation_id`              | string      | 最终候选所属 PipelineGeneration                           |
| `status`                              | string      | `selected` / `selected_with_warning` / `failed`     |
| `selection_profile`                   | string      | metric_first / balanced / interpretable / efficient |
| `final_pipeline_spec_id`              | string      | 最终 PipelineSpec ID                                  |
| `final_model_id`                      | string      | 最终模型 ID                                             |
| `final_model_family`                  | string      | 最终模型族                                               |
| `final_trial_id`                      | string      | 最终 trial ID                                         |
| `final_trial_type`                    | string      | baseline / fixed_params / hpo                       |
| `final_hyperparameters`               | object      | 最终超参数                                               |
| `primary_metric`                      | string      | 主指标                                                 |
| `primary_metric_value`                | float       | 最终主指标值                                              |
| `metric_direction`                    | string      | minimize / maximize                                 |
| `secondary_metrics`                   | object      | 次指标                                                 |
| `stability_summary`                   | object      | 稳定性摘要                                               |
| `baseline_comparison`                 | object      | 与 baseline 对比                                       |
| `selection_score`                     | float       | 综合选择评分                                              |
| `candidate_ranking`                   | array       | 候选排序                                                |
| `constraint_check_result`             | object      | 约束检查结果                                              |
| `system_selection_reason`             | object      | 系统结构化选择理由                                           |
| `llm_selection_explanation`           | object      | LLM 自然语言解释                                          |
| `candidate_difference_summary`        | array       | LLM 总结的候选差异                                         |
| `human_review_notes`                  | array       | 人类审核关注点                                             |
| `risk_notes`                          | array       | 潜在风险提示                                              |
| `llm_used`                            | boolean     | 是否调用 LLM                                            |
| `llm_confidence_level`                | string      | low / medium / high                                 |
| `final_artifact_manifest`             | object      | 最终 artifact 清单                                      |
| `interpretability_analysis_input`     | object      | 下游解释性分析输入                                           |
| `ready_for_interpretability_analysis` | boolean     | 是否可进入解释性分析                                          |
| `warnings`                            | array       | 警告                                                  |
| `error_message`                       | string/null | 错误信息                                                |
| `created_at`                          | datetime    | 创建时间                                                |
| `updated_at`                          | datetime    | 更新时间                                                |

---

## 10. 核心数据结构设计

### 10.1 FinalSelectedPipeline

```json
{
  "final_pipeline_spec_id": "ps_ridge_28d4dd",
  "final_model_id": "ridge",
  "final_model_family": "ridge",
  "final_trial_id": "trial_ridge_0003",
  "final_trial_type": "hpo",
  "final_hyperparameters": {
    "alpha": 1.0
  },
  "source_metric_evaluation_id": "me_xxxxxxxx",
  "source_pipeline_execution_id": "pe_xxxxxxxx",
  "source_pipeline_generation_id": "pg_xxxxxxxx"
}
```

---

### 10.2 CandidateSelectionItem

| 字段                           | 类型          | 说明                                       |
| ---------------------------- | ----------- | ---------------------------------------- |
| `candidate_id`               | string      | 候选 ID，建议使用 trial_id                      |
| `metric_evaluation_id`       | string      | 评估 ID                                    |
| `pipeline_execution_id`      | string      | 执行 ID                                    |
| `pipeline_generation_id`     | string      | Pipeline Generation ID                   |
| `pipeline_spec_id`           | string      | PipelineSpec ID                          |
| `trial_id`                   | string      | Trial ID                                 |
| `model_id`                   | string      | 模型 ID                                    |
| `model_family`               | string      | 模型族                                      |
| `pipeline_role`              | string      | baseline / candidate / hpo_candidate     |
| `trial_type`                 | string      | baseline / fixed_params / hpo            |
| `hyperparameters`            | object      | trial 参数                                 |
| `primary_metric_value`       | float       | 主指标值                                     |
| `primary_metric_rank`        | integer     | 主指标排名                                    |
| `stability_score`            | float       | 稳定性得分                                    |
| `baseline_improvement_score` | float       | baseline 提升得分                            |
| `interpretability_score`     | float       | 可解释性得分                                   |
| `cost_score`                 | float       | 成本得分                                     |
| `constraint_score`           | float       | 约束得分                                     |
| `selection_score`            | float       | 综合得分                                     |
| `selection_rank`             | integer     | 最终选择排名                                   |
| `candidate_status`           | string      | eligible / selected / rejected / warning |
| `is_final_selected`          | boolean     | 是否最终选中                                   |
| `rejection_reason`           | string/null | 未被选中的原因                                  |

---

### 10.3 SelectionPolicy

```json
{
  "selection_profile": "balanced",
  "primary_metric_weight": 0.5,
  "stability_weight": 0.2,
  "baseline_improvement_weight": 0.15,
  "interpretability_weight": 0.1,
  "cost_weight": 0.05,
  "constraint_weight": 0.0,
  "require_model_artifact": true,
  "require_prediction_artifact": true,
  "allow_baseline_as_final": true,
  "tie_breaker_order": [
    "primary_metric",
    "stability",
    "interpretability",
    "cost"
  ]
}
```

---

### 10.4 SystemSelectionReason

| 字段                        | 类型     | 说明             |
| ------------------------- | ------ | -------------- |
| `main_reason`             | string | 系统主选择理由        |
| `metric_reason`           | string | 指标表现理由         |
| `stability_reason`        | string | 稳定性理由          |
| `baseline_reason`         | string | baseline 对比理由  |
| `interpretability_reason` | string | 可解释性理由         |
| `cost_reason`             | string | 成本理由           |
| `constraint_reason`       | string | 约束满足理由         |
| `artifact_reason`         | string | artifact 完整性理由 |
| `tradeoff_summary`        | string | 综合权衡说明         |

---

### 10.5 LLMSelectionExplanation

```json
{
  "why_selected": "The selected ridge pipeline achieved the best balance between MAE, fold stability, interpretability, and training cost.",
  "candidate_difference_summary": [
    {
      "candidate": "ridge_hpo",
      "summary": "Best overall trade-off with strong metric performance and high interpretability."
    },
    {
      "candidate": "random_forest_hpo",
      "summary": "Competitive metric performance but lower interpretability and higher training cost."
    },
    {
      "candidate": "dummy_mean_baseline",
      "summary": "Useful baseline but substantially weaker than candidate models."
    }
  ],
  "selection_rationale_natural_language": "The final pipeline was selected because it provides a robust improvement over baseline while maintaining good stability across folds. Although some nonlinear models were competitive, the selected model better matches the interpretability preference.",
  "human_review_notes": [
    "Review whether the improvement over baseline is meaningful for the specific materials science objective.",
    "If the dataset is small, interpret fold-level stability cautiously.",
    "Before final reporting, verify that important features are scientifically meaningful."
  ],
  "risk_notes": [
    "The final model may still be limited by the current feature representation.",
    "The final choice is based on validation results rather than an external test set."
  ],
  "confidence_level": "medium"
}
```

---

### 10.6 FinalArtifactManifest

| 字段                           | 类型     | 说明                           |
| ---------------------------- | ------ | ---------------------------- |
| `model_artifact_path`        | string | 最终模型 artifact                |
| `prediction_artifact_paths`  | array  | 最终预测结果                       |
| `preprocessor_artifact_path` | string | 预处理 pipeline artifact        |
| `model_ready_matrix_path`    | string | 模型就绪矩阵                       |
| `feature_matrix_path`        | string | 特征矩阵                         |
| `metric_results_path`        | string | 指标结果 artifact                |
| `selection_result_path`      | string | selection result artifact    |
| `workflow_trace_paths`       | object | 上游 trace artifact 路径         |
| `artifact_integrity_status`  | string | complete / partial / missing |

---

### 10.7 InterpretabilityAnalysisInput

| 字段                                     | 类型      | 说明                          |
| -------------------------------------- | ------- | --------------------------- |
| `final_pipeline_selection_id`          | string  | 当前最终选择 ID                   |
| `task_id`                              | string  | 任务 ID                       |
| `task_type`                            | string  | regression / classification |
| `target_column`                        | string  | 目标列                         |
| `final_model_id`                       | string  | 最终模型 ID                     |
| `final_model_family`                   | string  | 最终模型族                       |
| `final_trial_id`                       | string  | 最终 trial                    |
| `final_pipeline_spec_id`               | string  | 最终 PipelineSpec             |
| `model_artifact_path`                  | string  | 模型 artifact                 |
| `model_ready_matrix_path`              | string  | 模型就绪特征矩阵                    |
| `feature_columns`                      | array   | 特征列                         |
| `prediction_artifact_paths`            | array   | 预测结果                        |
| `preprocessor_artifact_path`           | string  | 预处理 artifact                |
| `primary_metric`                       | string  | 主指标                         |
| `primary_metric_value`                 | float   | 主指标值                        |
| `secondary_metrics`                    | object  | 次指标                         |
| `interpretability_methods_recommended` | array   | 推荐解释方法                      |
| `selection_reason_summary`             | string  | 最终选择摘要                      |
| `ready_for_interpretability_analysis`  | boolean | 是否可进入解释性分析                  |

---

## 11. Selection Score 设计

### 11.1 综合评分公式

候选综合分数建议为：

```text
selection_score =
    primary_metric_score * primary_metric_weight
  + stability_score * stability_weight
  + baseline_improvement_score * baseline_improvement_weight
  + interpretability_score * interpretability_weight
  + cost_score * cost_weight
  + constraint_score * constraint_weight
```

所有子分数标准化到 `[0, 1]`。

---

### 11.2 Primary Metric Score

根据 `metric_direction` 处理：

| metric_direction | 规则        |
| ---------------- | --------- |
| minimize         | 指标越低，得分越高 |
| maximize         | 指标越高，得分越高 |

MVP 可采用 rank-based score：

```text
score = 1 - (rank - 1) / max(n_candidates - 1, 1)
```

---

### 11.3 Stability Score

| 情况          |  分数 |
| ----------- | --: |
| fold std 很低 | 1.0 |
| fold std 中等 | 0.6 |
| fold std 很高 | 0.2 |
| 无 fold 信息   | 0.5 |

---

### 11.4 Baseline Improvement Score

| 情况            |  分数 |
| ------------- | --: |
| 明显优于 baseline | 1.0 |
| 略优于 baseline  | 0.7 |
| 与 baseline 接近 | 0.5 |
| 差于 baseline   | 0.2 |
| 无 baseline    | 0.5 |

---

### 11.5 Interpretability Score

| 模型族                                  |                分数 |
| ------------------------------------ | ----------------: |
| linear / ridge / lasso / elastic_net |               1.0 |
| random_forest                        |               0.7 |
| gradient_boosting / xgboost          |               0.5 |
| svr / knn                            |               0.4 |
| dummy_mean                           | 0.8，但仅作为 baseline |

若用户选择 `interpretable` profile，应提高 interpretability weight。

---

### 11.6 Cost Score

| 情况        |  分数 |
| --------- | --: |
| 训练快、模型简单  | 1.0 |
| 成本中等      | 0.7 |
| 成本较高      | 0.4 |
| 成本极高或多次失败 | 0.2 |

---

### 11.7 Constraint Score

硬约束不满足时，候选不可选。

软约束不满足时，可以扣分并生成 warning。

---

## 12. LLM Selection Explainer 设计

### 12.1 运行时机

LLM Selection Explainer 必须在以下步骤之后运行：

```text
candidate scoring
candidate ranking
final selected candidate determined
system selection reason generated
artifact manifest resolved
```

即：

```text
系统先选择，LLM 后解释
```

---

### 12.2 LLM 输入上下文

LLM Selection Explainer 应接收摘要信息，不需要接收完整大 JSON。

建议输入：

1. task summary；
2. selected pipeline summary；
3. selected model summary；
4. selected trial summary；
5. primary metric and secondary metrics；
6. candidate ranking top N；
7. baseline comparison；
8. stability summary；
9. selection score components；
10. system selection reason；
11. constraint check result；
12. artifact completeness summary；
13. rejected candidates summary；
14. user preferences / selection profile。

---

### 12.3 LLM 输出内容

LLM 必须输出：

1. `why_selected`；
2. `candidate_difference_summary`；
3. `selection_rationale_natural_language`；
4. `human_review_notes`；
5. `risk_notes`；
6. `confidence_level`。

---

### 12.4 LLM Prompt 核心规则

Prompt 必须明确：

```text
You are an explanation assistant for final pipeline selection.

The final pipeline has already been selected by the system.

You must not change the selected pipeline.
You must not change candidate ranking.
You must not modify metric values.
You must not recommend another pipeline as the final selected one.
You must only explain why the system selected this pipeline, summarize candidate differences, and highlight human-review risks.
You must not output executable code.
```

---

### 12.5 LLM 输出安全校验

必须扫描并禁止以下内容：

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

禁止字段：

```text
python_code
script
shell_command
sql
change_selection
new_ranking
override_score
modified_metric
selected_pipeline_override
```

如果 LLM 输出不安全或不符合 schema：

* 不采纳 LLM 输出；
* 使用 `system_selection_reason` 作为 fallback；
* 状态可设为 `selected_with_warning`；
* `llm_selection_explanation.review_status = failed_or_fallback`；
* `ready_for_interpretability_analysis` 不受影响。

---

## 13. 后端功能设计

### 13.1 推荐目录结构

```text
backend/app/modules/final_pipeline_selection/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── selection_input_loader.py
    ├── candidate_collector.py
    ├── candidate_validator.py
    ├── selection_policy_builder.py
    ├── candidate_scorer.py
    ├── final_ranker.py
    ├── artifact_resolver.py
    ├── constraint_checker.py
    ├── selection_reason_builder.py
    ├── llm_selection_prompt_builder.py
    ├── llm_selection_explainer.py
    ├── llm_selection_explanation_parser.py
    ├── llm_selection_explanation_validator.py
    ├── llm_selection_explanation_normalizer.py
    ├── interpretability_input_builder.py
    ├── final_selection_artifact_manager.py
    └── builder.py
```

---

### 13.2 文件职责说明

| 文件                                        | 职责                                                |
| ----------------------------------------- | ------------------------------------------------- |
| `api.py`                                  | Final Pipeline Selection REST API                 |
| `service.py`                              | 主流程编排                                             |
| `model.py`                                | SQLModel 数据表                                      |
| `repository.py`                           | CRUD 与 latest 查询                                  |
| `schemas.py`                              | 请求、响应、内部 DTO                                      |
| `enums.py`                                | 状态、选择 profile、约束状态等枚举                             |
| `exceptions.py`                           | 专用异常                                              |
| `context_builder.py`                      | 读取 WorkflowRefinement 并校验 ready                   |
| `selection_input_loader.py`               | 加载 `final_pipeline_selection_input_json`          |
| `candidate_collector.py`                  | 收集候选 MetricEvaluation / PipelineExecution / Trial |
| `candidate_validator.py`                  | 校验候选完整性                                           |
| `selection_policy_builder.py`             | 构建 selection policy                               |
| `candidate_scorer.py`                     | 计算候选综合评分                                          |
| `final_ranker.py`                         | 排序并选出最终 pipeline                                  |
| `artifact_resolver.py`                    | 校验最终 artifact 路径                                  |
| `constraint_checker.py`                   | 校验用户约束与系统约束                                       |
| `selection_reason_builder.py`             | 生成系统结构化选择理由                                       |
| `llm_selection_prompt_builder.py`         | 构建 LLM explanation prompt                         |
| `llm_selection_explainer.py`              | 调用 LLM 生成解释                                       |
| `llm_selection_explanation_parser.py`     | 解析 LLM 输出                                         |
| `llm_selection_explanation_validator.py`  | 校验 LLM 输出结构与安全                                    |
| `llm_selection_explanation_normalizer.py` | 标准化 LLM 输出                                        |
| `interpretability_input_builder.py`       | 构建下游 Interpretability Analysis 输入                 |
| `final_selection_artifact_manager.py`     | 保存 selection artifacts                            |
| `builder.py`                              | 构建最终响应                                            |

---

## 14. 后端主流程

```text
FinalPipelineSelectionService.create_final_selection(task_id, request)
    ↓
1. build_final_selection_context()
    ↓
2. load_final_pipeline_selection_input()
    ↓
3. collect_candidate_experiments()
    ↓
4. validate_candidates()
    ↓
5. build_selection_policy()
    ↓
6. check_constraints()
    ↓
7. score_candidates()
    ↓
8. rank_candidates()
    ↓
9. select_final_pipeline()
    ↓
10. resolve_final_artifacts()
    ↓
11. build_system_selection_reason()
    ↓
12. build_llm_selection_explanation_context()
    ↓
13. call_llm_selection_explainer()
    ↓
14. parse_llm_selection_explanation()
    ↓
15. validate_llm_selection_explanation()
    ↓
16. normalize_llm_selection_explanation()
    ↓
17. build_interpretability_analysis_input()
    ↓
18. save_selection_artifacts()
    ↓
19. build_response()
    ↓
20. persist()
```

---

### 14.1 Step 1：构建选择上下文

`context_builder.py` 负责：

* 根据 `task_id` 获取最新 WorkflowRefinement；
* 或根据 `workflow_refinement_id` 获取指定记录；
* 校验：

  * `decision = proceed_next_stage`；
  * `ready_for_final_pipeline_selection = true`；
  * `final_pipeline_selection_input_json` 存在；
* 关联读取：

  * MetricEvaluation；
  * PipelineExecution；
  * PipelineGeneration；
  * WorkflowPlan；
  * TaskSpecification。

失败场景：

| 场景                             | error_code                                          |
| ------------------------------ | --------------------------------------------------- |
| 找不到 WorkflowRefinement         | `WORKFLOW_REFINEMENT_NOT_FOUND`                     |
| WorkflowRefinement 未 ready     | `WORKFLOW_REFINEMENT_NOT_READY_FOR_FINAL_SELECTION` |
| decision 不是 proceed_next_stage | `WORKFLOW_REFINEMENT_NOT_PROCEED_DECISION`          |
| final input 缺失                 | `FINAL_PIPELINE_SELECTION_INPUT_MISSING`            |

---

### 14.2 Step 2：加载 Final Pipeline Selection Input

`selection_input_loader.py` 负责校验：

* `candidate_metric_evaluation_ids` 非空；
* `candidate_pipeline_execution_ids` 非空；
* `current_best_model_id` 存在；
* `current_best_trial_id` 存在；
* `current_best_pipeline_spec_id` 存在；
* `selection_policy` 存在；
* `constraints` 存在；
* `ready_for_final_pipeline_selection = true`。

---

### 14.3 Step 3：收集候选实验

`candidate_collector.py` 负责：

* 加载所有候选 MetricEvaluation；
* 加载所有候选 PipelineExecution；
* 从 `evaluation_json` 中提取：

  * trial_metric_results；
  * pipeline_metric_results；
  * model_ranking；
  * baseline_comparison；
* 从 `execution_json` 中提取：

  * trial_results；
  * pipeline_run_results；
  * artifact paths；
  * params；
  * model artifact；
  * prediction artifact；
* 生成统一候选列表。

候选粒度：

```text
trial-level candidate
```

---

### 14.4 Step 4：候选完整性校验

`candidate_validator.py` 检查：

1. trial 状态是否 completed；
2. trial 是否有 metric result；
3. trial 是否有 primary metric；
4. pipeline_spec_id 是否存在；
5. model_id 是否存在；
6. model artifact 是否存在；
7. prediction artifact 是否存在；
8. candidate 是否属于允许任务类型；
9. 是否违反用户硬约束；
10. 是否能构建下游 interpretability input。

---

### 14.5 Step 5：构建 Selection Policy

`selection_policy_builder.py` 合并策略来源：

```text
请求参数 > WorkflowRefinement.selection_policy > TaskSpecification.user_priority > 默认策略
```

默认 profile：

| profile         | 特点               |
| --------------- | ---------------- |
| `metric_first`  | 主指标权重最高          |
| `balanced`      | 指标、稳定性、可解释性、成本综合 |
| `interpretable` | 提高线性/可解释模型权重     |
| `efficient`     | 提高训练成本和简洁性权重     |

---

### 14.6 Step 6：约束检查

`constraint_checker.py` 检查：

* 用户硬约束；
* task type；
* artifact 完整性；
* interpretability priority；
* baseline policy；
* 是否允许 baseline 作为 final；
* 是否要求 candidate 必须超过 baseline。

如果所有候选都被约束排除，模块失败。

---

### 14.7 Step 7：候选评分

`candidate_scorer.py` 计算：

* primary_metric_score；
* stability_score；
* baseline_improvement_score；
* interpretability_score；
* cost_score；
* constraint_score；
* selection_score。

---

### 14.8 Step 8：最终排序与选择

`final_ranker.py` 负责：

1. 按 `selection_score` 降序排序；
2. 使用 tie-breaker：

   * primary metric 更优；
   * stability 更好；
   * interpretability 更好；
   * cost 更低；
   * candidate 优先于 baseline；
   * iteration index 更新者优先；
3. 输出：

   * final selected candidate；
   * candidate ranking；
   * rejected candidates。

---

### 14.9 Step 9：解析最终 Artifact

`artifact_resolver.py` 校验：

* model artifact；
* prediction artifact；
* model-ready matrix；
* preprocessor artifact；
* feature matrix；
* metric results artifact；
* workflow trace。

路径必须：

* 存在；
* 位于允许目录；
* 不包含 `..`；
* 文件类型符合预期。

---

### 14.10 Step 10：构建系统选择理由

`selection_reason_builder.py` 生成：

* main reason；
* metric reason；
* stability reason；
* baseline reason；
* interpretability reason；
* cost reason；
* constraint reason；
* artifact reason；
* tradeoff summary。

---

### 14.11 Step 11：LLM 解释最终选择

LLM Selection Explainer 在系统选择完成后运行。

如果 LLM 成功：

* 写入 `llm_selection_explanation`；
* 写入 `candidate_difference_summary`；
* 写入 `human_review_notes`；
* 写入 `risk_notes`。

如果 LLM 失败：

* 不改变 final selected pipeline；
* 使用 system reason fallback；
* 状态可为 `selected_with_warning`；
* 记录 warning。

---

### 14.12 Step 12：构建 Interpretability Analysis Input

`interpretability_input_builder.py` 设置：

```text
ready_for_interpretability_analysis = true
```

条件：

* final model artifact exists；
* model-ready matrix exists；
* feature columns non-empty；
* prediction artifacts exist；
* final trial id exists；
* preprocessor artifact exists。

---

## 15. 数据库设计

### 15.1 新增表：FinalPipelineSelection

表名建议：

```text
final_pipeline_selection
```

字段设计：

| 字段                                     | 类型       | 索引    | 说明                                                  |
| -------------------------------------- | -------- | ----- | --------------------------------------------------- |
| `id`                                   | string   | PK    | `fps_{uuid8}`                                       |
| `task_id`                              | string   | index | 任务 ID                                               |
| `workflow_refinement_id`               | string   | index | 上游 WorkflowRefinement ID                            |
| `metric_evaluation_id`                 | string   | index | 最终候选所属 MetricEvaluation                             |
| `pipeline_execution_id`                | string   | index | 最终候选所属 PipelineExecution                            |
| `pipeline_generation_id`               | string   | index | 最终候选所属 PipelineGeneration                           |
| `status`                               | string   | index | selected / selected_with_warning / failed           |
| `selection_profile`                    | string   | index | metric_first / balanced / interpretable / efficient |
| `final_pipeline_spec_id`               | string   | index | 最终 PipelineSpec                                     |
| `final_model_id`                       | string   | index | 最终模型                                                |
| `final_model_family`                   | string   | index | 最终模型族                                               |
| `final_trial_id`                       | string   | index | 最终 trial                                            |
| `primary_metric`                       | string   | index | 主指标                                                 |
| `primary_metric_value`                 | float    |       | 主指标值                                                |
| `selection_score`                      | float    |       | 综合选择评分                                              |
| `ready_for_interpretability_analysis`  | boolean  | index | 是否可进入解释性分析                                          |
| `llm_used`                             | boolean  |       | 是否调用 LLM                                            |
| `llm_confidence_level`                 | string   |       | LLM 解释置信度                                           |
| `selection_json`                       | JSONB    |       | 完整选择结果                                              |
| `candidate_ranking_json`               | JSONB    |       | 候选排序                                                |
| `system_selection_reason_json`         | JSONB    |       | 系统选择理由                                              |
| `llm_selection_explanation_json`       | JSONB    |       | LLM 选择解释                                            |
| `candidate_difference_summary_json`    | JSONB    |       | 候选差异总结                                              |
| `human_review_notes_json`              | JSONB    |       | 人类审核提示                                              |
| `risk_notes_json`                      | JSONB    |       | 风险提示                                                |
| `interpretability_analysis_input_json` | JSONB    |       | 下游解释性分析输入                                           |
| `artifact_manifest_json`               | JSONB    |       | 最终 artifact manifest                                |
| `llm_request_json`                     | JSONB    |       | LLM 请求                                              |
| `llm_response_json`                    | JSONB    |       | LLM 响应                                              |
| `error_message`                        | string   |       | 错误信息                                                |
| `created_at`                           | datetime | index | 创建时间                                                |
| `updated_at`                           | datetime |       | 更新时间                                                |

---

## 16. 状态设计

### 16.1 FinalPipelineSelectionStatus

| 状态                      | 说明                          |
| ----------------------- | --------------------------- |
| `selecting`             | 正在选择                        |
| `selected`              | 成功完成最终选择，且 LLM 解释正常         |
| `selected_with_warning` | 系统选择成功，但存在非致命警告，例如 LLM 解释失败 |
| `failed`                | 最终选择失败                      |

---

### 16.2 CandidateStatus

| 状态         | 说明                   |
| ---------- | -------------------- |
| `eligible` | 可参与最终选择              |
| `selected` | 最终选中                 |
| `rejected` | 因约束或 artifact 不完整被拒绝 |
| `warning`  | 可选但存在风险              |

---

## 17. Artifact 设计

### 17.1 Artifact 根目录

```text
/app/artifacts/final_selection/{final_pipeline_selection_id}/
```

目录结构：

```text
final_selection/{final_pipeline_selection_id}/
    ├── manifest.json
    ├── final_pipeline_selection_result.json
    ├── candidate_ranking.json
    ├── selection_policy.json
    ├── constraint_check_result.json
    ├── system_selection_reason.json
    ├── llm_selection_explanation.json
    ├── final_artifact_manifest.json
    ├── selection_reason.json
    └── interpretability_analysis_input.json
```

---

## 18. API 设计

### 18.1 创建 Final Pipeline Selection

```text
POST /api/final-pipeline-selections/{task_id}
```

---

### 18.2 获取指定 Final Pipeline Selection

```text
GET /api/final-pipeline-selections/{final_pipeline_selection_id}
```

---

### 18.3 获取任务最新 Final Pipeline Selection

```text
GET /api/tasks/{task_id}/final-pipeline-selection
```

---

### 18.4 重新选择

```text
POST /api/final-pipeline-selections/{task_id}/rerun
```

---

### 18.5 获取候选排名

```text
GET /api/final-pipeline-selections/{final_pipeline_selection_id}/ranking
```

---

### 18.6 获取 LLM 选择解释

```text
GET /api/final-pipeline-selections/{final_pipeline_selection_id}/llm-explanation
```

---

### 18.7 获取 Interpretability Analysis Input

```text
GET /api/final-pipeline-selections/{final_pipeline_selection_id}/interpretability-analysis-input
```

---

### 18.8 获取 Final Artifact Manifest

```text
GET /api/final-pipeline-selections/{final_pipeline_selection_id}/artifact-manifest
```

---

## 19. 前端功能设计

### 19.1 新增前端文件结构

```text
frontend/src/api/finalPipelineSelectionApi.ts

frontend/src/modules/finalPipelineSelection/
    ├── components/
    │   ├── FinalPipelineSelectionPanel.tsx
    │   ├── FinalSelectionSummaryCard.tsx
    │   ├── FinalSelectedPipelineCard.tsx
    │   ├── CandidateRankingTable.tsx
    │   ├── SystemSelectionReasonCard.tsx
    │   ├── LLMSelectionExplanationCard.tsx
    │   ├── CandidateDifferenceSummaryCard.tsx
    │   ├── HumanReviewNotesCard.tsx
    │   ├── RiskNotesCard.tsx
    │   ├── ConstraintCheckCard.tsx
    │   ├── FinalArtifactManifestCard.tsx
    │   ├── InterpretabilityInputCard.tsx
    │   └── FinalPipelineSelectionJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

---

### 19.2 页面集成位置

新增在 Workflow Refinement 后：

```text
LLM-driven Workflow Refinement
Final Pipeline Selection   ← 新增
Interpretability Analysis
Final Output
```

---

### 19.3 主面板功能

`FinalPipelineSelectionPanel` 应提供：

| 功能                          | 说明               |
| --------------------------- | ---------------- |
| Run Final Selection         | 启动最终 Pipeline 选择 |
| Re-run Selection            | 重新选择             |
| Load Latest                 | 加载最新选择结果         |
| View Final Pipeline         | 查看最终模型与 Pipeline |
| View Candidate Ranking      | 查看候选排序           |
| View System Reason          | 查看系统选择理由         |
| View LLM Explanation        | 查看 LLM 自然语言解释    |
| View Candidate Differences  | 查看候选差异总结         |
| View Human Review Notes     | 查看人工审核提示         |
| View Artifacts              | 查看最终 artifact 清单 |
| View Interpretability Input | 查看解释性分析输入        |
| View Full JSON              | 查看完整 JSON        |

---

### 19.4 前端展示顺序

推荐展示顺序：

```text
1. Final Selection Summary
2. Final Selected Pipeline
3. Candidate Ranking
4. System Selection Reason
5. LLM Selection Explanation
6. Candidate Difference Summary
7. Human Review Notes
8. Risk Notes
9. Constraint Check
10. Final Artifact Manifest
11. Interpretability Analysis Input
12. Full JSON
```

---

### 19.5 Final Selection Summary

展示：

* Final Selection ID；
* status；
* selection profile；
* final model；
* final trial；
* primary metric；
* primary metric value；
* selection score；
* LLM explanation status；
* ready for Interpretability Analysis。

---

### 19.6 Final Selected Pipeline Card

展示：

* final pipeline spec id；
* final model id；
* final model family；
* final trial id；
* final hyperparameters；
* metric value；
* source metric evaluation；
* source pipeline execution；
* source pipeline generation。

---

### 19.7 Candidate Ranking Table

表格字段：

| 列                | 说明                             |
| ---------------- | ------------------------------ |
| Rank             | 最终选择排名                         |
| Model            | 模型                             |
| Trial            | trial                          |
| Pipeline Spec    | pipeline spec                  |
| Role             | baseline / candidate / hpo     |
| Primary Metric   | 主指标                            |
| Metric Score     | 指标得分                           |
| Stability        | 稳定性                            |
| Baseline Gain    | baseline 提升                    |
| Interpretability | 可解释性                           |
| Cost             | 成本                             |
| Selection Score  | 综合评分                           |
| Status           | eligible / selected / rejected |

---

### 19.8 System Selection Reason Card

展示：

* main reason；
* metric reason；
* stability reason；
* baseline reason；
* interpretability reason；
* cost reason；
* constraint reason；
* artifact reason；
* tradeoff summary。

---

### 19.9 LLM Selection Explanation Card

展示：

* why selected；
* selection rationale natural language；
* LLM confidence；
* LLM explanation status；
* fallback warning，如有。

---

### 19.10 Candidate Difference Summary Card

展示：

* 每个候选 pipeline 的自然语言总结；
* 候选间的优势差异；
* 复杂度差异；
* 稳定性差异；
* 可解释性差异。

---

### 19.11 Human Review Notes Card

展示：

* 需要人工检查的科学合理性问题；
* 数据集小样本风险；
* baseline improvement 是否足够；
* 解释性结果后续重点；
* 外部测试集缺失风险。

---

### 19.12 Risk Notes Card

展示：

* 选择风险；
* 模型泛化风险；
* 特征表达限制；
* validation-only 选择风险；
* artifact 或复现风险。

---

## 20. 前端状态与交互

### 20.1 按钮启用规则

| 条件                                                      | Run Final Selection     |
| ------------------------------------------------------- | ----------------------- |
| 无 task_id                                               | disabled                |
| 无 WorkflowRefinement                                    | disabled                |
| WorkflowRefinement decision 不是 proceed_next_stage       | disabled                |
| WorkflowRefinement 未 ready_for_final_pipeline_selection | disabled                |
| 正在 selecting                                            | loading                 |
| 已 selected 且 force_rerun=false                          | 显示 Load Latest / Re-run |
| 上游 ready_for_final_pipeline_selection=true              | enabled                 |

---

### 20.2 状态颜色建议

| 状态                                         | 颜色     |
| ------------------------------------------ | ------ |
| `selecting`                                | blue   |
| `selected`                                 | green  |
| `selected_with_warning`                    | orange |
| `failed`                                   | red    |
| `ready_for_interpretability_analysis=true` | green  |
| `candidate rejected`                       | red    |
| `candidate eligible`                       | blue   |
| `candidate selected`                       | green  |
| `llm explanation failed`                   | orange |

---

## 21. 安全设计

### 21.1 绝对禁止

本模块禁止：

1. 训练模型；
2. 调用 `model.fit()`；
3. 调用 `model.predict()`；
4. 重新计算指标；
5. 修改 MetricEvaluation；
6. 修改 PipelineExecution；
7. 修改 PipelineGeneration；
8. 修改 WorkflowRefinement；
9. 动态执行代码；
10. 让 LLM 覆盖系统选择；
11. 让 LLM 修改候选排名；
12. 选择 artifact 缺失的 trial；
13. 写入未授权目录。

---

### 21.2 路径安全

所有 artifact 路径必须：

* 来自上游数据库记录；
* 位于 `/app/artifacts/` 允许目录；
* 不包含 `..`；
* 文件存在；
* 文件类型匹配；
* 不被本模块覆盖。

---

### 21.3 候选安全

候选必须满足：

* trial completed；
* metric evaluated；
* model artifact 存在；
* prediction artifact 存在；
* pipeline spec 存在；
* task_type 兼容；
* 未违反硬约束。

---

### 21.4 LLM 安全

LLM 输出不得影响：

* final selected pipeline；
* final model；
* final trial；
* final hyperparameters；
* candidate ranking；
* selection score；
* metric values；
* artifact manifest；
* interpretability input。

---

## 22. 异常设计

建议新增异常：

| 异常类                                          | error_code                                          | 场景                      |
| -------------------------------------------- | --------------------------------------------------- | ----------------------- |
| `FinalPipelineSelectionNotFoundException`    | `FINAL_PIPELINE_SELECTION_NOT_FOUND`                | 找不到最终选择记录               |
| `WorkflowRefinementRequiredException`        | `WORKFLOW_REFINEMENT_REQUIRED`                      | 缺少上游 WorkflowRefinement |
| `WorkflowRefinementNotReadyException`        | `WORKFLOW_REFINEMENT_NOT_READY_FOR_FINAL_SELECTION` | 上游未 ready               |
| `WorkflowRefinementDecisionInvalidException` | `WORKFLOW_REFINEMENT_DECISION_INVALID`              | 上游 decision 不是 proceed  |
| `FinalSelectionInputInvalidException`        | `FINAL_SELECTION_INPUT_INVALID`                     | 输入合同无效                  |
| `CandidateCollectionException`               | `FINAL_SELECTION_CANDIDATE_COLLECTION_FAILED`       | 候选收集失败                  |
| `CandidateValidationException`               | `FINAL_SELECTION_CANDIDATE_VALIDATION_FAILED`       | 候选校验失败                  |
| `SelectionPolicyException`                   | `FINAL_SELECTION_POLICY_INVALID`                    | 选择策略无效                  |
| `CandidateScoringException`                  | `FINAL_SELECTION_SCORING_FAILED`                    | 候选评分失败                  |
| `FinalRankingException`                      | `FINAL_SELECTION_RANKING_FAILED`                    | 排序失败                    |
| `FinalArtifactResolveException`              | `FINAL_SELECTION_ARTIFACT_RESOLVE_FAILED`           | artifact 解析失败           |
| `LLMSelectionExplanationException`           | `LLM_SELECTION_EXPLANATION_FAILED`                  | LLM 解释失败                |
| `LLMSelectionExplanationValidationException` | `LLM_SELECTION_EXPLANATION_VALIDATION_FAILED`       | LLM 输出校验失败              |
| `InterpretabilityInputBuildException`        | `INTERPRETABILITY_INPUT_BUILD_FAILED`               | 下游输入构建失败                |
| `FinalSelectionArtifactSaveException`        | `FINAL_SELECTION_ARTIFACT_SAVE_FAILED`              | artifact 保存失败           |

---

## 23. MVP 验收标准

### 23.1 后端验收标准

必须满足：

1. 可以通过 API 创建 Final Pipeline Selection；
2. 必须校验 `WorkflowRefinement.ready_for_final_pipeline_selection = true`；
3. 必须校验 `WorkflowRefinement.decision = proceed_next_stage`；
4. 必须消费 `final_pipeline_selection_input_json`；
5. 能收集候选 MetricEvaluation；
6. 能收集候选 PipelineExecution；
7. 能构建 trial-level candidate list；
8. 能校验候选 artifact 完整性；
9. 能根据 selection policy 计算 selection_score；
10. 能生成 candidate_ranking；
11. 能选择 final pipeline / model / trial / params；
12. 能生成 system_selection_reason；
13. MVP 阶段必须调用 LLM Selection Explainer；
14. LLM 必须解释为什么选择该 pipeline；
15. LLM 必须总结候选 pipeline 差异；
16. LLM 必须生成自然语言选择理由；
17. LLM 必须提醒人类关注潜在风险；
18. LLM 不得修改 final selected pipeline、candidate ranking、selection score 或 metric values；
19. LLM 输出必须经过 parser、validator、normalizer；
20. LLM 失败时系统选择仍然有效，状态可为 `selected_with_warning`；
21. 能生成 final_artifact_manifest；
22. 能生成 `interpretability_analysis_input_json`；
23. 能持久化完整选择结果；
24. 不重新训练模型；
25. 不重新计算指标；
26. 不执行任意代码。

---

### 23.2 前端验收标准

必须满足：

1. 新增 Final Pipeline Selection 面板；
2. 可以点击 Run Final Selection；
3. 可以点击 Re-run Selection；
4. 可以展示 final selected pipeline；
5. 可以展示 final model；
6. 可以展示 final trial；
7. 可以展示 final hyperparameters；
8. 可以展示 primary metric 和 selection score；
9. 可以展示 candidate ranking；
10. 可以展示 system selection reason；
11. 可以展示 LLM selection explanation；
12. 可以展示 candidate difference summary；
13. 可以展示 human review notes；
14. 可以展示 risk notes；
15. 可以展示 constraint check；
16. 可以展示 final artifact manifest；
17. 可以展示 interpretability analysis input；
18. 可以查看完整 JSON。

---

### 23.3 安全验收标准

必须满足：

1. 不允许执行训练；
2. 不允许执行预测；
3. 不允许执行任意代码；
4. 不允许覆盖上游记录；
5. 不允许选择 artifact 缺失的候选；
6. 不允许未完成 trial 进入最终选择；
7. 不允许 LLM 覆盖系统排名；
8. 不允许 LLM 修改指标；
9. 不允许 LLM 修改 artifact；
10. 所有路径必须经过安全校验。

---

## 24. 推荐实现优先级

### P0：必须完成

1. 后端 `final_pipeline_selection` 模块；
2. `FinalPipelineSelection` 数据表；
3. `context_builder`；
4. `selection_input_loader`；
5. `candidate_collector`；
6. `candidate_validator`；
7. `selection_policy_builder`；
8. `candidate_scorer`；
9. `final_ranker`；
10. `artifact_resolver`；
11. `selection_reason_builder`；
12. `llm_selection_prompt_builder`；
13. `llm_selection_explainer`；
14. `llm_selection_explanation_parser`；
15. `llm_selection_explanation_validator`；
16. `llm_selection_explanation_normalizer`；
17. `interpretability_input_builder`；
18. 核心 API；
19. 前端主面板；
20. Final Selected Pipeline 展示；
21. Candidate Ranking 表；
22. LLM Selection Explanation 展示；
23. Interpretability Input 展示。

---

### P1：建议完成

1. 更细粒度 selection score 解释；
2. selection profile 配置；
3. constraint check 可视化；
4. artifact manifest 完整性检查；
5. 历史候选跨轮次对比；
6. LLM 解释 fallback 展示。

---

### P2：后续迭代

1. 多目标 Pareto selection；
2. 不确定性加权选择；
3. 统计显著性检验；
4. 人工确认最终选择；
5. 模型压缩或部署候选选择；
6. 与 Final Output 深度联动。

---

## 25. 给 AI Coding 工具的实现提示词

```text
请基于当前 MLAgent 项目实现模块十四 Final Pipeline Selection。开发前先阅读 PROJECT_IMPLEMENTATION_OVERVIEW.md，重点理解模块十三 Workflow Refinement 的 final_pipeline_selection_input_json 输出合同，以及模块十一 Metric Evaluation、模块十 Pipeline Execution 的数据结构。

实现要求：
1. 新增 backend/app/modules/final_pipeline_selection 模块，结构遵循现有模块模式：api.py、service.py、model.py、repository.py、schemas.py、enums.py、exceptions.py、context_builder.py、builder.py 等；
2. 本模块消费 WorkflowRefinement.final_pipeline_selection_input_json，必须校验 WorkflowRefinement.decision=proceed_next_stage 且 ready_for_final_pipeline_selection=true；
3. 收集 candidate_metric_evaluation_ids 和 candidate_pipeline_execution_ids 对应的完整评估结果和训练结果；
4. 以 trial-level candidate 为选择粒度，构建 CandidateSelectionItem 列表；
5. 校验每个候选的 metric、trial、pipeline_spec、model_artifact、prediction_artifact 是否完整；
6. 实现 selection_policy_builder，支持 metric_first、balanced、interpretable、efficient 四种 profile；
7. 实现 candidate_scorer，综合 primary_metric_score、stability_score、baseline_improvement_score、interpretability_score、cost_score、constraint_score 计算 selection_score；
8. 实现 final_ranker，输出 candidate_ranking 并选择 final_pipeline_spec_id、final_model_id、final_trial_id、final_hyperparameters；
9. 构建 system_selection_reason，解释系统选择该 candidate 的结构化理由；
10. MVP 阶段必须实现 LLM Selection Explainer，LLM 只负责解释系统选择，不得修改最终选择、候选排名、selection_score、metric values 或 artifact paths；
11. LLM 必须输出 why_selected、candidate_difference_summary、selection_rationale_natural_language、human_review_notes、risk_notes、confidence_level；
12. LLM 输出必须经过 parser、validator、normalizer，并扫描 import/def/class/eval/exec/subprocess/model.fit/Pipeline 等危险模式；
13. 构建 final_artifact_manifest，包含 model artifact、prediction artifact、preprocessor artifact、model-ready matrix、feature matrix、metric results；
14. 构建 interpretability_analysis_input_json，供模块十五 Interpretability Analysis 使用；
15. 前端新增 FinalPipelineSelectionPanel，展示 final selected pipeline、candidate ranking、system selection reason、LLM selection explanation、candidate difference summary、human review notes、risk notes、constraint check、artifact manifest、interpretability input 和完整 JSON；
16. 严禁重新训练模型、重新计算指标、执行任意代码、修改上游记录或让 LLM 覆盖系统最终选择。
```

---

## 26. 总结

**Final Pipeline Selection** 是 MLAgent 从“多轮实验与闭环优化”进入“最终模型交付”的关键模块。

它的核心价值是：

```text
把多轮实验、多组候选模型、多次指标评估结果，收敛为一个唯一、稳定、可解释、可复现的最终 Pipeline。
```

本模块的最终形态是：

```text
系统完成最终选择；
LLM 完成选择解释。
```

也就是：

```text
System Selector:
    决定 final pipeline / model / trial / params

LLM Selection Explainer:
    解释为什么选择它
    总结候选差异
    生成自然语言理由
    提醒人类关注风险
```

本模块必须坚持：

```text
只选择，不训练；
只解释，不篡改；
系统选择是权威；
LLM 解释是辅助；
所有 artifact 和候选必须可追溯；
下游输出必须服务于 Interpretability Analysis。
```

完成该模块后，MLAgent 将具备从自动化实验结果中稳定选出最终模型的能力，并为下一步 **Interpretability Analysis** 提供唯一、明确、可复现的最终输入。
