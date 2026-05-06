# PRD：LLM-driven Workflow Refinement 模块

> 项目名称：MLAgent — AI-driven AutoML for Materials Science
> 模块编号：13
> 模块名称：LLM-driven Workflow Refinement
> 中文名称：LLM 驱动的迭代决策与工作流精炼
> 上游模块：LLM-based Result Diagnosis
> 下游模块：Final Pipeline Selection，或回到 Workflow Planning / Model Search 等前序模块开启下一轮迭代
> 文档用途：指导后端开发、前端开发与 AI Coding 工具实现本模块
> 版本：MVP v1.0
> 输出格式：Markdown

---

## 1. 背景与上下文

当前 MLAgent 已完成十二个核心业务模块，系统已经能够自动完成从任务输入、任务理解、数据集画像、工作流规划、特征工程、特征预处理、模型搜索、Pipeline 生成、训练执行、指标评估到 LLM 结果诊断的完整链路。附件中明确说明，当前系统最新完成到 **模块十二：LLM-based Result Diagnosis**，尚未实现的后续模块包括 Closed-loop Refinement、Final Pipeline Selection、Interpretability Analysis、Final Output 等。

模块十二已经能够消费 Metric Evaluation 输出的 `result_diagnosis_input_json`，结合评估结果、模型排名、baseline 对比、fold 稳定性、数据画像、特征工程和 pipeline 记录，生成结构化诊断结果，并输出 `closed_loop_refinement_input_json` 作为下一阶段输入。附件中也明确指出，Result Diagnosis 已实现 LLM 诊断、系统规则 fallback、证据驱动诊断、以及 `ClosedLoopRefinementInput` 构建能力。

但是，本模块的定位需要进一步明确：它不是简单生成一些 refinement proposal，而是一个 **LLM 决策型闭环模块**。

本模块的核心任务是：

> 让 LLM 深度阅读上游结果诊断、指标评估、实验日志、pipeline 记录和历史实验结果，然后做出明确决策：当前实验是否可以进入 Final Pipeline Selection，还是需要回到前序模块进行迭代优化。若选择迭代优化，LLM 必须生成新的 `WorkflowPlanResponse`，并说明修改原因、修改范围、保留内容和建议重新进入的模块。

---

## 2. 模块定位

### 2.1 一句话定义

**LLM-driven Workflow Refinement 是 MLAgent 中负责闭环决策与工作流重规划的模块。它由 LLM 基于诊断结果和历史实验表现，判断当前任务应进入最终 Pipeline 选择，还是生成新的 WorkflowPlanResponse 并回到前序模块开启下一轮迭代。**

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
LLM-driven Workflow Refinement   ← 当前模块
  ├── proceed_next_stage
  │       ↓
  │   Final Pipeline Selection
  │
  └── iterate_refinement
          ↓
      Revised WorkflowPlanResponse
          ↓
      回到 Workflow Planning / Feature Engineering / Model Search 等前序模块
```

---

## 4. 模块核心职责

本模块需要完成三件事：

### 4.1 做决策

LLM 必须输出明确决策：

```text
proceed_next_stage
```

或：

```text
iterate_refinement
```

即：

* 如果当前实验结果足够好，进入 **Final Pipeline Selection**；
* 如果当前结果仍存在明显问题，生成新的 Workflow Plan 并进入下一轮迭代。

---

### 4.2 给理由

LLM 必须给出详细决策理由，理由需要基于证据：

* best model 表现；
* baseline improvement；
* fold stability；
* trial variance；
* failed trials；
* Result Diagnosis findings；
* root cause hypotheses；
* feature quality；
* model search coverage；
* HPO budget；
* validation strategy；
* historical experiment trend。

不能只输出简单结论，例如“建议继续优化”。

---

### 4.3 如果迭代，生成新的 WorkflowPlanResponse

如果 LLM 决定迭代，必须输出一个新的：

```text
Revised WorkflowPlanResponse
```

它应与模块四 Workflow Planning 的输出结构兼容，并明确：

* 哪些策略被修改；
* 哪些策略保持不变；
* 修改原因；
* 修改对应的诊断问题；
* 推荐从哪个前序模块重新进入；
* 后续哪些 artifact 可以复用；
* 哪些 artifact 应该重新生成。

---

## 5. 与原 Closed-loop Refinement 的区别

原来的 Closed-loop Refinement 更像：

```text
系统根据诊断结果生成一些 refinement actions
```

现在的 **LLM-driven Workflow Refinement** 应该是：

```text
LLM 阅读完整诊断上下文
→ 做出 proceed 或 iterate 的决策
→ 给出详细理由
→ 若 iterate，则生成新的 WorkflowPlanResponse
→ 指定 rerun entry point
```

因此，本模块的核心产物不是普通的 `RefinementAction`，而是：

```text
WorkflowRefinementDecision
RevisedWorkflowPlanResponse
IterationRerunPlan
FinalPipelineSelectionInput
```

---

## 6. 核心设计原则

### 6.1 LLM 深度参与决策

本模块允许 LLM 深度参与：

* 是否继续迭代；
* 是否进入 Final Pipeline Selection；
* 为什么继续或停止；
* 如果迭代，如何调整 workflow；
* 下一轮从哪个模块重新进入；
* 哪些已有 artifact 可以复用；
* 哪些模块必须重跑。

这是本模块与之前 advisory-only 模块的最大区别。

---

### 6.2 LLM 可以生成 WorkflowPlanResponse，但不能生成可执行代码

LLM 可以输出新的结构化 `WorkflowPlanResponse`。

但仍然禁止：

* Python 代码；
* sklearn 代码；
* model.fit；
* Pipeline 代码；
* shell command；
* SQL；
* 动态 import；
* 修改 Registry；
* 直接触发训练；
* 直接修改数据库；
* 直接修改系统运行逻辑。

---

### 6.3 Revised WorkflowPlanResponse 必须经过系统校验

LLM 生成的新 Workflow Plan 不能直接进入执行链路。

它必须经过：

```text
Parser
  ↓
Validator
  ↓
Normalizer
  ↓
WorkflowPlan-compatible Schema Check
  ↓
Featurizer Registry Check
  ↓
Model Registry / HPO Registry Check
  ↓
Safety Check
```

只有通过系统校验后，才能作为下一轮迭代的输入。

---

### 6.4 默认逻辑入口回到 Workflow Planning

因为本模块的核心产物是新的 `WorkflowPlanResponse`，因此逻辑上应回到：

```text
模块四：LLM-guided Workflow Planning
```

但为了避免不必要的重复计算，LLM 需要同时输出：

```text
recommended_rerun_from_stage
```

用于指定实际重新进入的最小模块。

例如：

| 诊断问题          | 推荐重新进入模块                                    |
| ------------- | ------------------------------------------- |
| 特征不足、特征噪声、欠拟合 | `workflow_planning` 或 `feature_engineering` |
| 模型族不匹配        | `model_search_context` 或 `model_search`     |
| HPO 不足        | `model_search`                              |
| 验证不稳定         | `workflow_planning` 或 `model_search`        |
| 结果已足够好        | `final_pipeline_selection`                  |

---

### 6.5 不覆盖历史，只追加新版本

本模块生成的是新的 refinement 记录和 revised workflow plan，不覆盖旧数据。

需要保留：

* 原 WorkflowPlan；
* 原 FeatureEngineering；
* 原 PipelineExecution；
* 原 MetricEvaluation；
* 原 ResultDiagnosis；
* 当前 Workflow Refinement 决策记录。

---

## 7. 产品目标

### 7.1 MVP 目标

本模块 MVP 需要实现：

1. 读取最新或指定的 `ResultDiagnosis`；
2. 校验 `ready_for_closed_loop_refinement = true`；
3. 加载 `closed_loop_refinement_input_json`；
4. 汇总 Result Diagnosis 的完整诊断结果；
5. 汇总 Metric Evaluation 的模型排名和 baseline 对比；
6. 汇总 Pipeline Execution 的训练日志和失败 trial；
7. 汇总 Workflow Plan、Feature Engineering、Model Search Plan、Pipeline Generation 的关键记录；
8. 收集历史实验结果；
9. 构建 LLM workflow refinement prompt；
10. 调用 LLM 输出结构化决策；
11. 解析并校验 LLM 输出；
12. 如果决策为 `proceed_next_stage`，生成 `final_pipeline_selection_input`；
13. 如果决策为 `iterate_refinement`，生成新的 `Revised WorkflowPlanResponse`；
14. 输出 `recommended_rerun_from_stage`；
15. 输出详细决策理由；
16. 持久化完整 refinement 结果；
17. 前端展示决策、理由、新 Workflow Plan、策略差异、重跑入口和下游输入。

---

### 7.2 非目标

MVP 阶段不做：

1. 不直接重新运行 Workflow Planning；
2. 不直接重新运行 Feature Engineering；
3. 不直接重新训练模型；
4. 不直接执行 HPO；
5. 不直接计算新指标；
6. 不直接选择最终模型；
7. 不执行 SHAP；
8. 不生成最终报告；
9. 不让 LLM 输出可执行代码；
10. 不让 LLM 修改 Registry；
11. 不让 LLM 直接写数据库覆盖上游记录。

---

## 8. 输入设计

### 8.1 API 请求输入

接口：

```text
POST /api/workflow-refinements/{task_id}
```

请求字段：

| 字段                              | 类型      | 必填 | 说明                                                      |
| ------------------------------- | ------- | -: | ------------------------------------------------------- |
| `result_diagnosis_id`           | string  |  否 | 指定诊断记录；为空则使用最新 ready 诊断                                 |
| `force_rerun`                   | boolean |  否 | 是否强制重新生成 refinement                                     |
| `use_llm`                       | boolean |  否 | 是否调用 LLM，默认 true                                        |
| `max_iterations`                | integer |  否 | 最大迭代轮数，默认 3                                             |
| `current_iteration_index`       | integer |  否 | 当前迭代轮次，可由系统自动计算                                         |
| `decision_profile`              | string  |  否 | `conservative` / `balanced` / `exploratory`，默认 balanced |
| `allow_full_workflow_rerun`     | boolean |  否 | 是否允许从 Workflow Planning 重新开始，默认 true                    |
| `allow_partial_rerun`           | boolean |  否 | 是否允许从 Model Search 等中间模块重跑，默认 true                      |
| `minimum_improvement_threshold` | float   |  否 | 认为值得继续迭代的最小提升阈值                                         |
| `notes`                         | string  |  否 | 用户备注                                                    |

---

### 8.2 必需上游输入

| 来源                     | 必需字段                                                                                                                    |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `ResultDiagnosis`      | `id`, `task_id`, `status`, `ready_for_closed_loop_refinement`, `diagnosis_json`, `closed_loop_refinement_input_json`    |
| `MetricEvaluation`     | `evaluation_json`, `metric_summary_json`, `model_ranking_json`, `baseline_comparison`, `best_model_id`, `best_trial_id` |
| `PipelineExecution`    | `execution_json`, `runtime_log_json`, `trial_results`, `pipeline_run_results`                                           |
| `PipelineGeneration`   | `pipeline_json`, `execution_input_json`, `pipeline_specs`, `trial_plan`                                                 |
| `ModelSearchPlan`      | `plan_json`, `candidate_model_plan`, `hpo_plan`, `search_space_plan`, `validation_plan`, `evaluation_plan`              |
| `WorkflowPlan`         | `plan_json`, 原始 WorkflowPlanResponse                                                                                    |
| `FeatureEngineering`   | `feature_json`                                                                                                          |
| `FeaturePreprocessing` | `preprocessing_json`                                                                                                    |
| `DatasetProfile`       | `profile_json`                                                                                                          |
| `TaskSpecification`    | `task_spec_json`                                                                                                        |
| `TaskInterpretation`   | `interpretation_json`                                                                                                   |

---

### 8.3 历史实验输入

用于支持多轮迭代决策：

| 历史数据                   | 用途                  |
| ---------------------- | ------------------- |
| 历史 MetricEvaluation    | 判断指标是否持续改善          |
| 历史 ResultDiagnosis     | 判断同类问题是否反复出现        |
| 历史 Workflow Refinement | 避免重复生成相同方案          |
| 历史 PipelineExecution   | 判断训练失败率和 runtime 成本 |
| 历史 ModelSearchPlan     | 判断模型族是否已尝试          |
| 历史 WorkflowPlan        | 判断 workflow 演化轨迹    |

---

## 9. 输出设计

### 9.1 核心输出：WorkflowRefinementResponse

| 字段                                      | 类型          | 说明                                            |
| --------------------------------------- | ----------- | --------------------------------------------- |
| `workflow_refinement_id`                | string      | 记录 ID，例如 `wr_xxxxxxxx`                        |
| `task_id`                               | string      | 任务 ID                                         |
| `result_diagnosis_id`                   | string      | 上游诊断 ID                                       |
| `metric_evaluation_id`                  | string      | 上游评估 ID                                       |
| `iteration_index`                       | integer     | 当前迭代轮次                                        |
| `status`                                | string      | `decided` / `decided_with_warning` / `failed` |
| `decision`                              | string      | `proceed_next_stage` / `iterate_refinement`   |
| `decision_confidence_level`             | string      | low / medium / high                           |
| `decision_reasoning`                    | object      | 详细决策理由                                        |
| `evidence_used`                         | array       | 决策所用证据                                        |
| `recommended_rerun_from_stage`          | string/null | 若迭代，建议重跑入口                                    |
| `revised_workflow_plan`                 | object/null | 若迭代，新的 WorkflowPlanResponse                   |
| `workflow_plan_delta`                   | object/null | 新旧 workflow 差异                                |
| `iteration_rerun_plan`                  | object/null | 下一轮迭代重跑计划                                     |
| `final_pipeline_selection_input`        | object/null | 若进入下一阶段，下游输入                                  |
| `llm_workflow_refinement`               | object      | LLM 原始决策标准化结果                                 |
| `workflow_refinement_validation_result` | object      | 校验结果                                          |
| `artifact_manifest`                     | object      | 产物路径                                          |
| `ready_for_iteration`                   | boolean     | 是否可进入下一轮                                      |
| `ready_for_final_pipeline_selection`    | boolean     | 是否可进入最终选择                                     |
| `warnings`                              | array       | 警告                                            |
| `error_message`                         | string/null | 错误信息                                          |
| `created_at`                            | datetime    | 创建时间                                          |
| `updated_at`                            | datetime    | 更新时间                                          |

---

## 10. 核心数据结构设计

### 10.1 WorkflowRefinementDecision

```json
{
  "decision": "iterate_refinement",
  "decision_confidence_level": "high",
  "primary_reason": "The best candidate improves only weakly over baseline and fold stability is poor.",
  "should_generate_revised_workflow_plan": true,
  "recommended_rerun_from_stage": "workflow_planning",
  "should_proceed_to_final_selection": false
}
```

字段说明：

| 字段                                      | 类型      | 说明                                          |
| --------------------------------------- | ------- | ------------------------------------------- |
| `decision`                              | string  | `proceed_next_stage` / `iterate_refinement` |
| `decision_confidence_level`             | string  | low / medium / high                         |
| `primary_reason`                        | string  | 核心理由                                        |
| `should_generate_revised_workflow_plan` | boolean | 是否生成新版 workflow                             |
| `recommended_rerun_from_stage`          | string  | 建议重跑入口                                      |
| `should_proceed_to_final_selection`     | boolean | 是否进入 Final Pipeline Selection               |

---

### 10.2 DecisionReasoning

```json
{
  "performance_assessment": "Current best model is not sufficiently better than baseline.",
  "baseline_assessment": "Candidate improvement over baseline is weak.",
  "stability_assessment": "Fold-level variance suggests instability.",
  "diagnosis_assessment": "Result diagnosis points to feature insufficiency and HPO insufficiency.",
  "cost_assessment": "A moderate rerun is acceptable because current trial budget was limited.",
  "risk_assessment": "Rerunning from workflow planning may increase runtime but improves search coverage.",
  "final_reasoning_summary": "Iteration is recommended because the current result is not robust enough for final selection."
}
```

---

### 10.3 EvidenceUsed

| 字段                  | 类型     | 说明                                                                            |
| ------------------- | ------ | ----------------------------------------------------------------------------- |
| `evidence_id`       | string | 证据 ID                                                                         |
| `source_module`     | string | metric_evaluation / result_diagnosis / pipeline_execution / dataset_profile 等 |
| `evidence_type`     | string | metric / baseline / stability / diagnosis / runtime / feature                 |
| `source_field`      | string | 字段来源                                                                          |
| `value`             | any    | 证据值                                                                           |
| `interpretation`    | string | LLM 对证据的解释                                                                    |
| `supports_decision` | string | 支持 proceed 还是 iterate                                                         |

---

### 10.4 RevisedWorkflowPlanResponse

`revised_workflow_plan` 需要与模块四 `WorkflowPlanResponse` 的核心结构兼容。

建议结构：

```json
{
  "workflow_plan_id": "wr_generated_plan_placeholder",
  "status": "planned_by_refinement",
  "planning_mode": "llm_refinement",
  "task_summary": {},
  "data_strategy": {},
  "feature_strategy": {},
  "model_strategy": {},
  "validation_strategy": {},
  "evaluation_strategy": {},
  "hpo_strategy": {},
  "interpretability_strategy": {},
  "pipeline_generation_input": {},
  "planning_warnings": [],
  "planning_assumptions": [],
  "llm_reasoning_summary": "",
  "confidence_score": 0.85,
  "refinement_metadata": {
    "source_workflow_plan_id": "wp_xxxxxxxx",
    "source_result_diagnosis_id": "rd_xxxxxxxx",
    "changed_sections": [
      "feature_strategy",
      "model_strategy",
      "hpo_strategy"
    ],
    "preserved_sections": [
      "task_summary",
      "data_strategy",
      "evaluation_strategy"
    ],
    "recommended_rerun_from_stage": "workflow_planning"
  }
}
```

说明：

* `workflow_plan_id` 可以先使用占位 ID，不直接写入 WorkflowPlan 表；
* 真正进入下一轮时，系统可以基于该 revised plan 创建新 WorkflowPlan 记录；
* 所有字段必须经过 WorkflowPlan Validator 校验；
* `pipeline_generation_input` 可以作为参考，不作为直接执行输入。

---

### 10.5 WorkflowPlanDelta

用于展示新旧 workflow 差异。

| 字段                           | 类型     | 说明           |
| ---------------------------- | ------ | ------------ |
| `changed_sections`           | array  | 被修改的策略部分     |
| `preserved_sections`         | array  | 保持不变的策略部分    |
| `feature_strategy_delta`     | object | 特征策略变化       |
| `model_strategy_delta`       | object | 模型策略变化       |
| `hpo_strategy_delta`         | object | HPO 策略变化     |
| `validation_strategy_delta`  | object | 验证策略变化       |
| `evaluation_strategy_delta`  | object | 评价策略变化       |
| `change_reason_map`          | object | 每项变化对应的理由    |
| `diagnosis_to_change_map`    | object | 诊断问题到策略修改的映射 |
| `rejected_or_unsafe_changes` | array  | 被系统拒绝的变化     |

---

### 10.6 IterationRerunPlan

如果 decision = `iterate_refinement`，必须输出：

| 字段                                     | 类型      | 说明               |
| -------------------------------------- | ------- | ---------------- |
| `next_iteration_index`                 | integer | 下一轮编号            |
| `recommended_rerun_from_stage`         | string  | 推荐重跑入口           |
| `rerun_stages`                         | array   | 需要重跑的模块          |
| `reuse_artifacts`                      | array   | 可复用 artifact     |
| `invalidate_artifacts`                 | array   | 需要重新生成的 artifact |
| `expected_improvement_targets`         | array   | 下一轮希望改善的指标或问题    |
| `minimum_improvement_threshold`        | float   | 最小提升阈值           |
| `stop_after_next_iteration_if_no_gain` | boolean | 下一轮无收益是否停止       |
| `reasoning`                            | string  | 迭代路径理由           |

---

### 10.7 FinalPipelineSelectionInput

如果 decision = `proceed_next_stage`，必须输出：

| 字段                                   | 类型      | 说明                 |
| ------------------------------------ | ------- | ------------------ |
| `workflow_refinement_id`             | string  | 当前 refinement ID   |
| `task_id`                            | string  | 任务 ID              |
| `decision`                           | string  | proceed_next_stage |
| `candidate_metric_evaluation_ids`    | array   | 候选评估记录             |
| `candidate_pipeline_execution_ids`   | array   | 候选执行记录             |
| `best_metric_evaluation_id`          | string  | 当前最佳评估             |
| `current_best_model_id`              | string  | 当前最佳模型             |
| `current_best_trial_id`              | string  | 当前最佳 trial         |
| `current_best_pipeline_spec_id`      | string  | 当前最佳 pipeline      |
| `selection_policy`                   | object  | 最终选择策略             |
| `constraints`                        | object  | 最终选择约束             |
| `ready_for_final_pipeline_selection` | boolean | 是否可进入最终选择          |

---

## 11. recommended_rerun_from_stage 设计

### 11.1 允许值

```text
workflow_planning
feature_engineering
feature_preprocessing
model_search_context
model_search
pipeline_generation
pipeline_execution
metric_evaluation
final_pipeline_selection
```

---

### 11.2 推荐规则

| 问题类型                       | 默认 rerun entry                            |
| -------------------------- | ----------------------------------------- |
| feature_insufficiency      | workflow_planning                         |
| feature_noise              | workflow_planning 或 feature_preprocessing |
| underfitting               | workflow_planning                         |
| model_mismatch             | model_search_context                      |
| hpo_insufficient           | model_search                              |
| validation_instability     | workflow_planning                         |
| weak_baseline_improvement  | workflow_planning                         |
| limited_pipeline_gain      | workflow_planning 或 model_search          |
| pipeline execution failure | pipeline_generation 或 pipeline_execution  |
| metric calculation issue   | metric_evaluation                         |
| result good enough         | final_pipeline_selection                  |

---

## 12. 后端功能设计

### 12.1 推荐目录结构

建议新增：

```text
backend/app/modules/workflow_refinement/
    ├── __init__.py
    ├── api.py
    ├── service.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    ├── enums.py
    ├── exceptions.py
    ├── context_builder.py
    ├── refinement_input_loader.py
    ├── experiment_history_collector.py
    ├── workflow_refinement_context_builder.py
    ├── llm_prompt_builder.py
    ├── llm_workflow_refiner.py
    ├── llm_response_parser.py
    ├── workflow_refinement_validator.py
    ├── workflow_refinement_normalizer.py
    ├── revised_workflow_plan_validator.py
    ├── workflow_plan_delta_builder.py
    ├── iteration_rerun_plan_builder.py
    ├── final_selection_input_builder.py
    ├── refinement_artifact_manager.py
    └── builder.py
```

---

### 12.2 文件职责说明

| 文件                                       | 职责                                     |
| ---------------------------------------- | -------------------------------------- |
| `api.py`                                 | REST API                               |
| `service.py`                             | 主流程编排                                  |
| `model.py`                               | SQLModel 数据表                           |
| `repository.py`                          | CRUD 与 latest 查询                       |
| `schemas.py`                             | 请求、响应、内部 DTO                           |
| `enums.py`                               | 决策、状态、重跑入口等枚举                          |
| `exceptions.py`                          | 模块专用异常                                 |
| `context_builder.py`                     | 读取 ResultDiagnosis 并校验 ready           |
| `refinement_input_loader.py`             | 加载 `closed_loop_refinement_input_json` |
| `experiment_history_collector.py`        | 收集历史实验记录                               |
| `workflow_refinement_context_builder.py` | 构建 LLM refinement context              |
| `llm_prompt_builder.py`                  | 构建 LLM prompt                          |
| `llm_workflow_refiner.py`                | 调用 LLM                                 |
| `llm_response_parser.py`                 | 解析 LLM JSON                            |
| `workflow_refinement_validator.py`       | 校验 LLM 决策结果和安全内容                       |
| `workflow_refinement_normalizer.py`      | 标准化 LLM 输出                             |
| `revised_workflow_plan_validator.py`     | 校验 revised WorkflowPlanResponse        |
| `workflow_plan_delta_builder.py`         | 构建新旧 WorkflowPlan 差异                   |
| `iteration_rerun_plan_builder.py`        | 构建下一轮重跑计划                              |
| `final_selection_input_builder.py`       | 构建 Final Pipeline Selection 输入         |
| `refinement_artifact_manager.py`         | 保存 artifacts                           |
| `builder.py`                             | 构建响应                                   |

---

## 13. 后端主流程

### 13.1 主流程概览

```text
WorkflowRefinementService.create_workflow_refinement(task_id, request)
    ↓
1. build_workflow_refinement_context()
    ↓
2. load_closed_loop_refinement_input()
    ↓
3. collect_experiment_history()
    ↓
4. build_llm_workflow_refinement_context()
    ↓
5. build_llm_prompt()
    ↓
6. call_llm_workflow_refiner()
    ↓
7. parse_llm_response()
    ↓
8. validate_workflow_refinement_decision()
    ↓
9. normalize_workflow_refinement_result()
    ↓
10. validate_revised_workflow_plan_if_needed()
    ↓
11. build_workflow_plan_delta()
    ↓
12. build_iteration_rerun_plan_or_final_selection_input()
    ↓
13. save_artifacts()
    ↓
14. build_response()
    ↓
15. persist()
```

---

### 13.2 Step 1：构建上下文

`context_builder.py` 负责：

* 根据 `task_id` 找到最新 ResultDiagnosis；
* 或根据请求中的 `result_diagnosis_id` 找指定记录；
* 校验 ResultDiagnosis 状态：

  * `diagnosed`
  * `diagnosed_with_warning`
  * `fallback_diagnosed`
* 校验：

  * `ready_for_closed_loop_refinement = true`
* 读取：

  * `diagnosis_json`
  * `closed_loop_refinement_input_json`
  * `system_checks_json`
* 关联读取：

  * MetricEvaluation；
  * PipelineExecution；
  * PipelineGeneration；
  * ModelSearchPlan；
  * ModelSearchContext；
  * WorkflowPlan；
  * FeatureEngineering；
  * FeaturePreprocessing；
  * DatasetProfile；
  * TaskSpecification；
  * TaskInterpretation。

---

### 13.3 Step 2：加载 closed_loop_refinement_input

`refinement_input_loader.py` 校验：

* `should_refine`;
* `refinement_focus`;
* `priority_recommendations`;
* `constraints_to_preserve`;
* `avoid_actions`;
* `suggested_next_iteration_profile`;
* `ready_for_closed_loop_refinement`.

注意：

即使上游 `should_refine = true`，本模块 LLM 仍可以重新判断是否进入下一阶段，但必须给出理由。

---

### 13.4 Step 3：收集历史实验

`experiment_history_collector.py` 输出 `ExperimentHistorySummary`：

| 字段                         | 说明               |
| -------------------------- | ---------------- |
| `n_iterations_completed`   | 已完成轮次            |
| `best_metric_so_far`       | 历史最佳指标           |
| `best_model_so_far`        | 历史最佳模型           |
| `metric_trend`             | 指标趋势             |
| `previous_decisions`       | 历史 refinement 决策 |
| `repeated_diagnosis_types` | 反复出现的问题          |
| `tried_model_families`     | 已尝试模型族           |
| `tried_feature_strategies` | 已尝试特征策略          |
| `runtime_cost_summary`     | 运行成本摘要           |
| `failed_trial_summary`     | 失败 trial 摘要      |

---

### 13.5 Step 4：构建 LLM Workflow Refinement Context

上下文应包含：

1. task summary；
2. original WorkflowPlanResponse；
3. latest WorkflowPlanResponse；
4. feature engineering summary；
5. preprocessing summary；
6. model search plan summary；
7. pipeline generation summary；
8. pipeline execution summary；
9. metric evaluation summary；
10. result diagnosis full summary；
11. closed_loop_refinement_input；
12. historical experiment summary；
13. allowed rerun entry points；
14. allowed workflow plan fields；
15. forbidden actions；
16. user/system constraints。

---

## 14. LLM Prompt 设计

### 14.1 LLM 角色定义

Prompt 中必须明确：

```text
You are an LLM-driven workflow refinement decision maker for an AutoML system in materials science.

Your task is to decide whether the system should proceed to Final Pipeline Selection or iterate by generating a revised WorkflowPlanResponse.

You must base your decision on the provided diagnosis, metrics, pipeline logs, workflow records, and experiment history.

If you choose iteration, you must output a revised WorkflowPlanResponse and detailed reasons for each changed section.

You are not allowed to output executable code.
You are not allowed to directly train models.
You are not allowed to modify registries.
You are not allowed to create Python scripts.
You are not allowed to bypass system validators.
```

---

### 14.2 LLM 必须回答的问题

Prompt 应强制 LLM 回答：

1. 当前是否可以进入 Final Pipeline Selection？
2. 如果可以，为什么？
3. 如果不可以，主要阻碍是什么？
4. 是否需要生成 revised WorkflowPlanResponse？
5. 哪些 workflow sections 需要改变？
6. 哪些 workflow sections 应该保持不变？
7. 应该从哪个模块重新进入？
8. 哪些 artifact 可以复用？
9. 哪些 artifact 必须重新生成？
10. 下一轮期望解决什么问题？
11. 下一轮如果没有提升，是否应该停止？

---

### 14.3 LLM 输出 Schema

LLM 必须输出 JSON：

```json
{
  "workflow_refinement_decision": {
    "decision": "iterate_refinement",
    "decision_confidence_level": "high",
    "primary_reason": "The current best candidate does not improve sufficiently over baseline and the diagnosis indicates feature insufficiency.",
    "should_generate_revised_workflow_plan": true,
    "recommended_rerun_from_stage": "workflow_planning",
    "should_proceed_to_final_selection": false
  },
  "decision_reasoning": {
    "performance_assessment": "The best model has only weak improvement over baseline.",
    "baseline_assessment": "Candidate improvement is below the expected threshold.",
    "stability_assessment": "Fold-level variance indicates moderate instability.",
    "diagnosis_assessment": "The dominant diagnosis is feature_insufficiency with supporting evidence.",
    "cost_assessment": "A new iteration is acceptable because the current HPO budget was moderate.",
    "risk_assessment": "The main risk is increased feature dimensionality.",
    "final_reasoning_summary": "A new workflow iteration is recommended before final pipeline selection."
  },
  "evidence_used": [
    {
      "source_module": "metric_evaluation",
      "evidence_type": "baseline",
      "source_field": "baseline_comparison.relative_improvement_percentage",
      "value": 2.5,
      "interpretation": "The improvement over baseline is weak.",
      "supports_decision": "iterate_refinement"
    }
  ],
  "revised_workflow_plan": {
    "status": "planned_by_refinement",
    "planning_mode": "llm_refinement",
    "task_summary": {},
    "data_strategy": {},
    "feature_strategy": {},
    "model_strategy": {},
    "validation_strategy": {},
    "evaluation_strategy": {},
    "hpo_strategy": {},
    "interpretability_strategy": {},
    "pipeline_generation_input": {},
    "planning_warnings": [],
    "planning_assumptions": [],
    "llm_reasoning_summary": "",
    "confidence_score": 0.85,
    "refinement_metadata": {
      "changed_sections": ["feature_strategy", "model_strategy", "hpo_strategy"],
      "preserved_sections": ["task_summary", "data_strategy", "evaluation_strategy"],
      "recommended_rerun_from_stage": "workflow_planning"
    }
  },
  "iteration_rerun_plan": {
    "next_iteration_index": 1,
    "recommended_rerun_from_stage": "workflow_planning",
    "rerun_stages": [
      "workflow_planning",
      "feature_engineering",
      "feature_preprocessing",
      "model_search_context",
      "model_search",
      "pipeline_generation",
      "pipeline_execution",
      "metric_evaluation",
      "result_diagnosis"
    ],
    "reuse_artifacts": ["raw_dataset"],
    "invalidate_artifacts": [
      "feature_matrix",
      "model_ready_matrix",
      "model_search_plan",
      "pipeline_generation",
      "training_artifacts",
      "metric_evaluation"
    ],
    "expected_improvement_targets": [
      "increase baseline improvement",
      "reduce fold variance"
    ],
    "minimum_improvement_threshold": 0.03,
    "stop_after_next_iteration_if_no_gain": true,
    "reasoning": "Feature and model strategy changes require regeneration from workflow planning."
  },
  "final_pipeline_selection_input": null,
  "confidence_level": "high"
}
```

如果 decision = `proceed_next_stage`，则 `revised_workflow_plan = null`，并必须输出 `final_pipeline_selection_input`。

---

## 15. LLM 输出安全与校验

### 15.1 禁止字段

LLM 输出中禁止出现：

```text
code
python_code
script
shell_command
sql
workflow_patch
pipeline_patch
registry_patch
model_fit_code
train_code
executable
direct_execution
```

---

### 15.2 禁止内容扫描

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

发现后：

* 标记 LLM 输出不安全；
* 不采纳 revised workflow plan；
* 状态设为 `failed` 或 `decided_with_warning`；
* 不进入下一轮；
* 不进入 Final Pipeline Selection，除非系统 fallback 能明确判断可以 proceed。

---

### 15.3 Revised WorkflowPlanResponse 校验

`revised_workflow_plan_validator.py` 必须复用或对齐模块四 Workflow Planning 的 Validator 逻辑。

必须检查：

1. 顶层字段完整；
2. `task_summary` 合法；
3. `data_strategy` 合法；
4. `feature_strategy` 合法；
5. `model_strategy` 合法；
6. `validation_strategy` 合法；
7. `evaluation_strategy` 合法；
8. `hpo_strategy` 合法；
9. `interpretability_strategy` 合法；
10. `pipeline_generation_input` 合法；
11. feature strategy 中的 featurizer 必须能被 Featurizer Registry 解析；
12. model strategy 中的模型族必须能被 Model Registry 解析；
13. hpo strategy 中的方法必须能被 HPO Registry 解析；
14. 不包含可执行代码；
15. 不违反 `constraints_to_preserve`；
16. 不违反 `avoid_actions`。

---

## 16. 决策逻辑设计

### 16.1 proceed_next_stage 条件

LLM 可以选择进入 Final Pipeline Selection，如果满足：

* best candidate 明显优于 baseline；
* fold stability 可接受；
* 没有 high severity 诊断；
* 当前 best model 表现足够稳定；
* 继续迭代的预期收益较低；
* 已达到最大迭代轮数；
* 历史迭代收益趋于收敛。

---

### 16.2 iterate_refinement 条件

LLM 应选择迭代，如果存在：

* candidate 未明显超过 baseline；
* fold variance 高；
* feature insufficiency；
* model mismatch；
* HPO insufficient；
* validation instability；
* underfitting；
* overfitting risk；
* limited pipeline gain；
* 训练失败率高；
* 历史仍有未尝试的关键策略。

---

## 17. 数据库设计

### 17.1 新增表：WorkflowRefinement

表名建议：

```text
workflow_refinement
```

字段设计：

| 字段                                    | 类型       | 索引    | 说明                                      |
| ------------------------------------- | -------- | ----- | --------------------------------------- |
| `id`                                  | string   | PK    | `wr_{uuid8}`                            |
| `task_id`                             | string   | index | 任务 ID                                   |
| `result_diagnosis_id`                 | string   | index | 上游诊断 ID                                 |
| `metric_evaluation_id`                | string   | index | 上游评估 ID                                 |
| `pipeline_execution_id`               | string   | index | 上游执行 ID                                 |
| `source_workflow_plan_id`             | string   | index | 被精炼的 WorkflowPlan ID                    |
| `iteration_index`                     | integer  | index | 当前迭代轮次                                  |
| `status`                              | string   | index | decided / decided_with_warning / failed |
| `decision`                            | string   | index | proceed_next_stage / iterate_refinement |
| `recommended_rerun_from_stage`        | string   | index | 推荐重跑入口                                  |
| `ready_for_iteration`                 | boolean  | index | 是否可进入下一轮                                |
| `ready_for_final_pipeline_selection`  | boolean  | index | 是否可进入最终选择                               |
| `decision_confidence_level`           | string   |       | low / medium / high                     |
| `workflow_refinement_json`            | JSONB    |       | 完整结果                                    |
| `revised_workflow_plan_json`          | JSONB    |       | 新 WorkflowPlanResponse                  |
| `workflow_plan_delta_json`            | JSONB    |       | 新旧计划差异                                  |
| `iteration_rerun_plan_json`           | JSONB    |       | 下一轮重跑计划                                 |
| `final_pipeline_selection_input_json` | JSONB    |       | 下游输入                                    |
| `llm_request_json`                    | JSONB    |       | LLM 请求                                  |
| `llm_response_json`                   | JSONB    |       | LLM 原始响应                                |
| `validation_result_json`              | JSONB    |       | 校验结果                                    |
| `artifact_dir`                        | string   |       | artifact 目录                             |
| `error_message`                       | string   |       | 错误信息                                    |
| `created_at`                          | datetime | index | 创建时间                                    |
| `updated_at`                          | datetime |       | 更新时间                                    |

---

## 18. 状态设计

### 18.1 WorkflowRefinementStatus

| 状态                     | 说明       |
| ---------------------- | -------- |
| `deciding`             | 正在决策     |
| `decided`              | 成功完成决策   |
| `decided_with_warning` | 决策成功但有警告 |
| `failed`               | 决策失败     |

---

### 18.2 WorkflowRefinementDecision

| 决策                   | 说明                              |
| -------------------- | ------------------------------- |
| `proceed_next_stage` | 进入 Final Pipeline Selection     |
| `iterate_refinement` | 生成 revised Workflow Plan 并开启下一轮 |

---

## 19. Artifact 设计

### 19.1 Artifact 根目录

```text
/app/artifacts/workflow_refinement/{workflow_refinement_id}/
```

目录结构：

```text
workflow_refinement/{workflow_refinement_id}/
    ├── manifest.json
    ├── workflow_refinement_result.json
    ├── llm_refinement_context.json
    ├── llm_request.json
    ├── llm_response.json
    ├── revised_workflow_plan.json
    ├── workflow_plan_delta.json
    ├── iteration_rerun_plan.json
    ├── final_pipeline_selection_input.json
    └── validation_result.json
```

---

## 20. API 设计

### 20.1 创建 Workflow Refinement

```text
POST /api/workflow-refinements/{task_id}
```

---

### 20.2 获取指定 Workflow Refinement

```text
GET /api/workflow-refinements/{workflow_refinement_id}
```

---

### 20.3 获取任务最新 Workflow Refinement

```text
GET /api/tasks/{task_id}/workflow-refinement
```

---

### 20.4 重新运行 Workflow Refinement

```text
POST /api/workflow-refinements/{task_id}/rerun
```

---

### 20.5 获取 Revised Workflow Plan

```text
GET /api/workflow-refinements/{workflow_refinement_id}/revised-workflow-plan
```

---

### 20.6 获取 Iteration Rerun Plan

```text
GET /api/workflow-refinements/{workflow_refinement_id}/iteration-rerun-plan
```

---

### 20.7 获取 Final Pipeline Selection Input

```text
GET /api/workflow-refinements/{workflow_refinement_id}/final-pipeline-selection-input
```

---

## 21. 前端功能设计

### 21.1 新增前端文件结构

```text
frontend/src/api/workflowRefinementApi.ts

frontend/src/modules/workflowRefinement/
    ├── components/
    │   ├── WorkflowRefinementPanel.tsx
    │   ├── RefinementDecisionCard.tsx
    │   ├── DecisionReasoningCard.tsx
    │   ├── EvidenceUsedTable.tsx
    │   ├── RevisedWorkflowPlanCard.tsx
    │   ├── WorkflowPlanDeltaCard.tsx
    │   ├── IterationRerunPlanCard.tsx
    │   ├── FinalPipelineSelectionInputCard.tsx
    │   ├── WorkflowRefinementValidationCard.tsx
    │   └── WorkflowRefinementJsonViewer.tsx
    ├── types.ts
    └── constants.ts
```

---

### 21.2 页面集成位置

当前前端采用单页 `TaskSpecificationPage`，已包含 12 个嵌入式模块面板。附件说明当前前端模块以面板方式直接调用各自 API 并管理本地状态。

新增顺序：

```text
Metric Evaluation
LLM-based Result Diagnosis
LLM-driven Workflow Refinement   ← 新增
Final Pipeline Selection
Interpretability Analysis
Final Output
```

---

### 21.3 主面板功能

`WorkflowRefinementPanel` 应提供：

| 功能                         | 说明                        |
| -------------------------- | ------------------------- |
| Run Workflow Refinement    | 启动 LLM 迭代决策               |
| Re-run Refinement          | 重新生成决策                    |
| Load Latest                | 加载最新决策                    |
| View Decision              | 查看 proceed / iterate      |
| View Reasoning             | 查看详细理由                    |
| View Revised Workflow Plan | 查看新版 WorkflowPlanResponse |
| View Workflow Delta        | 查看新旧 workflow 差异          |
| View Rerun Plan            | 查看下一轮重跑入口                 |
| View Final Selection Input | 查看最终选择输入                  |
| View Full JSON             | 查看完整 JSON                 |

---

### 21.4 前端展示区域

#### 21.4.1 Refinement Decision Card

展示：

* decision；
* confidence；
* primary reason；
* recommended rerun stage；
* ready for iteration；
* ready for final selection。

---

#### 21.4.2 Decision Reasoning Card

展示：

* performance assessment；
* baseline assessment；
* stability assessment；
* diagnosis assessment；
* cost assessment；
* risk assessment；
* final reasoning summary。

---

#### 21.4.3 Evidence Used Table

表格字段：

| 列                 | 说明     |
| ----------------- | ------ |
| Source Module     | 来源模块   |
| Evidence Type     | 证据类型   |
| Source Field      | 字段     |
| Value             | 值      |
| Interpretation    | 解释     |
| Supports Decision | 支持哪个决策 |

---

#### 21.4.4 Revised Workflow Plan Card

当 decision = `iterate_refinement` 时展示：

* task summary；
* data strategy；
* feature strategy；
* model strategy；
* validation strategy；
* evaluation strategy；
* hpo strategy；
* interpretability strategy；
* planning warnings；
* reasoning summary。

---

#### 21.4.5 Workflow Plan Delta Card

展示：

* changed sections；
* preserved sections；
* feature strategy delta；
* model strategy delta；
* hpo strategy delta；
* validation strategy delta；
* diagnosis-to-change map；
* rejected changes。

---

#### 21.4.6 Iteration Rerun Plan Card

展示：

* next iteration index；
* recommended rerun from stage；
* rerun stages；
* reuse artifacts；
* invalidate artifacts；
* expected improvement targets；
* minimum improvement threshold；
* stop rule。

---

#### 21.4.7 Final Pipeline Selection Input Card

当 decision = `proceed_next_stage` 时展示：

* candidate metric evaluations；
* current best model；
* current best trial；
* current best pipeline spec；
* selection policy；
* constraints；
* ready for final selection。

---

## 22. 前端状态与交互

### 22.1 按钮启用规则

| 条件                                       | Run Workflow Refinement |
| ---------------------------------------- | ----------------------- |
| 无 task_id                                | disabled                |
| 无 ResultDiagnosis                        | disabled                |
| ResultDiagnosis 未 ready                  | disabled                |
| 正在 deciding                              | loading                 |
| 已 decided 且 force_rerun=false            | 显示 Load Latest / Re-run |
| 上游 ready_for_closed_loop_refinement=true | enabled                 |

---

### 22.2 状态颜色建议

| 状态 / 决策                    | 颜色     |
| -------------------------- | ------ |
| `deciding`                 | blue   |
| `decided`                  | green  |
| `decided_with_warning`     | orange |
| `failed`                   | red    |
| `proceed_next_stage`       | green  |
| `iterate_refinement`       | orange |
| `workflow_planning` rerun  | purple |
| `model_search` rerun       | blue   |
| `final_pipeline_selection` | green  |

---

## 23. 安全设计

### 23.1 绝对禁止

本模块禁止：

1. 执行训练；
2. 调用 Controlled Executor；
3. 调用 model.fit；
4. 调用 model.predict；
5. 写 Python 代码；
6. 写 shell command；
7. 修改 Registry；
8. 覆盖旧 WorkflowPlan；
9. 覆盖旧 PipelineExecution；
10. 直接执行下一轮模块；
11. 绕过 WorkflowPlan Validator；
12. 绕过 Featurizer / Model / HPO Registry。

---

### 23.2 允许行为

本模块允许：

1. 输出新的 revised workflow plan；
2. 输出重跑入口；
3. 输出重跑计划；
4. 输出进入 Final Pipeline Selection 的输入；
5. 输出详细决策理由；
6. 输出策略差异；
7. 输出 artifact 复用建议。

---

## 24. 异常设计

建议新增异常：

| 异常类                                        | error_code                                           | 场景                  |
| ------------------------------------------ | ---------------------------------------------------- | ------------------- |
| `WorkflowRefinementNotFoundException`      | `WORKFLOW_REFINEMENT_NOT_FOUND`                      | 找不到记录               |
| `ResultDiagnosisRequiredException`         | `RESULT_DIAGNOSIS_REQUIRED`                          | 缺少上游诊断              |
| `ResultDiagnosisNotReadyException`         | `RESULT_DIAGNOSIS_NOT_READY_FOR_WORKFLOW_REFINEMENT` | 上游未 ready           |
| `WorkflowRefinementInputInvalidException`  | `WORKFLOW_REFINEMENT_INPUT_INVALID`                  | 输入合同无效              |
| `WorkflowRefinementContextBuildException`  | `WORKFLOW_REFINEMENT_CONTEXT_BUILD_FAILED`           | 上下文构建失败             |
| `LLMWorkflowRefinementCallException`       | `LLM_WORKFLOW_REFINEMENT_CALL_FAILED`                | LLM 调用失败            |
| `LLMWorkflowRefinementParseException`      | `LLM_WORKFLOW_REFINEMENT_PARSE_FAILED`               | LLM 响应解析失败          |
| `LLMWorkflowRefinementValidationException` | `LLM_WORKFLOW_REFINEMENT_VALIDATION_FAILED`          | LLM 输出校验失败          |
| `RevisedWorkflowPlanValidationException`   | `REVISED_WORKFLOW_PLAN_VALIDATION_FAILED`            | 新 WorkflowPlan 校验失败 |
| `IterationRerunPlanBuildException`         | `ITERATION_RERUN_PLAN_BUILD_FAILED`                  | 重跑计划构建失败            |
| `FinalSelectionInputBuildException`        | `FINAL_SELECTION_INPUT_BUILD_FAILED`                 | 下游输入构建失败            |
| `WorkflowRefinementArtifactSaveException`  | `WORKFLOW_REFINEMENT_ARTIFACT_SAVE_FAILED`           | artifact 保存失败       |

---

## 25. MVP 验收标准

### 25.1 后端验收标准

必须满足：

1. 可以通过 API 启动 Workflow Refinement；
2. 必须校验 `ResultDiagnosis.ready_for_closed_loop_refinement = true`；
3. 必须读取 `closed_loop_refinement_input_json`；
4. 能汇总 Metric Evaluation、Pipeline Execution、Workflow Plan 等上下文；
5. 能构建 LLM refinement prompt；
6. LLM 必须输出 `decision`；
7. decision 只能是 `proceed_next_stage` 或 `iterate_refinement`；
8. 如果 decision = `iterate_refinement`，必须输出 `revised_workflow_plan`；
9. revised workflow plan 必须通过系统校验；
10. 必须输出 `recommended_rerun_from_stage`；
11. 必须输出详细 `decision_reasoning`；
12. 必须输出 `workflow_plan_delta`；
13. 必须输出 `iteration_rerun_plan` 或 `final_pipeline_selection_input`；
14. 必须持久化完整结果；
15. 不得执行训练；
16. 不得生成可执行代码；
17. 不得覆盖旧 WorkflowPlan；
18. LLM 输出必须经过 parser、validator、normalizer。

---

### 25.2 前端验收标准

必须满足：

1. 新增 Workflow Refinement 面板；
2. 可以点击 Run Workflow Refinement；
3. 可以点击 Re-run；
4. 可以展示 proceed / iterate 决策；
5. 可以展示详细决策理由；
6. 可以展示 evidence used；
7. 可以展示 revised WorkflowPlanResponse；
8. 可以展示 workflow plan delta；
9. 可以展示 rerun entry point；
10. 可以展示 iteration rerun plan；
11. 可以展示 final pipeline selection input；
12. 可以查看完整 JSON。

---

## 26. 推荐实现优先级

### P0：必须完成

1. 后端 `workflow_refinement` 模块；
2. `WorkflowRefinement` 数据表；
3. `context_builder`；
4. `refinement_input_loader`；
5. `workflow_refinement_context_builder`；
6. `llm_prompt_builder`；
7. `llm_workflow_refiner`；
8. `llm_response_parser`；
9. `workflow_refinement_validator`；
10. `workflow_refinement_normalizer`；
11. `revised_workflow_plan_validator`；
12. `workflow_plan_delta_builder`；
13. `iteration_rerun_plan_builder`；
14. `final_selection_input_builder`；
15. 核心 API；
16. 前端主面板；
17. 决策展示；
18. Revised Workflow Plan 展示。

---

### P1：建议完成

1. experiment history collector；
2. artifact manager；
3. 详细 workflow delta 展示；
4. 历史指标趋势展示；
5. 重跑入口可视化；
6. constraints conflict 展示。

---

### P2：后续迭代

1. 人工确认后自动触发下一轮；
2. 多轮自动闭环执行；
3. revised workflow plan 版本对比；
4. 多 objective refinement；
5. 跨任务经验迁移；
6. 材料领域知识增强 refinement。


---

## 27. 总结

**LLM-driven Workflow Refinement** 是 MLAgent 从“结果诊断”进入“闭环自我改进”的关键模块。

它的核心价值是：

```text
让 LLM 基于完整实验诊断上下文做出明确闭环决策：
要么进入 Final Pipeline Selection；
要么生成新的 WorkflowPlanResponse，并回到前序模块开启下一轮迭代。
```

本模块必须坚持：

```text
LLM 深度参与决策；
LLM 可以生成 revised WorkflowPlanResponse；
但 LLM 不能输出可执行代码；
不能直接训练；
不能覆盖历史；
不能绕过 Validator / Registry / Controlled Executor。
```

完成该模块后，MLAgent 将真正具备 **“诊断 → 决策 → 重规划 → 再迭代”** 的闭环 AutoML 能力。
