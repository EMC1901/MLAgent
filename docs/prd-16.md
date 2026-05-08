# PRD：Final Output 模块

> 项目名称：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：16
> 模块名称：Final Output
> 中文名称：最终输出 / 最终交付
> 上游模块：Interpretability Analysis
> 下游模块：无，作为当前 AutoML 任务的最终交付模块
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0
> 输出格式：Markdown

---

## 1. 背景与上下文

当前 MLAgent 已完成从任务输入到模型解释的完整自动化链路：

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
15. Interpretability Analysis
```

模块 15 **Interpretability Analysis** 已经完成最终模型的解释性分析，并输出：

```text
final_output_input_json
```

该输入中包含：

* 最终模型信息；
* 最终 trial 信息；
* 最终 pipeline 信息；
* 模型 artifact；
* 预测结果 artifact；
* 指标摘要；
* final selection summary；
* global feature importance；
* SHAP summary；
* material insight summary；
* interpretability artifacts；
* workflow trace references；
* `ready_for_final_output` 状态。

因此，本模块 **Final Output** 的核心任务是：

> 汇总 MLAgent 全流程的最终产物，生成可下载、可审查、可复现、可交付的最终结果包，包括模型文件、预测结果、实验记录、workflow trace、解释性结果和可复现实验报告。

---

## 2. 模块定位

### 2.1 一句话定义

**Final Output 是 MLAgent 的最终交付模块。它负责汇总最终模型、实验记录、指标评估、解释性分析、workflow trace 和 artifact manifest，生成用户可下载、可复现、可审查的最终输出结果包与实验报告。**

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
Final Pipeline Selection
  ↓
Interpretability Analysis
  ↓
Final Output   ← 当前模块
```

---

## 4. 模块核心职责

Final Output 需要完成以下工作：

1. 消费 Interpretability Analysis 输出的 `final_output_input_json`；
2. 校验 `ready_for_final_output = true`；
3. 收集最终模型 artifact；
4. 收集最终预测结果 artifact；
5. 收集最终指标评估结果；
6. 收集 Final Pipeline Selection 结果；
7. 收集 Interpretability Analysis 结果；
8. 收集完整 workflow trace；
9. 汇总数据集、特征工程、模型搜索、训练、评估、诊断、迭代、最终选择、解释性分析的关键记录；
10. 生成最终 artifact manifest；
11. 生成最终实验摘要；
12. 生成可复现实验配置摘要；
13. 调用 LLM 生成自然语言最终报告；
14. 生成最终输出包；
15. 生成下载入口；
16. 持久化 Final Output 结果；
17. 前端展示最终模型、指标、解释性结果、报告摘要、artifact 清单、下载入口和完整 JSON。

---

## 5. 与上游模块的边界

### 5.1 与 Interpretability Analysis 的边界

Interpretability Analysis 负责：

* 计算 feature importance；
* 计算 SHAP；
* 生成 local explanations；
* 分析高误差样本；
* 生成材料规律解释；
* 输出 `final_output_input_json`。

Final Output 负责：

* 汇总解释性结果；
* 生成最终报告；
* 打包最终 artifact；
* 输出最终交付结果。

Final Output 不负责：

* 重新计算 SHAP；
* 重新计算 feature importance；
* 重新生成解释性分析；
* 修改材料规律解释。

---

### 5.2 与 Final Pipeline Selection 的边界

Final Pipeline Selection 负责：

* 选择最终 pipeline；
* 选择最终 model；
* 选择最终 trial；
* 生成最终 artifact manifest；
* 输出 Interpretability Analysis 输入。

Final Output 只引用最终选择结果，不重新选择模型。

---

### 5.3 与 Metric Evaluation 的边界

Metric Evaluation 负责指标计算和模型 ranking。

Final Output 只展示和汇总指标结果，不重新计算指标。

---

### 5.4 与 Pipeline Execution 的边界

Pipeline Execution 负责训练、预测和保存模型 artifact。

Final Output 只打包模型文件和预测结果，不重新训练、不重新预测。

---

## 6. 核心设计原则

### 6.1 Final Output 只汇总，不再决策

本模块已经处于 MLAgent 最终阶段，因此不再做：

* 模型选择；
* 模型训练；
* HPO；
* 指标计算；
* 解释性分析；
* workflow refinement；
* 任务重跑。

它只做：

```text
汇总 → 校验 → 归档 → 报告生成 → 输出交付
```

---

### 6.2 系统负责 artifact 归档，LLM 负责报告文本生成

本模块采用：

```text
System Output Builder + LLM Report Writer
```

其中：

```text
System Output Builder
```

负责：

* 收集 artifacts；
* 校验路径；
* 构建 manifest；
* 构建 workflow trace；
* 构建 reproducibility summary；
* 生成最终 JSON；
* 生成最终输出包。

```text
LLM Report Writer
```

负责：

* 生成最终实验报告；
* 总结任务目标；
* 总结数据与特征；
* 总结模型搜索与最终选择；
* 总结指标表现；
* 总结解释性分析；
* 总结限制和注意事项；
* 生成面向用户的自然语言报告。

LLM 不允许：

* 修改指标；
* 修改最终模型；
* 修改最终选择；
* 修改 SHAP / feature importance；
* 修改 artifact 路径；
* 生成可执行代码；
* 夸大材料机理结论；
* 声称模型解释等同于因果发现。

---

### 6.3 输出必须可复现

Final Output 必须包含足够信息，使用户未来可以理解和复现实验流程。

至少需要记录：

* task specification；
* task interpretation；
* dataset profile；
* workflow plan；
* feature engineering summary；
* preprocessing summary；
* model search plan；
* pipeline generation summary；
* execution summary；
* metric evaluation summary；
* result diagnosis summary；
* workflow refinement decision；
* final pipeline selection；
* interpretability analysis；
* artifacts；
* environment summary；
* model and prediction paths；
* report generation time。

---

### 6.4 最终报告必须区分事实与解释

最终报告中必须区分：

```text
系统计算事实
```

和：

```text
LLM 解释性总结
```

例如：

* MAE、RMSE、R2 是系统计算事实；
* SHAP top features 是系统计算事实；
* “这些特征可能反映某类材料化学因素”是 LLM 解释性假设；
* 不能把模型关联性解释写成确定性因果结论。

---

## 7. 产品目标

### 7.1 MVP 目标

MVP 阶段需要实现：

1. 读取最新或指定 InterpretabilityAnalysis；
2. 校验 `ready_for_final_output = true`；
3. 加载 `final_output_input_json`；
4. 收集最终模型 artifact；
5. 收集预测结果 artifact；
6. 收集 metric summary；
7. 收集 final selection summary；
8. 收集 interpretability results；
9. 收集 workflow trace refs；
10. 构建 final artifact manifest；
11. 构建 reproducibility summary；
12. 构建 final output summary；
13. 调用 LLM 生成最终报告；
14. 生成最终 JSON 报告；
15. 生成最终 Markdown 报告；
16. 生成最终 output package；
17. 输出下载路径；
18. 持久化 Final Output 记录；
19. 前端展示最终结果摘要、报告、artifact 清单、下载入口和完整 JSON。

---

### 7.2 非目标

MVP 阶段不做：

1. 不重新训练模型；
2. 不重新预测；
3. 不重新计算指标；
4. 不重新执行解释性分析；
5. 不重新选择最终 pipeline；
6. 不自动部署模型；
7. 不生成生产推理服务；
8. 不生成论文全文；
9. 不生成 Notebook；
10. 不让 LLM 输出可执行代码；
11. 不让 LLM 修改系统事实数据；
12. 不让 LLM 覆盖最终选择结果。

---

## 8. 输入设计

### 8.1 API 请求输入

接口：

```text
POST /api/final-outputs/{task_id}
```

请求字段：

| 字段                                   | 类型      | 必填 | 说明                                           |
| ------------------------------------ | ------- | -: | -------------------------------------------- |
| `interpretability_analysis_id`       | string  |  否 | 指定 InterpretabilityAnalysis；为空则使用最新 ready 记录 |
| `force_rerun`                        | boolean |  否 | 是否强制重新生成最终输出，默认 false                        |
| `use_llm_report_writer`              | boolean |  否 | 是否调用 LLM 生成最终报告，MVP 默认 true                  |
| `report_profile`                     | string  |  否 | `compact` / `standard` / `full`，默认 standard  |
| `output_format`                      | array   |  否 | 输出格式，默认 `["json", "markdown"]`               |
| `include_model_artifact`             | boolean |  否 | 是否包含模型 artifact，默认 true                      |
| `include_prediction_artifact`        | boolean |  否 | 是否包含预测结果，默认 true                             |
| `include_workflow_trace`             | boolean |  否 | 是否包含 workflow trace，默认 true                  |
| `include_interpretability_artifacts` | boolean |  否 | 是否包含解释性 artifact，默认 true                     |
| `include_reproducibility_summary`    | boolean |  否 | 是否包含复现摘要，默认 true                             |
| `notes`                              | string  |  否 | 用户备注                                         |

---

### 8.2 必需上游输入

| 来源                         | 必需字段                                                                                                                                                                                                                                                        |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `InterpretabilityAnalysis` | `id`, `task_id`, `status`, `ready_for_final_output`, `final_output_input_json`                                                                                                                                                                              |
| `final_output_input_json`  | `final_model_id`, `final_trial_id`, `model_artifact_path`, `prediction_artifact_paths`, `metric_summary`, `selection_summary`, `global_feature_importance`, `shap_summary`, `material_insight_summary`, `interpretability_artifacts`, `workflow_trace_refs` |
| `FinalPipelineSelection`   | `selection_json`, `final_artifact_manifest`, `system_selection_reason`, `llm_selection_explanation`                                                                                                                                                         |
| `MetricEvaluation`         | `metric_summary_json`, `model_ranking_json`, `baseline_comparison`                                                                                                                                                                                          |
| `PipelineExecution`        | `execution_json`, `training_artifact_manifest`                                                                                                                                                                                                              |
| `PipelineGeneration`       | `pipeline_json`, `pipeline_bundle`                                                                                                                                                                                                                          |
| `ModelSearchPlan`          | `plan_json`                                                                                                                                                                                                                                                 |
| `WorkflowRefinement`       | `workflow_refinement_json`, `decision`, `revised_workflow_plan_json`                                                                                                                                                                                        |
| `ResultDiagnosis`          | `diagnosis_json`                                                                                                                                                                                                                                            |
| `FeaturePreprocessing`     | `preprocessing_json`, `preprocessor_artifact_path`                                                                                                                                                                                                          |
| `FeatureEngineering`       | `feature_json`, `feature_artifact_path`                                                                                                                                                                                                                     |
| `DatasetProfile`           | `profile_json`                                                                                                                                                                                                                                              |
| `TaskSpecification`        | `task_spec_json`                                                                                                                                                                                                                                            |
| `TaskInterpretation`       | `interpretation_json`                                                                                                                                                                                                                                       |

---

## 9. 输出设计

### 9.1 核心输出：FinalOutputResponse

| 字段                             | 类型          | 说明                                                |
| ------------------------------ | ----------- | ------------------------------------------------- |
| `final_output_id`              | string      | 最终输出 ID，例如 `fo_xxxxxxxx`                          |
| `task_id`                      | string      | 任务 ID                                             |
| `interpretability_analysis_id` | string      | 上游解释性分析 ID                                        |
| `final_pipeline_selection_id`  | string      | 最终选择 ID                                           |
| `status`                       | string      | `generated` / `generated_with_warning` / `failed` |
| `report_profile`               | string      | compact / standard / full                         |
| `final_model_summary`          | object      | 最终模型摘要                                            |
| `final_metric_summary`         | object      | 最终指标摘要                                            |
| `final_selection_summary`      | object      | 最终选择摘要                                            |
| `interpretability_summary`     | object      | 解释性摘要                                             |
| `workflow_trace_summary`       | object      | 全流程 trace 摘要                                      |
| `reproducibility_summary`      | object      | 可复现摘要                                             |
| `final_artifact_manifest`      | object      | 最终 artifact 清单                                    |
| `final_report`                 | object      | 最终报告内容                                            |
| `llm_report_summary`           | object      | LLM 生成的自然语言报告                                     |
| `output_package_manifest`      | object      | 输出包清单                                             |
| `download_links`               | object      | 下载链接或路径                                           |
| `ready_for_delivery`           | boolean     | 是否可交付                                             |
| `warnings`                     | array       | 警告                                                |
| `error_message`                | string/null | 错误信息                                              |
| `created_at`                   | datetime    | 创建时间                                              |
| `updated_at`                   | datetime    | 更新时间                                              |

---

## 10. 核心数据结构设计

### 10.1 FinalModelSummary

```json
{
  "final_model_id": "ridge",
  "final_model_family": "ridge",
  "final_trial_id": "trial_ridge_0003",
  "final_pipeline_spec_id": "ps_ridge_28d4dd",
  "final_hyperparameters": {
    "alpha": 1.0
  },
  "model_artifact_path": "/app/artifacts/training/pe_xxx/models/trial_ridge_0003.joblib",
  "selection_reason_summary": "Selected for the best balance between metric performance, stability, interpretability, and cost."
}
```

---

### 10.2 FinalMetricSummary

| 字段                       | 类型      | 说明                  |
| ------------------------ | ------- | ------------------- |
| `primary_metric`         | string  | 主指标                 |
| `primary_metric_value`   | float   | 主指标值                |
| `metric_direction`       | string  | minimize / maximize |
| `secondary_metrics`      | object  | 次指标                 |
| `baseline_comparison`    | object  | baseline 对比         |
| `model_ranking_position` | integer | 最终模型排名              |
| `stability_summary`      | object  | 稳定性摘要               |

---

### 10.3 FinalSelectionSummary

| 字段                             | 类型     | 说明        |
| ------------------------------ | ------ | --------- |
| `final_pipeline_selection_id`  | string | 最终选择 ID   |
| `selection_profile`            | string | 选择策略      |
| `selection_score`              | float  | 综合选择分数    |
| `system_selection_reason`      | object | 系统结构化选择理由 |
| `llm_selection_explanation`    | object | LLM 选择解释  |
| `candidate_difference_summary` | array  | 候选差异总结    |
| `risk_notes`                   | array  | 选择风险提示    |

---

### 10.4 InterpretabilitySummary

| 字段                             | 类型     | 说明              |
| ------------------------------ | ------ | --------------- |
| `interpretability_analysis_id` | string | 解释性分析 ID        |
| `methods_used`                 | array  | 使用的解释方法         |
| `top_features`                 | array  | Top features    |
| `shap_summary`                 | object | SHAP 摘要         |
| `material_insight_summary`     | object | 材料规律解释          |
| `interpretability_risk_notes`  | array  | 解释风险提示          |
| `artifact_paths`               | object | 解释性 artifact 路径 |

---

### 10.5 WorkflowTraceSummary

用于展示从任务输入到最终输出的完整流程 trace。

| 字段                             | 类型      | 说明                           |
| ------------------------------ | ------- | ---------------------------- |
| `task_specification_id`        | string  | Task Specification ID        |
| `task_interpretation_id`       | string  | Task Interpretation ID       |
| `dataset_profile_id`           | string  | Dataset Profile ID           |
| `workflow_plan_id`             | string  | Workflow Plan ID             |
| `feature_engineering_id`       | string  | Feature Engineering ID       |
| `feature_preprocessing_id`     | string  | Feature Preprocessing ID     |
| `model_search_context_id`      | string  | Model Search Context ID      |
| `model_search_plan_id`         | string  | Model Search Plan ID         |
| `pipeline_generation_id`       | string  | Pipeline Generation ID       |
| `pipeline_execution_id`        | string  | Pipeline Execution ID        |
| `metric_evaluation_id`         | string  | Metric Evaluation ID         |
| `result_diagnosis_id`          | string  | Result Diagnosis ID          |
| `workflow_refinement_id`       | string  | Workflow Refinement ID       |
| `final_pipeline_selection_id`  | string  | Final Pipeline Selection ID  |
| `interpretability_analysis_id` | string  | Interpretability Analysis ID |
| `iteration_count`              | integer | 迭代轮数                         |
| `workflow_trace_artifacts`     | object  | trace artifact 路径            |

---

### 10.6 ReproducibilitySummary

| 字段                           | 类型           | 说明             |
| ---------------------------- | ------------ | -------------- |
| `dataset_source`             | string       | 数据来源           |
| `target_column`              | string       | 目标列            |
| `feature_columns_count`      | integer      | 特征数量           |
| `feature_artifact_path`      | string       | 特征 artifact    |
| `preprocessor_artifact_path` | string       | 预处理 artifact   |
| `model_ready_matrix_path`    | string       | 模型就绪矩阵         |
| `model_artifact_path`        | string       | 模型 artifact    |
| `prediction_artifact_paths`  | array        | 预测 artifact    |
| `random_state`               | integer/null | 随机种子           |
| `validation_strategy`        | object       | 验证策略           |
| `hpo_summary`                | object       | HPO 摘要         |
| `environment_summary`        | object       | 运行环境           |
| `registry_versions`          | object       | Registry 版本，可选 |
| `created_at`                 | datetime     | 输出生成时间         |

---

### 10.7 FinalReport

最终报告结构建议：

```json
{
  "title": "Final AutoML Report for Materials Property Prediction",
  "executive_summary": "",
  "task_overview": "",
  "dataset_summary": "",
  "workflow_summary": "",
  "feature_engineering_summary": "",
  "model_search_summary": "",
  "final_model_summary": "",
  "metric_summary": "",
  "interpretability_summary": "",
  "material_insight_summary": "",
  "limitations_and_risks": "",
  "reproducibility_notes": "",
  "artifact_summary": "",
  "next_steps": ""
}
```

---

### 10.8 OutputPackageManifest

| 字段                                | 类型          | 说明                          |
| --------------------------------- | ----------- | --------------------------- |
| `output_package_id`               | string      | 输出包 ID                      |
| `package_root_dir`                | string      | 输出包目录                       |
| `json_report_path`                | string      | JSON 报告路径                   |
| `markdown_report_path`            | string      | Markdown 报告路径               |
| `model_artifact_path`             | string      | 模型 artifact                 |
| `prediction_artifact_paths`       | array       | 预测结果                        |
| `interpretability_artifact_paths` | object      | 解释性结果                       |
| `workflow_trace_path`             | string      | workflow trace              |
| `manifest_path`                   | string      | manifest                    |
| `package_zip_path`                | string/null | 压缩包路径，MVP 可选                |
| `package_status`                  | string      | complete / partial / failed |

---

## 11. LLM Report Writer 设计

### 11.1 LLM 运行时机

LLM Report Writer 必须在系统完成以下工作后运行：

```text
final output context built
artifact manifest resolved
metric summary prepared
selection summary prepared
interpretability summary prepared
workflow trace summary prepared
```

也就是：

```text
系统先汇总事实，LLM 后写报告
```

---

### 11.2 LLM 输入上下文

LLM 输入应为摘要化上下文，不应传完整大 JSON 或完整数据表。

建议包含：

1. task overview；
2. dataset summary；
3. target column；
4. feature summary；
5. workflow plan summary；
6. model search summary；
7. final selected model；
8. final hyperparameters；
9. primary metric and secondary metrics；
10. baseline comparison；
11. final selection reason；
12. top feature importance；
13. SHAP summary；
14. material insight summary；
15. interpretability limitations；
16. workflow trace summary；
17. artifact summary；
18. report style instruction。

---

### 11.3 LLM 输出内容

LLM 必须输出结构化 JSON：

```json
{
  "executive_summary": "",
  "task_overview": "",
  "dataset_summary": "",
  "workflow_summary": "",
  "feature_engineering_summary": "",
  "model_search_summary": "",
  "final_model_summary": "",
  "metric_summary": "",
  "interpretability_summary": "",
  "material_insight_summary": "",
  "limitations_and_risks": "",
  "reproducibility_notes": "",
  "artifact_summary": "",
  "next_steps": "",
  "confidence_level": "medium"
}
```

---

### 11.4 LLM Prompt 核心规则

Prompt 必须明确：

```text
You are a report writer for a materials science AutoML system.

The system has already computed all metrics, selected the final pipeline, and computed interpretability results.

You must not change metric values.
You must not change the selected model.
You must not change feature importance or SHAP values.
You must not invent artifacts.
You must not output executable code.
You must clearly distinguish model-based interpretation from causal scientific conclusions.
You must write a concise, accurate, reproducible final report.
```

---

### 11.5 LLM 安全校验

禁止字段：

```text
python_code
script
shell_command
sql
modified_metric
modified_model
modified_artifact
modified_shap_values
causal_claim_without_evidence
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

* 不采纳 LLM 报告；
* 使用系统模板生成 fallback report；
* 状态设为 `generated_with_warning`；
* `ready_for_delivery` 不受影响，只要系统 artifact 完整。

---

## 12. 后端功能设计

### 12.1 推荐目录结构

```text
backend/app/modules/final_output/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── final_output_input_loader.py
    ├── workflow_trace_collector.py
    ├── final_artifact_resolver.py
    ├── reproducibility_summary_builder.py
    ├── final_summary_builder.py
    ├── llm_report_prompt_builder.py
    ├── llm_report_writer.py
    ├── llm_report_parser.py
    ├── llm_report_validator.py
    ├── llm_report_normalizer.py
    ├── report_renderer.py
    ├── output_package_builder.py
    ├── final_output_artifact_manager.py
    └── builder.py
```

---

### 12.2 文件职责说明

| 文件                                   | 职责                                    |
| ------------------------------------ | ------------------------------------- |
| `api.py`                             | Final Output REST API                 |
| `service.py`                         | 主流程编排                                 |
| `model.py`                           | SQLModel 数据表                          |
| `repository.py`                      | CRUD 与 latest 查询                      |
| `schemas.py`                         | 请求、响应、内部 DTO                          |
| `enums.py`                           | 状态、输出格式、报告 profile 等枚举                |
| `exceptions.py`                      | 专用异常                                  |
| `context_builder.py`                 | 读取 InterpretabilityAnalysis 并校验 ready |
| `final_output_input_loader.py`       | 加载 `final_output_input_json`          |
| `workflow_trace_collector.py`        | 汇总全流程 trace                           |
| `final_artifact_resolver.py`         | 校验最终 artifact 路径                      |
| `reproducibility_summary_builder.py` | 构建复现摘要                                |
| `final_summary_builder.py`           | 构建系统事实摘要                              |
| `llm_report_prompt_builder.py`       | 构建 LLM report prompt                  |
| `llm_report_writer.py`               | 调用 LLM 生成报告                           |
| `llm_report_parser.py`               | 解析 LLM 输出                             |
| `llm_report_validator.py`            | 校验 LLM 输出                             |
| `llm_report_normalizer.py`           | 标准化 LLM 报告                            |
| `report_renderer.py`                 | 渲染 JSON / Markdown 报告                 |
| `output_package_builder.py`          | 构建最终输出包                               |
| `final_output_artifact_manager.py`   | 保存 final output artifacts             |
| `builder.py`                         | 构建最终响应                                |

---

## 13. 后端主流程

```text
FinalOutputService.create_final_output(task_id, request)
    ↓
1. build_final_output_context()
    ↓
2. load_final_output_input()
    ↓
3. validate_ready_for_final_output()
    ↓
4. collect_workflow_trace()
    ↓
5. resolve_final_artifacts()
    ↓
6. build_reproducibility_summary()
    ↓
7. build_final_output_summary()
    ↓
8. build_llm_report_context()
    ↓
9. call_llm_report_writer()
    ↓
10. parse_llm_report()
    ↓
11. validate_llm_report()
    ↓
12. normalize_llm_report()
    ↓
13. render_json_report()
    ↓
14. render_markdown_report()
    ↓
15. build_output_package()
    ↓
16. save_final_output_artifacts()
    ↓
17. build_response()
    ↓
18. persist()
```

---

### 13.1 Step 1：构建上下文

`context_builder.py` 负责：

* 根据 `task_id` 获取最新 InterpretabilityAnalysis；
* 或根据 `interpretability_analysis_id` 获取指定记录；
* 校验：

  * `status in analyzed / analyzed_with_warning`；
  * `ready_for_final_output = true`；
  * `final_output_input_json` 存在；
* 关联读取：

  * FinalPipelineSelection；
  * MetricEvaluation；
  * PipelineExecution；
  * PipelineGeneration；
  * ModelSearchPlan；
  * WorkflowRefinement；
  * ResultDiagnosis；
  * FeatureEngineering；
  * FeaturePreprocessing；
  * DatasetProfile；
  * TaskSpecification；
  * TaskInterpretation。

---

### 13.2 Step 2：加载 Final Output Input

`final_output_input_loader.py` 校验：

* `interpretability_analysis_id`；
* `final_pipeline_selection_id`；
* `task_id`；
* `final_model_id`；
* `final_trial_id`；
* `model_artifact_path`；
* `prediction_artifact_paths`；
* `metric_summary`；
* `selection_summary`；
* `global_feature_importance`；
* `material_insight_summary`；
* `workflow_trace_refs`；
* `ready_for_final_output`。

---

### 13.3 Step 3：收集 Workflow Trace

`workflow_trace_collector.py` 负责收集各模块 ID 和摘要。

输出：

```text
WorkflowTraceSummary
```

必须包含：

* 每个模块的 ID；
* 每个模块的 status；
* 每个模块的关键输出摘要；
* artifact refs；
* iteration index；
* 若存在迭代，记录 revised workflow plan 和 rerun history。

---

### 13.4 Step 4：解析最终 Artifact

`final_artifact_resolver.py` 负责校验：

* model artifact；
* prediction artifacts；
* preprocessor artifact；
* feature matrix；
* model-ready matrix；
* metric artifacts；
* interpretability artifacts；
* workflow trace artifacts。

所有路径必须：

* 存在；
* 位于允许 artifact 目录；
* 不包含 `..`；
* 文件类型符合预期；
* 不覆盖上游产物。

---

### 13.5 Step 5：构建复现摘要

`reproducibility_summary_builder.py` 汇总：

* 数据来源；
* 目标列；
* 特征列数量；
* 特征工程策略；
* 预处理策略；
* 模型搜索策略；
* HPO 策略；
* 验证策略；
* 最终模型；
* 最终参数；
* random state；
* artifact 路径；
* 环境摘要。

---

### 13.6 Step 6：构建系统事实摘要

`final_summary_builder.py` 构建：

* final model summary；
* final metric summary；
* final selection summary；
* interpretability summary；
* workflow trace summary；
* artifact summary。

这些是系统事实，不依赖 LLM。

---

### 13.7 Step 7：调用 LLM Report Writer

LLM 只负责生成报告文本。

如果 LLM 失败：

* 使用系统模板 fallback；
* status 可设为 `generated_with_warning`；
* 不影响 artifact package 生成。

---

### 13.8 Step 8：渲染报告

`report_renderer.py` 输出：

1. JSON report；
2. Markdown report。

MVP 阶段建议优先支持：

```text
final_report.json
final_report.md
```

后续可扩展 PDF / DOCX。

---

### 13.9 Step 9：构建输出包

`output_package_builder.py` 生成输出目录：

```text
/app/artifacts/final_output/{final_output_id}/
```

并保存：

* final_report.json；
* final_report.md；
* manifest.json；
* artifact_manifest.json；
* workflow_trace.json；
* reproducibility_summary.json；
* optional package zip。

---

## 14. 数据库设计

### 14.1 新增表：FinalOutput

表名建议：

```text
final_output
```

字段设计：

| 字段                             | 类型       | 索引    | 说明                                          |
| ------------------------------ | -------- | ----- | ------------------------------------------- |
| `id`                           | string   | PK    | `fo_{uuid8}`                                |
| `task_id`                      | string   | index | 任务 ID                                       |
| `interpretability_analysis_id` | string   | index | 上游 InterpretabilityAnalysis ID              |
| `final_pipeline_selection_id`  | string   | index | FinalPipelineSelection ID                   |
| `status`                       | string   | index | generated / generated_with_warning / failed |
| `report_profile`               | string   | index | compact / standard / full                   |
| `final_model_id`               | string   | index | 最终模型                                        |
| `final_trial_id`               | string   | index | 最终 trial                                    |
| `primary_metric`               | string   | index | 主指标                                         |
| `primary_metric_value`         | float    |       | 主指标值                                        |
| `ready_for_delivery`           | boolean  | index | 是否可交付                                       |
| `final_output_json`            | JSONB    |       | 完整最终输出                                      |
| `final_report_json`            | JSONB    |       | 报告结构                                        |
| `llm_report_json`              | JSONB    |       | LLM 报告                                      |
| `workflow_trace_json`          | JSONB    |       | workflow trace                              |
| `reproducibility_summary_json` | JSONB    |       | 复现摘要                                        |
| `artifact_manifest_json`       | JSONB    |       | artifact 清单                                 |
| `output_package_manifest_json` | JSONB    |       | 输出包清单                                       |
| `download_links_json`          | JSONB    |       | 下载路径                                        |
| `llm_used`                     | boolean  |       | 是否调用 LLM                                    |
| `llm_confidence_level`         | string   |       | LLM 置信度                                     |
| `llm_request_json`             | JSONB    |       | LLM 请求                                      |
| `llm_response_json`            | JSONB    |       | LLM 响应                                      |
| `artifact_dir`                 | string   |       | final output artifact 目录                    |
| `error_message`                | string   |       | 错误信息                                        |
| `created_at`                   | datetime | index | 创建时间                                        |
| `updated_at`                   | datetime |       | 更新时间                                        |

---

## 15. 状态设计

### 15.1 FinalOutputStatus

| 状态                       | 说明                                |
| ------------------------ | --------------------------------- |
| `generating`             | 正在生成最终输出                          |
| `generated`              | 成功生成最终输出                          |
| `generated_with_warning` | 输出成功，但部分非关键内容失败，如 LLM 报告 fallback |
| `failed`                 | 最终输出失败                            |

---

### 15.2 ready_for_delivery 规则

| 条件                               | ready_for_delivery |
| -------------------------------- | ------------------ |
| final_report.json 存在             | true               |
| manifest.json 存在                 | true               |
| final model artifact 可引用         | true               |
| metric summary 存在                | true               |
| final output package manifest 存在 | true               |
| 缺少模型 artifact                    | false              |
| 缺少 report                        | false              |
| artifact manifest 构建失败           | false              |

---

## 16. Artifact 设计

### 16.1 Artifact 根目录

```text
/app/artifacts/final_output/{final_output_id}/
```

目录结构：

```text
final_output/{final_output_id}/
    ├── manifest.json
    ├── final_output_result.json
    ├── final_report.json
    ├── final_report.md
    ├── workflow_trace.json
    ├── reproducibility_summary.json
    ├── artifact_manifest.json
    ├── output_package_manifest.json
    ├── llm_report.json
    └── package/
        ├── model/
        │   └── model_artifact_ref.json
        ├── predictions/
        │   └── prediction_artifacts_ref.json
        ├── interpretability/
        │   └── interpretability_artifacts_ref.json
        └── reports/
            ├── final_report.json
            └── final_report.md
```

MVP 阶段可以先保存引用路径，不复制大文件。

后续版本可支持将 artifact 复制或压缩到统一交付包。

---

## 17. API 设计

### 17.1 创建 Final Output

```text
POST /api/final-outputs/{task_id}
```

---

### 17.2 获取指定 Final Output

```text
GET /api/final-outputs/{final_output_id}
```

---

### 17.3 获取任务最新 Final Output

```text
GET /api/tasks/{task_id}/final-output
```

---

### 17.4 重新生成 Final Output

```text
POST /api/final-outputs/{task_id}/rerun
```

---

### 17.5 获取最终报告

```text
GET /api/final-outputs/{final_output_id}/report
```

---

### 17.6 获取 Workflow Trace

```text
GET /api/final-outputs/{final_output_id}/workflow-trace
```

---

### 17.7 获取 Artifact Manifest

```text
GET /api/final-outputs/{final_output_id}/artifact-manifest
```

---

### 17.8 获取下载链接

```text
GET /api/final-outputs/{final_output_id}/downloads
```

---

## 18. 前端功能设计

### 18.1 新增前端文件结构

```text
frontend/src/api/finalOutputApi.ts

frontend/src/modules/finalOutput/
    ├── components/
    │   ├── FinalOutputPanel.tsx
    │   ├── FinalOutputSummaryCard.tsx
    │   ├── FinalModelSummaryCard.tsx
    │   ├── FinalMetricSummaryCard.tsx
    │   ├── FinalReportViewer.tsx
    │   ├── WorkflowTraceCard.tsx
    │   ├── ReproducibilitySummaryCard.tsx
    │   ├── FinalArtifactManifestCard.tsx
    │   ├── DownloadLinksCard.tsx
    │   ├── LLMReportSummaryCard.tsx
    │   └── FinalOutputJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

---

### 18.2 页面集成位置

新增在 Interpretability Analysis 后：

```text
Interpretability Analysis
Final Output   ← 新增
```

---

### 18.3 主面板功能

`FinalOutputPanel` 应提供：

| 功能                           | 说明             |
| ---------------------------- | -------------- |
| Generate Final Output        | 生成最终输出         |
| Re-generate Output           | 重新生成           |
| Load Latest                  | 加载最新结果         |
| View Final Report            | 查看最终报告         |
| View Workflow Trace          | 查看全流程 trace    |
| View Reproducibility Summary | 查看复现摘要         |
| View Artifacts               | 查看 artifact 清单 |
| View Downloads               | 查看下载入口         |
| View Full JSON               | 查看完整 JSON      |

---

### 18.4 前端展示顺序

推荐展示：

```text
1. Final Output Summary
2. Final Model Summary
3. Final Metric Summary
4. Final Report
5. Interpretability Summary
6. Workflow Trace
7. Reproducibility Summary
8. Artifact Manifest
9. Download Links
10. Full JSON
```

---

### 18.5 Final Output Summary Card

展示：

* final output id；
* status；
* final model；
* final trial；
* primary metric；
* ready for delivery；
* report profile；
* generated time。

---

### 18.6 Final Model Summary Card

展示：

* final model id；
* model family；
* final trial；
* final hyperparameters；
* model artifact path；
* selection reason summary。

---

### 18.7 Final Metric Summary Card

展示：

* primary metric；
* primary metric value；
* metric direction；
* secondary metrics；
* baseline improvement；
* stability summary。

---

### 18.8 Final Report Viewer

展示 Markdown 报告内容。

建议支持：

* 折叠章节；
* 复制报告；
* 查看 JSON 报告；
* 显示 LLM report fallback 状态。

---

### 18.9 Workflow Trace Card

展示：

* 每个模块 ID；
* 每个模块状态；
* 关键输出；
* 迭代次数；
* 是否经过 workflow refinement；
* 最终路径。

---

### 18.10 Reproducibility Summary Card

展示：

* dataset source；
* target column；
* feature count；
* preprocessing artifact；
* model-ready matrix；
* final model；
* validation strategy；
* HPO summary；
* random state；
* environment summary。

---

### 18.11 Artifact Manifest Card

展示：

* final report；
* model artifact；
* prediction artifacts；
* interpretability artifacts；
* workflow trace；
* reproducibility summary；
* package root dir。

---

### 18.12 Download Links Card

展示：

* JSON report；
* Markdown report；
* manifest；
* final output package；
* model artifact reference；
* prediction artifact reference。

---

## 19. 前端状态与交互

### 19.1 按钮启用规则

| 条件                               | Generate Final Output        |
| -------------------------------- | ---------------------------- |
| 无 task_id                        | disabled                     |
| 无 InterpretabilityAnalysis       | disabled                     |
| InterpretabilityAnalysis 未 ready | disabled                     |
| 正在 generating                    | loading                      |
| 已 generated 且 force_rerun=false  | 显示 Load Latest / Re-generate |
| 上游 ready_for_final_output=true   | enabled                      |

---

### 19.2 状态颜色建议

| 状态                        | 颜色     |
| ------------------------- | ------ |
| `generating`              | blue   |
| `generated`               | green  |
| `generated_with_warning`  | orange |
| `failed`                  | red    |
| `ready_for_delivery=true` | green  |
| `llm fallback used`       | orange |

---

## 20. 安全设计

### 20.1 绝对禁止

本模块禁止：

1. 训练模型；
2. 调用 `model.fit()`；
3. 调用 `model.predict()`；
4. 重新计算指标；
5. 重新选择模型；
6. 重新解释模型；
7. 修改模型 artifact；
8. 修改 prediction artifact；
9. 修改 SHAP / importance 数值；
10. 执行 LLM 输出；
11. 接受用户自定义代码；
12. 让 LLM 修改事实数据。

---

### 20.2 路径安全

所有路径必须：

* 来自上游 artifact manifest；
* 位于允许 artifact 目录；
* 不包含 `..`；
* 文件存在；
* 文件类型符合预期；
* 不被 Final Output 覆盖。

输出路径必须位于：

```text
/app/artifacts/final_output/{final_output_id}/
```

---

### 20.3 LLM 安全

LLM 只能生成报告文本。

不得输出：

* executable code；
* modified metrics；
* modified model information；
* modified artifact paths；
* unsupported causal claims；
* fabricated results；
* fabricated artifacts。

---

## 21. 异常设计

建议新增异常：

| 异常类                                         | error_code                                             | 场景                    |
| ------------------------------------------- | ------------------------------------------------------ | --------------------- |
| `FinalOutputNotFoundException`              | `FINAL_OUTPUT_NOT_FOUND`                               | 找不到最终输出               |
| `InterpretabilityAnalysisRequiredException` | `INTERPRETABILITY_ANALYSIS_REQUIRED`                   | 缺少上游解释分析              |
| `InterpretabilityAnalysisNotReadyException` | `INTERPRETABILITY_ANALYSIS_NOT_READY_FOR_FINAL_OUTPUT` | 上游未 ready             |
| `FinalOutputInputInvalidException`          | `FINAL_OUTPUT_INPUT_INVALID`                           | final_output_input 无效 |
| `WorkflowTraceCollectException`             | `WORKFLOW_TRACE_COLLECT_FAILED`                        | trace 收集失败            |
| `FinalArtifactResolveException`             | `FINAL_ARTIFACT_RESOLVE_FAILED`                        | artifact 校验失败         |
| `ReproducibilitySummaryBuildException`      | `REPRODUCIBILITY_SUMMARY_BUILD_FAILED`                 | 复现摘要构建失败              |
| `LLMReportWriterException`                  | `LLM_REPORT_WRITER_FAILED`                             | LLM 报告生成失败            |
| `LLMReportValidationException`              | `LLM_REPORT_VALIDATION_FAILED`                         | LLM 报告校验失败            |
| `ReportRenderException`                     | `FINAL_REPORT_RENDER_FAILED`                           | 报告渲染失败                |
| `OutputPackageBuildException`               | `OUTPUT_PACKAGE_BUILD_FAILED`                          | 输出包构建失败               |
| `FinalOutputArtifactSaveException`          | `FINAL_OUTPUT_ARTIFACT_SAVE_FAILED`                    | artifact 保存失败         |

---

## 22. MVP 验收标准

### 22.1 后端验收标准

必须满足：

1. 可以通过 API 创建 Final Output；
2. 必须校验 `InterpretabilityAnalysis.ready_for_final_output = true`；
3. 必须消费 `final_output_input_json`；
4. 能收集 workflow trace；
5. 能校验最终模型 artifact；
6. 能校验预测 artifact；
7. 能校验解释性 artifact；
8. 能生成 final artifact manifest；
9. 能生成 reproducibility summary；
10. 能生成 final output summary；
11. MVP 阶段必须调用 LLM Report Writer；
12. LLM 必须生成最终报告文本；
13. LLM 不得修改系统事实数据；
14. LLM 失败时必须使用 fallback report；
15. 能输出 final_report.json；
16. 能输出 final_report.md；
17. 能生成 output_package_manifest；
18. 能持久化完整结果；
19. 不重新训练模型；
20. 不重新计算指标；
21. 不执行任意代码。

---

### 22.2 前端验收标准

必须满足：

1. 新增 Final Output 面板；
2. 可以点击 Generate Final Output；
3. 可以点击 Re-generate；
4. 可以展示 final output summary；
5. 可以展示 final model summary；
6. 可以展示 final metric summary；
7. 可以展示 final report；
8. 可以展示 workflow trace；
9. 可以展示 reproducibility summary；
10. 可以展示 artifact manifest；
11. 可以展示 download links；
12. 可以查看完整 JSON。

---

### 22.3 安全验收标准

必须满足：

1. 不允许重新训练；
2. 不允许重新预测；
3. 不允许重新计算指标；
4. 不允许修改 artifact；
5. 不允许 LLM 修改事实数据；
6. 不允许 LLM 输出可执行代码；
7. 所有路径必须经过安全校验；
8. 报告必须区分模型解释与因果结论。

---

## 23. 推荐实现优先级

### P0：必须完成

1. 后端 `final_output` 模块；
2. `FinalOutput` 数据表；
3. `context_builder`；
4. `final_output_input_loader`；
5. `workflow_trace_collector`；
6. `final_artifact_resolver`；
7. `reproducibility_summary_builder`；
8. `final_summary_builder`；
9. `llm_report_writer`；
10. `llm_report_parser / validator / normalizer`；
11. `report_renderer`；
12. `output_package_builder`；
13. 核心 API；
14. 前端 FinalOutputPanel；
15. Final Report Viewer；
16. Workflow Trace 展示；
17. Artifact Manifest 展示；
18. Download Links 展示。

---

### P1：建议完成

1. Markdown 报告章节折叠；
2. 报告复制功能；
3. final output package zip；
4. LLM fallback report 展示；
5. 更详细的 environment summary；
6. workflow trace 可视化。

---

### P2：后续迭代

1. PDF 报告导出；
2. DOCX 报告导出；
3. Notebook 导出；
4. 一键下载完整 artifact package；
5. 面向论文的图表与图注导出；
6. 自动生成实验复现脚本配置；
7. 模型卡 Model Card；
8. 数据卡 Data Card。

---

## 24. 总结

**Final Output** 是 MLAgent 的最终交付模块。

它的核心价值是：

```text
把 MLAgent 全流程产生的模型、预测、指标、解释性结果和 workflow trace 汇总为可下载、可审查、可复现的最终交付结果。
```

本模块的最终形态是：

```text
系统汇总事实与 artifact；
LLM 生成最终报告文本。
```

也就是：

```text
System Output Builder:
    汇总 artifact
    构建 manifest
    构建 workflow trace
    构建 reproducibility summary
    生成 final output package

LLM Report Writer:
    总结任务目标
    总结模型与指标
    总结解释性结果
    说明限制和风险
    生成自然语言最终报告
```

本模块必须坚持：

```text
只汇总，不训练；
只报告，不篡改；
系统事实是权威；
LLM 报告是表达层；
最终输出必须可追溯、可复现、可交付。
```

完成该模块后，MLAgent 将形成完整的端到端闭环：

```text
任务输入 → 自动建模 → 自动评估 → 自动诊断 → 工作流精炼 → 最终选择 → 解释性分析 → 最终交付
```
