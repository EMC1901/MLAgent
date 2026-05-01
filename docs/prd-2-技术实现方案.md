# LLM-based Task Interpretation 模块架构与技术栈方案

## 1. 模块名称

LLM-based Task Interpretation  
基于大语言模型的任务理解模块

---

## 2. 模块定位

本模块是 MLAgent 系统的第二个业务模块，位于：

```text
Task Input
    ↓
LLM-based Task Interpretation
    ↓
Dataset Loading and Profiling
    ↓
Workflow Planning
    ↓
Pipeline Generation
    ↓
Pipeline Execution
    ↓
Evaluation and Diagnosis
    ↓
Report Generation
````

当前 Task Input 模块已经完成：

1. 用户任务表单收集；
2. 字段标准化；
3. 必填字段校验；
4. 基础合法性校验；
5. Task Specification Object 构建；
6. PostgreSQL 持久化；
7. 通过 task_id 查询任务规格。

因此，本模块不再重复做表单输入、基础字段校验和任务规格构建，而是基于已有 Task Specification Object 进行 LLM 语义理解、任务规范化和建模意图解析。

---

# 3. 总体架构设计

## 3.1 架构目标

LLM-based Task Interpretation 模块的架构目标是：

1. 与 Task Input 模块通过 task_id 自然衔接；
2. 将 Task Specification Object 转换为 Task Interpretation Object；
3. 隔离 LLM 调用逻辑，方便后续更换不同大模型供应商；
4. 保证 LLM 输出可解析、可校验、可持久化；
5. 为后续 Dataset Loading and Profiling、Workflow Planning 模块提供稳定的语义输入；
6. 支持后续多轮任务澄清、任务版本管理、知识库增强等扩展能力。

---

## 3.2 推荐整体架构

```text
Frontend
  └── Task Interpretation Result Panel
        ↓
Backend API Layer
  └── task_interpretation/api.py
        ↓
Service Layer
  └── task_interpretation/service.py
        ↓
Task Specification Adapter
  └── 从 task_specification 模块读取 Task Specification Object
        ↓
Prompt Builder
  └── 构建 LLM Prompt
        ↓
LLM Client
  └── 调用外部 LLM
        ↓
LLM Response Parser
  └── 解析 LLM JSON 输出
        ↓
Interpretation Validator
  └── 校验 LLM 输出合法性
        ↓
Interpretation Builder
  └── 构建 Task Interpretation Object
        ↓
Repository Layer
  └── 写入 task_interpretation 表
        ↓
Downstream Interface
  ├── Dataset Loading Hint
  └── Workflow Planning Hint
```

---

## 3.3 后端分层架构

```text
API 层
  ↓
Service 编排层
  ↓
Domain Components 领域组件层
  ├── Task Specification Adapter
  ├── Prompt Builder
  ├── LLM Client
  ├── Parser
  ├── Validator
  └── Builder
  ↓
Repository 数据访问层
  ↓
Database 数据层
```

---

# 4. 模块目录结构设计

建议新增独立业务模块目录：

```text
backend/app/modules/task_interpretation/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── task_spec_adapter.py
├── prompt_builder.py
├── llm_client.py
├── parser.py
├── validator.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

## 4.1 文件职责说明

| 文件                     | 职责                                                  |
| ---------------------- | --------------------------------------------------- |
| `api.py`               | 定义任务理解相关 HTTP 接口                                    |
| `schemas.py`           | 定义请求体、响应体、内部 DTO                                    |
| `service.py`           | 业务编排中枢，串联任务读取、Prompt 构建、LLM 调用、解析、校验、持久化            |
| `model.py`             | 定义 `task_interpretation` 数据库表                       |
| `repository.py`        | 负责 Task Interpretation 结果的 CRUD                     |
| `task_spec_adapter.py` | 适配 Task Input 模块输出，将 Task Specification 转换为本模块内部上下文 |
| `prompt_builder.py`    | 根据 Task Specification Object 构建稳定 Prompt            |
| `llm_client.py`        | 封装 LLM API 调用，屏蔽模型供应商差异                             |
| `parser.py`            | 解析 LLM 原始返回，提取 JSON                                 |
| `validator.py`         | 校验 LLM 输出是否符合 Task Interpretation Schema            |
| `builder.py`           | 构建最终 Task Interpretation Object                     |
| `enums.py`             | 定义本模块状态、目标类型、模态类型等枚举                                |
| `exceptions.py`        | 定义本模块专用异常                                           |

---

# 5. 技术栈方案

## 5.1 后端技术栈

| 技术       | 推荐方案                | 说明                          |
| -------- | ------------------- | --------------------------- |
| Web 框架   | FastAPI             | 与现有系统保持一致                   |
| ORM      | SQLModel            | 与 Task Input 模块保持一致         |
| 数据库      | PostgreSQL 16       | 继续使用当前数据库                   |
| 灵活字段存储   | JSONB               | 存储复杂 LLM 解释结果               |
| 数据校验     | Pydantic v2         | 定义 LLM 输出 Schema 与 API 响应模型 |
| 配置管理     | pydantic-settings   | 统一管理 LLM API Key、模型名、超时等    |
| HTTP 客户端 | httpx               | 调用外部 LLM API，支持同步/异步        |
| 日志       | logging / structlog | 记录 LLM 请求、响应、错误和耗时          |
| 容器化      | Docker Compose      | 延续当前部署方式                    |
| 数据库迁移    | Alembic             | 后续建议正式启用                    |

---

## 5.2 LLM 技术选型

MVP 阶段建议采用可替换的 LLM Client 抽象，不将具体模型写死在业务逻辑中。

### 推荐抽象方式

```text
LLMClient Interface
  ├── OpenAIClient
  ├── DeepSeekClient
  ├── QwenClient
  ├── ClaudeClient
  └── LocalModelClient
```

### MVP 推荐优先级

| 方案              | 适用场景            | 推荐度  |
| --------------- | --------------- | ---- |
| OpenAI / GPT 系列 | 输出稳定，JSON 遵循能力强 | 高    |
| Qwen / DeepSeek | 国内开发环境更方便，成本较低  | 高    |
| Claude          | 长文本理解强          | 中    |
| 本地模型            | 私有化部署、低成本       | 后续扩展 |

### LLM 调用要求

LLM 输出必须满足：

1. JSON 格式；
2. 字段符合 Task Interpretation Schema；
3. 不输出 Markdown；
4. 不生成代码；
5. 不进入 Workflow Planning；
6. 对不确定内容必须输出 `ambiguities`；
7. 对潜在风险必须输出 `warnings`；
8. 必须输出 `confidence_score`。

---

# 6. 核心数据对象设计

## 6.1 输入对象：Task Specification Object

来源：Task Input 模块。

核心字段包括：

```text
task_id
task_name
task_description
material_system
prediction_target
task_type
dataset_description
input_type
target_column
evaluation_metric
user_priority
constraints
status
missing_fields
validation_messages
created_at
updated_at
```

本模块只接收 `valid` 或 `valid_with_warning` 状态的任务。

---

## 6.2 中间对象：Task Interpretation Context

该对象由 `task_spec_adapter.py` 构建，用于屏蔽 Task Input 模块内部存储细节。

```json
{
  "task_id": "task_xxxxxxxx",
  "task_summary": {
    "task_name": "Band gap prediction",
    "task_description": "Predict experimental band gaps",
    "material_system": "inorganic crystals"
  },
  "ml_task": {
    "task_type": "regression",
    "prediction_target": "experimental band gap",
    "target_column": "band_gap",
    "evaluation_metric": "MAE"
  },
  "data_context": {
    "dataset_description": "matbench_expt_gap",
    "input_type": "composition"
  },
  "user_intent": {
    "user_priority": ["accuracy", "interpretability"],
    "constraints": []
  }
}
```

---

## 6.3 输出对象：Task Interpretation Object

```json
{
  "interpretation_id": "interp_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "status": "interpreted",
  "interpreted_task_type": "regression",
  "interpreted_input_modality": "composition",
  "interpreted_material_domain": "inorganic crystals",
  "interpreted_prediction_target": {
    "raw_target": "experimental band gap",
    "normalized_target": "band_gap",
    "target_category": "electronic_property",
    "target_unit": "eV",
    "target_description": "Predict experimental band gap from composition."
  },
  "modeling_intent": {
    "primary_goal": "property_prediction",
    "secondary_goals": ["interpretability"],
    "optimization_direction": "minimize_error",
    "preferred_metric": "MAE"
  },
  "dataset_intent": {
    "dataset_reference": "matbench_expt_gap",
    "expected_input_columns": ["composition"],
    "expected_target_column": "band_gap",
    "requires_structure_file": false,
    "dataset_loading_hint": {
      "source_type": "public_benchmark",
      "possible_loader": "matbench",
      "needs_file_upload": false
    }
  },
  "planning_hint": {
    "task_family": "supervised_regression",
    "input_representation": "composition_based",
    "requires_feature_engineering": true,
    "requires_model_interpretability": true,
    "suggested_metric_direction": "minimize"
  },
  "constraint_interpretation": {
    "hard_constraints": [],
    "soft_constraints": ["prefer interpretable models"],
    "potential_conflicts": []
  },
  "recommended_defaults": {
    "evaluation_metric": "MAE",
    "validation_strategy": "cross_validation",
    "baseline_requirement": true
  },
  "ambiguities": [],
  "warnings": [],
  "llm_reasoning_summary": "This is a composition-based regression task for predicting experimental band gap.",
  "confidence_score": 0.92,
  "created_at": "2026-04-30T10:00:00",
  "updated_at": "2026-04-30T10:00:00"
}
```

---

# 7. 数据库设计

## 7.1 表名

```text
task_interpretation
```

---

## 7.2 字段设计

| 字段                            | 类型             | 说明                            |
| ----------------------------- | -------------- | ----------------------------- |
| `id`                          | VARCHAR / UUID | 主键，格式如 `interp_xxxxxxxx`      |
| `task_id`                     | VARCHAR        | 外键，关联 `task_specification.id` |
| `status`                      | VARCHAR        | 解释状态                          |
| `interpreted_task_type`       | VARCHAR        | LLM 解释后的任务类型                  |
| `interpreted_input_modality`  | VARCHAR        | LLM 解释后的输入模态                  |
| `interpreted_material_domain` | VARCHAR        | 材料体系                          |
| `confidence_score`            | FLOAT          | 置信度                           |
| `interpretation_json`         | JSONB          | 完整 Task Interpretation Object |
| `llm_request_json`            | JSONB          | LLM 请求记录                      |
| `llm_response_json`           | JSONB          | LLM 原始响应                      |
| `error_message`               | TEXT           | 错误信息                          |
| `created_at`                  | TIMESTAMPTZ    | 创建时间                          |
| `updated_at`                  | TIMESTAMPTZ    | 更新时间                          |

---

## 7.3 索引设计

| 索引                                | 说明             |
| --------------------------------- | -------------- |
| `PRIMARY KEY(id)`                 | 主键索引           |
| `INDEX(task_id)`                  | 根据任务 ID 查询解释结果 |
| `INDEX(status)`                   | 按解释状态筛选        |
| `INDEX(created_at)`               | 查询最新解释结果       |
| `INDEX(task_id, created_at DESC)` | 查询某任务最新解释结果    |

---

## 7.4 存储策略

采用：

```text
结构化高频字段单独建列
+
复杂解释结果存入 JSONB
```

原因：

1. `interpreted_task_type`、`input_modality`、`confidence_score` 后续会高频查询；
2. `modeling_intent`、`dataset_intent`、`planning_hint` 结构复杂，适合存入 JSONB；
3. 便于后续扩展字段，不频繁修改表结构。

---

# 8. API 设计

## 8.1 创建任务理解结果

```text
POST /api/task-interpretations/{task_id}
```

### 功能

根据已有 Task Specification Object 生成 Task Interpretation Object。

### 请求参数

| 参数      | 位置   | 必填 | 说明                    |
| ------- | ---- | -- | --------------------- |
| task_id | path | 是  | Task Input 模块生成的任务 ID |

### 请求体

MVP 阶段可为空。

后续可扩展：

```json
{
  "force_rerun": false,
  "llm_provider": "default",
  "model_name": "default"
}
```

### 响应

```json
{
  "success": true,
  "message": "Task interpretation created successfully.",
  "data": {
    "interpretation_id": "interp_xxxxxxxx",
    "task_id": "task_xxxxxxxx",
    "status": "interpreted",
    "interpreted_task_type": "regression",
    "interpreted_input_modality": "composition",
    "confidence_score": 0.92
  }
}
```

---

## 8.2 查询任务理解结果

```text
GET /api/task-interpretations/{interpretation_id}
```

### 功能

根据 interpretation_id 查询完整解释结果。

---

## 8.3 查询某个 task_id 的最新解释结果

```text
GET /api/tasks/{task_id}/interpretation
```

### 功能

获取某个任务对应的最新 Task Interpretation Object。

### 作用

供后续模块调用，例如：

```text
Dataset Loading 模块
Workflow Planning 模块
前端任务详情页
```

---

## 8.4 重新执行任务理解

```text
POST /api/task-interpretations/{task_id}/rerun
```

### 功能

当 Task Specification 被修改后，重新调用 LLM 生成新的解释结果。

### 设计原则

1. 不覆盖旧结果；
2. 新增一条 interpretation 记录；
3. 默认查询最新一条；
4. 保留历史版本，便于追踪任务理解变化。

---

# 9. 核心业务数据流

## 9.1 创建任务理解结果数据流

```text
用户点击 Run Task Interpretation
    ↓
前端调用 POST /api/task-interpretations/{task_id}
    ↓
api.py 接收请求
    ↓
service.py 开始业务编排
    ↓
task_spec_adapter.py 根据 task_id 读取 Task Specification Object
    ↓
检查 task.status 是否为 valid 或 valid_with_warning
    ↓
构建 Task Interpretation Context
    ↓
prompt_builder.py 构建 LLM Prompt
    ↓
llm_client.py 调用外部 LLM
    ↓
parser.py 解析 LLM JSON 输出
    ↓
validator.py 校验输出 Schema
    ↓
builder.py 构建 Task Interpretation Object
    ↓
repository.py 写入 task_interpretation 表
    ↓
返回解释结果给前端
```

---

## 9.2 与 Task Input 模块的协作

```text
task_specification 表
    ↓
TaskSpecificationRepository.get_by_id(task_id)
    ↓
Task Specification Object
    ↓
Task Specification Adapter
    ↓
Task Interpretation Context
```

本模块不直接修改 Task Input 模块数据，只读取其输出。

---

## 9.3 与 Dataset Loading 模块的协作

本模块向 Dataset Loading 模块提供：

```json
{
  "dataset_intent": {
    "dataset_reference": "matbench_expt_gap",
    "source_type": "public_benchmark",
    "expected_input_columns": ["composition"],
    "expected_target_column": "band_gap",
    "requires_structure_file": false,
    "needs_file_upload": false
  }
}
```

Dataset Loading 模块后续据此判断：

1. 是否使用公开数据集加载器；
2. 是否需要用户上传文件；
3. 需要读取哪些输入列；
4. 目标列是什么；
5. 是否需要 CIF/POSCAR 等结构文件。

---

## 9.4 与 Workflow Planning 模块的协作

本模块向 Workflow Planning 模块提供：

```json
{
  "planning_hint": {
    "task_family": "supervised_regression",
    "input_representation": "composition_based",
    "requires_feature_engineering": true,
    "requires_model_interpretability": true,
    "suggested_metric_direction": "minimize"
  }
}
```

Workflow Planning 模块后续据此制定：

1. 数据预处理策略；
2. 特征工程策略；
3. 候选模型范围；
4. 超参数搜索空间；
5. 验证策略；
6. Pipeline 组合策略。

---

# 10. Prompt 架构设计

## 10.1 Prompt Builder 职责

`prompt_builder.py` 不直接调用 LLM，只负责把 Task Interpretation Context 转换为标准 Prompt。

---

## 10.2 Prompt 组成

推荐 Prompt 由五部分组成：

```text
System Role
    ↓
Module Boundary
    ↓
Task Specification Context
    ↓
Interpretation Requirements
    ↓
Output JSON Schema
```

---

## 10.3 Prompt 内容要求

Prompt 必须明确告诉 LLM：

1. 你是材料机器学习任务理解专家；
2. 你只负责任务理解；
3. 不要生成代码；
4. 不要规划完整 workflow；
5. 不要选择具体模型；
6. 不要假设数据已经加载；
7. 输出必须是严格 JSON；
8. 不确定信息写入 ambiguities；
9. 风险信息写入 warnings；
10. 给出 confidence_score。

---

## 10.4 Prompt 输出 Schema

LLM 输出必须包含：

```text
interpreted_task_type
interpreted_input_modality
interpreted_material_domain
interpreted_prediction_target
modeling_intent
dataset_intent
planning_hint
constraint_interpretation
recommended_defaults
ambiguities
warnings
llm_reasoning_summary
confidence_score
```

---

# 11. LLM Client 设计

## 11.1 设计目标

LLM Client 必须保持独立，不能和业务逻辑耦合。

业务层只关心：

```text
输入 Prompt
↓
返回 LLM 原始结果
```

不关心具体调用的是 OpenAI、Qwen、DeepSeek 还是本地模型。

---

## 11.2 推荐接口抽象

```text
LLMClient
  ├── generate(prompt, response_format)
  ├── provider
  ├── model_name
  ├── timeout
  └── max_retries
```

---

## 11.3 配置项

建议在 `.env` 中新增：

```text
LLM_PROVIDER=openai
LLM_MODEL=gpt-4.1
LLM_API_KEY=xxx
LLM_BASE_URL=xxx
LLM_TIMEOUT=60
LLM_MAX_RETRIES=2
LLM_TEMPERATURE=0
```

---

## 11.4 MVP 推荐参数

| 参数              | 推荐值   | 原因         |
| --------------- | ----- | ---------- |
| temperature     | 0     | 保证输出稳定     |
| max_retries     | 2     | 应对偶发失败     |
| timeout         | 60s   | 避免请求长时间阻塞  |
| response_format | JSON  | 提高输出可解析性   |
| streaming       | false | MVP 阶段简化实现 |

---

# 12. 解析与校验设计

## 12.1 Parser 设计

`parser.py` 负责：

1. 提取 LLM 返回文本；
2. 清理可能的 Markdown 包裹；
3. 解析 JSON；
4. 返回 Python dict；
5. 解析失败时抛出专用异常。

---

## 12.2 Validator 设计

`validator.py` 负责检查：

1. 必填字段是否存在；
2. 枚举值是否合法；
3. `confidence_score` 是否在 0 到 1 之间；
4. `ambiguities` 是否为数组；
5. `warnings` 是否为数组；
6. `interpreted_task_type` 是否与允许类型一致；
7. `interpreted_input_modality` 是否与允许模态一致；
8. 输出中是否混入 workflow planning 级别内容。

---

## 12.3 Builder 设计

`builder.py` 负责：

1. 生成 interpretation_id；
2. 合并 task_id；
3. 填充 created_at、updated_at；
4. 根据 warnings 和 ambiguities 决定最终 status；
5. 构建最终 Task Interpretation Object。

---

# 13. 状态管理设计

## 13.1 状态枚举

```text
pending
interpreting
interpreted
interpreted_with_warning
failed
blocked
```

---

## 13.2 状态含义

| 状态                       | 含义                         |
| ------------------------ | -------------------------- |
| pending                  | 已创建解释任务，尚未调用 LLM           |
| interpreting             | 正在调用 LLM                   |
| interpreted              | 解释成功，且无明显警告                |
| interpreted_with_warning | 解释成功，但存在歧义或警告              |
| failed                   | LLM 调用、解析或校验失败             |
| blocked                  | Task Specification 状态不允许解释 |

---

## 13.3 状态流转

```text
收到解释请求
    ↓
检查 Task Specification 状态
    ├── invalid / incomplete → blocked
    └── valid / valid_with_warning
            ↓
        pending
            ↓
        interpreting
            ↓
        interpreted / interpreted_with_warning / failed
```

---

# 14. 异常处理设计

## 14.1 异常类型

建议新增：

```text
TaskInterpretationException
├── TaskNotReadyException
├── LLMCallException
├── LLMOutputParseException
├── LLMOutputValidationException
└── InterpretationNotFoundException
```

---

## 14.2 错误码设计

| 错误码                           | 场景                         |
| ----------------------------- | -------------------------- |
| `TASK_NOT_FOUND`              | task_id 不存在                |
| `TASK_NOT_READY`              | Task Specification 状态不允许解释 |
| `LLM_CALL_FAILED`             | LLM API 调用失败               |
| `LLM_OUTPUT_PARSE_ERROR`      | LLM 返回无法解析为 JSON           |
| `LLM_OUTPUT_VALIDATION_ERROR` | LLM JSON 不符合 Schema        |
| `INTERPRETATION_NOT_FOUND`    | 查询不到解释结果                   |

---

# 15. 前端架构设计

## 15.1 前端模块目录建议

```text
frontend/src/modules/taskInterpretation/
├── components/
│   ├── TaskInterpretationPanel.tsx
│   ├── InterpretationSummaryCard.tsx
│   ├── InterpretationWarningList.tsx
│   └── InterpretationJsonViewer.tsx
├── hooks/
│   └── useTaskInterpretation.ts
├── types.ts
└── constants.ts
```

---

## 15.2 前端 API 客户端扩展

建议在现有 `frontend/src/api/` 下新增：

```text
taskInterpretationApi.ts
```

封装：

```text
createTaskInterpretation(taskId)
getTaskInterpretation(interpretationId)
getLatestTaskInterpretationByTaskId(taskId)
rerunTaskInterpretation(taskId)
```

---

## 15.3 前端展示内容

MVP 阶段展示：

1. 解释状态；
2. 任务类型；
3. 输入模态；
4. 材料体系；
5. 预测目标规范化结果；
6. 建模意图；
7. 数据集意图；
8. Workflow Planning Hint；
9. 歧义；
10. 警告；
11. 置信度；
12. 原始 JSON 展示。

---

# 16. 与后续模块的扩展接口

## 16.1 提供给 Dataset Loading 的接口

推荐后续 Dataset Loading 模块通过以下接口读取解释结果：

```text
GET /api/tasks/{task_id}/interpretation
```

重点消费字段：

```text
dataset_intent
interpreted_input_modality
interpreted_prediction_target
warnings
ambiguities
```

---

## 16.2 提供给 Workflow Planning 的接口

Workflow Planning 模块重点消费字段：

```text
planning_hint
modeling_intent
constraint_interpretation
recommended_defaults
interpreted_task_type
interpreted_input_modality
```

---

## 16.3 预留下游字段

建议 Task Interpretation Object 中预留：

```json
{
  "dataset_loading_hint": {},
  "workflow_planning_hint": {},
  "agent_context": {}
}
```

其中：

| 字段                       | 作用                |
| ------------------------ | ----------------- |
| `dataset_loading_hint`   | 给数据加载模块使用         |
| `workflow_planning_hint` | 给工作流规划模块使用        |
| `agent_context`          | 给后续 Agent Loop 使用 |

---

# 17. 日志与可观测性设计

## 17.1 需要记录的日志

| 日志内容              | 说明         |
| ----------------- | ---------- |
| task_id           | 当前解释任务     |
| interpretation_id | 当前解释结果 ID  |
| LLM provider      | 使用的大模型供应商  |
| model_name        | 使用的模型      |
| prompt_tokens     | 输入 token 数 |
| completion_tokens | 输出 token 数 |
| latency_ms        | 调用耗时       |
| status            | 解释状态       |
| error_message     | 错误信息       |

---

## 17.2 LLM 请求追踪

建议持久化：

```text
llm_request_json
llm_response_json
```

目的：

1. 方便调试 Prompt；
2. 方便追踪 LLM 输出错误；
3. 方便后续优化任务理解效果；
4. 方便论文实验中展示系统执行 trace。

---

# 18. 安全与稳定性设计

## 18.1 Prompt Injection 防护

由于用户输入会进入 Prompt，需要做基础防护：

1. 用户输入统一作为 data context，而不是 system instruction；
2. Prompt 中明确声明用户字段不可覆盖系统规则；
3. LLM 输出必须经过 Schema 校验；
4. 不允许 LLM 返回可执行代码；
5. 不允许 LLM 修改数据库状态；
6. 不允许 LLM 直接触发后续 Pipeline 执行。

---

## 18.2 LLM 输出防护

必须执行：

```text
LLM raw output
    ↓
JSON parse
    ↓
Schema validation
    ↓
Business validation
    ↓
Build object
    ↓
Persist
```

禁止直接信任 LLM 原始输出。

---

# 19. MVP 实现范围

## 19.1 MVP 必须实现

1. 新增 `task_interpretation` 后端模块；
2. 通过 task_id 读取 Task Specification Object；
3. 检查 Task Specification 状态；
4. 构建 Task Interpretation Context；
5. 构建 Prompt；
6. 调用 LLM；
7. 解析 LLM JSON；
8. 校验输出 Schema；
9. 构建 Task Interpretation Object；
10. 持久化解释结果；
11. 提供创建、查询、重跑 API；
12. 前端可查看解释结果。

---

## 19.2 MVP 不实现

1. 不做多轮澄清；
2. 不做真实数据加载；
3. 不做 Workflow Planning；
4. 不生成 Pipeline 代码；
5. 不执行模型训练；
6. 不做 Agent 自动循环；
7. 不做复杂权限系统；
8. 不做任务队列异步化。

---

# 20. 后续演进方向

## 20.1 V2：用户确认机制

增加：

```text
LLM Interpretation Result
    ↓
用户确认 / 修改
    ↓
Confirmed Task Interpretation Object
```

作用：

1. 提高任务理解可靠性；
2. 避免错误解释直接进入后续模块；
3. 支持用户修正 LLM 对材料任务的理解。

---

## 20.2 V3：知识库增强

引入材料领域知识库：

1. 材料属性 ontology；
2. 常见 Matbench 数据集说明；
3. 常见材料描述符说明；
4. 常见评价指标说明。

形成：

```text
Task Specification
    ↓
Knowledge Retrieval
    ↓
LLM Interpretation
    ↓
Task Interpretation Object
```

---

## 20.3 V4：Agent 化任务理解

将任务理解模块升级为 Agent 子系统：

```text
Think
    ↓
Need clarification?
    ↓
Ask user / infer with confidence
    ↓
Generate interpretation
    ↓
Validate
    ↓
Finish
```

---

# 21. 推荐开发顺序

## 阶段一：后端基础结构

1. 创建 `task_interpretation` 模块目录；
2. 定义 `model.py`；
3. 定义 `schemas.py`；
4. 定义 `repository.py`；
5. 注册 API 路由。

---

## 阶段二：与 Task Input 模块打通

1. 实现 `task_spec_adapter.py`；
2. 根据 task_id 查询 Task Specification；
3. 检查 Task Specification 状态；
4. 构建 Task Interpretation Context。

---

## 阶段三：LLM 调用链路

1. 实现 `prompt_builder.py`；
2. 实现 `llm_client.py`；
3. 实现 `parser.py`；
4. 实现 `validator.py`；
5. 实现 `builder.py`。

---

## 阶段四：API 与持久化

1. 实现创建解释接口；
2. 实现查询解释接口；
3. 实现按 task_id 查询最新解释接口；
4. 实现 rerun 接口；
5. 将结果写入 PostgreSQL。

---

## 阶段五：前端展示

1. 新增 TaskInterpretationPanel；
2. 增加 Run Interpretation 按钮；
3. 展示解释结果；
4. 展示 warnings 和 ambiguities；
5. 展示 JSON 详情。

---

# 22. 总结

LLM-based Task Interpretation 模块应被设计为 Task Input 与后续自动化建模模块之间的语义桥梁。

它的核心职责不是重新收集任务信息，也不是直接规划完整机器学习流程，而是：

```text
Task Specification Object
    ↓
LLM semantic understanding
    ↓
Task Interpretation Object
    ↓
Dataset Loading Hint + Workflow Planning Hint
```

该模块在架构上应坚持：

1. 独立业务模块；
2. 清晰分层；
3. LLM 调用解耦；
4. 输出 Schema 强约束；
5. 结果可持久化；
6. 可追踪、可重跑、可扩展；
7. 为 Dataset Loading、Workflow Planning 和后续 Agent Loop 预留标准接口。

