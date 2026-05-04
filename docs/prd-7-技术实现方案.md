# Model Search Context Update 模块架构与技术栈方案

## 1. 模块名称

Model Search Context Update  
模型搜索上下文更新模块

---

## 2. 架构定位

本模块是一个 **LLM-guided strategy calibration module**。

它不是执行模块，而是策略更新模块。

它的输入是：

```text
Workflow Plan
+
Feature Engineering Object
+
Feature Preprocessing Object
````

它的输出是：

```text
Model Search Context Object
+
model_search_context_input
```

---

## 3. 总体架构

```text
Frontend
  └── Model Search Context Panel
        ↓
Backend API Layer
        ↓
Service Layer
        ↓
Context Builder
        ↓
Dataset / Feature / Preprocessing Analyzers
        ↓
LLM Context Builder
        ↓
LLM Strategy Advisor
        ↓
LLM Response Parser
        ↓
LLM Advice Validator
        ↓
Strategy Merger
        ↓
Object Builder
        ↓
Repository
        ↓
Automated Model and HPO Search
```

---

## 4. 核心架构原则

### 4.1 LLM 深度参与

LLM 参与：

1. 分析数据变化；
2. 理解 feature group 删除对建模的影响；
3. 判断候选模型策略是否需要调整；
4. 建议 HPO 预算；
5. 建议验证策略；
6. 给出策略调整原因。

---

### 4.2 LLM 不直接控制系统执行

LLM 不允许：

1. 输出训练代码；
2. 输出可执行 pipeline；
3. 输出系统配置修改代码；
4. 输出动态执行逻辑；
5. 绕过系统注册表选择模型；
6. 直接决定最终策略。

---

### 4.3 系统负责最终落地

最终结果由系统执行：

```text
LLM advice
    ↓
schema validation
    ↓
registry validation
    ↓
rule-based merge
    ↓
final context object
```

---

## 5. 后端模块拆分

```text
backend/app/modules/model_search_context/
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

## 6. 文件职责

| 文件                              | 职责                     |
| ------------------------------- | ---------------------- |
| api.py                          | 定义 API                 |
| schemas.py                      | 定义 DTO 和输出对象           |
| service.py                      | 编排完整流程                 |
| model.py                        | 定义数据库表                 |
| repository.py                   | CRUD 和最新记录查询           |
| context_builder.py              | 读取上游模块                 |
| dataset_profile_analyzer.py     | 分析有效样本数、最终特征数          |
| feature_group_analyzer.py       | 分析 feature group 保留和删除 |
| preprocessing_analyzer.py       | 分析已执行的预处理              |
| llm_context_builder.py          | 构建 LLM 输入上下文           |
| llm_strategy_advisor.py         | 调用 LLM 获取结构化策略建议       |
| llm_response_parser.py          | 解析 LLM JSON            |
| llm_advice_validator.py         | 校验 LLM 建议是否合法          |
| strategy_merger.py              | 合并系统规则和 LLM 建议         |
| model_strategy_adjuster.py      | 生成最终模型策略               |
| hpo_strategy_adjuster.py        | 生成最终 HPO 策略            |
| validation_strategy_adjuster.py | 生成最终验证策略               |
| evaluation_strategy_adjuster.py | 校验评价策略                 |
| builder.py                      | 构建输出对象                 |
| enums.py                        | 状态和枚举                  |
| exceptions.py                   | 异常定义                   |

---

## 7. 技术栈方案

| 技术                  | 用途           |
| ------------------- | ------------ |
| FastAPI             | API 层        |
| SQLModel            | ORM          |
| PostgreSQL JSONB    | 存储完整上下文对象    |
| Pydantic v2         | Schema 校验    |
| pydantic-settings   | 配置管理         |
| httpx               | LLM API 调用   |
| logging / structlog | 结构化日志        |
| pytest              | 测试           |
| Model Registry      | 校验模型合法性      |
| HPO Registry        | 校验 HPO 方法合法性 |

---

## 8. LLM 技术方案

### 8.1 LLM 调用方式

本模块应复用已有 LLM Client。

建议路径：

```text
backend/app/shared/llm/
```

或复用当前 Task Interpretation / Workflow Planning 中已有 LLM Client。

---

### 8.2 LLM Prompt 结构

Prompt 应包含：

```text
System Role
    ↓
Safety Boundary
    ↓
Task Context
    ↓
Model-ready Dataset Summary
    ↓
Feature Group Summary
    ↓
Preprocessing Summary
    ↓
Allowed Model Families
    ↓
Allowed HPO Methods
    ↓
Required JSON Schema
```

---

### 8.3 Prompt 关键约束

必须明确：

```text
Do not output executable code.
Do not output Python scripts.
Do not invent unsupported model families.
Only choose from allowed_model_families.
Only choose from allowed_hpo_methods.
Return JSON only.
```

---

## 9. Model Registry 设计

为了约束 LLM 输出，本模块需要依赖 Model Registry。

建议新增或预留：

```text
backend/app/shared/registry/model_registry.py
```

Registry 定义：

1. model_family；
2. supported_task_types；
3. requires_scaling；
4. supports_regression；
5. supports_classification；
6. default_hpo_space_id；
7. complexity_level；
8. interpretability_level。

示例模型族：

```text
dummy_mean
linear_regression
ridge
lasso
elastic_net
random_forest
gradient_boosting
xgboost
svr
knn
```

---

## 10. HPO Registry 设计

建议新增或预留：

```text
backend/app/shared/registry/hpo_registry.py
```

定义：

1. random_search；
2. grid_search；
3. optuna_tpe；
4. bayesian_search；
5. successive_halving。

---

## 11. 数据流设计

```text
POST /api/model-search-contexts/{task_id}
    ↓
读取上游模块
    ↓
分析 model-ready dataset
    ↓
构建 LLM 输入
    ↓
调用 LLM 生成结构化 advice
    ↓
解析 LLM JSON
    ↓
校验 advice
    ↓
合并系统规则
    ↓
生成 final model_search_context_input
    ↓
写入数据库
```

---

## 12. LLM Advice Validation

系统必须校验：

1. 是否为合法 JSON；
2. 是否符合 Pydantic Schema；
3. 是否包含可执行代码；
4. 模型是否在 Model Registry；
5. HPO 方法是否在 HPO Registry；
6. max_trials 是否超过配置上限；
7. primary_metric 是否与任务类型兼容；
8. validation_strategy 是否与样本数兼容；
9. 是否缺少必要字段。

非法建议处理：

```text
reject invalid field
    ↓
record rejected_suggestions
    ↓
fallback to system rule
```

---

## 13. Strategy Merger 设计

最终策略生成逻辑：

```text
Original Workflow Plan Strategy
    ↓
System Rule Adjustment
    ↓
LLM Advice
    ↓
Registry Validation
    ↓
Final Updated Strategy
```

优先级建议：

```text
Safety validation > System constraints > User priority > LLM advice > Original plan
```

---

## 14. 数据库设计

表名：

```text
model_search_context
```

核心字段：

| 字段                          | 类型          |
| --------------------------- | ----------- |
| id                          | VARCHAR     |
| task_id                     | VARCHAR     |
| workflow_plan_id            | VARCHAR     |
| feature_engineering_id      | VARCHAR     |
| feature_preprocessing_id    | VARCHAR     |
| status                      | VARCHAR     |
| update_mode                 | VARCHAR     |
| task_type                   | VARCHAR     |
| n_samples                   | INTEGER     |
| n_final_features            | INTEGER     |
| primary_metric              | VARCHAR     |
| model_strategy_adjusted     | BOOLEAN     |
| hpo_strategy_adjusted       | BOOLEAN     |
| llm_used                    | BOOLEAN     |
| llm_confidence_score        | FLOAT       |
| ready_for_model_search_plan | BOOLEAN     |
| context_json                | JSONB       |
| llm_request_json            | JSONB       |
| llm_response_json           | JSONB       |
| error_message               | TEXT        |
| created_at                  | TIMESTAMPTZ |
| updated_at                  | TIMESTAMPTZ |

---

## 15. API 设计

```text
POST /api/model-search-contexts/{task_id}
GET /api/model-search-contexts/{context_id}
GET /api/tasks/{task_id}/model-search-context
POST /api/model-search-contexts/{task_id}/rerun
```

---

## 16. 状态设计

```text
pending
analyzing
llm_advising
validating_advice
updating
updated
updated_with_warning
failed
blocked
```

---

## 17. 配置设计

```text
MODEL_CONTEXT_ENABLE_LLM_ADVISOR=true
MODEL_CONTEXT_LLM_TEMPERATURE=0
MODEL_CONTEXT_LLM_TIMEOUT=60
MODEL_CONTEXT_LLM_MAX_RETRIES=2

MODEL_CONTEXT_LOW_FEATURE_THRESHOLD=20
MODEL_CONTEXT_HIGH_REDUCTION_RATIO=0.8
MODEL_CONTEXT_SMALL_SAMPLE_THRESHOLD=200

MODEL_CONTEXT_MAX_HPO_TRIALS=50
MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_SMALL=20
MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_MEDIUM=30
MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_LARGE=50
```

---

## 18. 前端设计

目录：

```text
frontend/src/modules/modelSearchContext/
```

组件：

```text
ModelSearchContextPanel.tsx
EffectiveDatasetProfileCard.tsx
FeatureGroupSummaryCard.tsx
PreprocessingSummaryCard.tsx
LLMAdviceCard.tsx
LLMAdviceValidationCard.tsx
StrategyAdjustmentCard.tsx
UpdatedModelStrategyCard.tsx
UpdatedHPOStrategyCard.tsx
ModelSearchContextJsonViewer.tsx
```

---

## 19. 测试方案

### 19.1 单元测试

1. dataset analyzer；
2. feature group analyzer；
3. preprocessing analyzer；
4. LLM response parser；
5. LLM advice validator；
6. strategy merger。

### 19.2 集成测试

1. LLM 输出合法 JSON；
2. LLM 输出非法模型被拒绝；
3. LLM 输出代码片段被拒绝；
4. LLM 输出过大 HPO budget 被截断；
5. 系统 fallback 生效；
6. 成功生成 model_search_context_input。

---

## 20. MVP 实现范围

MVP 必须实现：

1. LLM 结构化建议；
2. LLM JSON 解析；
3. LLM 建议校验；
4. Model Registry 校验；
5. HPO Registry 校验；
6. 系统规则合并；
7. Model Search Context 持久化；
8. 下游 model_search_context_input 输出。

MVP 不实现：

1. 不训练模型；
2. 不执行 HPO；
3. 不生成训练代码；
4. 不执行 Pipeline；
5. 不做历史训练反馈融合。

---

## 21. 总结

Model Search Context Update 是 LLM 深度参与模型搜索策略调整的关键模块。

它通过：

```text
LLM reasoning
+
system registry
+
schema validation
+
rule-based merge
```

生成安全、稳定、可控的 Model Search Context。

最终原则：

```text
LLM 参与策略判断，
但系统控制最终执行边界。
```

```
```