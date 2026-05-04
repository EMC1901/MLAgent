# PRD：Automated Model and HPO Search 模块需求文档

## 1. 模块名称

Automated Model and HPO Search  
自动化模型与超参数搜索规划模块

---

## 2. 模块定位

本模块位于 **Model Search Context Update** 之后，**Executable Pipeline Generation** 之前。

系统流程为：

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
Result Diagnosis
    ↓
Report Generation
````

本模块的核心职责是：

```text
基于 Model Search Context 输出的最终建模上下文，
结合 Model Registry、HPO Registry 和 LLM 策略能力，
生成结构化、可校验、可执行器消费的 Model Search Plan。
```

本模块不训练模型，不执行 HPO，不生成可执行训练代码，而是生成下游 Pipeline Generation 可消费的模型搜索计划。

---

## 3. 背景说明

当前系统已完成从任务输入到模型搜索上下文更新的七个模块。

其中：

1. Feature Engineering 已生成 raw feature matrix artifact；
2. Feature Preprocessing 已完成特征清洗、缺失值填补、缩放、基础特征筛选，并输出 model-ready artifact 和 preprocessor artifact；
3. Model Search Context Update 已基于真实 model-ready dataset，对原 Workflow Plan 中的模型策略和 HPO 策略进行了上下文更新；
4. Model Registry 已定义系统支持的模型族；
5. HPO Registry 已定义系统支持的 HPO 方法。

因此，下一步需要一个独立模块，将：

```text
model_search_context_input
    ↓
Model Registry / HPO Registry
    ↓
LLM strategy suggestion
    ↓
system validation
    ↓
Model Search Plan
```

转换为标准化模型搜索计划，供后续 Executable Pipeline Generation 生成受控 Pipeline Spec。

---

## 4. 核心设计原则

### 4.1 LLM 必须深度参与

LLM 在本模块中应参与：

1. 理解当前任务类型；
2. 分析 model-ready dataset 的样本数、特征数和预处理状态；
3. 判断候选模型组合是否合理；
4. 建议不同模型族的优先级；
5. 建议 HPO 搜索预算；
6. 建议超参数搜索空间的宽窄；
7. 给出模型搜索策略解释。

---

### 4.2 LLM 不得返回可执行代码

LLM 不允许输出：

```text
Python 训练代码
model.fit 代码
Optuna study 执行代码
sklearn Pipeline 代码
Shell 命令
SQL 修改语句
动态 import 逻辑
任何可能修改系统运行逻辑的代码
```

LLM 只能输出结构化建议，例如：

```json
{
  "recommended_models": ["ridge", "random_forest", "xgboost"],
  "hpo_budget_level": "moderate",
  "search_space_profile": "balanced",
  "reasoning_summary": "The dataset has moderate samples and low final feature count."
}
```

最终 Model Search Plan 必须由系统根据 Registry、模板和校验器生成。

---

## 5. 模块目标

本模块目标是：

1. 读取最新 Model Search Context Object；
2. 校验 `ready_for_model_search_plan = true`；
3. 读取 `model_search_context_input`；
4. 根据 task_type、metric、样本数、特征数、预处理状态构建模型搜索上下文；
5. 调用 LLM 生成结构化模型搜索建议；
6. 使用 Model Registry 校验候选模型合法性；
7. 使用 HPO Registry 校验 HPO 方法合法性；
8. 使用系统模板生成每个模型的超参数搜索空间；
9. 生成统一的 Model Search Plan；
10. 持久化 Model Search Plan；
11. 输出 Pipeline Generation 可消费的 `pipeline_generation_input`；
12. 前端展示候选模型、搜索空间、预算和校验结果。

---

## 6. 系统边界

### 6.1 本模块负责

本模块负责：

1. 读取 Model Search Context；
2. 构建 LLM Model Search Prompt；
3. 调用 LLM 获取结构化模型搜索建议；
4. 校验 LLM 建议；
5. 从 Model Registry 中选择合法模型；
6. 从 HPO Registry 中选择合法搜索方法；
7. 生成候选模型列表；
8. 生成每个模型的超参数搜索空间；
9. 生成 HPO 预算；
10. 生成 trial allocation 计划；
11. 生成 baseline model 计划；
12. 生成 Model Search Plan Object；
13. 生成下游 Pipeline Generation 输入；
14. 持久化结果；
15. 前端展示和 rerun。

---

### 6.2 本模块不负责

本模块不负责：

1. 不重新执行 Workflow Planning；
2. 不重新执行 Feature Engineering；
3. 不重新执行 Feature Preprocessing；
4. 不重新生成 Model Search Context；
5. 不读取完整数据矩阵进行训练；
6. 不训练模型；
7. 不执行 HPO；
8. 不计算模型指标；
9. 不保存 trained model artifact；
10. 不生成 Python 训练脚本；
11. 不生成可执行 Pipeline 代码；
12. 不执行 Pipeline；
13. 不选择最终最佳模型。

特别注意：

```text
本模块负责“生成模型搜索计划”；
不负责“执行模型搜索过程”。
```

---

## 7. 上游输入

### 7.1 Model Search Context Object

本模块最关键输入。

重点消费：

| 字段                          | 说明                             |
| --------------------------- | ------------------------------ |
| context_id                  | Model Search Context ID        |
| task_id                     | 任务 ID                          |
| workflow_plan_id            | Workflow Plan ID               |
| feature_preprocessing_id    | Feature Preprocessing ID       |
| status                      | updated / updated_with_warning |
| dataset_effective_profile   | 样本数、最终特征数、特征削减比例               |
| feature_group_summary       | 保留/删除的 feature group           |
| preprocessing_summary       | 已执行预处理操作                       |
| updated_model_strategy      | 更新后的模型策略                       |
| updated_hpo_strategy        | 更新后的 HPO 策略                    |
| updated_validation_strategy | 更新后的验证策略                       |
| updated_evaluation_strategy | 更新后的评价策略                       |
| model_search_context_input  | 本模块直接消费的标准输入                   |

---

### 7.2 model_search_context_input

示例：

```json
{
  "model_ready_matrix_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/model_ready_features.parquet",
  "preprocessing_pipeline_artifact_id": "artifact_preprocessor_xxxxxxxx",
  "target_column": "band_gap",
  "feature_columns": [],
  "task_type": "regression",
  "primary_metric": "MAE",
  "model_strategy": {},
  "validation_strategy": {},
  "evaluation_strategy": {},
  "hpo_strategy": {},
  "ready_for_model_search_plan": true
}
```

---

### 7.3 Model Registry

本模块需要使用 Model Registry 获取：

1. 系统支持的模型族；
2. 每个模型支持的任务类型；
3. 是否需要 scaling；
4. 是否适合作为 baseline；
5. 训练成本；
6. 可解释性等级；
7. 默认超参数模板 ID；
8. 模型别名。

---

### 7.4 HPO Registry

本模块需要使用 HPO Registry 获取：

1. 系统支持的 HPO 方法；
2. 每种方法支持的任务类型；
3. 最小 trials；
4. 最大 trials；
5. 是否支持并行；
6. 预算级别；
7. 方法别名。

---

## 8. 前置条件

进入本模块前必须满足：

1. task_id 存在；
2. Model Search Context 已存在；
3. Model Search Context 状态为 `updated` 或 `updated_with_warning`；
4. `ready_for_model_search_plan = true`；
5. `model_ready_matrix_path` 存在；
6. `preprocessing_pipeline_artifact_id` 存在；
7. target_column 存在；
8. feature_columns 非空；
9. task_type 合法；
10. primary_metric 合法；
11. Model Registry 可用；
12. HPO Registry 可用。

---

## 9. 输出对象

### 9.1 输出对象名称

```text
Model Search Plan Object
```

数据库表建议命名：

```text
model_search_plan
```

---

### 9.2 输出对象示例

```json
{
  "model_search_plan_id": "msp_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "model_search_context_id": "msc_xxxxxxxx",
  "feature_preprocessing_id": "fmp_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "status": "planned",
  "planning_mode": "llm_guided_with_registry_validation",
  "dataset_context": {
    "model_ready_matrix_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/model_ready_features.parquet",
    "preprocessing_pipeline_artifact_id": "artifact_preprocessor_xxxxxxxx",
    "n_samples": 4604,
    "n_features": 14,
    "target_column": "band_gap",
    "task_type": "regression",
    "primary_metric": "MAE"
  },
  "candidate_model_plan": {
    "baseline_models": [
      {
        "model_id": "dummy_mean",
        "role": "baseline",
        "hpo_enabled": false
      },
      {
        "model_id": "ridge",
        "role": "strong_baseline",
        "hpo_enabled": true
      }
    ],
    "candidate_models": [
      {
        "model_id": "random_forest",
        "model_family": "tree_ensemble",
        "priority": "high",
        "hpo_enabled": true,
        "reason": "Robust on small-to-medium tabular datasets."
      },
      {
        "model_id": "gradient_boosting",
        "model_family": "boosting",
        "priority": "high",
        "hpo_enabled": true,
        "reason": "Strong nonlinear baseline for tabular regression."
      },
      {
        "model_id": "xgboost",
        "model_family": "boosting",
        "priority": "medium",
        "hpo_enabled": true,
        "reason": "High-performance model when dependency is available."
      }
    ],
    "excluded_models": [
      {
        "model_id": "knn",
        "reason": "Less preferred for current feature setting."
      }
    ]
  },
  "hpo_plan": {
    "enabled": true,
    "search_method": "random_search",
    "budget_level": "moderate",
    "max_total_trials": 30,
    "max_parallel_trials": 1,
    "trial_allocation": [
      {
        "model_id": "ridge",
        "max_trials": 5
      },
      {
        "model_id": "random_forest",
        "max_trials": 10
      },
      {
        "model_id": "gradient_boosting",
        "max_trials": 10
      },
      {
        "model_id": "xgboost",
        "max_trials": 5
      }
    ]
  },
  "search_space_plan": {
    "spaces": [
      {
        "model_id": "ridge",
        "search_space_id": "ridge_default_regression",
        "parameters": []
      },
      {
        "model_id": "random_forest",
        "search_space_id": "random_forest_default_regression",
        "parameters": []
      }
    ]
  },
  "validation_plan": {
    "split_strategy": "k_fold_cross_validation",
    "n_splits": 5,
    "random_state": 42,
    "shuffle": true
  },
  "evaluation_plan": {
    "primary_metric": "MAE",
    "metric_direction": "minimize",
    "secondary_metrics": ["RMSE", "R2"]
  },
  "llm_model_search_advice": {
    "used": true,
    "confidence_score": 0.87,
    "summary": "Prefer robust tabular regression models with moderate HPO budget."
  },
  "system_validation_result": {
    "is_valid": true,
    "rejected_models": [],
    "rejected_hpo_methods": [],
    "fallback_applied": false,
    "warnings": []
  },
  "pipeline_generation_input": {
    "model_ready_matrix_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/model_ready_features.parquet",
    "preprocessing_pipeline_artifact_id": "artifact_preprocessor_xxxxxxxx",
    "target_column": "band_gap",
    "feature_columns": [],
    "candidate_model_plan": {},
    "hpo_plan": {},
    "search_space_plan": {},
    "validation_plan": {},
    "evaluation_plan": {},
    "ready_for_pipeline_generation": true
  },
  "warnings": [],
  "errors": [],
  "created_at": "2026-05-04T10:00:00",
  "updated_at": "2026-05-04T10:00:00"
}
```

---

## 10. LLM 参与方式

### 10.1 LLM 输入

LLM 接收系统整理后的结构化上下文：

```json
{
  "task_type": "regression",
  "primary_metric": "MAE",
  "n_samples": 4604,
  "n_features": 14,
  "feature_group_summary": {},
  "preprocessing_summary": {},
  "updated_model_strategy": {},
  "updated_hpo_strategy": {},
  "allowed_model_families": [],
  "allowed_hpo_methods": []
}
```

LLM 不接收：

1. 原始数据矩阵；
2. 完整文件路径以外的敏感信息；
3. 系统内部执行代码；
4. 数据库连接信息；
5. 可执行模板内容。

---

### 10.2 LLM 输出

LLM 必须输出结构化 JSON 建议：

```json
{
  "recommended_model_ids": [
    "ridge",
    "random_forest",
    "gradient_boosting",
    "xgboost"
  ],
  "baseline_model_ids": [
    "dummy_mean",
    "linear_regression",
    "ridge"
  ],
  "excluded_model_ids": [
    {
      "model_id": "knn",
      "reason": "Less suitable for the current model-ready dataset."
    }
  ],
  "hpo_recommendation": {
    "enabled": true,
    "search_method": "random_search",
    "budget_level": "moderate",
    "max_total_trials": 30
  },
  "search_space_profile": {
    "space_width": "moderate",
    "prefer_conservative_ranges": true
  },
  "model_priority_notes": [
    {
      "model_id": "random_forest",
      "priority": "high",
      "reason": "Robust and stable for tabular materials descriptors."
    }
  ],
  "risk_notes": [],
  "confidence_score": 0.87
}
```

---

### 10.3 LLM 输出校验

系统必须校验：

1. JSON 是否可解析；
2. Schema 是否正确；
3. candidate model 是否存在于 Model Registry；
4. HPO method 是否存在于 HPO Registry；
5. max_total_trials 是否超过系统上限；
6. 模型是否支持当前 task_type；
7. 指标是否支持当前 task_type；
8. 是否包含可执行代码；
9. 是否包含未注册模型；
10. 是否包含系统无法支持的搜索方式。

---

## 11. 核心功能需求

### 11.1 功能一：获取上游上下文

#### 输入

```text
task_id
```

#### 处理

1. 查询最新 Model Search Context；
2. 校验状态；
3. 读取 `model_search_context_input`；
4. 读取 Model Registry；
5. 读取 HPO Registry；
6. 构建 Model Search Planning Context。

#### 输出

```json
{
  "task_id": "task_xxxxxxxx",
  "model_search_context_id": "msc_xxxxxxxx",
  "task_type": "regression",
  "primary_metric": "MAE",
  "model_ready_matrix_path": "...",
  "allowed_models": [],
  "allowed_hpo_methods": []
}
```

---

### 11.2 功能二：构建 LLM Model Search Prompt

#### 处理

Prompt 应包含：

1. system role；
2. 安全边界；
3. task context；
4. model-ready dataset summary；
5. preprocessing summary；
6. updated strategy from Model Search Context；
7. allowed model list；
8. allowed HPO method list；
9. required JSON schema；
10. 禁止输出代码说明。

---

### 11.3 功能三：LLM 生成模型搜索建议

LLM 生成：

1. 推荐候选模型；
2. baseline 模型；
3. 排除模型及原因；
4. HPO 方法；
5. HPO 预算；
6. 搜索空间宽窄建议；
7. 模型优先级；
8. 风险提示；
9. 置信度。

---

### 11.4 功能四：LLM 输出解析与校验

处理：

1. 去除 markdown 代码块；
2. 提取 JSON；
3. Pydantic Schema 校验；
4. Model Registry 校验；
5. HPO Registry 校验；
6. 安全内容校验；
7. 记录 rejected_suggestions。

---

### 11.5 功能五：生成候选模型计划

系统根据：

```text
Model Search Context
+
LLM advice
+
Model Registry
+
system rules
```

生成：

1. baseline_models；
2. candidate_models；
3. excluded_models；
4. model priority；
5. hpo_enabled 标记；
6. model role。

---

### 11.6 功能六：生成 HPO 计划

系统根据：

```text
updated_hpo_strategy
+
LLM advice
+
HPO Registry
+
dataset size
+
feature count
```

生成：

1. search_method；
2. budget_level；
3. max_total_trials；
4. max_parallel_trials；
5. trial_allocation；
6. early_stopping flag；
7. fallback method。

---

### 11.7 功能七：生成超参数搜索空间计划

系统不得让 LLM 直接提供任意参数空间。

系统应基于内置 search space templates 生成每个模型的参数空间：

```text
model_id
    ↓
search_space_template
    ↓
task_type adjustment
    ↓
budget adjustment
    ↓
final search space plan
```

输出：

1. search_space_id；
2. parameter names；
3. parameter type；
4. value range；
5. sampling distribution；
6. default value；
7. constraints。

注意：

```text
LLM 只能建议 search_space_profile；
最终参数空间必须由系统模板生成。
```

---

### 11.8 功能八：生成验证计划

从 Model Search Context 中继承并规范化：

1. split_strategy；
2. n_splits；
3. random_state；
4. shuffle；
5. stratification_required；
6. benchmark split 标记。

---

### 11.9 功能九：生成评价计划

从 Model Search Context 中继承并规范化：

1. primary_metric；
2. metric_direction；
3. secondary_metrics；
4. scorer_id；
5. metric compatibility。

---

### 11.10 功能十：生成 Pipeline Generation Input

输出给下游：

```json
{
  "model_ready_matrix_path": "...",
  "preprocessing_pipeline_artifact_id": "...",
  "target_column": "band_gap",
  "feature_columns": [],
  "candidate_model_plan": {},
  "hpo_plan": {},
  "search_space_plan": {},
  "validation_plan": {},
  "evaluation_plan": {},
  "ready_for_pipeline_generation": true
}
```

---

## 12. 状态设计

| 状态                   | 含义                        |
| -------------------- | ------------------------- |
| pending              | 已创建计划任务，尚未执行              |
| loading_context      | 正在读取 Model Search Context |
| llm_advising         | 正在调用 LLM 生成建议             |
| validating_advice    | 正在校验 LLM 建议               |
| generating_plan      | 正在生成 Model Search Plan    |
| planned              | 计划生成完成                    |
| planned_with_warning | 计划生成完成但有警告                |
| failed               | 计划生成失败                    |
| blocked              | 上游状态不满足                   |

---

## 13. API 需求

### 13.1 创建 Model Search Plan

```text
POST /api/model-search-plans/{task_id}
```

请求体：

```json
{
  "force_rerun": false,
  "use_llm_advisor": true,
  "max_total_trials_override": null,
  "preferred_search_method": null,
  "include_models": [],
  "exclude_models": []
}
```

---

### 13.2 查询 Model Search Plan

```text
GET /api/model-search-plans/{model_search_plan_id}
```

---

### 13.3 查询任务最新 Model Search Plan

```text
GET /api/tasks/{task_id}/model-search-plan
```

---

### 13.4 重新生成 Model Search Plan

```text
POST /api/model-search-plans/{task_id}/rerun
```

原则：

1. 不覆盖旧记录；
2. 生成新 plan；
3. 默认查询最新 plan。

---

### 13.5 查询 Plan Summary

```text
GET /api/model-search-plans/{model_search_plan_id}/summary
```

用于前端快速展示候选模型、HPO 预算、搜索空间数量。

---

## 14. 数据库设计

### 14.1 表名

```text
model_search_plan
```

---

### 14.2 字段设计

| 字段                            | 类型          | 说明                        |
| ----------------------------- | ----------- | ------------------------- |
| id                            | VARCHAR     | 主键，格式 `msp_xxxxxxxx`      |
| task_id                       | VARCHAR     | 任务 ID                     |
| model_search_context_id       | VARCHAR     | Model Search Context ID   |
| feature_preprocessing_id      | VARCHAR     | Feature Preprocessing ID  |
| workflow_plan_id              | VARCHAR     | Workflow Plan ID          |
| status                        | VARCHAR     | 状态                        |
| planning_mode                 | VARCHAR     | 规划模式                      |
| task_type                     | VARCHAR     | 任务类型                      |
| target_column                 | VARCHAR     | 目标列                       |
| primary_metric                | VARCHAR     | 主指标                       |
| n_samples                     | INTEGER     | 样本数                       |
| n_features                    | INTEGER     | 特征数                       |
| n_candidate_models            | INTEGER     | 候选模型数量                    |
| hpo_enabled                   | BOOLEAN     | 是否启用 HPO                  |
| hpo_method                    | VARCHAR     | HPO 方法                    |
| max_total_trials              | INTEGER     | 最大总 trials                |
| ready_for_pipeline_generation | BOOLEAN     | 是否可进入 Pipeline Generation |
| llm_used                      | BOOLEAN     | 是否使用 LLM                  |
| llm_confidence_score          | FLOAT       | LLM 置信度                   |
| plan_json                     | JSONB       | 完整 Model Search Plan      |
| llm_request_json              | JSONB       | LLM 请求                    |
| llm_response_json             | JSONB       | LLM 响应                    |
| error_message                 | TEXT        | 错误信息                      |
| created_at                    | TIMESTAMPTZ | 创建时间                      |
| updated_at                    | TIMESTAMPTZ | 更新时间                      |

---

### 14.3 索引设计

| 索引                                   | 说明                               |
| ------------------------------------ | -------------------------------- |
| PRIMARY KEY(id)                      | 主键                               |
| INDEX(task_id)                       | 按任务查询                            |
| INDEX(model_search_context_id)       | 按上下文查询                           |
| INDEX(feature_preprocessing_id)      | 按预处理结果查询                         |
| INDEX(status)                        | 按状态查询                            |
| INDEX(ready_for_pipeline_generation) | 筛选可进入 Pipeline Generation 的 plan |
| INDEX(created_at)                    | 查询最新                             |
| INDEX(task_id, created_at DESC)      | 查询某任务最新 plan                     |

---

## 15. 后端模块结构建议

新增模块目录：

```text
backend/app/modules/model_search/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── llm_prompt_builder.py
├── llm_model_search_advisor.py
├── llm_response_parser.py
├── llm_advice_validator.py
├── candidate_model_selector.py
├── hpo_plan_builder.py
├── search_space_builder.py
├── trial_allocator.py
├── validation_plan_builder.py
├── evaluation_plan_builder.py
├── pipeline_input_builder.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

### 15.1 文件职责

| 文件                          | 职责                                 |
| --------------------------- | ---------------------------------- |
| api.py                      | 定义 Model Search Plan API           |
| schemas.py                  | 定义请求、响应、内部 DTO                     |
| service.py                  | 编排完整模型搜索计划生成流程                     |
| model.py                    | 定义 model_search_plan 表             |
| repository.py               | CRUD 和 get_latest_by_task_id       |
| context_builder.py          | 读取 Model Search Context 和 Registry |
| llm_prompt_builder.py       | 构建 LLM Prompt                      |
| llm_model_search_advisor.py | 调用 LLM 获取模型搜索建议                    |
| llm_response_parser.py      | 解析 LLM JSON                        |
| llm_advice_validator.py     | 校验 LLM 建议                          |
| candidate_model_selector.py | 生成候选模型计划                           |
| hpo_plan_builder.py         | 生成 HPO 计划                          |
| search_space_builder.py     | 基于模板生成超参数搜索空间                      |
| trial_allocator.py          | 分配不同模型的 trial budget               |
| validation_plan_builder.py  | 生成验证计划                             |
| evaluation_plan_builder.py  | 生成评价计划                             |
| pipeline_input_builder.py   | 生成下游 Pipeline Generation 输入        |
| builder.py                  | 构建 Model Search Plan Object        |
| enums.py                    | 状态、预算、搜索空间宽度枚举                     |
| exceptions.py               | 模块专用异常                             |

---

## 16. 前端需求

### 16.1 新增前端模块

```text
frontend/src/modules/modelSearch/
├── components/
│   ├── ModelSearchPlanPanel.tsx
│   ├── ModelSearchSummaryCard.tsx
│   ├── CandidateModelPlanCard.tsx
│   ├── BaselineModelCard.tsx
│   ├── HPOPlanCard.tsx
│   ├── SearchSpacePlanCard.tsx
│   ├── TrialAllocationCard.tsx
│   ├── ValidationEvaluationPlanCard.tsx
│   ├── LLMModelSearchAdviceCard.tsx
│   ├── SystemValidationResultCard.tsx
│   └── ModelSearchPlanJsonViewer.tsx
├── types.ts
└── constants.ts
```

---

### 16.2 前端 API 客户端

新增：

```text
frontend/src/api/modelSearchApi.ts
```

封装：

```text
createModelSearchPlan(taskId)
getModelSearchPlan(planId)
getLatestModelSearchPlanByTaskId(taskId)
rerunModelSearchPlan(taskId)
getModelSearchPlanSummary(planId)
```

---

### 16.3 前端展示内容

MVP 阶段展示：

1. Model Search Plan 状态；
2. task_type；
3. primary_metric；
4. n_samples；
5. n_features；
6. baseline models；
7. candidate models；
8. excluded models；
9. HPO method；
10. max_total_trials；
11. trial allocation；
12. search space summary；
13. validation plan；
14. evaluation plan；
15. LLM advice；
16. rejected suggestions；
17. ready_for_pipeline_generation；
18. warnings / errors；
19. 完整 JSON。

---

### 16.4 页面集成

当前前端是单一 TaskSpecificationPage，含多个嵌入式面板。建议在现有页面中追加：

```text
ModelSearchPlanPanel
```

放置在：

```text
ModelSearchContextPanel
    ↓
ModelSearchPlanPanel
    ↓
后续 PipelineGenerationPanel
```

---

## 17. 错误处理

### 17.1 错误码

| 错误码                                | 场景                                  |
| ---------------------------------- | ----------------------------------- |
| TASK_NOT_FOUND                     | task_id 不存在                         |
| MODEL_SEARCH_CONTEXT_REQUIRED      | 尚未执行 Model Search Context           |
| MODEL_SEARCH_CONTEXT_NOT_READY     | Model Search Context 状态不可用          |
| MODEL_READY_INPUT_NOT_READY        | ready_for_model_search_plan = false |
| MODEL_REGISTRY_UNAVAILABLE         | Model Registry 不可用                  |
| HPO_REGISTRY_UNAVAILABLE           | HPO Registry 不可用                    |
| LLM_MODEL_SEARCH_CALL_FAILED       | LLM 调用失败                            |
| LLM_MODEL_SEARCH_PARSE_FAILED      | LLM 输出解析失败                          |
| LLM_MODEL_SEARCH_VALIDATION_FAILED | LLM 建议校验失败                          |
| NO_SUPPORTED_MODEL_FOUND           | 无可用候选模型                             |
| NO_SUPPORTED_HPO_METHOD_FOUND      | 无可用 HPO 方法                          |
| SEARCH_SPACE_BUILD_FAILED          | 超参数搜索空间生成失败                         |
| TRIAL_ALLOCATION_FAILED            | trial 分配失败                          |
| MODEL_SEARCH_PLAN_NOT_FOUND        | 查询不到 plan                           |

---

### 17.2 Warning

| Warning                           | 场景                            |
| --------------------------------- | ----------------------------- |
| LLM_SUGGESTION_PARTIALLY_REJECTED | LLM 部分建议被拒绝                   |
| FALLBACK_MODEL_USED               | 使用系统 fallback 模型              |
| FALLBACK_HPO_METHOD_USED          | 使用系统 fallback HPO 方法          |
| LOW_HPO_BUDGET                    | HPO 预算较低                      |
| HIGH_TRIAL_COUNT                  | trial 数较高                     |
| MODEL_EXCLUDED_BY_REGISTRY        | 模型因 Registry 约束被排除            |
| SEARCH_SPACE_NARROWED_BY_SYSTEM   | 搜索空间被系统收窄                     |
| READY_WITH_WARNINGS               | 可进入 Pipeline Generation 但存在警告 |

---

## 18. 配置需求

新增配置：

```text
MODEL_SEARCH_ENABLE_LLM_ADVISOR=true
MODEL_SEARCH_LLM_TEMPERATURE=0
MODEL_SEARCH_LLM_TIMEOUT=60
MODEL_SEARCH_LLM_MAX_RETRIES=2

MODEL_SEARCH_DEFAULT_HPO_METHOD=random_search
MODEL_SEARCH_MAX_TOTAL_TRIALS=50
MODEL_SEARCH_DEFAULT_MAX_PARALLEL_TRIALS=1

MODEL_SEARCH_MIN_CANDIDATE_MODELS=1
MODEL_SEARCH_MAX_CANDIDATE_MODELS=6
MODEL_SEARCH_REQUIRE_BASELINE=true
MODEL_SEARCH_ENABLE_XGBOOST=true
MODEL_SEARCH_ENABLE_SVR=true
MODEL_SEARCH_ENABLE_KNN=false
```

---

## 19. MVP 验收标准

| 序号 | 验收标准                                      |
| -- | ----------------------------------------- |
| 1  | 能通过 task_id 读取最新 Model Search Context     |
| 2  | 能拒绝 Model Search Context 未完成的任务           |
| 3  | 能拒绝 ready_for_model_search_plan=false 的任务 |
| 4  | 能读取 Model Registry                        |
| 5  | 能读取 HPO Registry                          |
| 6  | 能构建 LLM Model Search Prompt               |
| 7  | 能调用 LLM 获取结构化模型搜索建议                       |
| 8  | 能解析 LLM JSON                              |
| 9  | 能拒绝 LLM 输出中的未注册模型                         |
| 10 | 能拒绝 LLM 输出中的未注册 HPO 方法                    |
| 11 | 能拒绝 LLM 输出中的可执行代码                         |
| 12 | 能生成 baseline model plan                   |
| 13 | 能生成 candidate model plan                  |
| 14 | 能生成 HPO plan                              |
| 15 | 能生成 search_space_plan                     |
| 16 | 能生成 trial_allocation                      |
| 17 | 能生成 validation_plan                       |
| 18 | 能生成 evaluation_plan                       |
| 19 | 能生成 pipeline_generation_input             |
| 20 | 能持久化 Model Search Plan                    |
| 21 | 能查询某任务最新 Model Search Plan                |
| 22 | 能 rerun 且不覆盖旧结果                           |
| 23 | 前端能展示候选模型和 HPO 计划                         |
| 24 | 不训练模型                                     |
| 25 | 不执行 HPO                                   |
| 26 | 不生成可执行代码                                  |

---

## 20. 示例流程

### 20.1 输入

```json
{
  "model_search_context_input": {
    "model_ready_matrix_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/model_ready_features.parquet",
    "preprocessing_pipeline_artifact_id": "artifact_preprocessor_xxxxxxxx",
    "target_column": "band_gap",
    "feature_columns": [],
    "task_type": "regression",
    "primary_metric": "MAE",
    "model_strategy": {},
    "validation_strategy": {},
    "evaluation_strategy": {},
    "hpo_strategy": {},
    "ready_for_model_search_plan": true
  }
}
```

---

### 20.2 处理流程

```text
POST /api/model-search-plans/task_xxxxxxxx
    ↓
读取 Model Search Context
    ↓
读取 Model Registry / HPO Registry
    ↓
构建 LLM Model Search Prompt
    ↓
LLM 生成结构化模型搜索建议
    ↓
解析和校验 LLM 输出
    ↓
生成候选模型计划
    ↓
生成 HPO 计划
    ↓
生成超参数搜索空间计划
    ↓
生成 trial allocation
    ↓
生成 validation / evaluation plan
    ↓
生成 pipeline_generation_input
    ↓
持久化 Model Search Plan
```

---

### 20.3 输出摘要

```json
{
  "status": "planned_with_warning",
  "n_candidate_models": 4,
  "hpo_enabled": true,
  "hpo_method": "random_search",
  "max_total_trials": 30,
  "ready_for_pipeline_generation": true
}
```

---

## 21. 后续迭代方向

### 21.1 V2：搜索空间模板增强

支持：

1. 模型族级默认搜索空间；
2. 任务类型级搜索空间；
3. 数据规模自适应搜索空间；
4. 高维/低维特征自适应搜索空间；
5. 材料任务专用模型偏好模板。

---

### 21.2 V3：多策略 Model Search Plan

支持生成多个计划版本：

```text
accuracy_first
efficiency_first
interpretability_first
balanced
```

---

### 21.3 V4：历史实验反馈融合

结合历史训练结果，调整模型候选优先级和 HPO 预算。

---

### 21.4 V5：Pipeline Generation 深度联动

将 `pipeline_generation_input` 直接转化为受控 Pipeline Spec，而非代码。

---

## 22. 总结

Automated Model and HPO Search 模块是 Model Search Context Update 与 Executable Pipeline Generation 之间的模型搜索规划层。

它的核心输入是：

```text
Model Search Context Object
+
Model Registry
+
HPO Registry
+
LLM structured advice
```

它的核心输出是：

```text
Model Search Plan Object
+
pipeline_generation_input
```

它应该回答：

```text
本任务应该搜索哪些模型？
哪些模型作为 baseline？
HPO 方法是什么？
每个模型搜索多少 trials？
每个模型的搜索空间是什么？
下游 Pipeline Generation 应该如何构建训练任务？
```

它不应该回答：

```text
哪个模型效果最好？
训练结果是多少？
如何执行 HPO？
如何生成 Python 训练代码？
如何运行训练脚本？
```

一句话总结：

```text
Automated Model and HPO Search 让 LLM 深度参与模型搜索策略设计，
但最终由系统基于 Registry、模板和校验器生成稳定、安全、可控的 Model Search Plan。
```

```
```
