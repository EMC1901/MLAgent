# PRD：Workflow Planning、Automated Feature Engineering、Feature Preprocessing 协同重构

> 项目名称：MLAgent — AI-driven Automated Machine Learning Framework for Materials Science  
> 文档类型：产品需求文档 / PRD  
> 适用模块：
> - 模块四：LLM-guided Workflow Planning
> - 模块五：Automated Feature Engineering
> - 模块六：Feature Preprocessing
>
> 重要说明：
> 本次重构 **不改变 Workflow Planning 模块生成完整 WorkflowPlan 的职责**。Workflow Planning 仍需输出完整工作流规划，包括 DataStrategy、FeatureStrategy、ModelStrategy、HPOStrategy、EvaluationStrategy、ValidationStrategy 等内容。  
>
> 本次重构的重点是：
> 1. 增强 WorkflowPlan 中 FeatureStrategy 的能力感知性、材料学针对性和可执行性；
> 2. 增强 Feature Engineering 模块的能力供给、执行反馈和特征质量画像；
> 3. 将 Feature Preprocessing 重构为“LLM 决策 + 系统执行”的模块；
> 4. 将 Feature Preprocessing 能力收敛为当前阶段必须支持的 12 类核心能力；
> 5. 所有 LLM 决策必须给出结构化理由、证据、风险和 fallback；
> 6. 保持模块七及后续模块的兼容性。
>
> 当前系统已经实现 16 个端到端 MVP 模块，模块四负责 LLM 工作流规划，模块五负责特征工程，模块六负责特征预处理，并通过 artifact 链式传递给后续模型搜索、流水线生成、训练评估和最终报告模块。:contentReference[oaicite:0]{index=0}

---

## 1. 背景

MLAgent 当前采用如下端到端管道：

```text
Task Specification
→ Task Interpretation
→ Dataset Profile
→ Workflow Planning
→ Feature Engineering
→ Feature Preprocessing
→ Model Search Context
→ Model Search
→ Pipeline Generation
→ Pipeline Execution
→ Metric Evaluation
→ Result Diagnosis
→ Workflow Refinement
→ Final Pipeline Selection
→ Interpretability Analysis
→ Final Output
````

本 PRD 聚焦其中三个连续模块：

```text
模块四：Workflow Planning
→ 模块五：Feature Engineering
→ 模块六：Feature Preprocessing
```

当前三者已经可以形成基本链路：

```text
Workflow Planning 生成 WorkflowPlan
→ Feature Engineering 根据 FeatureStrategy 生成特征矩阵
→ Feature Preprocessing 生成 model-ready artifact
```

但目前的问题是，三者之间的协同还不够紧密：

1. Workflow Planning 对 Feature Engineering 可执行能力的感知不够强；
2. FeatureStrategy 不够具体、可执行、可解释；
3. Feature Engineering 输出给 Feature Preprocessing 的质量画像不足；
4. Feature Preprocessing 目前更像固定规则执行器，LLM 参与不足；
5. Feature Preprocessing 应该基于真实特征矩阵结果进行二次决策；
6. LLM 的每个决策都需要可解释、可审查、可追踪。

---

## 2. 核心设计思想

本次重构目标不是让 Workflow Planning 只输出 FeatureStrategy，而是让它在保留完整 WorkflowPlan 的基础上，增强 FeatureStrategy 的质量。

重构后的模块关系如下：

```text
Dataset Profile
    ↓
Workflow Planning
    - 生成完整 WorkflowPlan
    - 读取 Feature Engineering Capability Registry
    - 生成能力感知型 FeatureStrategy
    - 给出 high-level PreprocessingIntent
    ↓
Feature Engineering
    - 严格执行 WorkflowPlan.FeatureStrategy
    - 生成 Feature Matrix
    - 生成 Feature Groups
    - 生成 Feature Quality Profile
    - 生成 FeaturePreprocessingDecisionInput
    ↓
Feature Preprocessing
    - 读取 FeaturePreprocessingDecisionInput
    - 读取 Feature Preprocessing Capability Registry
    - LLM 生成 PreprocessingPlan
    - Validator 校验
    - Executor 执行
    - 输出 model-ready artifact
    ↓
Model Search Context
```

---

## 3. 产品目标

### 3.1 总体目标

将模块四、五、六升级为一个紧密协同的材料机器学习特征处理子系统：

```text
完整 WorkflowPlan 生成
+ Feature Engineering 能力感知规划
+ Feature Engineering 严格执行
+ Feature Matrix 质量反馈
+ LLM-guided Feature Preprocessing 再决策
+ Feature Preprocessing 安全执行
```

### 3.2 具体目标

#### 目标一：保留 Workflow Planning 的完整职责

Workflow Planning 仍必须输出完整 WorkflowPlan，包括：

```text
TaskSummary
DataStrategy
FeatureStrategy
PreprocessingIntent
ModelStrategy
HPOStrategy
EvaluationStrategy
ValidationStrategy
ExecutionHints
WorkflowRationale
```

FeatureStrategy 只是 WorkflowPlan 的一个组成部分，不是 WorkflowPlan 的全部。

#### 目标二：增强 FeatureStrategy

WorkflowPlan 中的 FeatureStrategy 必须：

1. 基于 Feature Engineering Capability Registry 生成；
2. 只引用系统当前可执行的 Feature Engineering capability；
3. 结合材料体系、预测目标、输入模态、数据质量和材料学知识；
4. 输出具体、可执行的 feature actions；
5. 每个 feature action 必须包含详细 rationale；
6. 对 rejected feature actions 给出拒绝理由；
7. 给 Feature Preprocessing 提供 high-level intent，但不生成最终 PreprocessingPlan。

#### 目标三：增强 Feature Engineering 执行反馈

Feature Engineering 模块必须：

1. 严格执行 WorkflowPlan.FeatureStrategy；
2. 不自行做高层 feature strategy 决策；
3. 输出 feature matrix artifact；
4. 输出 feature group metadata；
5. 输出 feature quality profile；
6. 输出 action-level execution report；
7. 输出 feature provenance；
8. 构建 FeaturePreprocessingDecisionInput，供模块六 LLM 决策使用。

#### 目标四：引入 LLM-guided Feature Preprocessing

Feature Preprocessing 模块必须：

1. 读取 Feature Engineering 的真实输出；
2. 读取 Feature Preprocessing Capability Registry；
3. 由 LLM 生成结构化 PreprocessingPlan；
4. 每个 preprocessing operation 都必须有 rationale；
5. 系统对 PreprocessingPlan 进行严格校验；
6. 系统执行经过校验的 preprocessing plan；
7. 输出 model-ready artifact、preprocessor artifact、removed features、provenance；
8. 明确防止数据泄漏。

#### 目标五：Feature Preprocess 能力收敛

现阶段 Feature Preprocessing 不追求过多能力，必须聚焦以下 12 类核心能力：

1. 缺失值处理能力；
2. 缺失机制分析能力；
3. 常量、近常量与低信息量特征过滤；
4. 缩放与标准化能力；
5. 偏态分布与数值变换能力；
6. 相关性、共线性与冗余特征处理；
7. 目标泄漏与标识列检测；
8. 特征选择能力；
9. 特征组策略能力；
10. 降维能力；
11. 可解释性保护能力；
12. Artifact 与可重复性能力。

---

## 4. 非目标

本次重构不包括：

1. 不取消 Workflow Planning 的完整 WorkflowPlan 生成功能；
2. 不把 Workflow Planning 改造成只输出 FeatureStrategy 的模块；
3. 不重构模块七 Model Search Context 的整体职责；
4. 不重构模块八 Model Search 的模型搜索职责；
5. 不重构模块九至十六的主流程；
6. 不允许 LLM 生成任意可执行 Python 代码；
7. 不允许 Feature Engineering 或 Feature Preprocessing 执行未注册 capability；
8. 不新增认证、权限、多租户、计费或生产部署能力；
9. 不要求当前阶段实现过宽的材料数据清洗能力，例如单位转换、结构物理约束校验、batch effect 检测等；
10. 不直接修改 Final Output 模块，但需保证 rationale 和 provenance 可被最终报告引用。

---

## 5. 模块边界

---

# 5.1 模块四：LLM-guided Workflow Planning

## 5.1.1 保留原有职责

Workflow Planning 仍然是完整工作流规划模块，必须输出完整 WorkflowPlan。

完整 WorkflowPlan 至少包含：

```text
task_summary
data_strategy
feature_strategy
preprocessing_intent
model_strategy
hpo_strategy
evaluation_strategy
validation_strategy
workflow_rationale
```

## 5.1.2 本次增强职责

Workflow Planning 需要增强 FeatureStrategy：

```text
FeatureStrategy = Capability-aware Feature Engineering Strategy
```

它需要：

1. 读取 Feature Engineering Capability Registry；
2. 知道 Feature Engineering 当前全部可执行能力；
3. 根据材料任务和数据情况选择特征工程策略；
4. 输出可执行 feature actions；
5. 每个 feature action 都必须有 rationale；
6. 输出 rejected feature actions 及拒绝理由；
7. 输出 high-level PreprocessingIntent；
8. 不输出最终 PreprocessingPlan。

## 5.1.3 Workflow Planning 不负责

Workflow Planning 不负责：

1. 不执行 Feature Engineering；
2. 不读取真实生成后的 Feature Matrix；
3. 不执行 Feature Preprocessing；
4. 不生成最终 PreprocessingPlan；
5. 不生成 model-ready artifact；
6. 不替代模块六中的 LLM preprocessing decision；
7. 不修改后续模块七、八、九的职责。

---

# 5.2 模块五：Automated Feature Engineering

## 5.2.1 模块定位

Feature Engineering 是：

```text
Feature Engineering Capability Provider + Feature Engineering Executor
```

## 5.2.2 模块负责

Feature Engineering 负责：

1. 维护 Feature Engineering Capability Registry；
2. 接收 WorkflowPlan.FeatureStrategy；
3. 校验 FeatureStrategy 中的 feature actions；
4. 严格执行 selected feature actions；
5. 执行 fallback actions；
6. 生成 feature matrix artifact；
7. 生成 feature groups；
8. 生成 feature quality profile；
9. 生成 execution report；
10. 生成 feature provenance；
11. 构建 FeaturePreprocessingDecisionInput。

## 5.2.3 模块不负责

Feature Engineering 不负责：

1. 不生成完整 WorkflowPlan；
2. 不自行决定高层 feature strategy；
3. 不修改 ModelStrategy、HPOStrategy、EvaluationStrategy；
4. 不执行 Feature Preprocessing；
5. 不选择模型；
6. 不执行训练；
7. 不计算最终模型指标。

---

# 5.3 模块六：Feature Preprocessing

## 5.3.1 模块定位

Feature Preprocessing 重构为：

```text
LLM-guided Feature Preprocessing Planner
+ Safe Feature Preprocessing Executor
```

模块六内部拆分为：

```text
6A. Preprocessing Planning
6B. Preprocessing Execution
```

## 5.3.2 模块负责

Feature Preprocessing 负责：

1. 读取 FeaturePreprocessingDecisionInput；
2. 读取 Feature Preprocessing Capability Registry；
3. 构建 LLM preprocessing context；
4. 调用 LLM 生成 PreprocessingPlan；
5. 校验 PreprocessingPlan；
6. 执行 PreprocessingPlan；
7. 生成 model-ready artifact；
8. 生成 preprocessor artifact；
9. 输出 removed features；
10. 输出 retained feature groups；
11. 输出 preprocessing provenance；
12. 构建 model_search_context_input；
13. 保证数据泄漏防护。

## 5.3.3 模块不负责

Feature Preprocessing 不负责：

1. 不生成材料特征；
2. 不修改 WorkflowPlan 的完整策略；
3. 不选择模型；
4. 不执行模型训练；
5. 不计算模型评估指标；
6. 不执行未注册 preprocessing operation；
7. 不允许 LLM 生成自定义执行代码。

---

## 6. 后端需求

---

# 6.1 Capability Registry 需求

## 6.1.1 Feature Engineering Capability Registry

### 目标

让 Workflow Planning LLM 在生成完整 WorkflowPlan 时，明确知道 Feature Engineering 模块当前可执行能力。

### Capability 字段

每个 Feature Engineering capability 至少包含：

```json
{
  "capability_id": "string",
  "display_name": "string",
  "status": "available | planned | disabled | experimental",
  "feature_family": "composition | structure | descriptor | hybrid | metadata",
  "input_modalities": ["composition", "structure", "descriptor_table"],
  "supported_task_types": ["regression", "classification"],
  "required_input_columns": ["formula"],
  "optional_input_columns": [],
  "output_feature_groups": ["string"],
  "material_use_cases": ["formation_energy", "band_gap", "elasticity", "stability"],
  "dependencies": ["pymatgen", "matminer"],
  "estimated_cost": "low | medium | high",
  "known_limitations": [],
  "fallback_capability_ids": [],
  "version": "string"
}
```

### 规则

1. 只有 `available` capability 可作为主执行 action；
2. `planned` capability 可以被 LLM 作为不可用能力提及，但不能进入 required 或 recommended actions；
3. `disabled` capability 不应暴露给 LLM 作为候选；
4. Registry 必须支持按 input modality、task type、feature family、status 过滤；
5. Registry 必须支持 prompt-safe serialization；
6. WorkflowPlan 必须保存 registry snapshot version。

---

## 6.1.2 Feature Preprocessing Capability Registry

### 目标

让 Feature Preprocessing LLM 明确知道模块六当前支持哪些预处理能力。

### Capability 字段

每个 preprocessing capability 至少包含：

```json
{
  "capability_id": "string",
  "display_name": "string",
  "capability_group": "missing_value_handling",
  "operation_type": "imputation | analysis | filtering | scaling | transformation | redundancy_filter | leakage_detection | feature_selection | group_policy | dimensionality_reduction | lineage | artifact_tracking",
  "status": "available | planned | disabled | experimental",
  "supported_feature_types": ["numeric", "categorical", "boolean"],
  "supported_feature_groups": ["composition", "structure", "descriptor", "metadata", "generated"],
  "requires_target": false,
  "fit_scope": "dataset_profile_only | train_only | fold_only",
  "allowed_pipeline_positions": ["before_scaling", "after_imputation"],
  "parameters_schema": {},
  "default_parameters": {},
  "risk_notes": [],
  "fallback_capability_ids": [],
  "version": "string"
}
```

### 规则

1. LLM 只能选择 `available` preprocessing capability；
2. 所有 operation 必须来自 Registry；
3. 所有需要学习数据分布参数的 operation 必须声明 fit_scope；
4. target-aware operation 默认禁用，除非明确 fold-safe；
5. 所有 operation 必须有 rationale；
6. 执行器只执行经过 validator 校验的 operation；
7. Registry snapshot 必须被持久化。

---

# 6.2 Workflow Planning 后端需求

## 6.2.1 输入

Workflow Planning 继续使用现有输入：

```text
TaskSpecification
TaskInterpretation
DatasetProfile
```

新增输入：

```text
FeatureEngineeringCapabilityRegistrySnapshot
```

## 6.2.2 输出

Workflow Planning 仍输出完整 WorkflowPlan。

建议增强后的 WorkflowPlan 结构如下：

```json
{
  "workflow_plan": {
    "task_summary": {},
    "data_strategy": {},
    "feature_strategy": {
      "strategy_id": "string",
      "strategy_version": "string",
      "input_modality_assessment": {
        "detected_modalities": ["composition"],
        "usable_modalities": ["composition"],
        "unusable_modalities": [],
        "rationale": "string"
      },
      "selected_feature_actions": [
        {
          "action_id": "string",
          "capability_id": "string",
          "priority": "required | recommended | optional | fallback",
          "input_columns": ["formula"],
          "parameters": {},
          "output_feature_group": "composition_elemental_statistics",
          "decision_rationale": {
            "reason": "string",
            "evidence": [],
            "material_science_basis": "string",
            "expected_benefit": "string",
            "risk": "string",
            "fallback": "string"
          }
        }
      ],
      "rejected_feature_actions": [
        {
          "capability_id": "string",
          "reason": "string",
          "evidence": []
        }
      ],
      "fallback_strategy": {
        "fallback_actions": [],
        "trigger_conditions": []
      },
      "feature_group_expectations": [
        {
          "feature_group": "string",
          "expected_signal": "string",
          "known_limitations": "string"
        }
      ]
    },
    "preprocessing_intent": {
      "intent_id": "string",
      "high_level_goals": [],
      "risks_to_check_after_feature_engineering": [],
      "non_final_notes": "Final executable preprocessing decisions will be made by Feature Preprocessing after Feature Engineering output is available."
    },
    "model_strategy": {},
    "hpo_strategy": {},
    "evaluation_strategy": {},
    "validation_strategy": {},
    "workflow_rationale": {
      "overall_reasoning_summary": "string",
      "key_assumptions": [],
      "known_risks": []
    }
  }
}
```

## 6.2.3 Workflow Planning Prompt 要求

Prompt 必须明确：

```text
You must generate a complete WorkflowPlan.
Do not only generate FeatureStrategy.
FeatureStrategy is one section of the full WorkflowPlan.
Feature Preprocessing will make final preprocessing decisions after Feature Engineering output is available.
```

Prompt 必须包含：

1. TaskSpecification；
2. TaskInterpretation；
3. DatasetProfile；
4. Feature Engineering Capability Registry；
5. 完整 WorkflowPlan schema；
6. FeatureStrategy 子 schema；
7. Rationale schema；
8. 规则：FeatureStrategy 只能引用 available capabilities；
9. 规则：PreprocessingIntent 只输出高层目标；
10. 规则：不能编造系统不支持的 capability。

## 6.2.4 Validator 要求

WorkflowPlan Validator 必须校验：

### 完整 WorkflowPlan 校验

* `task_summary` 存在；
* `data_strategy` 存在；
* `feature_strategy` 存在；
* `model_strategy` 存在；
* `hpo_strategy` 存在；
* `evaluation_strategy` 存在；
* `validation_strategy` 存在。

### FeatureStrategy 校验

* capability_id 存在；
* capability status 为 available；
* input modality 匹配；
* required input columns 存在；
* selected feature action 有 decision_rationale；
* rationale 包含 reason、evidence、material_science_basis、expected_benefit、risk、fallback；
* rejected feature action 有 reason；
* planned capability 不得作为 required 或 recommended action。

### PreprocessingIntent 校验

* 只能包含 high-level goals；
* 不能指定最终 column-level operation；
* 不能指定最终 executable PreprocessingPlan；
* 不能替代模块六的 LLM PreprocessingPlan。

---

# 6.3 Feature Engineering 后端需求

## 6.3.1 输入

```text
task_id
WorkflowPlan.feature_strategy
DatasetProfile raw data reference
TaskSpecification
TaskInterpretation
FeatureEngineeringCapabilityRegistry
```

## 6.3.2 执行原则

Feature Engineering 必须：

1. 严格执行 WorkflowPlan.FeatureStrategy；
2. 不自行生成高层 FeatureStrategy；
3. 只执行 Registry 中 available capability；
4. 允许执行 FeatureStrategy 中定义的 fallback；
5. 每个 action 单独记录执行结果；
6. required action 全部失败时模块失败；
7. optional action 失败时可 completed_with_warnings；
8. 不执行 Feature Preprocessing operation；
9. 不修改完整 WorkflowPlan 的其他策略。

## 6.3.3 输出

FeatureEngineeringResponse 增强为：

```json
{
  "feature_engineering_id": "string",
  "task_id": "string",
  "status": "completed | completed_with_warnings | failed",
  "workflow_plan_id": "string",
  "executed_feature_strategy_id": "string",
  "feature_matrix_artifact": {
    "path": "string",
    "format": "parquet",
    "row_count": 1000,
    "column_count": 128,
    "artifact_hash": "string"
  },
  "feature_groups": [
    {
      "group_id": "string",
      "source_action_id": "string",
      "capability_id": "string",
      "feature_family": "composition | structure | descriptor | metadata",
      "feature_names": [],
      "feature_count": 50,
      "semantic_description": "string"
    }
  ],
  "feature_quality_profile": {
    "global_summary": {
      "row_count": 1000,
      "feature_count": 128,
      "numeric_feature_count": 128,
      "categorical_feature_count": 0,
      "missing_value_ratio": 0.03,
      "constant_feature_count": 2,
      "near_constant_feature_count": 4,
      "low_information_feature_count": 5,
      "high_missing_feature_count": 3,
      "high_correlation_pair_count": 120,
      "high_skewness_feature_count": 20
    },
    "per_feature_summary": [],
    "per_group_summary": [],
    "quality_warnings": []
  },
  "execution_report": {
    "action_results": [
      {
        "action_id": "string",
        "capability_id": "string",
        "status": "success | failed | fallback_used | skipped",
        "generated_feature_count": 50,
        "warnings": [],
        "error_message": null,
        "fallback_action_id": null
      }
    ]
  },
  "feature_provenance": {
    "registry_snapshot_version": "string",
    "input_artifact_hash": "string",
    "featurizer_versions": {},
    "dependency_versions": {},
    "created_at": "datetime"
  },
  "feature_preprocessing_decision_input": {}
}
```

## 6.3.4 FeaturePreprocessingDecisionInput

Feature Engineering 必须生成模块六专用输入：

```json
{
  "task_context": {
    "task_type": "regression",
    "prediction_target": "string",
    "evaluation_metric": "string",
    "user_priority": []
  },
  "dataset_context": {
    "row_count": 1000,
    "target_column": "string",
    "input_modalities": [],
    "data_quality_summary": {}
  },
  "workflow_context": {
    "workflow_plan_id": "string",
    "feature_strategy_summary": {},
    "preprocessing_intent": {}
  },
  "feature_matrix_context": {
    "artifact_path": "string",
    "row_count": 1000,
    "feature_count": 128,
    "feature_groups": [],
    "feature_quality_profile": {}
  },
  "execution_context": {
    "feature_engineering_status": "completed",
    "warnings": [],
    "failed_actions": [],
    "fallback_used": []
  },
  "known_preprocessing_risks": [
    "missing_values",
    "high_collinearity",
    "skewed_distribution",
    "low_information_features",
    "possible_leakage"
  ]
}
```

---

# 6.4 Feature Preprocessing 后端需求

## 6.4.1 输入

```text
task_id
FeatureEngineering.feature_preprocessing_decision_input
FeaturePreprocessingCapabilityRegistry
WorkflowPlan.preprocessing_intent
```

说明：

```text
WorkflowPlan.preprocessing_intent 只能作为高层参考。
最终可执行 PreprocessingPlan 必须由模块六在看到 Feature Engineering 输出后生成。
```

## 6.4.2 内部流程

```text
1. build_context
2. load FeaturePreprocessingDecisionInput
3. load FeaturePreprocessingCapabilityRegistry
4. build LLM preprocessing prompt
5. call LLM
6. parse response
7. validate PreprocessingPlan
8. normalize PreprocessingPlan
9. execute PreprocessingPlan
10. save model-ready artifacts
11. save preprocessor artifacts
12. build model_search_context_input
13. persist
```

---

## 6.4.3 Feature Preprocessing 必须支持的 12 类能力

---

### 能力一：缺失值处理能力

#### 必须支持的 capability

```text
missing_rate_filter
median_imputer
mean_imputer
most_frequent_imputer
constant_imputer
missing_indicator
groupwise_imputer
```

#### 说明

模块六必须能够处理 Feature Engineering 输出中的缺失值问题，包括：

1. 删除缺失率过高的特征；
2. 对数值特征进行 mean / median 插补；
3. 对类别特征进行 most frequent 插补；
4. 对特殊场景使用 constant 插补；
5. 为缺失值生成 missing indicator；
6. 按 feature group 使用不同插补策略。

#### LLM 决策要求

LLM 需要说明：

* 为什么选择该插补策略；
* 哪些 feature group 使用该策略；
* 缺失率证据是什么；
* 是否需要 missing indicator；
* 该策略的风险；
* fallback 是什么。

---

### 能力二：缺失机制分析能力

#### 必须支持的 capability

```text
missingness_profile_analyzer
missing_by_feature_group_analyzer
missing_pattern_analyzer
missing_target_correlation_checker
missing_not_at_random_flagger
```

#### 说明

模块六不仅要填补缺失值，还要分析缺失机制。

需要分析：

1. 全局缺失率；
2. feature-level 缺失率；
3. feature group 缺失率；
4. 缺失模式是否集中在某些特征组；
5. 缺失是否与 target 分布存在明显关联；
6. 是否存在 Missing Not At Random 风险。

#### 输出要求

缺失机制分析结果应进入：

```text
feature_preprocessing_plan.global_policy
operation_sequence evidence
preprocessing_execution_report
warnings_for_downstream
```

---

### 能力三：常量、近常量与低信息量特征过滤

#### 必须支持的 capability

```text
constant_feature_filter
near_constant_feature_filter
low_variance_filter
low_unique_ratio_filter
single_value_dominance_filter
```

#### 说明

模块六必须过滤低信息量特征，包括：

1. 常量特征；
2. 近常量特征；
3. 低方差特征；
4. 唯一值比例过低的特征；
5. 单一值占比过高的特征。

#### LLM 决策要求

LLM 需要说明：

* 删除阈值；
* 阈值依据；
* 删除特征数量；
* 是否影响某些 feature group；
* 对可解释性的影响；
* 是否保留某些材料学重要但低方差的特征。

---

### 能力四：缩放与标准化能力

#### 必须支持的 capability

```text
standard_scaler
minmax_scaler
robust_scaler
maxabs_scaler
no_scaling
groupwise_scaler
model_family_aware_scaling_policy
```

#### 说明

模块六必须支持多种缩放策略，并允许按 feature group 或模型族选择缩放方式。

典型策略：

```text
linear_model_variant:
  standard_scaler or robust_scaler

tree_model_variant:
  no_scaling

kernel_or_distance_based_variant:
  robust_scaler or standard_scaler

descriptor_heavy_variant:
  robust_scaler
```

#### LLM 决策要求

LLM 需要说明：

* 为什么需要缩放；
* 哪些特征组需要缩放；
* 哪些模型族依赖缩放；
* 为什么选择 standard / robust / minmax / no_scaling；
* 缩放是否可能降低可解释性；
* fallback 是什么。

---

### 能力五：偏态分布与数值变换能力

#### 必须支持的 capability

```text
skewness_analyzer
log_transform
log1p_transform
signed_log_transform
power_transform_yeo_johnson
quantile_transform_normal
quantile_transform_uniform
auto_skewness_transform_selector
```

#### 说明

Feature Engineering 生成的材料特征可能存在强偏态。模块六必须支持对偏态分布进行分析和变换。

适用场景：

1. 特征分布长尾；
2. 极端值较多；
3. 数值尺度跨度大；
4. 线性模型或距离模型受偏态影响明显。

#### 约束

1. log transform 只能用于正值或经过安全处理的特征；
2. signed log 可用于包含负值的偏态特征；
3. quantile transform 必须 fold-safe；
4. 所有 fit 型 transformation 不得在全量数据上 fit 后用于 CV 评估。

---

### 能力六：相关性、共线性与冗余特征处理

#### 必须支持的 capability

```text
pearson_correlation_filter
spearman_correlation_filter
correlation_pair_reporter
variance_inflation_factor_filter
hierarchical_correlation_clustering
representative_feature_selector
feature_group_redundancy_analyzer
```

#### 说明

材料特征经常高度相关，尤其是 matminer composition features、元素统计特征、descriptor 特征等。

模块六必须支持：

1. 计算 Pearson / Spearman 相关性；
2. 找出高相关特征对；
3. 按阈值过滤冗余特征；
4. 对相关簇保留代表特征；
5. 对线性模型相关场景做 VIF 过滤；
6. 按 feature group 分析冗余程度。

#### LLM 决策要求

LLM 需要说明：

* 使用 Pearson 还是 Spearman；
* 相关性阈值；
* 如何选择保留特征；
* 是否优先保留可解释性更强的特征；
* 是否避免删除材料学关键特征；
* 对后续解释分析的影响。

---

### 能力七：目标泄漏与标识列检测

#### 必须支持的 capability

```text
target_column_excluder
id_column_dropper
metadata_column_detector
duplicate_target_column_detector
target_name_similarity_checker
target_correlation_leakage_checker
basic_leakage_checker
leakage_risk_report_builder
```

#### 说明

模块六必须防止目标泄漏和无意义标识列进入模型。

需要检测：

1. target column 是否混入 feature matrix；
2. ID、样本编号、文件名、数据库编号等列；
3. 与 target 名称高度相似的列；
4. target 的单位转换版本；
5. 与 target 几乎完全相关的可疑列；
6. 后验测量字段或结果摘要字段。

#### 强制规则

1. target column 必须排除；
2. ID column 默认排除；
3. 高泄漏风险列默认排除或 flag_for_review；
4. 所有泄漏风险必须进入 execution_report 和 warnings_for_downstream。

---

### 能力八：特征选择能力

#### 必须支持的 capability

```text
variance_threshold_selector
missing_rate_selector
correlation_selector
mutual_information_selector
f_regression_selector
f_classif_selector
lasso_selector
elastic_net_selector
tree_importance_selector
recursive_feature_elimination
sequential_feature_selector
max_feature_count_limiter
```

#### 说明

材料机器学习常见小样本、高维特征问题。模块六必须支持多种特征选择方式。

特征选择分为三类：

```text
无监督特征选择：
  missing_rate_selector
  variance_threshold_selector
  correlation_selector

监督特征选择：
  mutual_information_selector
  f_regression_selector
  f_classif_selector
  lasso_selector
  elastic_net_selector
  tree_importance_selector

包装式选择：
  recursive_feature_elimination
  sequential_feature_selector
```

#### 数据泄漏规则

1. 监督特征选择必须 fold-safe；
2. 不能在全量数据上 fit 后用于 CV 评估；
3. 如果当前执行器不支持 fold 内监督选择，则该 capability 只能输出 recommendation，不能生成 fitted artifact；
4. PreprocessingPlan 必须标记 target-aware selection 是否启用。

---

### 能力九：特征组策略能力

#### 必须支持的 capability

```text
feature_group_allowlist
feature_group_denylist
feature_group_priority_policy
feature_group_specific_pipeline
feature_group_quality_ranker
feature_group_preservation_policy
```

#### 说明

Feature Engineering 输出应包含 feature groups。模块六必须支持按 feature group 制定预处理策略。

典型 feature groups：

```text
composition_stoichiometry
composition_elemental_statistics
descriptor_numeric
structure_basic
structure_symmetry
metadata
generated
```

模块六需要支持：

1. 按 feature group 使用不同插补策略；
2. 按 feature group 使用不同缩放策略；
3. 按 feature group 设置保留优先级；
4. 对低质量 feature group 进行过滤；
5. 对可解释性重要 feature group 进行保护；
6. 输出 retained / removed feature group 列表。

---

### 能力十：降维能力

#### 必须支持的 capability

```text
pca_transform
incremental_pca_transform
truncated_svd_transform
feature_group_pca
dimension_reduction_policy_builder
```

#### 说明

模块六必须支持降维能力，但降维应谨慎使用，因为会降低可解释性。

适用场景：

1. 特征维度远大于样本数；
2. descriptor 特征高度冗余；
3. 线性模型或距离模型受高维影响；
4. 需要生成 compact variant；
5. 某些 feature group 内部高度相关。

#### 约束

1. 降维必须 fold-safe；
2. 降维后的 artifact 必须保留 lineage；
3. 降维 variant 不能替代所有可解释性保留 variant；
4. LLM 必须说明为什么使用降维；
5. LLM 必须说明降维对可解释性的影响。

---

### 能力十一：可解释性保护能力

#### 必须支持的 capability

```text
interpretability_preserving_selector
feature_name_lineage_tracker
transformed_feature_name_generator
feature_group_lineage_tracker
post_preprocessing_explainability_reporter
```

#### 说明

后续 Interpretability Analysis 依赖可追踪特征名和 feature group 信息。模块六必须保证预处理后仍能追踪：

1. 原始特征名；
2. 转换后特征名；
3. 所属 feature group；
4. 来源 feature action；
5. 是否被插补；
6. 是否被缩放；
7. 是否被数值变换；
8. 是否被特征选择保留；
9. 是否进入降维组件；
10. 是否可以直接解释。

#### 输出要求

必须生成：

```text
feature_lineage_map
feature_group_lineage_map
transformed_feature_name_map
explainability_preservation_report
```

---

### 能力十二：Artifact 与可重复性能力

#### 必须支持的 capability

```text
preprocessing_plan_snapshot
preprocessing_registry_snapshot
input_feature_artifact_hash
output_artifact_hash
operation_parameter_snapshot
fitted_statistics_summary
removed_feature_report
retained_feature_report
random_seed_recorder
dependency_version_recorder
```

#### 说明

Feature Preprocessing 必须保证结果可复现、可审计、可追踪。

必须记录：

1. 输入 feature artifact hash；
2. 输出 model-ready artifact hash；
3. preprocessing plan snapshot；
4. registry snapshot；
5. operation 参数；
6. fitted statistics；
7. removed features；
8. retained features；
9. random seed；
10. dependency versions；
11. created_at；
12. artifact usage。

---

## 6.4.4 PreprocessingPlan 结构

```json
{
  "preprocessing_plan": {
    "plan_id": "string",
    "plan_version": "string",
    "global_policy": {
      "leakage_prevention": {
        "fit_transform_scope": "train_fold_only",
        "target_column_excluded": true,
        "id_columns_excluded": true,
        "target_aware_selection_allowed": false,
        "rationale": "string"
      },
      "variant_strategy": {
        "mode": "single | model_family_specific | multiple_variants",
        "rationale": "string"
      }
    },
    "capability_groups_used": [
      "missing_value_handling",
      "missingness_analysis",
      "low_information_filtering",
      "scaling_normalization",
      "distribution_transformation",
      "correlation_collinearity",
      "leakage_detection",
      "feature_selection",
      "feature_group_policy",
      "dimensionality_reduction",
      "interpretability_preservation",
      "artifact_reproducibility"
    ],
    "column_policies": [
      {
        "column_name": "string",
        "action": "keep | drop | transform | flag_for_review",
        "reason": "string",
        "evidence": [],
        "risk": "string"
      }
    ],
    "feature_group_policies": [
      {
        "feature_group": "string",
        "policy": "preserve | filter | transform | reduce_dimension | drop",
        "operations": [
          {
            "operation_id": "string",
            "capability_id": "string",
            "parameters": {},
            "execution_scope": "dataset_profile_only | train_only | fold_only",
            "decision_rationale": {
              "reason": "string",
              "evidence": [],
              "expected_benefit": "string",
              "risk": "string",
              "fallback": "string"
            }
          }
        ]
      }
    ],
    "operation_sequence": [
      {
        "step_order": 1,
        "operation_id": "string",
        "capability_id": "string",
        "target_feature_groups": [],
        "target_columns": [],
        "parameters": {},
        "execution_scope": "dataset_profile_only | train_only | fold_only",
        "decision_rationale": {
          "reason": "string",
          "evidence": [],
          "expected_benefit": "string",
          "risk": "string",
          "fallback": "string"
        }
      }
    ],
    "model_family_specific_notes": [
      {
        "model_family": "linear_model",
        "preprocessing_needs": [],
        "rationale": "string"
      }
    ],
    "rejected_operations": [
      {
        "capability_id": "string",
        "reason": "string",
        "evidence": []
      }
    ],
    "warnings_for_downstream": []
  }
}
```

---

## 6.4.5 PreprocessingPlan Validator 要求

Validator 必须校验：

1. capability_id 存在；
2. capability status 为 available；
3. parameters 符合 schema；
4. feature group 存在；
5. target column 被排除；
6. ID column 被排除或 flag；
7. operation 顺序合法；
8. 每个 operation 有 decision_rationale；
9. rationale 包含 reason、evidence、expected_benefit、risk、fallback；
10. fit 型 transformer 不得在全量数据上为 CV 评估 fit；
11. target-aware selection 默认禁用；
12. target-aware selection 若启用，必须 fold_only；
13. 降维必须 fold-safe；
14. lineage 必须可追踪；
15. 不允许 LLM 自定义代码；
16. 不允许路径穿越；
17. 不允许未注册 operation。

---

## 6.4.6 数据泄漏防护要求

P0 强制规则：

```text
任何会学习数据分布参数的 operation，例如 imputer、scaler、feature selector、PCA，
不得在全量数据上 fit 后直接用于交叉验证评估。
```

实现要求：

1. 模块六可以生成 preprocessing plan；
2. 模块六可以生成 pipeline template；
3. Pipeline Execution 应在每个 fold 内 fit preprocessing pipeline；
4. 模块六可以生成 preview artifact，但必须标记 `usage = preview`；
5. preview artifact 不得用于正式 CV 评分；
6. full-data fitted preprocessor 只能用于 final_training；
7. 所有 artifact 必须标记 usage。

---

## 6.4.7 FeaturePreprocessingResponse 输出

```json
{
  "feature_preprocessing_id": "string",
  "task_id": "string",
  "status": "completed | completed_with_warnings | failed",
  "preprocessing_plan": {},
  "execution_report": {
    "operation_results": [
      {
        "operation_id": "string",
        "capability_id": "string",
        "capability_group": "string",
        "status": "success | failed | skipped | fallback_used",
        "affected_features": [],
        "removed_features": [],
        "warnings": [],
        "error_message": null
      }
    ]
  },
  "model_ready_artifacts": [
    {
      "artifact_id": "string",
      "variant_name": "default",
      "path": "string",
      "usage": "preview | fold_safe_template | final_training",
      "row_count": 1000,
      "feature_count": 80,
      "artifact_hash": "string"
    }
  ],
  "preprocessor_artifacts": [
    {
      "artifact_id": "string",
      "variant_name": "default",
      "path": "string",
      "usage": "pipeline_template | fitted_preview | final_training",
      "artifact_hash": "string"
    }
  ],
  "removed_features": [
    {
      "feature_name": "string",
      "reason": "high_missing_rate",
      "evidence": "missing_ratio=0.72",
      "source_feature_group": "descriptor_numeric"
    }
  ],
  "retained_feature_groups": [],
  "feature_lineage_map": {},
  "feature_group_lineage_map": {},
  "explainability_preservation_report": {},
  "preprocessing_provenance": {
    "registry_snapshot_version": "string",
    "input_feature_artifact_hash": "string",
    "output_artifact_hash": "string",
    "operation_parameter_snapshot": {},
    "fitted_statistics_summary": {},
    "dependency_versions": {},
    "random_seed": null,
    "created_at": "datetime"
  },
  "model_search_context_input": {}
}
```

---

## 7. API 需求

---

# 7.1 Workflow Planning API

保留现有端点：

```text
POST /api/workflow-plans/{task_id}
GET /api/workflow-plans/{id}
GET /api/workflow-plans/by-task/{task_id}
POST /api/workflow-plans/{task_id}/rerun
```

新增端点：

```text
GET /api/workflow-plans/{id}/feature-strategy
GET /api/workflow-plans/{id}/feature-strategy-rationale
GET /api/workflow-plans/{id}/preprocessing-intent
```

说明：

这些端点只读取完整 WorkflowPlan 的子结构，不改变 WorkflowPlan 的完整性。

---

# 7.2 Feature Engineering API

保留现有端点：

```text
POST /api/feature-engineerings/{task_id}
GET /api/feature-engineerings/{id}
GET /api/feature-engineerings/by-task/{task_id}
POST /api/feature-engineerings/{task_id}/rerun
GET /api/feature-engineerings/{id}/preview
```

新增端点：

```text
GET /api/feature-engineering/capabilities
GET /api/feature-engineerings/{id}/execution-report
GET /api/feature-engineerings/{id}/feature-groups
GET /api/feature-engineerings/{id}/quality-profile
GET /api/feature-engineerings/{id}/preprocessing-decision-input
GET /api/feature-engineerings/{id}/provenance
```

---

# 7.3 Feature Preprocessing API

保留现有端点：

```text
POST /api/feature-preprocessings/{task_id}
GET /api/feature-preprocessings/{id}
GET /api/feature-preprocessings/by-task/{task_id}
POST /api/feature-preprocessings/{task_id}/rerun
```

新增端点：

```text
GET /api/feature-preprocessing/capabilities
POST /api/feature-preprocessings/{task_id}/plan
POST /api/feature-preprocessings/{task_id}/execute
GET /api/feature-preprocessings/{id}/plan
GET /api/feature-preprocessings/{id}/rationale
GET /api/feature-preprocessings/{id}/execution-report
GET /api/feature-preprocessings/{id}/removed-features
GET /api/feature-preprocessings/{id}/feature-lineage
GET /api/feature-preprocessings/{id}/artifact-manifest
GET /api/feature-preprocessings/{id}/provenance
```

---

## 8. 前端需求

---

# 8.1 WorkflowPlanningPanel 增强

WorkflowPlanningPanel 仍展示完整 WorkflowPlan，不得只展示 FeatureStrategy。

页面结构：

```text
Workflow Plan
├── Task Summary
├── Data Strategy
├── Feature Strategy
│   ├── Input Modality Assessment
│   ├── Selected Feature Actions
│   ├── Rejected Feature Actions
│   ├── Fallback Strategy
│   └── Feature Strategy Rationales
├── Preprocessing Intent
├── Model Strategy
├── HPO Strategy
├── Evaluation Strategy
├── Validation Strategy
└── Overall Workflow Rationale
```

## 8.1.1 Feature Strategy 展示

每个 selected feature action 展示：

* capability name；
* status；
* feature family；
* priority；
* input columns；
* output feature group；
* reason；
* evidence；
* material science basis；
* expected benefit；
* risk；
* fallback。

## 8.1.2 Preprocessing Intent 展示

PreprocessingIntent 区域必须明确显示：

```text
Final preprocessing decisions will be made after Feature Engineering output is available.
```

---

# 8.2 FeatureEngineeringPanel 增强

页面结构：

```text
Feature Engineering
├── Input Feature Strategy
├── Planned Feature Actions
├── Execution Results
├── Feature Matrix Summary
├── Feature Groups
├── Feature Quality Profile
├── Warnings and Failed Actions
├── Provenance
└── Output to Feature Preprocessing
```

## 8.2.1 Execution Results

每个 action 展示：

* action_id；
* capability_id；
* status；
* generated feature count；
* fallback used；
* warnings；
* error message。

## 8.2.2 Feature Matrix Summary

展示：

* row count；
* feature count；
* numeric feature count；
* categorical feature count；
* missing ratio；
* constant feature count；
* near constant feature count；
* low information feature count；
* high correlation pair count；
* high skewness feature count；
* artifact hash。

## 8.2.3 Feature Quality Profile

展示：

* global summary；
* per group summary；
* high missing features；
* near constant features；
* low information features；
* high skewness features；
* high correlation pairs；
* quality warnings。

---

# 8.3 FeaturePreprocessingPanel 增强

页面结构：

```text
Feature Preprocessing
├── Input Feature Quality Summary
├── LLM Preprocessing Plan
├── Decision Rationales
├── Leakage Prevention Summary
├── Capability Groups Used
├── Operation Sequence
├── Feature Group Policies
├── Column Policies
├── Execution Results
├── Removed Features
├── Feature Lineage
├── Explainability Preservation Report
├── Model-ready Artifacts
├── Preprocessor Artifacts
└── Provenance
```

## 8.3.1 LLM Preprocessing Plan

展示：

* plan id；
* plan version；
* global policy；
* variant strategy；
* capability groups used；
* model-family-specific notes；
* warnings for downstream。

## 8.3.2 Decision Rationales

每个 operation 展示：

* operation name；
* capability id；
* capability group；
* target feature groups；
* parameters；
* execution scope；
* reason；
* evidence；
* expected benefit；
* risk；
* fallback。

## 8.3.3 Leakage Prevention Summary

必须高亮展示：

* target excluded；
* ID columns excluded；
* fit scope；
* target-aware selection 是否启用；
* fold-safe mode 是否启用；
* leakage warnings。

## 8.3.4 Removed Features

表格字段：

| Feature | Reason | Evidence | Source Group | Operation |
| ------- | ------ | -------- | ------------ | --------- |

## 8.3.5 Feature Lineage

展示：

* original feature name；
* transformed feature name；
* source feature group；
* source feature action；
* transformations applied；
* retained / removed；
* explainability status。

---

## 9. LLM 决策要求

---

# 9.1 FeatureStrategy 决策要求

Workflow Planning 中每个 selected feature action 必须包含：

```json
{
  "reason": "为什么选择该特征工程动作",
  "evidence": ["来自任务、数据、Registry 或材料学知识的证据"],
  "material_science_basis": "材料学依据",
  "expected_benefit": "预期收益",
  "risk": "潜在风险",
  "fallback": "失败或不适用时的替代方案"
}
```

---

# 9.2 PreprocessingPlan 决策要求

Feature Preprocessing 中每个 operation 必须包含：

```json
{
  "reason": "为什么选择该预处理操作",
  "evidence": ["来自 Feature Quality Profile 或 FeaturePreprocessingDecisionInput 的证据"],
  "expected_benefit": "预期收益",
  "risk": "潜在风险",
  "fallback": "失败或不适用时的替代方案"
}
```

---

# 9.3 LLM 不允许行为

LLM 不允许：

```text
1. 在 Workflow Planning 中只生成 FeatureStrategy 而不生成完整 WorkflowPlan；
2. 引用不存在的 Feature Engineering capability；
3. 引用不存在的 Feature Preprocessing capability；
4. 把 planned capability 作为 required action；
5. 编造系统不支持的 featurizer；
6. 编造系统不支持的 preprocessing operation；
7. 生成自定义代码；
8. 让执行模块自行决定核心策略；
9. 忽略数据泄漏风险；
10. 对 target column 做普通 feature transform；
11. 对全量数据 fit transformer 后用于 CV 评估；
12. 丢失 feature lineage。
```

---

## 10. 数据结构兼容性

---

# 10.1 WorkflowPlan 兼容性

不得删除现有 WorkflowPlan 主要字段。

新增字段建议：

```text
feature_strategy.selected_feature_actions
feature_strategy.rejected_feature_actions
feature_strategy.feature_group_expectations
feature_strategy.rationales
feature_engineering_registry_snapshot
preprocessing_intent
workflow_rationale
```

---

# 10.2 FeatureEngineering 兼容性

新增字段建议：

```text
executed_feature_strategy_id
execution_report
feature_groups
feature_quality_profile
feature_provenance
feature_preprocessing_decision_input
```

---

# 10.3 FeaturePreprocessing 兼容性

新增字段建议：

```text
preprocessing_plan
preprocessing_registry_snapshot
execution_report
removed_features
retained_feature_groups
feature_lineage_map
feature_group_lineage_map
explainability_preservation_report
model_ready_artifacts
preprocessor_artifacts
preprocessing_provenance
model_search_context_input
```

---

# 10.4 下游兼容性

模块六必须继续向模块七提供：

```text
model_ready_matrix_path
preprocessor_path
feature_summary
model_search_context_input
```

如果引入多 variant，则必须提供：

```json
{
  "default_variant_id": "string",
  "available_variants": [],
  "recommended_variant_by_model_family": {}
}
```

---

## 11. 安全与可靠性要求

---

# 11.1 Registry 约束

1. 所有 feature actions 必须来自 Feature Engineering Capability Registry；
2. 所有 preprocessing operations 必须来自 Feature Preprocessing Capability Registry；
3. Registry status 必须参与校验；
4. unavailable capability 不得执行；
5. planned capability 不得作为主执行路径。

---

# 11.2 LLM 输出安全

1. LLM 输出必须是严格 JSON；
2. 必须经过 parser、validator、normalizer；
3. 不允许自定义代码；
4. 不允许路径操作；
5. 不允许绕过 Registry；
6. 不允许直接操作数据库或文件系统。

---

# 11.3 数据泄漏防护

必须实现：

1. target column 永不进入 feature matrix；
2. ID column 默认排除或标记；
3. fit 型 transformer 不得在全量数据上为 CV 评估 fit；
4. target-aware selection 默认禁用；
5. 如果启用 target-aware selection，必须 fold_only；
6. PCA / SVD 等降维必须 fold-safe；
7. model-ready artifact 必须标记 usage；
8. preview artifact 不得用于正式评估。

---

# 11.4 可解释性保护

必须实现：

1. 所有特征保留 lineage；
2. 转换后特征必须可追溯到原始特征；
3. 降维特征必须标记为 reduced / less interpretable；
4. 删除特征必须有删除原因；
5. 输出 explainability preservation report；
6. 后续 Interpretability Analysis 能读取 lineage 信息。

---

## 12. 验收标准

---

# 12.1 Workflow Planning 验收标准

1. Workflow Planning 仍输出完整 WorkflowPlan；
2. WorkflowPlan 中包含 DataStrategy、FeatureStrategy、ModelStrategy、HPOStrategy、EvaluationStrategy、ValidationStrategy；
3. FeatureStrategy 读取 Feature Engineering Capability Registry；
4. FeatureStrategy 中每个 selected action 有 rationale；
5. Validator 可拒绝 unknown / planned / disabled capability；
6. PreprocessingIntent 只包含高层意图；
7. 前端可展示完整 WorkflowPlan 和 FeatureStrategy rationale。

---

# 12.2 Feature Engineering 验收标准

1. 模块五严格执行 WorkflowPlan.FeatureStrategy；
2. 每个 action 有 execution result；
3. 输出 feature matrix artifact；
4. 输出 feature groups；
5. 输出 feature quality profile；
6. 输出 feature provenance；
7. 输出 FeaturePreprocessingDecisionInput；
8. 前端可展示执行结果、质量画像、warnings 和 provenance；
9. fallback 使用被显式记录。

---

# 12.3 Feature Preprocessing 验收标准

1. 模块六读取 FeaturePreprocessingCapabilityRegistry；
2. 模块六支持本 PRD 定义的 12 类 Feature Preprocess 能力；
3. LLM 基于 Feature Engineering 输出生成 PreprocessingPlan；
4. 每个 preprocessing operation 有 rationale；
5. Validator 能拒绝未注册 operation；
6. Validator 能识别数据泄漏风险；
7. 输出 removed_features；
8. 输出 feature lineage；
9. 输出 explainability preservation report；
10. 输出 model-ready artifact；
11. 输出 preprocessing provenance；
12. 前端可展示 operation sequence、rationale、leakage summary、lineage 和 artifacts；
13. 输出仍兼容模块七。

---

## 13. 里程碑

---

# Milestone 1：Registry 与 Schema 扩展

交付：

* Feature Engineering Capability Registry 增强；
* Feature Preprocessing Capability Registry 新增；
* 12 类 Feature Preprocess capability 定义；
* WorkflowPlan.FeatureStrategy schema 增强；
* PreprocessingPlan schema 新增；
* Rationale schema 新增；
* Validator 规则定义。

---

# Milestone 2：Workflow Planning 增强

交付：

* Workflow Planning prompt 更新；
* 仍输出完整 WorkflowPlan；
* FeatureStrategy 变成 capability-aware；
* PreprocessingIntent 明确为 high-level；
* 前端展示完整 WorkflowPlan 和 FeatureStrategy rationale。

---

# Milestone 3：Feature Engineering 增强

交付：

* Feature Engineering 严格执行 FeatureStrategy；
* action-level execution report；
* feature quality profile；
* feature provenance；
* FeaturePreprocessingDecisionInput；
* 前端展示增强。

---

# Milestone 4：Feature Preprocessing LLM Planning

交付：

* Feature Preprocessing Capability Registry；
* LLM PreprocessingPlan；
* PreprocessingPlanValidator；
* plan-only API；
* rationale 展示；
* leakage summary；
* 12 类能力中的 analysis / filtering / scaling / transformation / leakage detection 基础链路。

---

# Milestone 5：Feature Preprocessing Execution 与下游兼容

交付：

* 缺失值处理；
* 缺失机制分析；
* 低信息量过滤；
* 缩放与标准化；
* 偏态变换；
* 相关性与共线性处理；
* 目标泄漏检测；
* 特征选择；
* 特征组策略；
* 降维；
* 可解释性 lineage；
* artifact reproducibility；
* 下游模块七兼容；
* 端到端流程通过。

---

## 14. 风险与应对

---

# 14.1 Workflow Planning 被误改成只输出 FeatureStrategy

风险：

开发时误解重构目标，导致 WorkflowPlan 其他策略丢失。

应对：

1. Validator 强制校验完整 WorkflowPlan；
2. Prompt 明确要求完整 WorkflowPlan；
3. API response 保持完整 WorkflowPlan；
4. 前端继续展示完整 WorkflowPlan。

---

# 14.2 Feature Preprocessing 能力过宽导致实现复杂

风险：

预处理模块被设计得过大，影响 MVP 迭代速度。

应对：

1. 当前阶段只实现本 PRD 定义的 12 类能力；
2. 不引入单位处理、物理约束、batch effect 等额外能力；
3. 每类能力先实现稳定可用版本；
4. 高级能力通过 Registry 标记 experimental。

---

# 14.3 数据泄漏

风险：

Feature Preprocessing 在全量数据上 fit transformer 并用于 CV。

应对：

1. 强制 fit_scope；
2. 默认 fold-safe；
3. artifact usage 标记；
4. Pipeline Execution 中 fold 内 fit；
5. Validator 拦截高风险计划。

---

# 14.4 LLM 决策理由泛化

风险：

LLM 输出看起来合理，但缺少真实证据。

应对：

1. evidence 必须引用 Feature Quality Profile；
2. rationale 不完整则 validator 拒绝；
3. 前端展示 evidence；
4. 最终报告保留 rationale。

---

# 14.5 前端信息过载

风险：

完整 WorkflowPlan、FeatureStrategy、PreprocessingPlan、rationale、quality profile 信息较多。

应对：

1. 默认展示 summary；
2. rationale 折叠展示；
3. warning 高亮；
4. advanced details 放入展开面板；
5. 提供 “View Full JSON” 调试入口。

---

## 15. 最终目标形态

重构完成后，三个模块的关系应为：

```text
Workflow Planning
= 完整 WorkflowPlan 生成器
= FeatureStrategy 的能力感知决策者
= 保留 Data / Model / HPO / Evaluation / Validation 等完整规划职责

Feature Engineering
= Feature Engineering Capability Provider
= FeatureStrategy Executor
= Feature Matrix + Quality Profile + Provenance Producer

Feature Preprocessing
= LLM-guided Preprocessing Planner
= 12 类核心 Feature Preprocess 能力执行器
= Model-ready Artifact + Lineage + Provenance Producer
```

最终系统不是：

```text
Workflow Planning 只生成 FeatureStrategy
```

而是：

```text
Workflow Planning 生成完整 WorkflowPlan
其中 FeatureStrategy 更具体、更可执行、更有材料学依据

Feature Engineering 严格执行 FeatureStrategy
并反馈真实特征矩阵、特征组和质量画像

Feature Preprocessing 在真实特征质量基础上
由 LLM 再决策并安全执行 12 类核心预处理能力

后续 Model Search、Pipeline Execution、Interpretability Analysis
可以基于更可靠、更可解释、更可复现的 model-ready artifact 继续运行
```

