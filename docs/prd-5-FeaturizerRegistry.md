# Featurizer Registry 统一注册中心技术实现方案

## 1. 背景与问题

当前系统中出现的问题是：

```text
Workflow Planning 模块生成的 recommended_featurizers
    与
Feature Engineering 模块内部 _AVAILABLE_FEATURIZERS
不匹配
````

导致：

```text
LLM 推荐 featurizer 名称
    ↓
Feature Engineering 查找可用 featurizer
    ↓
全部被判定为 unsupported
    ↓
无可执行 featurizer
    ↓
Feature Engineering 无法继续
```

该问题的本质不是单个 featurizer 名称错误，而是模块之间缺少统一的 **工程契约层**。

Workflow Planning 模块输出的是“规划结果”，Feature Engineering 模块需要的是“可执行组件 ID”。如果二者分别维护自己的 featurizer 名称体系，就会持续出现命名不一致、别名不一致、未来扩展困难等问题。

---

## 2. 方案目标

本方案的目标是建立统一的 **Featurizer Registry**，作为 Workflow Planning 与 Feature Engineering 之间共享的特征工程能力注册中心。

核心目标：

1. 统一定义系统当前支持的 featurizer；
2. 统一定义 featurizer 的唯一 ID、别名、输入模态、适用任务、可用状态；
3. Workflow Planning 只能从 Registry 中选择可执行 featurizer；
4. Feature Engineering 只执行 Registry 中状态为 `available` 的 featurizer；
5. 支持 alias 映射，将 LLM 语义名称映射为系统内部可执行 ID；
6. 支持未来扩展 pymatgen、matminer、Magpie、structure descriptors 等特征工程能力；
7. 避免 LLM 自由创造工程组件名称；
8. 为 Pipeline Generation、Report Generation、前端能力展示预留统一接口。

---

## 3. 方案定位

Featurizer Registry 是一个跨模块共享能力层，位于：

```text
shared registry layer
    ↓
Workflow Planning
    ↓
Feature Engineering
    ↓
Pipeline Generation
```

它不是新的业务流程模块，而是一个 **shared capability / shared contract**。

它服务于：

1. Workflow Planning Prompt 构建；
2. Workflow Planning 输出校验；
3. Feature Engineering 策略解析；
4. Feature Engineering Featurizer 路由；
5. 前端展示系统支持的特征工程能力；
6. 后续 Pipeline Generation 生成特征工程步骤；
7. Report Generation 描述实际使用的特征方法。

---

## 4. 总体架构

## 4.1 当前相关模块

当前项目中，Workflow Planning 模块已经实现：

1. `context_builder.py`：读取 Task Specification、Task Interpretation、Dataset Profile；
2. `prompt_builder.py`：构建 LLM Prompt；
3. `llm_client_adapter.py`：复用 Task Interpretation 模块的 LLMClient；
4. `parser.py`：解析 LLM JSON；
5. `validator.py`：校验 Workflow Plan Schema；
6. `builder.py`：构建 Workflow Plan Object；
7. `repository.py`：持久化 Workflow Plan。

当前 Dataset Profile 模块已经能够输出 `workflow_planning_input`，作为 Workflow Planning 的数据事实输入；Workflow Planning 再输出 `feature_strategy` 给 Feature Engineering 消费。

---

## 4.2 引入 Registry 后的架构

```text
backend/app/shared/registry/
    └── featurizer_registry.py
            ↓
Workflow Planning Prompt Builder
            ↓
Workflow Planning Validator
            ↓
Workflow Plan Object
            ↓
Feature Engineering Strategy Resolver
            ↓
Feature Engineering Featurizer Router
            ↓
Feature Matrix Artifact
```

---

## 4.3 核心数据流

```text
Featurizer Registry
    ↓ 提供 available featurizer list
Workflow Planning Prompt Builder
    ↓ 限制 LLM 只能选择 executable featurizer_id
LLM 生成 Workflow Plan
    ↓
Workflow Planning Validator
    ↓ 校验 recommended_featurizers 是否存在于 Registry
Workflow Plan 持久化
    ↓
Feature Engineering Strategy Resolver
    ↓ 将 featurizer_id / alias 解析为 executable featurizer
Feature Engineering 执行
    ↓
Feature Engineering Object
```

---

# 5. 模块拆分设计

## 5.1 新增 shared registry 目录

建议新增：

```text
backend/app/shared/registry/
├── __init__.py
├── featurizer_registry.py
├── schemas.py
└── exceptions.py
```

---

## 5.2 文件职责

| 文件                       | 职责                                                                   |
| ------------------------ | -------------------------------------------------------------------- |
| `featurizer_registry.py` | 定义 featurizer 注册表、查询函数、alias 解析函数                                    |
| `schemas.py`             | 定义 FeaturizerSpec、FeaturizerCapability、FeaturizerResolveResult 等数据结构 |
| `exceptions.py`          | 定义 Registry 相关异常，如 FeaturizerNotFoundException                       |
| `__init__.py`            | 导出 Registry 公共方法                                                     |

---

## 5.3 可选扩展目录

如果后续 Registry 内容变多，可以拆成配置文件：

```text
backend/app/shared/registry/
├── featurizer_registry.py
├── schemas.py
├── data/
│   └── featurizers.json
└── loaders.py
```

MVP 阶段建议先用 Python 常量定义，避免引入过多配置解析复杂度。

---

# 6. Featurizer Registry 数据模型

## 6.1 FeaturizerSpec

每个 featurizer 应定义为一个标准对象。

```json
{
  "id": "basic_composition",
  "display_name": "Basic Composition Descriptors",
  "description": "Generate lightweight composition-based descriptors from chemical formulas.",
  "input_modalities": ["composition"],
  "feature_type": "composition_descriptors",
  "supported_task_types": ["regression", "classification"],
  "aliases": [
    "elemental_property_statistics",
    "stoichiometric_features",
    "composition_descriptors",
    "basic_composition_descriptors"
  ],
  "status": "available",
  "mvp_supported": true,
  "requires_dependencies": [],
  "output_feature_kind": "numeric",
  "estimated_feature_count": "10-50",
  "fallback_priority": 10
}
```

---

## 6.2 字段说明

| 字段                        | 说明                                                  |
| ------------------------- | --------------------------------------------------- |
| `id`                      | 系统内部唯一可执行 featurizer ID                             |
| `display_name`            | 前端展示名称                                              |
| `description`             | 功能说明                                                |
| `input_modalities`        | 支持的输入模态，如 composition、descriptor、structure          |
| `feature_type`            | 特征类型，如 composition_descriptors、existing_descriptors |
| `supported_task_types`    | 支持的任务类型，如 regression、classification                 |
| `aliases`                 | 可映射到该 featurizer 的语义别名                              |
| `status`                  | 当前状态：available、planned、disabled、deprecated          |
| `mvp_supported`           | 是否 MVP 可用                                           |
| `requires_dependencies`   | 依赖库，如 pymatgen、matminer                             |
| `output_feature_kind`     | 输出特征类型，如 numeric、categorical、mixed                  |
| `estimated_feature_count` | 预估特征数量                                              |
| `fallback_priority`       | fallback 选择优先级，数值越大优先级越高                            |

---

## 6.3 状态枚举

```text
available   当前可执行
planned     未来计划支持，但当前不可执行
disabled    临时关闭
deprecated  已废弃，不推荐使用
```

Workflow Planning 只能选择：

```text
status = available
```

Feature Engineering 只能执行：

```text
status = available
```

planned 类型可以出现在 `future_featurizers` 或 `unsupported_future_featurizers` 中，但不能进入 `executable_featurizers`。

---

# 7. MVP Registry 内容建议

## 7.1 basic_composition

```json
{
  "id": "basic_composition",
  "display_name": "Basic Composition Descriptors",
  "input_modalities": ["composition"],
  "feature_type": "composition_descriptors",
  "supported_task_types": ["regression", "classification"],
  "aliases": [
    "basic_composition",
    "composition_descriptors",
    "basic_composition_descriptors",
    "elemental_property_statistics",
    "stoichiometric_features",
    "composition_statistics",
    "formula_statistics"
  ],
  "status": "available",
  "mvp_supported": true,
  "requires_dependencies": [],
  "output_feature_kind": "numeric",
  "fallback_priority": 100
}
```

---

## 7.2 descriptor_passthrough

```json
{
  "id": "descriptor_passthrough",
  "display_name": "Existing Descriptor Passthrough",
  "input_modalities": ["descriptor"],
  "feature_type": "existing_descriptors",
  "supported_task_types": ["regression", "classification"],
  "aliases": [
    "descriptor_passthrough",
    "existing_descriptors",
    "descriptor_features",
    "numeric_descriptors",
    "precomputed_descriptors"
  ],
  "status": "available",
  "mvp_supported": true,
  "requires_dependencies": [],
  "output_feature_kind": "numeric",
  "fallback_priority": 100
}
```

---

## 7.3 structure_placeholder

```json
{
  "id": "structure_placeholder",
  "display_name": "Structure Featurizer Placeholder",
  "input_modalities": ["structure"],
  "feature_type": "structure_descriptors",
  "supported_task_types": ["regression", "classification"],
  "aliases": [
    "structure_descriptors",
    "structure_features",
    "crystal_structure_descriptors"
  ],
  "status": "planned",
  "mvp_supported": false,
  "requires_dependencies": ["pymatgen", "matminer"],
  "output_feature_kind": "numeric",
  "fallback_priority": 10
}
```

---

## 7.4 matminer_magpie

```json
{
  "id": "matminer_magpie",
  "display_name": "Matminer Magpie Descriptors",
  "input_modalities": ["composition"],
  "feature_type": "composition_descriptors",
  "supported_task_types": ["regression", "classification"],
  "aliases": [
    "magpie",
    "magpie_descriptors",
    "matminer_magpie",
    "matminer_composition_features",
    "element_property_magpie"
  ],
  "status": "planned",
  "mvp_supported": false,
  "requires_dependencies": ["matminer", "pymatgen"],
  "output_feature_kind": "numeric",
  "fallback_priority": 20
}
```

---

# 8. Registry 核心能力设计

## 8.1 查询所有 featurizers

用途：

1. 前端展示；
2. Workflow Planning Prompt 构建；
3. 调试接口。

输出：

```json
[
  {
    "id": "basic_composition",
    "display_name": "Basic Composition Descriptors",
    "status": "available"
  }
]
```

---

## 8.2 查询 available featurizers

输入：

```text
input_modality
task_type
feature_type 可选
```

输出：

```json
[
  {
    "id": "basic_composition",
    "display_name": "Basic Composition Descriptors",
    "feature_type": "composition_descriptors"
  }
]
```

用途：

1. Workflow Planning Prompt；
2. Workflow Planning Validator；
3. Feature Engineering Strategy Resolver。

---

## 8.3 alias 解析

输入：

```text
elemental_property_statistics
```

输出：

```json
{
  "input_name": "elemental_property_statistics",
  "resolved_id": "basic_composition",
  "matched_by": "alias",
  "status": "available"
}
```

---

## 8.4 fallback 获取

输入：

```json
{
  "input_modality": "composition",
  "task_type": "regression"
}
```

输出：

```json
{
  "fallback_featurizer_id": "basic_composition",
  "reason": "Highest priority available composition featurizer"
}
```

---

## 8.5 future / planned featurizer 查询

用于 Workflow Planning 解释：

```json
{
  "planned_featurizers": [
    "matminer_magpie"
  ]
}
```

注意：

planned featurizer 只能用于说明未来能力，不能进入可执行字段。

---

# 9. Workflow Planning 模块改造方案

当前 Workflow Planning 模块已有 Prompt Builder、LLM 调用适配器、Parser、Validator 和 Builder。Registry 应嵌入 Prompt 构建和 Validator 两个环节。

---

## 9.1 prompt_builder.py 改造

### 当前问题

Prompt 允许 LLM 自由生成：

```json
"recommended_featurizers": [
  "elemental_property_statistics",
  "stoichiometric_features"
]
```

这类名称偏语义，未必是系统可执行 ID。

---

### 改造目标

Prompt Builder 应从 Registry 获取当前可用 featurizer，并注入 Prompt。

示例：

```json
{
  "available_featurizers": [
    {
      "id": "basic_composition",
      "input_modalities": ["composition"],
      "feature_type": "composition_descriptors",
      "description": "Generate lightweight composition descriptors."
    },
    {
      "id": "descriptor_passthrough",
      "input_modalities": ["descriptor"],
      "feature_type": "existing_descriptors",
      "description": "Use existing numeric descriptor columns."
    }
  ]
}
```

---

### Prompt 规则新增

在 Workflow Planning Prompt 中增加：

```text
You must select executable featurizers only from available_featurizers.
Do not invent new executable featurizer IDs.
If you want to mention scientific or semantic feature concepts, put them into semantic_featurizers.
Only executable_featurizers will be consumed by the Feature Engineering module.
```

---

## 9.2 Workflow Plan 输出结构调整

建议将原来的：

```json
"feature_strategy": {
  "recommended_featurizers": [
    "elemental_property_statistics",
    "stoichiometric_features"
  ]
}
```

调整为：

```json
{
  "feature_strategy": {
    "feature_type": "composition_descriptors",
    "executable_featurizers": [
      "basic_composition"
    ],
    "semantic_featurizers": [
      "elemental_property_statistics",
      "stoichiometric_features"
    ],
    "unsupported_future_featurizers": [
      "matminer_magpie"
    ],
    "requires_structure_features": false,
    "feature_selection_required": true,
    "feature_scaling_required": true
  }
}
```

---

## 9.3 字段含义

| 字段                               | 含义                                    | 是否给 Feature Engineering 执行 |
| -------------------------------- | ------------------------------------- | -------------------------- |
| `executable_featurizers`         | Registry 中 `status=available` 的可执行 ID | 是                          |
| `semantic_featurizers`           | 语义层面的特征概念说明                           | 否                          |
| `unsupported_future_featurizers` | Registry 中 planned 或当前不支持的未来能力        | 否                          |
| `feature_type`                   | 特征工程类型                                | 是                          |
| `feature_selection_required`     | 后续是否需要特征选择                            | 是                          |
| `feature_scaling_required`       | 后续是否需要缩放                              | 是                          |

---

## 9.4 validator.py 改造

Validator 新增校验：

1. `feature_strategy.executable_featurizers` 必须为数组；
2. 每个 executable featurizer 必须存在于 Registry；
3. 每个 executable featurizer 的状态必须为 `available`；
4. 每个 executable featurizer 必须支持当前 input_modality；
5. `semantic_featurizers` 不要求存在于 Registry；
6. `unsupported_future_featurizers` 可以是 `planned`，但不能是完全未知名称；
7. 如果 executable_featurizers 为空，则尝试根据 input_modality 设置默认 fallback；
8. 如果 fallback 失败，则 Workflow Plan 校验失败。

---

## 9.5 兼容旧字段

为了兼容已有 Workflow Plan，可以支持旧字段：

```json
"recommended_featurizers": []
```

兼容逻辑：

```text
如果 executable_featurizers 存在：
    使用 executable_featurizers
否则如果 recommended_featurizers 存在：
    尝试通过 Registry alias 解析
否则：
    使用 Registry fallback
```

---

# 10. Feature Engineering 模块改造方案

Feature Engineering 模块应从“内部硬编码 `_AVAILABLE_FEATURIZERS`”改为依赖 Registry。

---

## 10.1 strategy_resolver.py 改造

### 当前问题

Feature Engineering 用 `_AVAILABLE_FEATURIZERS` 判断是否支持 featurizer。

### 改造目标

`strategy_resolver.py` 不再维护独立可用列表，而是调用 Registry。

---

## 10.2 新解析流程

```text
读取 Workflow Plan feature_strategy
    ↓
优先读取 executable_featurizers
    ↓
若不存在，读取 recommended_featurizers 兼容旧格式
    ↓
对每个名称执行 Registry.resolve()
    ↓
过滤 status != available 的 featurizer
    ↓
校验 input_modality 是否匹配
    ↓
如果没有可用 featurizer：
        使用 Registry.get_default_fallback()
    ↓
输出 ResolvedFeatureStrategy
```

---

## 10.3 ResolvedFeatureStrategy

```json
{
  "feature_type": "composition_descriptors",
  "input_modality": "composition",
  "selected_featurizers": [
    "basic_composition"
  ],
  "semantic_featurizers": [
    "elemental_property_statistics",
    "stoichiometric_features"
  ],
  "unsupported_featurizers": [],
  "fallback_featurizers": [],
  "resolution_log": [
    {
      "input": "elemental_property_statistics",
      "resolved_to": "basic_composition",
      "matched_by": "alias"
    }
  ],
  "feature_scaling_required": true,
  "feature_selection_required": true
}
```

---

## 10.4 Featurizer Router 改造

Featurizer Router 根据 `selected_featurizers` 调用具体实现：

| Registry ID              | 对应实现                                     |
| ------------------------ | ---------------------------------------- |
| `basic_composition`      | `CompositionFeaturizer`                  |
| `descriptor_passthrough` | `DescriptorFeaturizer`                   |
| `structure_placeholder`  | `StructureFeaturizer`，MVP 返回 unsupported |
| `matminer_magpie`        | 后续 `MatminerCompositionFeaturizer`       |

---

## 10.5 删除或降级 _AVAILABLE_FEATURIZERS

建议：

1. 删除 Feature Engineering 内部 `_AVAILABLE_FEATURIZERS`；
2. 或将其改为从 Registry 动态生成；
3. 禁止维护第二份独立可用列表。

最终应做到：

```text
Registry 是唯一 featurizer 能力来源
```

---

# 11. 前端与接口协作

## 11.1 新增 Registry 查询接口

可选新增 API：

```text
GET /api/registries/featurizers
```

### 功能

查询系统支持的 featurizer 能力。

### 响应示例

```json
{
  "success": true,
  "message": "Featurizer registry retrieved successfully.",
  "data": {
    "featurizers": [
      {
        "id": "basic_composition",
        "display_name": "Basic Composition Descriptors",
        "input_modalities": ["composition"],
        "feature_type": "composition_descriptors",
        "status": "available",
        "mvp_supported": true
      }
    ]
  }
}
```

---

## 11.2 按输入模态查询

```text
GET /api/registries/featurizers?input_modality=composition&status=available
```

用途：

1. Workflow Plan 前端展示；
2. Feature Engineering 前端展示；
3. 未来用户手动选择 featurizer。

---

## 11.3 前端展示调整

WorkflowPlanPanel 建议展示：

1. executable_featurizers；
2. semantic_featurizers；
3. unsupported_future_featurizers；
4. 每个 executable featurizer 的 display_name；
5. 是否 MVP supported。

FeatureEngineeringPanel 建议展示：

1. selected_featurizers；
2. resolution_log；
3. fallback_featurizers；
4. unsupported_featurizers；
5. 实际执行的 featurizer 实现。

---

# 12. 数据结构兼容策略

## 12.1 Workflow Plan 兼容

现有 Workflow Plan 中可能仍然是：

```json
"recommended_featurizers": [
  "elemental_property_statistics",
  "stoichiometric_features"
]
```

兼容策略：

```text
旧字段 recommended_featurizers
    ↓
Registry alias 解析
    ↓
映射到 executable featurizers
```

---

## 12.2 Feature Engineering 兼容

Feature Engineering 策略解析应支持：

```text
优先级 1：feature_strategy.executable_featurizers
优先级 2：feature_strategy.recommended_featurizers
优先级 3：Registry fallback
```

---

## 12.3 数据库无需强制迁移旧数据

由于 Workflow Plan 的完整对象存储在 JSONB 中，短期无需立即迁移旧的 `plan_json`。

建议：

1. 新生成的 Workflow Plan 使用新结构；
2. 旧 Workflow Plan 在 Feature Engineering 中通过兼容逻辑解析；
3. 后续如需统一，可增加 migration script。

当前项目已广泛采用 JSONB 存储复杂对象，这种兼容策略与现有混合存储方式一致。

---

# 13. 与已完成模块的自然衔接

## 13.1 与 Workflow Planning 的衔接

Workflow Planning 继续负责：

1. 构建 Planning Context；
2. 构建 Prompt；
3. 调用 LLM；
4. 解析和校验输出；
5. 保存 Workflow Plan。

Registry 只增强：

```text
Prompt Builder
Validator
Builder 输出结构
```

不改变 Workflow Planning 的主流程。

---

## 13.2 与 Feature Engineering 的衔接

Feature Engineering 继续负责：

1. 读取 Workflow Plan；
2. 解析 feature_strategy；
3. 调用具体 Featurizer；
4. 生成 Feature Matrix Artifact；
5. 输出 Feature Engineering Object。

Registry 只替代：

```text
_AVAILABLE_FEATURIZERS
硬编码 alias
硬编码 fallback
```

不改变 Feature Engineering 的核心流程。

---

## 13.3 与 Dataset Profile 的衔接

Dataset Profile 不需要改动。

它继续输出：

1. input_modality；
2. input_columns；
3. target_column；
4. workflow_planning_input；
5. is_usable_for_ml。

这些字段仍然用于 Registry 过滤可用 featurizer。

---

## 13.4 与 Task Interpretation 的衔接

Task Interpretation 不需要改动。

它输出的：

1. interpreted_input_modality；
2. interpreted_task_type；
3. interpreted_material_domain；

可以作为 Registry 查询条件。

---

# 14. 为后续模块预留扩展

## 14.1 Pipeline Generation

Pipeline Generation 可通过 Registry 获取：

1. featurizer ID；
2. 对应 pipeline component；
3. 需要的依赖；
4. 预期输入输出；
5. 是否需要保存 transformer。

未来可扩展字段：

```json
{
  "pipeline_component": "CompositionFeaturizerComponent",
  "requires_fit": false,
  "requires_transform": true,
  "artifact_type": "feature_matrix"
}
```

---

## 14.2 Pipeline Execution

Pipeline Execution 可通过 Registry 确认：

1. 该 featurizer 是否可执行；
2. 对应运行组件；
3. 依赖库是否可用；
4. 是否需要 fallback。

---

## 14.3 Result Diagnosis

Result Diagnosis 可基于 Registry 解释：

1. 当前使用的是基础特征还是高级特征；
2. 是否可能因特征表达能力不足导致模型效果差；
3. 是否建议升级到 planned featurizer，如 matminer_magpie。

---

## 14.4 Report Generation

Report Generation 可使用 Registry 中的：

1. display_name；
2. description；
3. feature_type；
4. aliases；
5. dependencies；

生成报告中的 Feature Engineering 方法描述。

---

# 15. 技术选型

## 15.1 后端技术栈

继续沿用当前系统：

| 技术                  | 用途                        |
| ------------------- | ------------------------- |
| FastAPI             | 提供 registry 查询接口          |
| Pydantic v2         | 定义 FeaturizerSpec 和响应模型   |
| SQLModel/PostgreSQL | MVP 不需要新表；后续可持久化 registry |
| JSONB               | 如未来将 registry 存数据库，可存复杂配置 |
| Python 常量 / JSON 配置 | MVP 推荐使用 Python 常量        |
| logging             | 记录 alias 解析和 fallback 情况  |

---

## 15.2 MVP 是否需要数据库表

MVP 不建议新增数据库表。

推荐：

```text
Featurizer Registry = Python 静态配置
```

原因：

1. 当前 featurizer 数量少；
2. 修改频率低；
3. 避免引入管理后台；
4. 避免数据库迁移；
5. 更适合快速修复模块契约问题。

后续可以迁移为：

```text
featurizer_registry 表
```

但不是当前必要项。

---

## 15.3 未来数据库表设计

如后续需要可视化管理 featurizer，可新增：

```text
featurizer_registry
```

字段：

| 字段                    | 类型          | 说明                                    |
| --------------------- | ----------- | ------------------------------------- |
| id                    | VARCHAR     | featurizer ID                         |
| display_name          | VARCHAR     | 展示名称                                  |
| input_modalities      | JSONB       | 支持模态                                  |
| feature_type          | VARCHAR     | 特征类型                                  |
| aliases               | JSONB       | 别名列表                                  |
| status                | VARCHAR     | available/planned/disabled/deprecated |
| requires_dependencies | JSONB       | 依赖库                                   |
| metadata_json         | JSONB       | 扩展元数据                                 |
| created_at            | TIMESTAMPTZ | 创建时间                                  |
| updated_at            | TIMESTAMPTZ | 更新时间                                  |

---

# 16. 错误处理设计

## 16.1 Registry 相关错误码

| 错误码                             | 场景                              |
| ------------------------------- | ------------------------------- |
| `FEATURIZER_NOT_FOUND`          | featurizer ID 或 alias 无法解析      |
| `FEATURIZER_NOT_AVAILABLE`      | featurizer 存在但状态不是 available    |
| `FEATURIZER_MODALITY_MISMATCH`  | featurizer 不支持当前 input_modality |
| `FEATURIZER_TASK_TYPE_MISMATCH` | featurizer 不支持当前 task_type      |
| `NO_AVAILABLE_FEATURIZER`       | 当前输入模态下没有可用 featurizer          |
| `FEATURIZER_REGISTRY_INVALID`   | Registry 配置本身不合法                |

---

## 16.2 Warning 设计

以下情况不直接失败，但进入 warnings：

1. LLM 输出旧字段 `recommended_featurizers`；
2. LLM 输出 alias 而非 executable ID；
3. alias 被成功映射到 executable ID；
4. LLM 输出 planned featurizer；
5. 使用 fallback featurizer；
6. 某个 featurizer 不支持当前输入模态，被忽略；
7. semantic_featurizers 中存在未注册名称。

---

# 17. 校验策略

## 17.1 Registry 自检

系统启动或测试时应检查：

1. featurizer id 唯一；
2. alias 不冲突；
3. status 合法；
4. input_modalities 合法；
5. feature_type 合法；
6. fallback_priority 合法；
7. available featurizer 至少有一个可用于 composition；
8. available featurizer 至少有一个可用于 descriptor。

---

## 17.2 Workflow Plan 校验

Workflow Planning Validator 应检查：

1. executable_featurizers 是否存在；
2. executable_featurizers 是否来自 Registry；
3. executable_featurizers 是否 available；
4. executable_featurizers 是否支持 input_modality；
5. recommended_featurizers 旧字段是否可兼容解析；
6. planned featurizer 不得进入 executable_featurizers。

---

## 17.3 Feature Engineering 校验

Feature Engineering Strategy Resolver 应检查：

1. 输入 featurizer 是否可解析；
2. 是否 available；
3. 是否支持 input_modality；
4. 是否支持 task_type；
5. 是否存在可用 fallback；
6. 最终 selected_featurizers 是否非空。

---

# 18. 测试方案

## 18.1 单元测试

建议新增测试：

```text
tests/shared/registry/test_featurizer_registry.py
tests/modules/workflow_planning/test_featurizer_registry_integration.py
tests/modules/feature_engineering/test_strategy_resolver.py
```

---

## 18.2 Registry 单元测试

测试内容：

1. `basic_composition` 可以被 id 查询；
2. `elemental_property_statistics` alias 可以解析到 `basic_composition`；
3. `stoichiometric_features` alias 可以解析到 `basic_composition`；
4. `existing_descriptors` alias 可以解析到 `descriptor_passthrough`；
5. `matminer_magpie` 状态为 planned，不能作为 executable；
6. composition fallback 返回 `basic_composition`；
7. descriptor fallback 返回 `descriptor_passthrough`；
8. structure 当前无 available featurizer，返回 planned 或 unsupported。

---

## 18.3 Workflow Planning 集成测试

测试内容：

1. Prompt 中包含 available_featurizers；
2. Validator 接受 `executable_featurizers=["basic_composition"]`；
3. Validator 拒绝 `executable_featurizers=["elemental_property_statistics"]`，除非走兼容解析；
4. Validator 拒绝 `executable_featurizers=["matminer_magpie"]`，因为其 status 为 planned；
5. 旧字段 `recommended_featurizers` 可兼容解析。

---

## 18.4 Feature Engineering 集成测试

测试内容：

1. 旧 Workflow Plan 的 `recommended_featurizers=["elemental_property_statistics"]` 可解析为 `basic_composition`；
2. 如果 LLM 输出未知 featurizer，composition 输入 fallback 到 `basic_composition`；
3. descriptor 输入 fallback 到 `descriptor_passthrough`；
4. structure 输入在无 descriptor fallback 时返回明确 unsupported；
5. selected_featurizers 非空时进入 Featurizer Router。

---

# 19. 推荐开发步骤

## 阶段一：建立 Registry 基础能力

1. 新增 `backend/app/shared/registry/` 目录；
2. 定义 FeaturizerSpec；
3. 定义 Featurizer Registry 静态配置；
4. 实现查询、alias 解析、fallback 查询；
5. 增加 Registry 自检逻辑。

---

## 阶段二：改造 Workflow Planning

1. 修改 `workflow_planning/prompt_builder.py`；
2. 在 Prompt 中注入 available featurizers；
3. 修改输出 schema，增加 `executable_featurizers`、`semantic_featurizers`、`unsupported_future_featurizers`；
4. 修改 `workflow_planning/validator.py`；
5. 使用 Registry 校验 executable featurizers；
6. 兼容旧字段 `recommended_featurizers`。

---

## 阶段三：改造 Feature Engineering

1. 修改 `feature_engineering/strategy_resolver.py`；
2. 移除或降级 `_AVAILABLE_FEATURIZERS`；
3. 使用 Registry 解析 featurizer；
4. 增加 alias 解析日志；
5. 增加 fallback 逻辑；
6. 输出 ResolvedFeatureStrategy。

---

## 阶段四：前端展示增强

1. 新增 Registry 查询 API；
2. WorkflowPlanPanel 展示 executable / semantic / future featurizers；
3. FeatureEngineeringPanel 展示 resolution_log；
4. 显示 fallback 是否发生。

---

## 阶段五：测试与回归

1. 增加 Registry 单元测试；
2. 增加 Workflow Planning Validator 测试；
3. 增加 Feature Engineering Strategy Resolver 测试；
4. 跑通完整流程：

```text
Task Specification
    ↓
Task Interpretation
    ↓
Dataset Profile
    ↓
Workflow Planning
    ↓
Feature Engineering
```

验证 Feature Engineering 不再出现“全部 unsupported”。

---

# 20. 最终推荐规则

最终系统应遵循以下规则：

```text
Featurizer Registry 是唯一的 featurizer 能力来源。
```

Workflow Planning：

```text
只能输出 Registry 中 available 的 executable_featurizer_id。
```

Feature Engineering：

```text
只执行 Registry 中 available 的 featurizer。
```

LLM：

```text
可以生成 semantic_featurizers 作为解释，但不能创造 executable_featurizer_id。
```

Fallback：

```text
当 LLM 输出不规范时，由 Registry 负责 alias 解析和默认 fallback。
```

后续扩展：

```text
新增 featurizer 时，只需注册到 Registry，再实现对应 Featurizer 类。
```

---

# 21. 总结

本技术方案通过引入 **Featurizer Registry 统一注册中心**，将原本分散在 Workflow Planning 和 Feature Engineering 中的 featurizer 命名、状态、别名、可用性判断统一收敛到一个共享契约层。

改造后的关键链路为：

```text
Featurizer Registry
    ↓
Workflow Planning Prompt Builder
    ↓
Workflow Planning Validator
    ↓
Workflow Plan.feature_strategy.executable_featurizers
    ↓
Feature Engineering Strategy Resolver
    ↓
Featurizer Router
    ↓
Feature Matrix Artifact
```

该方案能够解决当前问题：

```text
LLM 推荐名称 ≠ Feature Engineering 可执行名称
```

并进一步为后续扩展提供稳定基础：

1. 支持 matminer / pymatgen；
2. 支持 structure descriptors；
3. 支持多 featurizer 组合；
4. 支持前端能力展示；
5. 支持 Pipeline Generation 组件映射；
6. 支持 Result Diagnosis 解释特征能力不足问题；
7. 支持 Report Generation 自动描述特征工程方法。

一句话总结：

```text
不要让 LLM 自由命名工程组件；
让 LLM 从 Registry 中选择；
让 Feature Engineering 按 Registry 执行。
```

