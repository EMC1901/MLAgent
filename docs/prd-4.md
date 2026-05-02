# PRD-4：LLM-guided Workflow Planning 模块需求文档

## 1. 模块名称

LLM-guided Workflow Planning  
基于大语言模型引导的机器学习工作流规划模块

---

## 2. 模块定位

本模块是 MLAgent 系统的第四个核心业务模块，位于：

```text
Task Specification
    ↓
LLM-based Task Interpretation
    ↓
Dataset Loading, Checking, and Profiling
    ↓
LLM-guided Workflow Planning
    ↓
Pipeline Generation
    ↓
Pipeline Execution
    ↓
Metric Evaluation
    ↓
Result Diagnosis
    ↓
Workflow Refinement
    ↓
Report Generation
````

当前系统已完成：

1. **Task Specification 模块**：负责用户任务输入、字段标准化、基础校验与 Task Specification Object 持久化；
2. **LLM-based Task Interpretation 模块**：负责理解任务语义，输出 `modeling_intent`、`dataset_intent`、`planning_hint` 等；
3. **Dataset Loading, Checking, and Profiling 模块**：负责数据加载、Schema 检查、模态检查、质量检查、目标变量画像，并输出 `workflow_planning_input`。

本模块的职责是基于前三个模块的输出，使用 LLM 生成一个结构化、可执行导向、但尚不包含具体代码的 **Workflow Plan Object**。

---

## 3. 模块目标

本模块的核心目标是：

1. 接收 `task_id`，读取该任务对应的 Task Specification、Task Interpretation 和 Dataset Profile；
2. 检查上游模块状态是否满足工作流规划条件；
3. 汇总任务语义、用户偏好、数据画像和数据质量问题；
4. 通过 LLM 规划端到端机器学习工作流策略；
5. 输出标准化 `Workflow Plan Object`；
6. 明确后续 Pipeline Generation 模块需要执行的步骤；
7. 规划但不执行，包括数据预处理策略、特征工程策略、模型候选集、验证策略、评估策略、解释性策略；
8. 持久化工作流规划结果，支持查询、重跑和版本追踪。

---

## 4. 系统边界

### 4.1 本模块负责的内容

本模块负责：

1. 读取 Task Specification Object；
2. 读取最新 Task Interpretation Object；
3. 读取最新 Dataset Profile Object；
4. 检查 Dataset Profile 是否可进入规划阶段；
5. 构建 Workflow Planning Context；
6. 调用 LLM 生成工作流规划；
7. 解析 LLM 返回的结构化 JSON；
8. 校验 Workflow Plan Schema；
9. 生成 Workflow Plan Object；
10. 持久化规划结果；
11. 向后续 Pipeline Generation 模块提供标准化规划结果。

---

### 4.2 本模块不负责的内容

本模块不负责：

1. 不负责收集用户输入；
2. 不负责重新解释用户任务；
3. 不负责加载真实数据；
4. 不负责执行数据清洗；
5. 不负责实际生成特征矩阵；
6. 不负责训练模型；
7. 不负责执行超参数搜索；
8. 不负责生成 Python Pipeline 代码；
9. 不负责计算模型评估指标；
10. 不负责诊断模型表现；
11. 不负责生成最终报告。

特别注意：

```text
本模块只回答“应该如何规划机器学习工作流”；
不回答“代码如何写、模型训练结果如何、性能好不好”。
```

---

## 5. 上游输入

## 5.1 输入来源一：Task Specification Object

本模块主要消费以下字段：

| 字段                | 说明                    |
| ----------------- | --------------------- |
| task_id           | 任务唯一 ID               |
| task_name         | 任务名称                  |
| task_description  | 用户原始任务描述              |
| material_system   | 材料体系                  |
| prediction_target | 原始预测目标                |
| task_type         | 用户选择的任务类型             |
| input_type        | 用户选择的输入类型             |
| target_column     | 目标列                   |
| evaluation_metric | 用户指定评价指标              |
| user_priority     | 用户偏好                  |
| constraints       | 用户约束                  |
| status            | Task Specification 状态 |

---

## 5.2 输入来源二：Task Interpretation Object

本模块主要消费以下字段：

| 字段                            | 说明            |
| ----------------------------- | ------------- |
| interpretation_id             | 任务理解结果 ID     |
| interpreted_task_type         | LLM 解释后的任务类型  |
| interpreted_input_modality    | LLM 解释后的输入模态  |
| interpreted_material_domain   | 材料领域          |
| interpreted_prediction_target | 标准化预测目标       |
| modeling_intent               | 建模意图          |
| planning_hint                 | 任务理解阶段给出的规划提示 |
| constraint_interpretation     | 用户约束解析        |
| recommended_defaults          | 推荐默认值         |
| ambiguities                   | 任务歧义          |
| warnings                      | 任务理解警告        |
| confidence_score              | 任务理解置信度       |

---

## 5.3 输入来源三：Dataset Profile Object

本模块主要消费以下字段：

| 字段                      | 说明       |
| ----------------------- | -------- |
| dataset_profile_id      | 数据画像 ID  |
| status                  | 数据画像状态   |
| dataset_source          | 数据来源     |
| dataset_schema          | 数据字段结构   |
| modality_check          | 输入模态检查结果 |
| target_profile          | 目标变量画像   |
| data_quality            | 数据质量检查结果 |
| profiling_summary       | 数据画像摘要   |
| workflow_planning_input | 后续规划输入   |

其中最重要的是：

```text
workflow_planning_input
```

示例：

```json
{
  "input_modality": "composition",
  "task_type": "regression",
  "target_column": "band_gap",
  "input_columns": ["composition"],
  "n_samples": 4604,
  "n_columns": 2,
  "n_features_raw": 1,
  "sample_size_level": "medium",
  "has_missing_values": false,
  "has_duplicates": false,
  "requires_cleaning": false,
  "requires_target_transformation_check": false,
  "quality_level": "good",
  "is_usable_for_ml": true
}
```

---

## 6. 前置条件

### 6.1 必须满足

进入本模块前必须满足：

1. `task_id` 存在；
2. Task Specification 状态为 `valid` 或 `valid_with_warning`；
3. Task Interpretation 已存在；
4. Task Interpretation 状态为 `interpreted` 或 `interpreted_with_warning`；
5. Dataset Profile 已存在；
6. Dataset Profile 状态为 `profiled` 或 `profiled_with_warning`；
7. `profiling_summary.is_usable_for_ml = true`；
8. `workflow_planning_input` 存在；
9. `target_column` 存在；
10. 至少存在一个输入列。

---

### 6.2 不允许进入本模块的情况

| 情况                         | 处理方式                                 |
| -------------------------- | ------------------------------------ |
| task_id 不存在                | 返回 `TASK_NOT_FOUND`                  |
| Task Specification 状态不合法   | 返回 `TASK_NOT_READY`                  |
| Task Interpretation 不存在    | 返回 `INTERPRETATION_REQUIRED`         |
| Task Interpretation 状态不合法  | 返回 `INTERPRETATION_NOT_READY`        |
| Dataset Profile 不存在        | 返回 `DATASET_PROFILE_REQUIRED`        |
| Dataset Profile 状态不合法      | 返回 `DATASET_PROFILE_NOT_READY`       |
| 数据不可用于机器学习                 | 返回 `DATASET_NOT_USABLE_FOR_ML`       |
| workflow_planning_input 缺失 | 返回 `WORKFLOW_PLANNING_INPUT_MISSING` |

---

## 7. 输出对象

### 7.1 输出对象名称

```text
Workflow Plan Object
```

### 7.2 输出对象示例

```json
{
  "workflow_plan_id": "plan_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "dataset_profile_id": "profile_xxxxxxxx",
  "status": "planned",
  "planning_mode": "llm_guided",
  "task_summary": {
    "task_type": "regression",
    "input_modality": "composition",
    "prediction_target": "band_gap",
    "material_domain": "inorganic crystals",
    "primary_goal": "property_prediction"
  },
  "data_strategy": {
    "input_columns": ["composition"],
    "target_column": "band_gap",
    "required_cleaning_steps": [],
    "target_handling": {
      "requires_transformation_check": false,
      "recommended_transformation": "none"
    },
    "duplicate_handling": "drop_duplicate_inputs_if_target_consistent",
    "missing_value_strategy": "no_missing_values_detected"
  },
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "recommended_featurizers": [
      "elemental_property_statistics",
      "stoichiometric_features"
    ],
    "requires_structure_features": false,
    "feature_selection_required": true,
    "feature_scaling_required": true
  },
  "model_strategy": {
    "candidate_model_families": [
      "random_forest",
      "gradient_boosting",
      "xgboost",
      "svr",
      "ridge"
    ],
    "baseline_models": [
      "dummy_regressor",
      "ridge"
    ],
    "preferred_model_bias": "balance_accuracy_and_interpretability",
    "excluded_model_families": []
  },
  "validation_strategy": {
    "split_strategy": "k_fold_cross_validation",
    "n_splits": 5,
    "test_size": null,
    "random_state": 42,
    "stratification_required": false
  },
  "evaluation_strategy": {
    "primary_metric": "MAE",
    "secondary_metrics": ["RMSE", "R2"],
    "metric_direction": "minimize"
  },
  "hpo_strategy": {
    "enabled": true,
    "search_method": "random_search",
    "budget_level": "medium",
    "max_trials": 30
  },
  "interpretability_strategy": {
    "enabled": true,
    "methods": ["feature_importance", "shap"],
    "priority": "high"
  },
  "pipeline_generation_input": {
    "pipeline_steps": [
      "load_dataset",
      "clean_data",
      "generate_composition_features",
      "split_data",
      "train_baselines",
      "train_candidate_models",
      "run_hpo",
      "evaluate_models",
      "save_best_model"
    ],
    "required_components": {
      "data_cleaner": true,
      "featurizer": true,
      "model_trainer": true,
      "evaluator": true
    }
  },
  "planning_warnings": [],
  "planning_assumptions": [
    "The composition column contains valid chemical formulas.",
    "MAE is suitable as the primary metric for band gap regression."
  ],
  "llm_reasoning_summary": "The dataset is a medium-sized composition-based regression task, so descriptor-based features and tree-based models are appropriate.",
  "confidence_score": 0.91,
  "created_at": "2026-05-01T10:00:00",
  "updated_at": "2026-05-01T10:00:00"
}
```

---

## 8. 核心功能需求

## 8.1 功能一：获取上游上下文

### 输入

```text
task_id
```

### 处理

1. 根据 task_id 查询 Task Specification；
2. 查询最新 Task Interpretation；
3. 查询最新 Dataset Profile；
4. 检查三个上游对象状态；
5. 合并为 Workflow Planning Context。

### 输出

```json
{
  "task_id": "task_xxxxxxxx",
  "task_specification": {},
  "task_interpretation": {},
  "dataset_profile": {},
  "workflow_planning_input": {}
}
```

---

## 8.2 功能二：构建 Workflow Planning Context

### 输入

```text
Task Specification Object
Task Interpretation Object
Dataset Profile Object
```

### 处理

从三个对象中抽取规划所需信息：

1. 任务类型；
2. 输入模态；
3. 预测目标；
4. 评价指标；
5. 用户偏好；
6. 用户约束；
7. 数据规模；
8. 数据质量；
9. 目标变量分布；
10. 输入列与目标列；
11. 是否需要清洗；
12. 是否需要目标变换检查；
13. 是否强调可解释性；
14. 是否存在歧义或警告。

### 输出

```json
{
  "task_context": {},
  "data_context": {},
  "user_preference_context": {},
  "planning_constraints": {}
}
```

---

## 8.3 功能三：构建 LLM Planning Prompt

### 输入

```text
Workflow Planning Context
```

### 处理

Prompt 需要明确告诉 LLM：

1. 当前模块只做 workflow planning；
2. 不生成代码；
3. 不执行训练；
4. 不虚构数据；
5. 必须基于 Dataset Profile 中的数据事实；
6. 必须输出严格 JSON；
7. 必须符合 Workflow Plan Schema；
8. 不确定的内容写入 `planning_assumptions`；
9. 风险与限制写入 `planning_warnings`。

### 输出

```text
system_prompt
user_message
```

---

## 8.4 功能四：LLM 生成 Workflow Plan

### 输入

```text
system_prompt
user_message
```

### 处理

调用 LLM，生成结构化 Workflow Plan。

LLM 需要规划：

1. 数据处理策略；
2. 特征工程策略；
3. 候选模型策略；
4. baseline 策略；
5. 验证策略；
6. 评价指标策略；
7. HPO 策略；
8. 可解释性策略；
9. Pipeline Generation 输入；
10. 规划假设；
11. 规划警告；
12. 置信度。

### 输出

```text
LLM raw response
```

---

## 8.5 功能五：解析 LLM 输出

### 输入

```text
LLM raw response
```

### 处理

1. 清理 Markdown 包裹；
2. 提取 JSON；
3. 解析为 dict；
4. 解析失败时可重试一次；
5. 多次失败则返回 `LLM_OUTPUT_PARSE_ERROR`。

### 输出

```text
Parsed Workflow Plan dict
```

---

## 8.6 功能六：校验 Workflow Plan Schema

### 输入

```text
Parsed Workflow Plan dict
```

### 处理

检查：

1. 必填顶层字段是否存在；
2. `task_summary` 是否完整；
3. `data_strategy` 是否完整；
4. `feature_strategy` 是否完整；
5. `model_strategy` 是否完整；
6. `validation_strategy` 是否完整；
7. `evaluation_strategy` 是否完整；
8. `hpo_strategy` 是否完整；
9. `interpretability_strategy` 是否完整；
10. `pipeline_generation_input` 是否完整；
11. `confidence_score` 是否在 0 到 1 之间；
12. 是否存在不允许的内容，例如完整代码、训练结果、虚构指标。

### 输出

```text
Validated Workflow Plan dict
```

---

## 8.7 功能七：数据策略规划

### 输入

```text
workflow_planning_input
data_quality
dataset_schema
target_profile
```

### 处理

规划内容包括：

1. 是否需要删除重复行；
2. 是否需要处理缺失值；
3. 是否需要删除全空列；
4. 是否需要处理异常目标值；
5. 是否需要目标变换检查；
6. 是否需要保留原始列；
7. 是否需要记录清洗日志。

### 输出

```json
{
  "data_strategy": {
    "required_cleaning_steps": [],
    "missing_value_strategy": "no_missing_values_detected",
    "duplicate_handling": "none",
    "target_handling": {
      "requires_transformation_check": false,
      "recommended_transformation": "none"
    }
  }
}
```

---

## 8.8 功能八：特征工程策略规划

### 输入

```text
input_modality
dataset_schema
material_domain
prediction_target
```

### 处理

根据输入模态规划特征策略。

### composition 输入

可规划：

1. composition descriptors；
2. elemental property statistics；
3. stoichiometric features；
4. optional Magpie-style descriptors；
5. feature scaling；
6. feature selection。

### structure 输入

可规划：

1. structure descriptors；
2. density/symmetry features；
3. local environment features；
4. graph-based representation；
5. 是否需要结构解析。

### descriptor 输入

可规划：

1. 使用现有数值描述符；
2. 缺失值处理；
3. 标准化；
4. 特征选择；
5. 多重共线性检查。

### 输出

```json
{
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "recommended_featurizers": [],
    "feature_selection_required": true,
    "feature_scaling_required": true
  }
}
```

---

## 8.9 功能九：模型策略规划

### 输入

```text
task_type
sample_size_level
input_modality
user_priority
constraints
```

### 处理

根据任务类型和数据规模规划候选模型族。

### regression

可规划：

1. Ridge / Lasso；
2. Random Forest Regressor；
3. Gradient Boosting；
4. XGBoost / LightGBM；
5. SVR；
6. Gaussian Process Regression；
7. MLP Regressor。

### classification

可规划：

1. Logistic Regression；
2. Random Forest Classifier；
3. Gradient Boosting；
4. XGBoost / LightGBM；
5. SVM；
6. MLP Classifier。

### ranking

可规划：

1. learning-to-rank 方法；
2. pairwise ranking；
3. score-based regression approximation。

### 输出

```json
{
  "model_strategy": {
    "candidate_model_families": [],
    "baseline_models": [],
    "preferred_model_bias": "accuracy_first",
    "excluded_model_families": []
  }
}
```

---

## 8.10 功能十：验证策略规划

### 输入

```text
n_samples
task_type
target_profile
sample_size_level
```

### 处理

规划：

1. train/test split；
2. k-fold cross validation；
3. stratified split；
4. repeated CV；
5. 是否需要固定 random_state；
6. 是否需要保持 Matbench benchmark split。

### 输出

```json
{
  "validation_strategy": {
    "split_strategy": "k_fold_cross_validation",
    "n_splits": 5,
    "test_size": null,
    "random_state": 42,
    "stratification_required": false
  }
}
```

---

## 8.11 功能十一：评估策略规划

### 输入

```text
task_type
evaluation_metric
recommended_defaults
target_profile
```

### 处理

规划：

1. primary metric；
2. secondary metrics；
3. metric direction；
4. 是否需要记录 benchmark-compatible metrics；
5. 是否需要训练集/验证集/测试集分开记录。

### 输出

```json
{
  "evaluation_strategy": {
    "primary_metric": "MAE",
    "secondary_metrics": ["RMSE", "R2"],
    "metric_direction": "minimize"
  }
}
```

---

## 8.12 功能十二：HPO 策略规划

### 输入

```text
sample_size_level
candidate_model_families
user_priority
constraints
```

### 处理

规划：

1. 是否启用 HPO；
2. 搜索方法；
3. 搜索预算；
4. max_trials；
5. 是否先跑 baseline 再 HPO；
6. 是否限制复杂模型搜索。

### 输出

```json
{
  "hpo_strategy": {
    "enabled": true,
    "search_method": "random_search",
    "budget_level": "medium",
    "max_trials": 30
  }
}
```

---

## 8.13 功能十三：可解释性策略规划

### 输入

```text
user_priority
constraint_interpretation
model_strategy
feature_strategy
```

### 处理

规划：

1. 是否启用解释性分析；
2. 使用 feature importance；
3. 使用 SHAP；
4. 使用 permutation importance；
5. 是否需要输出材料规律解释；
6. 是否限制模型族以提升解释性。

### 输出

```json
{
  "interpretability_strategy": {
    "enabled": true,
    "methods": ["feature_importance", "shap"],
    "priority": "high"
  }
}
```

---

## 8.14 功能十四：生成 Pipeline Generation 输入

### 输入

```text
data_strategy
feature_strategy
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
```

### 处理

生成后续 Pipeline Generation 模块可消费的结构化输入：

1. pipeline_steps；
2. required_components；
3. component_config_hints；
4. expected_artifacts；
5. execution_order。

### 输出

```json
{
  "pipeline_generation_input": {
    "pipeline_steps": [
      "load_dataset",
      "clean_data",
      "generate_features",
      "split_data",
      "train_baselines",
      "train_candidate_models",
      "run_hpo",
      "evaluate_models",
      "save_best_model"
    ],
    "required_components": {
      "data_cleaner": true,
      "featurizer": true,
      "model_trainer": true,
      "evaluator": true
    }
  }
}
```

---

## 9. 状态设计

### 9.1 状态枚举

| 状态                   | 含义             |
| -------------------- | -------------- |
| pending              | 已创建规划任务，但尚未执行  |
| planning             | 正在调用 LLM 生成规划  |
| planned              | 规划成功，且无明显警告    |
| planned_with_warning | 规划成功，但存在警告或假设  |
| failed               | LLM 调用、解析或校验失败 |
| blocked              | 上游状态不满足规划条件    |

---

### 9.2 状态流转

```text
收到 planning 请求
    ↓
检查 Task Specification
    ↓
检查 Task Interpretation
    ↓
检查 Dataset Profile
    ├── 不满足条件 → blocked
    └── 满足条件
            ↓
        pending
            ↓
        planning
            ↓
        planned / planned_with_warning / failed
```

---

## 10. API 需求

## 10.1 创建 Workflow Plan

```text
POST /api/workflow-plans/{task_id}
```

### 功能

根据 task_id 读取上游三个模块结果，调用 LLM 生成 Workflow Plan Object。

### 请求参数

| 参数      | 位置   | 必填 | 说明    |
| ------- | ---- | -- | ----- |
| task_id | path | 是  | 任务 ID |

### 请求体

MVP 阶段可为空。

后续可扩展：

```json
{
  "force_rerun": false,
  "planning_mode": "llm_guided",
  "llm_provider": "default",
  "model_name": "default"
}
```

### 响应

```json
{
  "success": true,
  "message": "Workflow plan created successfully.",
  "data": {
    "workflow_plan_id": "plan_xxxxxxxx",
    "task_id": "task_xxxxxxxx",
    "interpretation_id": "interp_xxxxxxxx",
    "dataset_profile_id": "profile_xxxxxxxx",
    "status": "planned",
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
    "confidence_score": 0.91
  }
}
```

---

## 10.2 查询 Workflow Plan

```text
GET /api/workflow-plans/{workflow_plan_id}
```

### 功能

根据 workflow_plan_id 查询完整 Workflow Plan Object。

---

## 10.3 查询某任务最新 Workflow Plan

```text
GET /api/tasks/{task_id}/workflow-plan
```

### 功能

返回某个 task_id 对应的最新一条 Workflow Plan Object。

---

## 10.4 重新执行 Workflow Planning

```text
POST /api/workflow-plans/{task_id}/rerun
```

### 功能

重新执行工作流规划。

### 处理原则

1. 不覆盖旧结果；
2. 新增一条 Workflow Plan 记录；
3. 默认查询最新一条；
4. 保留历史版本，便于追踪规划变化。

---

## 11. 数据库设计

## 11.1 表名

```text
workflow_plan
```

---

## 11.2 字段设计

| 字段                       | 类型          | 说明                        |
| ------------------------ | ----------- | ------------------------- |
| id                       | VARCHAR     | 主键，格式 `plan_xxxxxxxx`     |
| task_id                  | VARCHAR     | 关联 task_specification.id  |
| interpretation_id        | VARCHAR     | 关联 task_interpretation.id |
| dataset_profile_id       | VARCHAR     | 关联 dataset_profile.id     |
| status                   | VARCHAR     | 规划状态                      |
| planning_mode            | VARCHAR     | 规划模式，如 llm_guided         |
| task_type                | VARCHAR     | 任务类型                      |
| input_modality           | VARCHAR     | 输入模态                      |
| primary_metric           | VARCHAR     | 主评价指标                     |
| feature_type             | VARCHAR     | 推荐特征类型                    |
| validation_strategy      | VARCHAR     | 验证策略                      |
| hpo_enabled              | BOOLEAN     | 是否启用 HPO                  |
| interpretability_enabled | BOOLEAN     | 是否启用解释性分析                 |
| confidence_score         | FLOAT       | LLM 规划置信度                 |
| plan_json                | JSONB       | 完整 Workflow Plan Object   |
| llm_request_json         | JSONB       | LLM 请求记录                  |
| llm_response_json        | JSONB       | LLM 原始响应                  |
| error_message            | TEXT        | 错误信息                      |
| created_at               | TIMESTAMPTZ | 创建时间                      |
| updated_at               | TIMESTAMPTZ | 更新时间                      |

---

## 11.3 索引设计

| 索引                              | 说明           |
| ------------------------------- | ------------ |
| PRIMARY KEY(id)                 | 主键索引         |
| INDEX(task_id)                  | 根据任务查询规划     |
| INDEX(interpretation_id)        | 根据任务理解结果查询规划 |
| INDEX(dataset_profile_id)       | 根据数据画像查询规划   |
| INDEX(status)                   | 按状态筛选        |
| INDEX(created_at)               | 查询最新规划       |
| INDEX(task_id, created_at DESC) | 查询任务最新规划     |

---

## 11.4 存储原则

继续沿用当前系统的混合存储策略：

```text
高频查询字段单独建列
+
复杂嵌套对象存入 JSONB
```

高频字段包括：

1. task_id；
2. interpretation_id；
3. dataset_profile_id；
4. status；
5. task_type；
6. input_modality；
7. primary_metric；
8. feature_type；
9. validation_strategy；
10. hpo_enabled；
11. confidence_score。

---

## 12. 后端模块结构建议

新增模块目录：

```text
backend/app/modules/workflow_planning/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── prompt_builder.py
├── llm_client_adapter.py
├── parser.py
├── validator.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

## 12.1 文件职责

| 文件                    | 职责                                                                            |
| --------------------- | ----------------------------------------------------------------------------- |
| api.py                | 定义 Workflow Planning 相关 HTTP 接口                                               |
| schemas.py            | 定义请求、响应、内部 DTO                                                                |
| service.py            | 编排上游读取、Prompt 构建、LLM 调用、解析、校验、持久化流程                                           |
| model.py              | 定义 workflow_plan 数据库表                                                         |
| repository.py         | 提供 Workflow Plan CRUD                                                         |
| context_builder.py    | 读取 Task Specification、Task Interpretation、Dataset Profile，构建 Planning Context |
| prompt_builder.py     | 根据 Planning Context 构建 LLM Prompt                                             |
| llm_client_adapter.py | 复用或适配已有 task_interpretation.llm_client                                        |
| parser.py             | 解析 LLM 返回 JSON                                                                |
| validator.py          | 校验 Workflow Plan Schema                                                       |
| builder.py            | 构建 Workflow Plan Object                                                       |
| enums.py              | 定义状态、规划模式、策略枚举                                                                |
| exceptions.py         | 定义模块专用异常                                                                      |

---

## 13. 与已实现模块的衔接

## 13.1 与 Task Specification 模块的关系

本模块只读取 Task Specification，不修改。

主要消费：

```text
task_id
task_name
prediction_target
task_type
input_type
target_column
evaluation_metric
user_priority
constraints
status
```

---

## 13.2 与 Task Interpretation 模块的关系

本模块只读取 Task Interpretation，不修改。

主要消费：

```text
interpreted_task_type
interpreted_input_modality
interpreted_prediction_target
modeling_intent
planning_hint
constraint_interpretation
recommended_defaults
warnings
ambiguities
confidence_score
```

---

## 13.3 与 Dataset Profile 模块的关系

本模块只读取 Dataset Profile，不修改。

主要消费：

```text
dataset_schema
target_profile
data_quality
profiling_summary
workflow_planning_input
```

Dataset Profile 是本模块能否执行的关键前置条件。

---

## 13.4 与 Pipeline Generation 模块的关系

本模块输出：

```text
Workflow Plan Object
pipeline_generation_input
```

Pipeline Generation 模块后续应读取：

```text
GET /api/tasks/{task_id}/workflow-plan
```

并重点消费：

1. data_strategy；
2. feature_strategy；
3. model_strategy；
4. validation_strategy；
5. evaluation_strategy；
6. hpo_strategy；
7. interpretability_strategy；
8. pipeline_generation_input。

但本模块不生成具体代码。

---

## 14. 错误处理

### 14.1 错误码设计

| 错误码                             | 场景                         |
| ------------------------------- | -------------------------- |
| TASK_NOT_FOUND                  | task_id 不存在                |
| TASK_NOT_READY                  | Task Specification 状态不允许   |
| INTERPRETATION_REQUIRED         | 尚未执行任务理解                   |
| INTERPRETATION_NOT_READY        | Task Interpretation 状态不允许  |
| DATASET_PROFILE_REQUIRED        | 尚未执行数据画像                   |
| DATASET_PROFILE_NOT_READY       | Dataset Profile 状态不允许      |
| DATASET_NOT_USABLE_FOR_ML       | 数据不可用于机器学习                 |
| WORKFLOW_PLANNING_INPUT_MISSING | 缺少 workflow_planning_input |
| LLM_CALL_FAILED                 | LLM 调用失败                   |
| LLM_OUTPUT_PARSE_ERROR          | LLM 返回无法解析                 |
| WORKFLOW_PLAN_VALIDATION_FAILED | Workflow Plan Schema 校验失败  |
| WORKFLOW_PLAN_NOT_FOUND         | Workflow Plan 不存在          |

---

### 14.2 非阻断性 Warning

以下问题不一定阻断流程，但应进入 `planning_warnings`：

1. 样本量 very_small；
2. 数据质量为 fair 或 poor；
3. 任务理解存在 ambiguities；
4. 目标变量高度偏态；
5. 分类任务类别不平衡；
6. 用户同时要求高准确率和强解释性；
7. 用户约束限制了可选模型范围；
8. 输入模态与数据画像存在轻微不一致；
9. HPO 预算可能不足；
10. 推荐策略依赖后续 Pipeline Generation 的组件支持。

---

## 15. 前端需求

## 15.1 前端模块目录建议

```text
frontend/src/modules/workflowPlanning/
├── components/
│   ├── WorkflowPlanPanel.tsx
│   ├── WorkflowTaskSummaryCard.tsx
│   ├── DataStrategyCard.tsx
│   ├── FeatureStrategyCard.tsx
│   ├── ModelStrategyCard.tsx
│   ├── ValidationStrategyCard.tsx
│   ├── EvaluationStrategyCard.tsx
│   ├── HPOStrategyCard.tsx
│   ├── InterpretabilityStrategyCard.tsx
│   ├── PipelineGenerationInputCard.tsx
│   └── WorkflowPlanJsonViewer.tsx
├── types.ts
└── constants.ts
```

---

## 15.2 前端 API 客户端

新增：

```text
frontend/src/api/workflowPlanningApi.ts
```

封装接口：

```text
createWorkflowPlan(taskId)
getWorkflowPlan(planId)
getLatestWorkflowPlanByTaskId(taskId)
rerunWorkflowPlan(taskId)
```

---

## 15.3 前端展示内容

MVP 阶段展示：

1. Workflow Plan 状态；
2. 任务摘要；
3. 数据处理策略；
4. 特征工程策略；
5. 候选模型策略；
6. 验证策略；
7. 评价指标策略；
8. HPO 策略；
9. 可解释性策略；
10. Pipeline Generation 输入；
11. planning_warnings；
12. planning_assumptions；
13. confidence_score；
14. 完整 JSON。

---

## 16. MVP 验收标准

| 序号 | 验收标准                                         |
| -- | -------------------------------------------- |
| 1  | 能通过 task_id 获取 Task Specification            |
| 2  | 能通过 task_id 获取最新 Task Interpretation         |
| 3  | 能通过 task_id 获取最新 Dataset Profile             |
| 4  | 能拒绝上游状态不满足的任务                                |
| 5  | 能读取 workflow_planning_input                  |
| 6  | 能构建 Workflow Planning Context                |
| 7  | 能构建 LLM Planning Prompt                      |
| 8  | 能调用 LLM 生成 Workflow Plan                     |
| 9  | 能解析 LLM JSON 输出                              |
| 10 | 能校验 Workflow Plan Schema                     |
| 11 | 能输出 data_strategy                            |
| 12 | 能输出 feature_strategy                         |
| 13 | 能输出 model_strategy                           |
| 14 | 能输出 validation_strategy                      |
| 15 | 能输出 evaluation_strategy                      |
| 16 | 能输出 hpo_strategy                             |
| 17 | 能输出 interpretability_strategy                |
| 18 | 能输出 pipeline_generation_input                |
| 19 | 能输出 planning_warnings 和 planning_assumptions |
| 20 | 能持久化 Workflow Plan Object                    |
| 21 | 能查询某任务最新 Workflow Plan                       |
| 22 | 能重新执行规划且不覆盖旧结果                               |
| 23 | 不生成业务代码                                      |
| 24 | 不执行模型训练                                      |
| 25 | 不计算真实评估指标                                    |

---

## 17. 示例流程

### 17.1 输入

用户已经完成：

1. Task Specification；
2. Task Interpretation；
3. Dataset Profile。

Dataset Profile 中包含：

```json
{
  "workflow_planning_input": {
    "input_modality": "composition",
    "task_type": "regression",
    "target_column": "band_gap",
    "input_columns": ["composition"],
    "n_samples": 4604,
    "sample_size_level": "medium",
    "has_missing_values": false,
    "has_duplicates": false,
    "requires_cleaning": false,
    "quality_level": "good",
    "is_usable_for_ml": true
  }
}
```

---

### 17.2 处理流程

```text
POST /api/workflow-plans/task_xxxxxxxx
    ↓
读取 Task Specification
    ↓
读取最新 Task Interpretation
    ↓
读取最新 Dataset Profile
    ↓
检查上游状态
    ↓
构建 Workflow Planning Context
    ↓
构建 LLM Planning Prompt
    ↓
调用 LLM
    ↓
解析 Workflow Plan JSON
    ↓
校验 Workflow Plan Schema
    ↓
构建 Workflow Plan Object
    ↓
写入 workflow_plan 表
    ↓
返回前端展示
```

---

### 17.3 输出

```json
{
  "workflow_plan_id": "plan_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "status": "planned",
  "data_strategy": {
    "required_cleaning_steps": [],
    "missing_value_strategy": "no_missing_values_detected"
  },
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "recommended_featurizers": [
      "elemental_property_statistics",
      "stoichiometric_features"
    ],
    "feature_scaling_required": true
  },
  "model_strategy": {
    "candidate_model_families": [
      "random_forest",
      "gradient_boosting",
      "xgboost",
      "svr"
    ],
    "baseline_models": [
      "dummy_regressor",
      "ridge"
    ]
  },
  "validation_strategy": {
    "split_strategy": "k_fold_cross_validation",
    "n_splits": 5
  },
  "evaluation_strategy": {
    "primary_metric": "MAE",
    "secondary_metrics": ["RMSE", "R2"],
    "metric_direction": "minimize"
  },
  "hpo_strategy": {
    "enabled": true,
    "search_method": "random_search",
    "max_trials": 30
  },
  "interpretability_strategy": {
    "enabled": true,
    "methods": ["feature_importance", "shap"]
  },
  "pipeline_generation_input": {
    "pipeline_steps": [
      "load_dataset",
      "clean_data",
      "generate_composition_features",
      "split_data",
      "train_baselines",
      "train_candidate_models",
      "run_hpo",
      "evaluate_models"
    ]
  }
}
```

---

## 18. 后续迭代方向

MVP 后可以扩展：

1. 支持用户确认或编辑 Workflow Plan；
2. 支持多套候选 Workflow Plan；
3. 支持按 accuracy / interpretability / efficiency 生成不同规划；
4. 支持规则引擎与 LLM 混合规划；
5. 支持基于历史实验结果的规划优化；
6. 支持材料领域知识库增强规划；
7. 支持更细粒度的 HPO 搜索空间规划；
8. 支持自动判断是否需要 GNN / deep learning；
9. 支持 benchmark-compatible split 规划；
10. 支持将 Workflow Plan 编译为 Pipeline Generation DSL；
11. 支持 Agent Loop 中的动态重规划。

---

## 19. 总结

LLM-guided Workflow Planning 模块是连接“数据事实层”和“可执行 Pipeline 生成层”的规划中枢。

它的核心职责不是执行机器学习，也不是生成代码，而是基于：

```text
Task Specification Object
    +
Task Interpretation Object
    +
Dataset Profile Object
```

生成：

```text
Workflow Plan Object
    +
pipeline_generation_input
```

该模块最终应回答：

```text
这个材料机器学习任务应该如何组织建模流程？
需要哪些数据处理步骤？
应该采用什么特征策略？
应该考虑哪些模型族？
如何划分训练与验证？
使用哪些评价指标？
是否需要 HPO？
是否需要解释性分析？
后续 Pipeline Generation 应生成哪些步骤？
```

本模块输出的 Workflow Plan Object 将成为下一步 Pipeline Generation 模块的核心输入。

```
```
