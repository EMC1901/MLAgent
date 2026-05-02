# Automated Feature Engineering 外部特征库扩展技术实现方案

## 1. 方案名称

Automated Feature Engineering External Library Enhancement  
自动化特征工程外部特征库扩展技术实现方案

---

## 2. 背景与目标

当前 MLAgent 已完成前五个核心业务模块：

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

其中 Feature Engineering 模块已经实现完整 MVP 流程，能够读取前四个模块输出、重新加载原始数据、解析特征策略、执行 featurizer、构建特征矩阵、检查特征质量、保存 parquet artifact，并持久化 Feature Engineering Object。

当前 Feature Engineering 已实现：

1. `CompositionFeaturizer`：生成 16 维基础 composition 描述符；
2. `DescriptorFeaturizer`：已有数值描述符直通；
3. `StructureFeaturizer`：占位符，MVP 未实现；
4. `Featurizer Registry`：统一注册、查询和校验 featurizer；
5. `artifact_manager.py`：保存 parquet 特征矩阵并生成 preview_json。

本次扩展目标是：在不破坏现有主流程和 API 的前提下，引入 `pymatgen` 与 `matminer`，将 Feature Engineering 从轻量 MVP 特征升级为标准材料特征工程能力。

---

# 3. 总体架构设计

## 3.1 扩展后的总体架构

```text
Workflow Plan.feature_strategy
        ↓
Feature Engineering Context Builder
        ↓
Data Loader Adapter
        ↓
Strategy Resolver
        ↓
Featurizer Registry
        ↓
Dependency Checker
        ↓
Featurizer Router
        ├── BasicCompositionFeaturizer
        ├── PymatgenCompositionParser
        ├── MatminerStoichiometryFeaturizer
        ├── MatminerElementPropertyFeaturizer
        ├── MatminerValenceOrbitalFeaturizer
        ├── MatminerMagpieFeaturizer
        ├── DescriptorCleanerFeaturizer
        └── StructureBasicFeaturizer
        ↓
Feature Group Merger
        ↓
Feature Matrix Builder
        ↓
Feature Quality Checker
        ↓
Artifact Manager
        ↓
Feature Engineering Builder
        ↓
Repository / PostgreSQL
```

---

## 3.2 技术实现原则

本次扩展坚持以下原则：

1. **不改变现有 Feature Engineering 主流程**；
2. **不修改前四个模块的核心职责**；
3. **Featurizer Registry 仍是唯一 featurizer 能力来源**；
4. **Workflow Planning 只选择 Registry 中 available 的 featurizer**；
5. **Feature Engineering 只执行 Registry 中 available 的 featurizer**；
6. **外部库失败时允许 fallback 到 basic_composition**；
7. **特征矩阵仍保存为 artifact，不直接存入数据库**；
8. **复杂特征工程结果继续存入 JSONB**；
9. **为 Pipeline Generation、Execution、Evaluation、Diagnosis、Report Generation 保留稳定接口**。

当前项目已经采用 JSONB 存储复杂对象、结构化字段单独建列的模式，且 Feature Engineering 已有 artifact 存储机制，因此本次扩展应继续沿用该设计。

---

# 4. 技术栈方案

## 4.1 后端新增依赖

在 `backend/requirements.txt` 中新增：

```text
pymatgen
matminer
scikit-learn
pyarrow
joblib
```

---

## 4.2 依赖用途说明

| 依赖             | 用途                                                            | 是否必需  |
| -------------- | ------------------------------------------------------------- | ----- |
| `pymatgen`     | Composition / Structure 解析                                    | P0 必需 |
| `matminer`     | 标准材料 featurizer                                               | P0 必需 |
| `scikit-learn` | 后续 imputation、scaling、feature selection、Pipeline Execution 预留 | P1 建议 |
| `pyarrow`      | parquet artifact 保存                                           | P1 建议 |
| `joblib`       | 后续保存 transformer / pipeline artifact                          | P2 预留 |

---

## 4.3 依赖引入策略

### 4.3.1 推荐策略

本次扩展建议正式引入：

```text
pymatgen
matminer
```

原因：

1. `pymatgen` 是材料 composition / structure 解析的事实标准之一；
2. `matminer` 能直接提供成熟材料特征工程能力；
3. 可以让 `matminer_magpie` 从 planned 升级为 available；
4. 能显著增强材料描述符表达能力。

---

### 4.3.2 容错策略

即使外部库未安装，也不能导致整个系统不可用。

系统应支持：

```text
pymatgen/matminer installed
    → 启用 matminer 系列 featurizer

pymatgen/matminer missing
    → matminer 系列 featurizer 标记 unavailable
    → fallback 到 basic_composition
```

---

## 4.4 配置项扩展

在 `settings.py` 和 `.env.example` 中新增：

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
FEATURE_DROP_CONSTANT_COLUMNS=true
FEATURE_DROP_ALL_MISSING_COLUMNS=true
```

说明：

| 配置项                                | 作用                                   |
| ---------------------------------- | ------------------------------------ |
| `ENABLE_PYMATGEN`                  | 是否启用 pymatgen                        |
| `ENABLE_MATMINER`                  | 是否启用 matminer 总开关                    |
| `ENABLE_MATMINER_MAGPIE`           | 是否启用 Magpie 特征                       |
| `ENABLE_MATMINER_STOICHIOMETRY`    | 是否启用 Stoichiometry                   |
| `ENABLE_MATMINER_ELEMENT_PROPERTY` | 是否启用 ElementProperty                 |
| `ENABLE_MATMINER_VALENCE_ORBITAL`  | 是否启用 ValenceOrbital                  |
| `ENABLE_STRUCTURE_FEATURIZER`      | 是否启用结构特征                             |
| `MAX_FEATURE_DIMENSION`            | 最大允许特征维度                             |
| `MAX_FEATURE_MISSING_RATIO`        | 最大允许特征缺失比例                           |
| `FEATURE_GROUP_PREFIX_ENABLED`     | 是否启用 `{featurizer_id}__{feature}` 命名 |
| `FEATURE_EXTERNAL_LIBRARY_TIMEOUT` | 外部库特征生成超时阈值                          |

---

# 5. 模块拆分设计

## 5.1 后端目录结构调整

在现有 Feature Engineering 模块下扩展：

```text
backend/app/modules/feature_engineering/
├── featurizers/
│   ├── __init__.py
│   ├── base_featurizer.py
│   ├── composition_featurizer.py
│   ├── descriptor_featurizer.py
│   ├── structure_featurizer.py
│   ├── pymatgen_composition_parser.py
│   ├── matminer_stoichiometry_featurizer.py
│   ├── matminer_element_property_featurizer.py
│   ├── matminer_valence_orbital_featurizer.py
│   ├── matminer_magpie_featurizer.py
│   ├── descriptor_cleaner_featurizer.py
│   └── structure_basic_featurizer.py
├── dependency_checker.py
├── featurizer_router.py
├── feature_group_merger.py
└── feature_metadata_builder.py
```

---

## 5.2 新增文件职责

| 文件                                        | 职责                                                       |
| ----------------------------------------- | -------------------------------------------------------- |
| `dependency_checker.py`                   | 检查 pymatgen、matminer、sklearn 等依赖是否可用，返回版本与状态             |
| `featurizer_router.py`                    | 根据 Registry 中的 featurizer_id 路由到具体 Featurizer 实现         |
| `feature_group_merger.py`                 | 合并多个 featurizer 输出的 feature dataframe                    |
| `feature_metadata_builder.py`             | 构建 feature_groups、dependency_metadata、execution metadata |
| `pymatgen_composition_parser.py`          | 使用 pymatgen 解析 composition                               |
| `matminer_stoichiometry_featurizer.py`    | 封装 matminer Stoichiometry                                |
| `matminer_element_property_featurizer.py` | 封装 matminer ElementProperty                              |
| `matminer_valence_orbital_featurizer.py`  | 封装 matminer ValenceOrbital                               |
| `matminer_magpie_featurizer.py`           | 封装 Magpie preset 类特征                                     |
| `descriptor_cleaner_featurizer.py`        | 增强 descriptor 输入清理                                       |
| `structure_basic_featurizer.py`           | 结构基础特征占位或初版实现                                            |

---

## 5.3 Registry 目录扩展

当前系统已存在 `backend/app/shared/registry/featurizer_registry.py`，并提供 featurizer 注册、查询和校验能力。

建议扩展为：

```text
backend/app/shared/registry/
├── __init__.py
├── featurizer_registry.py
├── schemas.py
├── exceptions.py
└── dependency_status.py
```

| 文件                       | 职责                                                                               |
| ------------------------ | -------------------------------------------------------------------------------- |
| `dependency_status.py`   | 提供依赖状态检测结果，供 Registry 使用                                                         |
| `schemas.py`             | 扩展 FeaturizerSpec，支持 dependency_status、estimated_feature_count、runtime_available |
| `featurizer_registry.py` | 新增外部库 featurizer 注册项和动态可用性判断                                                     |

---

# 6. Featurizer Registry 改造方案

## 6.1 FeaturizerSpec 扩展

当前 Registry 已能注册 featurizer 的基本信息。本次扩展建议将 FeaturizerSpec 扩展为：

```json
{
  "id": "matminer_element_property",
  "display_name": "Matminer ElementProperty Features",
  "description": "Generate element property statistics using matminer ElementProperty preset.",
  "input_modalities": ["composition"],
  "feature_type": "composition_descriptors",
  "supported_task_types": ["regression", "classification"],
  "aliases": [
    "element_property",
    "elemental_property_statistics",
    "magpie_element_property"
  ],
  "status": "available",
  "runtime_available": true,
  "requires_dependencies": ["pymatgen", "matminer"],
  "dependency_status": {
    "pymatgen": {
      "installed": true,
      "version": "x.x.x"
    },
    "matminer": {
      "installed": true,
      "version": "x.x.x"
    }
  },
  "output_feature_kind": "numeric",
  "estimated_feature_count": 132,
  "fallback_priority": 80,
  "implementation": "MatminerElementPropertyFeaturizer"
}
```

---

## 6.2 新增 Registry 字段说明

| 字段                        | 说明                  |
| ------------------------- | ------------------- |
| `runtime_available`       | 结合配置开关和依赖检测后的真实可用状态 |
| `dependency_status`       | 外部库安装状态与版本          |
| `estimated_feature_count` | 预估特征数量              |
| `implementation`          | 对应 Featurizer 实现类名称 |
| `fallback_priority`       | fallback 优先级        |

---

## 6.3 新增 Featurizer 注册项

### 6.3.1 `pymatgen_composition_parser`

```text
id: pymatgen_composition_parser
input_modalities: composition
feature_type: parser
status: available if pymatgen installed
implementation: PymatgenCompositionParser
```

说明：该组件主要作为 matminer composition featurizer 的前置解析能力，默认不单独作为 feature group 输出。

---

### 6.3.2 `matminer_stoichiometry`

```text
id: matminer_stoichiometry
input_modalities: composition
feature_type: composition_descriptors
requires_dependencies: pymatgen, matminer
implementation: MatminerStoichiometryFeaturizer
estimated_feature_count: 8
```

---

### 6.3.3 `matminer_element_property`

```text
id: matminer_element_property
input_modalities: composition
feature_type: composition_descriptors
requires_dependencies: pymatgen, matminer
implementation: MatminerElementPropertyFeaturizer
estimated_feature_count: 132
```

---

### 6.3.4 `matminer_valence_orbital`

```text
id: matminer_valence_orbital
input_modalities: composition
feature_type: composition_descriptors
requires_dependencies: pymatgen, matminer
implementation: MatminerValenceOrbitalFeaturizer
estimated_feature_count: 4
```

---

### 6.3.5 `matminer_magpie`

当前 Registry 中已有 `matminer_magpie`，但处于 planned 状态。扩展后：

```text
如果 pymatgen + matminer 可用：
    status = available
    runtime_available = true

否则：
    status = unavailable 或 planned
    runtime_available = false
```

---

### 6.3.6 `descriptor_cleaner`

```text
id: descriptor_cleaner
input_modalities: descriptor
feature_type: existing_descriptors
requires_dependencies: pandas, numpy
implementation: DescriptorCleanerFeaturizer
estimated_feature_count: dynamic
```

---

### 6.3.7 `matminer_structure_basic`

```text
id: matminer_structure_basic
input_modalities: structure
feature_type: structure_descriptors
requires_dependencies: pymatgen, matminer
implementation: StructureBasicFeaturizer
status: available only if ENABLE_STRUCTURE_FEATURIZER=true and dependencies installed
```

---

## 6.4 Registry 查询逻辑改造

`get_available_featurizers(input_modality, task_type)` 应改为同时检查：

1. 静态 status；
2. 配置开关；
3. 依赖是否安装；
4. input_modality 是否匹配；
5. task_type 是否匹配；
6. runtime_available 是否为 true。

返回给 Workflow Planning 的 featurizer 必须是：

```text
status = available
runtime_available = true
```

---

# 7. Feature Engineering 内部执行架构

## 7.1 Service 层主流程保持不变

当前 Feature Engineering Service 的主流程已经完整，不应重写。扩展后仍保持：

```text
create_feature_engineering(task_id)
    ↓
build_feature_engineering_context()
    ↓
reload_raw_data()
    ↓
resolve_feature_strategy()
    ↓
run_featurizers()
    ↓
build_feature_matrix()
    ↓
check_feature_quality()
    ↓
save_feature_artifact()
    ↓
build_feature_engineering_object()
    ↓
repository.create()
```

当前项目已有该链路，扩展应只增强 `resolve_feature_strategy()` 与 `run_featurizers()` 之后的能力，不改变 API 层与持久化模式。

---

## 7.2 Strategy Resolver 改造

### 输入

```json
{
  "feature_strategy": {
    "executable_featurizers": [
      "matminer_stoichiometry",
      "matminer_element_property",
      "matminer_valence_orbital"
    ]
  },
  "input_modality": "composition",
  "task_type": "regression"
}
```

### 处理

1. 读取 `executable_featurizers`；
2. 通过 Registry 解析每个 featurizer；
3. 检查 runtime_available；
4. 检查 input_modality；
5. 检查 task_type；
6. 将 unavailable featurizer 放入 skipped / unsupported；
7. 如果所有外部 featurizer 不可用，fallback 到 `basic_composition`；
8. 输出 ResolvedFeatureStrategy。

### 输出

```json
{
  "selected_featurizers": [
    "matminer_stoichiometry",
    "matminer_element_property",
    "matminer_valence_orbital"
  ],
  "fallback_featurizers": [],
  "skipped_featurizers": [],
  "unsupported_featurizers": [],
  "dependency_metadata": {
    "pymatgen": "x.x.x",
    "matminer": "x.x.x"
  }
}
```

---

## 7.3 Featurizer Router 设计

### 职责

`featurizer_router.py` 根据 featurizer_id 找到对应实现。

### 路由表

| featurizer_id               | 实现类                                 |
| --------------------------- | ----------------------------------- |
| `basic_composition`         | `CompositionFeaturizer`             |
| `descriptor_passthrough`    | `DescriptorFeaturizer`              |
| `descriptor_cleaner`        | `DescriptorCleanerFeaturizer`       |
| `matminer_stoichiometry`    | `MatminerStoichiometryFeaturizer`   |
| `matminer_element_property` | `MatminerElementPropertyFeaturizer` |
| `matminer_valence_orbital`  | `MatminerValenceOrbitalFeaturizer`  |
| `matminer_magpie`           | `MatminerMagpieFeaturizer`          |
| `matminer_structure_basic`  | `StructureBasicFeaturizer`          |

---

## 7.4 Featurizer 统一接口

当前已有 `base_featurizer.py` 抽象基类。扩展后所有 featurizer 必须遵循统一接口：

```text
featurize(raw_dataframe, context, resolved_strategy) → FeaturizationResult
```

### FeaturizationResult 标准结构

```json
{
  "featurizer_id": "matminer_element_property",
  "display_name": "Matminer ElementProperty Features",
  "status": "success",
  "feature_dataframe": "internal_dataframe_reference",
  "feature_columns": [],
  "failed_samples": [],
  "failed_sample_count": 0,
  "warnings": [],
  "errors": [],
  "execution_time_ms": 820,
  "dependency_versions": {
    "pymatgen": "x.x.x",
    "matminer": "x.x.x"
  }
}
```

---

# 8. 外部库 Featurizer 设计

## 8.1 PymatgenCompositionParser

### 职责

为所有 matminer composition featurizer 提供统一 composition 解析。

### 输入

```text
raw_dataframe + composition_column
```

### 输出

```text
pymatgen Composition list
```

### 失败处理

1. 单样本解析失败：记录 failed_sample；
2. 失败比例低于阈值：该样本相关特征填 NaN；
3. 失败比例超过阈值：当前 featurizer failed；
4. 全部失败：整体 Feature Engineering failed，除非 fallback 可用。

---

## 8.2 MatminerStoichiometryFeaturizer

### 输入

pymatgen Composition list。

### 输出

stoichiometry feature dataframe。

### 特征命名

```text
matminer_stoichiometry__{original_feature_name}
```

### 记录内容

1. n_features_generated；
2. failed_sample_count；
3. execution_time_ms；
4. dependency_versions。

---

## 8.3 MatminerElementPropertyFeaturizer

### 输入

pymatgen Composition list。

### 默认配置

```text
ElementProperty.from_preset("magpie")
```

### 输出

Magpie 风格元素属性统计特征。

### 特征命名

```text
matminer_element_property__{original_feature_name}
```

---

## 8.4 MatminerValenceOrbitalFeaturizer

### 输入

pymatgen Composition list。

### 输出

价电子轨道描述符。

### 特征命名

```text
matminer_valence_orbital__{original_feature_name}
```

---

## 8.5 MatminerMagpieFeaturizer

### 定位

`matminer_magpie` 可以作为对 `matminer_element_property` 的语义包装，或者作为单独 featurizer。

推荐 MVP 扩展中将其映射为：

```text
matminer_magpie → ElementProperty.from_preset("magpie")
```

并在 Registry 中保留 alias：

```text
magpie
magpie_descriptors
matminer_composition_features
```

---

## 8.6 StructureBasicFeaturizer

### MVP 扩展策略

结构特征可以分两阶段实现。

#### 阶段一

支持用户数据中已有数值型 structure descriptors，fallback 到 `descriptor_cleaner`。

#### 阶段二

支持 pymatgen Structure 解析和基础结构特征：

1. density；
2. volume；
3. number of sites；
4. lattice a/b/c；
5. lattice alpha/beta/gamma；
6. formula weight；
7. space group number，如可获得。

### 注意

当前系统已明确 structure featurizer 是占位符，CIF/POSCAR 等结构文件加载和解析尚未实现，且 pymatgen/matminer 尚未引入，因此结构特征建议作为 P1 或 P2，不应阻塞 composition 扩展。

---

# 9. Feature Group 合并设计

## 9.1 Feature Group Merger 职责

`feature_group_merger.py` 负责将多个 featurizer 输出合并成统一 feature dataframe。

### 输入

```text
List[FeaturizationResult]
```

### 处理

1. 只合并 status 为 success / success_with_warning 的结果；
2. 保持原始样本顺序；
3. 检查行数一致性；
4. 检查重复列名；
5. 自动添加 featurizer 前缀；
6. 合并 failed_samples；
7. 合并 warnings / errors；
8. 生成 feature_groups metadata。

### 输出

```json
{
  "merged_feature_dataframe": "internal_dataframe_reference",
  "feature_groups": [],
  "merged_feature_columns": [],
  "warnings": [],
  "errors": []
}
```

---

## 9.2 特征命名规范

统一采用：

```text
{featurizer_id}__{original_feature_name}
```

示例：

```text
matminer_element_property__MagpieData_mean_NpValence
matminer_stoichiometry__num_atoms
basic_composition__n_elements
```

### 目的

1. 避免不同 featurizer 生成重名特征；
2. 支持按 feature group 解释；
3. 支持 Result Diagnosis 分析不同特征组贡献；
4. 支持 Report Generation 自动描述特征来源。

---

# 10. Feature Matrix Builder 改造

当前系统已有 `feature_matrix_builder.py`，负责构建标准特征矩阵。扩展后仍保持职责不变，但需要支持多 feature group。

## 10.1 标准矩阵结构

```text
sample_id
feature_group_1__feature_1
feature_group_1__feature_2
feature_group_2__feature_1
...
target_column
```

---

## 10.2 构建规则

1. 自动生成或保留 sample_id；
2. 合并 feature dataframe 与 target_column；
3. 不将原始 composition / structure 字段作为训练特征；
4. 保留 feature_groups metadata；
5. 检查 n_samples 与原始数据一致；
6. 检查 target_column 存在；
7. 检查 feature columns 非空；
8. 检查 feature dimension 不超过 `MAX_FEATURE_DIMENSION`。

---

# 11. Feature Quality Checker 改造

当前系统已有 feature_quality_checker，用于检查缺失、常量、全空等问题。扩展后需要支持高维外部库特征检查。

## 11.1 新增检查内容

1. 高缺失率特征；
2. 高维特征矩阵；
3. 重复特征名；
4. 全零特征；
5. 近似常量特征；
6. 无穷值；
7. matminer 单样本生成失败；
8. feature group 级别缺失统计；
9. feature group 级别失败统计。

---

## 11.2 输出结构增强

```json
{
  "missing_values": {
    "total_missing": 0,
    "columns_with_missing": [],
    "high_missing_ratio_columns": []
  },
  "feature_groups_quality": [
    {
      "group_name": "matminer_element_property",
      "missing_ratio": 0.02,
      "constant_feature_count": 3,
      "failed_sample_count": 0
    }
  ],
  "invalid_features": [],
  "dropped_features": [],
  "constant_features": [],
  "all_missing_features": [],
  "is_valid_feature_matrix": true,
  "warnings": [],
  "errors": []
}
```

---

## 11.3 阻断条件

以下情况应阻断：

1. 最终特征数为 0；
2. target_column 丢失；
3. 所有 featurizer 失败；
4. feature matrix artifact 保存失败；
5. 特征维度超过 `MAX_FEATURE_DIMENSION` 且未允许继续；
6. 所有特征缺失率超过阈值；
7. composition 解析全部失败。

---

# 12. Artifact Manager 改造

当前 artifact_manager 已负责保存 parquet 特征矩阵并生成 preview_json。

## 12.1 保持不变

1. 继续保存 parquet；
2. 继续保存 preview_json；
3. 不在 API 中返回完整矩阵；
4. 继续通过 artifact_id / artifact_path 供后续模块使用。

---

## 12.2 新增 metadata 文件

建议 artifact 目录结构扩展为：

```text
/app/artifacts/features/
└── feat_xxxxxxxx/
    ├── features.parquet
    ├── feature_schema.json
    ├── feature_groups.json
    ├── dependency_metadata.json
    └── metadata.json
```

---

## 12.3 metadata 内容

```json
{
  "feature_engineering_id": "feat_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "workflow_plan_id": "plan_xxxxxxxx",
  "n_samples": 4604,
  "n_features": 140,
  "target_column": "band_gap",
  "feature_groups": [],
  "dependency_metadata": {
    "pymatgen": "x.x.x",
    "matminer": "x.x.x"
  },
  "created_at": "2026-05-02T10:00:00"
}
```

---

# 13. Builder 与输出对象改造

## 13.1 Feature Engineering Object 保持兼容

已有字段继续保留：

1. feature_engineering_id；
2. task_id；
3. interpretation_id；
4. dataset_profile_id；
5. workflow_plan_id；
6. status；
7. input_modality；
8. feature_type；
9. feature_generation；
10. feature_matrix；
11. feature_schema；
12. feature_quality；
13. preprocessing_requirements；
14. downstream_input；
15. warnings；
16. errors。

---

## 13.2 新增字段

建议新增：

```json
{
  "dependency_metadata": {
    "pymatgen": {
      "installed": true,
      "version": "x.x.x"
    },
    "matminer": {
      "installed": true,
      "version": "x.x.x"
    }
  },
  "feature_schema": {
    "feature_groups": []
  },
  "feature_generation": {
    "fallback_featurizers": [],
    "skipped_featurizers": [],
    "unsupported_featurizers": []
  }
}
```

---

## 13.3 downstream_input 增强

```json
{
  "feature_matrix_artifact_id": "artifact_xxxxxxxx",
  "feature_matrix_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
  "target_column": "band_gap",
  "feature_columns": [],
  "feature_groups": [],
  "task_type": "regression",
  "primary_metric": "MAE",
  "preprocessing_requirements": {
    "scaling_required": true,
    "imputation_required": false,
    "feature_selection_required": true
  },
  "ready_for_pipeline_generation": true
}
```

---

# 14. API 协作设计

## 14.1 Feature Engineering API 保持兼容

现有接口保持不变：

```text
POST /api/feature-engineering/{task_id}
GET /api/feature-engineering/{feature_engineering_id}
GET /api/tasks/{task_id}/feature-engineering
POST /api/feature-engineering/{task_id}/rerun
GET /api/feature-engineering/{feature_engineering_id}/preview
```

当前系统已实现这些接口，扩展不应破坏它们。

---

## 14.2 Registry API 增强

当前系统已有：

```text
GET /api/registries/featurizers
GET /api/registries/featurizers/validate
```

它们由 `registry_api.py` 和 `featurizer_registry.py` 提供。

建议增强：

```text
GET /api/registries/featurizers?input_modality=composition&status=available
GET /api/registries/featurizers?feature_type=composition_descriptors
GET /api/registries/featurizers?requires_dependency=matminer
GET /api/registries/featurizers/{featurizer_id}
GET /api/registries/featurizers/dependencies
```

---

## 14.3 Registry API 响应增强

```json
{
  "success": true,
  "message": "Featurizers retrieved successfully.",
  "data": {
    "featurizers": [
      {
        "id": "matminer_element_property",
        "display_name": "Matminer ElementProperty Features",
        "input_modalities": ["composition"],
        "feature_type": "composition_descriptors",
        "status": "available",
        "runtime_available": true,
        "requires_dependencies": ["pymatgen", "matminer"],
        "dependency_status": {
          "pymatgen": {
            "installed": true,
            "version": "x.x.x"
          },
          "matminer": {
            "installed": true,
            "version": "x.x.x"
          }
        },
        "estimated_feature_count": 132
      }
    ]
  }
}
```

---

# 15. 与已完成模块的衔接

## 15.1 与 Task Specification

不需要改动。

继续通过 task_id 读取任务基本信息。所有后续模块都通过 task_id 关联同一任务，这是当前系统约定。

---

## 15.2 与 Task Interpretation

不需要改动。

Feature Engineering 继续读取 interpreted_input_modality、interpreted_task_type、material domain 等信息，不重新执行任务理解。

---

## 15.3 与 Dataset Profile

不需要重构主流程。

Feature Engineering 继续通过 `data_loader_adapter.reload_raw_data()` 复用 Dataset Profile 数据源信息重新加载原始数据。当前系统中 Feature Engineering 已依赖 Dataset Profile 与 Workflow Plan 作为前置对象。

结构数据相关能力未来可能需要 Dataset Profile 增强 CIF/POSCAR 文件加载与 structure column 检查；本次可先将 structure support 标为 P1/P2。

---

## 15.4 与 Workflow Planning

需要轻量改造。

Workflow Planning Prompt Builder 应从扩展后的 Registry 读取 available featurizers，避免 LLM 推荐不可执行 featurizer。当前 Workflow Planning 已具备 Prompt Builder、Validator、Builder 与持久化流程，本次只需增强 Prompt 和 Validator，不改变主流程。

### 改造点

1. Prompt Builder 注入外部库 featurizer 列表；
2. Validator 校验 `executable_featurizers`；
3. planned / unavailable featurizer 不允许进入 executable 列表；
4. Workflow Plan 的 `feature_strategy` 保持兼容。

---

# 16. 为后续模块预留接口

## 16.1 Pipeline Generation

Pipeline Generation 后续重点消费：

```json
{
  "feature_matrix_artifact_id": "artifact_xxxxxxxx",
  "feature_matrix_path": "/app/artifacts/features/feat_xxxxxxxx/features.parquet",
  "target_column": "band_gap",
  "feature_columns": [],
  "feature_groups": [],
  "preprocessing_requirements": {},
  "ready_for_pipeline_generation": true
}
```

Pipeline Generation 不需要关心 matminer 如何执行，只使用最终 feature matrix artifact。

---

## 16.2 Pipeline Execution

Pipeline Execution 后续通过 artifact_path 读取 parquet：

```text
read feature matrix artifact
    ↓
split X / y
    ↓
execute pipeline
```

---

## 16.3 Metric Evaluation

Metric Evaluation 后续可复用：

1. task_type；
2. primary_metric；
3. target_column；
4. feature_matrix_artifact_id。

---

## 16.4 Result Diagnosis

Result Diagnosis 后续可分析：

1. feature_groups；
2. featurizer failure；
3. fallback；
4. high missing ratio features；
5. constant features；
6. whether only basic fallback was used。

---

## 16.5 Report Generation

Report Generation 后续可使用：

1. selected_featurizers；
2. feature group descriptions；
3. dependency versions；
4. n_features；
5. feature quality；
6. warnings；
7. feature matrix artifact metadata。

---

# 17. 错误处理设计

## 17.1 新增异常类型

建议在 Feature Engineering 模块 exceptions.py 中增加：

```text
ExternalFeaturizerDependencyException
ExternalFeaturizerExecutionException
CompositionParseException
StructureParseException
FeatureGroupMergeException
FeatureDimensionTooHighException
FeatureMissingRatioTooHighException
```

---

## 17.2 新增错误码

| 错误码                                      | 场景                 |
| ---------------------------------------- | ------------------ |
| `PYMATGEN_NOT_INSTALLED`                 | pymatgen 未安装       |
| `MATMINER_NOT_INSTALLED`                 | matminer 未安装       |
| `EXTERNAL_FEATURIZER_DEPENDENCY_MISSING` | 外部 featurizer 依赖缺失 |
| `EXTERNAL_FEATURIZER_FAILED`             | 外部库特征生成失败          |
| `COMPOSITION_PARSE_FAILED`               | composition 解析失败   |
| `STRUCTURE_PARSE_FAILED`                 | structure 解析失败     |
| `FEATURE_GROUP_MERGE_FAILED`             | feature group 合并失败 |
| `ALL_FEATURIZERS_FAILED`                 | 所有 featurizer 均失败  |
| `FEATURE_DIMENSION_TOO_HIGH`             | 特征维度超过阈值           |
| `FEATURE_MISSING_RATIO_TOO_HIGH`         | 特征缺失比例超过阈值         |

---

## 17.3 Warning 设计

| warning                                 | 场景                                      |
| --------------------------------------- | --------------------------------------- |
| `USING_BASIC_COMPOSITION_FALLBACK`      | 外部 featurizer 不可用，回退到 basic_composition |
| `MATMINER_FEATURES_PARTIALLY_FAILED`    | matminer 部分样本失败                         |
| `EXTERNAL_LIBRARY_VERSION_NOT_RECORDED` | 无法记录依赖版本                                |
| `HIGH_FEATURE_MISSING_RATIO`            | 特征缺失比例较高                                |
| `HIGH_DIMENSIONAL_FEATURE_MATRIX`       | 特征维度较高                                  |
| `CONSTANT_FEATURES_DROPPED`             | 常量特征被删除                                 |
| `STRUCTURE_FEATURES_DISABLED`           | 结构特征未启用                                 |
| `FEATURE_GROUP_SKIPPED`                 | 某个 feature group 被跳过                    |

---

# 18. 状态管理设计

## 18.1 Feature Engineering 状态不变

继续沿用当前状态：

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

当前系统 Feature Engineering 已具备 completed、completed_with_warning、failed、blocked 等状态，扩展不应引入不兼容状态。

---

## 18.2 Featurizer 执行状态

新增 featurizer 级别状态：

```text
success
success_with_warning
failed
skipped
unavailable
fallback_used
```

这些状态只存在于 `feature_generation.executed_featurizers`、`skipped_featurizers`、`fallback_featurizers` 等 JSON 结构中，不需要新增数据库列。

---

# 19. 前端实现方案

## 19.1 FeatureEngineeringPanel 增强

当前前端已有 `FeatureEngineeringPanel.tsx` 与 `featureEngineeringApi.ts`。

建议增强展示：

1. Feature Group Summary；
2. Executed Featurizers；
3. Dependency Status；
4. pymatgen / matminer version；
5. Fallback Featurizers；
6. Skipped / Unavailable Featurizers；
7. Feature Count by Group；
8. High Missing Ratio Features；
9. Constant Features；
10. Feature Matrix Preview；
11. Full JSON。

---

## 19.2 Registry Capability Panel

建议新增或增强 Registry 展示组件：

```text
frontend/src/modules/featureEngineering/components/FeaturizerRegistryPanel.tsx
```

展示：

1. available featurizers；
2. planned featurizers；
3. unavailable featurizers；
4. dependency_status；
5. estimated_feature_count；
6. input_modality；
7. feature_type。

---

## 19.3 API 客户端扩展

在 `featureEngineeringApi.ts` 中新增：

```text
getFeaturizers(params)
getFeaturizerById(featurizerId)
getFeaturizerDependencies()
validateFeaturizerRegistry()
```

---

# 20. 测试方案

## 20.1 单元测试

建议新增：

```text
tests/modules/feature_engineering/test_dependency_checker.py
tests/modules/feature_engineering/test_pymatgen_composition_parser.py
tests/modules/feature_engineering/test_matminer_featurizers.py
tests/modules/feature_engineering/test_feature_group_merger.py
tests/shared/registry/test_external_featurizer_registry.py
```

---

## 20.2 测试重点

### Dependency Checker

1. pymatgen installed；
2. matminer installed；
3. 依赖缺失时返回 unavailable；
4. version 能被记录。

### Registry

1. matminer featurizer 可注册；
2. dependency missing 时 runtime_available=false；
3. available featurizer 才进入 Prompt；
4. fallback 返回 basic_composition。

### Featurizer

1. 合法 composition 可被 pymatgen 解析；
2. 非法 composition 被记录 failed_samples；
3. matminer_stoichiometry 输出非空特征；
4. matminer_element_property 输出特征列；
5. 多 featurizer 输出可合并；
6. 特征名前缀正确。

### Feature Engineering 集成测试

1. Workflow Plan 指定多个 matminer featurizer；
2. Feature Engineering 成功输出 feature_groups；
3. artifact 成功保存；
4. preview 可读取；
5. fallback 可用；
6. 所有 featurizer 失败时整体 failed。

---

# 21. 开发步骤建议

## 阶段一：依赖与配置

1. 更新 requirements.txt；
2. 更新 Dockerfile，确保依赖能安装；
3. 更新 .env.example；
4. 更新 settings.py；
5. 新增 dependency_checker.py。

---

## 阶段二：Registry 扩展

1. 扩展 FeaturizerSpec；
2. 注册 matminer_stoichiometry；
3. 注册 matminer_element_property；
4. 注册 matminer_valence_orbital；
5. 升级 matminer_magpie；
6. 注册 descriptor_cleaner；
7. 增加 runtime_available；
8. 增强 Registry API。

---

## 阶段三：Featurizer 实现

1. 实现 PymatgenCompositionParser；
2. 实现 MatminerStoichiometryFeaturizer；
3. 实现 MatminerElementPropertyFeaturizer；
4. 实现 MatminerValenceOrbitalFeaturizer；
5. 实现 MatminerMagpieFeaturizer；
6. 实现 DescriptorCleanerFeaturizer；
7. 实现 StructureBasicFeaturizer placeholder 或 P1 版本。

---

## 阶段四：Feature Engineering 主链路增强

1. 修改 strategy_resolver.py；
2. 新增 featurizer_router.py；
3. 新增 feature_group_merger.py；
4. 增强 feature_matrix_builder.py；
5. 增强 feature_quality_checker.py；
6. 增强 artifact_manager.py；
7. 增强 builder.py。

---

## 阶段五：Workflow Planning 适配

1. 修改 workflow_planning/prompt_builder.py；
2. 让 Prompt 读取扩展后的 available featurizers；
3. 修改 workflow_planning/validator.py；
4. 校验 executable_featurizers 是否 runtime_available；
5. 避免 LLM 选择 unavailable featurizer。

---

## 阶段六：前端展示增强

1. 增强 FeatureEngineeringPanel；
2. 增加 feature group 展示；
3. 增加 dependency status 展示；
4. 增加 Registry Capability Panel；
5. 增强 preview 展示。

---

## 阶段七：测试与回归

1. Registry 单元测试；
2. Dependency checker 测试；
3. matminer featurizer 测试；
4. Feature Engineering 集成测试；
5. 完整五模块端到端回归测试。

---

# 22. 部署与运维注意事项

## 22.1 Docker 构建

`pymatgen` 和 `matminer` 依赖较重，Docker 构建时间会增加。

建议：

1. 使用缓存层优化 requirements 安装；
2. 后续考虑拆分 base image；
3. 若构建失败，优先检查编译依赖；
4. 在 README 中说明首次构建时间较长。

---

## 22.2 运行资源

matminer 特征生成可能增加：

1. CPU 消耗；
2. 内存占用；
3. 请求耗时。

建议 MVP 阶段同步执行；当数据集较大时，后续引入任务队列。

---

## 22.3 Artifact 存储

当前上传文件和特征 artifact 均保存在本地目录，存在容器重启或卷未挂载导致丢失的风险。当前项目文档也已将文件上传目录和特征 artifact 存储列为潜在风险。

建议：

1. 开发环境使用 Docker volume；
2. 后续生产环境迁移至 MinIO / S3；
3. 增加 artifact 清理策略。

---

# 23. 验收标准

| 序号 | 验收标准                                                             |
| -- | ---------------------------------------------------------------- |
| 1  | requirements.txt 中新增 pymatgen                                    |
| 2  | requirements.txt 中新增 matminer                                    |
| 3  | Registry 能检测 pymatgen / matminer 安装状态                            |
| 4  | Registry API 能返回 dependency_status                               |
| 5  | Registry 中新增 matminer_stoichiometry                              |
| 6  | Registry 中新增 matminer_element_property                           |
| 7  | Registry 中新增 matminer_valence_orbital                            |
| 8  | matminer_magpie 在依赖满足时 runtime_available=true                    |
| 9  | Workflow Planning Prompt 只展示 runtime_available=true 的 featurizer |
| 10 | Workflow Planning Validator 拒绝 unavailable featurizer            |
| 11 | Feature Engineering 能执行多个 matminer featurizer                    |
| 12 | Feature Engineering 能合并多个 feature group                          |
| 13 | 特征名统一使用 `{featurizer_id}__{feature_name}`                        |
| 14 | Feature Engineering Object 包含 feature_groups                     |
| 15 | Feature Engineering Object 包含 dependency_metadata                |
| 16 | 单个外部 featurizer 失败时其他 featurizer 可继续                             |
| 17 | 外部库不可用时 fallback 到 basic_composition                             |
| 18 | 所有 featurizer 失败时整体 failed                                       |
| 19 | feature artifact 正常保存为 parquet                                   |
| 20 | preview 可展示扩展后的特征矩阵                                              |
| 21 | downstream_input 包含 feature_groups 和 preprocessing_requirements  |
| 22 | 不执行模型训练                                                          |
| 23 | 不执行 HPO                                                          |
| 24 | 不生成 Pipeline 代码                                                  |
| 25 | 五模块端到端流程可正常跑通                                                    |

---

# 24. 最终效果

扩展前：

```text
composition input
    ↓
basic_composition
    ↓
16-dimensional feature matrix
```

扩展后：

```text
composition input
    ↓
pymatgen Composition parsing
    ↓
matminer Stoichiometry
    +
matminer ElementProperty / Magpie
    +
matminer ValenceOrbital
    +
basic_composition fallback
    ↓
multi-group feature matrix artifact
```

最终输出仍然保持：

```text
Feature Engineering Object
    +
Feature Matrix Artifact
    +
downstream_input
```

但特征能力显著增强，为后续 Pipeline Generation、Pipeline Execution、Metric Evaluation、Result Diagnosis 和 Report Generation 提供更稳定、更丰富的材料特征基础。

