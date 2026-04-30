# 项目已实现部分说明文档

## 1. 项目概述

### 1.1 项目定位

MLAgent 是一个 **AI-driven Automated Machine Learning 框架**，面向材料科学领域，旨在让用户以结构化表单方式提交材料机器学习任务需求，并通过后续 LLM 理解、数据集加载、工作流规划、Pipeline 生成、模型训练、结果诊断等模块实现端到端的自动化机器学习流程。

### 1.2 当前实现阶段

当前项目处于 **MVP（Minimum Viable Product）阶段**，仅实现了整个框架的第一个模块 —— **User Task Specification（用户任务规格说明）**。

该模块的核心目标是：
- 通过结构化表单收集用户提交的材料机器学习任务需求
- 对表单字段进行标准化、完整性检查和合法性校验
- 生成标准化、可校验、可传递的 Task Specification Object
- 为后续模块（Task Understanding by LLM、Dataset Loading、Workflow Planning 等）提供统一输入

### 1.3 MVP 验收状态

根据 [prd-1-mvp.md](file:///c:/projects/MLAgent/docs/prd-1-mvp.md) 中定义的 11 项功能验收标准，当前已实现的核心能力包括：

| 序号 | 验收标准 | 状态 |
|------|----------|------|
| 1 | 能展示完整的任务填写表单 | 已实现 |
| 2 | 能区分必填字段、选填字段和条件必填字段 | 已实现 |
| 3 | 能接收用户提交的结构化字段 | 已实现 |
| 4 | 能生成唯一 task_id | 已实现 |
| 5 | 能将表单显示值标准化为系统内部字段 | 已实现 |
| 6 | 能识别缺失的必填字段 | 已实现 |
| 7 | 能识别明显不匹配的 task_type 与 evaluation_metric | 已实现 |
| 8 | 能返回清晰的错误提示和修改建议 | 已实现 |
| 9 | 能输出统一格式的 Task Specification Object | 已实现 |
| 10 | 能将 valid 状态的任务对象传递给后续模块 | 接口已预留，后续模块未实现 |

---

## 2. 当前目录结构说明

```
c:\projects\MLAgent/
├── backend/                          # FastAPI 后端服务
│   ├── app/
│   │   ├── main.py                   # FastAPI 应用主入口：CORS、异常处理、路由注册、数据库初始化
│   │   ├── __init__.py
│   │   ├── modules/                  # 业务模块目录
│   │   │   ├── __init__.py
│   │   │   └── task_specification/   # User Task Specification 模块（当前唯一业务模块）
│   │   │       ├── __init__.py
│   │   │       ├── api.py            # API 路由层：4 个 HTTP 接口
│   │   │       ├── schemas.py        # Pydantic 请求/响应数据模型
│   │   │       ├── service.py        # 业务编排层：create/get/update/validate 四个核心流程
│   │   │       ├── model.py          # SQLModel 数据库表模型
│   │   │       ├── repository.py     # 数据访问层：CRUD 操作
│   │   │       ├── normalizer.py     # 字段标准化组件
│   │   │       ├── validator.py      # 字段校验组件（完整性 + 合法性）
│   │   │       └── builder.py        # Task Specification Object 构建器
│   │   └── shared/                   # 跨模块公共基础设施
│   │       ├── __init__.py
│   │       ├── config/
│   │       │   ├── __init__.py
│   │       │   └── settings.py       # 环境变量配置（pydantic-settings）
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── connection.py     # SQLAlchemy engine 创建
│   │       │   └── session.py        # 数据库 Session 依赖注入
│   │       └── common/
│   │           ├── __init__.py
│   │           ├── enums.py          # 公共枚举定义（TaskStatus, TaskType, InputType 等）
│   │           ├── exceptions.py     # 统一异常定义（BusinessException, NotFoundException 等）
│   │           └── response.py       # 统一 API 响应格式（success_response / error_response）
│   ├── requirements.txt              # Python 依赖清单
│   ├── Dockerfile                    # 后端 Docker 镜像构建
│   ├── .env                          # 环境变量配置
│   └── .env.example                  # 环境变量模板
├── frontend/                         # React + TypeScript 前端应用
│   ├── public/
│   │   └── index.html                # HTML 入口
│   ├── src/
│   │   ├── index.tsx                 # React 应用入口，渲染 TaskSpecificationPage
│   │   ├── api/
│   │   │   └── taskApi.ts            # Axios API 客户端：4 个接口调用 + 类型定义 + 拦截器
│   │   └── modules/
│   │       └── taskSpecification/    # 前端任务规格模块
│   │           ├── pages/
│   │           │   └── TaskSpecificationPage.tsx  # 页面组件：布局 + 标题 + 表单容器
│   │           ├── components/
│   │           │   ├── TaskSpecificationForm.tsx  # 表单组件：字段渲染 + 提交 + 结果展示
│   │           │   └── TaskFieldGroup.tsx         # 字段分组组件：带标题的卡片容器
│   │           └── constants.ts      # 表单常量：Zod schema + 下拉选项定义
│   ├── package.json                  # Node.js 依赖清单
│   ├── package-lock.json
│   ├── tsconfig.json                 # TypeScript 配置
│   └── Dockerfile                    # 前端 Docker 镜像构建
├── docker-compose.yml                # Docker Compose 编排（db + backend + frontend）
└── docs/
    ├── prd-1-mvp.md                  # MVP 需求文档
    ├── prd-1-技术栈.md               # 技术栈说明
    └── prd-1-架构.md                 # 架构目录功能说明
```

### 2.1 关键文件职责速查

| 文件 | 职责 |
|------|------|
| [main.py](file:///c:/projects/MLAgent/backend/app/main.py) | FastAPI 应用入口，注册 CORS、全局异常处理器、路由、数据库表初始化 |
| [api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) | 定义 4 个 HTTP 路由（POST/GET/PUT/POST validate） |
| [service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) | 业务编排中枢，串联 normalizer → validator → builder → repository |
| [normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py) | 将用户表单显示值映射为系统内部标准值 |
| [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) | 必填检查 + 指标兼容性 + 输入/数据源一致性校验 |
| [builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/builder.py) | 组装原始字段、标准化字段、校验结果为完整 Task Specification Object |
| [model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py) | SQLModel 数据库表定义（task_specification 表） |
| [repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py) | 数据库 CRUD 操作 |
| [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py) | Pydantic 请求/响应模型 |
| [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) | 前端表单核心组件，含字段渲染、提交逻辑、结果展示 |
| [taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) | 前端 API 客户端，封装 Axios 调用和 TypeScript 类型 |
| [constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts) | Zod 校验 schema + 表单下拉选项常量 |

---

## 3. 当前系统输入与输出

### 3.1 用户输入

用户通过前端表单填写以下字段（根据 [constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts) 和 [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py)）：

| 字段 | 是否必填 | 输入方式 | 示例 |
|------|----------|----------|------|
| task_name | 选填 | 文本框 | "Band gap prediction" |
| task_description | 选填 | 多行文本框 | "Predict experimental band gaps..." |
| material_system | 选填 | 下拉框 | "inorganic crystals" |
| prediction_target | **必填** | 文本框 | "experimental band gap" |
| task_type | **必填** | 下拉框 | "regression" |
| dataset_description | **必填** | 多行文本框 | "matbench_expt_gap" |
| input_type | **必填** | 下拉框 | "composition" |
| target_column | **必填** | 文本框 | "band_gap" |
| evaluation_metric | 选填 | 下拉框 | "MAE" |
| user_priority | 选填 | 多选框 | ["accuracy", "interpretability"] |
| constraints | 选填 | 多行文本框（每行一条） | "Use interpretable models only" |

### 3.2 系统处理过程

1. **前端校验**：Zod schema 在提交前进行必填字段检查（[constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts) 中的 `taskSpecificationSchema`）
2. **HTTP 传输**：Axios 将 JSON 请求体发送至后端（[taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) 中的 `createTask` 函数）
3. **后端接收**：FastAPI 路由层接收请求，通过 Pydantic 模型反序列化（[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) 中的 `create_task` 函数）
4. **字段标准化**：normalizer 将 "Regression" → "regression"、"Mean Absolute Error" → "MAE" 等（[normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py) 中的 `normalize_fields` 函数）
5. **字段校验**：validator 检查必填字段、指标兼容性、输入/数据源一致性（[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 中的 `validate` 函数）
6. **对象构建**：builder 组装完整 Task Specification Object（[builder.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/builder.py) 中的 `build_task_specification` 函数）
7. **持久化**：repository 将数据写入 PostgreSQL（[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py) 中的 `create` 方法）

### 3.3 系统输出

后端返回统一格式的 JSON 响应（根据 [response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py)）：

**成功响应示例**：
```json
{
  "success": true,
  "message": "Task specification created successfully.",
  "data": {
    "task_id": "task_a1b2c3d4",
    "task_name": "Band gap prediction",
    "prediction_target": "experimental band gap",
    "task_type": "regression",
    "dataset_description": "matbench_expt_gap",
    "input_type": "composition",
    "target_column": "band_gap",
    "evaluation_metric": "MAE",
    "user_priority": ["accuracy", "interpretability"],
    "constraints": [],
    "status": "valid",
    "missing_fields": [],
    "validation_messages": [],
    "created_at": "2026-04-30T10:00:00",
    "updated_at": "2026-04-30T10:00:00"
  }
}
```

**状态说明**：
- `valid`：字段完整且无冲突
- `incomplete`：缺少必填字段
- `invalid`：字段存在明显冲突（如 regression + Accuracy）
- `valid_with_warning`：字段完整但有非阻断性警告（如未指定评价指标）

---

## 4. 当前技术栈说明

### 4.1 后端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **FastAPI** | 0.115.6 | Web 框架，提供 HTTP 路由、请求校验、OpenAPI 文档 |
| **Uvicorn** | 0.34.0 | ASGI 服务器，运行 FastAPI 应用 |
| **SQLModel** | 0.0.22 | ORM 框架，定义数据库模型和执行 CRUD 操作 |
| **Pydantic** | 2.10.4 | 数据验证和序列化，用于请求/响应模型 |
| **Pydantic Settings** | 2.7.1 | 环境变量管理 |
| **psycopg2-binary** | 2.9.10 | PostgreSQL 数据库驱动 |
| **python-dotenv** | 1.0.1 | 加载 .env 文件 |
| **Alembic** | 1.14.1 | 数据库迁移工具（已安装但当前未在代码中使用） |

### 4.2 前端技术栈

| 技术 | 版本 | 作用 |
|------|------|------|
| **React** | 18.3.1 | UI 组件框架 |
| **TypeScript** | 5.7.2 | 类型安全 |
| **React Hook Form** | 7.54.2 | 表单状态管理 |
| **Zod** | 3.24.1 | 前端表单校验 schema |
| **@hookform/resolvers** | 3.10.0 | React Hook Form 与 Zod 集成 |
| **Axios** | 1.7.9 | HTTP 客户端 |
| **react-scripts** | 5.0.1 | Create React App 构建工具 |

### 4.3 基础设施

| 技术 | 版本 | 作用 |
|------|------|------|
| **PostgreSQL** | 16 (Alpine) | 关系型数据库，存储 Task Specification 记录 |
| **Docker** | - | 容器化部署 |
| **Docker Compose** | 3.8 | 多服务编排（db + backend + frontend） |

### 4.4 技术分层与职责

```
前端层 (React + TypeScript)
  ├── 表单渲染 (TaskSpecificationForm.tsx)
  ├── 前端校验 (Zod schema in constants.ts)
  └── HTTP 通信 (Axios in taskApi.ts)
        ↓ HTTP POST/GET/PUT
后端层 (FastAPI)
  ├── API 路由 (api.py)
  ├── 业务编排 (service.py)
  ├── 字段标准化 (normalizer.py)
  ├── 字段校验 (validator.py)
  ├── 对象构建 (builder.py)
  └── 数据访问 (repository.py)
        ↓ SQL (SQLModel)
数据层 (PostgreSQL)
  └── task_specification 表 (model.py)
```

---

## 5. 已实现功能模块

### 5.1 模块一：任务表单展示（前端）

**文件**：[TaskSpecificationPage.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/pages/TaskSpecificationPage.tsx)、[TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx)、[TaskFieldGroup.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskFieldGroup.tsx)、[constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts)

**输入**：无业务输入，系统根据预设字段配置生成表单

**处理逻辑**：
- 渲染 5 个字段分组区域：基本信息、数据集信息、机器学习任务信息、评价指标信息、用户偏好与约束
- 使用 React Hook Form 管理表单状态
- 使用 Zod schema 进行前端实时校验
- 区分必填字段（prediction_target、task_type、dataset_description、input_type、target_column）和选填字段
- 提供下拉框、文本框、多行文本框、多选框等多种输入方式

**输出**：展示给用户的结构化任务填写表单

**完成度**：100%

### 5.2 模块二：任务表单提交与创建（前后端）

**前端文件**：[TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) 的 `onSubmit` 函数、[taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) 的 `createTask` 函数

**后端文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) 的 `create_task` 路由、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) 的 `create_task` 方法

**输入**：用户填写的表单 JSON 对象

**处理逻辑**：
1. 前端将 constraints 字符串按换行符分割为数组
2. 通过 Axios POST 请求发送至 `/api/tasks`
3. 后端生成唯一 task_id（格式：`task_` + 8 位 UUID hex）
4. 调用 normalizer 标准化字段
5. 调用 validator 校验字段
6. 调用 builder 构建 Task Specification Object
7. 调用 repository 写入数据库
8. 返回 TaskSpecificationResponse

**输出**：包含 task_id 和 status 的初始任务对象

**完成度**：100%

### 5.3 模块三：字段标准化

**文件**：[normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py)

**输入**：用户提交的原始表单字段

**处理逻辑**：
- `normalize_task_type`：将 "Regression" → "regression"、"Classification" → "classification"、"Ranking" → "ranking"
- `normalize_input_type`：将 "Chemical composition" → "composition"、"Crystal structure" → "structure" 等
- `normalize_evaluation_metric`：将 "Mean Absolute Error" → "MAE"、"Root Mean Squared Error" → "RMSE" 等
- `normalize_user_priority`：标准化用户优先级选项
- 对所有字符串字段执行 strip() 去除前后空格

**输出**：标准化后的字段字典

**完成度**：100%

### 5.4 模块四：必填字段完整性检查

**文件**：[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 的 `check_required_fields` 函数

**输入**：标准化后的 Task Specification 字段

**处理逻辑**：
- 检查 prediction_target 是否为空
- 检查 task_type 是否为空
- 检查 dataset_description 是否为空
- 检查 input_type 是否为空
- 检查 target_column 是否为空
- 为每个缺失字段生成对应的英文提示信息

**输出**：缺失字段列表 (missing_fields) 和校验消息列表 (validation_messages)

**完成度**：100%

> 注意：根据 PRD 文档，target_column 应为"条件必填"（当 dataset_source 为用户上传表格时必填），但当前代码实现中将其作为**无条件必填**字段处理。这是一个与 PRD 的差异点。

### 5.5 模块五：基础合法性校验

**文件**：[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 的 `check_evaluation_metric_compatibility` 和 `check_input_dataset_consistency` 函数

**输入**：标准化后的 Task Specification 字段

**处理逻辑**：

**指标兼容性校验**：
- regression 任务只接受 MAE、RMSE、R2
- classification 任务只接受 Accuracy、F1、ROC-AUC
- ranking 任务只接受 Spearman、NDCG、Top-k recall
- 不匹配时生成冲突提示信息

**输入/数据源一致性校验**：
- input_type 为 structure 时，检查 dataset_description 是否包含 cif、poscar、structure、crystal 等关键词
- input_type 为 composition 时，检查 dataset_description 是否只包含结构文件关键词

**输出**：冲突校验消息列表

**完成度**：100%

### 5.6 模块六：查询任务规格

**后端文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) 的 `get_task` 路由、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) 的 `get_task` 方法

**输入**：task_id（URL 路径参数）

**处理逻辑**：
1. 通过 repository 查询数据库记录
2. 若不存在，抛出 NotFoundException
3. 从 task_spec_json 中提取扩展字段
4. 组装为 TaskSpecificationResponse 返回

**输出**：完整的 Task Specification 对象

**完成度**：100%

### 5.7 模块七：更新任务规格

**后端文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) 的 `update_task` 路由、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) 的 `update_task` 方法

**输入**：task_id + 部分更新的字段（TaskSpecificationUpdateRequest）

**处理逻辑**：
1. 查询已有任务记录
2. 合并旧字段和新字段（使用 exclude_unset=True 只合并用户实际提交的字段）
3. 重新执行 normalizer → validator → builder 流程
4. 更新数据库记录
5. 返回更新后的任务对象

**输出**：更新后的 Task Specification 对象

**完成度**：100%

### 5.8 模块八：重新校验任务规格

**后端文件**：[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py) 的 `validate_task` 路由、[service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) 的 `validate_task` 方法

**输入**：task_id（URL 路径参数）

**处理逻辑**：
1. 从数据库加载已有任务
2. 从数据库字段重建 normalized_data 字典
3. 重新调用 validator 执行校验
4. 返回 ValidationResultResponse

**输出**：校验结果（status、missing_fields、validation_messages、warnings）

**完成度**：100%

### 5.9 模块九：错误提示与修改引导

**文件**：[validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 的校验消息生成逻辑、[TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) 的错误展示逻辑

**输入**：完整性检查和合法性校验结果

**处理逻辑**：
- 后端根据缺失字段或冲突字段生成英文提示信息
- 前端根据返回的 status 字段显示不同颜色的结果框（绿色=valid、橙色=incomplete/valid_with_warning、红色=invalid）
- 前端展示 missing_fields 和 validation_messages 列表

**输出**：前端展示的错误提示和修改建议

**完成度**：100%

### 5.10 模块十：统一 API 响应格式

**文件**：[response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py)、[exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)

**处理逻辑**：
- 所有成功响应使用 `success_response(message, data)` 函数
- 所有失败响应使用 `error_response(message, error_code)` 函数
- 统一格式：`{ success, message, data, error_code }`
- 全局异常处理器捕获 BusinessException 和通用 Exception

**完成度**：100%

### 5.11 模块十一：数据库持久化

**文件**：[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)、[repository.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/repository.py)、[connection.py](file:///c:/projects/MLAgent/backend/app/shared/database/connection.py)、[session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py)

**处理逻辑**：
- 使用 SQLModel 定义 task_specification 表
- 结构化字段（id、task_name、task_type、prediction_target 等）单独建列
- 灵活字段（task_description、material_system、user_priority、constraints、missing_fields 等）存入 JSONB 字段 task_spec_json
- 应用启动时通过 `SQLModel.metadata.create_all(engine)` 自动建表
- repository 提供 create、get_by_id、update、exists、list_tasks 五个方法

**完成度**：100%

---

## 6. 系统数据流与调用链路

### 6.1 创建任务的完整数据流

```
用户填写前端表单
    ↓
Zod schema 前端校验 (constants.ts: taskSpecificationSchema)
    ↓
React Hook Form 收集表单数据 (TaskSpecificationForm.tsx: onSubmit)
    ↓
constraints 字符串 → 数组转换 (TaskSpecificationForm.tsx: L53-55)
    ↓
Axios POST /api/tasks (taskApi.ts: createTask)
    ↓
FastAPI 路由接收 (api.py: create_task)
    ↓
Pydantic 反序列化为 TaskSpecificationCreateRequest (schemas.py)
    ↓
service.create_task() (service.py: L21-69)
    ├── 生成 task_id = "task_" + uuid4()[:8]
    ├── request.model_dump() → raw_data
    ├── normalize_fields(raw_data) → normalized_data (normalizer.py)
    ├── validate(normalized_data) → validation_result (validator.py)
    │     ├── check_required_fields() → missing_fields, validation_messages
    │     ├── check_evaluation_metric_compatibility() → compatibility_messages
    │     ├── check_input_dataset_consistency() → consistency_messages
    │     └── check_evaluation_metric_provided() → warnings
    ├── build_task_specification(...) → task_spec_dict (builder.py)
    ├── 创建 TaskSpecification ORM 对象 (model.py)
    └── repository.create(session, task_spec_model) (repository.py: L9-12)
          ↓
        session.add() → session.commit() → session.refresh()
          ↓
        PostgreSQL task_specification 表 INSERT
          ↓
返回 TaskSpecificationResponse (schemas.py: TaskSpecificationResponse)
    ↓
success_response() 包装 (response.py)
    ↓
JSON 响应返回前端
    ↓
前端展示结果 (TaskSpecificationForm.tsx: setResult)
```

### 6.2 查询任务的数据流

```
前端调用 getTask(taskId) (taskApi.ts)
    ↓
GET /api/tasks/{task_id} (api.py: get_task)
    ↓
service.get_task(session, task_id) (service.py: L71-98)
    ├── repository.get_by_id(session, task_id) (repository.py: L14-15)
    │     ↓
    │   session.get(TaskSpecification, task_id)
    │     ↓
    │   PostgreSQL SELECT
    ├── 若不存在 → 抛出 NotFoundException
    └── 从 task.task_spec_json 提取扩展字段
          ↓
返回 TaskSpecificationResponse
```

### 6.3 更新任务的数据流

```
前端调用 updateTask(taskId, request) (taskApi.ts)
    ↓
PUT /api/tasks/{task_id} (api.py: update_task)
    ↓
service.update_task(session, task_id, request) (service.py: L100-168)
    ├── repository.get_by_id() 查询原任务
    ├── request.model_dump(exclude_unset=True) 获取变更字段
    ├── 合并旧字段和新字段 → merged_data
    ├── normalize_fields(merged_data) → normalized_data
    ├── validate(normalized_data) → validation_result
    ├── build_task_specification(...) → task_spec_dict
    ├── 更新 existing_task 各字段
    └── repository.update(session, task_id, existing_task)
          ↓
        session.commit() → PostgreSQL UPDATE
          ↓
返回更新后的 TaskSpecificationResponse
```

### 6.4 重新校验的数据流

```
前端调用 validateTask(taskId) (taskApi.ts)
    ↓
POST /api/tasks/{task_id}/validate (api.py: validate_task)
    ↓
service.validate_task(session, task_id) (service.py: L170-199)
    ├── repository.get_by_id() 查询任务
    ├── 从数据库字段重建 normalized_data
    ├── validate(normalized_data) → validation_result
    └── 返回 ValidationResultResponse
```

---

## 7. 核心代码与关键设计说明

### 7.1 接口设计

系统提供 4 个 RESTful API 接口（定义于 [api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)）：

| 方法 | 路径 | 功能 | 请求体 | 响应体 |
|------|------|------|--------|--------|
| POST | `/api/tasks` | 创建任务规格 | TaskSpecificationCreateRequest | TaskSpecificationResponse |
| GET | `/api/tasks/{task_id}` | 查询任务规格 | 无 | TaskSpecificationResponse |
| PUT | `/api/tasks/{task_id}` | 更新任务规格 | TaskSpecificationUpdateRequest | TaskSpecificationResponse |
| POST | `/api/tasks/{task_id}/validate` | 重新校验任务 | 无 | ValidationResultResponse |

此外还有一个健康检查接口：
- GET `/health` → `{"status": "ok"}`

### 7.2 数据模型设计

**数据库表模型**（[model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py)）：

表名：`task_specification`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | str (PK) | 任务唯一标识，格式 task_xxxxxxxx |
| task_name | str (max 255) | 任务名称 |
| task_type | str (max 50) | 任务类型（regression/classification/ranking） |
| prediction_target | str (max 255) | 预测目标 |
| dataset_description | str (max 2000) | 数据集描述 |
| input_type | str (max 50) | 输入数据类型 |
| target_column | str (max 255) | 目标变量列名 |
| evaluation_metric | str (max 50) | 评价指标 |
| status | str (max 50) | 任务状态（valid/incomplete/invalid/valid_with_warning） |
| task_spec_json | JSONB | 扩展字段（包含 task_description、material_system、user_priority、constraints、missing_fields、validation_messages 等） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

**设计特点**：采用"结构化字段 + JSONB 灵活字段"的混合存储策略。高频查询字段单独建列，低频扩展字段存入 JSONB。

### 7.3 状态管理

任务状态流转逻辑（定义于 [enums.py](file:///c:/projects/MLAgent/backend/app/shared/common/enums.py) 的 `TaskStatus` 枚举，计算逻辑在 [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) 的 `validate` 函数）：

```
received（初始状态，当前代码中未实际使用）
    ↓
根据校验结果确定状态：
    ├── 有缺失字段 → incomplete
    ├── 有冲突字段（含 "not suitable" 或 "Please specify"） → invalid
    ├── 有警告但无缺失/冲突 → valid_with_warning
    └── 无问题 → valid
```

### 7.4 异常处理

**异常体系**（[exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)）：

```
BusinessException (基类)
├── ValidationException (VALIDATION_ERROR)
├── NotFoundException (NOT_FOUND)
└── DatabaseException (DATABASE_ERROR)
```

**全局异常处理器**（[main.py](file:///c:/projects/MLAgent/backend/app/main.py)）：
- `BusinessException` → HTTP 400 + error_response
- `Exception`（兜底） → HTTP 500 + error_response

**API 层异常处理**（[api.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/api.py)）：
- 每个路由函数内部使用 try-except 捕获 BusinessException
- 根据 error_code 区分 404（NOT_FOUND）和 400（其他）

### 7.5 配置管理

**环境变量配置**（[settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py)）：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| APP_NAME | "MLAgent" | 应用名称 |
| APP_ENV | "development" | 运行环境 |
| DEBUG | True | 调试模式（控制 SQL 日志输出） |
| DATABASE_URL | postgresql://postgres:postgres@db:5432/mlagent | 数据库连接串 |
| CORS_ORIGINS | ["http://localhost:3000"] | 允许的跨域来源 |

配置通过 pydantic-settings 从 `.env` 文件加载。

### 7.6 数据库连接与会话管理

**连接管理**（[connection.py](file:///c:/projects/MLAgent/backend/app/shared/database/connection.py)）：
- 使用 `create_engine(settings.DATABASE_URL, echo=settings.DEBUG)` 创建 engine
- echo 参数由 DEBUG 配置控制

**会话管理**（[session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py)）：
- 使用 FastAPI 依赖注入 `Depends(get_session)`
- 通过 `with Session(engine)` 管理生命周期，确保请求结束后自动关闭

### 7.7 跨域配置

CORS 中间件在 [main.py](file:///c:/projects/MLAgent/backend/app/main.py) 中配置：
- 允许来源：settings.CORS_ORIGINS（默认 http://localhost:3000）
- 允许凭证：True
- 允许方法和头部：全部

### 7.8 前端表单校验

**Zod Schema**（[constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts)）：

```typescript
taskSpecificationSchema = z.object({
  prediction_target: z.string().min(1, 'Prediction target is required'),
  task_type: z.string().min(1, 'Task type is required'),
  dataset_description: z.string().min(1, 'Dataset description is required'),
  input_type: z.string().min(1, 'Input type is required'),
  target_column: z.string().min(1, 'Target column is required'),
  // 其余字段为 optional
})
```

前端 Zod 校验与后端 validator.py 校验形成**双重校验机制**，确保数据质量。

### 7.9 前端 API 客户端设计

**Axios 客户端**（[taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts)）：
- baseURL：从环境变量 REACT_APP_API_URL 读取，默认 http://localhost:8000
- timeout：15000ms
- 请求拦截器：打印请求日志
- 响应拦截器：打印响应日志，区分网络错误、超时、HTTP 错误等场景
- 导出 4 个 API 函数：createTask、getTask、updateTask、validateTask
- 导出完整的 TypeScript 接口定义

---

## 8. 当前未完成部分与后续开发建议

### 8.1 与 PRD 的差异点

| PRD 要求 | 当前实现 | 差异说明 |
|----------|----------|----------|
| dataset_source 字段 | 实际使用 dataset_description | 字段名不一致，PRD 中为 dataset_source，代码中为 dataset_description |
| target_column 条件必填 | target_column 无条件必填 | PRD 规定仅当用户使用自定义表格数据时必填，当前代码对所有情况都要求必填 |
| evaluation_metric 缺失时状态为 valid_with_warning | 已实现 | 通过 warnings 列表和 valid_with_warning 状态实现 |
| status 包含 "received" 状态 | 枚举已定义但实际未使用 | TaskStatus.received 在枚举中定义，但创建任务时直接根据校验结果设置状态，不会先设为 received |

### 8.2 尚未实现的功能

根据 PRD 文档和整体架构设计，以下功能尚未实现：

1. **后续模块**：
   - Task Understanding by LLM（LLM 任务理解）
   - Dataset Loading and Profiling（数据集加载与分析）
   - Workflow Planning（工作流规划）
   - Pipeline Generation（Pipeline 生成）
   - Pipeline Execution（Pipeline 执行）
   - Metric Evaluation（指标评估）
   - Result Diagnosis（结果诊断）
   - Workflow Refinement（工作流优化）
   - Report Generation（报告生成）

2. **前端功能**：
   - 任务列表页面（当前只有单个任务表单页）
   - 任务详情查看页面
   - 任务编辑页面（前端未实现编辑表单，只有后端 API）
   - 校验结果面板组件（PRD 架构文档中提到了 ValidationMessagePanel.tsx 但实际未创建）
   - 表单提交后的状态轮询/实时更新

3. **后端功能**：
   - 任务列表接口（repository 有 list_tasks 方法但 API 层未暴露）
   - 任务删除接口
   - Alembic 数据库迁移（已安装但未配置和使用）
   - 分页查询
   - 按条件筛选任务

4. **基础设施**：
   - 单元测试 / 集成测试
   - API 文档完善（Swagger 已自动生成但缺少详细描述）
   - 日志系统（当前仅有 console.log）
   - 认证与授权
   - 文件上传功能（PRD 提到用户上传 CSV/Excel 文件）

### 8.3 潜在问题

1. **target_column 校验过于严格**：当前 validator.py 中 target_column 对所有情况都要求必填，但 PRD 规定仅在用户使用自定义表格数据时才必填。这会导致用户选择公开数据集（如 matbench_expt_gap）时也被要求填写 target_column。

2. **字段名不一致**：PRD 中使用 `dataset_source`，代码中使用 `dataset_description`。后续模块对接时可能出现字段名混淆。

3. **normalizer.py 中 EVALUATION_METRIC_MAPPING 的 "accuracy" 映射为 "Accuracy"**：首字母大写，但其他映射值都是全小写。这种不一致可能在后续比较逻辑中造成问题（尽管当前 validator.py 中使用了集合比较，大小写一致）。

4. **builder.py 中 created_at 参数类型注解**：`created_at: datetime = None` 应使用 `Optional[datetime] = None` 以符合 Python 类型注解规范。

5. **repository.py 的 update 方法**：使用 `task_spec.dict(exclude_unset=True)` 来更新字段，但传入的 task_spec 是已经手动赋值后的完整对象，exclude_unset=True 可能不会按预期工作（取决于哪些字段是显式设置的）。

6. **前端没有实现编辑功能**：后端提供了 PUT /api/tasks/{task_id} 接口，但前端没有对应的编辑页面或编辑表单逻辑。

7. **数据库自动建表**：当前在 main.py 的 startup 事件中使用 `SQLModel.metadata.create_all(engine)` 自动建表。在生产环境中应使用 Alembic 进行数据库迁移管理。

### 8.4 后续开发建议

**短期（完善当前模块）**：
1. 修正 target_column 的条件必填逻辑
2. 统一字段命名（dataset_source vs dataset_description）
3. 补充任务列表 API 和前端页面
4. 实现前端编辑功能
5. 添加单元测试覆盖核心校验逻辑

**中期（开发后续模块）**：
1. 按照 modules/ 目录的设计原则，为每个后续模块创建独立目录
2. 实现 Task Understanding by LLM 模块，接收 Task Specification Object 作为输入
3. 实现文件上传功能，支持用户上传 CSV/Excel 数据文件
4. 配置 Alembic 数据库迁移

**长期（完整框架）**：
1. 实现完整的 Pipeline 生成与执行链路
2. 集成 LLM API
3. 实现结果可视化
4. 添加用户认证与权限管理
5. 部署到生产环境

---

## 9. 给后续 AI Coding 大模型的开发提示

### 9.1 继续开发时应优先阅读的文件

**理解整体架构**：
1. [main.py](file:///c:/projects/MLAgent/backend/app/main.py) — 应用入口，了解路由注册和中间件配置
2. [prd-1-mvp.md](file:///c:/projects/MLAgent/docs/prd-1-mvp.md) — 需求文档，了解设计意图
3. [prd-1-架构.md](file:///c:/projects/MLAgent/docs/prd-1-架构.md) — 架构文档，了解各文件职责划分

**理解当前模块实现**：
4. [service.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/service.py) — 业务编排中枢，理解 create/update/get/validate 四个核心流程
5. [validator.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/validator.py) — 校验规则，理解必填检查、指标兼容性、输入一致性逻辑
6. [normalizer.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/normalizer.py) — 字段标准化映射表
7. [model.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/model.py) — 数据库表结构
8. [schemas.py](file:///c:/projects/MLAgent/backend/app/modules/task_specification/schemas.py) — 请求/响应数据模型

**理解前端实现**：
9. [TaskSpecificationForm.tsx](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx) — 前端表单核心组件
10. [taskApi.ts](file:///c:/projects/MLAgent/frontend/src/api/taskApi.ts) — API 客户端和 TypeScript 类型定义
11. [constants.ts](file:///c:/projects/MLAgent/frontend/src/modules/taskSpecification/constants.ts) — Zod schema 和表单选项常量

**理解基础设施**：
12. [settings.py](file:///c:/projects/MLAgent/backend/app/shared/config/settings.py) — 配置管理
13. [response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py) — 统一响应格式
14. [exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py) — 异常体系
15. [enums.py](file:///c:/projects/MLAgent/backend/app/shared/common/enums.py) — 枚举定义

### 9.2 开发时应注意的边界

1. **分层架构严格遵守**：
   - api.py 只负责接请求、调服务、回响应，不写业务逻辑
   - service.py 只负责组织流程，不写具体校验规则
   - normalizer.py 只负责字段映射，不判断字段冲突
   - validator.py 只负责判断规则，不操作数据库
   - builder.py 只负责组装对象，不判断规则
   - repository.py 只负责 CRUD，不判断业务逻辑

2. **不要重复实现的功能**：
   - 统一响应格式：使用 `success_response()` 和 `error_response()`（[response.py](file:///c:/projects/MLAgent/backend/app/shared/common/response.py)）
   - 异常处理：使用已有的 BusinessException 子类（[exceptions.py](file:///c:/projects/MLAgent/backend/app/shared/common/exceptions.py)）
   - 数据库会话：使用 `Depends(get_session)` 依赖注入（[session.py](file:///c:/projects/MLAgent/backend/app/shared/database/session.py)）
   - 枚举定义：使用 shared/common/enums.py 中已有的枚举
   - 前端 API 调用：复用 taskApi.ts 中的 Axios 实例和拦截器
   - 前端表单校验：复用 Zod schema 模式

3. **模块隔离原则**：
   - 每个业务模块（task_specification、task_understanding 等）应独立目录
   - 模块间通过明确的接口和数据对象交互
   - 不要将模块专用逻辑放入 shared/ 目录

4. **数据流方向**：
   - 前端 → API 路由 → Service → Normalizer/Validator/Builder → Repository → Database
   - 不要跳过中间层直接调用底层（如 API 直接调用 repository）

5. **状态流转**：
   - 任务状态由 validator.py 的 validate() 函数计算得出
   - 不要手动设置 status 字段，应通过校验流程自动确定

### 9.3 开发新模块的模板参考

如果要开发下一个模块（如 task_understanding），建议参考以下模式：

```
backend/app/modules/task_understanding/
├── __init__.py
├── api.py          # 路由定义，参考 api.py
├── schemas.py      # 请求/响应模型，参考 schemas.py
├── service.py      # 业务编排，参考 service.py
├── model.py        # 数据库模型，参考 model.py
├── repository.py   # 数据访问，参考 repository.py
└── (其他业务文件)   # 根据模块需求新增
```

新模块的输入应来自 task_specification 模块的输出（Task Specification Object），通过 task_id 关联。

### 9.4 测试建议

- 为 validator.py 中的每个校验函数编写单元测试
- 为 normalizer.py 中的映射函数编写单元测试
- 为 service.py 中的核心流程编写集成测试（使用测试数据库）
- 前端为 TaskSpecificationForm 编写组件测试

### 9.5 已知待修复问题清单

| 优先级 | 问题 | 涉及文件 |
|--------|------|----------|
| P0 | target_column 应改为条件必填 | validator.py: check_required_fields |
| P1 | 统一 dataset_source / dataset_description 命名 | schemas.py, model.py, service.py, normalizer.py, validator.py, builder.py, taskApi.ts, constants.ts |
| P1 | 实现前端编辑功能 | 新增编辑页面组件或复用 TaskSpecificationForm |
| P2 | 补充任务列表 API | api.py 新增 GET /api/tasks 路由 |
| P2 | 配置 Alembic 数据库迁移 | 新增 alembic 配置 |
| P3 | 添加单元测试 | 新增 tests/ 目录 |
