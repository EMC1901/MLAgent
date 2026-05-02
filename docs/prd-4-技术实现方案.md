# LLM-guided Workflow Planning 模块架构与技术栈方案

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

当前前三个模块已经完成：

1. **Task Specification**：生成用户任务规格对象；
2. **LLM-based Task Interpretation**：生成任务语义理解对象；
3. **Dataset Loading, Checking, and Profiling**：生成数据画像对象，并输出 `workflow_planning_input`。

本模块的核心职责是基于前三个模块的输出，生成结构化、可持久化、可查询、可重跑的 **Workflow Plan Object**。

---

# 3. 总体架构目标

## 3.1 架构目标

LLM-guided Workflow Planning 模块需要满足以下目标：

1. 与 Task Specification、Task Interpretation、Dataset Profile 三个已完成模块自然衔接；
2. 通过 `task_id` 读取完整上游上下文；
3. 基于数据事实、任务语义和用户偏好生成 Workflow Plan；
4. 复用现有 LLM 调用能力，避免重复实现外部模型调用逻辑；
5. 对 LLM 输出进行解析、校验和结构化封装；
6. 将复杂规划结果持久化到 PostgreSQL JSONB；
7. 为后续 Pipeline Generation 模块提供稳定的 `pipeline_generation_input`；
8. 支持规划结果查询、重跑和版本追踪；
9. 保持模块边界清晰：只规划，不执行，不生成代码，不训练模型。

---

## 3.2 总体架构图

```text
Frontend
  └── Workflow Planning Panel
        ↓
Backend API Layer
  └── workflow_planning/api.py
        ↓
Service Layer
  └── workflow_planning/service.py
        ↓
Context Builder
  ├── Read Task Specification
  ├── Read Latest Task Interpretation
  └── Read Latest Dataset Profile
        ↓
Planning Context Normalizer
  └── Normalize upstream context into planning-ready format
        ↓
Prompt Builder
  └── Build LLM planning prompt
        ↓
LLM Client Adapter
  └── Reuse task_interpretation.llm_client
        ↓
Parser
  └── Parse LLM JSON output
        ↓
Workflow Plan Validator
  └── Validate Workflow Plan schema and boundaries
        ↓
Workflow Plan Builder
  └── Build Workflow Plan Object
        ↓
Repository Layer
  └── Persist into workflow_plan table
        ↓
Downstream Interface
  └── Pipeline Generation Input
```

---

## 3.3 后端分层架构

```text
API 层
  ↓
Service 编排层
  ↓
Context 构建层
  ↓
Prompt 构建层
  ↓
LLM 调用适配层
  ↓
Parser 解析层
  ↓
Validator 校验层
  ↓
Builder 对象构建层
  ↓
Repository 数据访问层
  ↓
Database 数据层
```

各层职责如下：

| 层级                 | 职责                           |
| ------------------ | ---------------------------- |
| API 层              | 接收 HTTP 请求、调用 Service、返回统一响应 |
| Service 层          | 编排完整 workflow planning 流程    |
| Context Builder    | 读取并整合三个上游模块输出                |
| Prompt Builder     | 构建稳定、受约束的 LLM Prompt         |
| LLM Client Adapter | 复用已有 LLM Client 调用外部模型       |
| Parser             | 解析 LLM 返回 JSON               |
| Validator          | 校验 Workflow Plan 结构与边界       |
| Builder            | 构建最终 Workflow Plan Object    |
| Repository         | 负责 workflow_plan 表 CRUD      |
| Database           | 存储结构化字段与 JSONB 规划结果          |

---

# 4. 模块目录结构设计

建议新增独立业务模块：

```text
backend/app/modules/workflow_planning/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── context_normalizer.py
├── prompt_builder.py
├── llm_client_adapter.py
├── parser.py
├── validator.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

## 4.1 文件职责说明

| 文件                      | 职责                                                        |
| ----------------------- | --------------------------------------------------------- |
| `api.py`                | 定义 Workflow Planning 相关 HTTP 接口                           |
| `schemas.py`            | 定义请求、响应、内部 DTO                                            |
| `service.py`            | 编排上游读取、Prompt 构建、LLM 调用、解析、校验、持久化                         |
| `model.py`              | 定义 `workflow_plan` 数据库表                                   |
| `repository.py`         | 提供 Workflow Plan CRUD                                     |
| `context_builder.py`    | 读取 Task Specification、Task Interpretation、Dataset Profile |
| `context_normalizer.py` | 将上游复杂对象整理为规划所需上下文                                         |
| `prompt_builder.py`     | 构建 LLM Planning Prompt                                    |
| `llm_client_adapter.py` | 复用或适配已有 LLMClient                                         |
| `parser.py`             | 解析 LLM 返回 JSON                                            |
| `validator.py`          | 校验 Workflow Plan Schema 和模块边界                             |
| `builder.py`            | 生成 Workflow Plan Object                                   |
| `enums.py`              | 定义状态、规划模式、策略类型枚举                                          |
| `exceptions.py`         | 定义模块专用异常                                                  |

---

# 5. 技术栈方案

## 5.1 后端技术栈

继续沿用当前系统技术栈：

| 技术     | 推荐方案                 | 说明                          |
| ------ | -------------------- | --------------------------- |
| Web 框架 | FastAPI              | 与当前系统保持一致                   |
| ORM    | SQLModel             | 与前三个模块保持一致                  |
| 数据库    | PostgreSQL 16        | 使用现有数据库                     |
| 灵活字段存储 | JSONB                | 存储复杂 Workflow Plan Object   |
| 数据校验   | Pydantic v2          | 定义请求、响应和 LLM 输出 Schema      |
| 配置管理   | pydantic-settings    | 复用已有 settings               |
| LLM 调用 | httpx + 现有 LLMClient | 复用 Task Interpretation 模块能力 |
| 日志     | logging / structlog  | 记录规划请求、LLM 调用、解析错误          |
| 容器化    | Docker Compose       | 延续现有部署方式                    |
| 数据库迁移  | Alembic              | 后续建议启用                      |

---

## 5.2 LLM 技术选型

本模块应复用当前 `task_interpretation.llm_client.py` 中已有的 OpenAI 兼容接口调用能力。

### 推荐策略

```text
Workflow Planning Module
    ↓
llm_client_adapter.py
    ↓
task_interpretation.llm_client.LLMClient
```

### 原因

1. 避免重复实现 LLM 调用逻辑；
2. 保持 timeout、retry、temperature 等配置一致；
3. 未来若实现多 Provider 切换，只需升级统一 LLM Client；
4. 所有 LLM 调用日志与错误处理风格一致。

---

## 5.3 LLM 调用参数建议

| 参数              | 推荐值                   | 原因                                 |
| --------------- | --------------------- | ---------------------------------- |
| temperature     | 0                     | 保证规划结果稳定                           |
| max_retries     | 2                     | 应对偶发超时或解析失败                        |
| timeout         | 60s                   | Workflow Planning Prompt 较长，需要足够时间 |
| response_format | JSON                  | 后续建议升级为原生 JSON mode                |
| streaming       | false                 | MVP 阶段简化实现                         |
| model           | 使用 settings.LLM_MODEL | 与已有模块统一                            |

---

## 5.4 前端技术栈

继续沿用：

| 技术              | 用途               |
| --------------- | ---------------- |
| React           | 组件展示             |
| TypeScript      | 类型定义             |
| Axios           | API 调用           |
| React Hook Form | 后续用户编辑 plan 时可复用 |
| Zod             | 后续前端校验可复用        |

MVP 阶段主要新增结果展示组件，不需要复杂表单。

---

# 6. 核心数据对象设计

## 6.1 上游输入对象一：Task Specification Object

本模块主要消费：

```text
task_id
task_name
task_description
material_system
prediction_target
task_type
input_type
target_column
evaluation_metric
user_priority
constraints
status
```

使用原则：

1. 只读取，不修改；
2. 只接受 `valid` 或 `valid_with_warning`；
3. 若状态不满足，返回 `TASK_NOT_READY`。

---

## 6.2 上游输入对象二：Task Interpretation Object

本模块主要消费：

```text
interpretation_id
interpreted_task_type
interpreted_input_modality
interpreted_material_domain
interpreted_prediction_target
modeling_intent
planning_hint
constraint_interpretation
recommended_defaults
ambiguities
warnings
confidence_score
```

使用原则：

1. 只读取最新一条；
2. 只接受 `interpreted` 或 `interpreted_with_warning`；
3. 不重新执行任务理解；
4. 对 `ambiguities` 和 `warnings` 只作为规划风险输入。

---

## 6.3 上游输入对象三：Dataset Profile Object

本模块主要消费：

```text
dataset_profile_id
dataset_source
dataset_schema
modality_check
target_profile
data_quality
profiling_summary
workflow_planning_input
status
```

核心输入：

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
  "sample_size_level": "medium",
  "has_missing_values": false,
  "has_duplicates": false,
  "requires_cleaning": false,
  "requires_target_transformation_check": false,
  "quality_level": "good",
  "is_usable_for_ml": true
}
```

使用原则：

1. 只读取最新一条；
2. 只接受 `profiled` 或 `profiled_with_warning`；
3. 必须满足 `is_usable_for_ml = true`；
4. 不重新加载数据，不重新画像。

---

## 6.4 中间对象：Workflow Planning Context

`context_builder.py` 与 `context_normalizer.py` 共同构建该对象。

```json
{
  "task_context": {
    "task_id": "task_xxxxxxxx",
    "task_type": "regression",
    "input_modality": "composition",
    "prediction_target": "band_gap",
    "material_domain": "inorganic crystals",
    "evaluation_metric": "MAE"
  },
  "user_context": {
    "user_priority": ["accuracy", "interpretability"],
    "constraints": [],
    "interpreted_constraints": {}
  },
  "data_context": {
    "dataset_profile_id": "profile_xxxxxxxx",
    "dataset_source": {},
    "dataset_schema": {},
    "target_profile": {},
    "data_quality": {},
    "workflow_planning_input": {}
  },
  "planning_context": {
    "modeling_intent": {},
    "planning_hint": {},
    "recommended_defaults": {},
    "warnings": [],
    "ambiguities": []
  }
}
```

---

## 6.5 输出对象：Workflow Plan Object

```json
{
  "workflow_plan_id": "plan_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "dataset_profile_id": "profile_xxxxxxxx",
  "status": "planned",
  "planning_mode": "llm_guided",
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
  "confidence_score": 0.91,
  "created_at": "2026-05-01T10:00:00",
  "updated_at": "2026-05-01T10:00:00"
}
```

---

# 7. 数据库设计

## 7.1 表名

```text
workflow_plan
```

---

## 7.2 字段设计

| 字段                         | 类型          | 说明                      |
| -------------------------- | ----------- | ----------------------- |
| `id`                       | VARCHAR     | 主键，格式 `plan_xxxxxxxx`   |
| `task_id`                  | VARCHAR     | 关联 Task Specification   |
| `interpretation_id`        | VARCHAR     | 关联 Task Interpretation  |
| `dataset_profile_id`       | VARCHAR     | 关联 Dataset Profile      |
| `status`                   | VARCHAR     | 规划状态                    |
| `planning_mode`            | VARCHAR     | 规划模式，如 `llm_guided`     |
| `task_type`                | VARCHAR     | 任务类型                    |
| `input_modality`           | VARCHAR     | 输入模态                    |
| `primary_metric`           | VARCHAR     | 主评价指标                   |
| `feature_type`             | VARCHAR     | 特征类型                    |
| `validation_strategy`      | VARCHAR     | 验证策略                    |
| `hpo_enabled`              | BOOLEAN     | 是否启用 HPO                |
| `interpretability_enabled` | BOOLEAN     | 是否启用解释性分析               |
| `confidence_score`         | FLOAT       | 规划置信度                   |
| `plan_json`                | JSONB       | 完整 Workflow Plan Object |
| `llm_request_json`         | JSONB       | LLM 请求记录                |
| `llm_response_json`        | JSONB       | LLM 原始响应                |
| `error_message`            | TEXT        | 错误信息                    |
| `created_at`               | TIMESTAMPTZ | 创建时间                    |
| `updated_at`               | TIMESTAMPTZ | 更新时间                    |

---

## 7.3 索引设计

| 索引                                | 说明           |
| --------------------------------- | ------------ |
| `PRIMARY KEY(id)`                 | 主键索引         |
| `INDEX(task_id)`                  | 根据任务查询规划     |
| `INDEX(interpretation_id)`        | 根据任务理解结果查询规划 |
| `INDEX(dataset_profile_id)`       | 根据数据画像查询规划   |
| `INDEX(status)`                   | 按状态筛选        |
| `INDEX(created_at)`               | 查询最新规划       |
| `INDEX(task_id, created_at DESC)` | 查询某任务最新规划    |

---

## 7.4 存储策略

继续沿用当前系统的混合存储策略：

```text
高频查询字段单独建列
+
复杂嵌套对象存入 JSONB
```

高频字段包括：

```text
task_id
interpretation_id
dataset_profile_id
status
task_type
input_modality
primary_metric
feature_type
validation_strategy
hpo_enabled
interpretability_enabled
confidence_score
```

复杂字段包括：

```text
data_strategy
feature_strategy
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
pipeline_generation_input
planning_warnings
planning_assumptions
```

---

# 8. API 设计

## 8.1 创建 Workflow Plan

```text
POST /api/workflow-plans/{task_id}
```

### 功能

根据 `task_id` 读取上游三个模块结果，调用 LLM 生成 Workflow Plan Object。

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

## 8.2 查询 Workflow Plan

```text
GET /api/workflow-plans/{workflow_plan_id}
```

### 功能

根据 `workflow_plan_id` 查询完整 Workflow Plan Object。

---

## 8.3 查询某任务最新 Workflow Plan

```text
GET /api/tasks/{task_id}/workflow-plan
```

### 功能

查询某个 task_id 最新一条 Workflow Plan Object。

### 下游用途

后续模块可以通过该接口获取规划结果：

```text
Pipeline Generation
Pipeline Execution
Report Generation
前端任务详情页
```

---

## 8.4 重新执行 Workflow Planning

```text
POST /api/workflow-plans/{task_id}/rerun
```

### 功能

重新执行工作流规划。

### 原则

1. 不覆盖旧记录；
2. 新增一条 Workflow Plan；
3. 默认查询最新一条；
4. 保留历史版本，便于比较规划差异。

---

# 9. 核心业务数据流

## 9.1 创建 Workflow Plan 完整数据流

```text
用户点击 Run Workflow Planning
    ↓
前端调用 POST /api/workflow-plans/{task_id}
    ↓
workflow_planning/api.py 接收请求
    ↓
workflow_planning/service.py 开始业务编排
    ↓
context_builder.py 读取上游对象
        ├── Task Specification Object
        ├── Latest Task Interpretation Object
        └── Latest Dataset Profile Object
    ↓
检查上游状态
        ├── Task Specification: valid / valid_with_warning
        ├── Task Interpretation: interpreted / interpreted_with_warning
        └── Dataset Profile: profiled / profiled_with_warning
    ↓
检查 Dataset Profile 是否 usable_for_ml
    ↓
context_normalizer.py 构建 Workflow Planning Context
    ↓
prompt_builder.py 构建 system_prompt + user_message
    ↓
llm_client_adapter.py 调用已有 LLMClient
    ↓
parser.py 解析 LLM JSON 输出
    ↓
validator.py 校验 Workflow Plan Schema 和模块边界
    ↓
builder.py 构建 Workflow Plan Object
    ↓
repository.py 写入 workflow_plan 表
    ↓
返回 Workflow Plan Response
```

---

## 9.2 与 Task Specification 模块的数据流

```text
task_id
    ↓
TaskSpecificationRepository.get_by_id(task_id)
    ↓
Task Specification Object
    ↓
校验 status
    ↓
提取任务基础字段
```

本模块只读，不修改 Task Specification。

---

## 9.3 与 Task Interpretation 模块的数据流

```text
task_id
    ↓
TaskInterpretationRepository.get_latest_by_task_id(task_id)
    ↓
Task Interpretation Object
    ↓
校验 status
    ↓
提取 modeling_intent / planning_hint / constraint_interpretation
```

本模块只读，不重新调用任务理解逻辑。

---

## 9.4 与 Dataset Profile 模块的数据流

```text
task_id
    ↓
DatasetProfileRepository.get_latest_by_task_id(task_id)
    ↓
Dataset Profile Object
    ↓
校验 status 和 is_usable_for_ml
    ↓
提取 workflow_planning_input / data_quality / target_profile
```

本模块只读，不重新加载数据、不重新画像。

---

## 9.5 与 Pipeline Generation 模块的数据流

```text
Workflow Plan Object
    ↓
pipeline_generation_input
    ↓
Pipeline Generation Module
```

Pipeline Generation 后续重点消费：

```text
data_strategy
feature_strategy
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
pipeline_generation_input
```

---

# 10. Prompt 架构设计

## 10.1 Prompt Builder 职责

`prompt_builder.py` 只负责构建 Prompt，不调用 LLM，不解析结果。

---

## 10.2 Prompt 组成

推荐 Prompt 分为五部分：

```text
System Role
    ↓
Module Boundary
    ↓
Workflow Planning Context
    ↓
Planning Requirements
    ↓
Output JSON Schema
```

---

## 10.3 System Role

应明确：

```text
You are an expert AutoML workflow planner for materials science.
Your task is to generate a structured machine learning workflow plan.
You must not generate executable code.
You must not perform model training.
You must not fabricate evaluation results.
```

---

## 10.4 Module Boundary

Prompt 中必须明确本模块边界：

1. 只规划，不执行；
2. 不生成 Python 代码；
3. 不加载数据；
4. 不训练模型；
5. 不输出虚构性能指标；
6. 不修改上游对象；
7. 只输出 JSON。

---

## 10.5 Planning Requirements

要求 LLM 必须规划：

```text
data_strategy
feature_strategy
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
pipeline_generation_input
planning_warnings
planning_assumptions
confidence_score
```

---

## 10.6 Output JSON Schema

Prompt 中必须内嵌完整 JSON Schema，强制字段稳定。

推荐必填字段：

```text
task_summary
data_strategy
feature_strategy
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
pipeline_generation_input
planning_warnings
planning_assumptions
llm_reasoning_summary
confidence_score
```

---

# 11. LLM Client Adapter 设计

## 11.1 职责

`llm_client_adapter.py` 负责在 Workflow Planning 模块和已有 LLMClient 之间做适配。

它负责：

1. 复用已有 LLMClient；
2. 传入 workflow planning prompt；
3. 保留 LLM 请求与响应；
4. 统一错误包装；
5. 未来支持更换模型或 provider。

---

## 11.2 为什么不重新实现 LLM Client

当前 Task Interpretation 模块已实现：

1. OpenAI 兼容接口；
2. timeout；
3. retry；
4. temperature；
5. LLM 调用日志；
6. 原始响应返回。

因此 Workflow Planning 模块应复用，而不是复制。

---

## 11.3 后续扩展

未来可将 LLM Client 抽象上移到：

```text
backend/app/shared/llm/
├── __init__.py
├── client.py
├── providers/
│   ├── openai.py
│   ├── qwen.py
│   ├── deepseek.py
│   └── claude.py
└── schemas.py
```

但 MVP 阶段可暂时复用现有 `task_interpretation.llm_client.py`。

---

# 12. Parser 与 Validator 设计

## 12.1 Parser 职责

`parser.py` 负责：

1. 清理 Markdown 代码块；
2. 提取 JSON；
3. 解析为 dict；
4. 解析失败抛出模块专用异常；
5. 可复用 Task Interpretation 模块 parser 的处理思路。

---

## 12.2 Validator 职责

`validator.py` 负责：

1. 校验顶层必填字段；
2. 校验各策略对象是否存在；
3. 校验枚举字段是否合法；
4. 校验 `confidence_score` 是否在 0 到 1；
5. 校验 `planning_warnings` 是否为数组；
6. 校验 `planning_assumptions` 是否为数组；
7. 检查是否出现业务代码；
8. 检查是否出现虚构模型训练指标；
9. 检查是否越界进入 Pipeline Generation 或 Model Training。

---

## 12.3 必须禁止的输出

Validator 应识别并拒绝：

1. 完整 Python 代码；
2. 真实训练结果；
3. 虚构 MAE/RMSE/R² 数值；
4. 已训练模型路径；
5. 实际 Pipeline 执行日志；
6. 对上游数据的修改指令；
7. 超出 Workflow Planning 范围的执行型内容。

---

# 13. Builder 设计

## 13.1 职责

`builder.py` 负责将 validated plan dict 转换为最终 Workflow Plan Object。

---

## 13.2 Builder 需要补充的信息

1. workflow_plan_id；
2. task_id；
3. interpretation_id；
4. dataset_profile_id；
5. planning_mode；
6. status；
7. created_at；
8. updated_at。

---

## 13.3 状态生成规则

| 条件                          | status               |
| --------------------------- | -------------------- |
| 上游状态不满足                     | blocked              |
| LLM 调用失败                    | failed               |
| LLM 输出无法解析                  | failed               |
| Workflow Plan 校验失败          | failed               |
| 成功且无 warnings/assumptions   | planned              |
| 成功但有 warnings 或 assumptions | planned_with_warning |

说明：

MVP 中也可以将 `planning_assumptions` 视为正常产物，不一定导致 warning；但若 assumptions 涉及关键风险，则建议使用 `planned_with_warning`。

---

# 14. 状态管理设计

## 14.1 状态枚举

```text
pending
planning
planned
planned_with_warning
failed
blocked
```

---

## 14.2 状态含义

| 状态                   | 含义             |
| -------------------- | -------------- |
| pending              | 已创建规划任务，尚未开始   |
| planning             | 正在调用 LLM 规划    |
| planned              | 规划成功           |
| planned_with_warning | 规划成功但存在警告或关键假设 |
| failed               | LLM 调用、解析或校验失败 |
| blocked              | 上游状态不满足        |

---

## 14.3 状态流转

```text
收到请求
    ↓
检查上游状态
    ├── 不满足 → blocked
    └── 满足
          ↓
        pending
          ↓
        planning
          ↓
        planned / planned_with_warning / failed
```

MVP 阶段可以同步完成整个流程，不必持久化每个中间状态；但状态枚举应提前定义，便于后续异步任务扩展。

---

# 15. 异常处理设计

## 15.1 异常类型

建议新增模块专用异常：

```text
WorkflowPlanningException
├── WorkflowPlanningContextException
├── WorkflowPlanningUpstreamNotReadyException
├── WorkflowPlanningLLMCallException
├── WorkflowPlanParseException
├── WorkflowPlanValidationException
└── WorkflowPlanNotFoundException
```

---

## 15.2 错误码设计

| 错误码                               | 场景                         |
| --------------------------------- | -------------------------- |
| `TASK_NOT_FOUND`                  | task_id 不存在                |
| `TASK_NOT_READY`                  | Task Specification 状态不允许   |
| `INTERPRETATION_REQUIRED`         | 尚未执行任务理解                   |
| `INTERPRETATION_NOT_READY`        | Task Interpretation 状态不允许  |
| `DATASET_PROFILE_REQUIRED`        | 尚未执行数据画像                   |
| `DATASET_PROFILE_NOT_READY`       | Dataset Profile 状态不允许      |
| `DATASET_NOT_USABLE_FOR_ML`       | 数据不可用于机器学习                 |
| `WORKFLOW_PLANNING_INPUT_MISSING` | 缺少 workflow_planning_input |
| `WORKFLOW_PLANNING_CONTEXT_ERROR` | Planning Context 构建失败      |
| `LLM_CALL_FAILED`                 | LLM 调用失败                   |
| `LLM_OUTPUT_PARSE_ERROR`          | LLM 返回无法解析                 |
| `WORKFLOW_PLAN_VALIDATION_FAILED` | Workflow Plan 校验失败         |
| `WORKFLOW_PLAN_NOT_FOUND`         | Workflow Plan 不存在          |

---

# 16. 配置设计

## 16.1 新增环境变量建议

MVP 阶段可复用现有 LLM 配置，不必新增独立配置。

可选新增：

```text
WORKFLOW_PLANNING_LLM_MODEL=
WORKFLOW_PLANNING_TEMPERATURE=0
WORKFLOW_PLANNING_TIMEOUT=60
WORKFLOW_PLANNING_MAX_RETRIES=2
WORKFLOW_PLANNING_MAX_PROMPT_TOKENS=12000
```

---

## 16.2 配置原则

1. 默认复用全局 LLM 配置；
2. 若后续不同模块需要不同模型，可启用模块级配置；
3. Workflow Planning 的 temperature 应保持为 0；
4. Prompt token 过大时应截断非核心字段，而不是丢失关键上下文。

---

# 17. 前端架构设计

## 17.1 前端目录结构

建议新增：

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
│   ├── WorkflowPlanningWarningList.tsx
│   └── WorkflowPlanJsonViewer.tsx
├── types.ts
└── constants.ts
```

---

## 17.2 前端 API 客户端

新增：

```text
frontend/src/api/workflowPlanningApi.ts
```

封装：

```text
createWorkflowPlan(taskId)
getWorkflowPlan(planId)
getLatestWorkflowPlanByTaskId(taskId)
rerunWorkflowPlan(taskId)
```

---

## 17.3 前端展示内容

MVP 阶段展示：

1. workflow plan 状态；
2. task summary；
3. data strategy；
4. feature strategy；
5. model strategy；
6. validation strategy；
7. evaluation strategy；
8. HPO strategy；
9. interpretability strategy；
10. pipeline generation input；
11. planning warnings；
12. planning assumptions；
13. confidence score；
14. 完整 JSON。

---

# 18. 与后续模块的扩展接口

## 18.1 提供给 Pipeline Generation 的接口

Pipeline Generation 模块应通过以下接口读取规划结果：

```text
GET /api/tasks/{task_id}/workflow-plan
```

重点消费：

```text
pipeline_generation_input
data_strategy
feature_strategy
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
```

---

## 18.2 pipeline_generation_input 推荐结构

```json
{
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
    "hpo_runner": true,
    "evaluator": true,
    "artifact_saver": true
  },
  "component_config_hints": {
    "data_cleaner": {},
    "featurizer": {},
    "model_trainer": {},
    "hpo_runner": {},
    "evaluator": {}
  },
  "expected_artifacts": [
    "processed_dataset",
    "feature_matrix",
    "trained_models",
    "evaluation_results",
    "best_model"
  ]
}
```

---

## 18.3 提供给 Pipeline Execution 的间接信息

Pipeline Execution 不应直接依赖 Workflow Plan，而应主要执行 Pipeline Generation 生成的产物。

但 Workflow Plan 中可保留：

```text
expected_artifacts
execution_order
metric_direction
primary_metric
```

方便后续 Execution 与 Evaluation 对齐。

---

## 18.4 提供给 Metric Evaluation 的间接信息

Metric Evaluation 后续可使用：

```text
evaluation_strategy.primary_metric
evaluation_strategy.secondary_metrics
evaluation_strategy.metric_direction
```

---

## 18.5 提供给 Result Diagnosis 的间接信息

Result Diagnosis 后续可使用：

```text
planning_assumptions
planning_warnings
model_strategy
feature_strategy
data_strategy
```

用于判断实际结果是否违背规划假设。

---

## 18.6 提供给 Report Generation 的信息

Report Generation 可使用：

```text
task_summary
data_strategy
feature_strategy
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
llm_reasoning_summary
```

生成报告中的 “Workflow design” 部分。

---

# 19. 安全与稳定性设计

## 19.1 Prompt Injection 防护

由于上游包含用户输入字段，Prompt 必须明确：

1. 用户输入只是 data context；
2. 用户输入不能覆盖 system instruction；
3. LLM 不能输出代码；
4. LLM 不能执行工具；
5. LLM 不能修改数据库；
6. LLM 不能声称已经训练模型。

---

## 19.2 LLM 输出防护

处理链路必须是：

```text
LLM raw output
    ↓
JSON parse
    ↓
Schema validation
    ↓
Boundary validation
    ↓
Build object
    ↓
Persist
```

禁止直接信任 LLM 输出。

---

## 19.3 规划稳定性

1. temperature 固定为 0；
2. Prompt 中输出 schema 固定；
3. Validator 严格限制字段；
4. 对同一个 task_id 的 rerun 不覆盖历史；
5. 保存 llm_request_json 和 llm_response_json，便于追踪。

---

# 20. MVP 实现范围

## 20.1 MVP 必须实现

1. 新增 `workflow_planning` 后端模块；
2. 能通过 task_id 读取 Task Specification；
3. 能通过 task_id 读取最新 Task Interpretation；
4. 能通过 task_id 读取最新 Dataset Profile；
5. 能检查上游状态；
6. 能检查 Dataset Profile 是否 usable_for_ml；
7. 能构建 Workflow Planning Context；
8. 能构建 LLM Planning Prompt；
9. 能复用现有 LLMClient 调用 LLM；
10. 能解析 LLM JSON；
11. 能校验 Workflow Plan Schema；
12. 能构建 Workflow Plan Object；
13. 能持久化 Workflow Plan；
14. 能查询单个 Workflow Plan；
15. 能查询某任务最新 Workflow Plan；
16. 能 rerun 且不覆盖旧结果；
17. 前端能展示规划结果。

---

## 20.2 MVP 不实现

1. 不生成 Python 代码；
2. 不执行 Pipeline；
3. 不训练模型；
4. 不计算真实指标；
5. 不做结果诊断；
6. 不自动修正 Dataset Profile；
7. 不多轮询问用户；
8. 不生成多套候选规划；
9. 不实现 Agent Loop 动态重规划；
10. 不实现异步任务队列。

---

# 21. 后续演进方向

## 21.1 V2：规则引擎 + LLM 混合规划

将部分稳定规则前置为规则引擎：

```text
Dataset Profile
    ↓
Rule-based Planning Skeleton
    ↓
LLM Refine and Explain
    ↓
Workflow Plan Object
```

适合减少 LLM 不稳定性。

---

## 21.2 V3：多候选 Workflow Plan

支持生成多套方案：

```text
accuracy_first
interpretability_first
efficiency_first
balanced
```

用户可选择后进入 Pipeline Generation。

---

## 21.3 V4：用户确认与编辑

增加：

```text
Workflow Plan
    ↓
User Review / Edit
    ↓
Confirmed Workflow Plan
    ↓
Pipeline Generation
```

---

## 21.4 V5：Agent Loop 动态规划

在后续模型训练和诊断结果出来后，支持：

```text
Evaluation Result
    ↓
LLM Diagnosis
    ↓
Workflow Re-planning
    ↓
New Workflow Plan Version
```

---

# 22. 推荐开发顺序

## 阶段一：后端基础结构

1. 创建 `workflow_planning` 模块目录；
2. 定义 `model.py`；
3. 定义 `schemas.py`；
4. 定义 `repository.py`；
5. 注册 API 路由。

---

## 阶段二：打通上游模块

1. 实现 `context_builder.py`；
2. 查询 Task Specification；
3. 查询最新 Task Interpretation；
4. 查询最新 Dataset Profile；
5. 校验上游状态；
6. 构建 Workflow Planning Context。

---

## 阶段三：LLM 规划链路

1. 实现 `prompt_builder.py`；
2. 实现 `llm_client_adapter.py`；
3. 复用现有 LLMClient；
4. 实现 `parser.py`；
5. 实现 `validator.py`；
6. 实现 `builder.py`。

---

## 阶段四：API 与持久化

1. 实现创建 Workflow Plan 接口；
2. 实现查询 Workflow Plan 接口；
3. 实现查询最新 Workflow Plan 接口；
4. 实现 rerun 接口；
5. 写入 `workflow_plan` 表。

---

## 阶段五：前端展示

1. 新增 `workflowPlanningApi.ts`；
2. 新增 `WorkflowPlanPanel.tsx`；
3. 展示各策略卡片；
4. 展示 warnings / assumptions；
5. 展示完整 JSON；
6. 将按钮接入现有 TaskSpecificationPage 流程。

---

# 23. 总结

LLM-guided Workflow Planning 模块是 MLAgent 中连接“数据画像”与“可执行 Pipeline 生成”的规划中枢。

它的核心输入是：

```text
Task Specification Object
    +
Task Interpretation Object
    +
Dataset Profile Object
```

它的核心输出是：

```text
Workflow Plan Object
    +
pipeline_generation_input
```

它应该回答：

```text
应该如何组织材料机器学习工作流？
数据需要如何处理？
应该采用什么特征策略？
应该考虑哪些模型族？
如何划分训练和验证？
使用哪些评价指标？
是否需要 HPO？
是否需要解释性分析？
Pipeline Generation 下一步应该生成哪些组件？
```

它不应该回答：

```text
代码怎么写？
模型训练结果是多少？
哪个模型最终最好？
评估指标具体是多少？
如何诊断失败结果？
```

架构上应坚持：

1. 独立业务模块；
2. 与前三个模块通过 task_id、interpretation_id、dataset_profile_id 解耦协作；
3. 复用已有 LLM Client；
4. Prompt、Parser、Validator、Builder 分层清晰；
5. 输出 Schema 强约束；
6. 结果可持久化、可查询、可重跑；
7. 为 Pipeline Generation、Execution、Evaluation、Diagnosis 和 Report Generation 预留稳定接口。

