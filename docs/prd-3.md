# PRD-3：Dataset Loading, Checking, and Profiling 模块需求文档

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

1. Task Specification 模块：负责用户任务输入、字段标准化、基础校验、任务对象持久化；
2. LLM-based Task Interpretation 模块：负责基于 LLM 理解任务语义，输出 `Task Interpretation Object`，包括 `dataset_intent`、`planning_hint`、`modeling_intent` 等信息。

本模块接收前两个模块的输出，重点完成：

```text
识别数据来源
    ↓
加载数据集
    ↓
检查数据可用性
    ↓
分析数据结构与质量
    ↓
生成 Dataset Profile Object
```

该模块为后续 Workflow Planning 提供数据层面的事实依据。

---

## 3. 模块目标

本模块的核心目标是：

1. 根据 `task_id` 获取已完成的 Task Specification 与 Task Interpretation；
2. 根据 `dataset_intent` 判断数据来源；
3. 加载用户指定的数据集；
4. 检查数据是否满足当前材料机器学习任务的基本要求；
5. 识别输入列、目标列、样本量、字段类型、缺失值、重复值、异常值等数据特征；
6. 生成统一的 `Dataset Profile Object`；
7. 为后续 Workflow Planning 模块提供可靠的数据画像；
8. 不在本模块中做特征工程、模型选择、Pipeline 规划或训练。

---

## 4. 系统边界

### 4.1 本模块负责的内容

本模块负责：

1. 读取 Task Specification Object；
2. 读取最新 Task Interpretation Object；
3. 根据 `dataset_intent` 识别数据来源；
4. 支持加载公开基准数据集；
5. 支持加载用户上传的表格数据；
6. 检查数据集是否存在；
7. 检查目标列是否存在；
8. 检查输入列是否存在；
9. 检查输入模态与数据内容是否一致；
10. 检查样本数量；
11. 检查缺失值；
12. 检查重复样本；
13. 检查目标变量分布；
14. 检查字段类型；
15. 生成数据集基本统计信息；
16. 生成数据质量问题列表；
17. 生成后续 Workflow Planning 可消费的 `dataset_profile`；
18. 持久化数据加载与分析结果。

---

### 4.2 本模块不负责的内容

本模块不负责：

1. 不负责收集用户任务输入；
2. 不负责解释用户任务语义；
3. 不负责调用 LLM 做任务理解；
4. 不负责决定特征工程策略；
5. 不负责生成材料描述符；
6. 不负责模型选择；
7. 不负责超参数搜索；
8. 不负责生成 Pipeline 代码；
9. 不负责模型训练；
10. 不负责模型评估；
11. 不负责结果诊断；
12. 不负责最终报告生成。

特别注意：

```text
本模块只回答“当前任务的数据是什么、是否能用、质量如何”；
不回答“应该用什么特征、什么模型、什么 Pipeline”。
```

---

## 5. 上游输入

### 5.1 输入来源一：Task Specification Object

来自 Task Specification 模块。

核心字段包括：

| 字段                  | 说明      |
| ------------------- | ------- |
| task_id             | 任务唯一 ID |
| task_name           | 任务名称    |
| task_description    | 任务描述    |
| material_system     | 材料体系    |
| prediction_target   | 原始预测目标  |
| task_type           | 任务类型    |
| dataset_description | 数据集描述   |
| input_type          | 输入类型    |
| target_column       | 目标列名    |
| evaluation_metric   | 评价指标    |
| status              | 任务规格状态  |

---

### 5.2 输入来源二：Task Interpretation Object

来自 LLM-based Task Interpretation 模块。

本模块重点使用以下字段：

| 字段                            | 说明           |
| ----------------------------- | ------------ |
| interpretation_id             | 任务理解结果 ID    |
| task_id                       | 关联任务 ID      |
| status                        | 任务理解状态       |
| interpreted_task_type         | LLM 理解后的任务类型 |
| interpreted_input_modality    | LLM 理解后的输入模态 |
| interpreted_prediction_target | 标准化预测目标      |
| dataset_intent                | 数据集意图        |
| planning_hint                 | 后续规划提示       |
| warnings                      | 任务理解警告       |
| ambiguities                   | 任务理解歧义       |

其中 `dataset_intent` 是本模块最关键的输入。

示例：

```json id="dataset_intent_example"
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

## 6. 前置条件

### 6.1 必须满足的条件

进入本模块前必须满足：

1. `task_id` 存在；
2. Task Specification 状态为 `valid` 或 `valid_with_warning`；
3. Task Interpretation 已存在；
4. Task Interpretation 状态为 `interpreted` 或 `interpreted_with_warning`；
5. `dataset_intent` 存在；
6. 数据来源信息足够支持加载尝试。

---

### 6.2 不允许进入本模块的情况

| 情况                                        | 处理方式                           |
| ----------------------------------------- | ------------------------------ |
| task_id 不存在                               | 返回 `TASK_NOT_FOUND`            |
| Task Specification 状态为 incomplete/invalid | 返回 `TASK_NOT_READY`            |
| Task Interpretation 不存在                   | 返回 `INTERPRETATION_REQUIRED`   |
| Task Interpretation 状态为 failed/blocked    | 返回 `INTERPRETATION_NOT_READY`  |
| dataset_intent 缺失                         | 返回 `DATASET_INTENT_MISSING`    |
| 数据来源无法识别                                  | 返回 `DATASET_SOURCE_UNRESOLVED` |

---

## 7. 输出对象

### 7.1 输出对象名称

```text
Dataset Profile Object
```

### 7.2 输出对象示例

```json id="dataset_profile_object_example"
{
  "dataset_profile_id": "profile_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "interpretation_id": "interp_xxxxxxxx",
  "status": "profiled",
  "dataset_source": {
    "source_type": "public_benchmark",
    "dataset_reference": "matbench_expt_gap",
    "loader": "matbench",
    "loaded_from": "matbench_expt_gap"
  },
  "dataset_schema": {
    "n_samples": 4604,
    "n_columns": 2,
    "columns": [
      {
        "name": "composition",
        "role": "input",
        "dtype": "string",
        "missing_count": 0,
        "missing_ratio": 0.0
      },
      {
        "name": "band_gap",
        "role": "target",
        "dtype": "float",
        "missing_count": 0,
        "missing_ratio": 0.0
      }
    ],
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
  },
  "created_at": "2026-05-01T10:00:00",
  "updated_at": "2026-05-01T10:00:00"
}
```

---

## 8. 核心功能需求

## 8.1 功能一：获取上游任务上下文

### 输入

```text
task_id
```

### 处理

1. 根据 `task_id` 查询 Task Specification；
2. 查询该任务最新的 Task Interpretation；
3. 检查两个对象状态是否允许进入数据加载；
4. 合并任务输入信息与任务理解信息；
5. 构建 Dataset Loading Context。

### 输出

```json id="dataset_loading_context"
{
  "task_id": "task_xxxxxxxx",
  "task_specification": {},
  "task_interpretation": {},
  "dataset_intent": {},
  "expected_input_modality": "composition",
  "expected_target_column": "band_gap",
  "expected_task_type": "regression"
}
```

---

## 8.2 功能二：识别数据来源

### 输入

```text
dataset_description
dataset_intent
dataset_loading_hint
```

### 处理

系统需要判断数据来源属于以下类型：

| source_type      | 说明       |
| ---------------- | -------- |
| public_benchmark | 公开基准数据集  |
| uploaded_file    | 用户上传文件   |
| database_table   | 系统内部数据库表 |
| external_url     | 外部 URL   |
| unknown          | 无法识别     |

MVP 阶段建议优先支持：

1. `public_benchmark`；
2. `uploaded_file`。

### 输出

```json id="dataset_source_resolution"
{
  "source_type": "public_benchmark",
  "dataset_reference": "matbench_expt_gap",
  "loader": "matbench",
  "is_supported": true,
  "messages": []
}
```

---

## 8.3 功能三：加载公开基准数据集

### 输入

```text
source_type = public_benchmark
dataset_reference
possible_loader
```

### 处理

MVP 阶段建议支持 Matbench 数据集名称识别，例如：

1. `matbench_expt_gap`
2. `matbench_mp_e_form`
3. `matbench_log_gvrh`
4. `matbench_log_kvrh`

加载时只负责得到原始数据表或统一 DataFrame，不进行特征工程。

### 输出

```json id="public_dataset_loading_result"
{
  "is_loaded": true,
  "loader": "matbench",
  "dataset_reference": "matbench_expt_gap",
  "raw_data_shape": {
    "n_rows": 4604,
    "n_columns": 2
  },
  "load_messages": []
}
```

---

## 8.4 功能四：加载用户上传表格数据

### 输入

```text
source_type = uploaded_file
file_id / file_path
expected_target_column
expected_input_columns
```

### 支持格式

MVP 阶段建议支持：

| 格式    | 说明   |
| ----- | ---- |
| CSV   | 优先支持 |
| Excel | 可选支持 |
| JSONL | 后续支持 |

### 处理

1. 根据文件 ID 查找上传文件；
2. 判断文件格式；
3. 尝试读取为 DataFrame；
4. 检查文件是否为空；
5. 检查表头是否存在；
6. 返回统一数据对象。

### 输出

```json id="uploaded_dataset_loading_result"
{
  "is_loaded": true,
  "source_type": "uploaded_file",
  "file_name": "bandgap_dataset.csv",
  "raw_data_shape": {
    "n_rows": 1200,
    "n_columns": 8
  },
  "load_messages": []
}
```

---

## 8.5 功能五：字段与 Schema 检查

### 输入

```text
raw_dataframe
expected_input_columns
expected_target_column
expected_input_modality
```

### 处理

检查内容包括：

1. 目标列是否存在；
2. 输入列是否存在；
3. 表格是否为空；
4. 是否存在重复列名；
5. 字段类型是否合理；
6. 目标列是否可用于当前任务类型；
7. 输入列是否符合 expected_input_modality。

### 输出

```json id="schema_check_result"
{
  "target_column_exists": true,
  "input_columns_exist": true,
  "duplicate_columns": [],
  "schema_errors": [],
  "schema_warnings": []
}
```

---

## 8.6 功能六：输入模态一致性检查

### 输入

```text
expected_input_modality
input_columns
raw_dataframe
```

### 处理

根据不同输入模态执行基础检查：

### composition

检查：

1. 是否存在 composition/formula 相关列；
2. 样本是否像化学式；
3. 是否存在明显非法化学式；
4. 是否为空字符串。

### structure

检查：

1. 是否存在 structure/cif/poscar 相关列；
2. 是否包含结构文件路径或结构字符串；
3. 是否需要外部结构文件；
4. 是否缺少结构数据。

### descriptor

检查：

1. 是否存在数值型描述符列；
2. 描述符列数量是否足够；
3. 是否存在大量非数值字段。

### 输出

```json id="modality_check_result"
{
  "expected_input_modality": "composition",
  "detected_input_modality": "composition",
  "is_consistent": true,
  "invalid_sample_count": 0,
  "messages": []
}
```

---

## 8.7 功能七：数据质量检查

### 输入

```text
raw_dataframe
input_columns
target_column
```

### 处理

检查内容包括：

1. 缺失值数量与比例；
2. 重复行数量；
3. 重复输入样本数量；
4. 目标列缺失；
5. 输入列缺失；
6. 非法值；
7. 空字符串；
8. 常量列；
9. 高缺失率列；
10. 样本量是否过小。

### 输出

```json id="data_quality_result"
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

## 8.8 功能八：目标变量画像

### 输入

```text
target_column
task_type
raw_dataframe
```

### 处理

根据任务类型执行不同分析。

### regression

统计：

1. min；
2. max；
3. mean；
4. median；
5. std；
6. skewness；
7. outlier_count；
8. missing_ratio。

### classification

统计：

1. 类别数量；
2. 各类别样本数；
3. 类别占比；
4. 是否类别不平衡；
5. 缺失比例。

### ranking

统计：

1. ranking label 分布；
2. group 信息是否存在；
3. 排序标签是否合理。

### 输出

```json id="target_profile_result"
{
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
}
```

---

## 8.9 功能九：样本规模判断

### 输入

```text
n_samples
task_type
input_modality
```

### 处理

根据样本量判断数据规模：

| sample_size_level | 建议标准        |
| ----------------- | ----------- |
| very_small        | < 100       |
| small             | 100 - 999   |
| medium            | 1000 - 9999 |
| large             | >= 10000    |

该判断只作为数据画像，不负责决定模型。

### 输出

```json id="sample_size_level_result"
{
  "n_samples": 4604,
  "sample_size_level": "medium"
}
```

---

## 8.10 功能十：生成 Dataset Profile Object

### 输入

```text
loading_result
schema_check_result
modality_check_result
data_quality_result
target_profile_result
```

### 处理

1. 汇总所有检查结果；
2. 判断数据是否成功加载；
3. 判断数据是否可用于机器学习；
4. 汇总 warnings；
5. 汇总 errors；
6. 构建 `Dataset Profile Object`；
7. 生成 `workflow_planning_input`；
8. 持久化结果。

### 输出

```text
Dataset Profile Object
```

---

## 9. 状态设计

### 9.1 状态枚举

| 状态                    | 含义                     |
| --------------------- | ---------------------- |
| pending               | 已创建 profiling 任务，但尚未执行 |
| loading               | 正在加载数据                 |
| loaded                | 数据加载成功，但尚未完成检查         |
| checking              | 正在进行 schema 与质量检查      |
| profiled              | 数据加载、检查、画像完成           |
| profiled_with_warning | 完成画像，但存在非阻断性问题         |
| failed                | 数据加载或画像失败              |
| blocked               | 上游状态不满足要求              |

---

### 9.2 状态流转

```text
收到 profiling 请求
    ↓
检查上游 Task Specification 与 Task Interpretation
    ├── 不满足条件 → blocked
    └── 满足条件
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

---

## 10. API 需求

## 10.1 创建数据加载与画像结果

```text
POST /api/dataset-profiles/{task_id}
```

### 功能

根据 task_id 获取任务规格与任务理解结果，加载数据集并生成数据画像。

### 请求参数

| 参数      | 位置   | 必填 | 说明    |
| ------- | ---- | -- | ----- |
| task_id | path | 是  | 任务 ID |

### 请求体

MVP 阶段可为空。

后续可扩展：

```json id="create_dataset_profile_request"
{
  "force_rerun": false,
  "uploaded_file_id": "file_xxxxxxxx",
  "max_preview_rows": 20
}
```

### 响应

```json id="create_dataset_profile_response"
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

## 10.2 查询数据画像结果

```text
GET /api/dataset-profiles/{dataset_profile_id}
```

### 功能

根据 dataset_profile_id 查询完整 Dataset Profile Object。

---

## 10.3 查询某个任务的最新数据画像

```text
GET /api/tasks/{task_id}/dataset-profile
```

### 功能

返回某个 task_id 最新的一条 Dataset Profile Object。

---

## 10.4 重新执行数据加载与画像

```text
POST /api/dataset-profiles/{task_id}/rerun
```

### 功能

重新执行数据加载、检查与画像。

### 处理原则

1. 不覆盖旧结果；
2. 新增一条 Dataset Profile 记录；
3. 默认查询最新一条；
4. 保留历史记录，便于追踪数据变化。

---

## 10.5 数据预览接口

```text
GET /api/dataset-profiles/{dataset_profile_id}/preview
```

### 功能

返回数据集前 N 行预览。

### 注意

1. 默认返回前 20 行；
2. 不返回完整大数据集；
3. 对超大字段进行截断；
4. 不做特征工程。

---

## 11. 数据库设计

## 11.1 表名

```text
dataset_profile
```

---

## 11.2 字段设计

| 字段                | 类型          | 说明                        |
| ----------------- | ----------- | ------------------------- |
| id                | VARCHAR     | 主键，格式 `profile_xxxxxxxx`  |
| task_id           | VARCHAR     | 关联 task_specification.id  |
| interpretation_id | VARCHAR     | 关联 task_interpretation.id |
| status            | VARCHAR     | 数据画像状态                    |
| source_type       | VARCHAR     | 数据来源类型                    |
| dataset_reference | VARCHAR     | 数据集名称或文件引用                |
| n_samples         | INTEGER     | 样本数                       |
| n_columns         | INTEGER     | 字段数                       |
| input_modality    | VARCHAR     | 输入模态                      |
| target_column     | VARCHAR     | 目标列                       |
| quality_level     | VARCHAR     | 数据质量等级                    |
| is_usable_for_ml  | BOOLEAN     | 是否可用于机器学习                 |
| profile_json      | JSONB       | 完整 Dataset Profile Object |
| preview_json      | JSONB       | 数据预览数据                    |
| error_message     | TEXT        | 错误信息                      |
| created_at        | TIMESTAMPTZ | 创建时间                      |
| updated_at        | TIMESTAMPTZ | 更新时间                      |

---

## 11.3 索引设计

| 索引                              | 说明           |
| ------------------------------- | ------------ |
| PRIMARY KEY(id)                 | 主键索引         |
| INDEX(task_id)                  | 根据任务查询画像     |
| INDEX(interpretation_id)        | 根据任务理解结果查询画像 |
| INDEX(status)                   | 按状态筛选        |
| INDEX(source_type)              | 按数据来源筛选      |
| INDEX(created_at)               | 查询最新画像       |
| INDEX(task_id, created_at DESC) | 查询任务最新画像     |

---

## 11.4 存储原则

继续采用现有系统的混合存储策略：

```text
高频查询字段单独建列
+
复杂结构化画像结果存入 JSONB
```

高频字段包括：

1. task_id；
2. interpretation_id；
3. status；
4. source_type；
5. dataset_reference；
6. n_samples；
7. input_modality；
8. target_column；
9. quality_level；
10. is_usable_for_ml。

---

## 12. 后端模块结构建议

新增模块目录：

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
├── loaders/
│   ├── __init__.py
│   ├── base_loader.py
│   ├── matbench_loader.py
│   └── file_loader.py
├── checkers/
│   ├── __init__.py
│   ├── schema_checker.py
│   ├── modality_checker.py
│   ├── quality_checker.py
│   └── target_checker.py
├── profiler.py
├── builder.py
├── enums.py
└── exceptions.py
```

---

## 12.1 文件职责

| 文件                           | 职责                                                                       |
| ---------------------------- | ------------------------------------------------------------------------ |
| api.py                       | 定义数据画像相关 HTTP 接口                                                         |
| schemas.py                   | 定义请求、响应、内部 DTO                                                           |
| service.py                   | 编排完整数据加载、检查、画像流程                                                         |
| model.py                     | 定义 dataset_profile 数据库表                                                  |
| repository.py                | 提供 Dataset Profile CRUD                                                  |
| context_builder.py           | 读取上游 Task Specification 与 Task Interpretation，构建 Dataset Loading Context |
| source_resolver.py           | 根据 dataset_intent 判断数据来源                                                 |
| loaders/base_loader.py       | 定义数据加载器统一接口                                                              |
| loaders/matbench_loader.py   | 加载 Matbench 公开基准数据集                                                      |
| loaders/file_loader.py       | 加载用户上传 CSV/Excel 数据                                                      |
| checkers/schema_checker.py   | 检查目标列、输入列、字段类型                                                           |
| checkers/modality_checker.py | 检查输入模态一致性                                                                |
| checkers/quality_checker.py  | 检查缺失值、重复值、非法值等                                                           |
| checkers/target_checker.py   | 分析目标变量分布                                                                 |
| profiler.py                  | 汇总数据统计与画像结果                                                              |
| builder.py                   | 构建 Dataset Profile Object                                                |
| enums.py                     | 定义模块状态、数据来源、质量等级等枚举                                                      |
| exceptions.py                | 定义模块专用异常                                                                 |

---

## 13. 与已实现模块的衔接

## 13.1 与 Task Specification 模块的关系

Task Specification 模块负责：

1. 收集用户输入；
2. 标准化字段；
3. 校验任务基本合法性；
4. 生成 Task Specification Object。

Dataset Profile 模块只读取该对象，不修改其内容。

本模块主要消费：

```text
task_id
dataset_description
input_type
target_column
task_type
evaluation_metric
status
```

---

## 13.2 与 LLM-based Task Interpretation 模块的关系

Task Interpretation 模块负责：

1. 理解任务语义；
2. 生成 `dataset_intent`；
3. 生成 `planning_hint`；
4. 识别任务歧义和警告。

Dataset Profile 模块主要消费：

```text
interpretation_id
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

---

## 13.3 与 Workflow Planning 模块的关系

Workflow Planning 模块后续应消费本模块输出的：

```text
Dataset Profile Object
workflow_planning_input
```

但本模块不做 Workflow Planning。

本模块只提供数据事实，例如：

1. 数据量大小；
2. 数据列结构；
3. 输入模态；
4. 目标列分布；
5. 缺失值情况；
6. 重复值情况；
7. 是否需要清洗；
8. 是否可用于建模。

Workflow Planning 模块再基于这些事实决定：

1. 是否需要清洗；
2. 是否需要特征工程；
3. 选择什么验证方式；
4. 选择什么模型；
5. 是否需要目标变换；
6. 是否需要特殊处理小样本问题。

---

## 14. 错误处理

### 14.1 错误码设计

| 错误码                        | 场景                       |
| -------------------------- | ------------------------ |
| TASK_NOT_FOUND             | task_id 不存在              |
| TASK_NOT_READY             | Task Specification 状态不允许 |
| INTERPRETATION_REQUIRED    | 尚未执行任务理解                 |
| INTERPRETATION_NOT_READY   | 任务理解状态不允许                |
| DATASET_INTENT_MISSING     | dataset_intent 缺失        |
| DATASET_SOURCE_UNRESOLVED  | 无法识别数据来源                 |
| DATASET_SOURCE_UNSUPPORTED | 当前不支持该数据来源               |
| DATASET_LOAD_FAILED        | 数据集加载失败                  |
| DATASET_EMPTY              | 数据为空                     |
| TARGET_COLUMN_MISSING      | 目标列不存在                   |
| INPUT_COLUMN_MISSING       | 输入列不存在                   |
| MODALITY_MISMATCH          | 输入模态不匹配                  |
| PROFILE_VALIDATION_FAILED  | 数据画像结果校验失败               |

---

### 14.2 非阻断性警告

以下问题不一定阻断流程，但应进入 warnings：

1. evaluation_metric 未指定；
2. 样本量较小；
3. 存在少量缺失值；
4. 存在重复样本；
5. 目标变量分布偏斜；
6. regression target 存在异常值；
7. classification label 不均衡；
8. 输入列名称与预期列名不完全一致，但可自动推断；
9. 数据集描述与实际加载结果存在轻微差异。

---

## 15. 前端需求

## 15.1 前端模块目录建议

```text
frontend/src/modules/datasetProfile/
├── components/
│   ├── DatasetProfilePanel.tsx
│   ├── DatasetSchemaCard.tsx
│   ├── DataQualityCard.tsx
│   ├── TargetProfileCard.tsx
│   ├── DatasetWarningList.tsx
│   └── DatasetPreviewTable.tsx
├── types.ts
└── constants.ts
```

---

## 15.2 前端 API 客户端

新增：

```text
frontend/src/api/datasetProfileApi.ts
```

封装接口：

```text
createDatasetProfile(taskId)
getDatasetProfile(profileId)
getLatestDatasetProfileByTaskId(taskId)
rerunDatasetProfile(taskId)
getDatasetPreview(profileId)
```

---

## 15.3 前端展示内容

MVP 阶段展示：

1. profile 状态；
2. 数据来源；
3. 样本数；
4. 字段数；
5. 输入列；
6. 目标列；
7. 输入模态一致性；
8. 目标变量画像；
9. 缺失值统计；
10. 重复值统计；
11. warnings；
12. errors；
13. 数据预览表格；
14. 是否 ready for workflow planning。

---

## 16. MVP 验收标准

| 序号 | 验收标准                                        |
| -- | ------------------------------------------- |
| 1  | 能通过 task_id 获取 Task Specification           |
| 2  | 能通过 task_id 获取最新 Task Interpretation        |
| 3  | 能拒绝未完成 Task Interpretation 的任务              |
| 4  | 能读取 Task Interpretation 中的 dataset_intent   |
| 5  | 能识别 public_benchmark / uploaded_file 两类数据来源 |
| 6  | 能加载至少一个 Matbench 风格公开数据集                    |
| 7  | 能加载 CSV 用户上传数据                              |
| 8  | 能识别目标列是否存在                                  |
| 9  | 能识别输入列是否存在                                  |
| 10 | 能检查输入模态是否一致                                 |
| 11 | 能统计样本数和字段数                                  |
| 12 | 能统计缺失值                                      |
| 13 | 能统计重复值                                      |
| 14 | 能生成 regression target 基础统计                  |
| 15 | 能生成 classification label 分布                 |
| 16 | 能输出 Dataset Profile Object                  |
| 17 | 能持久化 Dataset Profile Object                 |
| 18 | 能查询某任务最新 Dataset Profile                    |
| 19 | 能重新执行 profiling 且不覆盖旧结果                     |
| 20 | 不生成特征工程方案                                   |
| 21 | 不选择模型                                       |
| 22 | 不生成 Pipeline                                |
| 23 | 不执行训练                                       |

---

## 17. 示例流程

### 17.1 输入

用户已经完成：

1. Task Specification；
2. Task Interpretation。

Task Interpretation 中包含：

```json id="example_input_interpretation"
{
  "task_id": "task_a1b2c3d4",
  "interpretation_id": "interp_12345678",
  "interpreted_task_type": "regression",
  "interpreted_input_modality": "composition",
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
  }
}
```

---

### 17.2 处理流程

```text
POST /api/dataset-profiles/task_a1b2c3d4
    ↓
读取 Task Specification
    ↓
读取最新 Task Interpretation
    ↓
提取 dataset_intent
    ↓
识别数据来源为 public_benchmark
    ↓
调用 Matbench Loader 加载 matbench_expt_gap
    ↓
检查 composition 列
    ↓
检查 band_gap 目标列
    ↓
分析缺失值、重复值、样本量、目标分布
    ↓
生成 Dataset Profile Object
    ↓
写入 dataset_profile 表
    ↓
返回前端展示
```

---

### 17.3 输出

```json id="example_dataset_profile_output"
{
  "dataset_profile_id": "profile_xxxxxxxx",
  "task_id": "task_a1b2c3d4",
  "interpretation_id": "interp_12345678",
  "status": "profiled",
  "dataset_source": {
    "source_type": "public_benchmark",
    "dataset_reference": "matbench_expt_gap",
    "loader": "matbench"
  },
  "dataset_schema": {
    "n_samples": 4604,
    "n_columns": 2,
    "input_columns": ["composition"],
    "target_column": "band_gap"
  },
  "modality_check": {
    "expected_input_modality": "composition",
    "detected_input_modality": "composition",
    "is_consistent": true
  },
  "target_profile": {
    "target_column": "band_gap",
    "task_type": "regression",
    "dtype": "float",
    "min": 0.0,
    "max": 11.7,
    "mean": 1.82,
    "std": 1.65
  },
  "data_quality": {
    "missing_values": {
      "total_missing": 0
    },
    "duplicates": {
      "duplicate_rows": 0,
      "duplicate_input_samples": 3
    },
    "warnings": []
  },
  "profiling_summary": {
    "is_loadable": true,
    "is_usable_for_ml": true,
    "sample_size_level": "medium",
    "quality_level": "good",
    "recommended_next_step": "ready_for_workflow_planning"
  }
}
```

---

## 18. 后续迭代方向

MVP 后可扩展：

1. 支持更多公开材料数据集；
2. 支持 Materials Project API；
3. 支持 OQMD 数据加载；
4. 支持 JARVIS 数据加载；
5. 支持结构文件批量上传；
6. 支持 CIF/POSCAR 解析；
7. 支持 pymatgen 结构合法性检查；
8. 支持材料成分合法性检查；
9. 支持数据预览分页；
10. 支持 profiling 结果可视化；
11. 支持数据版本管理；
12. 支持数据缓存；
13. 支持异步任务队列；
14. 支持数据清洗建议生成；
15. 支持与 Workflow Planning 的自动触发衔接。

---

## 19. 总结

Dataset Loading, Checking, and Profiling 模块是连接“任务理解”和“工作流规划”的数据事实层。

它的核心职责不是理解用户要做什么，也不是规划机器学习方案，而是回答：

```text
这个任务对应的数据能否被加载？
数据结构是什么？
输入列和目标列是否存在？
数据质量如何？
是否具备进入 Workflow Planning 的基本条件？
```

最终，该模块应输出标准化、可持久化、可查询的 `Dataset Profile Object`，为后续 Workflow Planning 提供可靠的数据依据。

```
```
