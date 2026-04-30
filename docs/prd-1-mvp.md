# User Task Specification 模块 MVP 需求文档

## 1. 模块概述

### 1.1 模块名称

User Task Specification

### 1.2 模块定位

User Task Specification 是 AI-driven Automated Machine Learning 框架的入口模块，负责让用户以“表单填写”的方式提交材料机器学习任务需求，并将用户填写的信息整理为标准化、可校验、可传递的任务说明对象。

该模块的核心目标是：

> 通过结构化表单收集用户任务需求，生成后续 LLM task understanding、dataset loading、workflow planning 等模块可以直接使用的 Task Specification Object。

### 1.3 MVP 阶段目标

MVP 阶段不依赖复杂自然语言抽取，而是通过表单字段约束用户输入，降低任务理解的不确定性。

MVP 阶段需要实现：

1. 提供结构化任务填写表单；
2. 引导用户填写材料机器学习任务的核心信息；
3. 对必填字段进行完整性检查；
4. 对任务类型、输入类型、评价指标进行基础合法性校验；
5. 输出标准化 Task Specification Object；
6. 对缺失或冲突字段给出提示信息。

---

## 2. 系统边界澄清

### 2.1 本模块负责的范围

User Task Specification 模块只负责“任务需求录入与规范化”，主要包括：

1. 展示任务填写表单；
2. 接收用户填写的结构化字段；
3. 检查必填字段是否完整；
4. 校验字段之间是否存在明显冲突；
5. 对部分字段进行标准化处理；
6. 生成 Task Specification Object；
7. 在信息缺失或冲突时提示用户修改。

### 2.2 本模块不负责的范围

MVP 阶段，本模块不负责以下内容：

1. 不从自然语言中自动抽取核心字段；
2. 不实际加载数据集；
3. 不分析数据质量；
4. 不进行数据清洗；
5. 不选择特征工程方法；
6. 不生成候选机器学习 pipeline；
7. 不执行模型训练；
8. 不计算模型评估指标；
9. 不进行结果诊断；
10. 不生成最终科研报告；
11. 不主动联网搜索数据集或文献。

### 2.3 与后续模块的关系

本模块的输出是后续模块的输入。

```text
User Task Specification
        ↓
Task Understanding by LLM
        ↓
Dataset Loading and Profiling
        ↓
Workflow Planning
````

本模块只解决：

> “用户提交了一个什么样的材料机器学习任务？”

而不解决：

> “这个任务应该如何建模、如何优化、如何解释结果？”

---

## 3. MVP 表单字段设计

MVP 阶段建议采用表单式任务输入。用户需要按照字段填写任务信息，而不是只输入一段自由文本。

### 3.1 表单字段总览

| 字段名               | 是否必填 | 输入方式               | 字段说明     | 示例                                               |
| ----------------- | ---- | ------------------ | -------- | ------------------------------------------------ |
| task_name         | 选填   | 文本框                | 任务名称     | Band gap prediction                              |
| task_description  | 选填   | 多行文本框              | 对任务的补充描述 | Predict experimental band gaps from compositions |
| material_system   | 选填   | 下拉框 / 文本框          | 材料体系     | inorganic crystals                               |
| prediction_target | 必填   | 文本框                | 预测目标材料性质 | band gap                                         |
| task_type         | 必填   | 下拉框                | 机器学习任务类型 | regression                                       |
| dataset_source    | 必填   | 文本框 / 文件路径 / 数据集名称 | 数据来源     | matbench_expt_gap                                |
| input_type        | 必填   | 下拉框                | 输入数据类型   | composition                                      |
| target_column     | 条件必填 | 文本框                | 目标变量列名   | band_gap                                         |
| evaluation_metric | 选填   | 下拉框                | 评价指标     | MAE                                              |
| user_priority     | 选填   | 多选框                | 用户优先目标   | accuracy, interpretability                       |
| constraints       | 选填   | 多行文本框              | 用户限制条件   | Use interpretable models only                    |

---

## 4. 核心数据对象

### 4.1 Task Specification Object

Task Specification Object 是本模块最终输出的标准化任务对象，用于描述一个材料机器学习任务的输入需求。

MVP 阶段建议包含以下字段：

| 字段名                 | 来源   | 说明                           |
| ------------------- | ---- | ---------------------------- |
| task_id             | 系统生成 | 任务唯一标识                       |
| task_name           | 用户填写 | 任务名称                         |
| task_description    | 用户填写 | 任务补充描述                       |
| material_system     | 用户填写 | 材料体系                         |
| prediction_target   | 用户填写 | 预测目标                         |
| task_type           | 用户选择 | 任务类型                         |
| dataset_source      | 用户填写 | 数据来源                         |
| input_type          | 用户选择 | 输入数据类型                       |
| target_column       | 用户填写 | 目标变量列名                       |
| evaluation_metric   | 用户选择 | 评价指标                         |
| user_priority       | 用户选择 | 用户偏好                         |
| constraints         | 用户填写 | 任务约束                         |
| status              | 系统生成 | valid / incomplete / invalid |
| missing_fields      | 系统生成 | 缺失字段列表                       |
| validation_messages | 系统生成 | 校验提示信息                       |

---

## 5. MVP 功能模块拆分

## 5.1 功能一：任务表单展示

### 功能目标

向用户展示结构化任务填写表单，引导用户按照标准字段提交材料机器学习任务需求。

### 输入

无用户业务输入。系统根据预设字段配置生成表单。

### 处理

系统需要展示以下表单区域：

1. 基本任务信息；
2. 数据集信息；
3. 机器学习任务信息；
4. 评价指标信息；
5. 用户偏好与约束信息。

表单应区分必填字段和选填字段。

必填字段包括：

1. prediction_target；
2. task_type；
3. dataset_source；
4. input_type。

条件必填字段包括：

1. target_column：当用户使用自定义表格数据时必填。

### 输出

展示给用户的任务填写表单。

---

## 5.2 功能二：任务表单提交

### 功能目标

接收用户填写的表单内容，生成初始任务对象。

### 输入

用户填写的表单字段。

示例：

```json
{
  "task_name": "Band gap prediction",
  "task_description": "Predict experimental band gaps from chemical compositions.",
  "material_system": "inorganic crystals",
  "prediction_target": "experimental band gap",
  "task_type": "regression",
  "dataset_source": "matbench_expt_gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE",
  "user_priority": ["accuracy", "interpretability"],
  "constraints": []
}
```

### 处理

系统需要完成以下处理：

1. 接收表单提交内容；
2. 为任务生成唯一 task_id；
3. 保存用户填写的原始字段；
4. 将字段整理为初始 Task Specification Object；
5. 将任务状态暂定为 received。

### 输出

初始任务对象：

```json
{
  "task_id": "task_001",
  "task_name": "Band gap prediction",
  "status": "received"
}
```

---

## 5.3 功能三：字段标准化

### 功能目标

将用户填写的字段转换为系统内部统一表达，保证后续模块接收到稳定、规范的输入。

### 输入

用户提交的表单字段。

示例：

```json
{
  "task_type": "Regression",
  "input_type": "Chemical composition",
  "evaluation_metric": "Mean Absolute Error"
}
```

### 处理

系统对部分字段进行标准化映射。

#### 任务类型标准化

| 表单显示值          | 系统标准值          |
| -------------- | -------------- |
| Regression     | regression     |
| Classification | classification |
| Ranking        | ranking        |

#### 输入类型标准化

| 表单显示值                 | 系统标准值            |
| --------------------- | ---------------- |
| Chemical composition  | composition      |
| Crystal structure     | structure        |
| Descriptor table      | descriptor_table |
| Text-derived features | text_features    |

#### 评价指标标准化

| 表单显示值                   | 系统标准值    |
| ----------------------- | -------- |
| Mean Absolute Error     | MAE      |
| Root Mean Squared Error | RMSE     |
| R-squared               | R2       |
| Accuracy                | Accuracy |
| F1 score                | F1       |
| ROC-AUC                 | ROC-AUC  |

### 输出

标准化后的字段结果：

```json
{
  "task_type": "regression",
  "input_type": "composition",
  "evaluation_metric": "MAE"
}
```

---

## 5.4 功能四：必填字段完整性检查

### 功能目标

检查用户是否填写了启动后续自动化流程所需的最低任务信息。

### 输入

标准化后的 Task Specification Object。

示例：

```json
{
  "prediction_target": "band gap",
  "task_type": "regression",
  "dataset_source": "matbench_expt_gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE"
}
```

### 处理

系统检查以下字段是否完整：

| 字段名               | 检查规则                             |
| ----------------- | -------------------------------- |
| prediction_target | 不允许为空                            |
| task_type         | 不允许为空                            |
| dataset_source    | 不允许为空                            |
| input_type        | 不允许为空                            |
| target_column     | 如果 dataset_source 为用户上传表格，则不允许为空 |
| evaluation_metric | 可为空；为空时给出提示，但不阻断流程               |

检查规则：

1. 如果 prediction_target 缺失，状态为 incomplete；
2. 如果 task_type 缺失，状态为 incomplete；
3. 如果 dataset_source 缺失，状态为 incomplete；
4. 如果 input_type 缺失，状态为 incomplete；
5. 如果用户上传的是 CSV、Excel 或自定义表格数据，但 target_column 缺失，状态为 incomplete；
6. 如果 evaluation_metric 缺失，状态为 valid_with_warning 或 warning。

### 输出

字段完整时：

```json
{
  "status": "valid",
  "missing_fields": []
}
```

字段不完整时：

```json
{
  "status": "incomplete",
  "missing_fields": ["target_column"],
  "validation_messages": [
    "Target column is required when using a user-provided tabular dataset."
  ]
}
```

---

## 5.5 功能五：基础合法性校验

### 功能目标

检查用户填写的字段之间是否存在明显冲突，避免错误任务进入后续模块。

### 输入

标准化后的 Task Specification Object。

示例：

```json
{
  "task_type": "regression",
  "evaluation_metric": "Accuracy",
  "input_type": "composition",
  "prediction_target": "band gap"
}
```

### 处理

系统根据预设规则进行基础校验。

#### 任务类型与评价指标匹配规则

| task_type      | 合法 evaluation_metric         |
| -------------- | ---------------------------- |
| regression     | MAE, RMSE, R2                |
| classification | Accuracy, F1, ROC-AUC        |
| ranking        | Spearman, NDCG, Top-k recall |

校验规则：

1. 如果 task_type 为 regression，但 evaluation_metric 为 Accuracy，则标记为 invalid；
2. 如果 task_type 为 classification，但 evaluation_metric 为 MAE，则标记为 invalid；
3. 如果 task_type 为 regression 且 prediction_target 是 band gap、formation energy、elastic modulus 等连续性质，则通过；
4. 如果 input_type 为 structure，但 dataset_source 未说明结构文件、结构字段或结构数据集来源，则标记为 incomplete；
5. 如果 input_type 为 composition，但 dataset_source 只指向结构文件夹，则标记为 warning 或 incomplete。

### 输出

字段合法时：

```json
{
  "status": "valid",
  "validation_messages": []
}
```

字段冲突时：

```json
{
  "status": "invalid",
  "validation_messages": [
    "Accuracy is not a suitable evaluation metric for a regression task."
  ]
}
```

---

## 5.6 功能六：错误提示与修改引导

### 功能目标

当用户表单信息缺失或存在冲突时，系统给出明确、可操作的修改提示，引导用户补充或修正字段。

### 输入

完整性检查和合法性校验结果。

示例：

```json
{
  "status": "incomplete",
  "missing_fields": ["target_column"],
  "validation_messages": []
}
```

### 处理

系统根据缺失字段或冲突字段生成提示信息。

#### 缺失字段提示规则

| 缺失字段              | 提示信息                                                                   |
| ----------------- | ---------------------------------------------------------------------- |
| prediction_target | Please specify the material property to be predicted.                  |
| task_type         | Please select the machine learning task type.                          |
| dataset_source    | Please provide the dataset source or data file path.                   |
| input_type        | Please select the input data type.                                     |
| target_column     | Please specify the target column in the dataset.                       |
| evaluation_metric | No evaluation metric is specified. A default metric may be used later. |

#### 冲突字段提示规则

| 冲突情况                                    | 提示信息                                                                                                         |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| regression + Accuracy                   | Accuracy is not suitable for regression tasks. Please select MAE, RMSE, or R2.                               |
| classification + MAE                    | MAE is not suitable for classification tasks. Please select Accuracy, F1, or ROC-AUC.                        |
| structure input but no structure source | Please specify where the structure data is provided, such as CIF files, POSCAR files, or a structure column. |

### 输出

提示信息示例：

```json
{
  "status": "incomplete",
  "missing_fields": ["target_column"],
  "validation_messages": [
    "Please specify the target column in the dataset."
  ]
}
```

---

## 5.7 功能七：标准化任务对象输出

### 功能目标

当用户填写的信息完整且合法后，输出可供后续模块使用的标准化 Task Specification Object。

### 输入

经过表单提交、字段标准化、完整性检查和合法性校验后的任务信息。

### 处理

系统整合所有字段，生成最终任务对象。

处理要求：

1. 保留用户填写的原始字段；
2. 保存系统标准化后的字段；
3. 标记任务状态；
4. 记录缺失字段、警告信息和校验信息；
5. 生成统一格式的 Task Specification Object；
6. 将该对象传递给后续 Task Understanding by LLM 模块。

### 输出

完整任务对象示例：

```json
{
  "task_id": "task_001",
  "task_name": "Band gap prediction",
  "task_description": "Predict experimental band gaps from chemical compositions.",
  "material_system": "inorganic crystals",
  "prediction_target": "experimental band gap",
  "task_type": "regression",
  "dataset_source": "matbench_expt_gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE",
  "user_priority": ["accuracy", "interpretability"],
  "constraints": [],
  "status": "valid",
  "missing_fields": [],
  "validation_messages": []
}
```

---

## 6. MVP 交互流程

### 6.1 正常流程

```text
用户打开任务填写页面
        ↓
系统展示 User Task Specification 表单
        ↓
用户填写任务字段
        ↓
用户提交表单
        ↓
系统进行字段标准化
        ↓
系统进行完整性检查
        ↓
系统进行基础合法性校验
        ↓
输出 valid Task Specification Object
```

### 6.2 信息缺失流程

```text
用户填写表单
        ↓
用户提交表单
        ↓
系统发现必填字段缺失
        ↓
返回 incomplete 状态
        ↓
提示用户补充缺失字段
        ↓
用户修改后重新提交
```

### 6.3 信息冲突流程

```text
用户填写表单
        ↓
用户提交表单
        ↓
系统发现字段冲突
        ↓
返回 invalid 状态
        ↓
提示用户修改冲突字段
        ↓
用户修改后重新提交
```

---

## 7. MVP 验收标准

### 7.1 功能验收标准

MVP 阶段，该模块应满足以下条件：

1. 能展示完整的任务填写表单；
2. 能区分必填字段、选填字段和条件必填字段；
3. 能接收用户提交的结构化字段；
4. 能生成唯一 task_id；
5. 能将表单显示值标准化为系统内部字段；
6. 能识别缺失的必填字段；
7. 能识别明显不匹配的 task_type 与 evaluation_metric；
8. 能返回清晰的错误提示和修改建议；
9. 能输出统一格式的 Task Specification Object；
10. 能将 valid 状态的任务对象传递给后续模块。

### 7.2 示例验收用例

#### 用例一：完整回归任务

用户填写：

```json
{
  "task_name": "Band gap prediction",
  "prediction_target": "experimental band gap",
  "task_type": "Regression",
  "dataset_source": "matbench_expt_gap",
  "input_type": "Chemical composition",
  "target_column": "band_gap",
  "evaluation_metric": "Mean Absolute Error"
}
```

期望输出：

```json
{
  "prediction_target": "experimental band gap",
  "task_type": "regression",
  "dataset_source": "matbench_expt_gap",
  "input_type": "composition",
  "target_column": "band_gap",
  "evaluation_metric": "MAE",
  "status": "valid"
}
```

#### 用例二：缺少目标列

用户填写：

```json
{
  "task_name": "Formation energy prediction",
  "prediction_target": "formation energy",
  "task_type": "Regression",
  "dataset_source": "uploaded_csv",
  "input_type": "Chemical composition",
  "target_column": "",
  "evaluation_metric": "Mean Absolute Error"
}
```

期望输出：

```json
{
  "prediction_target": "formation energy",
  "task_type": "regression",
  "dataset_source": "uploaded_csv",
  "input_type": "composition",
  "target_column": null,
  "status": "incomplete",
  "missing_fields": ["target_column"],
  "validation_messages": [
    "Please specify the target column in the dataset."
  ]
}
```

#### 用例三：指标与任务类型冲突

用户填写：

```json
{
  "task_name": "Band gap prediction",
  "prediction_target": "band gap",
  "task_type": "Regression",
  "dataset_source": "uploaded_csv",
  "input_type": "Chemical composition",
  "target_column": "band_gap",
  "evaluation_metric": "Accuracy"
}
```

期望输出：

```json
{
  "prediction_target": "band gap",
  "task_type": "regression",
  "input_type": "composition",
  "evaluation_metric": "Accuracy",
  "status": "invalid",
  "validation_messages": [
    "Accuracy is not suitable for regression tasks. Please select MAE, RMSE, or R2."
  ]
}
```

---

## 8. MVP 不支持内容

MVP 阶段暂不支持以下能力：

1. 不支持从大段自然语言中自动抽取字段；
2. 不支持多任务联合输入；
3. 不支持多目标预测；
4. 不支持主动联网检索数据集；
5. 不支持自动下载公开数据库；
6. 不支持自动检查数据文件真实存在；
7. 不支持自动读取数据内容；
8. 不支持复杂实验约束解析；
9. 不支持自动生成建模 workflow；
10. 不支持自动选择模型或特征工程策略；
11. 不支持自动生成论文级实验报告。

---

## 9. 设计原则

### 9.1 表单优先

MVP 阶段采用表单输入，而不是自由文本输入，以降低系统理解难度，提高任务输入质量。

### 9.2 必填字段明确

系统应清楚标注哪些字段必须填写，哪些字段可以后续默认处理，避免用户提交不可执行任务。

### 9.3 校验前置

在任务进入后续自动化流程之前，必须先完成完整性检查和基础合法性校验。

### 9.4 不过度推断

用户没有填写的信息不应被系统擅自补全。系统可以提示用户补充，但不应伪造任务字段。

### 9.5 可扩展

字段设计应为后续支持多目标预测、多数据集任务、结构输入、图神经网络输入等复杂场景预留空间。

---

## 10. 模块总结

User Task Specification 模块是整个 AI-driven AutoML 框架的任务入口层。

在 MVP 阶段，它的核心任务是：

> 通过结构化表单收集用户的材料机器学习任务需求，完成字段标准化、完整性检查和基础合法性校验，并输出可供后续模块使用的 Task Specification Object。

该模块不负责自动理解长文本任务描述，也不直接进行建模，而是确保整个自动化机器学习流程建立在清晰、完整、规范的用户任务输入之上。

