# PRD-2：LLM-based Task Interpretation 模块需求文档

## 1. 模块名称

LLM-based Task Interpretation  
基于大语言模型的任务理解模块

---

## 2. 模块定位

本模块是 AI-driven AutoML for Materials Science 系统的第二步，位于：

Task Input  
→ LLM-based Task Interpretation  
→ Dataset Loading and Profiling  
→ Workflow Planning  
→ Pipeline Generation  
→ Pipeline Execution  
→ Evaluation  
→ Diagnosis and Refinement  
→ Report Generation

本模块接收 Task Input 模块生成的 Task Specification Object，通过 LLM 对用户提交的材料机器学习任务进行语义理解、任务规范化、建模意图解析和下游模块输入增强。

---

## 3. 模块目标

本模块的核心目标是：

1. 将结构化但相对原始的 Task Specification Object 转换为更适合后续自动化流程使用的 Task Interpretation Object；
2. 利用 LLM 理解用户任务背后的材料科学语义和机器学习建模意图；
3. 对任务类型、输入模态、预测目标、评价指标、用户偏好和约束进行语义增强；
4. 识别任务中的潜在歧义、风险和缺失信息；
5. 为后续 Dataset Loading、Workflow Planning 模块提供清晰、规范、可机器读取的任务理解结果。

---

## 4. 系统边界

### 4.1 本模块负责的内容

本模块负责：

1. 接收已通过 Task Input 模块校验的 Task Specification Object；
2. 调用 LLM 对任务进行语义解析；
3. 识别材料任务类型，例如成分性质预测、结构性质预测、分类、排序等；
4. 规范化预测目标的科学含义；
5. 解释 input_type 与 prediction_target 之间的关系；
6. 推断推荐的建模目标表达；
7. 判断 evaluation_metric 是否合理，并给出语义层面的解释；
8. 解析 user_priority，例如 accuracy、interpretability、efficiency；
9. 解析 constraints 中的自然语言限制；
10. 输出标准化 Task Interpretation Object；
11. 记录 LLM 调用结果、解释理由、风险提示和置信度。

### 4.2 本模块不负责的内容

本模块不负责：

1. 不负责渲染任务输入表单；
2. 不负责修改 Task Input 模块已有字段校验逻辑；
3. 不负责上传、读取、解析真实数据文件；
4. 不负责生成特征工程方案；
5. 不负责选择具体模型；
6. 不负责生成完整 Workflow Plan；
7. 不负责执行机器学习 Pipeline；
8. 不负责模型训练、评估和调参；
9. 不负责生成最终实验报告。

---

## 5. 输入数据

### 5.1 输入来源

输入来自 Task Input 模块输出的 Task Specification Object。

### 5.2 输入方式

MVP 阶段建议通过 task_id 获取已有任务：

```text
POST /api/task-interpretations/{task_id}
````

后端流程：

```text
task_id
  ↓
查询 task_specification 表
  ↓
获取 Task Specification Object
  ↓
校验 task.status
  ↓
调用 LLM 进行任务理解
```

### 5.3 输入字段

本模块主要接收以下字段：

| 字段                  | 说明                                       |
| ------------------- | ---------------------------------------- |
| task_id             | 任务唯一 ID                                  |
| task_name           | 用户填写的任务名称                                |
| task_description    | 用户对任务的自然语言描述                             |
| material_system     | 材料体系                                     |
| prediction_target   | 预测目标                                     |
| task_type           | 任务类型，如 regression/classification/ranking |
| dataset_description | 数据集描述                                    |
| input_type          | 输入类型，如 composition/structure             |
| target_column       | 目标变量列名                                   |
| evaluation_metric   | 用户指定评价指标                                 |
| user_priority       | 用户优先级                                    |
| constraints         | 用户约束                                     |
| status              | Task Input 模块校验状态                        |
| validation_messages | 已有校验信息                                   |

---

## 6. 前置条件

### 6.1 必须满足

1. task_id 必须存在；
2. Task Specification Object 必须能够从数据库中读取；
3. status 必须为 valid 或 valid_with_warning；
4. 必填字段应已通过 Task Input 模块校验；
5. 系统必须配置可用的 LLM 调用参数。

### 6.2 不允许进入本模块的状态

以下状态不应进入 LLM 任务理解流程：

| status     | 处理方式                    |
| ---------- | ----------------------- |
| incomplete | 返回错误，提示用户先补全 Task Input |
| invalid    | 返回错误，提示用户先修正字段冲突        |
| not_found  | 返回任务不存在错误               |

---

## 7. 输出数据

### 7.1 输出对象

本模块输出 Task Interpretation Object。

### 7.2 输出字段设计

```json
{
  "interpretation_id": "interp_xxxxxxxx",
  "task_id": "task_xxxxxxxx",
  "status": "interpreted",
  "interpreted_task_type": "regression",
  "interpreted_input_modality": "composition",
  "interpreted_material_domain": "inorganic crystals",
  "interpreted_prediction_target": {
    "raw_target": "experimental band gap",
    "normalized_target": "band_gap",
    "target_category": "electronic_property",
    "target_unit": "eV",
    "target_description": "Predict the experimental band gap of inorganic crystalline materials."
  },
  "modeling_intent": {
    "primary_goal": "property_prediction",
    "secondary_goals": ["interpretability"],
    "optimization_direction": "minimize_error",
    "preferred_metric": "MAE"
  },
  "dataset_intent": {
    "dataset_reference": "matbench_expt_gap",
    "expected_input_columns": ["composition"],
    "expected_target_column": "band_gap",
    "requires_structure_file": false
  },
  "constraint_interpretation": {
    "hard_constraints": [],
    "soft_constraints": ["prefer interpretable models"],
    "potential_conflicts": []
  },
  "recommended_defaults": {
    "evaluation_metric": "MAE",
    "validation_strategy": "cross_validation",
    "baseline_requirement": true
  },
  "ambiguities": [],
  "warnings": [],
  "llm_reasoning_summary": "The task is interpreted as a composition-based regression problem for predicting experimental band gaps.",
  "confidence_score": 0.92,
  "created_at": "2026-04-30T10:00:00",
  "updated_at": "2026-04-30T10:00:00"
}
```

---

## 8. 核心功能需求

### 8.1 查询 Task Specification Object

#### 输入

```text
task_id
```

#### 处理

1. 根据 task_id 查询 Task Input 模块生成的任务对象；
2. 检查任务是否存在；
3. 检查任务状态是否允许进入 LLM Interpretation；
4. 提取任务字段，组装 LLM 输入上下文。

#### 输出

```text
可用于 LLM 调用的 task_context
```

---

### 8.2 构建 LLM Prompt

#### 输入

```text
Task Specification Object
```

#### 处理

系统需要将结构化任务字段转换为稳定、可控、可解析的 LLM Prompt。

Prompt 应包含：

1. 系统角色说明；
2. 当前任务字段；
3. 材料机器学习任务理解要求；
4. 输出 JSON Schema；
5. 禁止事项；
6. 字段解释规则；
7. 异常与歧义处理规则。

#### 输出

```text
LLM Prompt
```

---

### 8.3 LLM 任务语义理解

#### 输入

```text
LLM Prompt
```

#### 处理

LLM 需要完成以下理解任务：

1. 判断任务是否为材料机器学习任务；
2. 判断任务类型是否合理；
3. 判断输入模态；
4. 识别材料体系；
5. 标准化 prediction_target；
6. 判断目标性质类别；
7. 判断评价指标是否适合；
8. 解析用户优先级；
9. 解析自然语言约束；
10. 生成任务理解摘要；
11. 输出置信度。

#### 输出

```text
LLM 原始 JSON 响应
```

---

### 8.4 任务类型解释

#### 输入

```text
task_type
prediction_target
task_description
evaluation_metric
```

#### 处理

判断任务属于：

1. regression；
2. classification；
3. ranking；
4. unknown。

并说明该判断是否与 Task Input 中的 task_type 一致。

#### 输出

```json
{
  "interpreted_task_type": "regression",
  "task_type_consistency": true,
  "explanation": "Band gap prediction is a continuous property prediction task."
}
```

---

### 8.5 输入模态解释

#### 输入

```text
input_type
dataset_description
material_system
```

#### 处理

判断任务输入属于：

1. composition；
2. structure；
3. descriptor；
4. text；
5. mixed。

#### 输出

```json
{
  "interpreted_input_modality": "composition",
  "requires_structure_file": false,
  "expected_input_representation": "chemical formula"
}
```

---

### 8.6 预测目标规范化

#### 输入

```text
prediction_target
target_column
task_description
```

#### 处理

将用户输入的预测目标转化为系统内部更稳定的语义对象。

例如：

```text
experimental band gap
```

规范化为：

```json
{
  "normalized_target": "band_gap",
  "target_category": "electronic_property",
  "target_unit": "eV"
}
```

#### 输出

```text
标准化预测目标对象
```

---

### 8.7 建模意图解析

#### 输入

```text
task_type
prediction_target
evaluation_metric
user_priority
constraints
```

#### 处理

识别用户真正的建模目标：

1. property_prediction；
2. material_screening；
3. classification；
4. ranking；
5. interpretability_analysis；
6. benchmark_comparison。

#### 输出

```json
{
  "primary_goal": "property_prediction",
  "secondary_goals": ["interpretability"],
  "optimization_direction": "minimize_error"
}
```

---

### 8.8 用户偏好解析

#### 输入

```text
user_priority
constraints
```

#### 处理

将用户偏好拆解为后续系统可使用的语义信号。

例如：

```json
["accuracy", "interpretability"]
```

解释为：

```json
{
  "accuracy_priority": "high",
  "interpretability_priority": "high",
  "efficiency_priority": "medium"
}
```

#### 输出

```text
标准化用户偏好对象
```

---

### 8.9 约束条件解析

#### 输入

```text
constraints
```

#### 处理

将自然语言约束拆分为：

1. hard_constraints；
2. soft_constraints；
3. potential_conflicts。

例如：

```text
Use interpretable models only
```

解析为：

```json
{
  "hard_constraints": ["restrict_model_family_to_interpretable_models"],
  "soft_constraints": [],
  "potential_conflicts": ["may reduce predictive accuracy"]
}
```

#### 输出

```text
结构化约束对象
```

---

### 8.10 歧义与风险识别

#### 输入

```text
完整 Task Specification Object
```

#### 处理

识别以下问题：

1. 任务描述过短；
2. prediction_target 含义模糊；
3. dataset_description 不能判断真实数据来源；
4. input_type 与 dataset_description 可能不一致；
5. evaluation_metric 未指定；
6. target_column 与 prediction_target 可能不一致；
7. 用户约束之间可能冲突。

#### 输出

```json
{
  "ambiguities": [
    {
      "field": "dataset_description",
      "message": "Dataset source is not explicit enough to determine whether it is a public benchmark or user-provided data.",
      "severity": "medium"
    }
  ],
  "warnings": []
}
```

---

### 8.11 LLM 输出校验

#### 输入

```text
LLM 原始响应
```

#### 处理

1. 检查是否为合法 JSON；
2. 检查是否符合 Task Interpretation Schema；
3. 检查必要字段是否存在；
4. 检查枚举值是否合法；
5. 检查 confidence_score 是否在 0 到 1 之间；
6. 若解析失败，可执行一次重试；
7. 若仍失败，返回 interpretation_failed 状态。

#### 输出

```text
Validated Task Interpretation Object
```

---

### 8.12 结果持久化

#### 输入

```text
Validated Task Interpretation Object
```

#### 处理

将解释结果写入 task_interpretation 表。

#### 输出

```text
已持久化的 Task Interpretation Object
```

---

## 9. 状态设计

### 9.1 状态枚举

| 状态                       | 含义                             |
| ------------------------ | ------------------------------ |
| pending                  | 已创建解释任务，但尚未调用 LLM              |
| interpreting             | 正在调用 LLM                       |
| interpreted              | LLM 解释成功                       |
| interpreted_with_warning | 解释成功，但存在歧义或警告                  |
| failed                   | LLM 调用失败或输出无法解析                |
| blocked                  | Task Specification 状态不允许进入解释流程 |

### 9.2 状态流转

```text
pending
  ↓
interpreting
  ↓
interpreted / interpreted_with_warning / failed

blocked 状态由前置条件检查直接产生
```

---

## 10. API 需求

### 10.1 创建任务理解结果

```text
POST /api/task-interpretations/{task_id}
```

#### 请求参数

```text
task_id
```

#### 请求体

MVP 阶段可为空。

#### 响应

```json
{
  "success": true,
  "message": "Task interpretation created successfully.",
  "data": {
    "interpretation_id": "interp_xxxxxxxx",
    "task_id": "task_xxxxxxxx",
    "status": "interpreted",
    "interpreted_task_type": "regression",
    "interpreted_input_modality": "composition",
    "interpreted_prediction_target": {},
    "modeling_intent": {},
    "dataset_intent": {},
    "constraint_interpretation": {},
    "recommended_defaults": {},
    "ambiguities": [],
    "warnings": [],
    "confidence_score": 0.92
  }
}
```

---

### 10.2 查询任务理解结果

```text
GET /api/task-interpretations/{interpretation_id}
```

#### 响应

返回完整 Task Interpretation Object。

---

### 10.3 根据 task_id 查询最新任务理解结果

```text
GET /api/tasks/{task_id}/interpretation
```

#### 响应

返回该 task_id 对应的最新 Task Interpretation Object。

---

### 10.4 重新执行任务理解

```text
POST /api/task-interpretations/{task_id}/rerun
```

#### 使用场景

当用户修改 Task Input 后，需要重新生成任务理解结果。

---

## 11. 数据库设计建议

### 11.1 表名

```text
task_interpretation
```

### 11.2 字段设计

| 字段                          | 类型       | 说明                       |
| --------------------------- | -------- | ------------------------ |
| id                          | str      | interpretation_id，主键     |
| task_id                     | str      | 关联 task_specification.id |
| status                      | str      | 解释状态                     |
| interpreted_task_type       | str      | LLM 解释后的任务类型             |
| interpreted_input_modality  | str      | LLM 解释后的输入模态             |
| interpreted_material_domain | str      | 材料领域                     |
| confidence_score            | float    | 置信度                      |
| interpretation_json         | JSONB    | 完整解释结果                   |
| llm_request_json            | JSONB    | LLM 请求记录，可选              |
| llm_response_json           | JSONB    | LLM 原始响应，可选              |
| error_message               | text     | 错误信息                     |
| created_at                  | datetime | 创建时间                     |
| updated_at                  | datetime | 更新时间                     |

### 11.3 设计原则

1. 高频查询字段单独建列；
2. 复杂解释结果放入 JSONB；
3. task_id 与 task_specification 表建立外键关系；
4. 支持同一个 task_id 多次解释；
5. 默认查询最新一条解释结果。

---

## 12. 后端模块结构建议

```text
backend/app/modules/task_interpretation/
├── __init__.py
├── api.py
├── schemas.py
├── service.py
├── model.py
├── repository.py
├── prompt_builder.py
├── llm_client.py
├── parser.py
├── validator.py
└── builder.py
```

### 12.1 文件职责

| 文件                | 职责                                         |
| ----------------- | ------------------------------------------ |
| api.py            | 定义任务理解相关 HTTP 接口                           |
| schemas.py        | 定义请求、响应、内部数据对象                             |
| service.py        | 编排查询 Task Specification、调用 LLM、解析、校验、持久化流程 |
| model.py          | 定义 task_interpretation 数据库表                |
| repository.py     | 提供解释结果 CRUD 操作                             |
| prompt_builder.py | 根据 Task Specification Object 构建 LLM Prompt |
| llm_client.py     | 封装 LLM API 调用                              |
| parser.py         | 解析 LLM 返回的 JSON                            |
| validator.py      | 校验 LLM 输出是否符合 schema                       |
| builder.py        | 构建 Task Interpretation Object              |

---

## 13. 前端需求

MVP 阶段前端不是重点，但建议预留以下能力：

### 13.1 任务理解结果展示面板

展示内容：

1. interpreted_task_type；
2. interpreted_input_modality；
3. normalized_target；
4. modeling_intent；
5. recommended_defaults；
6. ambiguities；
7. warnings；
8. confidence_score。

### 13.2 用户操作

建议提供：

1. “Run Task Interpretation” 按钮；
2. “Re-run Interpretation” 按钮；
3. “View Interpretation Result” 面板。

---

## 14. LLM Prompt 设计要求

### 14.1 Prompt 输入内容

Prompt 必须包含：

1. 当前系统模块说明；
2. Task Specification Object；
3. 材料机器学习领域背景；
4. 任务理解目标；
5. 输出 JSON Schema；
6. 不允许生成代码；
7. 不允许做 Workflow Planning；
8. 不允许选择具体模型和超参数；
9. 不允许假设真实数据已经加载。

### 14.2 Prompt 约束

LLM 必须：

1. 只输出 JSON；
2. 不输出 Markdown；
3. 不输出解释性段落；
4. 不生成代码；
5. 不直接规划完整机器学习流程；
6. 对不确定内容标记 ambiguity；
7. 对风险内容标记 warning；
8. 给出 confidence_score。

---

## 15. 与相邻模块的关系

### 15.1 与 Task Input 模块的关系

Task Input 模块负责：

1. 表单字段收集；
2. 字段标准化；
3. 必填校验；
4. 基础合法性校验；
5. 生成 Task Specification Object。

本模块只消费 Task Specification Object，不重复做表单校验。

### 15.2 与 Dataset Loading 模块的关系

本模块不加载真实数据，只输出 dataset_intent，例如：

1. 数据集可能来源；
2. 预期输入字段；
3. 是否需要结构文件；
4. 目标列语义。

Dataset Loading 模块后续根据 dataset_intent 进行真实数据加载和 profiling。

### 15.3 与 Workflow Planning 模块的关系

本模块不制定完整 workflow，只输出任务理解结果和推荐默认值。

Workflow Planning 模块后续基于 Task Interpretation Object 决定：

1. 数据预处理策略；
2. 特征工程策略；
3. 候选模型；
4. HPO 搜索空间；
5. 验证策略；
6. Pipeline 组合。

---

## 16. 错误处理

### 16.1 task_id 不存在

返回：

```json
{
  "success": false,
  "message": "Task specification not found.",
  "error_code": "NOT_FOUND"
}
```

### 16.2 Task 状态不允许解释

返回：

```json
{
  "success": false,
  "message": "Only valid or valid_with_warning tasks can be interpreted.",
  "error_code": "TASK_NOT_READY"
}
```

### 16.3 LLM 调用失败

返回：

```json
{
  "success": false,
  "message": "LLM interpretation failed.",
  "error_code": "LLM_CALL_FAILED"
}
```

### 16.4 LLM 输出解析失败

返回：

```json
{
  "success": false,
  "message": "Failed to parse LLM output as valid Task Interpretation Object.",
  "error_code": "LLM_OUTPUT_PARSE_ERROR"
}
```

---

## 17. MVP 验收标准

| 序号 | 验收标准                                       |
| -- | ------------------------------------------ |
| 1  | 能通过 task_id 读取已有 Task Specification Object |
| 2  | 能拒绝 incomplete 或 invalid 状态的任务             |
| 3  | 能构建稳定的 LLM Prompt                          |
| 4  | 能调用 LLM 生成任务理解结果                           |
| 5  | 能解析 LLM 返回的 JSON                           |
| 6  | 能校验 LLM 输出是否符合 Task Interpretation Schema  |
| 7  | 能输出 interpreted_task_type                  |
| 8  | 能输出 interpreted_input_modality             |
| 9  | 能输出 normalized prediction target           |
| 10 | 能输出 modeling_intent                        |
| 11 | 能输出 dataset_intent                         |
| 12 | 能输出 constraint_interpretation              |
| 13 | 能输出 ambiguities 和 warnings                 |
| 14 | 能输出 confidence_score                       |
| 15 | 能将结果持久化到 task_interpretation 表             |
| 16 | 能通过 API 查询解释结果                             |
| 17 | 能重新执行任务理解                                  |
| 18 | 不生成 Workflow Plan                          |
| 19 | 不读取真实数据文件                                  |
| 20 | 不生成模型或 Pipeline 代码                         |

---

## 18. 示例流程

### 18.1 输入

```json
{
  "task_id": "task_a1b2c3d4",
  "task_name": "Band gap prediction",
  "prediction_target": "experimental band gap",
  "task_type": "regression",
  "dataset_description": "matbench_expt_gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE",
  "user_priority": ["accuracy", "interpretability"],
  "constraints": []
}
```

### 18.2 输出

```json
{
  "interpretation_id": "interp_12345678",
  "task_id": "task_a1b2c3d4",
  "status": "interpreted",
  "interpreted_task_type": "regression",
  "interpreted_input_modality": "composition",
  "interpreted_material_domain": "inorganic materials",
  "interpreted_prediction_target": {
    "raw_target": "experimental band gap",
    "normalized_target": "band_gap",
    "target_category": "electronic_property",
    "target_unit": "eV"
  },
  "modeling_intent": {
    "primary_goal": "property_prediction",
    "secondary_goals": ["interpretability"],
    "optimization_direction": "minimize_error",
    "preferred_metric": "MAE"
  },
  "dataset_intent": {
    "dataset_reference": "matbench_expt_gap",
    "expected_input_columns": ["composition"],
    "expected_target_column": "band_gap",
    "requires_structure_file": false
  },
  "constraint_interpretation": {
    "hard_constraints": [],
    "soft_constraints": [],
    "potential_conflicts": []
  },
  "recommended_defaults": {
    "evaluation_metric": "MAE",
    "validation_strategy": "cross_validation",
    "baseline_requirement": true
  },
  "ambiguities": [],
  "warnings": [],
  "confidence_score": 0.92
}
```

---

## 19. 后续迭代方向

MVP 之后可以增强：

1. 支持多轮澄清问题生成；
2. 支持用户确认或修改 LLM 解释结果；
3. 支持领域知识库辅助任务理解；
4. 支持材料属性 ontology 映射；
5. 支持常见公开数据集自动识别；
6. 支持根据历史任务案例进行 few-shot interpretation；
7. 支持任务复杂度评分；
8. 支持自动生成 Dataset Loading 模块所需的 schema hint；
9. 支持 Workflow Planning 模块所需的 planning hint；
10. 支持 LLM 输出版本管理与对比。

---

## 20. 总结

LLM-based Task Interpretation 模块的本质不是再次收集用户输入，也不是直接规划完整机器学习工作流，而是将 Task Input 模块生成的结构化任务对象进一步转化为具有材料科学语义和机器学习建模意图的 Task Interpretation Object。

该模块是 Task Input 与 Workflow Planning 之间的语义桥梁，负责让系统真正理解“用户想做什么材料机器学习任务”，并为后续自动化数据加载、工作流规划和 Pipeline 生成提供稳定、规范、可复用的任务理解结果。
