# 项目已实现部分说明文档

> 文档生成日期：2026-05-02
> 项目名称：MLAgent - AI-driven Automated Machine Learning Framework for Materials Science
> 文档用途：帮助后续 AI Coding 大模型和开发者快速理解当前项目已经完成的部分

---

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个面向材料科学领域的 AI 驱动自动化机器学习框架。其核心目标是让用户通过结构化表单提交材料机器学习任务需求，系统自动完成从任务理解、数据加载、工作流规划到 Pipeline 生成的全流程自动化。

### 1.2 当前实现阶段

当前项目已完成 **四个核心业务模块** 的端到端实现：

| 模块 | 阶段 | 完成度 |
|------|------|--------|
| **模块一：Task Specification（任务规格录入）** | MVP 已完成 | ~95% |
| **模块二：LLM-based Task Interpretation（基于大模型的任务理解）** | MVP 已完成 | ~90% |
| **模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）** | MVP 已完成 | ~90% |
| **模块四：Workflow Planning（工作流规划）** | MVP 已完成 | ~90% |

当前尚未实现的后续模块包括：Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis、Report Generation 等。

### 1.3 项目整体架构

```
用户浏览器 (React SPA)
    ↓ HTTP
FastAPI 后端 (Python)
    ↓
PostgreSQL 数据库
    ↓
外部 LLM API (OpenAI / Qwen / DeepSeek 等)
    ↓
外部数据集 (Matbench / 用户上传文件)
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
│   │   │   ├── task_interpretation/      # 模块二：LLM 任务理解
│   │   │   │   ├── __init__.py
│   │   │   │   ├── api.py                # API 路由层（4 个接口）
│   │   │   │   ├── schemas.py            # Pydantic 请求/响应模型
│   │   │   │   ├── service.py            # 业务编排中枢
│   │   │   │   ├── model.py              # SQLModel 数据库表定义
│   │   │   │   ├── repository.py         # 数据访问层（CRUD）
│   │   │   │   ├── task_spec_adapter.py  # 适配 Task Specification 模块输出
│   │   │   │   ├── prompt_builder.py     # LLM Prompt 构建
│   │   │   │   ├── llm_client.py         # LLM API 调用封装（httpx）
│   │   │   │   ├── parser.py             # LLM 响应解析（JSON 提取）
│   │   │   │   ├── validator.py          # LLM 输出校验
│   │   │   │   ├── builder.py            # Task Interpretation Object 构建器
│   │   │   │   ├── enums.py              # 枚举定义
│   │   │   │   └── exceptions.py         # 模块专用异常
│   │   │   └── dataset_profile/          # 模块三：数据集加载、检查与画像
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # API 路由层（5 个接口 + 文件上传）
│   │   │       ├── schemas.py            # Pydantic 请求/响应模型
│   │   │       ├── service.py            # 业务编排中枢
│   │   │       ├── model.py              # SQLModel 数据库表定义
│   │   │       ├── repository.py         # 数据访问层（CRUD）
│   │   │       ├── context_builder.py    # 构建 Dataset Loading Context
│   │   │       ├── source_resolver.py    # 数据源识别
│   │   │       ├── profiler.py           # 数据画像汇总
│   │   │       ├── builder.py            # Dataset Profile Object 构建器
│   │   │       ├── enums.py              # 枚举定义
│   │   │       ├── exceptions.py         # 模块专用异常
│   │   │       ├── loaders/              # 数据加载器
│   │   │       │   ├── __init__.py
│   │   │       │   ├── base_loader.py    # 抽象基类
│   │   │       │   ├── matbench_loader.py# Matbench 数据集加载器
│   │   │       │   └── file_loader.py    # 用户上传文件加载器
│   │   │       └── checkers/             # 数据检查器
│   │   │           ├── __init__.py
│   │   │           ├── schema_checker.py # Schema 检查
│   │   │           ├── modality_checker.py# 模态一致性检查
│   │   │           ├── quality_checker.py# 数据质量检查
│   │   │           └── target_checker.py # 目标变量画像
│   │   │   └── workflow_planning/        # 模块四：工作流规划
│   │   │       ├── __init__.py
│   │   │       ├── api.py                # API 路由层（4 个接口）
│   │   │       ├── schemas.py            # Pydantic 请求/响应模型
│   │   │       ├── service.py            # 业务编排中枢
│   │   │       ├── model.py              # SQLModel 数据库表定义
│   │   │       ├── repository.py         # 数据访问层（CRUD）
│   │   │       ├── context_builder.py    # 构建上游上下文（Task + Interpretation + Profile）
│   │   │       ├── prompt_builder.py     # LLM Prompt 构建
│   │   │       ├── llm_client_adapter.py # LLM 调用适配器（复用模块二的 LLMClient）
│   │   │       ├── parser.py             # LLM 响应解析（JSON 提取）
│   │   │       ├── validator.py          # LLM 输出校验（含禁止内容检测）
│   │   │       ├── builder.py            # Workflow Plan Object 构建器
│   │   │       ├── enums.py              # 枚举定义（WorkflowPlanStatus）
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
│   │   │   ├── taskInterpretationApi.ts  # Task Interpretation 模块 API 客户端
│   │   │   ├── datasetProfileApi.ts      # Dataset Profile 模块 API 客户端
│   │   │   └── workflowPlanningApi.ts    # Workflow Planning 模块 API 客户端
│   │   └── modules/
│   │       ├── taskSpecification/        # 前端任务规格模块
│   │       │   ├── pages/
│   │       │   │   └── TaskSpecificationPage.tsx  # 页面组件
│   │       │   ├── components/
│   │       │   │   ├── TaskSpecificationForm.tsx  # 任务表单（含 Zod 校验、提交、结果展示）
│   │       │   │   └── TaskFieldGroup.tsx         # 表单字段分组容器
│   │       │   └── constants.ts          # 表单选项常量 + Zod Schema
│   │       ├── taskInterpretation/       # 前端任务理解模块
│   │       │   ├── components/
│   │       │   │   └── TaskInterpretationPanel.tsx # LLM 结果展示面板
│   │       │   └── types.ts              # TypeScript 类型定义
│   │       └── datasetProfile/           # 前端数据集画像模块
│   │           ├── components/
│   │           │   ├── DatasetProfilePanel.tsx     # 画像结果展示面板
│   │           │   └── FileUpload.tsx              # 文件上传组件（拖拽/点击）
│   │           └── types.ts              # TypeScript 类型定义
│   │       └── workflowPlanning/         # 前端工作流规划模块
│   │           ├── components/
│   │           │   └── WorkflowPlanPanel.tsx       # 工作流规划结果展示面板
│   │           └── types.ts              # TypeScript 类型定义
│   ├── package.json                      # 前端依赖
│   ├── tsconfig.json                     # TypeScript 配置
│   └── Dockerfile                        # 前端容器化
├── docker-compose.yml                    # Docker Compose 编排（db + backend + frontend 三服务）
├── .gitignore
└── docs/
    ├── prd-1-mvp.md                      # Task Specification 模块 MVP 需求文档
    ├── prd-1-技术栈.md                    # 技术栈说明
    ├── prd-1-架构.md                      # 目录结构与架构设计文档
    ├── prd-2-技术实现方案.md               # LLM Task Interpretation 模块架构方案
    ├── prd-2.md                          # LLM Task Interpretation 模块需求文档
    ├── prd-3-技术实现方案.md               # Dataset Profile 模块架构方案
    ├── prd-3.md                          # Dataset Profile 模块需求文档
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

#### 输入三：用户上传数据集文件

- **入口**：前端 [FileUpload.tsx](file:///c:/projects/MLAgent/frontend/src/modules/datasetProfile/components/FileUpload.tsx) 拖拽或点击上传
- **支持格式**：CSV、XLSX、XLS
- **限制**：文件大小不超过 `DATASET_MAX_FILE_SIZE_MB`（默认 100MB）

#### 输入四：用户触发数据集画像

- **入口**：前端 [DatasetProfilePanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/datasetProfile/components/DatasetProfilePanel.tsx) 中的 "Run Dataset Profiling" 按钮
- **输入**：已存在的 task_id（要求 task 状态为 valid/valid_with_warning，且存在 interpreted/interpreted_with_warning 状态的 interpretation）
- **可选输入**：uploaded_file_id（用户上传的文件 ID）

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

#### 输出三：Dataset Profile Object

```json
{
  "dataset_profile_id": "profile_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "status": "profiled",
  "dataset_source": {
    "source_type": "public_benchmark",
    "dataset_reference": "matbench_expt_gap",
    "loader": "matbench"
  },
  "dataset_schema": {
    "n_samples": 4604,
    "n_columns": 2,
    "columns": [...],
    "input_columns": ["composition"],
    "target_column": "band_gap"
  },
  "modality_check": {
    "expected_input_modality": "composition",
    "detected_input_modality": "composition",
    "is_consistent": true,
    "messages": []
  },
  "target_profile": {
    "target_column": "band_gap",
    "task_type": "regression",
    "dtype": "float",
    "missing_count": 0,
    "missing_ratio": 0.0,
    "min": 0.0,
    "max": 11.7,
    "mean": 1.82,
    "std": 1.65,
    "skewness": 1.21,
    "outlier_count": 28
  },
  "data_quality": {
    "missing_values": { "total_missing": 0, "columns_with_missing": [] },
    "duplicates": { "duplicate_rows": 0, "duplicate_input_samples": 0 },
    "invalid_rows": { "count": 0, "examples": [] },
    "warnings": [],
    "errors": []
  },
  "profiling_summary": {
    "is_loadable": true,
    "is_usable_for_ml": true,
    "sample_size_level": "medium",
    "quality_level": "good",
    "main_issues": [],
    "recommended_next_step": "ready_for_workflow_planning"
  },
  "workflow_planning_input": {
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
| **pandas** | 2.2.3 | 表格数据处理、统计分析 |
| **numpy** | 2.2.0 | 数值计算、目标变量统计 |
| **openpyxl** | 3.1.5 | Excel 文件读取支持 |

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
| **ajv** | 8.20.0 | JSON Schema 校验（预留） |

### 4.3 基础设施

| 技术 | 版本 | 作用 |
|------|------|------|
| **PostgreSQL** | 16 (Alpine) | 关系型数据库，使用 JSONB 存储灵活字段 |
| **Docker Compose** | 3.8 | 容器编排（db + backend + frontend 三服务） |

### 4.4 各技术承担的作用

- **FastAPI + Pydantic**：后端 API 层，负责接收请求、数据校验、返回统一格式响应
- **SQLModel + PostgreSQL**：数据持久化层，使用 JSONB 存储复杂嵌套对象
- **httpx**：LLM 外部服务调用层，支持超时、重试、错误处理
- **pandas + numpy**：数据集加载、检查、画像分析的核心计算引擎
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
- **输入**：TaskSpecification 模型对象
- **处理逻辑**：
  - 检查 task 状态是否为 valid 或 valid_with_warning，否则抛出 TaskNotReadyException
  - 提取 task_summary、ml_task、data_context、user_intent 四个子上下文
  - 转换为 LLM Prompt 可消费的字典格式
- **输出**：Task Interpretation Context 字典
- **完成度**：100%

#### 5.2.8 模块专用异常体系

- **相关文件**：[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/exceptions.py)
- **异常类型**：
  - TaskInterpretationException（基类）
  - TaskNotReadyException（任务状态不满足）
  - LLMCallException（LLM 调用失败）
  - LLMOutputParseException（LLM 输出解析失败）
  - LLMOutputValidationException（LLM 输出校验失败）
  - InterpretationNotFoundException（理解结果不存在）
- **完成度**：100%

#### 5.2.9 数据库持久化

- **相关文件**：[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/repository.py)
- **表名**：`task_interpretation`
- **结构化字段**：id、task_id、status、interpreted_task_type、interpreted_input_modality、interpreted_material_domain、confidence_score、error_message、created_at、updated_at
- **JSONB 字段**：interpretation_json（完整理解对象）、llm_request_json、llm_response_json
- **完成度**：100%

---

### 5.3 模块三：Dataset Loading, Checking, and Profiling（数据集加载与画像）

#### 5.3.1 功能一：文件上传

- **相关文件**：
  - 前端：[FileUpload.tsx](file:///c:/projects/MLAgent/frontend/src/modules/datasetProfile/components/FileUpload.tsx)
  - 后端：[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py)（POST /api/dataset-profiles/upload）
- **输入**：用户上传的 CSV/XLSX/XLS 文件
- **处理逻辑**：
  1. 校验文件扩展名（.csv/.xlsx/.xls）
  2. 校验文件大小（不超过 DATASET_MAX_FILE_SIZE_MB）
  3. 生成 file_id（格式：`file_` + 8 位 uuid hex + 扩展名）
  4. 保存到服务器上传目录
  5. 使用 pandas 读取文件
  6. 返回文件基本信息（行数、列数、列名、前 N 行预览）
- **输出**：DatasetFileUploadResponse
- **完成度**：100%

#### 5.3.2 功能二：创建数据集画像

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py)（POST /api/dataset-profiles/{task_id}）
- **输入**：task_id（可选：uploaded_file_id、uploaded_file_path、max_preview_rows）
- **处理逻辑**：
  1. 通过 context_builder 读取上游 Task Specification 和 Task Interpretation
  2. 检查上游状态（task 需 valid/valid_with_warning，interpretation 需 interpreted/interpreted_with_warning）
  3. 通过 source_resolver 识别数据来源（public_benchmark / uploaded_file / unknown）
  4. 选择对应 Loader（MatbenchLoader / FileLoader）
  5. 加载数据为 pandas DataFrame
  6. 执行 schema_checker（列存在性、重复列名、全空列）
  7. 执行 modality_checker（输入模态一致性检测）
  8. 执行 quality_checker（缺失值、重复行、非法值、常量列、高缺失率列）
  9. 执行 target_checker（目标变量分布分析，regression/classification 不同策略）
  10. 通过 profiler 汇总所有检查结果
  11. 通过 builder 构建 Dataset Profile Object
  12. 写入 dataset_profile 表
- **输出**：DatasetProfileResponse
- **完成度**：100%

#### 5.3.3 功能三：查询数据集画像

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py)
  - GET /api/dataset-profiles/{dataset_profile_id}
  - GET /api/tasks/{task_id}/dataset-profile（查询某任务的最新画像）
- **输入**：dataset_profile_id 或 task_id
- **输出**：DatasetProfileResponse
- **完成度**：100%

#### 5.3.4 功能四：重新执行数据集画像

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py)（POST /api/dataset-profiles/{task_id}/rerun）
- **输入**：task_id
- **处理逻辑**：不覆盖旧结果，新增一条 profile 记录
- **输出**：新的 DatasetProfileResponse
- **完成度**：100%

#### 5.3.5 功能五：数据预览

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/api.py)（GET /api/dataset-profiles/{dataset_profile_id}/preview）
- **输入**：dataset_profile_id
- **处理逻辑**：从 preview_json 中读取前 N 行预览数据
- **输出**：DatasetPreviewResponse（含 columns、rows、total_rows、preview_rows）
- **完成度**：100%

#### 5.3.6 数据源识别

- **相关文件**：[source_resolver.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/source_resolver.py)
- **输入**：dataset_intent、dataset_description、uploaded_file_id、uploaded_file_path
- **处理逻辑**：
  - 优先检查是否有上传文件 ID/路径 → source_type = "uploaded_file"
  - 检查 dataset_loading_hint.source_type → "public_benchmark"
  - 检查 dataset_reference/description 中是否包含 "matbench" → "public_benchmark"
  - 检查 description 中是否包含 "csv/xlsx/excel/file/upload" → "uploaded_file"
  - 否则 → "unknown"
- **输出**：source_resolution 字典（含 source_type、dataset_reference、loader_name、is_supported）
- **完成度**：100%

#### 5.3.7 数据加载器

- **相关文件**：
  - [base_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/base_loader.py)（抽象基类）
  - [matbench_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/matbench_loader.py)
  - [file_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/file_loader.py)
- **MatbenchLoader 处理逻辑**：
  - 尝试导入 matbench 包加载真实数据集
  - 若 matbench 未安装，使用内置的已知数据集 schema 生成模拟数据（最多 200 行）
  - 已知数据集：matbench_expt_gap、matbench_mp_e_form、matbench_log_gvrh、matbench_log_kvrh
- **FileLoader 处理逻辑**：
  - 根据 file_path 或 file_id 查找上传文件
  - 校验文件扩展名和大小
  - 使用 pandas.read_csv 或 pandas.read_excel 读取
  - 返回 DataFrame 和加载结果字典
- **完成度**：100%（MatbenchLoader 的模拟数据生成是 MVP 阶段的权宜之计）

#### 5.3.8 数据检查器

- **Schema 检查**：[schema_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/schema_checker.py)
  - 检查目标列是否存在（支持大小写不敏感匹配）
  - 检查输入列是否存在
  - 检查重复列名
  - 检查全空列
- **Modality 检查**：[modality_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/modality_checker.py)
  - 根据列名和数据内容检测输入模态（composition/structure/descriptor/text/mixed）
  - 对 composition 类型使用正则表达式验证化学式格式
  - 比较检测到的模态与期望模态是否一致
- **Quality 检查**：[quality_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/quality_checker.py)
  - 缺失值统计（总数、涉及列）
  - 目标列缺失检查
  - 重复行检查
  - 重复输入样本检查
  - 非法值检查（空字符串）
  - 常量列检查
  - 高缺失率列检查（>50%）
  - 小样本警告（<100）
- **Target 检查**：[target_checker.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/checkers/target_checker.py)
  - Regression：min/max/mean/median/std/skewness/outlier_count（IQR 方法）
  - Classification：class_count/class_distribution/majority_class_ratio/is_imbalanced（>80% 判定为不平衡）
- **完成度**：100%

#### 5.3.9 数据画像汇总

- **相关文件**：[profiler.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/profiler.py)
- **处理逻辑**：
  - 汇总所有检查结果，判断数据质量等级（good/fair/poor/unusable）
  - 判断样本规模等级（very_small/small/medium/large）
  - 判断数据是否可用于机器学习
  - 构建 workflow_planning_input（为后续模块准备的输入）
  - 推荐下一步操作（ready_for_workflow_planning / needs_cleaning / needs_review / blocked）
- **完成度**：100%

#### 5.3.10 数据库持久化

- **相关文件**：[model.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/repository.py)
- **表名**：`dataset_profile`
- **结构化字段**：id、task_id、interpretation_id、status、source_type、dataset_reference、loader_name、n_samples、n_columns、input_modality、target_column、quality_level、is_usable_for_ml、error_message、created_at、updated_at
- **JSONB 字段**：profile_json（完整画像对象）、preview_json（数据预览）
- **完成度**：100%

---

### 5.4 模块四：Workflow Planning（工作流规划）

#### 5.4.1 功能一：创建工作流规划

- **相关文件**：
  - 前端：[WorkflowPlanPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/workflowPlanning/components/WorkflowPlanPanel.tsx)
  - 后端：[api.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/api.py)（POST /api/workflow-plans/{task_id}）
- **输入**：task_id（可选：planning_mode、llm_provider、model_name）
- **前置条件**：
  - Task 状态必须为 valid 或 valid_with_warning
  - 必须存在 interpreted 或 interpreted_with_warning 状态的 interpretation
  - 必须存在 profiled 或 profiled_with_warning 状态的 dataset profile
  - dataset profile 的 is_usable_for_ml 必须为 true
  - dataset profile 中必须包含 workflow_planning_input
- **处理逻辑**：
  1. 通过 context_builder 读取上游 Task Specification、Task Interpretation 和 Dataset Profile
  2. 检查上游状态是否满足条件，否则抛出 UpstreamNotReadyException
  3. 通过 prompt_builder 构建 LLM Prompt（含 System Prompt + User Message + JSON Schema）
  4. 通过 llm_client_adapter 调用 LLM API（复用模块二的 LLMClient）
  5. 通过 parser 解析 LLM 返回的 JSON（清理 Markdown 代码块包裹）
  6. 通过 validator 校验输出（含 13 个必填顶层字段、枚举值校验、禁止内容检测）
  7. 通过 builder 构建 Workflow Plan Object
  8. 写入 workflow_plan 表
- **输出**：WorkflowPlanResponse
- **完成度**：100%

#### 5.4.2 功能二：查询工作流规划

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/api.py)
  - GET /api/workflow-plans/{workflow_plan_id}
  - GET /api/tasks/{task_id}/workflow-plan（查询某任务的最新规划）
- **输入**：workflow_plan_id 或 task_id
- **输出**：WorkflowPlanResponse
- **完成度**：100%

#### 5.4.3 功能三：重新执行工作流规划

- **相关文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/api.py)（POST /api/workflow-plans/{task_id}/rerun）
- **输入**：task_id
- **处理逻辑**：不覆盖旧结果，新增一条 plan 记录
- **输出**：新的 WorkflowPlanResponse
- **完成度**：100%

#### 5.4.4 上游上下文构建

- **相关文件**：[context_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/context_builder.py)
- **输入**：task_id
- **处理逻辑**：
  - 从 task_specification 表读取任务规格
  - 从 task_interpretation 表读取最新 interpretation
  - 从 dataset_profile 表读取最新 profile
  - 检查各模块状态是否满足前置条件
  - 组装 task_context、interpretation_context、data_context 三个子上下文
- **输出**：Workflow Planning Context 字典
- **完成度**：100%

#### 5.4.5 LLM Prompt 构建

- **相关文件**：[prompt_builder.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/prompt_builder.py)
- **处理逻辑**：
  - System Prompt：定义角色为 AutoML 工作流规划专家，明确 10 条关键边界规则（不执行、不生成代码、不伪造结果等）
  - User Message：包含 Task Context + Interpretation Context + Data Context + 输出 JSON Schema
  - 输出 JSON Schema 包含 13 个必填顶层字段，使用 JSON Schema 格式约束
- **输出**：(system_prompt, user_message) 元组
- **完成度**：100%

#### 5.4.6 LLM 调用适配器

- **相关文件**：[llm_client_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/llm_client_adapter.py)
- **处理逻辑**：
  - 复用模块二的 LLMClient（[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)）
  - 调用 generate() 方法获取 LLM 原始响应
  - 记录请求信息（provider、model、system_prompt、user_message）
  - 调用失败时抛出 WorkflowPlanningLLMCallException
- **完成度**：100%

#### 5.4.7 LLM 输出解析与校验

- **相关文件**：[parser.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/parser.py)、[validator.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/validator.py)
- **parser 处理逻辑**：
  - 清理 Markdown 代码块包裹（```json ... ```）
  - JSON 解析
  - 解析失败抛出 WorkflowPlanParseException
- **validator 处理逻辑**：
  - 检查 13 个必填顶层字段
  - 检查各子对象（task_summary、data_strategy、feature_strategy 等）的必填字段
  - 检查枚举值（task_type、input_modality、split_strategy、search_method、budget_level、metric_direction）
  - 检查 confidence_score 是否在 0~1 之间
  - 检查数组字段类型
  - **禁止内容检测**：检测是否包含可执行代码（import pandas、def train、model.fit 等）或伪造的训练结果（MAE of、RMSE of 等）
- **完成度**：100%

#### 5.4.8 模块专用异常体系

- **相关文件**：[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/exceptions.py)
- **异常类型**：
  - WorkflowPlanningException（基类）
  - WorkflowPlanNotFoundException（规划结果不存在）
  - UpstreamNotReadyException（上游模块状态不满足）
  - WorkflowPlanningLLMCallException（LLM 调用失败）
  - WorkflowPlanParseException（LLM 输出解析失败）
  - WorkflowPlanValidationException（LLM 输出校验失败）
- **完成度**：100%

#### 5.4.9 数据库持久化

- **相关文件**：[model.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/repository.py)
- **表名**：`workflow_plan`
- **结构化字段**：id、task_id、interpretation_id、dataset_profile_id、status、planning_mode、task_type、input_modality、primary_metric、feature_type、validation_strategy、hpo_enabled、interpretability_enabled、confidence_score、error_message、created_at、updated_at
- **JSONB 字段**：plan_json（完整规划对象）、llm_request_json、llm_response_json
- **完成度**：100%

#### 5.4.10 前端展示

- **相关文件**：[WorkflowPlanPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/workflowPlanning/components/WorkflowPlanPanel.tsx)、[types.ts](file:///c:/projects/MLAgent/frontend/src/modules/workflowPlanning/types.ts)、[workflowPlanningApi.ts](file:///c:/projects/MLAgent/frontend/src/api/workflowPlanningApi.ts)
- **功能**：
  - "Run Workflow Planning" 和 "Re-run Planning" 按钮
  - 结果展示包含：Task Summary、Data Strategy、Feature Strategy、Model Strategy、Validation Strategy、Evaluation Strategy、HPO Strategy、Interpretability Strategy、Pipeline Generation Input、LLM Reasoning Summary、Planning Warnings、Planning Assumptions
  - 完整 JSON 展示
- **完成度**：100%

---

## 6. 系统数据流与调用链路

### 6.1 完整端到端数据流

```
用户浏览器
    ↓
[1] 填写并提交任务规格表单
    ↓ POST /api/tasks
[2] TaskSpecificationService.create_task()
    ├── normalize_fields()          # 字段标准化
    ├── validate()                  # 字段校验
    ├── build_task_specification()  # 构建对象
    └── TaskSpecificationRepository.create()  # 持久化
    ↓
[3] 返回 TaskSpecificationResponse（含 task_id、status）
    ↓
[4] 用户点击 "Run Interpretation"
    ↓ POST /api/task-interpretations/{task_id}
[5] TaskInterpretationService.create_interpretation()
    ├── TaskSpecificationRepository.get_by_id()      # 读取任务规格
    ├── adapt_task_spec()                            # 转换为 LLM 上下文
    ├── build_prompt()                               # 构建 LLM Prompt
    ├── LLMClient.generate()                         # 调用 LLM API
    ├── parse_llm_response()                         # 解析 JSON
    ├── validate_interpretation()                    # 校验 Schema
    ├── build_interpretation()                       # 构建对象
    └── TaskInterpretationRepository.create()        # 持久化
    ↓
[6] 返回 TaskInterpretationResponse
    ↓
[7] 用户上传数据集文件（可选）
    ↓ POST /api/dataset-profiles/upload
[8] upload_dataset_file()
    ├── 校验文件扩展名和大小
    ├── 保存到上传目录
    ├── pandas 读取文件
    └── 返回文件信息和预览
    ↓
[9] 用户点击 "Run Dataset Profiling"
    ↓ POST /api/dataset-profiles/{task_id}
[10] DatasetProfileService.create_profile()
    ├── build_dataset_loading_context()    # 构建上游上下文
    ├── resolve_source()                   # 识别数据来源
    ├── MatbenchLoader.load() 或 FileLoader.load()  # 加载数据
    ├── check_schema()                     # Schema 检查
    ├── check_modality()                   # 模态检查
    ├── check_quality()                    # 质量检查
    ├── check_target()                     # 目标变量画像
    ├── aggregate_profiling_summary()      # 汇总画像
    ├── build_workflow_planning_input()    # 构建下游输入
    ├── build_dataset_profile()            # 构建对象
    └── DatasetProfileRepository.create()  # 持久化
    ↓
[11] 返回 DatasetProfileResponse
    ↓
[12] 用户点击 "Run Workflow Planning"
    ↓ POST /api/workflow-plans/{task_id}
[13] WorkflowPlanningService.create_plan()
    ├── build_workflow_planning_context()    # 读取上游三个模块输出
    ├── build_prompt()                       # 构建 LLM Prompt
    ├── WorkflowPlanningLLMAdapter.generate()# 调用 LLM API
    ├── parse_llm_response()                 # 解析 JSON
    ├── validate_workflow_plan()             # 校验 Schema + 禁止内容
    ├── build_workflow_plan()                # 构建对象
    └── WorkflowPlanRepository.create()      # 持久化
    ↓
[14] 返回 WorkflowPlanResponse
```

### 6.2 模块间依赖关系

```
Task Specification 模块
    ↓ 被读取
Task Interpretation 模块（依赖 Task Specification 输出）
    ↓ 被读取
Dataset Profile 模块（依赖 Task Specification + Task Interpretation 输出）
    ↓ 被读取
Workflow Planning 模块（依赖 Task Specification + Task Interpretation + Dataset Profile 输出）
    ↓ 输出
Pipeline Generation 模块（后续开发）
```

### 6.3 前端组件渲染链路

```
TaskSpecificationPage
    └── TaskSpecificationForm
        ├── 表单提交成功后
        └── 渲染 TaskInterpretationPanel（当 status 为 valid/valid_with_warning）
            └── 渲染 DatasetProfilePanel（当 status 为 valid/valid_with_warning）
                └── FileUpload 组件
                └── 渲染 WorkflowPlanPanel（当 profile 状态为 profiled/profiled_with_warning）
```

---

## 7. 核心代码与关键设计说明

### 7.1 接口设计

#### 统一响应格式

- **相关文件**：[response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py)
- **结构**：所有 API 返回 `{ "success": bool, "message": str, "data": Any, "error_code": str | None }`
- **成功响应**：`success_response(message, data)`
- **错误响应**：`error_response(message, error_code, data)`

#### 全局异常处理

- **相关文件**：[main.py](file:///c:/projects/MLAgent/backend/app/main.py)
- **BusinessException**：返回 400 状态码 + error_response
- **Exception**：返回 500 状态码 + "Internal server error"

#### CORS 配置

- **相关文件**：[main.py](file:///c:/projects/MLAgent/backend/app/main.py)、[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)
- **配置项**：`CORS_ORIGINS`（默认 `["http://localhost:3000"]`）

### 7.2 数据模型设计

#### 混合存储策略

所有四个业务模块都采用相同的混合存储策略：

- **高频查询字段**：作为独立列存储（如 task_type、status、target_column）
- **复杂嵌套对象**：存入 JSONB 列（如 task_spec_json、interpretation_json、profile_json、plan_json）
- **优势**：兼顾查询性能和扩展灵活性

#### ID 生成规则

| 模块 | ID 格式 | 示例 |
|------|---------|------|
| Task Specification | `task_` + 8 位 uuid hex | `task_a1b2c3d4` |
| Task Interpretation | `interp_` + 8 位 uuid hex | `interp_e5f6g7h8` |
| Dataset Profile | `profile_` + 8 位 uuid hex | `profile_i9j0k1l2` |
| Workflow Plan | `plan_` + 8 位 uuid hex | `plan_m3n4o5p6` |
| Uploaded File | `file_` + 8 位 uuid hex + 扩展名 | `file_q7r8s9t0.csv` |

### 7.3 状态管理

#### Task Specification 状态

| 状态 | 含义 |
|------|------|
| received | 刚接收，尚未校验 |
| incomplete | 缺少必填字段 |
| invalid | 字段校验不通过 |
| valid | 校验通过 |
| valid_with_warning | 校验通过但有警告 |
| updated | 更新后状态 |

#### Task Interpretation 状态

| 状态 | 含义 |
|------|------|
| pending | 待执行 |
| interpreted | 解释完成 |
| interpreted_with_warning | 解释完成但有警告/歧义 |
| failed | LLM 调用或校验失败 |

#### Dataset Profile 状态

| 状态 | 含义 |
|------|------|
| pending | 待执行 |
| profiled | 画像完成 |
| profiled_with_warning | 画像完成但有警告 |
| failed | 加载或画像失败 |
| blocked | 上游状态不满足 |

#### Workflow Plan 状态

| 状态 | 含义 |
|------|------|
| pending | 待执行 |
| planned | 规划完成 |
| planned_with_warning | 规划完成但有警告/假设 |
| failed | LLM 调用、解析或校验失败 |

### 7.4 异常处理体系

#### 通用异常（shared 层）

- **相关文件**：[exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)
- **BusinessException**：业务异常基类（含 message 和 error_code）
- **ValidationException**：校验异常
- **NotFoundException**：资源不存在
- **DatabaseException**：数据库异常

#### 模块专用异常

- **Task Interpretation 模块**：[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/exceptions.py)
  - TaskNotReadyException、LLMCallException、LLMOutputParseException、LLMOutputValidationException、InterpretationNotFoundException
- **Dataset Profile 模块**：[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/exceptions.py)
  - DatasetProfileNotFoundException、DatasetContextBuildException、DatasetSourceUnresolvedException、DatasetSourceUnsupportedException、DatasetLoadException、DatasetSchemaException、DatasetModalityMismatchException
- **Workflow Planning 模块**：[exceptions.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/exceptions.py)
  - WorkflowPlanNotFoundException、UpstreamNotReadyException、WorkflowPlanningLLMCallException、WorkflowPlanParseException、WorkflowPlanValidationException

### 7.5 日志

- **LLM 调用日志**：[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)
  - 成功时记录 provider、model、tokens_used
  - 超时时记录尝试次数
  - HTTP 错误时记录 status_code 和 response body
  - 意外错误时记录异常信息
- **数据加载日志**：[matbench_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/matbench_loader.py)
  - matbench 未安装时记录 warning
  - 生成模拟数据时记录 info
- **Workflow Planning LLM 调用日志**：[llm_client_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/llm_client_adapter.py)
  - 调用前记录 provider、model
  - 调用失败时记录异常信息

### 7.6 配置管理

- **相关文件**：[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)
- **配置项**：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| APP_NAME | MLAgent | 应用名称 |
| APP_ENV | development | 运行环境 |
| DEBUG | True | 调试模式 |
| DATABASE_URL | postgresql://postgres:postgres@db:5432/mlagent | 数据库连接 |
| CORS_ORIGINS | ["http://localhost:3000"] | 允许的跨域源 |
| LLM_PROVIDER | openai | LLM 提供商 |
| LLM_MODEL | gpt-4.1 | LLM 模型 |
| LLM_API_KEY | "" | LLM API 密钥 |
| LLM_BASE_URL | https://api.openai.com/v1 | LLM API 地址 |
| LLM_TIMEOUT | 60 | LLM 请求超时（秒） |
| LLM_MAX_RETRIES | 2 | LLM 请求最大重试次数 |
| LLM_TEMPERATURE | 0.0 | LLM 温度参数 |
| DATASET_UPLOAD_DIR | /app/uploads | 数据集上传目录 |
| DATASET_MAX_FILE_SIZE_MB | 100 | 最大文件大小（MB） |
| DATASET_ALLOWED_EXTENSIONS | csv,xlsx,xls | 允许的文件扩展名 |
| DATASET_PREVIEW_ROWS | 20 | 预览行数 |

### 7.7 数据库

- **Engine 创建**：[connection.py](file:///c:/projects/MLAgent/backend/app/shared/database/connection.py)
  - 使用 SQLModel.create_engine()，DEBUG 模式下 echo=True
- **Session 注入**：[session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py)
  - FastAPI Depends 注入 get_session()
- **表自动创建**：[main.py](file:///c:/projects/MLAgent/backend/app/main.py) 的 startup 事件中调用 `SQLModel.metadata.create_all(engine)`
- **迁移工具**：Alembic 已安装但未启用

### 7.8 外部服务调用

#### LLM API 调用

- **相关文件**：[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py)
- **调用方式**：httpx.post 到 `{base_url}/chat/completions`
- **请求体**：model、messages（system + user）、temperature
- **重试策略**：最多重试 max_retries + 1 次，仅对 TimeoutException 重试，401/403 不重试
- **超时处理**：httpx.TimeoutException 捕获并重试

#### Matbench 数据集加载

- **相关文件**：[matbench_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/matbench_loader.py)
- **调用方式**：try/except ImportError，若 matbench 包未安装则使用模拟数据
- **模拟数据**：使用 numpy.random.uniform 生成 0~12 的随机值，最多 200 行

---

## 8. 当前未完成部分与后续开发建议

### 8.1 尚未实现的功能模块

| 模块 | 优先级 | 说明 |
|------|--------|------|
| **Pipeline Generation** | 高 | 根据 Workflow Plan 生成可执行的 ML Pipeline 代码 |
| **Pipeline Execution** | 高 | 执行 Pipeline，包括数据预处理、模型训练、评估 |
| **Metric Evaluation** | 中 | 评估模型性能指标，与用户指定的 evaluation_metric 对比 |
| **Result Diagnosis** | 中 | 诊断模型表现，分析错误案例、特征重要性等 |
| **Report Generation** | 中 | 生成最终报告，汇总全流程结果 |

### 8.2 半成品代码与待完善之处

#### 模块二：Task Interpretation

1. **多 Provider 切换未实现**：[llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py) 仅实现了 OpenAI 兼容接口调用，settings 中的 LLM_PROVIDER 配置未被使用来切换不同 Provider
2. **LLM 请求参数未从前端传入**：TaskInterpretationCreateRequest 中的 llm_provider 和 model_name 字段在 service 层未被使用
3. **Prompt 中 JSON Schema 未使用 LLM 原生 JSON mode**：当前仅通过文本描述要求 LLM 输出 JSON，未使用 OpenAI 的 response_format 参数

#### 模块三：Dataset Profile

1. **MatbenchLoader 使用模拟数据**：当 matbench 包未安装时，使用随机生成的模拟数据而非真实数据集，这仅适用于 MVP 测试
2. **文件上传与加载分离**：文件上传接口和 dataset profiling 接口是分开的，用户上传文件后需要手动传入 file_id 才能触发 profiling
3. **Structure 文件支持未实现**：CIF/POSCAR 等结构文件的加载和解析尚未实现
4. **DatabaseLoader 和 ExternalURLLoader 未实现**：[loaders/](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/) 目录下仅实现了 base_loader.py、matbench_loader.py、file_loader.py，database_loader.py 和 external_url_loader.py 尚未创建
5. **pymatgen/matminer 未引入**：requirements.txt 中未包含材料科学相关的 pymatgen 和 matminer 依赖

#### 模块四：Workflow Planning

1. **多 Provider 切换未实现**：[llm_client_adapter.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/llm_client_adapter.py) 复用模块二的 LLMClient，同样未实现多 Provider 切换
2. **LLM 请求参数未从前端传入**：WorkflowPlanCreateRequest 中的 llm_provider 和 model_name 字段在 service 层未被使用
3. **Prompt 中 JSON Schema 未使用 LLM 原生 JSON mode**：当前仅通过文本描述要求 LLM 输出 JSON，未使用 OpenAI 的 response_format 参数
4. **规划模式仅支持 llm_guided**：虽然 request 中有 planning_mode 字段，但 service 层未实现其他规划模式（如 template_based）

### 8.3 潜在问题

#### 架构层面

1. **数据库表自动创建**：当前在 startup 事件中调用 `SQLModel.metadata.create_all(engine)`，生产环境应使用 Alembic 迁移
2. **JSONB 字段查询性能**：大量使用 JSONB 存储复杂对象，若后续需要频繁按 JSONB 内部字段查询，需考虑添加 GIN 索引
3. **文件上传目录管理**：上传文件保存在 `/app/uploads` 目录，未实现定期清理或存储配额管理

#### 代码层面

1. **Service 层直接实例化 Repository**：如 [TaskSpecificationService.__init__](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py#L18) 中 `self.repository = TaskSpecificationRepository()`，未使用依赖注入
2. **异常处理不一致**：部分接口使用 HTTPException 包装 BusinessException，部分直接抛出，响应格式可能不统一
3. **前端无状态管理库**：当前前端使用 React useState 管理组件级状态，未引入 Redux/Zustand 等全局状态管理，跨组件通信依赖 props 传递

#### 安全层面

1. **LLM API Key 明文存储**：LLM_API_KEY 存储在 .env 文件中，需确保不提交到版本控制
2. **文件上传未做内容校验**：仅校验扩展名和大小，未校验文件内容是否为合法的 CSV/Excel 格式（虽然 pandas 读取失败会报错，但可能被恶意文件利用）
3. **CORS 配置**：生产环境应限制 CORS_ORIGINS 为具体域名，而非通配符

### 8.4 后续开发建议

#### 短期（下一个模块：Pipeline Generation）

1. 阅读 [prd-3-技术实现方案.md](file:///c:/projects/MLAgent/docs/prd-3-技术实现方案.md) 了解 Dataset Profile 模块的完整架构
2. 设计 Pipeline Generation 模块的 PRD 和技术方案
3. 定义 Pipeline Generation Object 的数据结构
4. 实现从 Workflow Plan 到可执行 Pipeline 代码的生成逻辑

#### 中期

1. 启用 Alembic 数据库迁移
2. 实现多 Provider LLM 切换（Qwen、DeepSeek 等）
3. 引入 pymatgen/matminer 用于材料特征工程
4. 实现 Structure 文件（CIF/POSCAR）加载器
5. 前端引入全局状态管理（Zustand/Redux）
6. 将 Workflow Planning 模块的 llm_provider 和 model_name 参数从前端传入并实际使用

#### 长期

1. Pipeline 执行引擎
2. 模型训练与评估
3. 结果诊断与报告生成
4. 生产环境部署优化（HTTPS、认证、限流等）

---

## 9. 给后续 AI Coding 大模型的开发提示

### 9.1 继续开发时应优先阅读的文件

#### 理解整体架构

1. [main.py](file:///c:/projects/MLAgent/backend/app/main.py) - FastAPI 应用入口、路由注册、异常处理
2. [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) - 全局配置项
3. [docker-compose.yml](file:///c:/projects/MLAgent/docker-compose.yml) - 服务编排

#### 理解已有模块的实现模式

4. [task_specification/service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) - 模块一的服务编排模式
5. [task_interpretation/service.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/service.py) - 模块二的服务编排模式（含 LLM 调用）
6. [dataset_profile/service.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/service.py) - 模块三的服务编排模式（含数据加载和检查）
7. [workflow_planning/service.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/service.py) - 模块四的服务编排模式（含 LLM 调用和上游依赖检查）

#### 理解数据模型

7. [task_specification/model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py) - 模块一的数据库模型
8. [task_interpretation/model.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/model.py) - 模块二的数据库模型
9. [dataset_profile/model.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/model.py) - 模块三的数据库模型
10. [workflow_planning/model.py](file:///c:/projects/MLAgent/backend/app/modules/workflow_planning/model.py) - 模块四的数据库模型

#### 理解前端组件

11. [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) - 主表单组件
12. [TaskInterpretationPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskInterpretation/components/TaskInterpretationPanel.tsx) - 任务理解结果展示
13. [DatasetProfilePanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/datasetProfile/components/DatasetProfilePanel.tsx) - 数据集画像结果展示
14. [WorkflowPlanPanel.tsx](file:///c:/projects/MLAgent/frontend/src/modules/workflowPlanning/components/WorkflowPlanPanel.tsx) - 工作流规划结果展示

### 9.2 开发时应注意的边界

#### 不要重复实现的功能

1. **不要重新实现数据库 CRUD**：已有 [repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py) 模式，新模块应复制该模式并修改
2. **不要重新实现统一响应格式**：使用 [response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py) 中的 `success_response()` 和 `error_response()`
3. **不要重新实现异常基类**：继承 [exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py) 中的 BusinessException
4. **不要重新实现 LLM 调用**：复用 [llm_client.py](file:///c:/projects/MLAgent/backend/app/modules/task_interpretation/llm_client.py) 或在其基础上扩展
5. **不要重新实现数据加载器**：新 Loader 应继承 [base_loader.py](file:///c:/projects/MLAgent/backend/app/modules/dataset_profile/loaders/base_loader.py)

#### 必须遵守的约定

1. **ID 生成规则**：新模块的 ID 格式应为 `{module_prefix}_` + 8 位 uuid hex
2. **状态枚举**：新模块的状态设计应参考已有模块的状态流转模式
3. **JSONB 存储**：复杂嵌套对象应存入 JSONB 列，高频查询字段应单独建列
4. **API 路由前缀**：新模块的 API 路由应使用 `/api/{module-name}s` 格式
5. **Pydantic 校验**：所有请求/响应模型应使用 Pydantic BaseModel
6. **前端 API 客户端**：新模块的 API 调用应在 `frontend/src/api/` 下新建文件，复用 [taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) 中的 axios 实例

### 9.3 模块间数据传递约定

1. **上游模块只读不写**：新模块读取 Task Specification / Task Interpretation / Dataset Profile 时，不应修改它们的数据
2. **状态检查**：调用上游模块前必须检查其状态是否满足前置条件
3. **通过 task_id 关联**：所有模块都通过 task_id 关联到同一个任务
4. **通过 interpretation_id 关联**：Dataset Profile 及后续模块通过 interpretation_id 关联到具体的理解结果

### 9.4 测试建议

1. 当前项目尚未实现自动化测试，建议后续开发时补充单元测试和集成测试
2. 重点测试：normalizer 映射规则、validator 校验逻辑、LLM output parser、data checkers
3. 使用 pytest 作为测试框架（与 FastAPI 生态一致）

### 9.5 启动开发环境

```bash
# 启动数据库
docker-compose up -d db

# 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 启动前端
cd frontend
npm install
npm start
```

或使用 Docker Compose 一键启动：

```bash
docker-compose up -d
```

---

*文档结束。本文档基于对项目中所有源代码文件的实际阅读和分析编写，所有文件路径、函数名、类名、接口名和数据结构均可在项目中找到对应实现。*