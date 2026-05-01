# Dataset Loading, Checking, and Profiling 模块架构与技术栈方案

## 1. 模块名称

Dataset Loading, Checking, and Profiling  
数据集加载、检查与画像分析模块

---

## 2. 模块定位

本模块是 MLAgent 系统的第三个核心业务模块，位于：

```text
Task Specification
    ↓
LLM-based Task Interpretation
    ↓
Dataset Loading, Checking, and Profiling
    ↓
Workflow Planning
    ↓
Pipeline Generation
    ↓
Pipeline Execution
    ↓
Metric Evaluation
    ↓
Result Diagnosis
    ↓
Report Generation
````

当前系统已经完成：

1. **Task Specification 模块**：负责用户任务输入、字段标准化、基础校验、Task Specification Object 构建与持久化；
2. **LLM-based Task Interpretation 模块**：负责基于 LLM 理解任务语义，输出 Task Interpretation Object，包括 `dataset_intent`、`planning_hint`、`modeling_intent` 等字段。

本模块的核心职责是：

```text
Task Specification Object
    +
Task Interpretation Object
    ↓
Dataset Loading Context
    ↓
Dataset Source Resolution
    ↓
Dataset Loading
    ↓
Schema Checking
    ↓
Modality Checking
    ↓
Data Quality Checking
    ↓
Target Profiling
    ↓
Dataset Profile Object
```

本模块不进行特征工程、不选择模型、不生成 Pipeline、不执行训练，只负责形成“数据事实层”。

---

# 3. 总体架构目标

## 3.1 架构目标

Dataset Loading, Checking, and Profiling 模块需要满足以下架构目标：

1. 与 Task Specification 模块通过 `task_id` 自然衔接；
2. 与 Task Interpretation 模块通过 `interpretation_id` 和 `dataset_intent` 自然衔接；
3. 支持多种数据来源的统一加载；
4. 支持公开基准数据集与用户上传数据；
5. 输出标准化 Dataset Profile Object；
6. 为后续 Workflow Planning 模块提供稳定、可机器读取的数据画像；
7. 数据加载器、检查器、画像器彼此解耦；
8. 支持后续扩展 Materials Project、OQMD、JARVIS、CIF/POSCAR 文件、数据库表等数据来源；
9. 支持 profiling 结果持久化、查询、重跑与版本追踪。

---

## 3.2 总体架构图

```text
Frontend
  └── Dataset Profile Panel
        ↓
Backend API Layer
  └── dataset_profile/api.py
        ↓
Service Layer
  └── dataset_profile/service.py
        ↓
Context Builder
  ├── Read Task Specification
  └── Read Latest Task Interpretation
        ↓
Source Resolver
  └── Resolve dataset source type
        ↓
Dataset Loader Layer
  ├── MatbenchLoader
  ├── FileLoader
  ├── DatabaseLoader          后续扩展
  ├── MaterialsProjectLoader  后续扩展
  └── StructureFileLoader     后续扩展
        ↓
Checking Layer
  ├── SchemaChecker
  ├── ModalityChecker
  ├── QualityChecker
  └── TargetChecker
        ↓
Profiler
  └── Aggregate profiling results
        ↓
Builder
  └── Build Dataset Profile Object
        ↓
Repository Layer
  └── Persist into dataset_profile table
        ↓
Downstream Interface
  └── Workflow Planning Input
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
Source Resolution 数据源识别层
  ↓
Loader 数据加载层
  ↓
Checker 数据检查层
  ↓
Profiler 数据画像层
  ↓
Builder 对象构建层
  ↓
Repository 数据访问层
  ↓
Database 数据层
```

各层职责必须保持清晰：

| 层级              | 职责                                               |
| --------------- | ------------------------------------------------ |
| API 层           | 接收 HTTP 请求、调用 Service、返回统一响应                     |
| Service 层       | 编排完整流程，不写具体检查规则                                  |
| Context Builder | 读取并组合上游 Task Specification 与 Task Interpretation |
| Source Resolver | 判断数据来源类型与加载器                                     |
| Loader 层        | 负责把外部数据加载为统一 DataFrame                           |
| Checker 层       | 负责数据结构、模态、质量、目标列检查                               |
| Profiler 层      | 汇总统计信息，形成数据画像                                    |
| Builder 层       | 构建 Dataset Profile Object                        |
| Repository 层    | 负责数据库 CRUD                                       |
| Database 层      | 存储数据画像结果                                         |

---

# 4. 模块目录结构设计

建议新增独立业务模块目录：

```text
backend/app/modules/dataset_profile/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── source_resolver.py
├── profiler.py
├── builder.py
├── enums.py
├── exceptions.py
├── loaders/
│   ├── __init__.py
│   ├── base_loader.py
│   ├── matbench_loader.py
│   ├── file_loader.py
│   ├── database_loader.py
│   └── external_url_loader.py
└── checkers/
    ├── __init__.py
    ├── schema_checker.py
    ├── modality_checker.py
    ├── quality_checker.py
    └── target_checker.py
```

---

## 4.1 文件职责说明

| 文件                               | 职责                                                                     |
| -------------------------------- | ---------------------------------------------------------------------- |
| `api.py`                         | 定义 Dataset Profile 相关 HTTP 接口                                          |
| `schemas.py`                     | 定义请求、响应、内部 DTO                                                         |
| `service.py`                     | 编排完整数据加载、检查、画像、持久化流程                                                   |
| `model.py`                       | 定义 `dataset_profile` 数据库表                                              |
| `repository.py`                  | 提供 Dataset Profile CRUD 操作                                             |
| `context_builder.py`             | 读取 Task Specification 与 Task Interpretation，构建 Dataset Loading Context |
| `source_resolver.py`             | 根据 `dataset_intent` 判断数据来源和加载器                                         |
| `profiler.py`                    | 汇总各类检查结果，生成数据画像摘要                                                      |
| `builder.py`                     | 构建最终 Dataset Profile Object                                            |
| `enums.py`                       | 定义状态、数据来源、质量等级、样本规模等枚举                                                 |
| `exceptions.py`                  | 定义模块专用异常                                                               |
| `loaders/base_loader.py`         | 定义统一数据加载器接口                                                            |
| `loaders/matbench_loader.py`     | 加载 Matbench 风格公开基准数据集                                                  |
| `loaders/file_loader.py`         | 加载用户上传 CSV/Excel 文件                                                    |
| `loaders/database_loader.py`     | 后续扩展：加载系统内部数据库表                                                        |
| `loaders/external_url_loader.py` | 后续扩展：加载外部 URL 数据                                                       |
| `checkers/schema_checker.py`     | 检查列名、字段类型、目标列、输入列                                                      |
| `checkers/modality_checker.py`   | 检查输入模态与数据内容是否一致                                                        |
| `checkers/quality_checker.py`    | 检查缺失值、重复值、非法值、常量列等                                                     |
| `checkers/target_checker.py`     | 分析 regression/classification/ranking 目标变量                              |

---

# 5. 技术栈方案

## 5.1 后端技术栈

| 技术       | 推荐方案                | 说明                          |
| -------- | ------------------- | --------------------------- |
| Web 框架   | FastAPI             | 与当前系统保持一致                   |
| ORM      | SQLModel            | 与已完成模块保持一致                  |
| 数据库      | PostgreSQL 16       | 继续使用当前数据库                   |
| 灵活字段存储   | JSONB               | 存储复杂 Dataset Profile Object |
| 数据校验     | Pydantic v2         | 定义请求、响应、内部 DTO              |
| 配置管理     | pydantic-settings   | 管理数据路径、上传目录、数据集缓存路径等        |
| 表格处理     | pandas              | 加载 CSV/Excel、基础统计、缺失值分析     |
| 数值计算     | numpy               | 目标列统计、异常值检测                 |
| Excel 读取 | openpyxl            | 支持 `.xlsx` 文件读取             |
| 材料工具     | pymatgen            | 后续用于成分/结构合法性检查              |
| Matbench | matbench            | 后续用于公开 benchmark 数据集加载      |
| 日志       | logging / structlog | 记录加载状态、数据规模、错误信息            |
| 容器化      | Docker Compose      | 延续当前部署方式                    |
| 数据迁移     | Alembic             | 建议后续正式启用                    |

---

## 5.2 MVP 阶段推荐依赖

MVP 阶段建议优先引入：

```text
pandas
numpy
openpyxl
matbench
matminer
pymatgen
```

注意：

1. `matminer` 和 `pymatgen` 依赖较重；
2. 容器构建时间会增加；

---

## 5.3 前端技术栈

继续沿用当前前端技术栈：

| 技术              | 用途             |
| --------------- | -------------- |
| React           | 页面与组件          |
| TypeScript      | 类型定义           |
| Axios           | API 调用         |
| React Hook Form | 如后续需要上传文件或配置参数 |
| Zod             | 如后续需要前端参数校验    |

MVP 阶段前端主要新增结果展示组件，不需要复杂表单。

---

# 6. 核心数据对象设计

## 6.1 上游输入对象一：Task Specification Object

本模块主要消费以下字段：

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
status
```

使用原则：

1. 只读取，不修改；
2. 只接受 `valid` 或 `valid_with_warning` 状态；
3. 若状态为 `incomplete` 或 `invalid`，直接阻断。

---

## 6.2 上游输入对象二：Task Interpretation Object

本模块主要消费以下字段：

```text
interpretation_id
task_id
status
interpreted_task_type
interpreted_input_modality
interpreted_prediction_target
dataset_intent
planning_hint
warnings
ambiguities
```

其中最重要的是：

```text
dataset_intent
```

示例：

```json
{
  "dataset_reference": "matbench_expt_gap",
  "expected_input_columns": ["composition"],
  "expected_target_column": "band_gap",
  "requires_structure_file": false,
  "dataset_loading_hint": {
    "source_type": "public_benchmark",
    "possible_loader": "matbench",
    "needs_file_upload": false
  }
}
```

---

## 6.3 中间对象：Dataset Loading Context

`context_builder.py` 负责将上游两个对象转换为统一上下文。

```json
{
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "task_context": {
    "task_type": "regression",
    "prediction_target": "experimental band gap",
    "target_column": "band_gap",
    "evaluation_metric": "MAE"
  },
  "interpretation_context": {
    "interpreted_task_type": "regression",
    "interpreted_input_modality": "composition",
    "interpreted_material_domain": "inorganic crystals"
  },
  "dataset_context": {
    "dataset_description": "matbench_expt_gap",
    "dataset_intent": {},
    "expected_input_columns": ["composition"],
    "expected_target_column": "band_gap",
    "requires_structure_file": false
  }
}
```

---

## 6.4 中间对象：Dataset Source Resolution

`source_resolver.py` 负责输出数据源识别结果。

```json
{
  "source_type": "public_benchmark",
  "dataset_reference": "matbench_expt_gap",
  "loader_name": "matbench",
  "is_supported": true,
  "requires_file_upload": false,
  "messages": []
}
```

---

## 6.5 中间对象：Dataset Loading Result

Loader 层统一输出：

```json
{
  "is_loaded": true,
  "source_type": "public_benchmark",
  "dataset_reference": "matbench_expt_gap",
  "loader_name": "matbench",
  "dataframe_ref": "internal_runtime_dataframe",
  "n_rows": 4604,
  "n_columns": 2,
  "columns": ["composition", "band_gap"],
  "load_messages": []
}
```

说明：

1. 实际 DataFrame 不直接进入 JSON 响应；
2. Service 内部使用 DataFrame；
3. 响应和持久化中只保存结构化摘要；
4. 如需要预览，单独保存 `preview_json`。

---

## 6.6 输出对象：Dataset Profile Object

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
    "columns": [],
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
    "missing_values": {},
    "duplicates": {},
    "invalid_rows": {},
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
    "n_samples": 4604,
    "n_features_raw": 1,
    "has_missing_values": false,
    "has_duplicates": true,
    "requires_cleaning": true,
    "requires_target_transformation_check": true
  }
}
```

---

# 7. 数据库设计

## 7.1 表名

```text
dataset_profile
```

---

## 7.2 字段设计

| 字段                  | 类型          | 说明                          |
| ------------------- | ----------- | --------------------------- |
| `id`                | VARCHAR     | 主键，格式 `profile_xxxxxxxx`    |
| `task_id`           | VARCHAR     | 关联 `task_specification.id`  |
| `interpretation_id` | VARCHAR     | 关联 `task_interpretation.id` |
| `status`            | VARCHAR     | profiling 状态                |
| `source_type`       | VARCHAR     | 数据来源类型                      |
| `dataset_reference` | VARCHAR     | 数据集名称、文件 ID 或外部引用           |
| `loader_name`       | VARCHAR     | 使用的数据加载器                    |
| `n_samples`         | INTEGER     | 样本数                         |
| `n_columns`         | INTEGER     | 字段数                         |
| `input_modality`    | VARCHAR     | 输入模态                        |
| `target_column`     | VARCHAR     | 目标列                         |
| `quality_level`     | VARCHAR     | 数据质量等级                      |
| `is_usable_for_ml`  | BOOLEAN     | 是否可用于机器学习                   |
| `profile_json`      | JSONB       | 完整 Dataset Profile Object   |
| `preview_json`      | JSONB       | 数据预览                        |
| `error_message`     | TEXT        | 错误信息                        |
| `created_at`        | TIMESTAMPTZ | 创建时间                        |
| `updated_at`        | TIMESTAMPTZ | 更新时间                        |

---

## 7.3 索引设计

| 索引                                | 说明         |
| --------------------------------- | ---------- |
| `PRIMARY KEY(id)`                 | 主键索引       |
| `INDEX(task_id)`                  | 根据任务查询画像   |
| `INDEX(interpretation_id)`        | 根据解释结果查询画像 |
| `INDEX(status)`                   | 按状态筛选      |
| `INDEX(source_type)`              | 按数据来源筛选    |
| `INDEX(created_at)`               | 查询最新记录     |
| `INDEX(task_id, created_at DESC)` | 查询某任务最新画像  |

---

## 7.4 存储策略

继续沿用现有模块的混合存储方式：

```text
高频查询字段单独建列
+
复杂嵌套对象存入 JSONB
```

优点：

1. 与 Task Specification、Task Interpretation 模块保持一致；
2. 便于按 task_id、status、source_type 查询；
3. 便于灵活扩展 Dataset Profile Object；
4. 降低后续字段扩展时的数据库迁移频率。

---

# 8. API 设计

## 8.1 创建数据画像

```text
POST /api/dataset-profiles/{task_id}
```

### 功能

根据 `task_id` 读取上游任务信息，执行数据加载、检查与画像。

### 请求参数

| 参数      | 位置   | 必填 | 说明                          |
| ------- | ---- | -- | --------------------------- |
| task_id | path | 是  | Task Specification 生成的任务 ID |

### 请求体

MVP 阶段可为空。

后续扩展：

```json
{
  "force_rerun": false,
  "uploaded_file_id": "file_xxxxxxxx",
  "max_preview_rows": 20
}
```

### 响应

```json
{
  "success": true,
  "message": "Dataset profile created successfully.",
  "data": {
    "dataset_profile_id": "profile_xxxxxxxx",
    "task_id": "task_xxxxxxxx",
    "interpretation_id": "interp_xxxxxxxx",
    "status": "profiled",
    "dataset_source": {},
    "dataset_schema": {},
    "modality_check": {},
    "target_profile": {},
    "data_quality": {},
    "profiling_summary": {},
    "workflow_planning_input": {}
  }
}
```

---

## 8.2 查询数据画像

```text
GET /api/dataset-profiles/{dataset_profile_id}
```

### 功能

根据 `dataset_profile_id` 查询完整 Dataset Profile Object。

---

## 8.3 查询某任务最新数据画像

```text
GET /api/tasks/{task_id}/dataset-profile
```

### 功能

根据 `task_id` 查询最新一条 Dataset Profile Object。

### 下游用途

后续模块可以通过该接口获取数据事实：

```text
Workflow Planning
Pipeline Generation
Report Generation
前端任务详情页
```

---

## 8.4 重新执行数据画像

```text
POST /api/dataset-profiles/{task_id}/rerun
```

### 功能

重新执行数据加载、检查与画像。

### 处理原则

1. 不覆盖旧记录；
2. 新增一条 Dataset Profile 记录；
3. 默认查询最新记录；
4. 保留历史版本，便于追踪数据变化。

---

## 8.5 数据预览接口

```text
GET /api/dataset-profiles/{dataset_profile_id}/preview
```

### 功能

返回数据集前 N 行预览。

### 设计原则

1. 默认返回前 20 行；
2. 不返回完整数据集；
3. 大字段截断；
4. 不执行特征工程；
5. 不暴露服务器内部文件路径。

---

# 9. 核心业务数据流

## 9.1 创建 Dataset Profile 完整数据流

```text
用户点击 Run Dataset Profiling
    ↓
前端调用 POST /api/dataset-profiles/{task_id}
    ↓
dataset_profile/api.py 接收请求
    ↓
dataset_profile/service.py 开始业务编排
    ↓
context_builder.py 读取上游对象
        ├── Task Specification Object
        └── Latest Task Interpretation Object
    ↓
检查上游状态
        ├── Task Specification: valid / valid_with_warning
        └── Task Interpretation: interpreted / interpreted_with_warning
    ↓
构建 Dataset Loading Context
    ↓
source_resolver.py 识别数据来源
    ↓
选择对应 Loader
        ├── MatbenchLoader
        └── FileLoader
    ↓
Loader 返回 DataFrame
    ↓
schema_checker.py 检查列结构
    ↓
modality_checker.py 检查输入模态
    ↓
quality_checker.py 检查数据质量
    ↓
target_checker.py 分析目标变量
    ↓
profiler.py 汇总画像结果
    ↓
builder.py 构建 Dataset Profile Object
    ↓
repository.py 写入 dataset_profile 表
    ↓
返回 Dataset Profile Response
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
检查 status
    ↓
提取 dataset_description / input_type / target_column / task_type
```

本模块只读取 Task Specification，不修改原任务规格。

---

## 9.3 与 Task Interpretation 模块的数据流

```text
task_id
    ↓
TaskInterpretationRepository.get_latest_by_task_id(task_id)
    ↓
Task Interpretation Object
    ↓
检查 status
    ↓
提取 dataset_intent / interpreted_input_modality / interpreted_task_type
```

本模块重点消费：

```text
dataset_intent
```

---

## 9.4 与 Workflow Planning 模块的数据流

```text
Dataset Profile Object
    ↓
workflow_planning_input
    ↓
Workflow Planning Module
```

本模块向 Workflow Planning 提供：

```json
{
  "input_modality": "composition",
  "task_type": "regression",
  "target_column": "band_gap",
  "n_samples": 4604,
  "n_features_raw": 1,
  "has_missing_values": false,
  "has_duplicates": true,
  "requires_cleaning": true,
  "requires_target_transformation_check": true,
  "quality_level": "good"
}
```

Workflow Planning 模块后续基于这些数据事实决定：

1. 数据清洗策略；
2. 特征工程策略；
3. 验证集划分方式；
4. 候选模型范围；
5. 是否需要小样本策略；
6. 是否需要目标变换；
7. 是否需要类别不平衡处理。

---

# 10. Source Resolver 设计

## 10.1 职责

`source_resolver.py` 负责根据上游信息判断数据来源。

输入：

```text
dataset_description
dataset_intent
dataset_loading_hint
uploaded_file_id
```

输出：

```json
{
  "source_type": "public_benchmark",
  "dataset_reference": "matbench_expt_gap",
  "loader_name": "matbench",
  "is_supported": true
}
```

---

## 10.2 支持的数据来源类型

| source_type         | 说明                    | MVP 是否支持 |
| ------------------- | --------------------- | -------- |
| `public_benchmark`  | 公开基准数据集               | 是        |
| `uploaded_file`     | 用户上传文件                | 是        |
| `database_table`    | 系统内部数据库表              | 后续       |
| `external_url`      | 外部链接                  | 后续       |
| `materials_project` | Materials Project API | 后续       |
| `oqmd`              | OQMD 数据               | 后续       |
| `jarvis`            | JARVIS 数据             | 后续       |
| `unknown`           | 无法识别                  | 是，但阻断    |

---

## 10.3 MVP 数据源识别规则

优先级建议：

```text
uploaded_file_id 存在
    → uploaded_file

dataset_intent.dataset_loading_hint.source_type 存在
    → 使用该 source_type

dataset_reference 包含 matbench
    → public_benchmark + matbench_loader

dataset_description 包含 csv/xlsx/file/upload
    → uploaded_file

否则
    → unknown
```

---

# 11. Loader 层设计

## 11.1 Loader 抽象

所有 Loader 应遵循统一接口：

```text
load(context, source_resolution) → DatasetLoadingResult
```

统一约定：

1. 输入为 Dataset Loading Context；
2. 输出为 DataFrame + 加载摘要；
3. 不做数据清洗；
4. 不做特征工程；
5. 不修改目标列；
6. 不改变原始数据含义。

---

## 11.2 MatbenchLoader

### 职责

负责加载 Matbench 风格公开基准数据集。

### MVP 支持数据集

建议优先支持：

```text
matbench_expt_gap
matbench_mp_e_form
matbench_log_gvrh
matbench_log_kvrh
```

### 输出

```json
{
  "is_loaded": true,
  "loader_name": "matbench",
  "dataset_reference": "matbench_expt_gap",
  "n_rows": 4604,
  "n_columns": 2,
  "columns": ["composition", "band_gap"]
}
```

---

## 11.3 FileLoader

### 职责

负责加载用户上传的 CSV/Excel 文件。

### 支持格式

| 格式         | MVP 支持 |
| ---------- | ------ |
| `.csv`     | 是      |
| `.xlsx`    | 是      |
| `.xls`     | 可选     |
| `.jsonl`   | 后续     |
| `.parquet` | 后续     |

### 检查内容

1. 文件是否存在；
2. 文件格式是否支持；
3. 文件是否为空；
4. 是否能读取为表格；
5. 是否存在表头；
6. 是否超过大小限制。

---

## 11.4 后续 Loader 扩展

后续可新增：

```text
MaterialsProjectLoader
OQMDLoader
JARVISLoader
StructureFileLoader
DatabaseTableLoader
ExternalURLLoader
```

扩展原则：

1. 新增 Loader 不修改 Service 主流程；
2. 只需在 Source Resolver 中注册映射关系；
3. Loader 输出统一 DatasetLoadingResult；
4. Checker 和 Profiler 可复用。

---

# 12. Checker 层设计

## 12.1 SchemaChecker

### 职责

检查数据表结构是否满足任务要求。

### 输入

```text
DataFrame
expected_input_columns
expected_target_column
```

### 检查内容

1. 表格是否为空；
2. 目标列是否存在；
3. 输入列是否存在；
4. 是否存在重复列名；
5. 字段类型是否合理；
6. 是否存在全空列；
7. 是否存在列名大小写或空格问题。

### 输出

```json
{
  "target_column_exists": true,
  "input_columns_exist": true,
  "duplicate_columns": [],
  "schema_errors": [],
  "schema_warnings": []
}
```

---

## 12.2 ModalityChecker

### 职责

检查数据内容是否符合预期输入模态。

### 支持模态

| 模态          | 检查重点                           |
| ----------- | ------------------------------ |
| composition | 化学式列是否存在，样本是否类似化学式             |
| structure   | 是否存在 CIF/POSCAR/structure 相关字段 |
| descriptor  | 是否存在足够数值型描述符                   |
| text        | 是否存在文本字段                       |
| mixed       | 是否存在多类输入字段                     |

### composition 检查

1. 是否存在 `composition`、`formula`、`chemical_formula` 等列；
2. 样本是否为非空字符串；
3. 是否明显不符合化学式形式；
4. 后续可用 pymatgen 做合法性检查。

### structure 检查

1. 是否存在 `structure`、`cif`、`poscar`、`structure_path` 等列；
2. 是否需要外部结构文件；
3. 路径或结构字符串是否为空；
4. 后续可用 pymatgen 解析结构。

---

## 12.3 QualityChecker

### 职责

检查数据质量问题。

### 检查内容

1. 缺失值数量；
2. 缺失值比例；
3. 重复行；
4. 重复输入样本；
5. 空字符串；
6. 常量列；
7. 高缺失率列；
8. 非法数值；
9. 样本量过小；
10. 目标列缺失。

### 输出

```json
{
  "missing_values": {
    "total_missing": 0,
    "columns_with_missing": []
  },
  "duplicates": {
    "duplicate_rows": 0,
    "duplicate_input_samples": 3
  },
  "invalid_rows": {
    "count": 0,
    "examples": []
  },
  "warnings": [],
  "errors": []
}
```

---

## 12.4 TargetChecker

### 职责

分析目标变量是否适合当前任务类型。

### regression 任务

统计：

```text
dtype
missing_count
missing_ratio
min
max
mean
median
std
skewness
outlier_count
```

### classification 任务

统计：

```text
class_count
class_distribution
majority_class_ratio
minority_class_count
is_imbalanced
missing_ratio
```

### ranking 任务

统计：

```text
ranking_label_distribution
group_column_exists
ranking_label_validity
```

---

# 13. Profiler 设计

## 13.1 职责

`profiler.py` 负责汇总 Loader 和 Checker 输出，形成整体画像。

输入：

```text
loading_result
schema_check_result
modality_check_result
quality_check_result
target_check_result
```

输出：

```text
profiling_summary
workflow_planning_input
```

---

## 13.2 质量等级判断

建议定义：

| quality_level | 条件               |
| ------------- | ---------------- |
| good          | 无阻断错误，缺失值和异常较少   |
| fair          | 有轻微问题，但可进入后续流程   |
| poor          | 问题较多，需要清洗后再建模    |
| unusable      | 缺少目标列、数据为空、严重不匹配 |

---

## 13.3 是否可用于机器学习

```text
is_usable_for_ml = true
```

需满足：

1. 数据成功加载；
2. 样本数 > 0；
3. 目标列存在；
4. 至少存在一个输入列；
5. 输入模态基本一致；
6. 没有阻断性错误。

---

## 13.4 sample_size_level 规则

| sample_size_level | 样本量         |
| ----------------- | ----------- |
| very_small        | < 100       |
| small             | 100 - 999   |
| medium            | 1000 - 9999 |
| large             | >= 10000    |

---

# 14. Builder 设计

## 14.1 职责

`builder.py` 负责构建最终 Dataset Profile Object。

它不做检查规则判断，只负责对象组装。

---

## 14.2 构建内容

Builder 需要组装：

```text
dataset_profile_id
task_id
interpretation_id
status
dataset_source
dataset_schema
modality_check
target_profile
data_quality
profiling_summary
workflow_planning_input
created_at
updated_at
```

---

## 14.3 状态生成规则

| 条件             | status                |
| -------------- | --------------------- |
| 上游状态不满足        | blocked               |
| 数据加载失败         | failed                |
| 存在阻断错误         | failed                |
| 完成画像且无 warning | profiled              |
| 完成画像但有 warning | profiled_with_warning |

---

# 15. 状态管理设计

## 15.1 状态枚举

```text
pending
loading
loaded
checking
profiled
profiled_with_warning
failed
blocked
```

---

## 15.2 状态含义

| 状态                    | 含义                                     |
| --------------------- | -------------------------------------- |
| pending               | 已创建 profiling 任务，但尚未执行                 |
| loading               | 正在加载数据                                 |
| loaded                | 数据加载成功                                 |
| checking              | 正在执行 schema、modality、quality、target 检查 |
| profiled              | 完成画像且无明显问题                             |
| profiled_with_warning | 完成画像但存在非阻断性问题                          |
| failed                | 数据加载或检查失败                              |
| blocked               | 上游模块状态不满足条件                            |

---

## 15.3 状态流转

```text
收到请求
    ↓
检查上游状态
    ├── 不满足 → blocked
    └── 满足
          ↓
        pending
          ↓
        loading
          ↓
        loaded
          ↓
        checking
          ↓
        profiled / profiled_with_warning / failed
```

MVP 阶段可以同步执行整个流程，不必真的持久化每一个中间状态；但状态枚举应提前设计完整，便于后续异步任务队列扩展。

---

# 16. 异常处理设计

## 16.1 异常类型

建议新增模块专用异常：

```text
DatasetProfileException
├── DatasetProfileNotFoundException
├── DatasetContextBuildException
├── DatasetSourceUnresolvedException
├── DatasetSourceUnsupportedException
├── DatasetLoadException
├── DatasetSchemaException
├── DatasetModalityMismatchException
└── DatasetProfileValidationException
```

---

## 16.2 错误码设计

| 错误码                          | 场景                        |
| ---------------------------- | ------------------------- |
| `TASK_NOT_FOUND`             | task_id 不存在               |
| `TASK_NOT_READY`             | Task Specification 状态不允许  |
| `INTERPRETATION_REQUIRED`    | 尚未执行任务理解                  |
| `INTERPRETATION_NOT_READY`   | Task Interpretation 状态不允许 |
| `DATASET_INTENT_MISSING`     | dataset_intent 缺失         |
| `DATASET_SOURCE_UNRESOLVED`  | 无法识别数据来源                  |
| `DATASET_SOURCE_UNSUPPORTED` | 当前不支持该数据源                 |
| `DATASET_LOAD_FAILED`        | 数据加载失败                    |
| `DATASET_EMPTY`              | 数据为空                      |
| `TARGET_COLUMN_MISSING`      | 目标列不存在                    |
| `INPUT_COLUMN_MISSING`       | 输入列不存在                    |
| `MODALITY_MISMATCH`          | 输入模态不匹配                   |
| `DATASET_PROFILE_NOT_FOUND`  | 数据画像不存在                   |
| `PROFILE_VALIDATION_FAILED`  | 画像结果不合法                   |

---

## 16.3 非阻断性 Warning

以下问题不应直接中断流程，但应进入 `warnings`：

1. 样本量较小；
2. 存在少量缺失值；
3. 存在重复输入样本；
4. 目标变量偏态明显；
5. regression target 存在异常值；
6. classification label 不均衡；
7. 部分输入列类型不理想；
8. 数据集字段名与 expected_input_columns 不完全一致，但可推断；
9. 公开数据集名称识别成功，但字段映射存在轻微差异。

---

# 17. 配置设计

## 17.1 新增环境变量建议

```text
DATASET_UPLOAD_DIR=/app/uploads
DATASET_CACHE_DIR=/app/.cache/datasets
DATASET_MAX_FILE_SIZE_MB=100
DATASET_PREVIEW_ROWS=20
DATASET_ALLOWED_EXTENSIONS=csv,xlsx
ENABLE_MATBENCH_LOADER=true
ENABLE_FILE_LOADER=true
```

---

## 17.2 配置说明

| 配置项                          | 说明                   |
| ---------------------------- | -------------------- |
| `DATASET_UPLOAD_DIR`         | 用户上传文件存储目录           |
| `DATASET_CACHE_DIR`          | 公开数据集缓存目录            |
| `DATASET_MAX_FILE_SIZE_MB`   | 上传文件大小限制             |
| `DATASET_PREVIEW_ROWS`       | 默认数据预览行数             |
| `DATASET_ALLOWED_EXTENSIONS` | 允许的文件类型              |
| `ENABLE_MATBENCH_LOADER`     | 是否启用 Matbench Loader |
| `ENABLE_FILE_LOADER`         | 是否启用文件 Loader        |

---

# 18. 前端架构设计

## 18.1 前端目录结构

建议新增：

```text
frontend/src/modules/datasetProfile/
├── components/
│   ├── DatasetProfilePanel.tsx
│   ├── DatasetSourceCard.tsx
│   ├── DatasetSchemaCard.tsx
│   ├── DataQualityCard.tsx
│   ├── TargetProfileCard.tsx
│   ├── DatasetWarningList.tsx
│   ├── DatasetErrorList.tsx
│   └── DatasetPreviewTable.tsx
├── types.ts
└── constants.ts
```

---

## 18.2 前端 API 客户端

新增：

```text
frontend/src/api/datasetProfileApi.ts
```

封装：

```text
createDatasetProfile(taskId)
getDatasetProfile(profileId)
getLatestDatasetProfileByTaskId(taskId)
rerunDatasetProfile(taskId)
getDatasetPreview(profileId)
```

---

## 18.3 前端展示内容

MVP 阶段展示：

1. profile 状态；
2. 数据来源；
3. 数据集名称；
4. loader 名称；
5. 样本数；
6. 字段数；
7. 输入列；
8. 目标列；
9. 输入模态一致性；
10. 目标变量画像；
11. 缺失值统计；
12. 重复值统计；
13. 数据质量等级；
14. 是否可用于机器学习；
15. 是否 ready for workflow planning；
16. warnings；
17. errors；
18. 数据预览表格。

---

# 19. 与后续模块的扩展接口

## 19.1 提供给 Workflow Planning 的接口

Workflow Planning 模块应通过以下接口读取数据画像：

```text
GET /api/tasks/{task_id}/dataset-profile
```

重点消费：

```text
workflow_planning_input
dataset_schema
target_profile
data_quality
profiling_summary
```

---

## 19.2 workflow_planning_input 推荐结构

```json
{
  "task_type": "regression",
  "input_modality": "composition",
  "target_column": "band_gap",
  "input_columns": ["composition"],
  "n_samples": 4604,
  "n_columns": 2,
  "sample_size_level": "medium",
  "has_missing_values": false,
  "has_duplicates": true,
  "requires_cleaning": true,
  "requires_target_transformation_check": true,
  "target_distribution": {
    "is_skewed": true,
    "has_outliers": true
  },
  "quality_level": "good",
  "is_usable_for_ml": true
}
```

---

## 19.3 后续 Pipeline Generation 可复用字段

Pipeline Generation 后续可间接使用：

```text
input_columns
target_column
input_modality
n_samples
quality_level
requires_cleaning
```

但 Dataset Profile 模块不直接服务 Pipeline Generation，应由 Workflow Planning 进行中间决策。

---

## 19.4 后续 Report Generation 可复用字段

Report Generation 可使用：

```text
dataset_source
dataset_schema
data_quality
target_profile
profiling_summary
```

用于自动生成实验报告中的 Dataset 部分。

---

# 20. 安全与稳定性设计

## 20.1 文件安全

对于 uploaded_file 数据源，必须考虑：

1. 文件大小限制；
2. 文件类型白名单；
3. 不信任用户上传文件名；
4. 文件路径不直接暴露给前端；
5. 禁止执行上传文件；
6. 读取失败要返回清晰错误；
7. 预览数据需限制行数和字段长度。

---

## 20.2 数据隐私

1. 不在日志中打印完整数据集；
2. 不在 API 响应中返回完整数据；
3. 只返回 preview；
4. 大字段截断；
5. 后续可加入数据脱敏策略。

---

## 20.3 稳定性

1. 大文件读取需要限制大小；
2. Profiling 阶段避免长时间阻塞；
3. 后续建议引入异步任务队列；
4. 数据集加载失败不应影响上游任务对象；
5. 每次 rerun 新增记录，不覆盖历史结果。

---

# 21. MVP 实现范围

## 21.1 MVP 必须实现

1. 新增 `dataset_profile` 后端模块；
2. 能通过 task_id 读取 Task Specification；
3. 能通过 task_id 读取最新 Task Interpretation；
4. 能检查上游状态；
5. 能构建 Dataset Loading Context；
6. 能识别 `public_benchmark` 和 `uploaded_file`；
7. 能加载至少一种公开 benchmark 风格数据；
8. 能加载 CSV 文件；
9. 能检查目标列是否存在；
10. 能检查输入列是否存在；
11. 能统计样本数和字段数；
12. 能检查缺失值；
13. 能检查重复值；
14. 能分析 regression target；
15. 能分析 classification label 分布；
16. 能生成 Dataset Profile Object；
17. 能持久化 Dataset Profile Object；
18. 能查询最新 Dataset Profile；
19. 能 rerun profiling 且不覆盖旧结果；
20. 能返回 preview 数据。

---

## 21.2 MVP 不实现

1. 不做特征工程；
2. 不生成材料描述符；
3. 不选择模型；
4. 不生成 Pipeline；
5. 不执行训练；
6. 不调用 LLM 做数据清洗建议；
7. 不做复杂数据可视化；
8. 不支持完整 Materials Project API；
9. 不支持完整 OQMD/JARVIS 加载；
10. 不支持大规模异步任务队列；
11. 不做权限系统。

---

# 22. 后续演进方向

## 22.1 V2：更多材料数据源

扩展：

1. Materials Project API；
2. OQMD；
3. JARVIS；
4. NOMAD；
5. 自定义数据库表。

---

## 22.2 V3：结构数据支持

新增：

1. CIF 文件上传；
2. POSCAR 文件上传；
3. pymatgen Structure 解析；
4. 晶体结构合法性检查；
5. structure-based dataset profile。

---

## 22.3 V4：数据缓存与版本管理

新增：

1. 数据集缓存；
2. 数据版本 hash；
3. 数据快照；
4. profile 历史对比；
5. 数据变更检测。

---

## 22.4 V5：异步 Profiling 任务

当数据集较大时，引入：

```text
FastAPI
  ↓
Task Queue
  ↓
Worker
  ↓
Dataset Profiling
  ↓
Status Polling / SSE
```

可选技术：

1. Celery + Redis；
2. RQ + Redis；
3. Dramatiq；
4. FastAPI BackgroundTasks；
5. Arq。

MVP 阶段暂不建议引入复杂异步队列。

---

# 23. 推荐开发顺序

## 阶段一：后端基础结构

1. 创建 `dataset_profile` 模块目录；
2. 定义 `model.py`；
3. 定义 `schemas.py`；
4. 定义 `repository.py`；
5. 注册 API 路由。

---

## 阶段二：打通上游模块

1. 实现 `context_builder.py`；
2. 查询 Task Specification；
3. 查询最新 Task Interpretation；
4. 检查上游状态；
5. 构建 Dataset Loading Context。

---

## 阶段三：数据源识别与加载

1. 实现 `source_resolver.py`；
2. 实现 `BaseLoader`；
3. 实现 `MatbenchLoader` 或 mock benchmark loader；
4. 实现 `FileLoader`；
5. 输出统一 DatasetLoadingResult。

---

## 阶段四：数据检查

1. 实现 `SchemaChecker`；
2. 实现 `ModalityChecker`；
3. 实现 `QualityChecker`；
4. 实现 `TargetChecker`。

---

## 阶段五：画像构建与持久化

1. 实现 `profiler.py`；
2. 实现 `builder.py`；
3. 写入 `dataset_profile` 表；
4. 实现查询、最新查询、rerun、preview 接口。

---

## 阶段六：前端展示

1. 新增 `DatasetProfilePanel`；
2. 接入 `datasetProfileApi.ts`；
3. 展示数据来源、schema、质量、target profile；
4. 展示 warnings/errors；
5. 展示 preview table；
6. 显示是否 ready for workflow planning。

---

# 24. 总结

Dataset Loading, Checking, and Profiling 模块应被设计为 MLAgent 的“数据事实层”。

它的核心职责是：

```text
Task Specification + Task Interpretation
    ↓
Dataset Loading Context
    ↓
Load raw dataset
    ↓
Check schema / modality / quality / target
    ↓
Generate Dataset Profile Object
    ↓
Provide workflow_planning_input
```

该模块不负责规划机器学习流程，也不负责选择特征和模型，而是为后续 Workflow Planning 模块提供可靠的数据依据。

最终，它应回答以下问题：

```text
数据能否加载？
数据来自哪里？
数据有多少样本和字段？
输入列和目标列是否存在？
输入模态是否匹配？
数据质量如何？
目标变量分布如何？
是否具备进入 Workflow Planning 的基本条件？
```

架构上应坚持：

1. 独立业务模块；
2. 与已完成模块通过 task_id 和 interpretation_id 解耦协作；
3. Loader、Checker、Profiler 分层清晰；
4. 统一 Dataset Profile Object 输出；
5. 画像结果可持久化、可查询、可重跑；
6. 为 Workflow Planning、Pipeline Generation 和 Report Generation 预留稳定接口。

```
```
