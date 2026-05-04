# PRD-6：Feature Preprocessing 模块需求文档

## 1. 模块名称

Feature Preprocessing  
特征矩阵校验与建模前预处理执行模块

---

## 2. 模块定位

本模块位于 **Automated Feature Engineering** 之后、**Automated Model and HPO Search** 之前。

调整后的系统流程为：

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
Feature Matrix Validation & Preprocessing Execution
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

当前 Feature Engineering 模块的职责是根据 Workflow Plan 中的 `feature_strategy` 执行 featurizer，构建特征矩阵，检查特征质量，并保存 feature artifact。
但 Feature Engineering 的产物仍可能包含非数值对象列、全空特征、常量特征、高缺失率特征或未经填补/缩放的数值特征。因此，本模块负责将 Feature Engineering 输出的 **raw feature matrix** 转换为 **model-ready feature matrix**。

---

## 3. 需求背景

在扩展 Feature Engineering 后，系统可能引入 pymatgen、matminer 等外部特征库。此时特征矩阵中可能出现：

1. `_pymatgen_composition` 等中间对象列；
2. object / dict / list 等不可建模字段；
3. 全空特征列；
4. 常量特征列；
5. 高缺失率特征列；
6. 含 `inf`、`-inf` 的非法数值列；
7. 部分 feature group 完全无效；
8. 需要 imputation、scaling、encoding、basic feature selection 的特征列。

如果直接进入 Automated Model and HPO Search，模型训练会出现报错、隐性数据污染或无效搜索。因此，需要新增一个模块，在模型搜索前完成严格的特征矩阵校验与实际预处理执行。

---

## 4. 模块目标

本模块的核心目标是：

1. 读取最新 Feature Engineering Object；
2. 加载 Feature Engineering 输出的 feature matrix artifact；
3. 严格校验特征矩阵是否可建模；
4. 删除非数值对象列、全空列、常量列、高缺失率列；
5. 对保留的缺失值执行 imputation；
6. 对需要缩放的数值特征执行 scaling；
7. 对允许的类别特征执行 encoding；
8. 可选执行基础 feature selection；
9. 生成 fitted preprocessing artifact；
10. 生成 model-ready feature matrix artifact；
11. 输出标准化的 Feature Matrix Preprocessing Object；
12. 为 Automated Model and HPO Search 提供真正可直接使用的 `model_search_input`。

---

## 5. 系统边界

### 5.1 本模块负责的内容

本模块负责：

1. 读取 Task Specification；
2. 读取 Task Interpretation；
3. 读取 Dataset Profile；
4. 读取 Workflow Plan；
5. 读取 Feature Engineering Object；
6. 加载 feature matrix artifact；
7. 校验 target column 是否存在；
8. 校验 feature columns 是否可建模；
9. 删除非法列；
10. 删除全空列；
11. 删除常量列；
12. 删除高缺失率列；
13. 执行缺失值填补；
14. 执行数值特征缩放；
15. 执行类别特征编码，MVP 可默认关闭；
16. 执行基础特征筛选，MVP 可实现方差过滤；
17. 保存 fitted preprocessing pipeline artifact；
18. 保存 model-ready feature matrix artifact；
19. 输出 model_search_input。

---

### 5.2 本模块不负责的内容

本模块不负责：

1. 不重新执行任务输入；
2. 不重新执行 LLM 任务理解；
3. 不重新加载原始数据集；
4. 不重新执行 Dataset Profiling；
5. 不重新执行 Workflow Planning；
6. 不重新生成材料特征；
7. 不调用 pymatgen / matminer 生成新特征；
8. 不训练模型；
9. 不执行 HPO；
10. 不计算模型评估指标；
11. 不选择最佳模型；
12. 不生成完整 Pipeline 代码；
13. 不做结果诊断；
14. 不生成最终报告。

特别注意：

```text
本模块负责 “raw feature matrix → model-ready feature matrix”；
不负责 “model-ready feature matrix → model training / HPO”。
```

---

## 6. 上游输入

### 6.1 Task Specification Object

主要消费：

| 字段                | 说明                                    |
| ----------------- | ------------------------------------- |
| task_id           | 任务 ID                                 |
| task_type         | regression / classification / ranking |
| target_column     | 目标列                                   |
| evaluation_metric | 用户指定评价指标                              |
| status            | 任务状态                                  |

---

### 6.2 Task Interpretation Object

主要消费：

| 字段                            | 说明           |
| ----------------------------- | ------------ |
| interpretation_id             | 任务理解 ID      |
| interpreted_task_type         | LLM 解释后的任务类型 |
| interpreted_input_modality    | 输入模态         |
| interpreted_prediction_target | 标准化预测目标      |
| modeling_intent               | 建模意图         |

---

### 6.3 Dataset Profile Object

主要消费：

| 字段                      | 说明      |
| ----------------------- | ------- |
| dataset_profile_id      | 数据画像 ID |
| target_profile          | 目标变量画像  |
| data_quality            | 原始数据质量  |
| profiling_summary       | 数据画像摘要  |
| workflow_planning_input | 工作流规划输入 |

Dataset Profile 当前已经输出 `dataset_source`、`dataset_schema`、`target_profile`、`data_quality`、`profiling_summary`、`workflow_planning_input` 和 preview 等对象。

---

### 6.4 Workflow Plan Object

主要消费：

| 字段                        | 说明            |
| ------------------------- | ------------- |
| workflow_plan_id          | 工作流规划 ID      |
| model_strategy            | 候选模型族，透传给模型搜索 |
| validation_strategy       | 验证策略，透传给模型搜索  |
| evaluation_strategy       | 评价指标策略        |
| hpo_strategy              | HPO 搜索策略      |
| interpretability_strategy | 可解释性策略        |
| feature_strategy          | 特征策略，用于校验一致性  |

Workflow Plan 当前已经包含 `model_strategy`、`validation_strategy`、`evaluation_strategy`、`hpo_strategy`、`interpretability_strategy` 和 `pipeline_generation_input` 等策略对象。

---

### 6.5 Feature Engineering Object

本模块最关键输入。

重点消费：

| 字段                         | 说明                                 |
| -------------------------- | ---------------------------------- |
| feature_engineering_id     | 特征工程结果 ID                          |
| status                     | completed / completed_with_warning |
| feature_generation         | featurizer 执行记录                    |
| feature_matrix             | raw feature matrix artifact        |
| feature_schema             | 原始特征列、特征组、特征数量                     |
| feature_quality            | 初步特征质量检查                           |
| preprocessing_requirements | 初步预处理需求                            |
| downstream_input           | Feature Engineering 下游输入           |
| warnings / errors          | 上游特征工程警告和错误                        |

---

## 7. 前置条件

进入本模块必须满足：

1. `task_id` 存在；
2. Task Specification 状态为 `valid` 或 `valid_with_warning`；
3. Task Interpretation 状态为 `interpreted` 或 `interpreted_with_warning`；
4. Dataset Profile 状态为 `profiled` 或 `profiled_with_warning`；
5. Workflow Plan 状态为 `planned` 或 `planned_with_warning`；
6. Feature Engineering 状态为 `completed` 或 `completed_with_warning`；
7. Feature Engineering Object 中存在 `feature_matrix.artifact_id`；
8. Feature Engineering Object 中存在 `feature_matrix.file_path`；
9. feature matrix artifact 文件可读取；
10. target column 存在。

---

## 8. 输出对象

### 8.1 输出对象名称

```text
Feature Matrix Preprocessing Object
```

数据库表建议命名：

```text
feature_matrix_preprocessing
```

---

### 8.2 输出对象示例

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
    "dropped_invalid_features": [
      {
        "name": "_pymatgen_composition",
        "reason": "non_numeric_object_column",
        "action": "dropped"
      }
    ],
    "dropped_all_missing_features": [],
    "dropped_constant_features": [],
    "dropped_high_missing_features": [],
    "retained_features": []
  },
  "feature_group_validation": {
    "groups": [
      {
        "group_name": "matminer_element_property",
        "n_raw_features": 80,
        "n_valid_features": 0,
        "status": "dropped",
        "reason": "all_features_invalid_or_constant"
      },
      {
        "group_name": "matminer_stoichiometry",
        "n_raw_features": 8,
        "n_valid_features": 6,
        "status": "retained"
      }
    ]
  },
  "preprocessing_execution": {
    "imputation": {
      "executed": true,
      "strategy": "median",
      "columns": [],
      "artifact_component": "numeric_imputer"
    },
    "scaling": {
      "executed": true,
      "strategy": "standard_scaler",
      "columns": [],
      "artifact_component": "numeric_scaler"
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
  "errors": [],
  "created_at": "2026-05-02T10:00:00",
  "updated_at": "2026-05-02T10:00:00"
}
```

---

## 9. 核心功能需求

## 9.1 功能一：获取上游上下文

### 输入

```text
task_id
```

### 处理

1. 查询 Task Specification；
2. 查询最新 Task Interpretation；
3. 查询最新 Dataset Profile；
4. 查询最新 Workflow Plan；
5. 查询最新 Feature Engineering；
6. 校验所有上游状态；
7. 构建 Feature Matrix Preprocessing Context。

### 输出

```json
{
  "task_id": "task_xxxxxxxx",
  "feature_engineering_id": "feat_xxxxxxxx",
  "feature_matrix_artifact": {},
  "target_column": "band_gap",
  "task_type": "regression",
  "workflow_plan": {},
  "preprocessing_requirements": {}
}
```

---

## 9.2 功能二：加载 Feature Matrix Artifact

### 输入

```text
feature_matrix.file_path
```

### 处理

1. 判断 artifact 文件是否存在；
2. 根据格式读取 parquet 或 CSV；
3. 检查 DataFrame 是否为空；
4. 检查 target column 是否存在；
5. 检查 sample_id 是否存在；
6. 提取候选 feature columns。

### 输出

```json
{
  "is_loaded": true,
  "n_samples": 4604,
  "n_columns": 142,
  "target_column": "band_gap",
  "candidate_feature_columns": []
}
```

---

## 9.3 功能三：非法特征列识别与删除

### 输入

```text
feature matrix
candidate_feature_columns
```

### 处理

识别并删除：

1. object 类型列；
2. pymatgen Composition 对象列；
3. dict/list/nested object 列；
4. datetime 列；
5. 无法转换为数值的字符串列；
6. 中间解析列，例如 `_pymatgen_composition`。

MVP 阶段允许直接进入模型的特征类型：

```text
numeric
boolean
```

### 输出

```json
{
  "dropped_invalid_features": [
    {
      "name": "_pymatgen_composition",
      "reason": "unsupported_object_column",
      "action": "dropped"
    }
  ],
  "retained_candidate_features": []
}
```

---

## 9.4 功能四：全空特征删除

### 处理

1. 统计每个特征的 missing_count；
2. missing_ratio = 1.0 的列标记为 all_missing；
3. 默认删除 all_missing features；
4. 写入 dropped features 记录。

---

## 9.5 功能五：常量特征删除

### 处理

1. 对每个特征计算非空 unique_count；
2. unique_count <= 1 的列标记为 constant；
3. 默认删除 constant features；
4. 写入 dropped features 记录。

---

## 9.6 功能六：高缺失率特征删除

### 处理

1. 计算每列 missing_ratio；
2. 默认阈值为 0.5；
3. missing_ratio > threshold 的列标记为 high_missing；
4. 默认删除高缺失率特征；
5. 剩余有缺失值的列进入 imputation。

---

## 9.7 功能七：无限值与非法数值处理

### 处理

1. 检查 `inf`；
2. 检查 `-inf`；
3. 将 `inf/-inf` 替换为 NaN；
4. 若替换后缺失率超过阈值，则删除该列；
5. 否则进入 imputation。

---

## 9.8 功能八：Feature Group 级别校验

### 处理

1. 根据 `{featurizer_id}__{feature_name}` 前缀识别 feature group；
2. 统计每个 group 的 raw feature count；
3. 统计每个 group 的 valid feature count；
4. 如果 group 全部特征被删除，标记 group 为 dropped；
5. 如果 group 部分保留，标记 group 为 retained_with_warning；
6. 输出 group 级别状态。

---

## 9.9 功能九：缺失值填补执行

### 输入

```text
filtered feature matrix
```

### 处理

对保留的数值特征执行 imputation。

默认策略：

| 任务类型           | 默认策略   |
| -------------- | ------ |
| regression     | median |
| classification | median |
| ranking        | median |

要求：

1. imputer 必须 fit 在当前矩阵上；
2. imputer 需要保存到 preprocessing pipeline artifact；
3. 执行后 model-ready matrix 中不应保留 NaN，除非配置允许。

---

## 9.10 功能十：数值特征缩放执行

### 输入

```text
imputed feature matrix
```

### 处理

根据 Workflow Plan 和 Feature Engineering 的 `preprocessing_requirements.scaling_required` 决定是否执行 scaling。

默认策略：

```text
standard_scaler
```

可选策略：

1. standard_scaler；
2. robust_scaler；
3. minmax_scaler；
4. none。

要求：

1. scaler 必须 fit；
2. scaler 必须保存到 preprocessing pipeline artifact；
3. 输出矩阵列名保持不变。

---

## 9.11 功能十一：类别特征编码执行

MVP 阶段默认：

```text
FEATURE_VALIDATION_ALLOW_CATEGORICAL=false
```

处理规则：

1. 如果出现 categorical feature，默认删除；
2. 如果配置允许，则执行 one-hot encoding；
3. 编码后的列名必须可追踪；
4. encoder 需要保存到 preprocessing pipeline artifact。

---

## 9.12 功能十二：基础特征筛选执行

MVP 阶段建议实现：

```text
variance_threshold
```

处理：

1. 删除近似零方差特征；
2. 记录 columns_dropped；
3. 更新 feature_columns；
4. 保存 selector 到 preprocessing pipeline artifact。

后续可扩展：

1. correlation filtering；
2. mutual information；
3. model-based feature selection；
4. SHAP-based selection。

---

## 9.13 功能十三：生成 Model-ready Feature Matrix Artifact

### 处理

1. 创建 model-ready artifact 目录；
2. 保存 `model_ready_features.parquet`；
3. 保存 `preprocessor.joblib`；
4. 保存 `preprocessing_metadata.json`；
5. 保存 `validation_report.json`；
6. 生成 preview_json。

### 输出

```json
{
  "model_ready_artifact": {
    "artifact_id": "artifact_model_ready_xxxxxxxx",
    "file_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/model_ready_features.parquet"
  },
  "preprocessing_pipeline_artifact": {
    "artifact_id": "artifact_preprocessor_xxxxxxxx",
    "file_path": "/app/artifacts/model_ready/fmp_xxxxxxxx/preprocessor.joblib"
  }
}
```

---

## 9.14 功能十四：生成 Model Search Input

### 处理

生成 Automated Model and HPO Search 可直接消费的输入：

1. model_ready_matrix_path；
2. preprocessing_pipeline_artifact_id；
3. target_column；
4. feature_columns；
5. task_type；
6. primary_metric；
7. model_strategy；
8. validation_strategy；
9. evaluation_strategy；
10. hpo_strategy；
11. ready_for_model_search。

---

## 10. Model-ready 判定规则

### 10.1 ready_for_model_search = true 的条件

必须同时满足：

1. feature matrix 成功加载；
2. target_column 存在；
3. 至少存在 1 个有效特征；
4. 样本数 > 0；
5. 所有保留特征均为数值型；
6. 不存在未处理的 NaN；
7. 不存在 `inf/-inf`；
8. 不存在 object 特征；
9. 不存在全空特征；
10. 不存在常量特征；
11. model-ready artifact 保存成功；
12. preprocessing pipeline artifact 保存成功。

---

### 10.2 ready_for_model_search = false 的情况

出现以下任一情况：

1. target_column 缺失；
2. 有效特征数为 0；
3. 清洗后样本数为 0；
4. 所有 feature group 被删除；
5. 缺失值无法填补；
6. 缩放失败；
7. 特征筛选后无特征保留；
8. artifact 保存失败；
9. pipeline artifact 保存失败。

---

## 11. 状态设计

### 11.1 状态枚举

| 状态                        | 含义                                                       |
| ------------------------- | -------------------------------------------------------- |
| pending                   | 已创建预处理任务，尚未执行                                            |
| loading_artifact          | 正在加载 raw feature artifact                                |
| validating                | 正在校验特征矩阵                                                 |
| filtering                 | 正在删除无效特征                                                 |
| preprocessing             | 正在执行 imputation / scaling / encoding / feature selection |
| artifact_saving           | 正在保存 model-ready artifact                                |
| preprocessed              | 预处理完成，可进入模型搜索                                            |
| preprocessed_with_warning | 预处理完成，但存在非阻断警告                                           |
| failed                    | 预处理失败，不可进入模型搜索                                           |
| blocked                   | 上游状态不满足                                                  |

---

### 11.2 状态流转

```text
收到请求
    ↓
检查上游状态
    ├── 不满足 → blocked
    └── 满足
          ↓
        pending
          ↓
        loading_artifact
          ↓
        validating
          ↓
        filtering
          ↓
        preprocessing
          ↓
        artifact_saving
          ↓
        preprocessed / preprocessed_with_warning / failed
```

---

## 12. API 需求

### 12.1 创建 Feature Matrix Preprocessing

```text
POST /api/feature-matrix-preprocessing/{task_id}
```

### 请求体

MVP 阶段可为空。

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
  "message": "Feature matrix preprocessing completed successfully.",
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

### 12.2 查询 Preprocessing 结果

```text
GET /api/feature-matrix-preprocessing/{preprocessing_id}
```

---

### 12.3 查询某任务最新 Preprocessing 结果

```text
GET /api/tasks/{task_id}/feature-matrix-preprocessing
```

---

### 12.4 重新执行 Preprocessing

```text
POST /api/feature-matrix-preprocessing/{task_id}/rerun
```

原则：

1. 不覆盖旧记录；
2. 新增一条 preprocessing 记录；
3. 生成新的 model-ready artifact；
4. 生成新的 preprocessing pipeline artifact；
5. 默认查询最新记录。

---

### 12.5 预览 Model-ready Matrix

```text
GET /api/feature-matrix-preprocessing/{preprocessing_id}/preview
```

---

## 13. 数据库设计

### 13.1 表名

```text
feature_matrix_preprocessing
```

---

### 13.2 字段设计

| 字段                         | 类型          | 说明                                 |
| -------------------------- | ----------- | ---------------------------------- |
| id                         | VARCHAR     | 主键，格式 `fmp_xxxxxxxx`               |
| task_id                    | VARCHAR     | 关联 Task Specification              |
| interpretation_id          | VARCHAR     | 关联 Task Interpretation             |
| dataset_profile_id         | VARCHAR     | 关联 Dataset Profile                 |
| workflow_plan_id           | VARCHAR     | 关联 Workflow Plan                   |
| feature_engineering_id     | VARCHAR     | 关联 Feature Engineering             |
| status                     | VARCHAR     | 预处理状态                              |
| n_samples                  | INTEGER     | 样本数                                |
| n_raw_features             | INTEGER     | 原始特征数                              |
| n_valid_features           | INTEGER     | 有效特征数                              |
| n_final_features           | INTEGER     | 预处理后特征数                            |
| n_dropped_features         | INTEGER     | 删除特征数                              |
| target_column              | VARCHAR     | 目标列                                |
| model_ready_artifact_id    | VARCHAR     | model-ready artifact ID            |
| model_ready_artifact_path  | TEXT        | model-ready artifact 路径            |
| preprocessor_artifact_id   | VARCHAR     | preprocessing pipeline artifact ID |
| preprocessor_artifact_path | TEXT        | preprocessing pipeline artifact 路径 |
| is_ready_for_model_search  | BOOLEAN     | 是否可进入模型搜索                          |
| preprocessing_json         | JSONB       | 完整 Preprocessing Object            |
| preview_json               | JSONB       | model-ready 预览                     |
| error_message              | TEXT        | 错误信息                               |
| created_at                 | TIMESTAMPTZ | 创建时间                               |
| updated_at                 | TIMESTAMPTZ | 更新时间                               |

---

## 14. 后端模块结构建议

新增模块目录：

```text
backend/app/modules/feature_matrix_preprocessing/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── context_builder.py
├── artifact_loader.py
├── column_validator.py
├── feature_group_validator.py
├── feature_filter.py
├── preprocessors/
│   ├── __init__.py
│   ├── imputer.py
│   ├── scaler.py
│   ├── encoder.py
│   └── feature_selector.py
├── preprocessing_pipeline_builder.py
├── artifact_manager.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

## 15. 与已实现模块的衔接

### 15.1 与 Feature Engineering 的关系

Feature Engineering 继续负责：

1. 执行 featurizer；
2. 生成 raw feature matrix；
3. 保存 raw feature artifact；
4. 输出初步 feature_quality；
5. 输出 preprocessing_requirements。

本模块负责：

1. 加载 raw feature artifact；
2. 严格删除无效列；
3. 执行建模前预处理；
4. 保存 model-ready artifact；
5. 保存 preprocessing pipeline artifact。

本模块不修改 Feature Engineering 原始记录。

---

### 15.2 与 Workflow Planning 的关系

本模块读取 Workflow Plan 中的：

1. model_strategy；
2. validation_strategy；
3. evaluation_strategy；
4. hpo_strategy；
5. interpretability_strategy。

但本模块不重新规划 workflow，也不调用 LLM。

---

### 15.3 与 Automated Model and HPO Search 的关系

本模块输出：

```text
model_search_input
```

Automated Model and HPO Search 后续只消费：

1. model_ready_matrix_path；
2. target_column；
3. feature_columns；
4. preprocessing_pipeline_artifact_id；
5. model_strategy；
6. validation_strategy；
7. evaluation_strategy；
8. hpo_strategy；
9. ready_for_model_search。

---

## 16. 错误处理

### 16.1 错误码设计

| 错误码                               | 场景                         |
| --------------------------------- | -------------------------- |
| TASK_NOT_FOUND                    | task_id 不存在                |
| TASK_NOT_READY                    | Task Specification 不可用     |
| INTERPRETATION_NOT_READY          | Task Interpretation 不可用    |
| DATASET_PROFILE_NOT_READY         | Dataset Profile 不可用        |
| WORKFLOW_PLAN_NOT_READY           | Workflow Plan 不可用          |
| FEATURE_ENGINEERING_REQUIRED      | 尚未执行 Feature Engineering   |
| FEATURE_ENGINEERING_NOT_READY     | Feature Engineering 状态不允许  |
| FEATURE_ARTIFACT_MISSING          | feature artifact 缺失        |
| FEATURE_ARTIFACT_LOAD_FAILED      | feature artifact 读取失败      |
| TARGET_COLUMN_MISSING             | 目标列缺失                      |
| NO_VALID_FEATURES                 | 没有有效特征                     |
| IMPUTATION_FAILED                 | 缺失值填补失败                    |
| SCALING_FAILED                    | 特征缩放失败                     |
| ENCODING_FAILED                   | 类别编码失败                     |
| FEATURE_SELECTION_FAILED          | 特征选择失败                     |
| MODEL_READY_ARTIFACT_SAVE_FAILED  | model-ready artifact 保存失败  |
| PREPROCESSOR_ARTIFACT_SAVE_FAILED | preprocessor artifact 保存失败 |

---

### 16.2 Warning 设计

| warning                       | 场景                     |
| ----------------------------- | ---------------------- |
| INVALID_FEATURES_DROPPED      | 非法特征列被删除               |
| ALL_MISSING_FEATURES_DROPPED  | 全空特征被删除                |
| CONSTANT_FEATURES_DROPPED     | 常量特征被删除                |
| HIGH_MISSING_FEATURES_DROPPED | 高缺失率特征被删除              |
| FEATURE_GROUP_DROPPED         | 某个 feature group 被整体删除 |
| IMPUTATION_EXECUTED           | 已执行缺失值填补               |
| SCALING_EXECUTED              | 已执行缩放                  |
| FEATURE_SELECTION_EXECUTED    | 已执行基础特征筛选              |
| LOW_EFFECTIVE_FEATURE_COUNT   | 有效特征数量较少               |
| MODEL_READY_WITH_WARNINGS     | 可进入模型搜索，但存在警告          |

---

## 17. 配置需求

新增 `.env` 配置：

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

## 18. 前端需求

### 18.1 新增前端模块

```text
frontend/src/modules/featureMatrixPreprocessing/
├── components/
│   ├── FeatureMatrixPreprocessingPanel.tsx
│   ├── ValidationSummaryCard.tsx
│   ├── ColumnFilteringCard.tsx
│   ├── FeatureGroupValidationCard.tsx
│   ├── PreprocessingExecutionCard.tsx
│   ├── ModelReadyArtifactCard.tsx
│   ├── ModelReadyPreviewTable.tsx
│   ├── PreprocessingWarningList.tsx
│   └── FeatureMatrixPreprocessingJsonViewer.tsx
├── types.ts
└── constants.ts
```

---

### 18.2 前端 API 客户端

新增：

```text
frontend/src/api/featureMatrixPreprocessingApi.ts
```

封装：

```text
createFeatureMatrixPreprocessing(taskId)
getFeatureMatrixPreprocessing(preprocessingId)
getLatestFeatureMatrixPreprocessingByTaskId(taskId)
rerunFeatureMatrixPreprocessing(taskId)
getModelReadyPreview(preprocessingId)
```

---

### 18.3 前端展示内容

MVP 阶段展示：

1. preprocessing 状态；
2. raw feature count；
3. valid feature count；
4. final feature count；
5. dropped feature count；
6. target column；
7. dropped invalid features；
8. dropped all-missing features；
9. dropped constant features；
10. dropped high-missing features；
11. feature group validation；
12. imputation 执行结果；
13. scaling 执行结果；
14. feature selection 执行结果；
15. model-ready artifact；
16. preprocessor artifact；
17. ready_for_model_search；
18. warnings/errors；
19. model-ready preview；
20. 完整 JSON。

---

## 19. MVP 验收标准

| 序号 | 验收标准                                        |
| -- | ------------------------------------------- |
| 1  | 能通过 task_id 获取最新 Feature Engineering Object |
| 2  | 能拒绝 Feature Engineering 未完成的任务              |
| 3  | 能读取 feature matrix parquet artifact         |
| 4  | 能识别并删除 `_pymatgen_composition` 等非法对象列       |
| 5  | 能删除全空特征                                     |
| 6  | 能删除常量特征                                     |
| 7  | 能删除高缺失率特征                                   |
| 8  | 能处理 inf / -inf                              |
| 9  | 能按 feature group 汇总有效特征数                    |
| 10 | 能整体剔除全无效 feature group                      |
| 11 | 能执行 median imputation                       |
| 12 | 能执行 standard scaling                        |
| 13 | 能执行 variance threshold 特征筛选                 |
| 14 | 能生成 model-ready feature matrix              |
| 15 | 能保存 model-ready artifact                    |
| 16 | 能保存 preprocessing pipeline artifact         |
| 17 | 能生成 model_search_input                      |
| 18 | 能正确设置 ready_for_model_search                |
| 19 | 能持久化 Feature Matrix Preprocessing Object    |
| 20 | 能查询某任务最新 Preprocessing 结果                   |
| 21 | 能 rerun 且不覆盖旧结果                             |
| 22 | 能返回 model-ready preview                     |
| 23 | 不训练模型                                       |
| 24 | 不执行 HPO                                     |
| 25 | 不生成 Pipeline 代码                             |

---

## 20. 示例流程

### 20.1 输入

Feature Engineering 输出：

```json
{
  "feature_matrix": {
    "file_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
    "n_features": 94,
    "target_column": "band_gap"
  },
  "feature_quality": {
    "invalid_features": ["_pymatgen_composition"],
    "all_missing_features": [
      "matminer_element_property__..."
    ],
    "constant_features": [
      "matminer_element_property__..."
    ]
  }
}
```

---

### 20.2 处理流程

```text
POST /api/feature-matrix-preprocessing/task_xxxxxxxx
    ↓
读取前五个模块结果
    ↓
加载 raw feature matrix artifact
    ↓
校验 target column
    ↓
删除非法 object 列
    ↓
删除全空列
    ↓
删除常量列
    ↓
删除高缺失率列
    ↓
按 feature group 汇总
    ↓
执行 imputation
    ↓
执行 scaling
    ↓
执行 variance threshold feature selection
    ↓
保存 model-ready matrix artifact
    ↓
保存 preprocessor.joblib
    ↓
输出 Feature Matrix Preprocessing Object
```

---

### 20.3 输出摘要

```json
{
  "status": "preprocessed_with_warning",
  "validation_summary": {
    "n_raw_features": 94,
    "n_valid_features_before_preprocessing": 14,
    "n_features_after_preprocessing": 14,
    "n_dropped_features": 80,
    "is_model_ready": true
  },
  "preprocessing_execution": {
    "imputation": {
      "executed": true,
      "strategy": "median"
    },
    "scaling": {
      "executed": true,
      "strategy": "standard_scaler"
    },
    "feature_selection": {
      "executed": true,
      "strategy": "variance_threshold"
    }
  },
  "model_search_input": {
    "ready_for_model_search": true
  }
}
```

---

## 21. 后续迭代方向

### 21.1 V2：更复杂的 Preprocessing Pipeline

支持：

1. RobustScaler；
2. MinMaxScaler；
3. KNNImputer；
4. IterativeImputer；
5. OneHotEncoder；
6. OrdinalEncoder；
7. PowerTransformer；
8. QuantileTransformer。

---

### 21.2 V3：多预处理版本

支持生成多个 model-ready dataset：

```text
strict_clean
balanced_clean
retain_more_features
low_missing_only
scaled_only
unscaled_tree_model_version
```

供模型搜索比较。

---

### 21.3 V4：与 Pipeline Generation 深度衔接

将 preprocessing pipeline artifact 编译进后续 pipeline specification，保证训练和推理阶段预处理逻辑一致。

---

## 22. 总结

Feature Matrix Validation & Preprocessing Execution 模块是 Feature Engineering 与 Automated Model and HPO Search 之间的建模数据准备层。

它的核心输入是：

```text
Feature Engineering Object
    +
Raw Feature Matrix Artifact
```

它的核心输出是：

```text
Feature Matrix Preprocessing Object
    +
Model-ready Feature Matrix Artifact
    +
Preprocessing Pipeline Artifact
    +
model_search_input
```

该模块最终应回答：

```text
当前特征矩阵能否建模？
哪些列被删除？
哪些缺失值被填补？
是否执行了缩放？
是否执行了特征筛选？
模型搜索阶段应该读取哪个干净 artifact？
```

它不应回答：

```text
应该训练哪个模型？
HPO 如何搜索？
模型效果是多少？
哪个模型最好？
Pipeline 代码如何生成？
```

一句话总结：

```text
本模块负责把 Feature Engineering 输出的 raw feature matrix 处理成真正可直接进入 Automated Model and HPO Search 的 model-ready dataset。
```




