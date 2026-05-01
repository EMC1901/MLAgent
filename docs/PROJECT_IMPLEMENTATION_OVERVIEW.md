# 项目已实现部分说明文档

> 文档生成日期：2026-05-01
> 项目名称：MLAgent - AI-driven Automated Machine Learning Framework for Materials Science
> 文档用途：帮助后续 AI Coding 大模型和开发者快速理解当前项目已完成的部分

---

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个面向材料科学领域的 AI 驱动自动化机器学习框架。其核心目标是让用户通过结构化表单提交材料机器学习任务需求，系统自动完成从任务理解、数据加载、工作流规划到 Pipeline 生成的全流程自动化。

### 1.2 当前实现阶段

当前项目已完成 **两个核心业务模块** 的端到端实现：

| 模块 | 阶段 | 完成度 |
|------|------|--------|
| **模块一：Task Specification（任务规格录入）** | MVP 已完成 | ~95% |
| **模块二：LLM-based Task Interpretation（基于大模型的任务理解）** | MVP 已完成 | ~90% |

当前尚未实现的后续模块包括：Dataset Loading and Profiling、Workflow Planning、Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis、Report Generation 等。

### 1.3 项目整体架构

```
用户浏览器 (React SPA)
    ↓ HTTP
FastAPI 后端 (Python)
    ↓
PostgreSQL 数据库
    ↓
外部 LLM API (OpenAI / Qwen / DeepSeek 等)
```

---

## 2. 当前目录结构说明

```
c:\projects\MLAgent/
├── backend/                              # 后端 FastAPI 项目
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # FastAPI 应用入口，路由注册、全局异常处理、CORS、启动事件
│   │   ├── modules/                      # 业务模块目录
│   │   │   ├── __init__.py
│   │   │   ├── task_specification/       # 模块一：任务规格录入与规范化
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # API 路由层（4 个接口）
│   │   │   │   ├── schemas.py            # Pydantic 请求/响应模型
│   │   │   │   ├── service.py            # 业务编排中枢
│   │   │   │   ├── model.py              # SQLModel 数据库表定义
│   │   │   │   ├── repository.py         # 数据访问层（CRUD）
│   │   │   │   ├── normalizer.py         # 字段标准化（task_type/input_type/evaluation_metric 映射）
│   │   │   │   ├── validator.py          # 字段完整性与合法性校验
│   │   │   │   └── builder.py            # Task Specification Object 构建器
│   │   │   └── task_interpretation/      # 模块二：LLM 任务理解
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # API 路由层（4 个接口）
│   │   │       ├── schemas.py            # Pydantic 请求/响应模型
│   │   │       ├── service.py            # 业务编排中枢
│   │   │       ├── model.py              # SQLModel 数据库表定义
│   │   │       ├── repository.py         # 数据访问层（CRUD）
│   │   │       ├── task_spec_adapter.py  # 适配 Task Specification 模块输出
│   │   │       ├── prompt_builder.py     # LLM Prompt 构建
│   │   │       ├── llm_client.py         # LLM API 调用封装（httpx）
│   │   │       ├── parser.py             # LLM 响应解析（JSON 提取）
│   │   │       ├── validator.py          # LLM 输出校验
│   │   │       ├── builder.py            # Task Interpretation Object 构建器
│   │   │       ├── enums.py              # 枚举定义
│   │   │       └── exceptions.py         # 模块专用异常
│   │   └── shared/                       # 公共能力
│   │       ├── __init__.py
│   │       ├── common/
│   │       │   ├── __init__.py
│   │       │   ├── response.py           # 统一 API 响应格式（success_response/error_response）
│   │       │   ├── exceptions.py         # 通用异常（BusinessException/NotFoundException 等）
│   │       │   └── enums.py              # 公共枚举（当前为空）
│   │       ├── config/
│   │       │   ├── __init__.py
│   │       │   └── settings.py           # 环境变量配置（pydantic-settings）
│   │       └── database/
│   │           ├── __init__.py
│   │           ├── connection.py         # 数据库 Engine 创建
│   │           └── session.py            # Session 依赖注入
│   ├── .env.example                      # 环境变量模板
│   ├── requirements.txt                  # Python 依赖
│   └── Dockerfile                        # 后端容器化
├── frontend/                             # 前端 React 项目
│   ├── public/
│   │   └── index.html                    # HTML 入口
│   ├── src/
│   │   ├── index.tsx                     # React 应用入口，渲染 TaskSpecificationPage
│   │   ├── api/
│   │   │   ├── taskApi.ts                # Task Specification 模块 API 客户端（axios）
│   │   │   └── taskInterpretationApi.ts  # Task Interpretation 模块 API 客户端
│   │   └── modules/
│   │       ├── taskSpecification/        # 前端任务规格模块
│   │       │   ├── pages/
│   │       │   │   └── TaskSpecificationPage.tsx  # 页面组件
│   │       │   ├── components/
│   │       │   │   ├── TaskSpecificationForm.tsx  # 任务表单（含 Zod 校验、提交、结果展示）
│   │       │   │   └── TaskFieldGroup.tsx         # 表单字段分组容器
│   │       │   └── constants.ts          # 表单选项常量 + Zod Schema
│   │       └── taskInterpretation/       # 前端任务理解模块
│   │           ├── components/
│   │           │   └── TaskInterpretationPanel.tsx # LLM 结果展示面板
│   │           └── types.ts              # TypeScript 类型定义
│   ├── package.json                      # 前端依赖
│   ├── tsconfig.json                     # TypeScript 配置
│   └── Dockerfile                        # 前端容器化
├── docker-compose.yml                    # Docker Compose 编排（db + backend + frontend）
├── .gitignore
└── docs/
    ├── prd-1-mvp.md                      # Task Specification 模块 MVP 需求文档
    ├── prd-1-技术栈.md                    # 技术栈说明
    ├── prd-1-架构.md                      # 目录结构与架构设计文档
    ├── prd-2-技术实现方案.md               # LLM Task Interpretation 模块架构方案
    ├── prd-2.md                          # LLM Task Interpretation 模块需求文档
    └── PROJECT_IMPLEMENTATION_OVERVIEW.md # 本文档
```

---

## 3. 当前系统输入与输出

### 3.1 系统输入

#### 输入一：用户通过前端表单提交任务规格

- **入口**：前端 [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx)
- **输入方式**：结构化表单填写
- **核心字段**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_name | string | 否 | 任务名称 |
| task_description | string | 否 | 任务描述 |
| material_system | string | 否 | 材料体系 |
| prediction_target | string | **是** | 预测目标 |
| task_type | string | **是** | 任务类型（regression/classification/ranking） |
| dataset_description | string | **是** | 数据集描述 |
| input_type | string | **是** | 输入数据类型 |
| target_column | string | **是** | 目标列名 |
| evaluation_metric | string | 否 | 评价指标 |
| user_priority | string[] | 否 | 用户偏好 |
| constraints | string[] | 否 | 约束条件 |

#### 输入二：用户触发 LLM 任务理解

- **入口**：前端 [TaskInterpretationPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskInterpretation/components/TaskInterpretationPanel.tsx) 中的 "Run Interpretation" 按钮
- **输入**：已存在的 task_id（要求 task 状态为 valid 或 valid_with_warning）
- **外部依赖**：LLM API（OpenAI 兼容接口）

### 3.2 系统输出

#### 输出一：Task Specification Object

```json
{
  "task_id": "task_xxxxxxxx",
  "task_name": "Band gap prediction",
  "prediction_target": "experimental band gap",
  "task_type": "regression",
  "dataset_description": "matbench_expt_gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE",
  "status": "valid",
  "missing_fields": [],
  "validation_messages": [],
  "created_at": "2026-05-01T...",
  "updated_at": "2026-05-01T..."
}
```

#### 输出二：Task Interpretation Object

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
    "target_description": "..."
  },
  "modeling_intent": { ... },
  "dataset_intent": { ... },
  "planning_hint": { ... },
  "constraint_interpretation": { ... },
  "recommended_defaults": { ... },
  "ambiguities": [],
  "warnings": [],
  "llm_reasoning_summary": "...",
  "confidence_score": 0.92
}
```

---

## 4. 当前技术栈说明

### 4.1 后端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **FastAPI** | 0.115.6 | Web 框架，提供 RESTful API |
| **Uvicorn** | 0.34.0 | ASGI 服务器 |
| **SQLModel** | 0.0.22 | ORM 框架，定义数据库模型和执行查询 |
| **Pydantic** | 2.10.4 | 数据校验和序列化（请求/响应模型） |
| **pydantic-settings** | 2.7.1 | 环境变量配置管理 |
| **psycopg2-binary** | 2.9.10 | PostgreSQL 数据库驱动 |
| **httpx** | 0.28.1 | HTTP 客户端，用于调用 LLM API |
| **python-dotenv** | 1.0.1 | .env 文件加载 |
| **Alembic** | 1.14.1 | 数据库迁移工具（已安装但未启用） |

### 4.2 前端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **React** | 18.3.1 | UI 框架 |
| **TypeScript** | 5.7.2 | 类型安全 |
| **React Hook Form** | 7.54.2 | 表单状态管理 |
| **Zod** | 3.24.1 | 前端表单校验 Schema |
| **@hookform/resolvers** | 3.10.0 | React Hook Form + Zod 集成 |
| **Axios** | 1.7.9 | HTTP 客户端 |
| **react-scripts** | 5.0.1 | Create React App 构建工具 |

### 4.3 基础设施

| 技术 | 版本 | 作用 |
|------|------|------|
| **PostgreSQL** | 16 (Alpine) | 关系型数据库，使用 JSONB 存储灵活字段 |
| **Docker Compose** | 3.8 | 容器编排（db + backend + frontend 三服务） |

### 4.4 各技术承担的作用

- **FastAPI + Pydantic**：后端 API 层，负责接收请求、数据校验、返回统一格式响应
- **SQLModel + PostgreSQL**：数据持久化层，使用 JSONB 存储复杂嵌套对象
- **httpx**：LLM 外部服务调用层，支持超时、重试、错误处理
- **React + TypeScript**：前端 SPA，提供表单填写和结果展示
- **React Hook Form + Zod**：前端表单校验，与后端校验规则保持一致
- **Docker Compose**：一键启动完整开发环境

---

## 5. 已实现功能模块

### 5.1 模块一：Task Specification（任务规格录入）

#### 5.1.1 功能一：任务表单展示与提交

- **相关文件**：
  - 前端：[TaskSpecificationPage.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/pages/TaskSpecificationPage.tsx)、[TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx)、[constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts)
  - 后端：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)（POST /api/tasks）
- **输入**：用户填写的表单字段
- **处理逻辑**：
  1. 前端通过 Zod Schema 进行表单校验
  2. 提交到 POST /api/tasks
  3. 后端生成 task_id（格式：`task_` + 8 位 uuid hex）
  4. 调用 normalizer 标准化字段
  5. 调用 validator 校验字段
  6. 调用 builder 构建 Task Specification Object
  7. 通过 repository 写入数据库
- **输出**：TaskSpecificationResponse（含 task_id、status、missing_fields、validation_messages）
- **完成度**：100%

#### 5.1.2 功能二：字段标准化

- **相关文件**：[normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py)
- **输入**：原始表单字段
- **处理逻辑**：
  - `task_type`：映射 "Regression" → "regression" 等
  - `input_type`：映射 "Chemical composition" → "composition" 等
  - `evaluation_metric`：映射 "Mean Absolute Error" → "MAE" 等
  - `user_priority`：标准化优先级选项
  - 字符串字段去除前后空格
- **输出**：标准化后的字段字典
- **完成度**：100%

#### 5.1.3 功能三：必填字段完整性检查

- **相关文件**：[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 中的 `check_required_fields()`
- **输入**：标准化后的任务字段
- **处理逻辑**：检查 prediction_target、task_type、dataset_description、input_type、target_column 是否缺失
- **输出**：missing_fields 列表 + validation_messages 列表
- **完成度**：100%

#### 5.1.4 功能四：基础合法性校验

- **相关文件**：[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 中的 `check_evaluation_metric_compatibility()` 和 `check_input_dataset_consistency()`
- **输入**：标准化后的任务字段
- **处理逻辑**：
  - 任务类型与评价指标匹配校验（regression → MAE/RMSE/R2，classification → Accuracy/F1/ROC-AUC）
  - 输入类型与数据集描述一致性校验（structure 类型需要 CIF/POSCAR 等结构文件提示）
- **输出**：validation_messages 列表
- **完成度**：100%

#### 5.1.5 功能五：查询任务规格

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)（GET /api/tasks/{task_id}）
- **输入**：task_id
- **处理逻辑**：通过 repository 查询数据库，组装为 TaskSpecificationResponse
- **输出**：完整任务规格对象
- **完成度**：100%

#### 5.1.6 功能六：更新任务规格

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)（PUT /api/tasks/{task_id}）
- **输入**：task_id + 更新字段
- **处理逻辑**：合并旧字段和新字段 → 重新 normalizer → 重新 validator → 重新 builder → 更新数据库
- **输出**：更新后的任务规格对象
- **完成度**：100%

#### 5.1.7 功能七：重新校验任务规格

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)（POST /api/tasks/{task_id}/validate）
- **输入**：task_id
- **处理逻辑**：从数据库读取任务 → 重新执行 validate → 返回 ValidationResultResponse
- **输出**：校验结果（status、missing_fields、validation_messages、warnings）
- **完成度**：100%

#### 5.1.8 数据库持久化

- **相关文件**：[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py)
- **表名**：`task_specification`
- **结构化字段**：id、task_name、task_type、prediction_target、dataset_description、input_type、target_column、evaluation_metric、status、created_at、updated_at
- **JSONB 字段**：task_spec_json（存储完整任务对象，含 user_priority、constraints、missing_fields 等）
- **完成度**：100%

---

### 5.2 模块二：LLM-based Task Interpretation（基于大模型的任务理解）

#### 5.2.1 功能一：创建任务理解结果

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py)（POST /api/task-interpretations/{task_id}）
- **输入**：task_id（可选：force_rerun、llm_provider、model_name）
- **处理逻辑**：
  1. 从 task_specification 模块读取 Task Specification
  2. 检查 task 状态是否为 valid 或 valid_with_warning
  3. 通过 task_spec_adapter 转换为 Task Interpretation Context
  4. 通过 prompt_builder 构建 LLM Prompt
  5. 通过 llm_client 调用外部 LLM API
  6. 通过 parser 解析 LLM JSON 输出
  7. 通过 validator 校验输出 Schema
  8. 通过 builder 构建 Task Interpretation Object
  9. 写入 task_interpretation 表
- **输出**：TaskInterpretationResponse
- **完成度**：100%

#### 5.2.2 功能二：查询任务理解结果

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py)
  - GET /api/task-interpretations/{interpretation_id}
  - GET /api/tasks/{task_id}/interpretation（查询某任务的最新理解结果）
- **输入**：interpretation_id 或 task_id
- **输出**：TaskInterpretationResponse
- **完成度**：100%

#### 5.2.3 功能三：重新执行任务理解

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/api.py)（POST /api/task-interpretations/{task_id}/rerun）
- **输入**：task_id
- **处理逻辑**：不覆盖旧结果，新增一条 interpretation 记录
- **输出**：新的 TaskInterpretationResponse
- **完成度**：100%

#### 5.2.4 LLM 调用封装

- **相关文件**：[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)
- **输入**：system_prompt + user_message
- **处理逻辑**：
  - 使用 httpx 调用 OpenAI 兼容接口（`{base_url}/chat/completions`）
  - 支持 temperature=0、timeout、max_retries
  - 超时重试机制
  - 401/403 错误不重试
  - 日志记录请求和响应
- **输出**：LLM 原始文本
- **完成度**：100%（但仅实现了 OpenAI 兼容接口调用，未实现多 Provider 切换）

#### 5.2.5 Prompt 构建

- **相关文件**：[prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py)
- **输入**：Task Interpretation Context
- **处理逻辑**：
  - System Prompt：定义角色为材料机器学习任务理解专家，明确输出规则
  - User Message：包含任务规格 JSON + 输出 JSON Schema
  - 输出 Schema 包含 12 个必填字段，使用 JSON Schema 格式约束
- **输出**：(system_prompt, user_message) 元组
- **完成度**：100%

#### 5.2.6 LLM 输出解析与校验

- **相关文件**：[parser.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/parser.py)、[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/validator.py)
- **parser 处理逻辑**：
  - 清理 Markdown 代码块包裹（```json ... ```）
  - JSON 解析
  - 解析失败抛出 LLMOutputParseException
- **validator 处理逻辑**：
  - 检查 12 个必填顶层字段
  - 检查 interpreted_task_type 是否在允许集合中
  - 检查 interpreted_input_modality 是否在允许集合中
  - 检查 target_category 是否在允许集合中
  - 检查 primary_goal 是否在允许集合中
  - 检查 confidence_score 是否在 0~1 之间
  - 检查 ambiguities 和 warnings 是否为数组
- **完成度**：100%

#### 5.2.7 Task Specification 适配器

- **相关文件**：[task_spec_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/task_spec_adapter.py)
- **输入**：TaskSpecification 数据库模型
- **处理逻辑**：
  - 检查 task 状态是否为 valid 或 valid_with_warning，否则抛出 TaskNotReadyException
  - 将 Task Specification 转换为 Task Interpretation Context（含 task_summary、ml_task、data_context、user_intent 四个子对象）
- **输出**：Context 字典
- **完成度**：100%

#### 5.2.8 数据库持久化

- **相关文件**：[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/repository.py)
- **表名**：`task_interpretation`
- **结构化字段**：id、task_id（索引）、status（索引）、interpreted_task_type、interpreted_input_modality、interpreted_material_domain、confidence_score、created_at（索引）、updated_at、error_message
- **JSONB 字段**：interpretation_json（完整解释对象）、llm_request_json（请求记录）、llm_response_json（原始响应）
- **完成度**：100%

---

### 5.3 公共基础设施

| 组件 | 文件 | 功能 | 完成度 |
|------|------|------|--------|
| 统一响应格式 | [response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py) | success_response / error_response | 100% |
| 通用异常 | [exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py) | BusinessException / NotFoundException / ValidationException / DatabaseException | 100% |
| 配置管理 | [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) | pydantic-settings 读取 .env | 100% |
| 数据库连接 | [connection.py](file:///c:/projects/MLAgent/backend/app/shared/database/connection.py) | create_engine | 100% |
| Session 注入 | [session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py) | get_session 依赖注入 | 100% |
| 全局异常处理 | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | BusinessException → 400, Exception → 500 | 100% |
| CORS 配置 | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | 允许 http://localhost:3000 | 100% |
| 自动建表 | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | startup 时 SQLModel.metadata.create_all | 100% |
| 健康检查 | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | GET /health | 100% |

---

## 6. 系统数据流与调用链路

### 6.1 完整数据流：从用户输入到 LLM 理解输出

```
[用户浏览器]
    ↓ 填写表单
[TaskSpecificationForm.tsx]
    ↓ Zod 前端校验
    ↓ POST /api/tasks
[api.py::create_task()]
    ↓ 调用
[service.py::create_task()]
    ├── 生成 task_id
    ├── 调用 normalizer.normalize_fields()          → 标准化字段
    ├── 调用 validator.validate()                    → 完整性 + 合法性校验
    ├── 调用 builder.build_task_specification()      → 构建任务对象
    └── 调用 repository.create()                     → 写入 task_specification 表
    ↓ 返回 TaskSpecificationResponse
[前端展示结果]
    ↓ 用户点击 "Run Interpretation"
[TaskInterpretationPanel.tsx]
    ↓ POST /api/task-interpretations/{task_id}
[api.py::create_task_interpretation()]
    ↓ 调用
[service.py::create_interpretation()]
    ├── task_repo.get_by_id()                        → 读取 Task Specification
    ├── task_spec_adapter.adapt_task_spec()          → 转换为 Context
    ├── prompt_builder.build_prompt()                → 构建 Prompt
    ├── llm_client.generate()                        → 调用外部 LLM API
    ├── parser.parse_llm_response()                  → 解析 JSON
    ├── validator.validate_interpretation()          → 校验输出 Schema
    ├── builder.build_interpretation()               → 构建解释对象
    └── interp_repo.create()                         → 写入 task_interpretation 表
    ↓ 返回 TaskInterpretationResponse
[前端展示 LLM 理解结果]
```

### 6.2 更新任务数据流

```
[用户修改表单]
    ↓ PUT /api/tasks/{task_id}
[service.py::update_task()]
    ├── repository.get_by_id()                       → 读取原任务
    ├── 合并旧字段和新字段
    ├── normalizer.normalize_fields()                → 重新标准化
    ├── validator.validate()                         → 重新校验
    ├── builder.build_task_specification()           → 重新构建
    └── repository.update()                          → 更新数据库
```

### 6.3 重新执行任务理解数据流

```
[用户点击 "Re-run Interpretation"]
    ↓ POST /api/task-interpretations/{task_id}/rerun
[service.py::rerun_interpretation()]
    → 直接调用 create_interpretation()               → 新增记录，不覆盖旧结果
```

### 6.4 数据库自动初始化

```
[uvicorn 启动]
    ↓
[main.py::on_startup()]
    ↓
[SQLModel.metadata.create_all(engine)]
    → 自动创建 task_specification 表
    → 自动创建 task_interpretation 表
```

---

## 7. 核心代码与关键设计说明

### 7.1 分层架构

项目严格遵循分层架构设计：

```
API 层（api.py）
    ↓ 接收请求，调用 service，返回响应
Service 层（service.py）
    ↓ 业务编排，串联各组件
Domain Components（normalizer/validator/builder/prompt_builder/llm_client/parser）
    ↓ 具体业务规则
Repository 层（repository.py）
    ↓ 数据库 CRUD
Database 层（model.py）
    ↓ 表结构定义
```

### 7.2 数据模型设计

#### TaskSpecification 表

- 使用 **SQLModel** 定义，继承 SQLModel 和 table=True
- 采用 **混合存储策略**：高频查询字段单独建列，灵活字段存入 JSONB
- 主键为 VARCHAR 类型（task_xxxxxxxx 格式），非自增 ID

#### TaskInterpretation 表

- 同样采用混合存储策略
- task_id 字段建立索引，支持按任务查询最新解释
- 保存 LLM 原始请求和响应，便于调试和追溯

### 7.3 状态管理

#### Task Specification 状态

| 状态 | 含义 | 触发条件 |
|------|------|----------|
| received | 初始状态 | 刚创建，尚未校验 |
| valid | 校验通过 | 必填字段完整 + 无冲突 |
| incomplete | 缺少必填字段 | check_required_fields 发现缺失 |
| invalid | 字段存在冲突 | 如 regression + Accuracy |
| valid_with_warning | 通过但有警告 | 如未指定 evaluation_metric |

#### Task Interpretation 状态

| 状态 | 含义 | 触发条件 |
|------|------|----------|
| pending | 已创建，尚未调用 LLM | 根据代码推测，当前未使用此状态 |
| interpreting | 正在调用 LLM | 根据代码推测，当前未使用此状态 |
| interpreted | 解释成功 | 无 ambiguities 和 warnings |
| interpreted_with_warning | 解释成功但有警告 | 存在 ambiguities 或 warnings |
| failed | LLM 调用/解析/校验失败 | 异常发生时 |
| blocked | Task Specification 状态不允许解释 | task 状态非 valid/valid_with_warning |

### 7.4 异常处理体系

```
Exception (Python 内置)
    └── BusinessException (shared/common/exceptions.py)
            ├── ValidationException
            ├── NotFoundException
            ├── DatabaseException
            └── TaskInterpretationException (task_interpretation/exceptions.py)
                    ├── TaskNotReadyException
                    ├── LLMCallException
                    ├── LLMOutputParseException
                    ├── LLMOutputValidationException
                    └── InterpretationNotFoundException
```

全局异常处理器在 [main.py](file:///c:/projects/MLAgent/backend/app/main.py) 中注册：
- BusinessException → HTTP 400
- Exception → HTTP 500

### 7.5 配置管理

通过 [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) 使用 pydantic-settings 管理：

```python
APP_NAME, APP_ENV, DEBUG, DATABASE_URL, CORS_ORIGINS
LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL
LLM_TIMEOUT, LLM_MAX_RETRIES, LLM_TEMPERATURE
```

所有配置从 `.env` 文件读取，有合理的默认值。

### 7.6 LLM 调用设计

- 使用 **OpenAI 兼容接口**（`{base_url}/chat/completions`）
- 通过环境变量可切换不同 Provider（理论上）
- 当前实际只实现了单一调用方式，未实现 Provider 接口抽象
- temperature=0 保证输出稳定性
- 支持超时重试（默认 2 次）
- 401/403 错误立即终止重试

### 7.7 前端设计

- 使用 **React Hook Form** 管理表单状态
- 使用 **Zod** 定义前端校验 Schema，与后端校验规则对应
- 表单提交后展示结果，包含 status 颜色标识
- 当 task 状态为 valid 或 valid_with_warning 时，自动展示 TaskInterpretationPanel
- 使用内联样式（inline styles），未引入 UI 组件库

### 7.8 接口汇总

| 方法 | 路径 | 模块 | 功能 |
|------|------|------|------|
| POST | /api/tasks | Task Specification | 创建任务规格 |
| GET | /api/tasks/{task_id} | Task Specification | 查询任务规格 |
| PUT | /api/tasks/{task_id} | Task Specification | 更新任务规格 |
| POST | /api/tasks/{task_id}/validate | Task Specification | 重新校验任务规格 |
| POST | /api/task-interpretations/{task_id} | Task Interpretation | 创建任务理解 |
| GET | /api/task-interpretations/{interpretation_id} | Task Interpretation | 查询理解结果 |
| GET | /api/tasks/{task_id}/interpretation | Task Interpretation | 查询任务最新理解 |
| POST | /api/task-interpretations/{task_id}/rerun | Task Interpretation | 重新执行理解 |
| GET | /health | 公共 | 健康检查 |

---

## 8. 当前未完成部分与后续开发建议

### 8.1 尚未实现的功能模块

根据 PRD 规划的完整流程，以下模块尚未实现：

| 模块 | 优先级 | 说明 |
|------|--------|------|
| **Dataset Loading and Profiling** | 高 | 根据 dataset_intent 加载数据集，分析数据质量 |
| **Workflow Planning** | 高 | 根据 planning_hint 制定 ML 工作流策略 |
| **Pipeline Generation** | 高 | 生成可执行的 ML Pipeline 代码 |
| **Pipeline Execution** | 中 | 执行 Pipeline，训练模型 |
| **Metric Evaluation** | 中 | 计算模型评估指标 |
| **Result Diagnosis** | 中 | 分析模型结果，诊断问题 |
| **Workflow Refinement** | 低 | 根据诊断结果优化工作流 |
| **Report Generation** | 低 | 生成科研报告 |

### 8.2 半成品与待完善部分

#### 8.2.1 LLM Provider 抽象未实现

- **当前状态**：[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py) 中虽然读取了 `settings.LLM_PROVIDER`，但实际只实现了 OpenAI 兼容接口调用
- **建议**：实现 LLMClient 接口抽象，支持 OpenAI、Qwen、DeepSeek、Claude 等不同 Provider

#### 8.2.2 Alembic 数据库迁移未启用

- **当前状态**：requirements.txt 已安装 alembic，但未初始化迁移脚本
- **当前做法**：startup 时 `SQLModel.metadata.create_all()` 自动建表
- **建议**：正式环境应启用 Alembic 管理表结构变更

#### 8.2.3 日志系统未配置

- **当前状态**：llm_client.py 中使用了 `logging.getLogger()`，但未配置日志格式和输出
- **建议**：在 main.py 或 settings.py 中配置 logging 或 structlog

#### 8.2.4 前端缺少路由系统

- **当前状态**：[index.tsx](file:///c:/projects/MLAgent/frontend/src/index.tsx) 直接渲染 TaskSpecificationPage，未使用 React Router
- **建议**：引入 react-router-dom，支持多页面导航

#### 8.2.5 前端缺少独立的结果查询页面

- **当前状态**：只能在提交表单后查看结果，无法通过 task_id 单独查询已有任务
- **建议**：新增任务详情页面，支持通过 task_id 查询和展示

#### 8.2.6 缺少单元测试和集成测试

- **当前状态**：项目中无任何测试文件
- **建议**：为 normalizer、validator、parser 等纯函数模块优先编写单元测试

#### 8.2.7 前端 UI 组件库未引入

- **当前状态**：使用内联样式，无 UI 组件库
- **建议**：引入 Ant Design / Material-UI 等组件库提升开发效率和一致性

#### 8.2.8 缺少用户认证和权限管理

- **当前状态**：无任何认证机制
- **建议**：后续生产环境需要引入 JWT 或 OAuth

### 8.3 潜在问题

| 问题 | 位置 | 说明 |
|------|------|------|
| target_column 校验过于严格 | [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py)::check_required_fields | 当前无条件要求 target_column，但 PRD 规定仅在使用自定义表格数据时必填 |
| 前端 constraints 处理 | [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) | 前端将 constraints 按换行分割为数组，但 Zod Schema 定义为 string 类型 |
| LLM 超时时间 | [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) | 默认 60 秒，对于复杂 LLM 调用可能不够 |
| 数据库连接池 | [connection.py](file:///c:/projects/MLAgent/backend/app/shared/database/connection.py) | 未显式配置连接池参数 |
| 前端 API 超时 | [taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) | 设置为 120 秒，但错误提示中写的是 15 秒，存在不一致 |

---

## 9. 给后续 AI Coding 大模型的开发提示

### 9.1 继续开发时应优先阅读的文件

| 优先级 | 文件 | 原因 |
|--------|------|------|
| **必读** | [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | 理解应用入口、路由注册、全局异常处理 |
| **必读** | [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) | 理解所有配置项 |
| **必读** | [response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py) + [exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py) | 理解统一响应和异常格式 |
| **必读** | [service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) | 理解业务编排模式 |
| **必读** | [service.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/service.py) | 理解 LLM 调用编排模式 |
| **选读** | [normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py) + [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) | 理解字段标准化和校验规则 |
| **选读** | [prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/prompt_builder.py) | 理解 Prompt 构建方式 |
| **选读** | [docker-compose.yml](file:///c:/projects/MLAgent/docker-compose.yml) | 理解部署架构 |

### 9.2 开发新模块时应遵循的模式

新增业务模块（如 Dataset Loading）时，请严格遵循现有模式：

```
backend/app/modules/new_module/
├── __init__.py
├── api.py                # FastAPI 路由，只负责接请求、调 service、回响应
├── schemas.py            # Pydantic 请求/响应模型
├── service.py            # 业务编排中枢
├── model.py              # SQLModel 数据库表定义
├── repository.py         # CRUD 操作
├── normalizer.py         # （如需要）字段标准化
├── validator.py          # （如需要）业务规则校验
├── builder.py            # （如需要）对象构建
├── enums.py              # （如需要）枚举定义
└── exceptions.py         # （如需要）模块专用异常
```

### 9.3 不要重复实现的功能

- **统一响应格式**：使用 `success_response()` 和 `error_response()`（[response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py)）
- **异常处理**：继承 `BusinessException` 或使用已有异常类（[exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)）
- **数据库连接**：使用 `get_session()` 依赖注入（[session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py)）
- **配置读取**：使用 `settings` 对象（[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)）
- **task_id 生成**：使用 `task_{uuid.uuid4().hex[:8]}` 格式
- **LLM 调用**：复用 `LLMClient`（[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)）
- **前端 API 客户端**：复用 [taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) 中的 axios 实例

### 9.4 需要注意的边界

- **API 层不写业务逻辑**：api.py 只负责路由和响应转换
- **Service 层不写具体规则**：规则放到 normalizer.py / validator.py
- **Repository 层不判断业务状态**：只负责 CRUD
- **Builder 层不判断规则**：只负责对象组装
- **模块间通过接口交互**：不直接访问其他模块的 repository 或 model
- **shared/ 只放跨模块复用内容**：模块专用逻辑不要放到 shared

### 9.5 数据库设计注意事项

- 使用 SQLModel 定义模型，继承 `SQLModel, table=True`
- 高频查询字段单独建列，复杂嵌套数据存入 JSONB
- 主键使用 VARCHAR 类型（业务 ID），非自增
- 添加 created_at 和 updated_at 时间戳字段
- 需要按条件查询的字段添加 index=True

### 9.6 前端开发注意事项

- 使用 React Hook Form + Zod 进行表单管理
- API 调用复用 [taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) 中的 axios 实例（baseURL 已配置）
- TypeScript 类型定义放在模块目录下的 types.ts 中
- 常量定义放在 constants.ts 中
- 新模块的 API 调用函数添加到 api/ 目录

### 9.7 测试建议

- 优先为 normalizer、validator、parser 等纯函数模块编写单元测试
- 使用 pytest 作为后端测试框架（需安装）
- 前端可使用 Jest + React Testing Library

---

> 本文档基于对项目中所有现有代码文件的实际分析编写，所有引用均指向真实存在的文件、函数和接口。文档内容反映了截至 2026-05-01 的项目实际状态。
