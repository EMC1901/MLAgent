下面给你一份可直接复制为 `.md` 的 **Automated Feature Engineering 模块架构与技术栈方案**。该方案基于当前已完成的四个模块设计：系统已经具备 `Task Specification Object`、`Task Interpretation Object`、`Dataset Profile Object`、`Workflow Plan Object` 的创建、查询和持久化能力；其中 Workflow Planning 已输出 `feature_strategy` 和 `pipeline_generation_input`，可作为本模块的核心上游输入。

````markdown id="automated_feature_engineering_architecture"
# Automated Feature Engineering 模块架构与技术栈方案

## 1. 模块名称

Automated Feature Engineering  
自动化特征工程模块

---

## 2. 模块定位

本模块是 MLAgent 系统的第五个核心业务模块，位于：

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

当前系统已完成四个模块：

1. **Task Specification**：生成用户任务规格对象；
2. **LLM-based Task Interpretation**：生成任务语义理解对象；
3. **Dataset Loading, Checking, and Profiling**：加载数据并生成数据画像；
4. **Workflow Planning**：基于任务语义和数据画像生成工作流规划。

本模块的核心职责是：

```text
Workflow Plan 中的 feature_strategy
    +
Dataset Profile 中的数据事实
    ↓
自动化特征工程
    ↓
Feature Engineering Object
    +
Feature Matrix Artifact
    +
downstream_input
```

本模块只负责生成机器学习可用的特征矩阵和特征工程元数据，不负责训练模型、不负责 HPO、不负责评估模型表现、不负责生成完整 Pipeline 代码。

---

# 3. 总体架构目标

## 3.1 架构目标

Automated Feature Engineering 模块需要满足以下目标：

1. 与前四个模块通过 `task_id` 自然衔接；
2. 读取最新 Task Specification、Task Interpretation、Dataset Profile、Workflow Plan；
3. 基于 Workflow Plan 的 `feature_strategy` 自动选择特征工程路径；
4. 基于 Dataset Profile 的 `dataset_source` 重新加载原始数据；
5. 支持 composition、descriptor 两类 MVP 输入；
6. 对 structure 输入提供明确的 unsupported 或 fallback 机制；
7. 生成标准化 feature matrix；
8. 将大型特征矩阵保存为 artifact，不直接存入数据库；
9. 将特征工程元数据、质量检查结果、artifact 引用写入 PostgreSQL；
10. 输出后续 Pipeline Generation 可消费的 `downstream_input`；
11. 支持查询、重跑、预览和版本追踪；
12. 为后续 Pipeline Generation、Pipeline Execution、Metric Evaluation、Report Generation 预留扩展接口。

---

## 3.2 总体架构图

```text
Frontend
  └── Feature Engineering Panel
        ↓
Backend API Layer
  └── feature_engineering/api.py
        ↓
Service Layer
  └── feature_engineering/service.py
        ↓
Context Builder
  ├── Read Task Specification
  ├── Read Latest Task Interpretation
  ├── Read Latest Dataset Profile
  └── Read Latest Workflow Plan
        ↓
Data Loader Adapter
  └── Reuse Dataset Profile loaders to reload raw data
        ↓
Strategy Resolver
  └── Parse workflow_plan.feature_strategy
        ↓
Featurizer Layer
  ├── CompositionFeaturizer
  ├── DescriptorFeaturizer
  └── StructureFeaturizer placeholder
        ↓
Feature Matrix Builder
  └── Combine features + target + sample_id
        ↓
Feature Quality Checker
  └── Check missing / constant / invalid features
        ↓
Artifact Manager
  └── Save feature matrix to local artifact path
        ↓
Feature Engineering Builder
  └── Build Feature Engineering Object
        ↓
Repository Layer
  └── Persist metadata into feature_engineering table
        ↓
Downstream Interface
  └── Pipeline Generation / Execution / Evaluation
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
Data Loader Adapter 数据加载适配层
  ↓
Strategy Resolver 策略解析层
  ↓
Featurizer 特征生成层
  ↓
Feature Quality Checker 特征质量检查层
  ↓
Artifact Manager 特征矩阵存储层
  ↓
Builder 对象构建层
  ↓
Repository 数据访问层
  ↓
Database 数据层
```

各层职责如下：

| 层级                      | 职责                                   |
| ----------------------- | ------------------------------------ |
| API 层                   | 接收 HTTP 请求、调用 Service、返回统一响应         |
| Service 层               | 编排完整自动化特征工程流程                        |
| Context Builder         | 读取并整合四个上游模块输出                        |
| Data Loader Adapter     | 复用 Dataset Profile 模块的数据加载器，重建原始数据   |
| Strategy Resolver       | 解析 Workflow Plan 中的 feature_strategy |
| Featurizer 层            | 根据输入模态生成特征                           |
| Feature Quality Checker | 检查特征矩阵质量                             |
| Artifact Manager        | 保存和读取特征矩阵文件                          |
| Builder 层               | 构建 Feature Engineering Object        |
| Repository 层            | 负责 feature_engineering 表 CRUD        |
| Database 层              | 存储结构化字段、JSONB 元数据和 artifact 引用       |

---

# 4. 模块目录结构设计

建议新增独立业务模块：

```text
backend/app/modules/feature_engineering/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── data_loader_adapter.py
├── strategy_resolver.py
├── feature_matrix_builder.py
├── artifact_manager.py
├── builder.py
├── enums.py
├── exceptions.py
├── featurizers/
│   ├── __init__.py
│   ├── base_featurizer.py
│   ├── composition_featurizer.py
│   ├── descriptor_featurizer.py
│   └── structure_featurizer.py
└── checkers/
    ├── __init__.py
    └── feature_quality_checker.py
```

---

## 4.1 文件职责说明

| 文件                                      | 职责                                                   |
| --------------------------------------- | ---------------------------------------------------- |
| `api.py`                                | 定义 Feature Engineering 相关 HTTP 接口                    |
| `schemas.py`                            | 定义请求、响应、内部 DTO                                       |
| `service.py`                            | 编排上游读取、数据重载、特征生成、质量检查、artifact 保存、持久化                |
| `model.py`                              | 定义 `feature_engineering` 数据库表                        |
| `repository.py`                         | 提供 Feature Engineering 结果 CRUD                       |
| `context_builder.py`                    | 读取 Task、Interpretation、Dataset Profile、Workflow Plan |
| `data_loader_adapter.py`                | 复用 Dataset Profile 模块 Loader，重新加载原始数据                |
| `strategy_resolver.py`                  | 解析 Workflow Plan 中的 `feature_strategy`               |
| `feature_matrix_builder.py`             | 合并 sample_id、features、target，构建标准 feature matrix     |
| `artifact_manager.py`                   | 保存、读取、预览特征矩阵 artifact                                |
| `builder.py`                            | 构建最终 Feature Engineering Object                      |
| `enums.py`                              | 定义状态、特征类型、artifact 类型等枚举                             |
| `exceptions.py`                         | 定义模块专用异常                                             |
| `featurizers/base_featurizer.py`        | 定义统一 Featurizer 接口                                   |
| `featurizers/composition_featurizer.py` | composition 输入的特征生成器                                 |
| `featurizers/descriptor_featurizer.py`  | 已有 descriptor 输入的特征整理器                               |
| `featurizers/structure_featurizer.py`   | structure 输入的占位或后续扩展实现                               |
| `checkers/feature_quality_checker.py`   | 检查特征矩阵缺失、常量、全空、非数值等问题                                |

---

# 5. 技术栈方案

## 5.1 后端技术栈

继续沿用当前系统技术栈，并增加少量特征工程相关依赖。

| 技术         | 推荐方案              | 说明                                    |
| ---------- | ----------------- | ------------------------------------- |
| Web 框架     | FastAPI           | 与当前系统保持一致                             |
| ORM        | SQLModel          | 与前四个模块保持一致                            |
| 数据库        | PostgreSQL 16     | 使用现有数据库                               |
| 灵活字段存储     | JSONB             | 存储 Feature Engineering Object 元数据     |
| 数据校验       | Pydantic v2       | 请求、响应、内部对象校验                          |
| 配置管理       | pydantic-settings | 管理 artifact 路径、输出格式等                  |
| 表格处理       | pandas            | 特征矩阵构建与数据处理                           |
| 数值计算       | numpy             | 数值特征统计与质量检查                           |
| 文件格式       | parquet / csv     | 特征矩阵 artifact 存储                      |
| Parquet 支持 | pyarrow           | 推荐用于高效存储特征矩阵                          |
| 材料工具       | pymatgen          | 后续用于 Composition/Structure 解析         |
| 材料特征库      | matminer          | 后续用于 Magpie / composition descriptors |
| 容器化        | Docker Compose    | 延续当前部署方式                              |
| 数据库迁移      | Alembic           | 后续建议启用                                |

---

## 5.2 MVP 阶段推荐依赖

当前系统已有：

```text
pandas
numpy
openpyxl
```

MVP 建议新增：

```text
pyarrow
```

原因：

1. Parquet 更适合保存特征矩阵；
2. 比 CSV 更节省空间；
3. 能较好保留数值列类型；
4. 后续 Pipeline Execution 读取更稳定。

MVP 可暂不强制引入：

```text
pymatgen
matminer
```

原因：

1. 依赖较重；
2. 容器构建时间增加；
3. MVP 可先实现轻量级 composition descriptor；
4. 后续再升级为材料科学标准 featurizer。

---

## 5.3 后续材料科学依赖

中期建议引入：

| 依赖           | 用途                                          |
| ------------ | ------------------------------------------- |
| pymatgen     | 解析 Composition、Structure、CIF/POSCAR         |
| matminer     | 生成 Magpie、ElementProperty、Stoichiometry 等特征 |
| scikit-learn | 特征缩放、特征选择、imputation、Pipeline Execution     |
| joblib       | 保存后续 scaler、selector、pipeline 等对象           |

说明：

scikit-learn 虽然后续更常用于模型训练，但特征工程模块可能也需要其 imputer、scaler、variance threshold 等组件。MVP 阶段可以只标记 `scaling_required` 和 `feature_selection_required`，不实际执行缩放和选择。

---

## 5.4 前端技术栈

继续沿用：

| 技术              | 用途                           |
| --------------- | ---------------------------- |
| React           | 组件展示                         |
| TypeScript      | 类型定义                         |
| Axios           | API 调用                       |
| React Hook Form | 后续用户覆盖 feature_strategy 时可复用 |
| Zod             | 后续前端参数校验可复用                  |

MVP 阶段主要新增结果展示组件，不需要复杂表单。

---

# 6. 核心数据对象设计

## 6.1 上游输入对象一：Task Specification Object

本模块主要消费：

```text
task_id
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
3. 不重新做任务表单校验。

---

## 6.2 上游输入对象二：Task Interpretation Object

本模块主要消费：

```text
interpretation_id
interpreted_task_type
interpreted_input_modality
interpreted_material_domain
interpreted_prediction_target
constraint_interpretation
warnings
```

使用原则：

1. 只读取最新一条；
2. 只接受 `interpreted` 或 `interpreted_with_warning`；
3. 不重新执行 LLM 任务理解。

---

## 6.3 上游输入对象三：Dataset Profile Object

本模块主要消费：

```text
dataset_profile_id
dataset_source
dataset_schema
workflow_planning_input
data_quality
target_profile
profiling_summary
preview_json
```

其中关键字段是：

```text
dataset_source
dataset_schema.input_columns
dataset_schema.target_column
profiling_summary.is_usable_for_ml
```

使用原则：

1. 只读取最新一条；
2. 只接受 `profiled` 或 `profiled_with_warning`；
3. 必须满足 `is_usable_for_ml = true`；
4. 可复用其数据源信息重新加载原始数据。

---

## 6.4 上游输入对象四：Workflow Plan Object

本模块主要消费：

```text
workflow_plan_id
data_strategy
feature_strategy
evaluation_strategy
pipeline_generation_input
planning_warnings
planning_assumptions
status
```

其中关键字段是：

```text
feature_strategy
```

示例：

```json
{
  "feature_type": "composition_descriptors",
  "recommended_featurizers": [
    "elemental_property_statistics",
    "stoichiometric_features"
  ],
  "requires_structure_features": false,
  "feature_selection_required": true,
  "feature_scaling_required": true
}
```

使用原则：

1. 只读取最新一条；
2. 只接受 `planned` 或 `planned_with_warning`；
3. 不修改 Workflow Plan；
4. 不重新调用 LLM 规划。

---

## 6.5 中间对象：Feature Engineering Context

`context_builder.py` 负责构建该对象。

```json
{
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "dataset_profile_id": "profile_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "task_context": {
    "task_type": "regression",
    "target_column": "band_gap",
    "evaluation_metric": "MAE"
  },
  "data_context": {
    "dataset_source": {},
    "input_columns": ["composition"],
    "target_column": "band_gap",
    "input_modality": "composition",
    "is_usable_for_ml": true
  },
  "feature_context": {
    "feature_strategy": {},
    "feature_type": "composition_descriptors",
    "recommended_featurizers": [],
    "feature_scaling_required": true,
    "feature_selection_required": true
  }
}
```

---

## 6.6 中间对象：Resolved Feature Strategy

`strategy_resolver.py` 负责构建该对象。

```json
{
  "feature_type": "composition_descriptors",
  "input_modality": "composition",
  "selected_featurizers": [
    "elemental_property_statistics",
    "stoichiometric_features"
  ],
  "fallback_featurizers": [],
  "unsupported_featurizers": [],
  "scaling_required": true,
  "feature_selection_required": true,
  "structure_features_required": false
}
```

---

## 6.7 输出对象：Feature Engineering Object

```json
{
  "feature_engineering_id": "feat_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "dataset_profile_id": "profile_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "status": "completed",
  "input_modality": "composition",
  "feature_type": "composition_descriptors",
  "feature_generation": {
    "selected_featurizers": [
      "elemental_property_statistics",
      "stoichiometric_features"
    ],
    "executed_featurizers": []
  },
  "feature_matrix": {
    "artifact_id": "artifact_features_xxxxxxxx",
    "storage_type": "local_file",
    "file_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
    "n_samples": 4604,
    "n_features": 140,
    "target_column": "band_gap",
    "index_column": "sample_id"
  },
  "feature_schema": {
    "feature_columns": [],
    "numeric_feature_count": 140,
    "categorical_feature_count": 0,
    "constant_feature_count": 0,
    "all_missing_feature_count": 0
  },
  "feature_quality": {
    "missing_values": {},
    "invalid_features": [],
    "dropped_features": [],
    "failed_samples": []
  },
  "preprocessing_requirements": {
    "scaling_required": true,
    "imputation_required": false,
    "feature_selection_required": true
  },
  "downstream_input": {
    "feature_matrix_artifact_id": "artifact_features_xxxxxxxx",
    "target_column": "band_gap",
    "feature_columns": [],
    "task_type": "regression",
    "primary_metric": "MAE",
    "ready_for_pipeline_generation": true
  },
  "warnings": [],
  "errors": [],
  "created_at": "2026-05-02T10:00:00",
  "updated_at": "2026-05-02T10:00:00"
}
```

---

# 7. 数据库设计

## 7.1 表名

```text
feature_engineering
```

---

## 7.2 字段设计

| 字段                      | 类型          | 说明                            |
| ----------------------- | ----------- | ----------------------------- |
| `id`                    | VARCHAR     | 主键，格式 `feat_xxxxxxxx`         |
| `task_id`               | VARCHAR     | 关联 Task Specification         |
| `interpretation_id`     | VARCHAR     | 关联 Task Interpretation        |
| `dataset_profile_id`    | VARCHAR     | 关联 Dataset Profile            |
| `workflow_plan_id`      | VARCHAR     | 关联 Workflow Plan              |
| `status`                | VARCHAR     | 特征工程状态                        |
| `input_modality`        | VARCHAR     | 输入模态                          |
| `feature_type`          | VARCHAR     | 特征类型                          |
| `n_samples`             | INTEGER     | 样本数                           |
| `n_features`            | INTEGER     | 特征数                           |
| `target_column`         | VARCHAR     | 目标列                           |
| `artifact_id`           | VARCHAR     | 特征矩阵 artifact ID              |
| `artifact_path`         | TEXT        | 特征矩阵文件路径                      |
| `is_ready_for_pipeline` | BOOLEAN     | 是否可进入 Pipeline Generation     |
| `feature_json`          | JSONB       | 完整 Feature Engineering Object |
| `preview_json`          | JSONB       | 特征矩阵预览                        |
| `error_message`         | TEXT        | 错误信息                          |
| `created_at`            | TIMESTAMPTZ | 创建时间                          |
| `updated_at`            | TIMESTAMPTZ | 更新时间                          |

---

## 7.3 索引设计

| 索引                                | 说明           |
| --------------------------------- | ------------ |
| `PRIMARY KEY(id)`                 | 主键索引         |
| `INDEX(task_id)`                  | 根据任务查询特征工程结果 |
| `INDEX(interpretation_id)`        | 根据任务理解结果查询   |
| `INDEX(dataset_profile_id)`       | 根据数据画像查询     |
| `INDEX(workflow_plan_id)`         | 根据工作流规划查询    |
| `INDEX(status)`                   | 按状态筛选        |
| `INDEX(created_at)`               | 查询最新记录       |
| `INDEX(task_id, created_at DESC)` | 查询某任务最新结果    |

---

## 7.4 存储策略

继续沿用当前系统的混合存储策略：

```text
高频查询字段单独建列
+
复杂嵌套对象存入 JSONB
+
大型特征矩阵保存为文件 artifact
```

### 不建议

```text
不建议将完整特征矩阵存入 JSONB
```

原因：

1. 特征矩阵可能很大；
2. JSONB 不适合高维数值矩阵；
3. 后续 Pipeline Execution 读取文件更方便；
4. Parquet/CSV 文件更适合作为 ML artifact。

---

# 8. Artifact 设计

## 8.1 Artifact 存储目录

建议新增配置：

```text
FEATURE_ARTIFACT_DIR=/app/artifacts/features
FEATURE_ARTIFACT_FORMAT=parquet
FEATURE_PREVIEW_ROWS=20
```

推荐目录结构：

```text
/app/artifacts/features/
└── feat_xxxxxxxx/
    ├── features.parquet
    ├── feature_schema.json
    └── metadata.json
```

---

## 8.2 Artifact ID 规则

```text
artifact_features_ + 8 位 uuid hex
```

示例：

```text
artifact_features_a1b2c3d4
```

---

## 8.3 Artifact 内容

| 文件                    | 内容                                                |
| --------------------- | ------------------------------------------------- |
| `features.parquet`    | 完整特征矩阵，包含 sample_id、feature columns、target_column |
| `feature_schema.json` | 特征列清单、特征类型、数量                                     |
| `metadata.json`       | task_id、workflow_plan_id、生成时间、featurizer 信息       |

---

## 8.4 Artifact 设计原则

1. API 不直接返回完整 feature matrix；
2. 数据库只保存 artifact 引用；
3. 预览数据存入 `preview_json`；
4. 后续 Pipeline Execution 通过 artifact_path 读取；
5. rerun 时生成新的 artifact，不覆盖旧 artifact。

---

# 9. API 设计

## 9.1 创建 Feature Engineering 结果

```text
POST /api/feature-engineering/{task_id}
```

### 功能

根据 `task_id` 读取上游四个模块结果，执行自动化特征工程。

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
  "override_feature_strategy": null,
  "output_format": "parquet"
}
```

### 响应

```json
{
  "success": true,
  "message": "Feature engineering completed successfully.",
  "data": {
    "feature_engineering_id": "feat_xxxxxxxx",
    "task_id": "task_xxxxxxxx",
    "workflow_plan_id": "plan_xxxxxxxx",
    "status": "completed",
    "input_modality": "composition",
    "feature_type": "composition_descriptors",
    "feature_matrix": {},
    "feature_schema": {},
    "feature_quality": {},
    "downstream_input": {}
  }
}
```

---

## 9.2 查询 Feature Engineering 结果

```text
GET /api/feature-engineering/{feature_engineering_id}
```

### 功能

根据 `feature_engineering_id` 查询完整 Feature Engineering Object。

---

## 9.3 查询某任务最新 Feature Engineering 结果

```text
GET /api/tasks/{task_id}/feature-engineering
```

### 功能

返回某个 `task_id` 最新一条 Feature Engineering Object。

---

## 9.4 重新执行 Feature Engineering

```text
POST /api/feature-engineering/{task_id}/rerun
```

### 功能

重新执行特征工程。

### 原则

1. 不覆盖旧记录；
2. 新增一条 Feature Engineering 记录；
3. 生成新的 feature artifact；
4. 默认查询最新一条；
5. 保留历史版本，便于比较不同特征方案。

---

## 9.5 特征矩阵预览接口

```text
GET /api/feature-engineering/{feature_engineering_id}/preview
```

### 功能

返回特征矩阵前 N 行预览。

### 设计原则

1. 默认返回前 20 行；
2. 不返回完整矩阵；
3. 数值保留合理精度；
4. 大字段截断；
5. 若 `preview_json` 缺失，可从 artifact 读取前 N 行。

---

# 10. 核心业务数据流

## 10.1 创建 Feature Engineering 完整数据流

```text
用户点击 Run Feature Engineering
    ↓
前端调用 POST /api/feature-engineering/{task_id}
    ↓
feature_engineering/api.py 接收请求
    ↓
feature_engineering/service.py 开始业务编排
    ↓
context_builder.py 读取上游对象
        ├── Task Specification Object
        ├── Latest Task Interpretation Object
        ├── Latest Dataset Profile Object
        └── Latest Workflow Plan Object
    ↓
检查上游状态
        ├── Task Specification: valid / valid_with_warning
        ├── Task Interpretation: interpreted / interpreted_with_warning
        ├── Dataset Profile: profiled / profiled_with_warning
        └── Workflow Plan: planned / planned_with_warning
    ↓
检查 Dataset Profile 是否 usable_for_ml
    ↓
检查 Workflow Plan 是否存在 feature_strategy
    ↓
data_loader_adapter.py 复用 Dataset Profile Loader 重新加载原始数据
    ↓
strategy_resolver.py 解析 feature_strategy
    ↓
选择 Featurizer
        ├── CompositionFeaturizer
        ├── DescriptorFeaturizer
        └── StructureFeaturizer placeholder
    ↓
生成 feature dataframe
    ↓
feature_matrix_builder.py 构建标准 feature matrix
    ↓
feature_quality_checker.py 检查特征质量
    ↓
artifact_manager.py 保存 feature matrix artifact
    ↓
builder.py 构建 Feature Engineering Object
    ↓
repository.py 写入 feature_engineering 表
    ↓
返回 Feature Engineering Response
```

---

## 10.2 与 Task Specification 模块的数据流

```text
task_id
    ↓
TaskSpecificationRepository.get_by_id(task_id)
    ↓
Task Specification Object
    ↓
校验 status
    ↓
提取 task_type / target_column / evaluation_metric
```

本模块只读，不修改 Task Specification。

---

## 10.3 与 Task Interpretation 模块的数据流

```text
task_id
    ↓
TaskInterpretationRepository.get_latest_by_task_id(task_id)
    ↓
Task Interpretation Object
    ↓
校验 status
    ↓
提取 interpreted_input_modality / material_domain / target info
```

本模块只读，不重新执行 LLM interpretation。

---

## 10.4 与 Dataset Profile 模块的数据流

```text
task_id
    ↓
DatasetProfileRepository.get_latest_by_task_id(task_id)
    ↓
Dataset Profile Object
    ↓
校验 status 与 is_usable_for_ml
    ↓
提取 dataset_source / dataset_schema / input_columns / target_column
    ↓
复用 Loader 重建 raw dataframe
```

本模块可复用 Dataset Profile 模块的数据加载器，但不重新进行完整 profiling。

---

## 10.5 与 Workflow Planning 模块的数据流

```text
task_id
    ↓
WorkflowPlanRepository.get_latest_by_task_id(task_id)
    ↓
Workflow Plan Object
    ↓
校验 status
    ↓
提取 feature_strategy / evaluation_strategy / pipeline_generation_input
```

本模块执行 Workflow Plan 中的 `feature_strategy`，但不修改 Workflow Plan。

---

## 10.6 与 Pipeline Generation 模块的数据流

```text
Feature Engineering Object
    ↓
downstream_input
    ↓
Pipeline Generation Module
```

Pipeline Generation 后续重点消费：

```text
feature_matrix_artifact_id
artifact_path
feature_columns
target_column
task_type
primary_metric
preprocessing_requirements
ready_for_pipeline_generation
```

---

# 11. Data Loader Adapter 设计

## 11.1 职责

`data_loader_adapter.py` 负责复用 Dataset Profile 模块已有 Loader，以便重新获得 raw dataframe。

---

## 11.2 复用原则

Dataset Profile 模块已经实现：

1. `MatbenchLoader`
2. `FileLoader`
3. `source_resolver`
4. 文件上传与读取能力

本模块不应重新实现完整数据加载系统，而应适配复用。

---

## 11.3 处理方式

输入：

```text
dataset_profile.dataset_source
dataset_profile.dataset_reference
dataset_profile.loader_name
uploaded_file_id / uploaded_file_path
```

输出：

```text
raw_dataframe
loading_summary
```

---

## 11.4 注意事项

1. 不重新执行完整 dataset profiling；
2. 不重新判断数据质量等级；
3. 只做必要的读取成功检查；
4. 如果原始文件丢失，应返回 `RAW_DATA_LOAD_FAILED`；
5. 如果 public benchmark 当前使用 mock loader，应在 warnings 中记录。

---

# 12. Strategy Resolver 设计

## 12.1 职责

`strategy_resolver.py` 负责把 Workflow Plan 的 `feature_strategy` 解析为本模块可执行的特征工程策略。

---

## 12.2 输入

```json
{
  "feature_type": "composition_descriptors",
  "recommended_featurizers": [
    "elemental_property_statistics",
    "stoichiometric_features"
  ],
  "requires_structure_features": false,
  "feature_selection_required": true,
  "feature_scaling_required": true
}
```

---

## 12.3 输出

```json
{
  "feature_type": "composition_descriptors",
  "input_modality": "composition",
  "selected_featurizers": [
    "elemental_property_statistics",
    "stoichiometric_features"
  ],
  "unsupported_featurizers": [],
  "fallback_featurizers": [],
  "scaling_required": true,
  "feature_selection_required": true
}
```

---

## 12.4 策略解析规则

| 条件                                     | 处理                          |
| -------------------------------------- | --------------------------- |
| feature_type = composition_descriptors | 使用 CompositionFeaturizer    |
| feature_type = existing_descriptors    | 使用 DescriptorFeaturizer     |
| feature_type = structure_descriptors   | 使用 StructureFeaturizer      |
| featurizer 不可用                         | 进入 unsupported_featurizers  |
| 可用替代方案存在                               | 使用 fallback_featurizers     |
| 无任何可用 featurizer                       | 返回 FEATURIZER_NOT_AVAILABLE |

---

# 13. Featurizer 层设计

## 13.1 BaseFeaturizer

所有 Featurizer 遵循统一接口：

```text
featurize(raw_dataframe, context, resolved_strategy) → FeaturizationResult
```

统一输出：

```json
{
  "status": "success",
  "feature_dataframe": "internal_dataframe_object",
  "feature_columns": [],
  "executed_featurizers": [],
  "failed_samples": [],
  "warnings": [],
  "errors": []
}
```

---

## 13.2 CompositionFeaturizer

### 职责

将 chemical formula / composition 列转换为数值型材料描述符。

### MVP 支持特征

建议先实现轻量级特征：

1. 元素数量；
2. 化学式原子总数；
3. 平均原子序数；
4. 最大原子序数；
5. 最小原子序数；
6. 平均原子量；
7. 最大原子量；
8. 最小原子量；
9. 平均电负性；
10. 最大电负性；
11. 最小电负性；
12. 化学计量熵；
13. 最大元素比例；
14. 最小元素比例；
15. 是否含金属元素；
16. 是否含过渡金属元素。

### MVP 实现原则

1. 尽量不依赖重型材料库；
2. 可使用内置元素属性表；
3. 对无法解析的化学式记录 failed_samples；
4. 不因少量失败样本中断整个流程；
5. 如果失败样本比例过高，则返回 failed。

### 后续升级

后续接入：

```text
pymatgen Composition
matminer ElementProperty
matminer Stoichiometry
Magpie descriptors
```

---

## 13.3 DescriptorFeaturizer

### 职责

当输入数据已经是 descriptor matrix 时，整理已有数值列作为特征。

### 处理逻辑

1. 识别数值型列；
2. 排除 target_column；
3. 排除 sample_id / id 等非特征列；
4. 标记非数值列；
5. 删除全空列；
6. 标记常量列；
7. 输出 feature dataframe。

### 适用场景

```text
用户上传的数据已经包含特征列
例如：density, volume, atomic_radius_mean, electronegativity_mean
```

---

## 13.4 StructureFeaturizer

### MVP 处理方式

MVP 阶段作为 placeholder。

当输入为 structure 时：

1. 如果数据中已有数值型 structure descriptors，可 fallback 到 DescriptorFeaturizer；
2. 如果只有 CIF/POSCAR/structure 字符串，则返回 `STRUCTURE_FEATURIZER_NOT_AVAILABLE`；
3. 在 warnings 中说明结构特征工程需要后续接入 pymatgen/matminer。

### 后续扩展

支持：

1. pymatgen Structure；
2. density descriptors；
3. symmetry descriptors；
4. radial distribution features；
5. local environment features；
6. graph-based representation。

---

# 14. Feature Matrix Builder 设计

## 14.1 职责

`feature_matrix_builder.py` 负责将 featurizer 输出转换为标准 feature matrix。

---

## 14.2 标准 feature matrix 结构

```text
sample_id
feature_1
feature_2
...
feature_n
target_column
```

---

## 14.3 构建规则

1. 保持与原始数据行顺序一致；
2. 自动生成 `sample_id`；
3. 保留目标列；
4. 不保留原始 composition / structure 列作为训练特征；
5. 原始输入列可写入 metadata；
6. 检查 feature matrix 行数是否等于原始数据行数；
7. 检查 target_column 是否存在；
8. 检查 feature columns 是否为空。

---

# 15. Feature Quality Checker 设计

## 15.1 职责

检查 feature matrix 是否适合后续建模。

---

## 15.2 检查内容

1. 特征数是否为 0；
2. 样本数是否为 0；
3. 目标列是否存在；
4. 特征列是否全为数值；
5. NaN 总量；
6. 每列缺失率；
7. 全空特征；
8. 常量特征；
9. 无限值；
10. 重复特征名；
11. failed samples；
12. 特征维度是否异常过高。

---

## 15.3 输出

```json
{
  "is_valid_feature_matrix": true,
  "missing_values": {
    "total_missing": 0,
    "columns_with_missing": []
  },
  "constant_features": [],
  "all_missing_features": [],
  "invalid_features": [],
  "dropped_features": [],
  "failed_samples": [],
  "warnings": [],
  "errors": []
}
```

---

## 15.4 阻断条件

以下情况应导致 `failed`：

1. 特征数为 0；
2. 样本数为 0；
3. 目标列缺失；
4. 所有样本特征生成失败；
5. 所有特征均为无效特征；
6. 输入模态完全不支持且无 fallback；
7. artifact 保存失败。

---

# 16. Artifact Manager 设计

## 16.1 职责

`artifact_manager.py` 负责：

1. 创建 artifact 目录；
2. 保存 feature matrix；
3. 保存 feature_schema；
4. 保存 metadata；
5. 生成 artifact_id；
6. 读取 preview；
7. 返回 artifact 引用。

---

## 16.2 推荐文件格式

| 格式      | 推荐度 | 说明               |
| ------- | --- | ---------------- |
| Parquet | 高   | 类型保留好，读取快，适合数值矩阵 |
| CSV     | 中   | 易读，但体积大，类型容易丢失   |
| JSON    | 低   | 不适合大型矩阵          |

MVP 推荐：

```text
parquet 优先，csv 作为 fallback
```

---

## 16.3 Artifact Metadata

```json
{
  "artifact_id": "artifact_features_xxxxxxxx",
  "feature_engineering_id": "feat_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "file_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
  "format": "parquet",
  "n_samples": 4604,
  "n_features": 140,
  "target_column": "band_gap",
  "created_at": "2026-05-02T10:00:00"
}
```

---

# 17. Builder 设计

## 17.1 职责

`builder.py` 负责构建最终 Feature Engineering Object。

---

## 17.2 Builder 需要组装

```text
feature_engineering_id
task_id
interpretation_id
dataset_profile_id
workflow_plan_id
status
input_modality
feature_type
feature_generation
feature_matrix
feature_schema
feature_quality
preprocessing_requirements
downstream_input
warnings
errors
created_at
updated_at
```

---

## 17.3 状态生成规则

| 条件                        | status                 |
| ------------------------- | ---------------------- |
| 上游状态不满足                   | blocked                |
| 原始数据加载失败                  | failed                 |
| featurizer 不可用且无 fallback | failed                 |
| 特征矩阵无效                    | failed                 |
| artifact 保存失败             | failed                 |
| 成功且无 warnings             | completed              |
| 成功但有 warnings             | completed_with_warning |

---

# 18. 状态管理设计

## 18.1 状态枚举

```text
pending
loading_data
featurizing
validating
completed
completed_with_warning
failed
blocked
```

---

## 18.2 状态含义

| 状态                     | 含义               |
| ---------------------- | ---------------- |
| pending                | 已创建特征工程任务，尚未执行   |
| loading_data           | 正在加载原始数据         |
| featurizing            | 正在生成特征           |
| validating             | 正在检查特征矩阵         |
| completed              | 特征工程完成           |
| completed_with_warning | 特征工程完成，但存在非阻断性问题 |
| failed                 | 特征工程失败           |
| blocked                | 上游状态不满足          |

---

## 18.3 状态流转

```text
收到请求
    ↓
检查上游状态
    ├── 不满足 → blocked
    └── 满足
          ↓
        pending
          ↓
        loading_data
          ↓
        featurizing
          ↓
        validating
          ↓
        completed / completed_with_warning / failed
```

MVP 阶段可以同步执行完整流程；后续大规模特征工程可引入异步任务队列。

---

# 19. 异常处理设计

## 19.1 异常类型

建议新增模块专用异常：

```text
FeatureEngineeringException
├── FeatureEngineeringNotFoundException
├── FeatureEngineeringUpstreamNotReadyException
├── FeatureStrategyMissingException
├── RawDataLoadException
├── InputModalityUnsupportedException
├── FeaturizerNotAvailableException
├── FeatureGenerationException
├── FeatureMatrixInvalidException
└── FeatureArtifactSaveException
```

---

## 19.2 错误码设计

| 错误码                             | 场景                       |
| ------------------------------- | ------------------------ |
| `TASK_NOT_FOUND`                | task_id 不存在              |
| `TASK_NOT_READY`                | Task Specification 状态不允许 |
| `INTERPRETATION_NOT_READY`      | Task Interpretation 不可用  |
| `DATASET_PROFILE_NOT_READY`     | Dataset Profile 不可用      |
| `WORKFLOW_PLAN_NOT_READY`       | Workflow Plan 不可用        |
| `FEATURE_STRATEGY_MISSING`      | feature_strategy 缺失      |
| `RAW_DATA_LOAD_FAILED`          | 原始数据加载失败                 |
| `INPUT_MODALITY_UNSUPPORTED`    | 输入模态不支持                  |
| `FEATURIZER_NOT_AVAILABLE`      | 指定 featurizer 不可用        |
| `FEATURE_GENERATION_FAILED`     | 特征生成失败                   |
| `FEATURE_MATRIX_INVALID`        | 特征矩阵不可用                  |
| `FEATURE_ARTIFACT_SAVE_FAILED`  | 特征文件保存失败                 |
| `FEATURE_ENGINEERING_NOT_FOUND` | 查询不到特征工程结果               |

---

## 19.3 非阻断性 Warning

以下情况不一定中断流程，但应记录到 `warnings`：

1. 部分样本特征生成失败；
2. 部分特征存在缺失值；
3. 删除了常量特征；
4. 删除了全空特征；
5. 使用了 MVP 简化特征而非 matminer 标准特征；
6. 结构输入暂未支持完整结构特征；
7. 特征数量较少；
8. 推荐 featurizer 不可用，使用 fallback；
9. 特征缩放未实际执行，仅标记为后续需求；
10. 特征选择未实际执行，仅标记为后续需求。

---

# 20. 配置设计

## 20.1 新增环境变量建议

```text
FEATURE_ARTIFACT_DIR=/app/artifacts/features
FEATURE_ARTIFACT_FORMAT=parquet
FEATURE_PREVIEW_ROWS=20
FEATURE_MAX_FAILED_SAMPLE_RATIO=0.2
ENABLE_COMPOSITION_FEATURIZER=true
ENABLE_DESCRIPTOR_FEATURIZER=true
ENABLE_STRUCTURE_FEATURIZER=false
```

---

## 20.2 配置说明

| 配置项                               | 说明                          |
| --------------------------------- | --------------------------- |
| `FEATURE_ARTIFACT_DIR`            | 特征矩阵 artifact 存储目录          |
| `FEATURE_ARTIFACT_FORMAT`         | 默认输出格式，推荐 parquet           |
| `FEATURE_PREVIEW_ROWS`            | 默认预览行数                      |
| `FEATURE_MAX_FAILED_SAMPLE_RATIO` | 允许的最大特征生成失败样本比例             |
| `ENABLE_COMPOSITION_FEATURIZER`   | 是否启用 composition featurizer |
| `ENABLE_DESCRIPTOR_FEATURIZER`    | 是否启用 descriptor featurizer  |
| `ENABLE_STRUCTURE_FEATURIZER`     | 是否启用 structure featurizer   |

---

# 21. 前端架构设计

## 21.1 前端目录结构

建议新增：

```text
frontend/src/modules/featureEngineering/
├── components/
│   ├── FeatureEngineeringPanel.tsx
│   ├── FeatureSummaryCard.tsx
│   ├── FeaturizerResultCard.tsx
│   ├── FeatureMatrixCard.tsx
│   ├── FeatureQualityCard.tsx
│   ├── FeaturePreviewTable.tsx
│   ├── FeatureWarningList.tsx
│   └── FeatureEngineeringJsonViewer.tsx
├── types.ts
└── constants.ts
```

---

## 21.2 前端 API 客户端

新增：

```text
frontend/src/api/featureEngineeringApi.ts
```

封装：

```text
createFeatureEngineering(taskId)
getFeatureEngineering(featureEngineeringId)
getLatestFeatureEngineeringByTaskId(taskId)
rerunFeatureEngineering(taskId)
getFeatureMatrixPreview(featureEngineeringId)
```

---

## 21.3 前端展示内容

MVP 阶段展示：

1. Feature Engineering 状态；
2. 输入模态；
3. 特征类型；
4. 使用的 featurizer；
5. 样本数；
6. 特征数；
7. 目标列；
8. artifact_id；
9. artifact 路径或隐藏路径摘要；
10. 特征质量；
11. dropped features；
12. failed samples；
13. warnings/errors；
14. 特征预览；
15. 是否 ready for pipeline generation；
16. 完整 JSON。

---

# 22. 与后续模块的扩展接口

## 22.1 提供给 Pipeline Generation 的接口

Pipeline Generation 模块应通过以下接口读取特征工程结果：

```text
GET /api/tasks/{task_id}/feature-engineering
```

重点消费：

```text
downstream_input
feature_matrix.artifact_id
feature_matrix.file_path
feature_schema.feature_columns
preprocessing_requirements
feature_quality
```

---

## 22.2 downstream_input 推荐结构

```json
{
  "feature_matrix_artifact_id": "artifact_features_xxxxxxxx",
  "feature_matrix_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
  "target_column": "band_gap",
  "feature_columns": [],
  "task_type": "regression",
  "primary_metric": "MAE",
  "scaling_required": true,
  "imputation_required": false,
  "feature_selection_required": true,
  "ready_for_pipeline_generation": true
}
```

---

## 22.3 提供给 Pipeline Execution 的间接信息

Pipeline Execution 后续可使用：

```text
feature_matrix_path
target_column
feature_columns
sample_id
preprocessing_requirements
```

但 Pipeline Execution 不应直接绕过 Pipeline Generation。它应优先执行后续生成的 pipeline specification 或 pipeline code。

---

## 22.4 提供给 Metric Evaluation 的信息

Metric Evaluation 后续可使用：

```text
task_type
primary_metric
target_column
feature_matrix_artifact_id
```

---

## 22.5 提供给 Result Diagnosis 的信息

Result Diagnosis 后续可使用：

```text
feature_quality
failed_samples
dropped_features
feature_generation
preprocessing_requirements
```

用于分析模型效果不佳是否源于特征工程问题。

---

## 22.6 提供给 Report Generation 的信息

Report Generation 可使用：

```text
feature_type
selected_featurizers
n_features
feature_quality
warnings
feature_schema
```

用于生成报告中的 Feature Engineering 部分。

---

# 23. 安全与稳定性设计

## 23.1 文件与路径安全

1. artifact 路径由系统生成，不允许用户指定任意路径；
2. API 响应中可返回 artifact_id，尽量少暴露真实服务器路径；
3. 保存文件前创建独立目录；
4. rerun 时生成新目录，不覆盖旧文件；
5. 删除任务时后续可增加 artifact 清理机制。

---

## 23.2 数据规模控制

1. API 不返回完整 feature matrix；
2. preview 默认限制 20 行；
3. 特征矩阵保存到文件；
4. 对超大数据集后续引入异步任务；
5. 对特征数量异常大的情况生成 warning。

---

## 23.3 稳定性

1. 少量 failed samples 不应导致整个任务失败；
2. failed sample ratio 超过阈值才失败；
3. Featurizer 报错应被捕获并写入 errors；
4. Artifact 保存失败必须阻断；
5. 上游对象只读，不修改。

---

# 24. MVP 实现范围

## 24.1 MVP 必须实现

1. 新增 `feature_engineering` 后端模块；
2. 能通过 task_id 读取前四个模块最新结果；
3. 能检查上游状态；
4. 能解析 Workflow Plan 中的 `feature_strategy`；
5. 能复用 Dataset Profile Loader 重新加载原始数据；
6. 能支持 composition 输入的基础特征工程；
7. 能支持 descriptor 输入的特征矩阵整理；
8. 能对 structure 输入给出明确 unsupported 或 fallback；
9. 能构建标准 feature matrix；
10. 能保留 target_column；
11. 能检查特征缺失、常量、全空、非法值；
12. 能保存 feature matrix artifact；
13. 能生成 Feature Engineering Object；
14. 能持久化 Feature Engineering Object；
15. 能查询单个 Feature Engineering 结果；
16. 能查询某任务最新 Feature Engineering 结果；
17. 能 rerun 且不覆盖旧结果；
18. 能返回特征矩阵 preview；
19. 前端能展示结果。

---

## 24.2 MVP 不实现

1. 不训练模型；
2. 不执行 HPO；
3. 不计算评估指标；
4. 不生成完整 Pipeline 代码；
5. 不调用 LLM 重新规划特征；
6. 不实现复杂结构特征；
7. 不强制接入 matminer；
8. 不强制执行特征选择；
9. 不强制执行特征缩放；
10. 不实现异步任务队列；
11. 不实现 artifact 清理系统。

---

# 25. 后续演进方向

## 25.1 V2：标准材料特征库

引入：

```text
pymatgen
matminer
Magpie descriptors
```

增强 composition 特征能力。

---

## 25.2 V3：Structure Feature Engineering

支持：

1. CIF/POSCAR 解析；
2. pymatgen Structure；
3. density/symmetry descriptors；
4. local environment descriptors；
5. radial distribution descriptors。

---

## 25.3 V4：特征选择与缩放实际执行

引入：

1. VarianceThreshold；
2. StandardScaler；
3. RobustScaler；
4. mutual information；
5. correlation filtering；
6. model-based feature selection。

---

## 25.4 V5：多特征方案并行生成

支持：

```text
composition_basic
composition_magpie
descriptor_only
hybrid_features
```

生成多个 Feature Engineering Object，供后续模型比较。

---

## 25.5 V6：Agent 驱动特征重构

在 Result Diagnosis 后支持：

```text
Evaluation Result
    ↓
Diagnosis
    ↓
LLM suggests feature refinement
    ↓
New Feature Engineering version
```

---

# 26. 推荐开发顺序

## 阶段一：后端基础结构

1. 创建 `feature_engineering` 模块目录；
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
5. 查询最新 Workflow Plan；
6. 校验上游状态；
7. 构建 Feature Engineering Context。

---

## 阶段三：数据加载与策略解析

1. 实现 `data_loader_adapter.py`；
2. 复用 Dataset Profile 模块 Loader；
3. 实现 `strategy_resolver.py`；
4. 解析 feature_strategy；
5. 识别 input_modality 和 feature_type。

---

## 阶段四：Featurizer 实现

1. 定义 `BaseFeaturizer`；
2. 实现 `CompositionFeaturizer`；
3. 实现 `DescriptorFeaturizer`；
4. 实现 `StructureFeaturizer` placeholder；
5. 输出统一 FeaturizationResult。

---

## 阶段五：矩阵构建与质量检查

1. 实现 `feature_matrix_builder.py`；
2. 实现 `feature_quality_checker.py`；
3. 检查 target_column 和 feature_columns；
4. 生成 feature_schema 和 feature_quality。

---

## 阶段六：Artifact 与持久化

1. 实现 `artifact_manager.py`；
2. 保存 features.parquet；
3. 生成 preview_json；
4. 构建 Feature Engineering Object；
5. 写入 feature_engineering 表。

---

## 阶段七：前端展示

1. 新增 `featureEngineeringApi.ts`；
2. 新增 `FeatureEngineeringPanel.tsx`；
3. 展示特征摘要、featurizer 结果、质量检查；
4. 展示 warnings/errors；
5. 展示 preview table；
6. 展示完整 JSON。

---

# 27. 总结

Automated Feature Engineering 模块是 MLAgent 从“规划”走向“可执行建模”的关键转换层。

它的核心输入是：

```text
Task Specification Object
    +
Task Interpretation Object
    +
Dataset Profile Object
    +
Workflow Plan Object
```

它的核心输出是：

```text
Feature Engineering Object
    +
Feature Matrix Artifact
    +
downstream_input
```

它应该回答：

```text
原始材料输入如何转化为机器学习特征？
使用了哪些 featurizer？
生成了多少特征？
特征矩阵是否可用？
哪些样本或特征存在问题？
后续 Pipeline Generation 应使用哪个 feature artifact？
```

它不应该回答：

```text
模型该如何训练？
模型效果是多少？
是否完成 HPO？
最终最佳模型是什么？
完整 Pipeline 代码是什么？
```

架构上应坚持：

1. 独立业务模块；
2. 与前四个模块通过 task_id、interpretation_id、dataset_profile_id、workflow_plan_id 解耦协作；
3. 复用 Dataset Profile 的 Loader；
4. Featurizer、Checker、Artifact Manager 分层清晰；
5. 大矩阵文件化存储，数据库只存元数据；
6. 输出可持久化、可查询、可重跑；
7. 为 Pipeline Generation、Execution、Evaluation、Diagnosis 和 Report Generation 预留稳定接口。

```
```
