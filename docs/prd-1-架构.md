# User Task Specification 模块 MVP 目录功能说明

## 一、后端目录

```text
backend/
  app/
    main.py

    modules/
      task_specification/
        api.py
        schemas.py
        service.py
        model.py
        repository.py
        normalizer.py
        validator.py
        builder.py

    shared/
      database/
        connection.py
        session.py

      common/
        response.py
        exceptions.py
        enums.py

      config/
        settings.py
````

---

# 1. backend/

## 功能定位

后端项目根目录。

用于存放 FastAPI 后端服务相关代码、依赖配置、Docker 配置、环境变量配置等。

## 主要内容

后续可以包含：

```text
backend/
  app/
  requirements.txt
  Dockerfile
  .env
  README.md
```

## 不建议放什么

不要把业务代码直接放在 `backend/` 根目录下。业务代码统一放到 `backend/app/` 下面。

---

# 2. backend/app/

## 功能定位

后端应用主目录。

所有 FastAPI 应用代码都放在这里。

## 主要职责

1. 存放应用入口；
2. 存放业务模块；
3. 存放公共基础设施；
4. 管理 API 路由注册；
5. 管理配置、数据库连接、通用异常等。

---

# 3. backend/app/main.py

## 功能定位

FastAPI 应用启动入口。

这是整个后端服务的主入口文件。

## 主要职责

1. 创建 FastAPI app 实例；
2. 注册各业务模块的 API 路由；
3. 注册全局异常处理器；
4. 配置跨域 CORS；
5. 配置应用启动和关闭事件；
6. 暴露 Swagger / OpenAPI 文档；
7. 初始化必要的应用资源。

## 在本模块中的作用

对于 User Task Specification MVP，`main.py` 至少需要注册：

```text
modules/task_specification/api.py
```

也就是让这些接口生效：

```text
POST /api/tasks
GET /api/tasks/{task_id}
PUT /api/tasks/{task_id}
POST /api/tasks/{task_id}/validate
```

## 不应该做什么

`main.py` 不应该写具体业务逻辑，比如：

```text
字段标准化
字段校验
数据库增删改查
Task Specification Object 构建
```

这些应该交给模块内部的 service、validator、repository 等文件。

---

# 4. backend/app/modules/

## 功能定位

业务模块目录。

每个业务阶段对应一个独立模块。

当前 MVP 只实现：

```text
task_specification/
```

后续可以逐步新增：

```text
task_understanding/
dataset_profiling/
workflow_planning/
pipeline_generation/
pipeline_execution/
metric_evaluation/
result_diagnosis/
workflow_refinement/
report_generation/
```

## 设计原则

每个模块都应该尽量做到：

```text
接口独立
业务逻辑独立
数据对象独立
数据库操作独立
```

这样后续模块增多时，不会互相污染。

---

# 5. backend/app/modules/task_specification/

## 功能定位

User Task Specification 模块目录。

这是第一个模块的完整业务闭环。

## 模块负责什么

该模块负责：

```text
接收用户任务表单
标准化字段
校验字段完整性和合法性
构建 Task Specification Object
保存任务规格
查询任务规格
更新任务规格
重新校验任务规格
```

## 模块不负责什么

该模块不负责：

```text
读取真实数据集
分析数据质量
选择特征工程方法
生成 pipeline
执行训练
计算模型指标
LLM 结果诊断
生成最终报告
```

---

# 6. backend/app/modules/task_specification/api.py

## 功能定位

User Task Specification 模块的 API 路由层。

它负责对外提供 HTTP 接口。

## 主要职责

1. 定义路由路径；
2. 接收前端请求；
3. 将请求体转换为 schema 对象；
4. 调用 service 层；
5. 返回统一 API 响应；
6. 处理接口级别的参数错误。

## 推荐包含的接口

### 6.1 创建任务规格

```text
POST /api/tasks
```

作用：

接收用户填写的任务表单，创建新的 Task Specification。

---

### 6.2 查询任务规格

```text
GET /api/tasks/{task_id}
```

作用：

根据任务 ID 查询已保存的 Task Specification。

---

### 6.3 更新任务规格

```text
PUT /api/tasks/{task_id}
```

作用：

允许用户修改已经提交的任务字段。

---

### 6.4 重新校验任务规格

```text
POST /api/tasks/{task_id}/validate
```

作用：

对已有任务重新执行完整性校验和合法性校验。

---

## 输入

来自前端的 HTTP 请求，例如：

```json
{
  "task_name": "Band gap prediction",
  "prediction_target": "experimental band gap",
  "task_type": "Regression",
  "dataset_source": "matbench_expt_gap",
  "input_type": "Chemical composition",
  "target_column": "band_gap",
  "evaluation_metric": "Mean Absolute Error"
}
```

## 输出

统一格式 API 响应，例如：

```json
{
  "success": true,
  "message": "Task specification created successfully.",
  "data": {
    "task_id": "task_001",
    "status": "valid"
  }
}
```

## 不应该做什么

`api.py` 不应该直接：

```text
写字段标准化逻辑
写字段冲突校验逻辑
直接操作数据库
拼装复杂 Task Specification Object
```

它只负责“接请求、调服务、回响应”。

---

# 7. backend/app/modules/task_specification/schemas.py

## 功能定位

User Task Specification 模块的 API 数据结构定义文件。

主要用于定义请求体、响应体和中间数据对象。

## 主要职责

1. 定义创建任务请求对象；
2. 定义更新任务请求对象；
3. 定义任务响应对象；
4. 定义校验结果响应对象；
5. 约束字段类型；
6. 为 FastAPI 自动生成 OpenAPI 文档提供结构信息。

## 推荐包含的对象

### 7.1 TaskSpecificationCreateRequest

用于创建任务时接收前端表单。

字段示例：

```text
task_name
task_description
material_system
prediction_target
task_type
dataset_source
input_type
target_column
evaluation_metric
user_priority
constraints
```

---

### 7.2 TaskSpecificationUpdateRequest

用于更新已有任务。

特点：

大多数字段应该是可选的，因为用户可能只修改其中一两个字段。

---

### 7.3 TaskSpecificationResponse

用于返回完整任务对象。

字段示例：

```text
task_id
task_name
prediction_target
task_type
dataset_source
input_type
target_column
evaluation_metric
status
missing_fields
validation_messages
created_at
updated_at
```

---

### 7.4 ValidationResultResponse

用于返回校验结果。

字段示例：

```text
status
missing_fields
validation_messages
warnings
```

## 不应该做什么

`schemas.py` 不应该写复杂业务逻辑。

它可以做基础类型约束，但不要把完整业务规则都写在这里。

例如：

```text
task_type 是否是 regression
```

可以在 schema 层做基础限制。

但：

```text
regression 不能使用 Accuracy
```

更适合放在 `validator.py` 中。

---

# 8. backend/app/modules/task_specification/service.py

## 功能定位

User Task Specification 模块的业务编排层。

这是本模块的核心业务中枢。

## 主要职责

1. 创建任务规格；
2. 更新任务规格；
3. 查询任务规格；
4. 重新校验任务规格；
5. 调用 normalizer 做字段标准化；
6. 调用 validator 做字段校验；
7. 调用 builder 生成最终任务对象；
8. 调用 repository 保存或读取数据库；
9. 控制任务状态流转。

## 典型处理流程

创建任务时：

```text
接收 CreateRequest
    ↓
生成 task_id
    ↓
调用 normalizer 标准化字段
    ↓
调用 validator 校验字段
    ↓
调用 builder 构建 Task Specification Object
    ↓
调用 repository 保存任务
    ↓
返回 TaskSpecificationResponse
```

更新任务时：

```text
接收 task_id 和 UpdateRequest
    ↓
从 repository 查询原任务
    ↓
合并旧字段和新字段
    ↓
重新 normalizer
    ↓
重新 validator
    ↓
重新 builder
    ↓
更新数据库
    ↓
返回更新后的任务对象
```

## 不应该做什么

`service.py` 不建议写大量具体规则。

例如这些最好不要直接写在 service 里：

```text
Regression → regression
Accuracy 不适合 regression
target_column 在 uploaded_csv 时必填
```

这些规则应该分别放到：

```text
normalizer.py
validator.py
```

service 只负责组织流程。

---

# 9. backend/app/modules/task_specification/model.py

## 功能定位

数据库模型定义文件。

用于描述 Task Specification 在数据库中的表结构。

## 主要职责

1. 定义数据库表名；
2. 定义字段名称；
3. 定义字段类型；
4. 定义索引；
5. 定义创建时间、更新时间；
6. 定义 JSONB 字段；
7. 供 ORM 使用。

## 推荐表名

```text
task_specification
```

## 推荐字段

```text
id
task_name
task_type
prediction_target
dataset_source
input_type
target_column
evaluation_metric
status
task_spec_json
created_at
updated_at
```

## 字段设计建议

### 结构化字段单独建列

例如：

```text
id
task_type
prediction_target
dataset_source
input_type
status
created_at
```

这些字段后续经常用于查询和筛选，所以建议单独建列。

### 灵活字段放入 JSONB

例如：

```text
task_description
material_system
user_priority
constraints
missing_fields
validation_messages
raw_form_values
normalized_values
```

这些字段未来可能扩展，所以适合放入 `task_spec_json`。

## 不应该做什么

`model.py` 不应该写业务处理逻辑。

它只描述“数据怎么存”。

---

# 10. backend/app/modules/task_specification/repository.py

## 功能定位

数据库访问层。

负责隔离业务逻辑与数据库操作。

## 主要职责

1. 创建任务记录；
2. 根据 task_id 查询任务；
3. 更新任务记录；
4. 保存校验结果；
5. 查询任务列表；
6. 判断任务是否存在。

## 推荐方法

```text
create(task_spec_object)
get_by_id(task_id)
update(task_id, task_spec_object)
exists(task_id)
list_tasks()
```

## 输入

来自 service 层的 Task Specification Object。

## 输出

数据库保存后的任务记录，或查询到的任务记录。

## 不应该做什么

`repository.py` 不应该判断：

```text
字段是否完整
任务类型和评价指标是否匹配
任务状态应该是 valid 还是 invalid
```

这些是业务逻辑，应放在 `validator.py` 或 `service.py`。

repository 只负责“存”和“取”。

---

# 11. backend/app/modules/task_specification/normalizer.py

## 功能定位

字段标准化组件。

负责把用户表单中的显示值转换成系统内部标准值。

## 为什么需要它

用户在前端可能看到的是：

```text
Regression
Chemical composition
Mean Absolute Error
```

但系统内部后续模块最好统一使用：

```text
regression
composition
MAE
```

这样后续 Dataset Profiling、Workflow Planning、Pipeline Generation 等模块才能稳定处理。

## 主要职责

1. 标准化 task_type；
2. 标准化 input_type；
3. 标准化 evaluation_metric；
4. 标准化 user_priority；
5. 清理字符串前后空格；
6. 统一大小写；
7. 保留原始字段和标准化字段的映射关系。

## 输入

用户提交的原始表单字段。

## 输出

标准化后的字段对象。

## 示例

输入：

```json
{
  "task_type": "Regression",
  "input_type": "Chemical composition",
  "evaluation_metric": "Mean Absolute Error"
}
```

输出：

```json
{
  "task_type": "regression",
  "input_type": "composition",
  "evaluation_metric": "MAE"
}
```

## 不应该做什么

`normalizer.py` 不负责判断字段之间是否冲突。

例如：

```text
regression + Accuracy 是否合理
```

这不是标准化问题，而是校验问题，应放在 `validator.py`。

---

# 12. backend/app/modules/task_specification/validator.py

## 功能定位

字段校验组件。

负责判断任务规格是否完整、合法、无明显冲突。

这是本模块最关键的质量控制文件。

## 主要职责

1. 必填字段校验；
2. 条件必填字段校验；
3. 字段取值范围校验；
4. 任务类型与评价指标匹配校验；
5. 输入类型与数据来源一致性校验；
6. 生成 missing_fields；
7. 生成 validation_messages；
8. 生成 warnings；
9. 计算最终任务状态。

## 核心校验规则

### 必填字段

```text
prediction_target
task_type
dataset_source
input_type
```

### 条件必填字段

```text
target_column
```

当用户使用自定义表格数据时，`target_column` 必填。

### 任务类型与评价指标匹配

```text
regression      → MAE / RMSE / R2
classification  → Accuracy / F1 / ROC-AUC
ranking         → Spearman / NDCG / Top-k recall
```

### 状态判断

```text
字段完整且无冲突      → valid
缺少必要字段          → incomplete
字段存在明显冲突      → invalid
有非阻断问题          → valid_with_warning / warning
```

## 输入

标准化后的任务字段。

## 输出

ValidationResult。

示例：

```json
{
  "status": "invalid",
  "missing_fields": [],
  "validation_messages": [
    "Accuracy is not suitable for regression tasks. Please select MAE, RMSE, or R2."
  ],
  "warnings": []
}
```

## 不应该做什么

`validator.py` 不应该操作数据库，也不应该构建完整最终任务对象。

它只负责判断“这个任务规格是否合格”。

---

# 13. backend/app/modules/task_specification/builder.py

## 功能定位

Task Specification Object 构建器。

负责把原始字段、标准化字段、校验结果、系统字段组装成最终对象。

## 主要职责

1. 生成最终 Task Specification Object；
2. 合并 raw_form_values；
3. 合并 normalized_values；
4. 合并 validation_result；
5. 添加 task_id；
6. 添加 created_at 和 updated_at；
7. 添加 status；
8. 输出统一结构，供 repository 保存和后续模块使用。

## 输入

包括：

```text
原始表单字段
标准化字段
校验结果
task_id
created_at
updated_at
```

## 输出

完整 Task Specification Object。

示例：

```json
{
  "task_id": "task_001",
  "task_name": "Band gap prediction",
  "task_description": "Predict experimental band gaps from chemical compositions.",
  "material_system": "inorganic crystals",
  "prediction_target": "experimental band gap",
  "task_type": "regression",
  "dataset_source": "matbench_expt_gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE",
  "user_priority": ["accuracy", "interpretability"],
  "constraints": [],
  "status": "valid",
  "missing_fields": [],
  "validation_messages": [],
  "created_at": "2026-04-26T22:00:00+08:00",
  "updated_at": "2026-04-26T22:00:00+08:00"
}
```

## 不应该做什么

`builder.py` 不负责判断规则，也不负责写数据库。

它只负责“组装对象”。

---

# 14. backend/app/shared/

## 功能定位

后端公共能力目录。

这里放跨模块复用的基础设施。

当前 User Task Specification 模块会用到其中的一部分。后续开发其他模块时也会复用。

## 设计原则

只有真正被多个模块共享的内容，才放到 `shared/`。

不要把某个业务模块专用逻辑放到 shared。

例如：

```text
task_specification_validator.py
```

不应该放到 shared，因为它只属于 task_specification 模块。

---

# 15. backend/app/shared/database/

## 功能定位

数据库公共配置目录。

负责数据库连接、会话管理、数据库初始化等。

---

# 16. backend/app/shared/database/connection.py

## 功能定位

数据库连接配置文件。

## 主要职责

1. 读取数据库连接地址；
2. 创建数据库 engine；
3. 配置连接池；
4. 管理数据库基础连接参数。

## 输入

来自环境变量或配置文件的数据库地址，例如：

```text
DATABASE_URL
```

## 输出

数据库 engine / connection 对象。

## 不应该做什么

不要在这里写具体业务表的增删改查。

这些应该放在各模块的 repository 中。

---

# 17. backend/app/shared/database/session.py

## 功能定位

数据库会话管理文件。

## 主要职责

1. 创建数据库 session；
2. 提供依赖注入使用的 session；
3. 管理 session 生命周期；
4. 确保请求结束后关闭 session；
5. 处理事务提交与回滚。

## 在 FastAPI 中的作用

API 请求进入后，可以通过依赖注入获得数据库 session。

然后 repository 使用这个 session 读写数据库。

## 不应该做什么

不要在这里写业务查询逻辑。

---

# 18. backend/app/shared/common/

## 功能定位

通用工具和基础对象目录。

用于存放跨模块复用的响应结构、异常类型、枚举定义等。

---

# 19. backend/app/shared/common/response.py

## 功能定位

统一 API 响应格式定义文件。

## 为什么需要它

前端调用不同接口时，最好收到一致格式的响应。

例如所有接口都返回：

```json
{
  "success": true,
  "message": "xxx",
  "data": {}
}
```

或：

```json
{
  "success": false,
  "message": "xxx",
  "error_code": "xxx",
  "data": null
}
```

## 主要职责

1. 定义成功响应格式；
2. 定义失败响应格式；
3. 统一 message、data、error_code 字段；
4. 降低前端处理复杂度。

## 不应该做什么

不要在 response.py 中写具体业务逻辑。

---

# 20. backend/app/shared/common/exceptions.py

## 功能定位

统一异常定义文件。

## 主要职责

定义项目内部通用异常，例如：

```text
BusinessException
ValidationException
NotFoundException
DatabaseException
```

## 使用场景

例如查询 task_id 不存在时，可以抛出：

```text
NotFoundException
```

然后由全局异常处理器转换成统一 API 响应。

## 好处

避免每个模块自己随便返回错误格式。

---

# 21. backend/app/shared/common/enums.py

## 功能定位

公共枚举定义文件。

## 主要职责

存放多个模块可能共享的枚举类型。

例如：

```text
TaskStatus
TaskType
InputType
EvaluationMetric
UserPriority
```

## 示例枚举

```text
TaskStatus:
  draft
  received
  valid
  incomplete
  invalid
  updated

TaskType:
  regression
  classification
  ranking

InputType:
  composition
  structure
  descriptor_table
  text_features
```

## 注意

如果某些枚举只属于一个模块，也可以先放在该模块内部。
但像 `TaskStatus`、`TaskType` 后续多个模块都可能使用，放在 shared 是合理的。

---

# 22. backend/app/shared/config/

## 功能定位

配置管理目录。

用于统一管理环境变量和系统配置。

---

# 23. backend/app/shared/config/settings.py

## 功能定位

项目配置文件。

## 主要职责

1. 读取环境变量；
2. 管理数据库配置；
3. 管理 API 配置；
4. 管理调试模式；
5. 管理跨域配置；
6. 后续管理 LLM API Key、文件存储路径、任务执行配置等。

## 当前 MVP 可包含配置

```text
APP_NAME
APP_ENV
DEBUG
DATABASE_URL
CORS_ORIGINS
```

## 后续可扩展配置

```text
LLM_PROVIDER
LLM_API_KEY
UPLOAD_DIR
MAX_FILE_SIZE
PIPELINE_TIMEOUT
```

---

# 二、前端目录

```text
frontend/
  src/
    modules/
      taskSpecification/
        pages/
          TaskSpecificationPage.tsx
        components/
          TaskSpecificationForm.tsx
          TaskFieldGroup.tsx
          ValidationMessagePanel.tsx
        api/
          taskSpecificationApi.ts
        schemas/
          taskSpecificationSchema.ts
        types/
          taskSpecificationTypes.ts

    shared/
      components/
      api/
        httpClient.ts
      types/
        apiResponse.ts
      utils/
```

---

# 24. frontend/

## 功能定位

前端项目根目录。

用于存放 React 前端应用代码、依赖配置、构建配置等。

后续可以包含：

```text
package.json
vite.config.ts
tsconfig.json
Dockerfile
.env
```

---

# 25. frontend/src/

## 功能定位

前端源码主目录。

所有 React 页面、组件、API 请求、类型定义等都放在这里。

---

# 26. frontend/src/modules/

## 功能定位

前端业务模块目录。

每个业务模块一个目录。

当前 MVP 只有：

```text
taskSpecification/
```

后续可以新增：

```text
datasetProfiling/
workflowPlanning/
pipelineExecution/
metricEvaluation/
reportGeneration/
```

---

# 27. frontend/src/modules/taskSpecification/

## 功能定位

User Task Specification 前端模块目录。

负责该模块所有页面、组件、接口请求、类型定义和前端表单校验。

---

# 28. frontend/src/modules/taskSpecification/pages/

## 功能定位

页面级组件目录。

页面组件通常负责组织一个完整业务页面，而不是具体表单控件细节。

---

# 29. frontend/src/modules/taskSpecification/pages/TaskSpecificationPage.tsx

## 功能定位

User Task Specification 页面入口。

这是用户看到的任务填写页面。

## 主要职责

1. 渲染页面标题和说明；
2. 引入 TaskSpecificationForm；
3. 管理页面级状态；
4. 处理任务创建成功后的跳转或提示；
5. 展示当前模块的整体布局；
6. 可选地展示最近创建的任务状态。

## 页面内容示例

页面可以包含：

```text
页面标题：Create Materials ML Task
说明文字：Please specify your materials machine learning task.
任务填写表单
提交按钮
校验结果面板
```

## 不应该做什么

不要在页面组件里写复杂表单字段逻辑。

表单字段逻辑应该放在：

```text
TaskSpecificationForm.tsx
```

---

# 30. frontend/src/modules/taskSpecification/components/

## 功能定位

User Task Specification 模块专用组件目录。

只存放该模块内部使用的组件。

---

# 31. frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx

## 功能定位

任务规格填写表单组件。

这是前端模块的核心组件。

## 主要职责

1. 渲染任务填写表单；
2. 管理表单状态；
3. 调用前端 schema 进行校验；
4. 处理用户输入；
5. 动态控制字段显示与必填规则；
6. 调用 API 提交表单；
7. 接收并展示后端校验结果。

## 表单字段

包括：

```text
task_name
task_description
material_system
prediction_target
task_type
dataset_source
input_type
target_column
evaluation_metric
user_priority
constraints
```

## 关键交互逻辑

例如：

```text
当 task_type = Regression
evaluation_metric 下拉框优先显示 MAE / RMSE / R2

当 task_type = Classification
evaluation_metric 下拉框优先显示 Accuracy / F1 / ROC-AUC

当 dataset_source = uploaded_csv
target_column 标记为必填
```

## 不应该做什么

不要在这里直接写后端业务规则的最终判断。

前端可以做提示和预校验，但最终是否合法以后端返回为准。

---

# 32. frontend/src/modules/taskSpecification/components/TaskFieldGroup.tsx

## 功能定位

任务字段分组组件。

用于把表单拆成多个清晰区域，提升可读性。

## 主要职责

1. 渲染一组相关字段；
2. 接收字段配置；
3. 统一展示分组标题和说明；
4. 减少 TaskSpecificationForm 组件复杂度。

## 推荐分组

可以分成：

```text
Basic Task Information
Dataset Information
Machine Learning Task Setting
Evaluation Setting
User Preferences and Constraints
```

## 好处

如果所有字段都直接写在 `TaskSpecificationForm.tsx` 里，后续会很长、很乱。

用 `TaskFieldGroup.tsx` 可以让表单结构更清楚。

---

# 33. frontend/src/modules/taskSpecification/components/ValidationMessagePanel.tsx

## 功能定位

校验结果展示组件。

用于展示后端返回的：

```text
missing_fields
validation_messages
warnings
status
```

## 主要职责

1. 展示字段缺失提示；
2. 展示字段冲突提示；
3. 展示 warning；
4. 展示任务状态；
5. 引导用户修改表单。

## 示例展示内容

```text
Status: incomplete

Please fix the following issues:
- Please specify the target column in the dataset.
```

或：

```text
Status: invalid

- Accuracy is not suitable for regression tasks. Please select MAE, RMSE, or R2.
```

---

# 34. frontend/src/modules/taskSpecification/api/

## 功能定位

User Task Specification 模块的前端 API 封装目录。

用于集中管理本模块所有 HTTP 请求。

---

# 35. frontend/src/modules/taskSpecification/api/taskSpecificationApi.ts

## 功能定位

User Task Specification 模块的 API 请求封装文件。

## 主要职责

封装以下请求：

```text
createTaskSpecification
getTaskSpecification
updateTaskSpecification
validateTaskSpecification
```

## 对应后端接口

```text
POST /api/tasks
GET /api/tasks/{task_id}
PUT /api/tasks/{task_id}
POST /api/tasks/{task_id}/validate
```

## 为什么需要单独封装

页面组件不应该直接写：

```text
fetch('/api/tasks')
```

而应该调用：

```text
createTaskSpecification(formData)
```

这样做的好处是：

```text
接口路径集中管理
请求参数统一处理
响应类型统一约束
后续接口变化时容易修改
```

---

# 36. frontend/src/modules/taskSpecification/schemas/

## 功能定位

前端表单校验 schema 目录。

---

# 37. frontend/src/modules/taskSpecification/schemas/taskSpecificationSchema.ts

## 功能定位

User Task Specification 前端表单校验规则文件。

## 主要职责

1. 定义表单字段结构；
2. 定义必填字段；
3. 定义字段类型；
4. 定义字段长度限制；
5. 定义前端条件校验规则；
6. 推导前端 TypeScript 类型。

## 典型校验规则

```text
prediction_target 不能为空
task_type 必须选择
dataset_source 不能为空
input_type 必须选择
如果 dataset_source = uploaded_csv，则 target_column 必填
```

## 注意

前端 schema 只负责提升用户体验。

最终可信校验仍然在后端：

```text
validator.py
```

---

# 38. frontend/src/modules/taskSpecification/types/

## 功能定位

User Task Specification 模块的 TypeScript 类型定义目录。

---

# 39. frontend/src/modules/taskSpecification/types/taskSpecificationTypes.ts

## 功能定位

定义前端使用的任务规格相关类型。

## 主要职责

定义：

```text
TaskSpecificationFormValues
TaskSpecificationCreateRequest
TaskSpecificationUpdateRequest
TaskSpecificationResponse
ValidationResult
TaskStatus
TaskType
InputType
EvaluationMetric
```

## 作用

1. 约束表单字段类型；
2. 约束 API 请求参数；
3. 约束 API 响应数据；
4. 减少前后端字段不一致；
5. 提高代码可维护性。

---

# 40. frontend/src/shared/

## 功能定位

前端公共能力目录。

存放跨模块复用的组件、API 工具、类型和工具函数。

---

# 41. frontend/src/shared/components/

## 功能定位

通用 UI 组件目录。

例如：

```text
Button
Input
Select
TextArea
CheckboxGroup
FormItem
Modal
Card
Loading
```

## 设计原则

只有多个模块都会用到的组件，才放在这里。

Task Specification 专用组件不要放进 shared。

---

# 42. frontend/src/shared/api/

## 功能定位

前端通用 API 工具目录。

---

# 43. frontend/src/shared/api/httpClient.ts

## 功能定位

统一 HTTP 请求客户端。

## 主要职责

1. 统一配置 baseURL；
2. 统一设置请求头；
3. 统一处理响应；
4. 统一处理错误；
5. 统一处理超时；
6. 后续可统一处理 token、鉴权、重试等。

## 使用方式

业务模块 API 不直接使用原始 fetch / axios，而是调用 `httpClient`。

例如：

```text
taskSpecificationApi.ts
    ↓
httpClient.ts
    ↓
后端接口
```

## 好处

后续如果要加：

```text
登录鉴权
请求拦截
错误弹窗
loading 状态
接口超时
```

只需要集中改 `httpClient.ts`。

---

# 44. frontend/src/shared/types/

## 功能定位

前端公共类型目录。

---

# 45. frontend/src/shared/types/apiResponse.ts

## 功能定位

统一 API 响应类型定义文件。

## 推荐定义的类型

```text
ApiResponse<T>
ApiError
PaginationResponse<T>
```

当前 MVP 主要需要：

```text
ApiResponse<T>
```

对应后端统一响应格式：

```json
{
  "success": true,
  "message": "xxx",
  "data": {}
}
```

## 好处

所有模块调用 API 时，都可以复用同一套响应类型。

---

# 46. frontend/src/shared/utils/

## 功能定位

前端通用工具函数目录。

## 当前 MVP 可能需要

```text
formatDate
isEmpty
cleanObject
```

## 注意

不要把业务规则塞进 utils。

例如：

```text
regression + Accuracy 不合法
```

这个不是通用工具逻辑，不应该放在 utils。

它应该属于 taskSpecification 模块。

---

# 三、整体调用关系

## 1. 前端调用链

```text
TaskSpecificationPage.tsx
    ↓
TaskSpecificationForm.tsx
    ↓
taskSpecificationSchema.ts
    ↓
taskSpecificationApi.ts
    ↓
httpClient.ts
    ↓
后端 POST /api/tasks
```

---

## 2. 后端调用链

```text
api.py
    ↓
service.py
    ↓
normalizer.py
    ↓
validator.py
    ↓
builder.py
    ↓
repository.py
    ↓
model.py
    ↓
PostgreSQL
```

---

# 四、目前 MVP 最小必须实现的文件

如果你想先做最小闭环，优先实现这些：

## 后端最小闭环

```text
backend/app/main.py
backend/app/modules/task_specification/api.py
backend/app/modules/task_specification/schemas.py
backend/app/modules/task_specification/service.py
backend/app/modules/task_specification/normalizer.py
backend/app/modules/task_specification/validator.py
backend/app/modules/task_specification/builder.py
backend/app/shared/common/response.py
backend/app/shared/common/enums.py
```

此时可以先不接数据库，直接返回 Task Specification Object。

---

## 加上数据库持久化后

再实现：

```text
backend/app/modules/task_specification/model.py
backend/app/modules/task_specification/repository.py
backend/app/shared/database/connection.py
backend/app/shared/database/session.py
backend/app/shared/config/settings.py
```

---

## 前端最小闭环

```text
frontend/src/modules/taskSpecification/pages/TaskSpecificationPage.tsx
frontend/src/modules/taskSpecification/components/TaskSpecificationForm.tsx
frontend/src/modules/taskSpecification/components/ValidationMessagePanel.tsx
frontend/src/modules/taskSpecification/api/taskSpecificationApi.ts
frontend/src/modules/taskSpecification/schemas/taskSpecificationSchema.ts
frontend/src/modules/taskSpecification/types/taskSpecificationTypes.ts
frontend/src/shared/api/httpClient.ts
frontend/src/shared/types/apiResponse.ts
```

---

# 五、最终总结

这套目录的核心思想是：

```text
业务模块独立
公共能力共享
接口层不写业务
Service 负责编排
Normalizer 负责标准化
Validator 负责校验
Builder 负责组装对象
Repository 负责数据库读写
Model 负责数据库结构
```

对于你现在的第一个模块，最重要的是先跑通：

```text
用户填写表单
    ↓
前端提交
    ↓
后端标准化
    ↓
后端校验
    ↓
生成 Task Specification Object
    ↓
返回任务状态
```

后续继续开发 Dataset Profiling、Workflow Planning、Pipeline Execution 等模块时，只需要在 `modules/` 下新增对应业务模块即可，不会破坏当前结构。

