# Feature Preprocessing 模块架构与技术栈方案

## 1. 模块名称

Feature Preprocessing  
特征预处理模块

---

## 2. 模块定位

Feature Preprocessing 位于 **Automated Feature Engineering** 之后、**Automated Model and HPO Search** 之前。

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
Automated Model and HPO Search
    ↓
Pipeline Generation / Pipeline Execution
    ↓
Metric Evaluation
    ↓
Result Diagnosis
    ↓
Report Generation
````

本模块的核心职责是：

```text
raw feature matrix
    ↓
特征矩阵校验
    ↓
无效列剔除
    ↓
缺失值填补
    ↓
数值缩放
    ↓
基础特征筛选
    ↓
model-ready feature matrix
```

它不负责重新生成特征，也不负责训练模型、执行 HPO 或生成 Pipeline 代码。

---

# 3. 总体架构目标

## 3.1 架构目标

Feature Preprocessing 模块需要满足以下目标：

1. 与前五个模块通过 `task_id` 自然衔接；
2. 读取最新 Feature Engineering Object；
3. 加载 Feature Engineering 生成的 raw feature matrix artifact；
4. 严格校验特征矩阵是否可建模；
5. 删除非法列、全空列、常量列、高缺失率列；
6. 执行缺失值填补；
7. 执行数值缩放；
8. 可选执行类别编码；
9. 可选执行基础特征筛选；
10. 保存 model-ready feature matrix artifact；
11. 保存 preprocessing pipeline artifact；
12. 输出标准化 Feature Preprocessing Object；
13. 为 Automated Model and HPO Search 提供稳定输入。

---

## 3.2 总体架构图

```text
Frontend
  └── Feature Preprocessing Panel
        ↓
Backend API Layer
  └── feature_preprocessing/api.py
        ↓
Service Layer
  └── feature_preprocessing/service.py
        ↓
Context Builder
  ├── Read Task Specification
  ├── Read Task Interpretation
  ├── Read Dataset Profile
  ├── Read Workflow Plan
  └── Read Feature Engineering
        ↓
Artifact Loader
  └── Load raw feature matrix artifact
        ↓
Column Validator
  └── Validate feature columns
        ↓
Feature Filter
  └── Drop invalid / all-missing / constant / high-missing columns
        ↓
Feature Group Validator
  └── Validate feature groups after filtering
        ↓
Preprocessing Executor
  ├── Imputation
  ├── Scaling
  ├── Encoding
  └── Feature Selection
        ↓
Artifact Manager
  ├── Save model-ready matrix
  └── Save preprocessing pipeline
        ↓
Builder
  └── Build Feature Preprocessing Object
        ↓
Repository
  └── Persist into feature_preprocessing table
        ↓
Downstream Interface
  └── Automated Model and HPO Search
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
Artifact 加载层
  ↓
Column Validation 校验层
  ↓
Feature Filtering 过滤层
  ↓
Preprocessing 执行层
  ↓
Artifact 存储层
  ↓
Builder 对象构建层
  ↓
Repository 数据访问层
  ↓
Database 数据层
```

各层职责如下：

| 层级                      | 职责                                               |
| ----------------------- | ------------------------------------------------ |
| API 层                   | 接收 HTTP 请求，返回统一响应                                |
| Service 层               | 编排完整 Feature Preprocessing 流程                    |
| Context Builder         | 读取并整合前五个模块输出                                     |
| Artifact Loader         | 加载 Feature Engineering 生成的 raw feature matrix    |
| Column Validator        | 校验列类型、非法值、target column                          |
| Feature Filter          | 删除不可建模特征列                                        |
| Feature Group Validator | 按 feature group 汇总有效性                            |
| Preprocessing Executor  | 执行 imputation、scaling、encoding、feature selection |
| Artifact Manager        | 保存 model-ready matrix 和 preprocessor artifact    |
| Builder                 | 构建 Feature Preprocessing Object                  |
| Repository              | 负责数据库 CRUD                                       |
| Database                | 持久化结构化字段和 JSONB 结果                               |

---

# 4. 模块目录结构设计

建议新增独立业务模块：

```text
backend/app/modules/feature_preprocessing/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── artifact_loader.py
├── column_validator.py
├── feature_filter.py
├── feature_group_validator.py
├── preprocessing_executor.py
├── preprocessing_pipeline_builder.py
├── artifact_manager.py
├── builder.py
├── enums.py
├── exceptions.py
└── preprocessors/
    ├── __init__.py
    ├── imputer.py
    ├── scaler.py
    ├── encoder.py
    └── feature_selector.py
```

---

## 4.1 文件职责说明

| 文件                                  | 职责                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------ |
| `api.py`                            | 定义 Feature Preprocessing 相关 API                                          |
| `schemas.py`                        | 定义请求、响应、内部 DTO                                                           |
| `service.py`                        | 编排完整预处理流程                                                                |
| `model.py`                          | 定义 `feature_preprocessing` 数据库表                                          |
| `repository.py`                     | 提供 Feature Preprocessing CRUD                                            |
| `context_builder.py`                | 读取 Task、Interpretation、Dataset Profile、Workflow Plan、Feature Engineering |
| `artifact_loader.py`                | 加载 raw feature matrix artifact                                           |
| `column_validator.py`               | 校验 target column、特征列类型、非法值                                               |
| `feature_filter.py`                 | 删除非法列、全空列、常量列、高缺失率列                                                      |
| `feature_group_validator.py`        | 按 feature group 汇总 retained/dropped 状态                                   |
| `preprocessing_executor.py`         | 统一执行 imputation、scaling、encoding、feature selection                       |
| `preprocessing_pipeline_builder.py` | 构建可保存的 sklearn preprocessing pipeline                                    |
| `artifact_manager.py`               | 保存 model-ready matrix、preprocessor joblib、metadata                       |
| `builder.py`                        | 构建 Feature Preprocessing Object                                          |
| `enums.py`                          | 定义状态、处理动作、预处理策略枚举                                                        |
| `exceptions.py`                     | 定义模块专用异常                                                                 |
| `preprocessors/imputer.py`          | 封装缺失值填补逻辑                                                                |
| `preprocessors/scaler.py`           | 封装数值缩放逻辑                                                                 |
| `preprocessors/encoder.py`          | 封装类别编码逻辑                                                                 |
| `preprocessors/feature_selector.py` | 封装基础特征筛选逻辑                                                               |

---

# 5. 技术栈方案

## 5.1 后端技术栈

| 技术          | 推荐方案                | 说明                                   |
| ----------- | ------------------- | ------------------------------------ |
| Web 框架      | FastAPI             | 与当前系统保持一致                            |
| ORM         | SQLModel            | 与已有模块保持一致                            |
| 数据库         | PostgreSQL 16       | 使用现有数据库                              |
| 复杂对象存储      | JSONB               | 存储完整 Feature Preprocessing Object    |
| 数据校验        | Pydantic v2         | 定义 API 和内部对象                         |
| 表格处理        | pandas              | 读取、过滤、保存特征矩阵                         |
| 数值计算        | numpy               | NaN、inf、方差、缺失率计算                     |
| 机器学习预处理     | scikit-learn        | imputer、scaler、encoder、selector      |
| artifact 保存 | parquet + joblib    | 保存 model-ready matrix 和 preprocessor |
| parquet 支持  | pyarrow             | 高效保存数值矩阵                             |
| 配置管理        | pydantic-settings   | 管理阈值、策略和 artifact 路径                 |
| 日志          | logging / structlog | 记录预处理过程、警告、错误                        |
| 容器化         | Docker Compose      | 延续当前部署方式                             |

---

## 5.2 推荐依赖

建议确保以下依赖存在：

```text
pandas
numpy
scikit-learn
pyarrow
joblib
```

说明：

| 依赖           | 用途                                               |
| ------------ | ------------------------------------------------ |
| pandas       | DataFrame 读取、过滤和保存                               |
| numpy        | 数值检查、NaN/inf 处理                                  |
| scikit-learn | SimpleImputer、StandardScaler、VarianceThreshold 等 |
| pyarrow      | 保存 parquet                                       |
| joblib       | 保存 fitted preprocessing pipeline                 |

---

## 5.3 Preprocessing 组件选型

| 任务                    | MVP 推荐实现                           |
| --------------------- | ---------------------------------- |
| 缺失值填补                 | `SimpleImputer(strategy="median")` |
| 数值缩放                  | `StandardScaler`                   |
| 类别编码                  | MVP 默认关闭；后续使用 `OneHotEncoder`      |
| 特征选择                  | `VarianceThreshold`                |
| Pipeline 保存           | `joblib.dump()`                    |
| model-ready matrix 保存 | parquet                            |

---

# 6. 核心数据对象设计

## 6.1 上游输入对象一：Feature Engineering Object

本模块重点消费：

```text
feature_engineering_id
status
feature_matrix.artifact_id
feature_matrix.file_path
feature_matrix.target_column
feature_schema.feature_columns
feature_schema.feature_groups
feature_quality.invalid_features
feature_quality.all_missing_features
feature_quality.constant_features
preprocessing_requirements
downstream_input
warnings
errors
```

使用原则：

1. 只读取，不修改；
2. 只接受 `completed` 或 `completed_with_warning`；
3. 必须存在 raw feature matrix artifact；
4. 必须存在 target column。

---

## 6.2 上游输入对象二：Workflow Plan Object

本模块重点消费：

```text
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
interpretability_strategy
feature_strategy
```

使用原则：

1. 不重新规划；
2. 不调用 LLM；
3. 只透传后续模型搜索所需策略；
4. 可参考 `feature_strategy.feature_scaling_required` 等字段决定默认预处理策略。

---

## 6.3 中间对象：Feature Preprocessing Context

```json
{
  "task_id": "task_xxxxxxxx",
  "feature_engineering_id": "feat_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "task_context": {
    "task_type": "regression",
    "target_column": "band_gap",
    "primary_metric": "MAE"
  },
  "artifact_context": {
    "raw_feature_matrix_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
    "raw_feature_artifact_id": "artifact_features_xxxxxxxx"
  },
  "strategy_context": {
    "model_strategy": {},
    "validation_strategy": {},
    "evaluation_strategy": {},
    "hpo_strategy": {}
  },
  "preprocessing_config": {
    "drop_invalid_features": true,
    "drop_all_missing_features": true,
    "drop_constant_features": true,
    "max_missing_ratio": 0.5,
    "imputation_strategy": "median",
    "scaling_strategy": "standard_scaler",
    "feature_selection_strategy": "variance_threshold"
  }
}
```

---

## 6.4 输出对象：Feature Preprocessing Object

```json
{
  "preprocessing_id": "fmp_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "dataset_profile_id": "profile_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "feature_engineering_id": "feat_xxxxxxxx",
  "status": "preprocessed",
  "input_artifact": {
    "feature_matrix_artifact_id": "artifact_features_xxxxxxxx",
    "file_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
    "n_samples": 4604,
    "n_raw_features": 140
  },
  "validation_summary": {
    "is_model_ready": true,
    "n_samples": 4604,
    "n_raw_features": 140,
    "n_valid_features_before_preprocessing": 128,
    "n_features_after_preprocessing": 128,
    "n_dropped_features": 12,
    "target_column": "band_gap",
    "task_type": "regression"
  },
  "column_validation": {
    "dropped_invalid_features": [],
    "dropped_all_missing_features": [],
    "dropped_constant_features": [],
    "dropped_high_missing_features": [],
    "retained_features": []
  },
  "feature_group_validation": {
    "groups": []
  },
  "preprocessing_execution": {
    "imputation": {
      "executed": true,
      "strategy": "median",
      "columns": []
    },
    "scaling": {
      "executed": true,
      "strategy": "standard_scaler",
      "columns": []
    },
    "categorical_encoding": {
      "executed": false,
      "strategy": "none",
      "columns": []
    },
    "feature_selection": {
      "executed": true,
      "strategy": "variance_threshold",
      "columns_dropped": []
    }
  },
  "model_ready_artifact": {
    "artifact_id": "artifact_model_ready_xxxxxxxx",
    "storage_type": "parquet",
    "file_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/model_ready_features.parquet",
    "n_samples": 4604,
    "n_features": 128,
    "target_column": "band_gap"
  },
  "preprocessing_pipeline_artifact": {
    "artifact_id": "artifact_preprocessor_xxxxxxxx",
    "storage_type": "joblib",
    "file_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/preprocessor.joblib"
  },
  "model_search_input": {
    "model_ready_artifact_id": "artifact_model_ready_xxxxxxxx",
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
    "ready_for_model_search": true
  },
  "warnings": [],
  "errors": []
}
```

---

# 7. 数据库设计

## 7.1 表名

```text
feature_preprocessing
```

---

## 7.2 字段设计

| 字段                           | 类型          | 说明                              |
| ---------------------------- | ----------- | ------------------------------- |
| `id`                         | VARCHAR     | 主键，格式 `fmp_xxxxxxxx`            |
| `task_id`                    | VARCHAR     | 关联 Task Specification           |
| `interpretation_id`          | VARCHAR     | 关联 Task Interpretation          |
| `dataset_profile_id`         | VARCHAR     | 关联 Dataset Profile              |
| `workflow_plan_id`           | VARCHAR     | 关联 Workflow Plan                |
| `feature_engineering_id`     | VARCHAR     | 关联 Feature Engineering          |
| `status`                     | VARCHAR     | 预处理状态                           |
| `n_samples`                  | INTEGER     | 样本数                             |
| `n_raw_features`             | INTEGER     | 原始特征数                           |
| `n_valid_features`           | INTEGER     | 有效特征数                           |
| `n_final_features`           | INTEGER     | 预处理后特征数                         |
| `n_dropped_features`         | INTEGER     | 删除特征数                           |
| `target_column`              | VARCHAR     | 目标列                             |
| `model_ready_artifact_id`    | VARCHAR     | model-ready artifact ID         |
| `model_ready_artifact_path`  | TEXT        | model-ready artifact 路径         |
| `preprocessor_artifact_id`   | VARCHAR     | preprocessor artifact ID        |
| `preprocessor_artifact_path` | TEXT        | preprocessor artifact 路径        |
| `is_ready_for_model_search`  | BOOLEAN     | 是否可进入模型搜索                       |
| `preprocessing_json`         | JSONB       | 完整 Feature Preprocessing Object |
| `preview_json`               | JSONB       | model-ready matrix 预览           |
| `error_message`              | TEXT        | 错误信息                            |
| `created_at`                 | TIMESTAMPTZ | 创建时间                            |
| `updated_at`                 | TIMESTAMPTZ | 更新时间                            |

---

## 7.3 索引设计

| 索引                                 | 说明         |
| ---------------------------------- | ---------- |
| `PRIMARY KEY(id)`                  | 主键索引       |
| `INDEX(task_id)`                   | 根据任务查询     |
| `INDEX(feature_engineering_id)`    | 根据特征工程结果查询 |
| `INDEX(workflow_plan_id)`          | 根据工作流规划查询  |
| `INDEX(status)`                    | 按状态筛选      |
| `INDEX(is_ready_for_model_search)` | 筛选可建模结果    |
| `INDEX(created_at)`                | 查询最新       |
| `INDEX(task_id, created_at DESC)`  | 查询某任务最新结果  |

---

## 7.4 存储策略

继续沿用当前系统模式：

```text
高频字段单独建列
+
复杂对象存 JSONB
+
大型矩阵保存为 artifact 文件
+
预处理器保存为 joblib artifact
```

不建议将完整 model-ready matrix 存入数据库。

---

# 8. API 设计

## 8.1 创建 Feature Preprocessing

```text
POST /api/feature-preprocessing/{task_id}
```

### 功能

根据 `task_id` 读取最新 Feature Engineering 结果，执行特征矩阵校验、过滤、缺失值填补、缩放、基础特征筛选，并生成 model-ready artifact。

### 请求体

MVP 可为空。

后续可扩展：

```json
{
  "force_rerun": false,
  "max_missing_ratio": 0.5,
  "drop_invalid_features": true,
  "drop_all_missing_features": true,
  "drop_constant_features": true,
  "drop_high_missing_features": true,
  "imputation_strategy": "median",
  "scaling_strategy": "standard_scaler",
  "feature_selection_strategy": "variance_threshold",
  "output_format": "parquet"
}
```

### 响应

```json
{
  "success": true,
  "message": "Feature preprocessing completed successfully.",
  "data": {
    "preprocessing_id": "fmp_xxxxxxxx",
    "task_id": "task_xxxxxxxx",
    "feature_engineering_id": "feat_xxxxxxxx",
    "status": "preprocessed",
    "validation_summary": {},
    "preprocessing_execution": {},
    "model_ready_artifact": {},
    "preprocessing_pipeline_artifact": {},
    "model_search_input": {}
  }
}
```

---

## 8.2 查询 Feature Preprocessing 结果

```text
GET /api/feature-preprocessing/{preprocessing_id}
```

---

## 8.3 查询某任务最新 Feature Preprocessing 结果

```text
GET /api/tasks/{task_id}/feature-preprocessing
```

---

## 8.4 重新执行 Feature Preprocessing

```text
POST /api/feature-preprocessing/{task_id}/rerun
```

原则：

1. 不覆盖旧记录；
2. 新增一条 preprocessing 记录；
3. 生成新的 model-ready artifact；
4. 生成新的 preprocessor artifact；
5. 默认查询最新结果。

---

## 8.5 预览 Model-ready Matrix

```text
GET /api/feature-preprocessing/{preprocessing_id}/preview
```

功能：

1. 返回 model-ready matrix 前 N 行；
2. 默认 20 行；
3. 不返回完整矩阵；
4. 数值保留合理精度。

---

# 9. 核心业务数据流

## 9.1 创建 Feature Preprocessing 完整数据流

```text
用户点击 Run Feature Preprocessing
    ↓
前端调用 POST /api/feature-preprocessing/{task_id}
    ↓
feature_preprocessing/api.py 接收请求
    ↓
feature_preprocessing/service.py 开始编排
    ↓
context_builder.py 读取前五个模块结果
        ├── Task Specification
        ├── Task Interpretation
        ├── Dataset Profile
        ├── Workflow Plan
        └── Feature Engineering
    ↓
检查上游状态
    ↓
artifact_loader.py 加载 raw feature matrix
    ↓
column_validator.py 校验 target column 和 feature columns
    ↓
feature_filter.py 删除非法/全空/常量/高缺失率特征
    ↓
feature_group_validator.py 汇总 feature group 有效性
    ↓
preprocessing_executor.py 执行 imputation / scaling / feature selection
    ↓
preprocessing_pipeline_builder.py 构建 fitted preprocessor
    ↓
artifact_manager.py 保存 model-ready matrix 和 preprocessor.joblib
    ↓
builder.py 构建 Feature Preprocessing Object
    ↓
repository.py 写入 feature_preprocessing 表
    ↓
返回 Feature Preprocessing Response
```

---

## 9.2 与 Feature Engineering 的数据流

```text
Feature Engineering Object
    ↓
feature_matrix.file_path
    ↓
Artifact Loader
    ↓
raw feature matrix
    ↓
Feature Preprocessing
```

本模块只读取 Feature Engineering 输出，不修改原始 Feature Engineering Object。

---

## 9.3 与 Automated Model and HPO Search 的数据流

```text
Feature Preprocessing Object
    ↓
model_search_input
    ↓
Automated Model and HPO Search
```

下游重点消费：

```text
model_ready_matrix_path
preprocessing_pipeline_artifact_id
target_column
feature_columns
task_type
primary_metric
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
ready_for_model_search
```

---

# 10. 核心组件设计

## 10.1 Context Builder

### 职责

读取前五个模块结果并构建统一上下文。

### 检查内容

1. task 是否存在；
2. Task Specification 状态是否有效；
3. Task Interpretation 状态是否有效；
4. Dataset Profile 状态是否有效；
5. Workflow Plan 状态是否有效；
6. Feature Engineering 状态是否为 completed / completed_with_warning；
7. feature artifact 是否存在；
8. target_column 是否明确。

---

## 10.2 Artifact Loader

### 职责

读取 Feature Engineering 输出的 raw feature matrix。

### 支持格式

| 格式      | 支持          |
| ------- | ----------- |
| parquet | MVP 必须支持    |
| csv     | fallback 支持 |
| json    | 不建议         |

### 输出

```json
{
  "dataframe": "internal_dataframe",
  "n_samples": 4604,
  "n_columns": 142,
  "target_column": "band_gap",
  "candidate_feature_columns": []
}
```

---

## 10.3 Column Validator

### 职责

判断哪些列可以进入预处理阶段。

### 删除列类型

1. object；
2. dict；
3. list；
4. pymatgen Composition；
5. datetime；
6. 无法转换为 float 的字符串；
7. 中间解析列；
8. 用户 ID / metadata 列。

### 保留列类型

1. integer；
2. float；
3. boolean；
4. 可选 categorical。

---

## 10.4 Feature Filter

### 职责

执行不可建模列剔除。

### 默认策略

| 问题                         | 默认动作                                       |
| -------------------------- | ------------------------------------------ |
| invalid object feature     | drop                                       |
| all missing feature        | drop                                       |
| constant feature           | drop                                       |
| high missing ratio feature | drop                                       |
| inf / -inf                 | replace with NaN, then check missing ratio |

---

## 10.5 Feature Group Validator

### 职责

从 feature name 前缀或 feature_schema.feature_groups 中识别特征组状态。

### 状态

| 状态                    | 含义        |
| --------------------- | --------- |
| retained              | 该组有足够有效特征 |
| retained_with_warning | 该组部分特征被删除 |
| dropped               | 该组所有特征被删除 |

---

## 10.6 Preprocessing Executor

### 职责

实际执行建模前预处理。

### MVP 处理顺序

```text
filtered feature matrix
    ↓
imputation
    ↓
scaling
    ↓
feature selection
    ↓
model-ready matrix
```

### 说明

1. imputation 应在 scaling 之前；
2. feature selection 可在 scaling 后执行；
3. target_column 不参与 imputation/scaling；
4. sample_id 不参与训练特征处理；
5. 输出仍保留 sample_id 和 target_column。

---

## 10.7 Preprocessing Pipeline Builder

### 职责

将实际执行过的 imputer、scaler、encoder、selector 组合成可持久化对象。

### 保存格式

```text
preprocessor.joblib
```

### 用途

1. 供后续模型训练复用；
2. 供 Pipeline Generation 编译进最终 pipeline；
3. 供未来推理阶段保持一致预处理。

---

## 10.8 Artifact Manager

### 职责

保存所有本模块产物。

### 目录结构

```text
/app/artifacts/model_ready/
└── fmp_xxxxxxxx/
    ├── model_ready_features.parquet
    ├── preprocessor.joblib
    ├── preprocessing_metadata.json
    ├── validation_report.json
    └── preview.json
```

---

# 11. Model-ready 判定规则

## 11.1 ready_for_model_search = true

必须同时满足：

1. target_column 存在；
2. 样本数 > 0；
3. final feature count >= `FEATURE_PREPROCESSING_MIN_VALID_FEATURES`；
4. 所有保留特征均为数值；
5. 不存在 NaN；
6. 不存在 inf / -inf；
7. 不存在 object 特征；
8. 不存在全空特征；
9. 不存在常量特征；
10. model-ready artifact 保存成功；
11. preprocessor artifact 保存成功。

---

## 11.2 ready_for_model_search = false

出现以下任一情况：

1. target_column 缺失；
2. 有效特征数为 0；
3. imputation 失败；
4. scaling 失败；
5. feature selection 后无特征；
6. artifact 保存失败；
7. 清洗后样本数为 0；
8. preprocessor artifact 保存失败。

---

# 12. 状态管理设计

## 12.1 状态枚举

```text
pending
loading_artifact
validating
filtering
preprocessing
artifact_saving
preprocessed
preprocessed_with_warning
failed
blocked
```

---

## 12.2 状态含义

| 状态                        | 含义                                |
| ------------------------- | --------------------------------- |
| pending                   | 已创建预处理任务，尚未执行                     |
| loading_artifact          | 正在加载 raw feature matrix           |
| validating                | 正在校验特征矩阵                          |
| filtering                 | 正在删除无效特征                          |
| preprocessing             | 正在执行 imputation/scaling/selection |
| artifact_saving           | 正在保存 model-ready artifact         |
| preprocessed              | 预处理成功                             |
| preprocessed_with_warning | 预处理成功但有警告                         |
| failed                    | 预处理失败                             |
| blocked                   | 上游状态不满足                           |

---

# 13. 异常处理设计

## 13.1 异常类型

建议新增：

```text
FeaturePreprocessingException
├── FeaturePreprocessingNotFoundException
├── FeaturePreprocessingUpstreamNotReadyException
├── FeatureArtifactLoadException
├── TargetColumnMissingException
├── NoValidFeaturesException
├── ImputationFailedException
├── ScalingFailedException
├── EncodingFailedException
├── FeatureSelectionFailedException
├── ModelReadyArtifactSaveException
└── PreprocessorArtifactSaveException
```

---

## 13.2 错误码设计

| 错误码                                 | 场景                         |
| ----------------------------------- | -------------------------- |
| `TASK_NOT_FOUND`                    | task_id 不存在                |
| `TASK_NOT_READY`                    | Task Specification 不可用     |
| `INTERPRETATION_NOT_READY`          | Task Interpretation 不可用    |
| `DATASET_PROFILE_NOT_READY`         | Dataset Profile 不可用        |
| `WORKFLOW_PLAN_NOT_READY`           | Workflow Plan 不可用          |
| `FEATURE_ENGINEERING_REQUIRED`      | 尚未执行 Feature Engineering   |
| `FEATURE_ENGINEERING_NOT_READY`     | Feature Engineering 状态不允许  |
| `FEATURE_ARTIFACT_MISSING`          | raw feature artifact 缺失    |
| `FEATURE_ARTIFACT_LOAD_FAILED`      | artifact 读取失败              |
| `TARGET_COLUMN_MISSING`             | 目标列缺失                      |
| `NO_VALID_FEATURES`                 | 没有有效特征                     |
| `IMPUTATION_FAILED`                 | 缺失值填补失败                    |
| `SCALING_FAILED`                    | 缩放失败                       |
| `ENCODING_FAILED`                   | 编码失败                       |
| `FEATURE_SELECTION_FAILED`          | 特征筛选失败                     |
| `MODEL_READY_ARTIFACT_SAVE_FAILED`  | model-ready artifact 保存失败  |
| `PREPROCESSOR_ARTIFACT_SAVE_FAILED` | preprocessor artifact 保存失败 |

---

## 13.3 Warning 设计

| Warning                         | 场景                     |
| ------------------------------- | ---------------------- |
| `INVALID_FEATURES_DROPPED`      | 非法特征被删除                |
| `ALL_MISSING_FEATURES_DROPPED`  | 全空特征被删除                |
| `CONSTANT_FEATURES_DROPPED`     | 常量特征被删除                |
| `HIGH_MISSING_FEATURES_DROPPED` | 高缺失率特征被删除              |
| `FEATURE_GROUP_DROPPED`         | 某个 feature group 被整体删除 |
| `IMPUTATION_EXECUTED`           | 已执行缺失值填补               |
| `SCALING_EXECUTED`              | 已执行缩放                  |
| `FEATURE_SELECTION_EXECUTED`    | 已执行基础特征筛选              |
| `LOW_EFFECTIVE_FEATURE_COUNT`   | 有效特征数较少                |
| `MODEL_READY_WITH_WARNINGS`     | 可进入模型搜索但存在警告           |

---

# 14. 配置设计

## 14.1 新增环境变量

```text
MODEL_READY_ARTIFACT_DIR=/app/artifacts/model_ready
MODEL_READY_ARTIFACT_FORMAT=parquet
PREPROCESSOR_ARTIFACT_FORMAT=joblib
FEATURE_PREPROCESSING_PREVIEW_ROWS=20

FEATURE_PREPROCESSING_MAX_MISSING_RATIO=0.5
FEATURE_PREPROCESSING_DROP_INVALID=true
FEATURE_PREPROCESSING_DROP_ALL_MISSING=true
FEATURE_PREPROCESSING_DROP_CONSTANT=true
FEATURE_PREPROCESSING_DROP_HIGH_MISSING=true
FEATURE_PREPROCESSING_MIN_VALID_FEATURES=1

FEATURE_PREPROCESSING_IMPUTATION_STRATEGY=median
FEATURE_PREPROCESSING_SCALING_STRATEGY=standard_scaler
FEATURE_PREPROCESSING_ENABLE_FEATURE_SELECTION=true
FEATURE_PREPROCESSING_FEATURE_SELECTION_STRATEGY=variance_threshold
FEATURE_PREPROCESSING_ALLOW_CATEGORICAL=false
```

---

# 15. 前端架构设计

## 15.1 前端目录结构

```text
frontend/src/modules/featurePreprocessing/
├── components/
│   ├── FeaturePreprocessingPanel.tsx
│   ├── ValidationSummaryCard.tsx
│   ├── ColumnFilteringCard.tsx
│   ├── FeatureGroupValidationCard.tsx
│   ├── PreprocessingExecutionCard.tsx
│   ├── ModelReadyArtifactCard.tsx
│   ├── ModelReadyPreviewTable.tsx
│   ├── PreprocessingWarningList.tsx
│   └── FeaturePreprocessingJsonViewer.tsx
├── types.ts
└── constants.ts
```

---

## 15.2 前端 API 客户端

```text
frontend/src/api/featurePreprocessingApi.ts
```

封装：

```text
createFeaturePreprocessing(taskId)
getFeaturePreprocessing(preprocessingId)
getLatestFeaturePreprocessingByTaskId(taskId)
rerunFeaturePreprocessing(taskId)
getModelReadyPreview(preprocessingId)
```

---

## 15.3 前端展示内容

MVP 展示：

1. preprocessing 状态；
2. raw feature count；
3. dropped feature count；
4. final feature count；
5. dropped invalid features；
6. dropped all-missing features；
7. dropped constant features；
8. dropped high-missing features；
9. feature group validation；
10. imputation 执行结果；
11. scaling 执行结果；
12. feature selection 执行结果；
13. model-ready artifact；
14. preprocessor artifact；
15. ready_for_model_search；
16. warnings/errors；
17. model-ready preview；
18. 完整 JSON。

---

# 16. 与后续模块的扩展接口

## 16.1 提供给 Automated Model and HPO Search

后续模块应通过：

```text
GET /api/tasks/{task_id}/feature-preprocessing
```

读取：

```text
model_search_input
```

重点消费：

```text
model_ready_matrix_path
preprocessing_pipeline_artifact_id
target_column
feature_columns
task_type
primary_metric
model_strategy
validation_strategy
evaluation_strategy
hpo_strategy
ready_for_model_search
```

---

## 16.2 提供给 Pipeline Generation

Pipeline Generation 可复用：

```text
preprocessing_pipeline_artifact_id
preprocessing_execution
feature_columns
model_ready_matrix_path
```

用于生成最终训练 Pipeline。

---

## 16.3 提供给 Result Diagnosis

Result Diagnosis 可使用：

```text
dropped_features
feature_group_validation
preprocessing_execution
warnings
```

诊断模型效果是否受特征有效性或预处理策略影响。

---

## 16.4 提供给 Report Generation

Report Generation 可使用：

```text
validation_summary
column_validation
feature_group_validation
preprocessing_execution
model_ready_artifact
```

生成实验报告中的 Feature Preprocessing 部分。

---

# 17. MVP 实现范围

## 17.1 MVP 必须实现

1. 新增 `feature_preprocessing` 后端模块；
2. 能读取前五个模块最新结果；
3. 能检查上游状态；
4. 能读取 raw feature matrix artifact；
5. 能删除非法 object 特征；
6. 能删除全空特征；
7. 能删除常量特征；
8. 能删除高缺失率特征；
9. 能处理 inf / -inf；
10. 能执行 median imputation；
11. 能执行 standard scaling；
12. 能执行 variance threshold feature selection；
13. 能保存 model-ready parquet；
14. 能保存 preprocessor joblib；
15. 能生成 Feature Preprocessing Object；
16. 能持久化 Feature Preprocessing Object；
17. 能查询某任务最新结果；
18. 能 rerun 且不覆盖旧结果；
19. 能返回 model-ready preview；
20. 前端能展示结果。

---

## 17.2 MVP 不实现

1. 不训练模型；
2. 不执行 HPO；
3. 不计算指标；
4. 不生成 Pipeline 代码；
5. 不重新生成材料特征；
6. 不重新执行 Workflow Planning；
7. 不支持复杂类别特征编码；
8. 不支持多版本预处理策略比较；
9. 不支持异步任务队列。

---

# 18. 推荐开发顺序

## 阶段一：后端基础结构

1. 创建 `feature_preprocessing` 模块目录；
2. 定义 `model.py`；
3. 定义 `schemas.py`；
4. 定义 `repository.py`；
5. 注册 API 路由。

---

## 阶段二：打通上游模块

1. 实现 `context_builder.py`；
2. 查询前五个模块结果；
3. 校验上游状态；
4. 构建 Feature Preprocessing Context。

---

## 阶段三：Artifact 加载与列校验

1. 实现 `artifact_loader.py`；
2. 实现 `column_validator.py`；
3. 识别非法列、全空列、常量列、高缺失率列。

---

## 阶段四：特征过滤与分组校验

1. 实现 `feature_filter.py`；
2. 实现 `feature_group_validator.py`；
3. 生成 retained/dropped feature group 信息。

---

## 阶段五：预处理执行

1. 实现 `preprocessors/imputer.py`；
2. 实现 `preprocessors/scaler.py`；
3. 实现 `preprocessors/feature_selector.py`；
4. 实现 `preprocessing_executor.py`；
5. 实现 `preprocessing_pipeline_builder.py`。

---

## 阶段六：Artifact 与持久化

1. 实现 `artifact_manager.py`；
2. 保存 model-ready parquet；
3. 保存 preprocessor.joblib；
4. 生成 preview_json；
5. 实现 `builder.py`；
6. 写入 `feature_preprocessing` 表。

---

## 阶段七：前端展示

1. 新增 `featurePreprocessingApi.ts`；
2. 新增 `FeaturePreprocessingPanel.tsx`；
3. 展示校验、过滤、预处理执行和 artifact 结果；
4. 展示完整 JSON。

---

# 19. 总结

Feature Preprocessing 模块是 Feature Engineering 和 Automated Model and HPO Search 之间的建模数据准备层。

它的核心输入是：

```text
Feature Engineering Object
+
Raw Feature Matrix Artifact
```

它的核心输出是：

```text
Feature Preprocessing Object
+
Model-ready Feature Matrix Artifact
+
Preprocessing Pipeline Artifact
+
model_search_input
```

它应该回答：

```text
当前特征矩阵是否能直接建模？
哪些列被删除？
哪些缺失值被填补？
是否执行了缩放？
是否执行了特征筛选？
模型搜索阶段应该读取哪个干净 artifact？
```

它不应该回答：

```text
应该训练哪个模型？
HPO 如何搜索？
模型效果是多少？
哪个模型最好？
Pipeline 代码如何生成？
```

一句话总结：

```text
Feature Preprocessing 负责将 Feature Engineering 输出的 raw feature matrix 处理成可直接进入 Automated Model and HPO Search 的 model-ready dataset。
```

