# PRD-5：Automated Feature Engineering 模块需求文档

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

当前系统已经完成：

1. **Task Specification**：生成用户任务规格对象；
2. **LLM-based Task Interpretation**：生成任务理解对象；
3. **Dataset Loading, Checking, and Profiling**：完成数据加载与画像，输出 `Dataset Profile Object`；
4. **Workflow Planning**：生成工作流规划对象，包含 `data_strategy`、`feature_strategy`、`model_strategy`、`pipeline_generation_input` 等内容。

本模块承接 Workflow Planning 的 `feature_strategy`，负责将原始材料输入转换为机器学习可用的特征矩阵，并输出标准化的 **Feature Engineering Object**。

---

## 3. 模块目标

本模块的核心目标是：

1. 通过 `task_id` 读取上游 Task Specification、Task Interpretation、Dataset Profile 和 Workflow Plan；
2. 检查上游状态是否满足特征工程执行条件；
3. 根据 Workflow Plan 中的 `feature_strategy` 和 Dataset Profile 中的数据事实，选择合适的特征生成方式；
4. 对 composition、structure、descriptor 等不同输入模态执行对应的特征工程；
5. 生成可供后续 Pipeline Generation / Pipeline Execution 使用的特征矩阵；
6. 输出特征列清单、特征类型、特征数量、缺失值情况、失败样本、特征生成日志；
7. 生成标准化 `Feature Engineering Object`；
8. 持久化特征工程元数据和特征文件引用；
9. 为后续模型训练、Pipeline Generation 和 Report Generation 提供可复用输入。

---

## 4. 系统边界

### 4.1 本模块负责的内容

本模块负责：

1. 读取最新 Workflow Plan；
2. 读取最新 Dataset Profile；
3. 加载或重建原始数据集；
4. 根据 `feature_strategy` 执行特征工程；
5. 生成 composition descriptors；
6. 支持已有 descriptor 输入的识别与整理；
7. 支持基础特征清洗，例如删除全空特征、常量特征；
8. 支持特征缺失值统计；
9. 支持特征矩阵预览；
10. 支持记录特征生成失败样本；
11. 支持保存特征矩阵文件；
12. 支持输出 Feature Engineering Object；
13. 支持查询、重跑和版本追踪。

---

### 4.2 本模块不负责的内容

本模块不负责：

1. 不负责收集用户任务输入；
2. 不负责重新理解任务语义；
3. 不负责重新制定 Workflow Plan；
4. 不负责模型选择；
5. 不负责模型训练；
6. 不负责超参数搜索；
7. 不负责模型评估；
8. 不负责判断最佳模型；
9. 不负责生成完整 Pipeline 代码；
10. 不负责最终报告生成。

特别注意：

```text
本模块只回答“如何把原始材料输入转换为可建模特征矩阵”；
不回答“用什么模型训练、模型效果如何、最终 Pipeline 代码怎么写”。
```

---

## 5. 上游输入

## 5.1 输入来源一：Task Specification Object

本模块主要消费以下字段：

| 字段                | 说明                    |
| ----------------- | --------------------- |
| task_id           | 任务唯一 ID               |
| task_type         | 任务类型                  |
| input_type        | 原始输入类型                |
| target_column     | 目标列                   |
| evaluation_metric | 评价指标                  |
| user_priority     | 用户偏好                  |
| constraints       | 用户约束                  |
| status            | Task Specification 状态 |

---

## 5.2 输入来源二：Task Interpretation Object

本模块主要消费以下字段：

| 字段                            | 说明           |
| ----------------------------- | ------------ |
| interpretation_id             | 任务理解结果 ID    |
| interpreted_task_type         | LLM 理解后的任务类型 |
| interpreted_input_modality    | LLM 理解后的输入模态 |
| interpreted_material_domain   | 材料体系         |
| interpreted_prediction_target | 标准化目标属性      |
| modeling_intent               | 建模意图         |
| constraint_interpretation     | 用户约束解析       |
| warnings                      | 任务理解警告       |

---

## 5.3 输入来源三：Dataset Profile Object

本模块主要消费以下字段：

| 字段                      | 说明           |
| ----------------------- | ------------ |
| dataset_profile_id      | 数据画像 ID      |
| dataset_source          | 数据来源         |
| dataset_schema          | 字段结构         |
| modality_check          | 输入模态检查结果     |
| data_quality            | 数据质量结果       |
| target_profile          | 目标变量画像       |
| profiling_summary       | 数据画像摘要       |
| workflow_planning_input | 工作流规划输入      |
| preview_json            | 数据预览，可用于前端展示 |

---

## 5.4 输入来源四：Workflow Plan Object

本模块最关键的上游输入是 Workflow Plan。

重点消费：

| 字段                        | 说明               |
| ------------------------- | ---------------- |
| workflow_plan_id          | 工作流规划 ID         |
| data_strategy             | 数据处理策略           |
| feature_strategy          | 特征工程策略           |
| validation_strategy       | 验证策略，后续保留        |
| evaluation_strategy       | 评价策略，后续保留        |
| pipeline_generation_input | 后续 Pipeline 生成输入 |
| planning_warnings         | 规划警告             |
| planning_assumptions      | 规划假设             |
| status                    | 规划状态             |

其中最重要的是：

```json
{
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "recommended_featurizers": [
      "elemental_property_statistics",
      "stoichiometric_features"
    ],
    "requires_structure_features": false,
    "feature_selection_required": true,
    "feature_scaling_required": true
  }
}
```

---

## 6. 前置条件

### 6.1 必须满足

进入本模块前必须满足：

1. `task_id` 存在；
2. Task Specification 状态为 `valid` 或 `valid_with_warning`；
3. Task Interpretation 状态为 `interpreted` 或 `interpreted_with_warning`；
4. Dataset Profile 状态为 `profiled` 或 `profiled_with_warning`；
5. Dataset Profile 中 `is_usable_for_ml = true`；
6. Workflow Plan 状态为 `planned` 或 `planned_with_warning`；
7. Workflow Plan 中必须存在 `feature_strategy`；
8. Dataset Profile 中必须存在输入列和目标列；
9. 原始数据集可被重新加载或可通过文件引用读取。

---

### 6.2 不允许进入本模块的情况

| 情况                          | 处理方式                            |
| --------------------------- | ------------------------------- |
| task_id 不存在                 | 返回 `TASK_NOT_FOUND`             |
| Task Specification 不可用      | 返回 `TASK_NOT_READY`             |
| Task Interpretation 不存在或不可用 | 返回 `INTERPRETATION_NOT_READY`   |
| Dataset Profile 不存在或不可用     | 返回 `DATASET_PROFILE_NOT_READY`  |
| Workflow Plan 不存在或不可用       | 返回 `WORKFLOW_PLAN_NOT_READY`    |
| feature_strategy 缺失         | 返回 `FEATURE_STRATEGY_MISSING`   |
| 数据不可用于机器学习                  | 返回 `DATASET_NOT_USABLE_FOR_ML`  |
| 原始数据无法加载                    | 返回 `RAW_DATA_LOAD_FAILED`       |
| 输入模态暂不支持                    | 返回 `INPUT_MODALITY_UNSUPPORTED` |

---

## 7. 输出对象

### 7.1 输出对象名称

```text
Feature Engineering Object
```

---

### 7.2 输出对象示例

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
    "executed_featurizers": [
      {
        "name": "elemental_property_statistics",
        "status": "success",
        "n_features_generated": 132,
        "failed_sample_count": 0
      },
      {
        "name": "stoichiometric_features",
        "status": "success",
        "n_features_generated": 8,
        "failed_sample_count": 0
      }
    ]
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
    "feature_columns": ["mean_atomic_number", "max_electronegativity", "..."],
    "numeric_feature_count": 140,
    "categorical_feature_count": 0,
    "constant_feature_count": 0,
    "all_missing_feature_count": 0
  },
  "feature_quality": {
    "missing_values": {
      "total_missing": 0,
      "columns_with_missing": []
    },
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
    "feature_columns": ["mean_atomic_number", "max_electronegativity"],
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

## 8. 核心功能需求

## 8.1 功能一：获取上游上下文

### 输入

```text
task_id
```

### 处理

1. 查询 Task Specification；
2. 查询最新 Task Interpretation；
3. 查询最新 Dataset Profile；
4. 查询最新 Workflow Plan；
5. 检查所有上游对象状态；
6. 构建 Feature Engineering Context。

### 输出

```json
{
  "task_id": "task_xxxxxxxx",
  "task_specification": {},
  "task_interpretation": {},
  "dataset_profile": {},
  "workflow_plan": {},
  "feature_strategy": {}
}
```

---

## 8.2 功能二：重建或加载原始数据

### 输入

```text
dataset_source
dataset_reference
uploaded_file_id
dataset_profile_id
```

### 处理

1. 根据 Dataset Profile 中的 `dataset_source` 判断数据来源；
2. 对 public_benchmark 数据集，复用 Dataset Profile 模块的 Loader；
3. 对 uploaded_file 数据集，根据文件引用重新加载；
4. 返回原始 DataFrame；
5. 不在此阶段重新进行完整 dataset profiling。

### 输出

```json
{
  "is_loaded": true,
  "n_rows": 4604,
  "n_columns": 2,
  "columns": ["composition", "band_gap"]
}
```

---

## 8.3 功能三：解析 Feature Strategy

### 输入

```text
workflow_plan.feature_strategy
dataset_profile.workflow_planning_input
```

### 处理

解析：

1. feature_type；
2. recommended_featurizers；
3. 是否需要结构特征；
4. 是否需要特征缩放；
5. 是否需要特征选择；
6. 是否需要保留原始输入列；
7. 是否存在不支持的 featurizer。

### 输出

```json
{
  "feature_type": "composition_descriptors",
  "selected_featurizers": [
    "elemental_property_statistics",
    "stoichiometric_features"
  ],
  "scaling_required": true,
  "feature_selection_required": true
}
```

---

## 8.4 功能四：Composition 特征工程

### 输入

```text
composition column
selected_featurizers
```

### MVP 支持特征

MVP 阶段建议支持轻量级 composition descriptors：

1. 元素数量；
2. 化学式原子总数；
3. 平均原子序数；
4. 最大/最小原子序数；
5. 平均原子量；
6. 最大/最小原子量；
7. 平均电负性；
8. 最大/最小电负性；
9. 化学计量相关特征；
10. 简单元素统计特征。

### 后续扩展

后续可接入：

1. matminer composition featurizers；
2. Magpie descriptors；
3. pymatgen Composition；
4. 领域知识增强特征；
5. 手工物理化学特征库。

### 输出

```json
{
  "featurizer": "composition_descriptors",
  "status": "success",
  "n_features_generated": 140,
  "failed_sample_count": 0
}
```

---

## 8.5 功能五：Descriptor 输入处理

### 输入

```text
descriptor columns
target column
```

### 处理

当输入模态为 `descriptor` 时：

1. 识别数值型 descriptor 列；
2. 排除 target_column；
3. 排除非数值列或将其标记为不可用；
4. 检查常量 descriptor；
5. 检查缺失值；
6. 生成 feature matrix。

### 输出

```json
{
  "feature_type": "existing_descriptors",
  "n_features": 128,
  "dropped_columns": [],
  "warnings": []
}
```

---

## 8.6 功能六：Structure 特征工程预留

### MVP 处理方式

MVP 阶段不强制实现完整 structure descriptors。

当输入模态为 `structure` 时：

1. 如果 Workflow Plan 要求结构特征，但系统未配置结构 featurizer，则返回 `STRUCTURE_FEATURIZER_NOT_AVAILABLE`；
2. 如果已有结构 descriptor 列，则按 descriptor 输入处理；
3. 在 Feature Engineering Object 中记录该限制。

### 后续扩展

未来支持：

1. pymatgen Structure；
2. matminer structure featurizers；
3. density/symmetry descriptors；
4. local environment descriptors；
5. graph representation。

---

## 8.7 功能七：特征矩阵构建

### 输入

```text
raw dataframe
generated feature dataframe
target_column
```

### 处理

1. 保持样本顺序；
2. 生成 sample_id；
3. 合并特征列和目标列；
4. 删除非特征原始列，或保留到 metadata；
5. 检查特征矩阵行数是否与原始数据一致；
6. 检查目标列是否保留；
7. 输出标准化 feature matrix。

### 输出

```json
{
  "n_samples": 4604,
  "n_features": 140,
  "target_column": "band_gap",
  "feature_columns": []
}
```

---

## 8.8 功能八：特征质量检查

### 输入

```text
feature matrix
feature columns
target column
```

### 处理

检查：

1. 特征缺失值；
2. 全空特征；
3. 常量特征；
4. 非数值特征；
5. 无限值；
6. NaN 比例；
7. 失败样本；
8. 特征数量是否为 0。

### 输出

```json
{
  "missing_values": {},
  "constant_features": [],
  "all_missing_features": [],
  "invalid_features": [],
  "failed_samples": [],
  "is_valid_feature_matrix": true
}
```

---

## 8.9 功能九：特征文件保存

### 输入

```text
feature matrix
feature_engineering_id
```

### 处理

1. 将特征矩阵保存为文件；
2. MVP 推荐保存为 CSV 或 Parquet；
3. 生成 artifact_id；
4. 记录文件路径、样本数、特征数；
5. 不在 API 响应中直接返回完整矩阵。

### 输出

```json
{
  "artifact_id": "artifact_features_xxxxxxxx",
  "storage_type": "local_file",
  "file_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet"
}
```

---

## 8.10 功能十：生成下游输入

### 输入

```text
feature_matrix
feature_schema
feature_quality
workflow_plan
```

### 处理

构建后续模块可消费的 `downstream_input`：

1. feature_matrix_artifact_id；
2. feature_columns；
3. target_column；
4. task_type；
5. primary_metric；
6. scaling_required；
7. imputation_required；
8. feature_selection_required；
9. ready_for_pipeline_generation。

### 输出

```json
{
  "downstream_input": {
    "feature_matrix_artifact_id": "artifact_features_xxxxxxxx",
    "target_column": "band_gap",
    "feature_columns": [],
    "task_type": "regression",
    "primary_metric": "MAE",
    "ready_for_pipeline_generation": true
  }
}
```

---

## 9. 状态设计

### 9.1 状态枚举

| 状态                     | 含义               |
| ---------------------- | ---------------- |
| pending                | 已创建特征工程任务，但尚未执行  |
| loading_data           | 正在加载原始数据         |
| featurizing            | 正在生成特征           |
| validating             | 正在检查特征矩阵         |
| completed              | 特征工程完成           |
| completed_with_warning | 特征工程完成，但存在非阻断性问题 |
| failed                 | 特征工程失败           |
| blocked                | 上游状态不满足条件        |

---

### 9.2 状态流转

```text
收到 feature engineering 请求
    ↓
检查上游状态
    ├── 不满足条件 → blocked
    └── 满足条件
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

---

## 10. API 需求

## 10.1 创建 Feature Engineering 结果

```text
POST /api/feature-engineering/{task_id}
```

### 功能

根据 task_id 读取上游四个模块结果，执行自动化特征工程。

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

## 10.2 查询 Feature Engineering 结果

```text
GET /api/feature-engineering/{feature_engineering_id}
```

### 功能

根据 feature_engineering_id 查询完整 Feature Engineering Object。

---

## 10.3 查询某任务最新 Feature Engineering 结果

```text
GET /api/tasks/{task_id}/feature-engineering
```

### 功能

返回某个 task_id 最新一条 Feature Engineering Object。

---

## 10.4 重新执行 Feature Engineering

```text
POST /api/feature-engineering/{task_id}/rerun
```

### 功能

重新执行特征工程。

### 处理原则

1. 不覆盖旧结果；
2. 新增一条 Feature Engineering 记录；
3. 默认查询最新一条；
4. 保留历史版本，便于比较不同特征方案。

---

## 10.5 特征矩阵预览接口

```text
GET /api/feature-engineering/{feature_engineering_id}/preview
```

### 功能

返回特征矩阵前 N 行预览。

### 注意

1. 默认返回前 20 行；
2. 不返回完整大矩阵；
3. 数值保留合理精度；
4. 大字段截断。

---

## 11. 数据库设计

## 11.1 表名

```text
feature_engineering
```

---

## 11.2 字段设计

| 字段                    | 类型          | 说明                            |
| --------------------- | ----------- | ----------------------------- |
| id                    | VARCHAR     | 主键，格式 `feat_xxxxxxxx`         |
| task_id               | VARCHAR     | 关联 Task Specification         |
| interpretation_id     | VARCHAR     | 关联 Task Interpretation        |
| dataset_profile_id    | VARCHAR     | 关联 Dataset Profile            |
| workflow_plan_id      | VARCHAR     | 关联 Workflow Plan              |
| status                | VARCHAR     | 特征工程状态                        |
| input_modality        | VARCHAR     | 输入模态                          |
| feature_type          | VARCHAR     | 特征类型                          |
| n_samples             | INTEGER     | 样本数                           |
| n_features            | INTEGER     | 特征数                           |
| target_column         | VARCHAR     | 目标列                           |
| artifact_id           | VARCHAR     | 特征矩阵文件 ID                     |
| artifact_path         | TEXT        | 特征矩阵文件路径                      |
| is_ready_for_pipeline | BOOLEAN     | 是否可进入后续 Pipeline              |
| feature_json          | JSONB       | 完整 Feature Engineering Object |
| preview_json          | JSONB       | 特征矩阵预览                        |
| error_message         | TEXT        | 错误信息                          |
| created_at            | TIMESTAMPTZ | 创建时间                          |
| updated_at            | TIMESTAMPTZ | 更新时间                          |

---

## 11.3 索引设计

| 索引                              | 说明           |
| ------------------------------- | ------------ |
| PRIMARY KEY(id)                 | 主键索引         |
| INDEX(task_id)                  | 根据任务查询特征工程结果 |
| INDEX(workflow_plan_id)         | 根据工作流规划查询结果  |
| INDEX(dataset_profile_id)       | 根据数据画像查询结果   |
| INDEX(status)                   | 按状态筛选        |
| INDEX(created_at)               | 查询最新记录       |
| INDEX(task_id, created_at DESC) | 查询某任务最新结果    |

---

## 11.4 存储原则

继续沿用当前系统的混合存储策略：

```text
高频查询字段单独建列
+
复杂嵌套对象存入 JSONB
+
大矩阵文件存储到 artifact 路径
```

不建议将完整特征矩阵直接存入 JSONB。

---

## 12. 后端模块结构建议

新增模块目录：

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
├── featurizers/
│   ├── __init__.py
│   ├── base_featurizer.py
│   ├── composition_featurizer.py
│   ├── descriptor_featurizer.py
│   └── structure_featurizer.py
├── checkers/
│   ├── __init__.py
│   └── feature_quality_checker.py
├── artifact_manager.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

## 12.1 文件职责

| 文件                                    | 职责                                                   |
| ------------------------------------- | ---------------------------------------------------- |
| api.py                                | 定义 Feature Engineering 相关 HTTP 接口                    |
| schemas.py                            | 定义请求、响应、内部 DTO                                       |
| service.py                            | 编排上游读取、数据加载、特征生成、质量检查、持久化                            |
| model.py                              | 定义 feature_engineering 数据库表                          |
| repository.py                         | 提供 Feature Engineering CRUD                          |
| context_builder.py                    | 读取 Task、Interpretation、Dataset Profile、Workflow Plan |
| data_loader_adapter.py                | 复用 Dataset Profile 模块的 Loader 重建原始数据                 |
| strategy_resolver.py                  | 解析 Workflow Plan 中的 feature_strategy                 |
| featurizers/base_featurizer.py        | 定义统一 Featurizer 接口                                   |
| featurizers/composition_featurizer.py | 生成 composition descriptors                           |
| featurizers/descriptor_featurizer.py  | 处理已有 descriptor 输入                                   |
| featurizers/structure_featurizer.py   | 预留结构特征生成                                             |
| checkers/feature_quality_checker.py   | 检查特征矩阵质量                                             |
| artifact_manager.py                   | 保存和读取特征矩阵文件                                          |
| builder.py                            | 构建 Feature Engineering Object                        |
| enums.py                              | 定义状态、特征类型、artifact 类型等枚举                             |
| exceptions.py                         | 定义模块专用异常                                             |

---

## 13. 与已实现模块的衔接

## 13.1 与 Task Specification 模块的关系

本模块只读取 Task Specification，不修改。

主要消费：

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

---

## 13.2 与 Task Interpretation 模块的关系

本模块只读取 Task Interpretation，不修改。

主要消费：

```text
interpreted_task_type
interpreted_input_modality
interpreted_material_domain
interpreted_prediction_target
constraint_interpretation
warnings
```

---

## 13.3 与 Dataset Profile 模块的关系

本模块依赖 Dataset Profile 提供：

```text
dataset_source
dataset_schema
workflow_planning_input
data_quality
target_profile
is_usable_for_ml
```

本模块可以复用 Dataset Profile 模块的数据加载器，但不重新执行完整数据画像。

---

## 13.4 与 Workflow Planning 模块的关系

本模块依赖 Workflow Plan 提供：

```text
data_strategy
feature_strategy
evaluation_strategy
pipeline_generation_input
planning_warnings
planning_assumptions
```

其中最关键的是：

```text
feature_strategy
```

本模块执行 Workflow Plan 中的特征工程意图，但不修改 Workflow Plan。

---

## 13.5 与后续 Pipeline Generation 模块的关系

本模块输出：

```text
Feature Engineering Object
downstream_input
feature_matrix artifact
```

Pipeline Generation 模块后续应重点消费：

1. feature_matrix_artifact_id；
2. feature_columns；
3. target_column；
4. preprocessing_requirements；
5. task_type；
6. primary_metric；
7. ready_for_pipeline_generation。

---

## 14. 错误处理

### 14.1 错误码设计

| 错误码                           | 场景                       |
| ----------------------------- | ------------------------ |
| TASK_NOT_FOUND                | task_id 不存在              |
| TASK_NOT_READY                | Task Specification 状态不允许 |
| INTERPRETATION_NOT_READY      | Task Interpretation 不可用  |
| DATASET_PROFILE_NOT_READY     | Dataset Profile 不可用      |
| WORKFLOW_PLAN_NOT_READY       | Workflow Plan 不可用        |
| FEATURE_STRATEGY_MISSING      | feature_strategy 缺失      |
| RAW_DATA_LOAD_FAILED          | 原始数据加载失败                 |
| INPUT_MODALITY_UNSUPPORTED    | 输入模态不支持                  |
| FEATURIZER_NOT_AVAILABLE      | 指定 featurizer 不可用        |
| FEATURE_GENERATION_FAILED     | 特征生成失败                   |
| FEATURE_MATRIX_INVALID        | 特征矩阵不可用                  |
| FEATURE_ARTIFACT_SAVE_FAILED  | 特征文件保存失败                 |
| FEATURE_ENGINEERING_NOT_FOUND | 查询不到特征工程结果               |

---

### 14.2 非阻断性 Warning

以下问题不一定阻断流程，但应进入 warnings：

1. 部分样本特征生成失败；
2. 部分特征存在缺失值；
3. 删除了常量特征；
4. 删除了全空特征；
5. 使用了 MVP 简化特征而非完整 matminer 特征；
6. 结构输入暂未支持完整结构特征；
7. 特征数量较少；
8. 用户要求的 featurizer 被替换为可用 featurizer；
9. 特征缩放/选择尚未执行，仅标记为后续要求。

---

## 15. 前端需求

## 15.1 前端模块目录建议

```text
frontend/src/modules/featureEngineering/
├── components/
│   ├── FeatureEngineeringPanel.tsx
│   ├── FeatureSummaryCard.tsx
│   ├── FeaturizerResultCard.tsx
│   ├── FeatureQualityCard.tsx
│   ├── FeaturePreviewTable.tsx
│   ├── FeatureWarningList.tsx
│   └── FeatureEngineeringJsonViewer.tsx
├── types.ts
└── constants.ts
```

---

## 15.2 前端 API 客户端

新增：

```text
frontend/src/api/featureEngineeringApi.ts
```

封装接口：

```text
createFeatureEngineering(taskId)
getFeatureEngineering(featureEngineeringId)
getLatestFeatureEngineeringByTaskId(taskId)
rerunFeatureEngineering(taskId)
getFeatureMatrixPreview(featureEngineeringId)
```

---

## 15.3 前端展示内容

MVP 阶段展示：

1. Feature Engineering 状态；
2. 输入模态；
3. 特征类型；
4. 使用的 featurizer；
5. 样本数；
6. 特征数；
7. 目标列；
8. 特征矩阵 artifact；
9. 特征质量；
10. dropped features；
11. failed samples；
12. warnings/errors；
13. 特征预览；
14. 是否 ready for pipeline generation；
15. 完整 JSON。

---

## 16. MVP 验收标准

| 序号 | 验收标准                                          |
| -- | --------------------------------------------- |
| 1  | 能通过 task_id 获取 Task Specification             |
| 2  | 能通过 task_id 获取最新 Task Interpretation          |
| 3  | 能通过 task_id 获取最新 Dataset Profile              |
| 4  | 能通过 task_id 获取最新 Workflow Plan                |
| 5  | 能拒绝上游状态不满足的任务                                 |
| 6  | 能读取 Workflow Plan 中的 feature_strategy         |
| 7  | 能重新加载原始数据集                                    |
| 8  | 能支持 composition 输入的基础特征工程                     |
| 9  | 能支持 descriptor 输入的特征矩阵整理                      |
| 10 | 能对 structure 输入给出明确 unsupported 或 fallback 结果 |
| 11 | 能生成 feature matrix                            |
| 12 | 能保留 target column                             |
| 13 | 能统计 feature columns                           |
| 14 | 能检查缺失特征、常量特征、全空特征                             |
| 15 | 能保存特征矩阵 artifact                              |
| 16 | 能生成 Feature Engineering Object                |
| 17 | 能持久化 Feature Engineering Object               |
| 18 | 能查询某任务最新 Feature Engineering 结果               |
| 19 | 能重新执行特征工程且不覆盖旧结果                              |
| 20 | 能返回特征矩阵预览                                     |
| 21 | 不训练模型                                         |
| 22 | 不执行 HPO                                       |
| 23 | 不生成完整 Pipeline 代码                             |
| 24 | 不计算模型评估指标                                     |

---

## 17. 示例流程

### 17.1 输入

Workflow Plan 中包含：

```json
{
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "recommended_featurizers": [
      "elemental_property_statistics",
      "stoichiometric_features"
    ],
    "requires_structure_features": false,
    "feature_selection_required": true,
    "feature_scaling_required": true
  }
}
```

Dataset Profile 中包含：

```json
{
  "workflow_planning_input": {
    "input_modality": "composition",
    "input_columns": ["composition"],
    "target_column": "band_gap",
    "task_type": "regression",
    "is_usable_for_ml": true
  }
}
```

---

### 17.2 处理流程

```text
POST /api/feature-engineering/task_xxxxxxxx
    ↓
读取 Task Specification
    ↓
读取最新 Task Interpretation
    ↓
读取最新 Dataset Profile
    ↓
读取最新 Workflow Plan
    ↓
检查上游状态
    ↓
加载原始数据
    ↓
解析 feature_strategy
    ↓
对 composition 列生成 descriptors
    ↓
构建 feature matrix
    ↓
检查特征质量
    ↓
保存 feature matrix artifact
    ↓
构建 Feature Engineering Object
    ↓
写入 feature_engineering 表
    ↓
返回前端展示
```

---

### 17.3 输出

```json
{
  "feature_engineering_id": "feat_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "status": "completed",
  "input_modality": "composition",
  "feature_type": "composition_descriptors",
  "feature_matrix": {
    "artifact_id": "artifact_features_xxxxxxxx",
    "n_samples": 4604,
    "n_features": 140,
    "target_column": "band_gap"
  },
  "feature_schema": {
    "numeric_feature_count": 140,
    "feature_columns": []
  },
  "feature_quality": {
    "missing_values": {},
    "dropped_features": [],
    "failed_samples": []
  },
  "downstream_input": {
    "feature_matrix_artifact_id": "artifact_features_xxxxxxxx",
    "ready_for_pipeline_generation": true
  }
}
```

---

## 18. 后续迭代方向

MVP 后可扩展：

1. 接入 pymatgen Composition 解析；
2. 接入 matminer composition featurizers；
3. 接入 Magpie descriptors；
4. 支持 structure descriptors；
5. 支持 CIF/POSCAR 文件特征工程；
6. 支持 graph-based representation；
7. 支持特征选择实际执行；
8. 支持特征缩放实际执行；
9. 支持特征工程 Pipeline 序列化；
10. 支持多套特征方案并行生成；
11. 支持 LLM 根据失败原因重新选择 featurizer；
12. 支持特征重要性反馈后的特征重构；
13. 支持 artifact 版本管理；
14. 支持大规模异步特征生成任务；
15. 支持特征矩阵缓存与复用。

---

## 19. 总结

Automated Feature Engineering 模块是连接 Workflow Planning 与后续 Pipeline Generation / Pipeline Execution 的特征转换层。

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

本模块最终应回答：

```text
原始材料输入如何转化为机器学习特征？
使用了哪些 featurizer？
生成了多少特征？
特征矩阵是否可用？
哪些样本或特征存在问题？
后续 Pipeline Generation 应使用哪个 feature artifact？
```

本模块不应回答：

```text
应该训练哪个模型？
模型效果是多少？
是否完成 HPO？
最终最佳模型是什么？
Pipeline 代码如何生成？
```

该模块输出的 Feature Engineering Object 将成为后续 Pipeline Generation、Pipeline Execution、Metric Evaluation 和 Report Generation 的重要基础。

