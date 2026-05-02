# PRD：Automated Feature Engineering 外部特征库扩展需求文档

## 1. 需求名称

Automated Feature Engineering Enhancement with External Libraries  
基于外部材料特征库的自动化特征工程能力扩展

---

## 2. 背景说明

MLAgent 当前已完成前五个核心模块：

```text
Task Specification
    ↓
LLM-based Task Interpretation
    ↓
Dataset Loading, Checking, and Profiling
    ↓
Workflow Planning
    ↓
Feature Engineering
````

当前 Feature Engineering 模块已经完成 MVP，能够基于上游四个模块输出，自动执行特征工程并生成 Feature Engineering Object 与 feature matrix artifact。当前流程包括：构建上游上下文、重新加载原始数据、解析特征策略、执行 featurizer、构建特征矩阵、检查特征质量、保存 parquet artifact，并持久化结果。

当前已实现的 Featurizer Registry 提供统一注册、查询和校验能力，已注册的 featurizer 包括：

| featurizer_id          | 当前状态      | 说明                          |
| ---------------------- | --------- | --------------------------- |
| basic_composition      | available | 基础 composition 16 维描述符      |
| descriptor_passthrough | available | 已有数值描述符直通                   |
| structure_placeholder  | planned   | 结构特征占位，MVP 不可用              |
| matminer_magpie        | planned   | Matminer Magpie 描述符，MVP 不可用 |

当前系统的问题是：`basic_composition` 特征维度和材料表达能力有限，难以充分支撑更复杂的材料性质预测任务。因此，本次需求允许引入外部材料科学特征库，重点扩展 composition-based 与 structure-based 特征能力。

---

## 3. 需求目标

本次扩展目标是将 Feature Engineering 从 MVP 的轻量特征能力，升级为支持外部材料特征库的可扩展特征工程子系统。

核心目标包括：

1. 引入 `pymatgen` 作为材料成分与结构解析基础库；
2. 引入 `matminer` 作为标准材料描述符生成库；
3. 支持 Magpie / ElementProperty / Stoichiometry / ValenceOrbital 等 composition featurizers；
4. 支持基础 structure featurizers；
5. 支持多 featurizer 组合执行；
6. 扩展 Featurizer Registry，使其能描述依赖库、依赖状态、featurizer 可用性和 fallback；
7. 保持与 Workflow Planning 的 feature_strategy 自然衔接；
8. 保持与 Feature Engineering 现有 API、数据库结构和 artifact 输出兼容；
9. 为后续 Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis 和 Report Generation 提供更高质量的 feature matrix；
10. 明确错误处理、依赖缺失处理、fallback 和特征质量检查规则。

---

## 4. 模块定位

本需求属于 **Feature Engineering 模块增强**，不是新增第六个业务模块。

它位于：

```text
Workflow Planning
    ↓
Enhanced Feature Engineering
    ↓
Pipeline Generation
```

本次扩展主要影响：

```text
backend/app/modules/feature_engineering/
    ├── featurizers/
    ├── strategy_resolver.py
    ├── feature_matrix_builder.py
    ├── artifact_manager.py
    ├── builder.py
    └── checkers/feature_quality_checker.py

backend/app/shared/registry/
    └── featurizer_registry.py

backend/app/shared/config/
    └── settings.py

backend/requirements.txt
```

---

## 5. 系统边界

### 5.1 本次扩展负责的内容

本次扩展负责：

1. 引入外部库依赖；
2. 扩展 Featurizer Registry；
3. 新增 matminer composition featurizers；
4. 新增 pymatgen composition parsing；
5. 新增 structure featurizer 基础能力；
6. 支持多个 featurizer 组合执行；
7. 支持 featurizer 级别执行记录；
8. 支持依赖缺失检测；
9. 支持外部库执行失败时 fallback；
10. 支持 feature group 元数据；
11. 支持特征命名规范；
12. 支持高维特征质量检查；
13. 支持生成更完整的 downstream_input；
14. 支持前端展示扩展后的特征工程结果。

---

### 5.2 本次扩展不负责的内容

本次扩展不负责：

1. 不重新设计 Task Specification；
2. 不重新设计 Task Interpretation；
3. 不重新设计 Dataset Profile 主流程；
4. 不重新设计 Workflow Planning 主流程；
5. 不训练模型；
6. 不做 HPO；
7. 不计算模型评估指标；
8. 不生成 Pipeline 代码；
9. 不执行 Pipeline；
10. 不做模型结果诊断；
11. 不生成最终报告；
12. 不实现完整异步任务系统；
13. 不实现用户权限、计费、配额等生产级功能。

特别注意：

```text
本需求只扩展“原始材料输入 → 特征矩阵”的能力；
不进入“特征矩阵 → 模型训练 → 模型评价”的阶段。
```

---

## 6. 外部库引入范围

### 6.1 必须引入

| 依赖       | 用途                         | 优先级 |
| -------- | -------------------------- | --- |
| pymatgen | Composition / Structure 解析 | P0  |
| matminer | 标准材料特征工程                   | P0  |

---

### 6.2 建议引入

| 依赖           | 用途                                         | 优先级 |
| ------------ | ------------------------------------------ | --- |
| scikit-learn | 后续 imputation、scaling、feature selection 预留 | P1  |
| pyarrow      | parquet artifact 存储                        | P1  |
| joblib       | 后续保存 transformer / pipeline artifact       | P2  |

---

### 6.3 依赖引入原则

1. 外部库应写入 `requirements.txt`；
2. 若依赖安装失败，系统应给出明确错误；
3. Featurizer Registry 应能识别依赖是否可用；
4. 依赖缺失不应导致整个 Feature Engineering 模块不可用；
5. 当 matminer 不可用时，应 fallback 到 `basic_composition`；
6. 当 pymatgen 不可用时，matminer-based featurizer 应不可用；
7. 外部库版本信息应记录到 Feature Engineering Object 的 metadata 中。

---

## 7. 当前能力与目标能力对比

### 7.1 当前能力

| 能力                      | 状态      | 说明                             |
| ----------------------- | ------- | ------------------------------ |
| basic_composition       | 已实现     | 16 维轻量 composition descriptors |
| descriptor_passthrough  | 已实现     | 数值描述符直通                        |
| structure_placeholder   | 占位      | 不可执行                           |
| matminer_magpie         | planned | 已注册但不可执行                       |
| Feature Matrix Artifact | 已实现     | parquet 存储                     |
| Featurizer Registry     | 已实现     | 静态注册表                          |

---

### 7.2 扩展后目标能力

| featurizer_id               | 依赖                  | 目标状态               | 说明                          |
| --------------------------- | ------------------- | ------------------ | --------------------------- |
| basic_composition           | 无                   | available          | 保留，作为 fallback              |
| pymatgen_composition_parser | pymatgen            | available          | 标准化解析 composition           |
| matminer_stoichiometry      | pymatgen + matminer | available          | 化学计量特征                      |
| matminer_element_property   | pymatgen + matminer | available          | 元素属性统计特征                    |
| matminer_magpie             | pymatgen + matminer | available          | Magpie 预设特征                 |
| matminer_valence_orbital    | pymatgen + matminer | available          | 价电子轨道特征                     |
| descriptor_passthrough      | 无                   | available          | 保留                          |
| descriptor_cleaner          | pandas/numpy        | available          | descriptor 清理增强             |
| pymatgen_structure_parser   | pymatgen            | optional           | 结构解析                        |
| matminer_structure_basic    | pymatgen + matminer | optional/planned   | 基础结构特征                      |
| structure_placeholder       | 无                   | deprecated/planned | 被真实 structure featurizer 替代 |

---

## 8. 用户故事

### 8.1 材料机器学习用户

作为材料机器学习用户，我希望系统能够自动调用标准材料特征库生成 Magpie、ElementProperty、Stoichiometry 等描述符，而不是只生成基础 16 维特征。

### 8.2 系统开发者

作为系统开发者，我希望新增 featurizer 时只需在 Registry 注册并实现对应 Featurizer 类，而不需要修改 Workflow Planning、Feature Engineering 的主流程。

### 8.3 Workflow Planning 模块

作为 Workflow Planning 模块，我希望能够从 Registry 获取当前真实可用的 featurizer 列表，并让 LLM 只选择 available featurizer。

### 8.4 Pipeline Generation 模块

作为后续 Pipeline Generation 模块，我希望 Feature Engineering 输出稳定的 feature artifact、feature columns、feature groups 和 preprocessing requirements，便于生成训练 pipeline。

### 8.5 Result Diagnosis 模块

作为后续诊断模块，我希望知道哪些 feature group 被使用、哪些失败、哪些 fallback，以便判断模型效果差是否与特征表达不足有关。

---

## 9. 输入数据

### 9.1 输入来源一：Workflow Plan Object

重点消费：

```json
{
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "executable_featurizers": [
      "matminer_stoichiometry",
      "matminer_element_property",
      "matminer_magpie"
    ],
    "semantic_featurizers": [
      "stoichiometric descriptors",
      "element property statistics",
      "Magpie descriptors"
    ],
    "unsupported_future_featurizers": [],
    "feature_scaling_required": true,
    "feature_selection_required": true
  }
}
```

---

### 9.2 输入来源二：Dataset Profile Object

重点消费：

```json
{
  "dataset_schema": {
    "input_columns": ["composition"],
    "target_column": "band_gap"
  },
  "workflow_planning_input": {
    "input_modality": "composition",
    "task_type": "regression",
    "target_column": "band_gap",
    "is_usable_for_ml": true
  }
}
```

Dataset Profile 已经负责数据加载、schema 检查、模态检查、质量检查和目标变量画像；Feature Engineering 只复用数据源信息重新加载原始数据，不重新做完整 dataset profiling。当前系统明确采用前置模块状态检查和依赖链路，Feature Engineering 依赖 Task、Interpretation、Profile、Plan 四个上游对象。

---

### 9.3 输入来源三：原始数据

支持输入类型：

| input_modality | 数据形式                                              | 本次扩展目标 |
| -------------- | ------------------------------------------------- | ------ |
| composition    | 化学式字符串                                            | P0 支持  |
| descriptor     | 已有数值描述符表                                          | P0 支持  |
| structure      | CIF / POSCAR / structure 对象 / structure 字符串       | P1 支持  |
| mixed          | composition + descriptor / structure + descriptor | P2 预留  |

---

## 10. 输出数据

### 10.1 输出对象名称

```text
Enhanced Feature Engineering Object
```

---

### 10.2 输出对象示例

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
      "matminer_stoichiometry",
      "matminer_element_property",
      "matminer_magpie"
    ],
    "executed_featurizers": [
      {
        "id": "matminer_stoichiometry",
        "display_name": "Matminer Stoichiometry Features",
        "status": "success",
        "n_features_generated": 8,
        "failed_sample_count": 0,
        "execution_time_ms": 180,
        "dependency_versions": {
          "pymatgen": "x.x.x",
          "matminer": "x.x.x"
        }
      },
      {
        "id": "matminer_element_property",
        "display_name": "Matminer ElementProperty Features",
        "status": "success",
        "n_features_generated": 132,
        "failed_sample_count": 0,
        "execution_time_ms": 820,
        "dependency_versions": {
          "pymatgen": "x.x.x",
          "matminer": "x.x.x"
        }
      }
    ],
    "fallback_featurizers": [],
    "skipped_featurizers": [],
    "unsupported_featurizers": []
  },
  "feature_matrix": {
    "artifact_id": "artifact_xxxxxxxx",
    "storage_type": "parquet",
    "file_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
    "n_samples": 4604,
    "n_features": 140,
    "target_column": "band_gap",
    "index_column": "sample_id"
  },
  "feature_schema": {
    "feature_columns": [],
    "feature_groups": [
      {
        "group_name": "matminer_stoichiometry",
        "n_features": 8
      },
      {
        "group_name": "matminer_element_property",
        "n_features": 132
      }
    ],
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
    "failed_samples": [],
    "constant_features": [],
    "all_missing_features": [],
    "is_valid_feature_matrix": true,
    "warnings": [],
    "errors": []
  },
  "preprocessing_requirements": {
    "scaling_required": true,
    "imputation_required": false,
    "feature_selection_required": true
  },
  "downstream_input": {
    "feature_matrix_artifact_id": "artifact_xxxxxxxx",
    "feature_matrix_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
    "target_column": "band_gap",
    "feature_columns": [],
    "feature_groups": [],
    "task_type": "regression",
    "primary_metric": "MAE",
    "ready_for_pipeline_generation": true
  },
  "warnings": [],
  "errors": []
}
```

---

## 11. 核心功能需求

## 11.1 功能一：引入 pymatgen Composition 解析

### 目标

使用 `pymatgen.core.Composition` 作为 composition 解析基础能力，替代或补充当前手写化学式解析逻辑。

### 输入

```text
composition column
```

### 处理

1. 读取 composition 字符串；
2. 使用 pymatgen 解析为 Composition；
3. 标准化非法或异常化学式；
4. 记录解析失败样本；
5. 为 matminer featurizer 提供标准输入；
6. 当 pymatgen 解析失败比例超过阈值时阻断。

### 输出

```json
{
  "parsed_compositions": "internal_object_reference",
  "failed_samples": [],
  "failed_sample_count": 0
}
```

---

## 11.2 功能二：新增 Matminer Stoichiometry Featurizer

### featurizer_id

```text
matminer_stoichiometry
```

### 依赖

```text
pymatgen
matminer
```

### 目标

生成标准化学计量特征。

### 处理

1. 接收 pymatgen Composition；
2. 调用 matminer Stoichiometry 类 featurizer；
3. 生成化学计量相关特征；
4. 统一添加特征名前缀；
5. 记录 feature group。

### 输出

```json
{
  "group_name": "matminer_stoichiometry",
  "n_features": 8,
  "status": "success"
}
```

---

## 11.3 功能三：新增 Matminer ElementProperty Featurizer

### featurizer_id

```text
matminer_element_property
```

### 依赖

```text
pymatgen
matminer
```

### 目标

生成元素属性统计特征，例如 Magpie preset 下的平均值、极差、最大值、最小值等。

### 处理

1. 接收 pymatgen Composition；
2. 调用 matminer ElementProperty；
3. 默认使用 Magpie preset；
4. 生成元素属性统计特征；
5. 统一添加前缀；
6. 记录每列名称和失败样本。

### 输出

```json
{
  "group_name": "matminer_element_property",
  "n_features": 132,
  "status": "success"
}
```

---

## 11.4 功能四：升级 Matminer Magpie Featurizer

### 当前状态

`matminer_magpie` 已在 Registry 中注册，但当前状态为 planned，不可执行。

### 扩展目标

将其升级为 available，前提是依赖检测通过。

### 处理

1. 检查 pymatgen 是否可用；
2. 检查 matminer 是否可用；
3. 如果可用，将 Registry 中 `matminer_magpie.status` 标记为 available；
4. 如果不可用，保持 unavailable/planned；
5. Workflow Planning Prompt 只注入 available 状态 featurizer。

---

## 11.5 功能五：新增 Matminer ValenceOrbital Featurizer

### featurizer_id

```text
matminer_valence_orbital
```

### 目标

生成价电子轨道相关 composition 特征。

### 输入

pymatgen Composition。

### 输出

```json
{
  "group_name": "matminer_valence_orbital",
  "n_features": 4,
  "status": "success"
}
```

---

## 11.6 功能六：支持多 featurizer 组合执行

### 输入

```json
{
  "executable_featurizers": [
    "basic_composition",
    "matminer_stoichiometry",
    "matminer_element_property",
    "matminer_valence_orbital"
  ]
}
```

### 处理

1. 按 Workflow Plan 给出的顺序执行；
2. 每个 featurizer 独立生成 feature dataframe；
3. 每个 featurizer 独立记录执行状态；
4. 将所有 feature group 按列合并；
5. 自动处理特征名冲突；
6. 单个 featurizer 失败不必立即中断；
7. 所有 featurizer 失败时整体失败。

### 输出

```json
{
  "executed_featurizers": [],
  "feature_groups": [],
  "n_features": 140
}
```

---

## 11.7 功能七：支持 Structure Basic Featurizer

### featurizer_id

```text
matminer_structure_basic
```

### 依赖

```text
pymatgen
matminer
```

### MVP 扩展范围

本次可以支持基础结构特征，但不强制支持复杂 graph representation。

支持内容：

1. density；
2. volume；
3. number of sites；
4. lattice parameters；
5. space group number，如可获得；
6. packing-related simple descriptors；
7. matminer 基础 structure featurizers，如依赖可用。

### 输入

| 数据形式                  | 是否支持 |
| --------------------- | ---- |
| pymatgen Structure 对象 | 支持   |
| CIF 字符串               | 可选支持 |
| CIF 文件路径              | 可选支持 |
| POSCAR 文件路径           | 可选支持 |
| structure column      | 可选支持 |

### 输出

```json
{
  "group_name": "matminer_structure_basic",
  "n_features": 10,
  "status": "success"
}
```

---

## 11.8 功能八：Descriptor Cleaner 增强

### featurizer_id

```text
descriptor_cleaner
```

### 目标

对用户已有 descriptor matrix 进行更规范的整理。

### 处理

1. 识别所有数值列；
2. 排除 target_column；
3. 排除 sample_id、id、formula、composition 等非特征列；
4. 删除全空列；
5. 删除常量列；
6. 标记高缺失率列；
7. 保留需要 imputation 的信息；
8. 输出 feature group。

---

## 11.9 功能九：Feature Group 元数据增强

每个 feature group 必须记录：

```json
{
  "group_name": "matminer_element_property",
  "display_name": "Matminer ElementProperty",
  "n_features": 132,
  "feature_columns": [],
  "status": "success",
  "dependency": ["pymatgen", "matminer"],
  "execution_time_ms": 820,
  "failed_sample_count": 0
}
```

---

## 11.10 功能十：特征命名规范

所有外部库生成特征必须统一命名。

### 规则

```text
{featurizer_id}__{original_feature_name}
```

示例：

```text
matminer_element_property__MagpieData_mean_NpValence
matminer_stoichiometry__num_atoms
basic_composition__n_elements
```

### 要求

1. 避免不同 featurizer 特征名冲突；
2. 保留原始 matminer feature name；
3. 支持按 feature group 过滤；
4. 支持后续解释与报告生成。

---

## 11.11 功能十一：依赖检测与 Registry 动态可用性

### 目标

Registry 不仅记录静态状态，还应能根据依赖是否安装判断 featurizer 当前是否 truly available。

### 处理

1. 启动时或调用时检查依赖；
2. 对需要 matminer 的 featurizer 检查 matminer；
3. 对需要 pymatgen 的 featurizer 检查 pymatgen；
4. 依赖缺失时标记为 unavailable；
5. 依赖存在时标记为 available；
6. Registry API 返回 dependency_status。

### 输出示例

```json
{
  "id": "matminer_element_property",
  "status": "available",
  "requires_dependencies": ["pymatgen", "matminer"],
  "dependency_status": {
    "pymatgen": "installed",
    "matminer": "installed"
  }
}
```

---

## 11.12 功能十二：Workflow Planning Prompt 适配

Workflow Planning Prompt Builder 必须读取扩展后的 Registry。

要求：

1. 只向 LLM 展示 status=available 的 featurizer；
2. planned/unavailable featurizer 只能用于说明未来能力；
3. LLM 输出的 `executable_featurizers` 必须来自 available 列表；
4. LLM 不允许编造 featurizer ID；
5. Validator 必须校验 featurizer ID 是否在 Registry 中。

---

## 11.13 功能十三：特征质量检查增强

在现有 feature_quality_checker 基础上新增：

1. 高缺失率特征检查；
2. 高维特征矩阵检查；
3. 重复特征名检查；
4. 全零特征检查；
5. 近似常量特征检查；
6. 无穷值检查；
7. matminer 生成失败样本统计；
8. feature group 级别质量汇总。

---

## 12. 状态设计

### 12.1 Feature Engineering 状态

沿用现有状态：

| 状态                     | 含义        |
| ---------------------- | --------- |
| pending                | 待执行       |
| loading_data           | 正在加载原始数据  |
| featurizing            | 正在生成特征    |
| validating             | 正在检查特征矩阵  |
| completed              | 成功完成      |
| completed_with_warning | 成功完成但存在警告 |
| failed                 | 失败        |
| blocked                | 上游状态不满足   |

---

### 12.2 Featurizer 执行状态

新增 featurizer 级别状态：

| 状态                   | 含义                           |
| -------------------- | ---------------------------- |
| success              | 执行成功                         |
| success_with_warning | 执行成功但存在警告                    |
| failed               | 执行失败                         |
| skipped              | 因策略或依赖跳过                     |
| unavailable          | 依赖缺失或当前不可用                   |
| fallback_used        | 原 featurizer 不可用，使用 fallback |

---

## 13. API 需求

### 13.1 现有 API 保持不变

继续使用：

```text
POST /api/feature-engineering/{task_id}
GET /api/feature-engineering/{feature_engineering_id}
GET /api/tasks/{task_id}/feature-engineering
POST /api/feature-engineering/{task_id}/rerun
GET /api/feature-engineering/{feature_engineering_id}/preview
```

---

### 13.2 Registry 查询接口增强

现有系统已有 Registry API：`GET /api/registries/featurizers` 与 `GET /api/registries/featurizers/validate`。

增强支持：

```text
GET /api/registries/featurizers?input_modality=composition&status=available
GET /api/registries/featurizers?feature_type=composition_descriptors
GET /api/registries/featurizers?requires_dependency=matminer
GET /api/registries/featurizers?mvp_supported=true
```

---

### 13.3 新增 Featurizer 详情接口

```text
GET /api/registries/featurizers/{featurizer_id}
```

响应示例：

```json
{
  "success": true,
  "message": "Featurizer retrieved successfully.",
  "data": {
    "id": "matminer_element_property",
    "display_name": "Matminer ElementProperty",
    "input_modalities": ["composition"],
    "feature_type": "composition_descriptors",
    "status": "available",
    "requires_dependencies": ["pymatgen", "matminer"],
    "dependency_status": {
      "pymatgen": "installed",
      "matminer": "installed"
    },
    "estimated_feature_count": 132
  }
}
```

---

### 13.4 可选新增依赖检查接口

```text
GET /api/registries/featurizers/dependencies
```

响应示例：

```json
{
  "success": true,
  "message": "Featurizer dependencies checked successfully.",
  "data": {
    "pymatgen": {
      "status": "installed",
      "version": "x.x.x"
    },
    "matminer": {
      "status": "installed",
      "version": "x.x.x"
    }
  }
}
```

---

## 14. 数据库设计

### 14.1 feature_engineering 表不强制新增字段

当前 Feature Engineering 表已采用结构化字段 + JSONB 的混合存储方式，完整结果可存入 `feature_json`，预览可存入 `preview_json`。因此，本次扩展不强制新增数据库字段。当前项目也已普遍采用 JSONB 存储复杂对象。

---

### 14.2 Feature Engineering Object 扩展字段

重点扩展以下 JSONB 内容：

```json
{
  "feature_generation": {
    "selected_featurizers": [],
    "executed_featurizers": [],
    "fallback_featurizers": [],
    "skipped_featurizers": [],
    "unsupported_featurizers": []
  },
  "feature_schema": {
    "feature_groups": [],
    "feature_columns": []
  },
  "dependency_metadata": {
    "pymatgen": {
      "version": "x.x.x"
    },
    "matminer": {
      "version": "x.x.x"
    }
  }
}
```

---

### 14.3 Registry 是否入库

本次不强制 Registry 入库。

推荐继续使用：

```text
Python 静态配置 + 动态依赖检查
```

原因：

1. 当前 featurizer 数量仍可控；
2. 更适合 AI Coding 工具快速实现；
3. 避免新增数据库迁移；
4. 方便通过代码评审管理 featurizer；
5. 后续再迁移为 YAML / JSON / 数据库表。

---

## 15. 配置需求

新增或扩展 `.env` 配置：

```text
ENABLE_PYMATGEN=true
ENABLE_MATMINER=true
ENABLE_MATMINER_MAGPIE=true
ENABLE_MATMINER_STOICHIOMETRY=true
ENABLE_MATMINER_ELEMENT_PROPERTY=true
ENABLE_MATMINER_VALENCE_ORBITAL=true
ENABLE_STRUCTURE_FEATURIZER=false
MAX_FEATURE_DIMENSION=2000
MAX_FEATURE_MISSING_RATIO=0.5
FEATURE_GROUP_PREFIX_ENABLED=true
FEATURE_EXTERNAL_LIBRARY_TIMEOUT=300
```

说明：

| 配置                               | 说明                   |
| -------------------------------- | -------------------- |
| ENABLE_PYMATGEN                  | 是否启用 pymatgen 解析     |
| ENABLE_MATMINER                  | 是否启用 matminer 总开关    |
| ENABLE_MATMINER_MAGPIE           | 是否启用 Magpie 特征       |
| ENABLE_MATMINER_STOICHIOMETRY    | 是否启用 Stoichiometry   |
| ENABLE_MATMINER_ELEMENT_PROPERTY | 是否启用 ElementProperty |
| ENABLE_MATMINER_VALENCE_ORBITAL  | 是否启用 ValenceOrbital  |
| ENABLE_STRUCTURE_FEATURIZER      | 是否启用结构特征             |
| MAX_FEATURE_DIMENSION            | 最大允许特征维度             |
| MAX_FEATURE_MISSING_RATIO        | 最大允许缺失比例             |
| FEATURE_GROUP_PREFIX_ENABLED     | 是否启用特征名前缀            |
| FEATURE_EXTERNAL_LIBRARY_TIMEOUT | 外部库特征生成超时阈值          |

---

## 16. 前端需求

### 16.1 FeatureEngineeringPanel 增强

新增展示：

1. Feature Group Summary；
2. Executed Featurizers；
3. Dependency Status；
4. Matminer / Pymatgen Version；
5. Fallback Featurizers；
6. Skipped / Unavailable Featurizers；
7. Feature Count by Group；
8. Feature Quality Summary；
9. High Missing Ratio Features；
10. Constant Features；
11. Feature Matrix Preview；
12. Full JSON。

---

### 16.2 Registry Capability 展示

可选新增：

```text
Featurizer Capability Panel
```

展示：

1. 当前可用 featurizer；
2. planned / unavailable featurizer；
3. 每个 featurizer 支持的 input_modality；
4. 每个 featurizer 的 dependency_status；
5. 每个 featurizer 的 estimated_feature_count；
6. 是否启用。

---

## 17. 与已实现模块的衔接

### 17.1 与 Workflow Planning 的衔接

Workflow Planning 继续负责生成 `feature_strategy`。

本次扩展要求：

1. Prompt Builder 从 Registry 中读取 available featurizers；
2. LLM 只能选择 available featurizer；
3. Validator 校验 `executable_featurizers`；
4. planned/unavailable featurizer 不得进入 executable 列表；
5. 新增外部库 featurizer 后，Workflow Planning 无需改主流程，只需读取扩展后的 Registry。

---

### 17.2 与 Feature Engineering 的衔接

Feature Engineering 继续负责执行 featurizer。

本次扩展要求：

1. Strategy Resolver 使用 Registry 解析 featurizer；
2. Featurizer Router 支持新 featurizer；
3. 每个 featurizer 独立执行；
4. 每个 featurizer 独立记录状态；
5. 所有 feature group 合并为统一 feature matrix。

---

### 17.3 与 Dataset Profile 的衔接

Dataset Profile 不需要重构。

继续提供：

1. dataset_source；
2. input_columns；
3. target_column；
4. input_modality；
5. is_usable_for_ml。

如果后续启用 structure featurizer，Dataset Profile 需要进一步增强 CIF/POSCAR 加载与 structure column 检查，但本次 PRD 可先将其列为可选扩展。

---

### 17.4 与 Pipeline Generation 的衔接

Pipeline Generation 后续只消费最终结果：

1. feature_matrix_artifact_id；
2. feature_matrix_path；
3. target_column；
4. feature_columns；
5. feature_groups；
6. preprocessing_requirements；
7. ready_for_pipeline_generation。

Pipeline Generation 不应重新执行 feature engineering。

---

## 18. 错误处理

### 18.1 新增错误码

| 错误码                                    | 场景                  |
| -------------------------------------- | ------------------- |
| PYMATGEN_NOT_INSTALLED                 | pymatgen 未安装        |
| MATMINER_NOT_INSTALLED                 | matminer 未安装        |
| EXTERNAL_FEATURIZER_DEPENDENCY_MISSING | 外部 featurizer 依赖缺失  |
| EXTERNAL_FEATURIZER_FAILED             | 外部库特征生成失败           |
| COMPOSITION_PARSE_FAILED               | composition 解析失败    |
| STRUCTURE_PARSE_FAILED                 | structure 解析失败      |
| FEATURIZER_GROUP_FAILED                | 单个 feature group 失败 |
| ALL_FEATURIZERS_FAILED                 | 所有 featurizer 均失败   |
| FEATURE_GROUP_MERGE_FAILED             | feature group 合并失败  |
| FEATURE_NAME_CONFLICT                  | 特征名冲突               |
| FEATURE_DIMENSION_TOO_HIGH             | 特征维度超过阈值            |
| FEATURE_MISSING_RATIO_TOO_HIGH         | 特征缺失比例超过阈值          |

---

### 18.2 Warning 设计

| warning                               | 场景                                      |
| ------------------------------------- | --------------------------------------- |
| USING_BASIC_COMPOSITION_FALLBACK      | 高级 featurizer 不可用，回退到 basic_composition |
| MATMINER_FEATURES_PARTIALLY_FAILED    | matminer 部分样本失败                         |
| HIGH_FEATURE_MISSING_RATIO            | 特征缺失率较高                                 |
| HIGH_DIMENSIONAL_FEATURE_MATRIX       | 特征维度较高                                  |
| CONSTANT_FEATURES_DROPPED             | 常量特征被删除                                 |
| FEATURE_GROUP_SKIPPED                 | 某 feature group 被跳过                     |
| STRUCTURE_FEATURES_DISABLED           | 结构特征未启用                                 |
| EXTERNAL_LIBRARY_VERSION_NOT_RECORDED | 未能记录外部库版本                               |

---

## 19. 非功能需求

### 19.1 稳定性

1. 单个 featurizer 失败不应立即导致整体失败；
2. 所有 featurizer 失败才整体失败；
3. 外部依赖缺失必须有明确 warning；
4. matminer 失败时可 fallback 到 basic_composition；
5. feature artifact 保存失败必须阻断；
6. 大型特征生成失败时不得影响上游记录。

---

### 19.2 性能

1. 中等规模数据集应可在同步接口内完成；
2. 外部库执行时间必须记录；
3. 高维特征矩阵不得直接通过 API 返回；
4. preview 限制默认 20 行；
5. 大规模数据集后续应支持异步任务队列；
6. 支持通过配置限制最大特征维度。

---

### 19.3 可追踪性

1. 记录每个 featurizer 的输入、输出、状态；
2. 记录外部库版本；
3. 记录失败样本数量；
4. 记录 feature group 数量；
5. 记录 fallback 过程；
6. 记录最终 feature columns；
7. 记录 artifact 路径和格式。

---

### 19.4 可扩展性

新增 featurizer 应遵循：

```text
Registry 注册
    ↓
Featurizer 类实现
    ↓
Router 映射
    ↓
Workflow Planning 自动可见
    ↓
Feature Engineering 自动可执行
```

---

## 20. 验收标准

| 序号 | 验收标准                                                    |
| -- | ------------------------------------------------------- |
| 1  | requirements.txt 中引入 pymatgen                           |
| 2  | requirements.txt 中引入 matminer                           |
| 3  | Registry 能识别 pymatgen / matminer 是否安装                   |
| 4  | Registry 能返回 matminer 相关 featurizer 的 dependency_status |
| 5  | Registry 中新增 matminer_stoichiometry                     |
| 6  | Registry 中新增 matminer_element_property                  |
| 7  | Registry 中新增 matminer_valence_orbital                   |
| 8  | matminer_magpie 可在依赖满足时变为 available                     |
| 9  | Workflow Planning Prompt 能看到 available 的外部库 featurizer  |
| 10 | Workflow Plan 能输出多个 executable_featurizers              |
| 11 | Feature Engineering 能执行多个 matminer featurizer           |
| 12 | Feature Engineering 能记录每个 featurizer 的执行状态              |
| 13 | Feature Engineering 能生成 feature_groups                  |
| 14 | 特征名带 featurizer_id 前缀                                   |
| 15 | 外部库依赖缺失时能 fallback 到 basic_composition                  |
| 16 | 单个 featurizer 失败时，其他 featurizer 可继续                     |
| 17 | 所有 featurizer 失败时整体 failed                              |
| 18 | feature matrix artifact 可正常保存                           |
| 19 | preview 能展示扩展后的特征矩阵                                     |
| 20 | downstream_input 包含 feature_groups                      |
| 21 | 不执行模型训练                                                 |
| 22 | 不执行 HPO                                                 |
| 23 | 不计算模型评估指标                                               |
| 24 | 不生成 Pipeline 代码                                         |

---

## 21. 示例流程

### 21.1 Workflow Plan 输入

```json
{
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "executable_featurizers": [
      "matminer_stoichiometry",
      "matminer_element_property",
      "matminer_valence_orbital"
    ],
    "semantic_featurizers": [
      "stoichiometry",
      "element property statistics",
      "valence orbital descriptors"
    ],
    "feature_scaling_required": true,
    "feature_selection_required": true
  }
}
```

---

### 21.2 Feature Engineering 执行流程

```text
读取 Workflow Plan
    ↓
解析 executable_featurizers
    ↓
Registry 校验 featurizer 状态与依赖
    ↓
加载原始 composition 数据
    ↓
pymatgen 解析 composition
    ↓
执行 matminer_stoichiometry
    ↓
执行 matminer_element_property
    ↓
执行 matminer_valence_orbital
    ↓
合并 feature groups
    ↓
检查特征质量
    ↓
保存 feature matrix artifact
    ↓
输出 Feature Engineering Object
```

---

### 21.3 输出摘要

```json
{
  "status": "completed",
  "n_features": 144,
  "feature_groups": [
    {
      "group_name": "matminer_stoichiometry",
      "n_features": 8
    },
    {
      "group_name": "matminer_element_property",
      "n_features": 132
    },
    {
      "group_name": "matminer_valence_orbital",
      "n_features": 4
    }
  ],
  "ready_for_pipeline_generation": true
}
```

---

## 22. 后续迭代方向

### 22.1 V2：结构特征增强

1. CIF/POSCAR 文件解析；
2. pymatgen Structure 解析；
3. matminer structure featurizers；
4. density / symmetry / local environment descriptors；
5. structure-based task 全流程支持。

---

### 22.2 V3：特征选择与缩放实际执行

当前 Feature Engineering 主要标记：

1. scaling_required；
2. imputation_required；
3. feature_selection_required。

后续可实际执行：

1. SimpleImputer；
2. StandardScaler；
3. RobustScaler；
4. VarianceThreshold；
5. correlation filtering；
6. mutual information selection。

---

### 22.3 V4：多 Feature Set 对比

支持一次生成多个 feature set：

```text
basic
matminer_light
matminer_full
descriptor_only
hybrid
```

为后续 AutoML 搜索提供更多候选特征空间。

---

### 22.4 V5：异步特征工程

当 matminer 或 structure 特征生成耗时较长时，引入：

```text
FastAPI
    ↓
Task Queue
    ↓
Worker
    ↓
Feature Engineering
    ↓
Status Polling / SSE
```

---

## 23. 总结

本次扩展的核心是：允许 Feature Engineering 模块引入外部材料科学特征库，将当前轻量级 MVP 特征能力升级为标准材料描述符生成能力。

扩展前：

```text
basic_composition 16 维基础特征
```

扩展后：

```text
pymatgen composition parsing
    +
matminer Stoichiometry
    +
matminer ElementProperty / Magpie
    +
matminer ValenceOrbital
    +
可选 structure descriptors
    +
feature group 可追踪
```

最终输出保持不变：

```text
Feature Engineering Object
    +
Feature Matrix Artifact
    +
downstream_input
```

但特征质量、特征丰富度和后续建模可用性显著增强。

本模块仍然严格保持边界：

```text
只做特征工程；
不训练模型；
不做 HPO；
不计算模型评估指标；
不生成 Pipeline 代码。
```



