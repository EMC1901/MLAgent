# PRD：Interpretability Analysis 模块

> 项目名称：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：15
> 模块名称：Interpretability Analysis
> 中文名称：模型解释性分析 / 材料规律解释
> 上游模块：Final Pipeline Selection
> 下游模块：Final Output
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0
> 输出格式：Markdown

---

## 1. 背景与上下文

当前 MLAgent 已完成从任务定义到最终 Pipeline 选择的核心自动化链路：

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
14. Final Pipeline Selection
```

模块 14 **Final Pipeline Selection** 已经完成最终模型选择，并输出：

```text
interpretability_analysis_input_json
```

该输入明确了：

* 最终模型；
* 最终 trial；
* 最终 pipeline spec；
* 模型 artifact；
* 预处理 artifact；
* 模型就绪特征矩阵；
* 特征列；
* 预测结果；
* 主指标和最终性能；
* 推荐解释方法；
* 是否可以进入解释性分析。

因此，本模块 **Interpretability Analysis** 的核心任务是：

> 基于最终选中的模型、特征矩阵、预测结果和 pipeline 记录，生成结构化模型解释结果，包括全局特征重要性、局部样本解释、SHAP 分析、材料特征规律解释和下游 Final Output 所需的解释性产物。

---

## 2. 模块定位

### 2.1 一句话定义

**Interpretability Analysis 是 MLAgent 中负责对最终选中模型进行可解释性分析的模块。它通过系统内置解释器计算 feature importance、SHAP value、局部解释和材料规律摘要，并由 LLM 对解释结果进行自然语言归纳，但不重新训练模型、不修改模型、不改变最终选择结果。**

---

## 3. 在整体链路中的位置

```text
Metric Evaluation
  ↓
LLM-based Result Diagnosis
  ↓
LLM-driven Workflow Refinement
  ↓
Final Pipeline Selection
  ↓
Interpretability Analysis   ← 当前模块
  ↓
Final Output
```

---

## 4. 模块核心职责

Interpretability Analysis 需要完成以下工作：

1. 消费 Final Pipeline Selection 输出的 `interpretability_analysis_input_json`；
2. 校验 `ready_for_interpretability_analysis = true`；
3. 加载最终模型 artifact；
4. 加载 model-ready feature matrix；
5. 加载 feature columns；
6. 加载 prediction artifacts；
7. 根据模型类型选择解释方法；
8. 计算全局 feature importance；
9. 计算 SHAP values；
10. 生成样本级 local explanation；
11. 汇总 top important features；
12. 分析预测误差较大的样本；
13. 生成材料领域解释摘要；
14. 调用 LLM 解释性总结器，将数值解释结果转化为可读的材料规律描述；
15. 生成 `final_output_input_json`；
16. 持久化解释性分析结果；
17. 前端展示特征重要性、SHAP 排名、局部解释、材料规律总结、风险提示和完整 JSON。

---

## 5. 与上下游模块的边界

### 5.1 与 Final Pipeline Selection 的边界

Final Pipeline Selection 负责：

* 选择最终模型；
* 选择最终 trial；
* 选择最终 pipeline；
* 确认最终 artifact；
* 输出 `interpretability_analysis_input_json`。

Interpretability Analysis 负责：

* 解释最终模型；
* 分析特征贡献；
* 生成 SHAP / feature importance 结果；
* 生成材料规律解释；
* 输出 Final Output 输入。

Interpretability Analysis 不负责：

* 重新选择模型；
* 修改 final selected pipeline；
* 修改 selection score；
* 修改 metric result；
* 重新训练模型。

---

### 5.2 与 Pipeline Execution 的边界

Pipeline Execution 负责训练和保存模型。

Interpretability Analysis 只加载已保存模型进行解释，不重新训练，不重新预测。

---

### 5.3 与 Metric Evaluation 的边界

Metric Evaluation 负责模型性能指标计算。

Interpretability Analysis 可以读取预测结果和误差，但不重新计算主指标，不重新排序模型。

---

### 5.4 与 Final Output 的边界

Interpretability Analysis 输出：

```text
final_output_input_json
```

Final Output 负责：

* 汇总最终模型；
* 汇总实验记录；
* 汇总指标结果；
* 汇总解释性结果；
* 生成最终模型文件、预测结果、workflow trace 和可复现实验报告。

Interpretability Analysis 不生成最终报告。

---

## 6. 核心设计原则

### 6.1 系统解释器负责数值解释，LLM 负责自然语言总结

本模块采用：

```text
System Interpretability Engine + LLM Explanation Summarizer
```

其中：

```text
System Interpretability Engine
```

负责：

* 加载模型；
* 加载特征矩阵；
* 计算 feature importance；
* 计算 SHAP values；
* 生成 local explanations；
* 生成误差样本分析；
* 保存解释性 artifact。

```text
LLM Explanation Summarizer
```

负责：

* 总结重要特征；
* 解释特征与目标性质之间的可能关系；
* 生成材料规律假设；
* 提醒解释风险；
* 生成面向报告的自然语言解释。

LLM 不允许：

* 修改 SHAP values；
* 修改 feature importance 数值；
* 修改最终模型；
* 修改预测结果；
* 输出可执行代码；
* 重新训练或重新预测；
* 直接决定科学结论为真。

---

### 6.2 解释性分析只针对最终选中模型

本模块 MVP 只解释 Final Pipeline Selection 选出的唯一最终模型。

不解释所有候选模型。

---

### 6.3 解释结果必须区分“计算事实”和“LLM 推断”

解释结果需要明确区分：

```text
computed_interpretability_results
```

和：

```text
llm_material_insights
```

其中：

* computed results 是系统计算得出的数值结果；
* LLM insights 是基于这些结果生成的解释性归纳和假设；
* LLM 生成的材料规律必须标注为 hypothesis / interpretation，而不是确定性结论。

---

### 6.4 解释方法必须与模型类型兼容

不同模型类型使用不同解释方法：

| 模型类型                                 | 推荐解释方法                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------ |
| linear / ridge / lasso / elastic_net | coefficient importance + permutation importance + SHAP linear explainer  |
| random_forest                        | native feature importance + permutation importance + SHAP tree explainer |
| gradient_boosting / xgboost          | native importance + SHAP tree explainer                                  |
| svr / knn                            | permutation importance + kernel SHAP / sampling SHAP                     |
| dummy_mean                           | 不做正式解释，只标记为 baseline-only                                                |

MVP 中，如果 SHAP 对某些模型成本过高，可使用 fallback：

```text
permutation_importance
```

---

## 7. 产品目标

### 7.1 MVP 目标

MVP 阶段需要实现：

1. 读取 FinalPipelineSelection；
2. 校验 `ready_for_interpretability_analysis = true`；
3. 加载 `interpretability_analysis_input_json`；
4. 加载最终模型 artifact；
5. 加载 model-ready matrix；
6. 获取 feature columns；
7. 加载 prediction artifact；
8. 根据模型类型选择解释方法；
9. 计算 global feature importance；
10. 计算 permutation importance；
11. 对支持的模型计算 SHAP values；
12. 生成 top features summary；
13. 生成 local sample explanations；
14. 生成 high-error sample explanations；
15. 调用 LLM 生成自然语言材料规律解释；
16. 输出解释风险提示；
17. 构建 `final_output_input_json`；
18. 持久化解释性结果；
19. 前端展示解释结果、图表数据、LLM 总结和 artifact。

---

### 7.2 非目标

MVP 阶段不做：

1. 不重新训练模型；
2. 不重新选择模型；
3. 不重新计算最终 ranking；
4. 不执行新的 HPO；
5. 不修改 feature matrix；
6. 不修改模型 artifact；
7. 不部署模型；
8. 不生成最终报告；
9. 不对所有候选 pipeline 做解释；
10. 不做因果推断；
11. 不声称发现确定性材料机理；
12. 不允许 LLM 输出或执行代码。

---

## 8. 输入设计

### 8.1 API 请求输入

接口：

```text
POST /api/interpretability-analyses/{task_id}
```

请求字段：

| 字段                               | 类型      | 必填 | 说明                                          |
| -------------------------------- | ------- | -: | ------------------------------------------- |
| `final_pipeline_selection_id`    | string  |  否 | 指定 FinalPipelineSelection；为空则使用最新 ready 记录  |
| `force_rerun`                    | boolean |  否 | 是否强制重新解释，默认 false                           |
| `use_llm_summarizer`             | boolean |  否 | 是否调用 LLM 总结器，MVP 默认 true                    |
| `interpretability_profile`       | string  |  否 | `compact` / `standard` / `full`，默认 standard |
| `max_shap_samples`               | integer |  否 | SHAP 最大采样样本数，默认 200                         |
| `max_local_explanations`         | integer |  否 | local explanation 样本数量，默认 10                |
| `include_high_error_samples`     | boolean |  否 | 是否解释高误差样本，默认 true                           |
| `include_permutation_importance` | boolean |  否 | 是否计算 permutation importance，默认 true         |
| `include_shap`                   | boolean |  否 | 是否计算 SHAP，默认 true                           |
| `notes`                          | string  |  否 | 用户备注                                        |

---

### 8.2 必需上游输入

| 来源                                        | 必需字段                                                                                                                                                                                                                                                         |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `FinalPipelineSelection`                  | `id`, `task_id`, `status`, `ready_for_interpretability_analysis`, `interpretability_analysis_input_json`                                                                                                                                                     |
| `interpretability_analysis_input_json`    | `final_model_id`, `final_model_family`, `final_trial_id`, `final_pipeline_spec_id`, `model_artifact_path`, `model_ready_matrix_path`, `feature_columns`, `prediction_artifact_paths`, `preprocessor_artifact_path`, `primary_metric`, `primary_metric_value` |
| `FinalPipelineSelection.selection_json`   | final selected pipeline、selection reason、candidate ranking                                                                                                                                                                                                   |
| `MetricEvaluation.evaluation_json`        | fold/trial metric results，可用于误差解释                                                                                                                                                                                                                            |
| `PipelineExecution.execution_json`        | trial result、prediction artifact、runtime                                                                                                                                                                                                                     |
| `FeatureEngineering.feature_json`         | feature generation metadata                                                                                                                                                                                                                                  |
| `FeaturePreprocessing.preprocessing_json` | scaling、imputation、feature selection metadata                                                                                                                                                                                                                |
| `DatasetProfile.profile_json`             | dataset size、target distribution、missing/outlier summary                                                                                                                                                                                                     |
| `TaskSpecification.task_spec_json`        | task goal、target、domain context                                                                                                                                                                                                                              |

---

## 9. 输出设计

### 9.1 核心输出：InterpretabilityAnalysisResponse

| 字段                              | 类型          | 说明                                              |
| ------------------------------- | ----------- | ----------------------------------------------- |
| `interpretability_analysis_id`  | string      | 解释性分析 ID，例如 `ia_xxxxxxxx`                       |
| `task_id`                       | string      | 任务 ID                                           |
| `final_pipeline_selection_id`   | string      | 上游最终选择 ID                                       |
| `metric_evaluation_id`          | string      | 关联评估 ID                                         |
| `pipeline_execution_id`         | string      | 关联执行 ID                                         |
| `status`                        | string      | `analyzed` / `analyzed_with_warning` / `failed` |
| `analysis_profile`              | string      | compact / standard / full                       |
| `final_model_id`                | string      | 最终模型                                            |
| `final_model_family`            | string      | 最终模型族                                           |
| `final_trial_id`                | string      | 最终 trial                                        |
| `interpretability_methods_used` | array       | 实际使用的方法                                         |
| `global_feature_importance`     | array       | 全局特征重要性                                         |
| `permutation_importance`        | array       | permutation importance 结果                       |
| `shap_summary`                  | object      | SHAP 汇总                                         |
| `local_explanations`            | array       | 样本级解释                                           |
| `high_error_sample_analysis`    | array       | 高误差样本解释                                         |
| `feature_group_summary`         | object      | 特征组解释，可选                                        |
| `material_insight_summary`      | object      | LLM 材料规律解释                                      |
| `llm_interpretability_summary`  | object      | LLM 自然语言总结                                      |
| `interpretability_risk_notes`   | array       | 解释风险提示                                          |
| `analysis_artifact_manifest`    | object      | 解释性分析 artifact 清单                               |
| `final_output_input`            | object      | 下游 Final Output 输入                              |
| `ready_for_final_output`        | boolean     | 是否可进入最终输出                                       |
| `warnings`                      | array       | 警告                                              |
| `error_message`                 | string/null | 错误信息                                            |
| `created_at`                    | datetime    | 创建时间                                            |
| `updated_at`                    | datetime    | 更新时间                                            |

---

## 10. 核心数据结构设计

### 10.1 GlobalFeatureImportanceItem

```json
{
  "feature_name": "MagpieData mean Electronegativity",
  "importance_value": 0.183,
  "importance_rank": 1,
  "importance_method": "permutation_importance",
  "direction": "positive_or_unknown",
  "feature_group": "composition_descriptor",
  "interpretation_hint": "This descriptor may reflect bonding tendency or chemical composition effects."
}
```

字段说明：

| 字段                    | 类型      | 说明                                                                       |
| --------------------- | ------- | ------------------------------------------------------------------------ |
| `feature_name`        | string  | 特征名称                                                                     |
| `importance_value`    | float   | 重要性值                                                                     |
| `importance_rank`     | integer | 排名                                                                       |
| `importance_method`   | string  | coefficient / native / permutation / shap                                |
| `direction`           | string  | positive / negative / non_monotonic / unknown                            |
| `feature_group`       | string  | composition_descriptor / structure_descriptor / statistical_descriptor 等 |
| `interpretation_hint` | string  | 解释提示                                                                     |

---

### 10.2 ShapSummary

```json
{
  "shap_available": true,
  "explainer_type": "tree_explainer",
  "n_samples_explained": 200,
  "top_shap_features": [
    {
      "feature_name": "mean Electronegativity",
      "mean_abs_shap": 0.124,
      "rank": 1,
      "direction_summary": "higher values tend to increase prediction"
    }
  ],
  "shap_artifact_paths": {
    "shap_values": "/app/artifacts/interpretability/ia_xxx/shap/shap_values.parquet",
    "summary_data": "/app/artifacts/interpretability/ia_xxx/shap/shap_summary.json"
  },
  "warnings": []
}
```

---

### 10.3 LocalExplanationItem

| 字段                          | 类型           | 说明          |
| --------------------------- | ------------ | ----------- |
| `sample_id`                 | string       | 样本 ID       |
| `y_true`                    | float/string | 真实值         |
| `y_pred`                    | float/string | 预测值         |
| `prediction_error`          | float/null   | 预测误差        |
| `top_positive_features`     | array        | 推高预测的特征     |
| `top_negative_features`     | array        | 拉低预测的特征     |
| `local_shap_values`         | object       | 局部 SHAP 值摘要 |
| `local_explanation_summary` | string       | 局部解释文本      |

---

### 10.4 HighErrorSampleAnalysis

| 字段                        | 类型         | 说明     |
| ------------------------- | ---------- | ------ |
| `sample_id`               | string     | 样本 ID  |
| `absolute_error`          | float      | 绝对误差   |
| `relative_error`          | float/null | 相对误差   |
| `error_rank`              | integer    | 误差排名   |
| `possible_error_factors`  | array      | 可能误差因素 |
| `feature_pattern_summary` | string     | 特征模式说明 |
| `review_suggestion`       | string     | 人工复查建议 |

---

### 10.5 MaterialInsightSummary

由 LLM 生成，但必须基于系统计算结果。

```json
{
  "top_material_patterns": [
    {
      "pattern": "Electronegativity-related descriptors are highly influential.",
      "supporting_features": [
        "mean Electronegativity",
        "range Electronegativity"
      ],
      "possible_material_meaning": "These features may reflect bonding character or compositional chemistry effects.",
      "evidence_strength": "moderate",
      "caution": "This is a model-based association, not a causal mechanism."
    }
  ],
  "feature_groups_interpretation": [
    {
      "feature_group": "composition_descriptor",
      "summary": "Composition-level descriptors dominate the selected model's predictions."
    }
  ],
  "domain_hypotheses": [
    "Elements with stronger electronegativity contrast may correlate with changes in the target property."
  ],
  "limitations": [
    "Interpretation is limited by the available descriptors and dataset size.",
    "SHAP values describe model behavior, not necessarily physical causality."
  ],
  "confidence_level": "medium"
}
```

---

### 10.6 FinalOutputInput

下游 Final Output 的正式输入。

| 字段                             | 类型      | 说明            |
| ------------------------------ | ------- | ------------- |
| `interpretability_analysis_id` | string  | 当前解释分析 ID     |
| `final_pipeline_selection_id`  | string  | 最终选择 ID       |
| `task_id`                      | string  | 任务 ID         |
| `final_model_id`               | string  | 最终模型 ID       |
| `final_trial_id`               | string  | 最终 trial ID   |
| `model_artifact_path`          | string  | 最终模型 artifact |
| `prediction_artifact_paths`    | array   | 预测结果          |
| `metric_summary`               | object  | 最终指标摘要        |
| `selection_summary`            | object  | 最终选择摘要        |
| `global_feature_importance`    | array   | 全局特征重要性       |
| `shap_summary`                 | object  | SHAP 摘要       |
| `material_insight_summary`     | object  | 材料规律解释        |
| `interpretability_artifacts`   | object  | 解释性 artifact  |
| `workflow_trace_refs`          | object  | 全流程 trace 引用  |
| `ready_for_final_output`       | boolean | 是否可进入最终输出     |

---

## 11. 解释方法设计

### 11.1 方法选择策略

`interpretability_method_selector.py` 根据 `final_model_family` 决定解释方法。

| model_family      | coefficient | native importance | permutation |                          SHAP |
| ----------------- | ----------: | ----------------: | ----------: | ----------------------------: |
| linear_regression |         Yes |                No |         Yes |                   Linear SHAP |
| ridge             |         Yes |                No |         Yes |                   Linear SHAP |
| lasso             |         Yes |                No |         Yes |                   Linear SHAP |
| elastic_net       |         Yes |                No |         Yes |                   Linear SHAP |
| random_forest     |          No |               Yes |         Yes |                     Tree SHAP |
| gradient_boosting |          No |               Yes |         Yes |                     Tree SHAP |
| xgboost           |          No |               Yes |         Yes |                     Tree SHAP |
| svr               |          No |                No |         Yes | Kernel/Sampling SHAP optional |
| knn               |          No |                No |         Yes | Kernel/Sampling SHAP optional |
| dummy_mean        |          No |                No |          No |                            No |

---

### 11.2 MVP 推荐解释方法

MVP 必须支持：

1. coefficient importance；
2. native feature importance；
3. permutation importance；
4. SHAP for linear/tree models；
5. top feature summary；
6. local explanation for selected samples；
7. high-error sample explanation。

对于无法支持 SHAP 的模型，应 fallback 到：

```text
permutation_importance + warning
```

---

### 11.3 SHAP 计算策略

为控制成本，SHAP 应支持采样：

| 参数                       | 默认值 |
| ------------------------ | --: |
| `max_shap_samples`       | 200 |
| `background_sample_size` | 100 |
| `max_features_to_report` |  30 |
| `max_local_explanations` |  10 |

如数据集较小，可以使用全量样本。

如数据集较大，应采样，并记录 sampling metadata。

---

## 12. LLM Interpretability Summarizer 设计

### 12.1 LLM 运行时机

LLM 必须在系统解释计算完成后运行：

```text
feature importance calculated
SHAP summary calculated
local explanations generated
high-error samples analyzed
```

也就是：

```text
系统先计算，LLM 后总结
```

---

### 12.2 LLM 输入上下文

LLM 输入应包含摘要，不传完整大矩阵。

建议包含：

1. task summary；
2. target property；
3. final model summary；
4. final metric summary；
5. top global feature importance；
6. top SHAP features；
7. feature group summary；
8. high-error sample summary；
9. feature engineering metadata；
10. preprocessing metadata；
11. dataset profile summary；
12. known limitations；
13. instructions to avoid causal overclaiming。

---

### 12.3 LLM 输出内容

LLM 必须输出：

1. top material patterns；
2. feature groups interpretation；
3. domain hypotheses；
4. limitations；
5. human review notes；
6. confidence level。

---

### 12.4 LLM Prompt 核心规则

Prompt 必须明确：

```text
You are an interpretability summarizer for a materials science AutoML system.

The numerical interpretability results have already been computed by the system.

You must not modify feature importance values.
You must not modify SHAP values.
You must not modify model predictions.
You must not claim causal mechanisms unless supported by evidence.
You must describe model-based associations and hypotheses.
You must not output executable code.
```

---

### 12.5 LLM 安全校验

禁止字段：

```text
python_code
script
shell_command
sql
modified_importance
modified_shap_values
causal_claim
model_update
feature_update
```

危险内容扫描：

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
```

如果 LLM 输出不安全：

* 不采纳 LLM 解释；
* 保留系统解释结果；
* 状态设为 `analyzed_with_warning`；
* `ready_for_final_output` 不受影响；
* 记录 warning。

---

## 13. 后端功能设计

### 13.1 推荐目录结构

```text
backend/app/modules/interpretability_analysis/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── interpretability_input_loader.py
    ├── model_artifact_loader.py
    ├── feature_matrix_loader.py
    ├── prediction_artifact_loader.py
    ├── interpretability_method_selector.py
    ├── coefficient_importance_analyzer.py
    ├── native_importance_analyzer.py
    ├── permutation_importance_analyzer.py
    ├── shap_analyzer.py
    ├── local_explanation_builder.py
    ├── high_error_sample_analyzer.py
    ├── feature_group_analyzer.py
    ├── llm_interpretability_prompt_builder.py
    ├── llm_interpretability_summarizer.py
    ├── llm_interpretability_parser.py
    ├── llm_interpretability_validator.py
    ├── llm_interpretability_normalizer.py
    ├── final_output_input_builder.py
    ├── interpretability_artifact_manager.py
    └── builder.py
```

---

### 13.2 文件职责说明

| 文件                                       | 职责                                  |
| ---------------------------------------- | ----------------------------------- |
| `api.py`                                 | Interpretability Analysis REST API  |
| `service.py`                             | 主流程编排                               |
| `model.py`                               | SQLModel 数据表                        |
| `repository.py`                          | CRUD 与 latest 查询                    |
| `schemas.py`                             | 请求、响应、内部 DTO                        |
| `enums.py`                               | 状态、解释方法、模型族等枚举                      |
| `exceptions.py`                          | 专用异常                                |
| `context_builder.py`                     | 读取 FinalPipelineSelection 并校验 ready |
| `interpretability_input_loader.py`       | 加载解释性输入合同                           |
| `model_artifact_loader.py`               | 安全加载最终模型                            |
| `feature_matrix_loader.py`               | 加载模型就绪特征矩阵                          |
| `prediction_artifact_loader.py`          | 加载预测结果                              |
| `interpretability_method_selector.py`    | 根据模型类型选择解释方法                        |
| `coefficient_importance_analyzer.py`     | 分析线性模型系数                            |
| `native_importance_analyzer.py`          | 分析树模型原生 feature importance          |
| `permutation_importance_analyzer.py`     | 计算 permutation importance           |
| `shap_analyzer.py`                       | 计算 SHAP values                      |
| `local_explanation_builder.py`           | 构建局部样本解释                            |
| `high_error_sample_analyzer.py`          | 分析高误差样本                             |
| `feature_group_analyzer.py`              | 按特征组聚合解释结果                          |
| `llm_interpretability_prompt_builder.py` | 构建 LLM 总结 prompt                    |
| `llm_interpretability_summarizer.py`     | 调用 LLM                              |
| `llm_interpretability_parser.py`         | 解析 LLM 输出                           |
| `llm_interpretability_validator.py`      | 校验 LLM 输出                           |
| `llm_interpretability_normalizer.py`     | 标准化 LLM 输出                          |
| `final_output_input_builder.py`          | 构建 Final Output 输入                  |
| `interpretability_artifact_manager.py`   | 保存 artifact                         |
| `builder.py`                             | 构建最终响应                              |

---

## 14. 后端主流程

```text
InterpretabilityAnalysisService.create_interpretability_analysis(task_id, request)
    ↓
1. build_interpretability_context()
    ↓
2. load_interpretability_analysis_input()
    ↓
3. validate_artifacts_and_paths()
    ↓
4. load_final_model_artifact()
    ↓
5. load_model_ready_feature_matrix()
    ↓
6. load_prediction_artifacts()
    ↓
7. select_interpretability_methods()
    ↓
8. compute_coefficient_or_native_importance()
    ↓
9. compute_permutation_importance()
    ↓
10. compute_shap_values_if_supported()
    ↓
11. build_global_feature_importance()
    ↓
12. build_local_explanations()
    ↓
13. analyze_high_error_samples()
    ↓
14. build_feature_group_summary()
    ↓
15. build_llm_interpretability_context()
    ↓
16. call_llm_interpretability_summarizer()
    ↓
17. parse_validate_normalize_llm_summary()
    ↓
18. build_final_output_input()
    ↓
19. save_interpretability_artifacts()
    ↓
20. build_response()
    ↓
21. persist()
```

---

### 14.1 Step 1：构建上下文

`context_builder.py` 负责：

* 根据 `task_id` 获取最新 FinalPipelineSelection；
* 或根据 `final_pipeline_selection_id` 获取指定记录；
* 校验：

  * `status in selected / selected_with_warning`；
  * `ready_for_interpretability_analysis = true`；
  * `interpretability_analysis_input_json` 存在；
* 关联读取：

  * MetricEvaluation；
  * PipelineExecution；
  * PipelineGeneration；
  * FeatureEngineering；
  * FeaturePreprocessing；
  * DatasetProfile；
  * TaskSpecification。

---

### 14.2 Step 2：加载解释性输入

`interpretability_input_loader.py` 校验：

* `final_model_id`；
* `final_model_family`；
* `final_trial_id`；
* `final_pipeline_spec_id`；
* `model_artifact_path`；
* `model_ready_matrix_path`；
* `feature_columns`；
* `prediction_artifact_paths`；
* `preprocessor_artifact_path`；
* `primary_metric`；
* `primary_metric_value`。

---

### 14.3 Step 3：路径和 artifact 安全校验

必须校验：

* 路径存在；
* 路径位于允许 artifact 目录；
* 不包含 `..`；
* 文件类型符合预期；
* 不覆盖任何上游 artifact；
* 模型 artifact 可读取；
* feature matrix 与 feature columns 一致。

---

### 14.4 Step 4：加载最终模型

`model_artifact_loader.py` 负责加载模型 artifact。

注意：

* 只允许从 FinalPipelineSelection 指定路径加载；
* 不允许加载用户任意路径；
* 不允许动态 import；
* 如果模型依赖缺失，应返回明确错误；
* 不允许重新 fit。

---

### 14.5 Step 5：加载特征矩阵

`feature_matrix_loader.py` 负责：

* 加载 model-ready matrix；
* 校验 feature columns；
* 校验 target column；
* 分离 X / y；
* 校验样本数；
* 校验数值类型；
* 按 SHAP / permutation 需要进行采样。

---

### 14.6 Step 6：选择解释方法

`interpretability_method_selector.py` 根据：

* model family；
* task type；
* 数据规模；
* request profile；
* 是否安装 SHAP；
* runtime budget；

生成：

```text
interpretability_method_plan
```

---

### 14.7 Step 7：计算全局重要性

根据模型类型计算：

* coefficient importance；
* native importance；
* permutation importance；
* SHAP mean absolute importance。

最终统一归一化为：

```text
global_feature_importance
```

---

### 14.8 Step 8：计算 SHAP

`shap_analyzer.py` 负责：

* 选择 explainer；
* 抽样；
* 计算 shap values；
* 聚合 mean absolute SHAP；
* 生成 top SHAP features；
* 保存 SHAP artifact；
* 返回 warnings。

如果 SHAP 失败：

* 不应导致整个模块失败；
* fallback 到 permutation importance；
* 状态可为 `analyzed_with_warning`。

---

### 14.9 Step 9：局部解释

`local_explanation_builder.py` 负责：

* 选择代表性样本；
* 选择高误差样本；
* 提取 top positive / negative feature contribution；
* 生成 local explanation summary。

---

### 14.10 Step 10：高误差样本分析

`high_error_sample_analyzer.py` 负责：

* 根据 prediction artifact 找出高误差样本；
* 提取其特征模式；
* 关联局部 SHAP；
* 生成 review suggestion。

---

### 14.11 Step 11：LLM 材料规律总结

LLM 总结必须基于系统计算结果。

输出：

* top material patterns；
* feature group interpretation；
* domain hypotheses；
* limitations；
* human review notes；
* confidence level。

LLM 输出必须经过 parser / validator / normalizer。

---

### 14.12 Step 12：构建 Final Output Input

`final_output_input_builder.py` 负责生成：

```text
final_output_input_json
```

只有满足：

* 至少有 global feature importance；
* final model artifact 存在；
* metric summary 存在；
* selection summary 存在；
* interpretability artifacts 已保存；

才设置：

```text
ready_for_final_output = true
```

---

## 15. 数据库设计

### 15.1 新增表：InterpretabilityAnalysis

表名建议：

```text
interpretability_analysis
```

字段设计：

| 字段                                | 类型       | 索引    | 说明                                                    |
| --------------------------------- | -------- | ----- | ----------------------------------------------------- |
| `id`                              | string   | PK    | `ia_{uuid8}`                                          |
| `task_id`                         | string   | index | 任务 ID                                                 |
| `final_pipeline_selection_id`     | string   | index | 上游 FinalPipelineSelection ID                          |
| `metric_evaluation_id`            | string   | index | 关联 MetricEvaluation ID                                |
| `pipeline_execution_id`           | string   | index | 关联 PipelineExecution ID                               |
| `status`                          | string   | index | analyzing / analyzed / analyzed_with_warning / failed |
| `analysis_profile`                | string   | index | compact / standard / full                             |
| `final_model_id`                  | string   | index | 最终模型                                                  |
| `final_model_family`              | string   | index | 最终模型族                                                 |
| `final_trial_id`                  | string   | index | 最终 trial                                              |
| `methods_used_json`               | JSONB    |       | 解释方法                                                  |
| `global_feature_importance_json`  | JSONB    |       | 全局特征重要性                                               |
| `permutation_importance_json`     | JSONB    |       | permutation importance                                |
| `shap_summary_json`               | JSONB    |       | SHAP 摘要                                               |
| `local_explanations_json`         | JSONB    |       | 局部解释                                                  |
| `high_error_sample_analysis_json` | JSONB    |       | 高误差样本分析                                               |
| `material_insight_summary_json`   | JSONB    |       | LLM 材料规律解释                                            |
| `llm_summary_json`                | JSONB    |       | LLM 总结                                                |
| `final_output_input_json`         | JSONB    |       | 下游 Final Output 输入                                    |
| `artifact_manifest_json`          | JSONB    |       | artifact manifest                                     |
| `ready_for_final_output`          | boolean  | index | 是否可进入最终输出                                             |
| `llm_used`                        | boolean  |       | 是否调用 LLM                                              |
| `llm_confidence_level`            | string   |       | LLM 置信度                                               |
| `llm_request_json`                | JSONB    |       | LLM 请求                                                |
| `llm_response_json`               | JSONB    |       | LLM 响应                                                |
| `error_message`                   | string   |       | 错误信息                                                  |
| `created_at`                      | datetime | index | 创建时间                                                  |
| `updated_at`                      | datetime |       | 更新时间                                                  |

---

## 16. 状态设计

### 16.1 InterpretabilityAnalysisStatus

| 状态                      | 说明                     |
| ----------------------- | ---------------------- |
| `analyzing`             | 正在解释分析                 |
| `analyzed`              | 解释分析成功                 |
| `analyzed_with_warning` | 分析成功，但部分解释方法失败或 LLM 失败 |
| `failed`                | 分析失败                   |

---

### 16.2 InterpretabilityMethodStatus

| 状态              | 说明             |
| --------------- | -------------- |
| `computed`      | 成功计算           |
| `skipped`       | 不适用或用户关闭       |
| `failed`        | 计算失败           |
| `fallback_used` | 使用 fallback 方法 |

---

## 17. Artifact 设计

### 17.1 Artifact 根目录

```text
/app/artifacts/interpretability/{interpretability_analysis_id}/
```

目录结构：

```text
interpretability/{interpretability_analysis_id}/
    ├── manifest.json
    ├── interpretability_analysis_result.json
    ├── global_feature_importance.json
    ├── permutation_importance.json
    ├── shap/
    │   ├── shap_values.parquet
    │   ├── shap_summary.json
    │   └── shap_sample_metadata.json
    ├── local_explanations.json
    ├── high_error_sample_analysis.json
    ├── feature_group_summary.json
    ├── material_insight_summary.json
    ├── llm_interpretability_summary.json
    └── final_output_input.json
```

---

## 18. API 设计

### 18.1 创建 Interpretability Analysis

```text
POST /api/interpretability-analyses/{task_id}
```

---

### 18.2 获取指定 Interpretability Analysis

```text
GET /api/interpretability-analyses/{interpretability_analysis_id}
```

---

### 18.3 获取任务最新 Interpretability Analysis

```text
GET /api/tasks/{task_id}/interpretability-analysis
```

---

### 18.4 重新运行解释性分析

```text
POST /api/interpretability-analyses/{task_id}/rerun
```

---

### 18.5 获取 Global Feature Importance

```text
GET /api/interpretability-analyses/{interpretability_analysis_id}/feature-importance
```

---

### 18.6 获取 SHAP Summary

```text
GET /api/interpretability-analyses/{interpretability_analysis_id}/shap-summary
```

---

### 18.7 获取 Local Explanations

```text
GET /api/interpretability-analyses/{interpretability_analysis_id}/local-explanations
```

---

### 18.8 获取 Final Output Input

```text
GET /api/interpretability-analyses/{interpretability_analysis_id}/final-output-input
```

---

## 19. 前端功能设计

### 19.1 新增前端文件结构

```text
frontend/src/api/interpretabilityAnalysisApi.ts

frontend/src/modules/interpretabilityAnalysis/
    ├── components/
    │   ├── InterpretabilityAnalysisPanel.tsx
    │   ├── InterpretabilitySummaryCard.tsx
    │   ├── GlobalFeatureImportanceTable.tsx
    │   ├── FeatureImportanceChart.tsx
    │   ├── ShapSummaryCard.tsx
    │   ├── ShapFeatureRankingTable.tsx
    │   ├── LocalExplanationTable.tsx
    │   ├── HighErrorSampleAnalysisCard.tsx
    │   ├── FeatureGroupSummaryCard.tsx
    │   ├── MaterialInsightSummaryCard.tsx
    │   ├── InterpretabilityRiskNotesCard.tsx
    │   ├── FinalOutputInputCard.tsx
    │   └── InterpretabilityAnalysisJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

---

### 19.2 页面集成位置

新增在 Final Pipeline Selection 后：

```text
Final Pipeline Selection
Interpretability Analysis   ← 新增
Final Output
```

---

### 19.3 主面板功能

`InterpretabilityAnalysisPanel` 应提供：

| 功能                            | 说明         |
| ----------------------------- | ---------- |
| Run Interpretability Analysis | 启动解释性分析    |
| Re-run Analysis               | 重新运行分析     |
| Load Latest                   | 加载最新结果     |
| View Feature Importance       | 查看全局特征重要性  |
| View SHAP Summary             | 查看 SHAP 摘要 |
| View Local Explanations       | 查看局部解释     |
| View High Error Samples       | 查看高误差样本    |
| View Material Insights        | 查看材料规律解释   |
| View Final Output Input       | 查看最终输出输入   |
| View Full JSON                | 查看完整 JSON  |

---

### 19.4 前端展示顺序

推荐展示：

```text
1. Interpretability Summary
2. Global Feature Importance
3. Feature Importance Chart
4. SHAP Summary
5. Local Explanations
6. High Error Sample Analysis
7. Feature Group Summary
8. Material Insight Summary
9. Interpretability Risk Notes
10. Final Output Input
11. Full JSON
```

---

### 19.5 Interpretability Summary Card

展示：

* analysis id；
* status；
* final model；
* final model family；
* final trial；
* methods used；
* SHAP available；
* LLM summary status；
* ready for Final Output。

---

### 19.6 Global Feature Importance Table

字段：

| 列                   | 说明   |
| ------------------- | ---- |
| Rank                | 排名   |
| Feature             | 特征名  |
| Importance          | 重要性  |
| Method              | 方法   |
| Direction           | 方向   |
| Feature Group       | 特征组  |
| Interpretation Hint | 解释提示 |

---

### 19.7 SHAP Summary Card

展示：

* shap available；
* explainer type；
* n samples explained；
* top shap features；
* warnings；
* shap artifact paths。

---

### 19.8 Local Explanation Table

展示：

* sample id；
* y_true；
* y_pred；
* error；
* top positive features；
* top negative features；
* local summary。

---

### 19.9 High Error Sample Analysis Card

展示：

* high-error sample list；
* absolute error；
* possible error factors；
* local feature pattern；
* review suggestion。

---

### 19.10 Material Insight Summary Card

展示 LLM 生成的：

* top material patterns；
* supporting features；
* possible material meaning；
* domain hypotheses；
* limitations；
* confidence level。

前端需要明显标注：

```text
These insights are model-based interpretations, not causal conclusions.
```

中文：

```text
这些解释是基于模型行为的关联性解释，不等同于确定性因果机理。
```

---

## 20. 前端状态与交互

### 20.1 按钮启用规则

| 条件                                          | Run Interpretability Analysis |
| ------------------------------------------- | ----------------------------- |
| 无 task_id                                   | disabled                      |
| 无 FinalPipelineSelection                    | disabled                      |
| FinalPipelineSelection 未 ready              | disabled                      |
| 正在 analyzing                                | loading                       |
| 已 analyzed 且 force_rerun=false              | 显示 Load Latest / Re-run       |
| 上游 ready_for_interpretability_analysis=true | enabled                       |

---

### 20.2 状态颜色建议

| 状态                            | 颜色     |
| ----------------------------- | ------ |
| `analyzing`                   | blue   |
| `analyzed`                    | green  |
| `analyzed_with_warning`       | orange |
| `failed`                      | red    |
| `ready_for_final_output=true` | green  |
| `shap failed / fallback`      | orange |

---

## 21. 安全设计

### 21.1 绝对禁止

本模块禁止：

1. 重新训练模型；
2. 调用 `model.fit()`；
3. 修改模型 artifact；
4. 修改 feature matrix；
5. 修改 prediction artifact；
6. 修改 metric result；
7. 修改 final selection；
8. 动态执行 LLM 输出；
9. 接受用户自定义解释代码；
10. 让 LLM 修改数值解释结果；
11. 让 LLM 声称确定性因果机制。

---

### 21.2 路径安全

所有输入路径必须：

* 来自 FinalPipelineSelection；
* 位于允许 artifact 目录；
* 不包含 `..`；
* 文件存在；
* 文件类型符合预期。

所有输出写入：

```text
/app/artifacts/interpretability/{interpretability_analysis_id}/
```

---

### 21.3 LLM 安全

LLM 仅能输出解释性文本和结构化总结。

不得输出：

* executable code；
* modified importance values；
* modified SHAP values；
* modified predictions；
* model update；
* feature update；
* causal certainty claim。

---

## 22. 异常设计

建议新增异常：

| 异常类                                         | error_code                                       | 场景               |
| ------------------------------------------- | ------------------------------------------------ | ---------------- |
| `InterpretabilityAnalysisNotFoundException` | `INTERPRETABILITY_ANALYSIS_NOT_FOUND`            | 找不到记录            |
| `FinalPipelineSelectionRequiredException`   | `FINAL_PIPELINE_SELECTION_REQUIRED`              | 缺少上游最终选择         |
| `FinalPipelineSelectionNotReadyException`   | `FINAL_SELECTION_NOT_READY_FOR_INTERPRETABILITY` | 上游未 ready        |
| `InterpretabilityInputInvalidException`     | `INTERPRETABILITY_INPUT_INVALID`                 | 输入合同无效           |
| `ModelArtifactLoadException`                | `MODEL_ARTIFACT_LOAD_FAILED`                     | 模型 artifact 加载失败 |
| `FeatureMatrixLoadException`                | `FEATURE_MATRIX_LOAD_FAILED`                     | 特征矩阵加载失败         |
| `PredictionArtifactLoadException`           | `PREDICTION_ARTIFACT_LOAD_FAILED`                | 预测结果加载失败         |
| `InterpretabilityMethodSelectionException`  | `INTERPRETABILITY_METHOD_SELECTION_FAILED`       | 方法选择失败           |
| `FeatureImportanceCalculationException`     | `FEATURE_IMPORTANCE_CALCULATION_FAILED`          | 特征重要性计算失败        |
| `ShapCalculationException`                  | `SHAP_CALCULATION_FAILED`                        | SHAP 计算失败        |
| `LocalExplanationException`                 | `LOCAL_EXPLANATION_FAILED`                       | 局部解释失败           |
| `LLMInterpretabilitySummaryException`       | `LLM_INTERPRETABILITY_SUMMARY_FAILED`            | LLM 总结失败         |
| `FinalOutputInputBuildException`            | `FINAL_OUTPUT_INPUT_BUILD_FAILED`                | 下游输入构建失败         |
| `InterpretabilityArtifactSaveException`     | `INTERPRETABILITY_ARTIFACT_SAVE_FAILED`          | artifact 保存失败    |

---

## 23. MVP 验收标准

### 23.1 后端验收标准

必须满足：

1. 可以通过 API 创建 Interpretability Analysis；
2. 必须校验 `FinalPipelineSelection.ready_for_interpretability_analysis = true`；
3. 必须消费 `interpretability_analysis_input_json`；
4. 能加载最终模型 artifact；
5. 能加载 model-ready feature matrix；
6. 能加载 prediction artifact；
7. 能根据 model family 选择解释方法；
8. 能计算 global feature importance；
9. 能计算 permutation importance；
10. 对 linear/tree 模型能计算 SHAP 或成功 fallback；
11. 能生成 local explanations；
12. 能生成 high-error sample analysis；
13. MVP 阶段必须调用 LLM Interpretability Summarizer；
14. LLM 必须输出材料规律解释、限制和风险提示；
15. LLM 不得修改数值解释结果；
16. 能生成 final_output_input_json；
17. 能持久化完整结果；
18. 不重新训练模型；
19. 不执行任意代码。

---

### 23.2 前端验收标准

必须满足：

1. 新增 Interpretability Analysis 面板；
2. 可以点击 Run Interpretability Analysis；
3. 可以点击 Re-run；
4. 可以展示 final model；
5. 可以展示解释方法；
6. 可以展示 global feature importance；
7. 可以展示 SHAP summary；
8. 可以展示 local explanations；
9. 可以展示 high-error sample analysis；
10. 可以展示 material insight summary；
11. 可以展示 interpretability risk notes；
12. 可以展示 ready_for_final_output；
13. 可以查看完整 JSON。

---

### 23.3 安全验收标准

必须满足：

1. 不允许重新训练；
2. 不允许修改模型；
3. 不允许修改预测；
4. 不允许修改 SHAP / importance 数值；
5. 不允许 LLM 输出可执行代码；
6. 不允许用户自定义解释代码；
7. 所有路径必须经过安全校验；
8. LLM 解释必须标注为模型关联性解释，不是因果结论。

---

## 24. 推荐实现优先级

### P0：必须完成

1. 后端 `interpretability_analysis` 模块；
2. `InterpretabilityAnalysis` 数据表；
3. `context_builder`；
4. `interpretability_input_loader`；
5. `model_artifact_loader`；
6. `feature_matrix_loader`；
7. `prediction_artifact_loader`；
8. `interpretability_method_selector`；
9. `permutation_importance_analyzer`；
10. `shap_analyzer`；
11. `global_feature_importance` 构建；
12. `local_explanation_builder`；
13. `llm_interpretability_summarizer`；
14. `final_output_input_builder`；
15. 核心 API；
16. 前端主面板；
17. Feature Importance 展示；
18. SHAP Summary 展示；
19. Material Insight 展示；
20. Final Output Input 展示。

---

### P1：建议完成

1. coefficient importance；
2. native tree importance；
3. high-error sample analysis；
4. feature group summary；
5. SHAP artifact 可视化数据；
6. LLM fallback 展示；
7. explanation risk notes。

---

### P2：后续迭代

1. SHAP dependence plot 数据；
2. PDP / ICE 分析；
3. 多模型解释对比；
4. 结构特征解释；
5. 材料领域知识库增强解释；
6. 论文图表导出；
7. 自动生成图注和报告段落。

---

## 25. 给 AI Coding 工具的实现提示词

```text
请基于当前 MLAgent 项目实现模块十五 Interpretability Analysis。开发前先阅读 PROJECT_IMPLEMENTATION_OVERVIEW.md，重点理解模块十四 Final Pipeline Selection 的 interpretability_analysis_input_json 输出合同。

实现要求：
1. 新增 backend/app/modules/interpretability_analysis 模块，结构遵循现有模块模式：api.py、service.py、model.py、repository.py、schemas.py、enums.py、exceptions.py、context_builder.py、builder.py 等；
2. 本模块消费 FinalPipelineSelection.interpretability_analysis_input_json，必须校验 FinalPipelineSelection.ready_for_interpretability_analysis=true；
3. 加载最终模型 artifact、model-ready feature matrix、feature columns、prediction artifacts、preprocessor artifact；
4. 根据 final_model_family 选择解释方法，MVP 至少支持 permutation importance，并对 linear/tree 模型支持 SHAP 或 fallback；
5. 生成 global_feature_importance、permutation_importance、shap_summary、local_explanations、high_error_sample_analysis；
6. MVP 阶段必须实现 LLM Interpretability Summarizer，LLM 只负责基于系统计算结果生成材料规律解释、限制说明和风险提示；
7. LLM 不得修改 feature importance、SHAP values、prediction、metric 或 final selection；
8. LLM 输出必须经过 parser、validator、normalizer，并扫描 import/def/class/eval/exec/subprocess/model.fit/Pipeline 等危险模式；
9. 构建 final_output_input_json，供模块十六 Final Output 使用；
10. 保存解释性 artifacts 到 /app/artifacts/interpretability/{interpretability_analysis_id}/；
11. 前端新增 InterpretabilityAnalysisPanel，展示 summary、global feature importance、SHAP summary、local explanations、high-error samples、material insights、risk notes、final output input 和完整 JSON；
12. 严禁重新训练模型、重新计算最终选择、执行任意代码、修改上游 artifact 或让 LLM 输出可执行逻辑。
```

---

## 26. 总结

**Interpretability Analysis** 是 MLAgent 从“最终模型选择”进入“可解释交付”的关键模块。

它的核心价值是：

```text
把最终选中的模型从一个性能结果，转化为可解释、可审查、可报告的材料机器学习结果。
```

本模块的最终形态是：

```text
系统计算解释结果；
LLM 总结解释含义。
```

也就是：

```text
System Interpretability Engine:
    计算 feature importance / SHAP / local explanations

LLM Interpretability Summarizer:
    总结重要特征
    生成材料规律假设
    提醒解释风险
    生成报告可用自然语言解释
```

本模块必须坚持：

```text
只解释，不训练；
只总结，不篡改；
系统计算是权威；
LLM 解释是辅助；
材料规律必须表达为模型关联性假设，而非确定性因果结论。
```

完成该模块后，MLAgent 将具备从最终模型到可解释材料规律总结的能力，并为最后一步 **Final Output** 提供完整、结构化、可复现的解释性输入。
