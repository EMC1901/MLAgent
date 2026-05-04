# PRD：Model Search Context Update 模块需求文档

## 1. 模块名称

Model Search Context Update  
模型搜索上下文更新模块

---

## 2. 模块定位

Model Search Context Update 位于 **Feature Preprocessing** 之后、**Automated Model and HPO Search** 之前。

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
基于 Feature Preprocessing 后真实的 model-ready dataset，
结合原 Workflow Plan 和 LLM 的策略分析能力，
对模型搜索上下文进行局部更新，
为 Automated Model and HPO Search 生成更准确、更合理、更可控的输入。
```

---

## 3. 重要设计原则

本系统不是“不使用 LLM”，而是：

```text
LLM 要深度参与机器学习流程；
但 LLM 不能返回可能修改系统运行逻辑、破坏系统稳定性或导致系统出错的可执行代码。
```

因此，本模块中 LLM 可以参与：

1. 分析 model-ready dataset 的变化；
2. 判断原 model_strategy 是否仍然合理；
3. 建议候选模型策略调整；
4. 建议 HPO 预算调整；
5. 建议 validation_strategy 调整；
6. 解释策略调整原因；
7. 输出结构化 JSON 建议。

但 LLM 不允许输出：

1. Python 训练代码；
2. HPO 执行代码；
3. Pipeline 脚本；
4. 数据库修改代码；
5. 系统配置修改代码；
6. 任何可直接执行并改变系统行为的代码。

最终 Model Search Context 必须由系统校验、合并和持久化。

---

## 4. 背景说明

Workflow Planning 阶段生成模型策略时，依据的是：

```text
任务语义
+
数据画像
+
预期特征工程策略
```

但经过 Automated Feature Engineering 和 Feature Preprocessing 后，真实建模数据可能已经发生明显变化：

```text
原计划特征数：140
预处理后最终有效特征数：14

原计划使用 matminer_element_property
预处理后该 feature group 被整体删除

原计划需要 scaling
Feature Preprocessing 已经完成 scaling

原计划 HPO budget = medium
实际特征数量很少，可能应降低搜索预算
```

因此，直接使用原始 Workflow Plan 进入 Automated Model and HPO Search 可能不准确。
本模块需要结合系统规则与 LLM 分析能力，对模型搜索上下文进行局部更新。

---

## 5. 模块目标

本模块目标是：

1. 读取最新 Workflow Plan；
2. 读取最新 Feature Engineering Object；
3. 读取最新 Feature Preprocessing Object；
4. 分析最终 model-ready dataset 的真实状态；
5. 汇总有效特征数、删除特征数、保留 feature group、删除 feature group；
6. 分析已执行的 preprocessing 操作；
7. 调用 LLM 进行模型搜索策略分析；
8. 接收 LLM 输出的结构化策略建议；
9. 使用系统规则校验 LLM 建议；
10. 合并系统规则与 LLM 建议，生成最终 Model Search Context；
11. 输出 Automated Model and HPO Search 可消费的 `model_search_context_input`；
12. 持久化 Model Search Context Object。

---

## 6. 系统边界

### 6.1 本模块负责

本模块负责：

1. 读取上游模块输出；
2. 构建 Model Search Context Update Context；
3. 分析真实 model-ready dataset；
4. 分析 feature group 保留与删除情况；
5. 分析 preprocessing 是否已执行；
6. 调用 LLM 生成结构化策略建议；
7. 校验 LLM 建议是否合法；
8. 生成 updated_model_strategy；
9. 生成 updated_hpo_strategy；
10. 生成 updated_validation_strategy；
11. 生成 updated_evaluation_strategy；
12. 输出 model_search_context_input；
13. 持久化上下文结果；
14. 支持查询、重跑与版本追踪。

---

### 6.2 本模块不负责

本模块不负责：

1. 不重新执行 Task Specification；
2. 不重新执行 Task Interpretation；
3. 不重新执行 Dataset Profiling；
4. 不重新执行 Workflow Planning；
5. 不重新执行 Feature Engineering；
6. 不重新执行 Feature Preprocessing；
7. 不训练模型；
8. 不执行 HPO；
9. 不生成 Pipeline 代码；
10. 不执行 Pipeline；
11. 不计算模型性能指标；
12. 不选择最佳模型；
13. 不生成最终报告。

特别注意：

```text
本模块只更新“模型搜索上下文”；
不执行“模型搜索过程”。
```

---

## 7. 上游输入

### 7.1 Workflow Plan Object

主要消费：

| 字段                        | 说明               |
| ------------------------- | ---------------- |
| workflow_plan_id          | Workflow Plan ID |
| model_strategy            | 原始模型策略           |
| validation_strategy       | 原始验证策略           |
| evaluation_strategy       | 原始评价策略           |
| hpo_strategy              | 原始 HPO 策略        |
| interpretability_strategy | 可解释性策略           |
| planning_warnings         | 规划警告             |
| planning_assumptions      | 规划假设             |

---

### 7.2 Feature Engineering Object

主要消费：

| 字段                     | 说明                  |
| ---------------------- | ------------------- |
| feature_engineering_id | 特征工程 ID             |
| feature_generation     | featurizer 执行记录     |
| feature_schema         | 原始 feature group 信息 |
| feature_quality        | 初步特征质量              |
| warnings               | 特征工程警告              |

---

### 7.3 Feature Preprocessing Object

本模块最关键输入。

| 字段                              | 说明                                    |
| ------------------------------- | ------------------------------------- |
| preprocessing_id                | 特征预处理 ID                              |
| status                          | 预处理状态                                 |
| validation_summary              | 有效特征、删除特征、样本数                         |
| column_validation               | 列级过滤结果                                |
| feature_group_validation        | feature group 有效性                     |
| preprocessing_execution         | imputation / scaling / selection 执行情况 |
| model_ready_artifact            | model-ready matrix artifact           |
| preprocessing_pipeline_artifact | preprocessor artifact                 |
| model_search_input              | 初始模型搜索输入                              |
| warnings                        | 预处理警告                                 |
| errors                          | 预处理错误                                 |

---

## 8. 前置条件

进入本模块前必须满足：

1. task_id 存在；
2. Workflow Plan 状态为 `planned` 或 `planned_with_warning`；
3. Feature Engineering 状态为 `completed` 或 `completed_with_warning`；
4. Feature Preprocessing 状态为 `preprocessed` 或 `preprocessed_with_warning`；
5. Feature Preprocessing 中 `ready_for_model_search = true`；
6. model-ready artifact 存在；
7. preprocessing pipeline artifact 存在；
8. target column 存在；
9. final feature count 大于 0。

---

## 9. LLM 参与方式

### 9.1 LLM 输入

LLM 接收的是系统构建后的结构化上下文，而不是原始文件或代码。

示例：

```json
{
  "task_type": "regression",
  "target_column": "band_gap",
  "primary_metric": "MAE",
  "dataset_effective_profile": {
    "n_samples": 4604,
    "n_final_features": 14,
    "feature_reduction_ratio": 0.85
  },
  "feature_group_summary": {
    "retained_groups": ["matminer_stoichiometry", "matminer_valence_orbital"],
    "dropped_groups": ["matminer_element_property"]
  },
  "preprocessing_summary": {
    "imputation_executed": true,
    "scaling_executed": true,
    "feature_selection_executed": true
  },
  "original_model_strategy": {},
  "original_hpo_strategy": {},
  "allowed_model_families": [],
  "allowed_hpo_methods": []
}
```

---

### 9.2 LLM 输出

LLM 必须输出结构化 JSON 建议。

示例：

```json
{
  "model_strategy_suggestion": {
    "candidate_model_families": [
      "ridge",
      "random_forest",
      "gradient_boosting",
      "xgboost"
    ],
    "baseline_models": [
      "dummy_mean",
      "linear_regression",
      "ridge"
    ],
    "preferred_model_bias": "balanced_accuracy_and_stability"
  },
  "hpo_strategy_suggestion": {
    "budget_level": "moderate",
    "max_trials": 30,
    "search_method": "random_search"
  },
  "validation_strategy_suggestion": {
    "split_strategy": "k_fold_cross_validation",
    "n_splits": 5
  },
  "adjustment_reasons": [
    "effective_feature_count_is_low",
    "major_feature_group_dropped",
    "scaling_already_executed"
  ],
  "confidence_score": 0.86
}
```

---

### 9.3 LLM 输出禁止内容

LLM 不允许输出：

```text
Python 代码
Shell 命令
SQL 修改语句
训练脚本
Pipeline 执行脚本
系统配置修改代码
动态 import 逻辑
任意可执行代码
```

---

### 9.4 系统校验原则

LLM 输出必须经过：

```text
JSON parse
    ↓
Schema validation
    ↓
Model registry validation
    ↓
HPO method validation
    ↓
Strategy boundary validation
    ↓
System rule merge
    ↓
Final Model Search Context Object
```

---

## 10. 输出对象

### 10.1 输出对象名称

```text
Model Search Context Object
```

数据库表建议：

```text
model_search_context
```

---

### 10.2 输出对象示例

```json
{
  "context_id": "msc_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "feature_engineering_id": "feat_xxxxxxxx",
  "feature_preprocessing_id": "fmp_xxxxxxxx",
  "status": "updated_with_warning",
  "update_mode": "llm_guided_with_system_validation",
  "dataset_effective_profile": {
    "n_samples": 4604,
    "n_raw_features": 140,
    "n_final_features": 14,
    "n_dropped_features": 126,
    "feature_reduction_ratio": 0.9,
    "target_column": "band_gap",
    "task_type": "regression"
  },
  "feature_group_summary": {
    "retained_groups": [
      "matminer_stoichiometry",
      "matminer_valence_orbital"
    ],
    "dropped_groups": [
      "matminer_element_property"
    ],
    "low_effective_feature_warning": true
  },
  "preprocessing_summary": {
    "imputation_executed": true,
    "scaling_executed": true,
    "feature_selection_executed": true,
    "categorical_encoding_executed": false,
    "preprocessing_pipeline_artifact_id": "artifact_preprocessor_xxxxxxxx"
  },
  "llm_strategy_advice": {
    "candidate_model_families": [],
    "hpo_budget_level": "moderate",
    "adjustment_reasons": [],
    "confidence_score": 0.86
  },
  "system_validation_result": {
    "is_valid": true,
    "rejected_suggestions": [],
    "fallback_applied": false
  },
  "strategy_adjustment": {
    "model_strategy_adjusted": true,
    "hpo_strategy_adjusted": true,
    "validation_strategy_adjusted": false,
    "evaluation_strategy_adjusted": false,
    "adjustment_reasons": [
      "low_effective_feature_count",
      "feature_group_dropped",
      "llm_recommended_conservative_hpo"
    ]
  },
  "updated_model_strategy": {},
  "updated_hpo_strategy": {},
  "updated_validation_strategy": {},
  "updated_evaluation_strategy": {},
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
  },
  "warnings": [],
  "errors": []
}
```

---

## 11. 核心功能需求

### 11.1 功能一：读取上游上下文

读取：

1. Workflow Plan；
2. Feature Engineering；
3. Feature Preprocessing；
4. Task Specification；
5. Task Interpretation。

输出 Model Search Context Update Context。

---

### 11.2 功能二：分析有效数据画像

分析：

1. n_samples；
2. n_raw_features；
3. n_final_features；
4. n_dropped_features；
5. feature_reduction_ratio；
6. target_column；
7. task_type。

---

### 11.3 功能三：分析 Feature Group 有效性

分析：

1. retained_groups；
2. dropped_groups；
3. partially_retained_groups；
4. 是否存在关键 feature group 被删除；
5. 是否仅剩少量低维特征；
6. 是否需要策略降级。

---

### 11.4 功能四：分析预处理执行状态

分析：

1. imputation 是否已执行；
2. scaling 是否已执行；
3. feature selection 是否已执行；
4. categorical encoding 是否已执行；
5. preprocessing pipeline artifact 是否存在；
6. 下游是否应避免重复预处理。

---

### 11.5 功能五：构建 LLM Strategy Context

将上游信息整理为 LLM 可消费的结构化上下文。

要求：

1. 不传递原始矩阵；
2. 不传递可执行代码；
3. 不传递系统内部敏感配置；
4. 只传递任务、数据摘要、策略摘要和允许选项；
5. 附带 allowed model families；
6. 附带 allowed HPO methods。

---

### 11.6 功能六：调用 LLM 生成策略建议

LLM 输出内容包括：

1. model_strategy_suggestion；
2. hpo_strategy_suggestion；
3. validation_strategy_suggestion；
4. evaluation_strategy_suggestion；
5. adjustment_reasons；
6. risk_notes；
7. confidence_score。

---

### 11.7 功能七：校验 LLM 建议

系统必须校验：

1. candidate_model_families 是否在 Model Registry 中；
2. HPO method 是否被系统支持；
3. max_trials 是否超过系统上限；
4. validation strategy 是否与样本数、任务类型兼容；
5. primary metric 是否与任务类型兼容；
6. 是否包含可执行代码；
7. 是否包含未注册模型；
8. 是否包含系统无法执行的策略。

---

### 11.8 功能八：合并系统规则与 LLM 建议

最终策略不是 LLM 原始输出，而是：

```text
系统规则
+
LLM 结构化建议
+
Model Registry 校验
+
HPO Registry 校验
+
安全边界校验
```

合并后的结果写入：

1. updated_model_strategy；
2. updated_hpo_strategy；
3. updated_validation_strategy；
4. updated_evaluation_strategy。

---

### 11.9 功能九：生成 model_search_context_input

生成 Automated Model and HPO Search 可直接消费的结构化输入：

```json
{
  "model_ready_matrix_path": "...",
  "preprocessing_pipeline_artifact_id": "...",
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

## 12. 状态设计

| 状态                   | 含义                       |
| -------------------- | ------------------------ |
| pending              | 已创建任务，尚未执行               |
| analyzing            | 正在分析 model-ready dataset |
| llm_advising         | 正在调用 LLM 生成结构化建议         |
| validating_advice    | 正在校验 LLM 建议              |
| updating             | 正在合并策略并生成上下文             |
| updated              | 更新完成                     |
| updated_with_warning | 更新完成但存在警告                |
| failed               | 更新失败                     |
| blocked              | 上游状态不满足                  |

---

## 13. API 设计

### 13.1 创建 Model Search Context

```text
POST /api/model-search-contexts/{task_id}
```

请求体 MVP 可为空。

后续可扩展：

```json
{
  "force_rerun": false,
  "use_llm_advisor": true,
  "adjust_model_strategy": true,
  "adjust_hpo_strategy": true,
  "adjust_validation_strategy": true
}
```

---

### 13.2 查询 Model Search Context

```text
GET /api/model-search-contexts/{context_id}
```

---

### 13.3 查询任务最新 Context

```text
GET /api/tasks/{task_id}/model-search-context
```

---

### 13.4 重新执行

```text
POST /api/model-search-contexts/{task_id}/rerun
```

---

## 14. 数据库设计

### 14.1 表名

```text
model_search_context
```

---

### 14.2 字段设计

| 字段                          | 类型          | 说明                       |
| --------------------------- | ----------- | ------------------------ |
| id                          | VARCHAR     | 主键，格式 `msc_xxxxxxxx`     |
| task_id                     | VARCHAR     | 任务 ID                    |
| workflow_plan_id            | VARCHAR     | Workflow Plan ID         |
| feature_engineering_id      | VARCHAR     | Feature Engineering ID   |
| feature_preprocessing_id    | VARCHAR     | Feature Preprocessing ID |
| status                      | VARCHAR     | 状态                       |
| update_mode                 | VARCHAR     | 更新模式                     |
| task_type                   | VARCHAR     | 任务类型                     |
| target_column               | VARCHAR     | 目标列                      |
| n_samples                   | INTEGER     | 样本数                      |
| n_final_features            | INTEGER     | 最终特征数                    |
| primary_metric              | VARCHAR     | 主指标                      |
| model_strategy_adjusted     | BOOLEAN     | 是否调整模型策略                 |
| hpo_strategy_adjusted       | BOOLEAN     | 是否调整 HPO 策略              |
| ready_for_model_search_plan | BOOLEAN     | 是否可进入 Model Search       |
| llm_used                    | BOOLEAN     | 是否使用 LLM                 |
| llm_confidence_score        | FLOAT       | LLM 建议置信度                |
| context_json                | JSONB       | 完整上下文对象                  |
| llm_request_json            | JSONB       | LLM 请求摘要                 |
| llm_response_json           | JSONB       | LLM 原始结构化响应              |
| error_message               | TEXT        | 错误信息                     |
| created_at                  | TIMESTAMPTZ | 创建时间                     |
| updated_at                  | TIMESTAMPTZ | 更新时间                     |

---

## 15. 后端模块结构建议

```text
backend/app/modules/model_search_context/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── dataset_profile_analyzer.py
├── feature_group_analyzer.py
├── preprocessing_analyzer.py
├── llm_context_builder.py
├── llm_strategy_advisor.py
├── llm_response_parser.py
├── llm_advice_validator.py
├── strategy_merger.py
├── model_strategy_adjuster.py
├── hpo_strategy_adjuster.py
├── validation_strategy_adjuster.py
├── evaluation_strategy_adjuster.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

## 16. 与下游模块的关系

Automated Model and HPO Search 后续应消费：

```text
model_search_context_input
```

而不是直接消费原 Workflow Plan。

---

## 17. MVP 验收标准

| 序号 | 验收标准                                 |
| -- | ------------------------------------ |
| 1  | 能读取 Workflow Plan                    |
| 2  | 能读取 Feature Engineering              |
| 3  | 能读取 Feature Preprocessing            |
| 4  | 能拒绝 ready_for_model_search=false 的任务 |
| 5  | 能构建 LLM Strategy Context             |
| 6  | 能调用 LLM 获取结构化建议                      |
| 7  | 能解析 LLM JSON 响应                      |
| 8  | 能拒绝 LLM 输出中的非法模型                     |
| 9  | 能拒绝 LLM 输出中的可执行代码                    |
| 10 | 能合并系统规则与 LLM 建议                      |
| 11 | 能生成 updated_model_strategy           |
| 12 | 能生成 updated_hpo_strategy             |
| 13 | 能生成 model_search_context_input       |
| 14 | 能持久化 Model Search Context            |
| 15 | 不训练模型                                |
| 16 | 不执行 HPO                              |
| 17 | 不生成可执行代码                             |

---

## 18. 总结

Model Search Context Update 模块是 Feature Preprocessing 与 Automated Model and HPO Search 之间的 LLM-guided 策略校准层。

它的核心输入是：

```text
Workflow Plan
+
Feature Engineering Object
+
Feature Preprocessing Object
```

它的核心输出是：

```text
Model Search Context Object
+
model_search_context_input
```

一句话总结：

```text
本模块让 LLM 深度参与模型搜索策略更新，
但通过系统校验和注册表约束，
保证最终输出稳定、安全、可控。
```

````


