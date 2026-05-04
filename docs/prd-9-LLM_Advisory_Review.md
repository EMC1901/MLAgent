# PRD：LLM Advisory Review 优化方案

> 所属系统：MLAgent — AI-driven AutoML for Materials Science
> 所属模块：Executable Pipeline Generation
> 优化对象：LLM Pipeline Review
> 优化后名称建议：LLM Advisory Review / LLM Risk Review
> 文档角色：产品经理、后端架构师、前端工程师、AI Agent 系统设计专家
> 版本：v1.0

---

## 1. 背景说明

当前 **Executable Pipeline Generation** 模块已经可以基于上游 `Model Search Plan` 生成结构化的 Pipeline Spec，并通过系统 Validator 和 Safety Checker 判断是否可以进入后续训练执行阶段。

当前模块中引入了 **LLM Pipeline Review**，用于让 LLM 对生成后的 Pipeline 进行辅助审查。但在实际运行中出现了如下结果：

```text
LLM Pipeline Review (Advisory Only)
LLM Review is advisory only. System Validator is authoritative.
Confidence: 0%
needs_improvement
```

从日志看，LLM 调用本身成功，但真实模型返回了较保守的评审意见，例如：

```json
{
  "overall_assessment": "needs_improvement",
  "approval_status": "conditional"
}
```

这说明当前问题不是 Pipeline Generation 失败，也不是 LLM 调用失败，而是：

> LLM Review 的职责定义、Prompt 约束、Schema 设计、结果归一化和前端呈现方式仍需优化。

---

## 2. 当前问题分析

### 2.1 LLM 被误导成“审批者”

当前的 “Pipeline Review” 容易让 LLM 理解为：

```text
请判断这个 Pipeline 是否足够好，是否应该批准。
```

这会导致 LLM 输出：

```text
needs_improvement
conditional
not approved
low confidence
```

但在 MLAgent 的架构中，LLM 不应该承担审批职责。

---

### 2.2 LLM Review 与 System Validator 职责混淆

当前系统中：

* **System Validator** 判断 Pipeline 是否结构合法、组件合法、路径合法、安全可控；
* **Safety Checker** 判断是否存在代码注入、非法路径、未注册组件等风险；
* **LLM Review** 应该只提供机器学习实践层面的非阻塞建议。

因此，LLM Review 不应该影响：

```text
ready_for_execution
```

---

### 2.3 Confidence 以百分比展示容易误导用户

`Confidence: 0%` 会让用户以为：

* Pipeline 生成失败；
* LLM 不认可结果；
* 当前模块不可进入下一步；
* 系统可靠性存在问题。

但实际上，这只是 LLM 对自身评审意见的不确定性，并不代表系统生成的 Pipeline 不可执行。

---

### 2.4 LLM 自创字段影响系统一致性

LLM 返回了：

```json
{
  "approval_status": "conditional"
}
```

这类字段不应进入主业务逻辑，也不应直接作为前端主结论展示。

系统应通过后端 Normalizer 将 LLM 原始输出转换为稳定、可控、可解释的结构化 Advisory Review。

---

## 3. 优化目标

### 3.1 产品目标

将当前的 **LLM Pipeline Review** 优化为：

```text
LLM Advisory Review
```

或：

```text
LLM Risk Review
```

其产品定位为：

> LLM 仅提供非阻塞的机器学习风险提示和后续优化建议，不负责批准、拒绝、修改或执行 Pipeline。

---

### 3.2 技术目标

本次优化需要实现：

1. 明确 LLM Review 不参与 `ready_for_execution` 判定；
2. 修改 Prompt，避免 LLM 输出审批式结论；
3. 收紧 LLM 输出 Schema；
4. 增加后端 Normalizer，统一处理 LLM 原始输出；
5. 增加后端 Validator，过滤非法字段和代码内容；
6. 优化前端展示，将系统校验结果作为主结论；
7. 将 LLM Review 放到 Advisory Notes 层级展示；
8. 避免显示 `Confidence: 0%` 这种误导性表达；
9. 保留 LLM 对 Pipeline 风险的解释价值；
10. 保持系统安全、稳定、可控。

---

## 4. 优化后模块定位

### 4.1 一句话定义

**LLM Advisory Review 是 Pipeline Generation 中的非阻塞式智能审查组件，用于提示机器学习实践风险和后续优化建议，但不决定 Pipeline 是否可执行。**

---

### 4.2 在 Pipeline Generation 中的位置

```text
Model Search Plan
    ↓
Pipeline Spec Builder
    ↓
System Validator
    ↓
Safety Checker
    ↓
LLM Advisory Review     ← 非阻塞建议层
    ↓
Execution Input Builder
    ↓
Pipeline Execution
```

注意：

```text
ready_for_execution 只能由 System Validator + Safety Checker + Artifact Check 决定。
```

---

## 5. 核心设计原则

### 5.1 Advisory Only

LLM Review 只能提供建议，不参与执行审批。

允许输出：

* 风险提示；
* 一致性观察；
* 资源风险；
* 后续优化建议；
* 人工关注点。

不允许输出：

* approve；
* reject；
* conditional approval；
* executable code；
* pipeline 修改方案；
* 模型实例化逻辑；
* HPO 执行逻辑。

---

### 5.2 System Validator Authoritative

系统权威判断逻辑必须保持为：

```text
ready_for_execution =
    pipeline_validation_result.is_valid
    AND safety_check_result.is_safe
    AND artifact_manifest.is_complete
    AND n_pipeline_specs > 0
```

不得加入：

```text
LLM approval_status
LLM overall_assessment
LLM confidence_score
LLM risk_level
```

---

### 5.3 LLM 输出不可信

所有 LLM 输出必须经过：

```text
Parser → Validator → Normalizer → Display Mapper
```

不得将 LLM 原始输出直接进入前端主展示区。

---

### 5.4 低置信度不是失败

LLM 的低置信度应被解释为：

```text
由于尚未执行训练、没有真实指标结果，LLM 对风险判断较谨慎。
```

而不是：

```text
Pipeline 不可用。
```

---

## 6. 优化范围

### 6.1 本次优化包含

后端：

1. 修改 LLM Review Prompt；
2. 重构 LLM Review 输出 Schema；
3. 新增 `llm_review_normalizer.py`；
4. 新增或增强 `llm_review_validator.py`；
5. 调整 `llm_pipeline_reviewer.py` 的结果处理逻辑；
6. 调整 `builder.py` 中的 review 输出结构；
7. 确保 `ready_for_execution` 不依赖 LLM Review；
8. 记录 raw LLM response，但不直接展示为主结论。

前端：

1. 将标题从 `LLM Pipeline Review` 改为 `LLM Advisory Review`；
2. 将 `Confidence: 0%` 改为 `Review confidence: Low`；
3. 用 `Review impact: Non-blocking` 替代审批式结论；
4. System Validator 作为主展示；
5. LLM Review 放在折叠式 Advisory 卡片；
6. 优化颜色和文案，避免误导用户。

---

### 6.2 本次优化不包含

1. 不重写 Pipeline Generation 主流程；
2. 不修改 PipelineSpec 生成逻辑；
3. 不修改 Model Search Plan；
4. 不修改 HPO 计划；
5. 不执行训练；
6. 不计算指标；
7. 不让 LLM 生成代码；
8. 不让 LLM 修改 Pipeline；
9. 不增加用户手动编辑 Pipeline 逻辑。

---

## 7. 用户故事

### 7.1 作为材料科学研究者

我希望系统在生成 Pipeline 后告诉我有哪些潜在风险，而不是让我误以为 LLM 的保守评价代表系统失败。

---

### 7.2 作为系统开发者

我希望 LLM Review 的输出结构稳定，不会因为 LLM 自创字段导致前端展示混乱或后端状态判断异常。

---

### 7.3 作为 AI Agent 系统设计者

我希望 LLM 深度参与审查和解释，但最终执行决策仍然由系统 Validator、Registry 和 Safety Checker 控制。

---

### 7.4 作为前端用户

我希望清楚看到：

```text
系统是否通过校验；
是否可以进入训练；
LLM 只是给出了哪些非阻塞建议。
```

---

## 8. 新的产品定义

建议将前端和文档中的说明统一改为：

```text
LLM Advisory Review provides non-blocking machine learning risk notes for human awareness. It does not approve, reject, modify, or execute generated pipelines. Execution readiness is determined only by the System Validator and Safety Checker.
```

中文说明：

```text
LLM 建议性审查仅用于提示潜在机器学习风险和后续优化方向，不负责批准、拒绝、修改或执行 Pipeline。是否可以进入训练执行阶段，只由系统 Validator 和 Safety Checker 决定。
```

---

## 9. 后端设计

## 9.1 推荐新增或调整文件

当前 Pipeline Generation 模块中建议新增或调整：

```text
backend/app/modules/pipeline_generation/
    ├── llm_review_prompt_builder.py
    ├── llm_pipeline_reviewer.py
    ├── llm_review_parser.py
    ├── llm_review_validator.py
    ├── llm_review_normalizer.py      ← 新增重点
    ├── builder.py
    ├── schemas.py
    └── service.py
```

---

## 9.2 后端处理流程

优化后的 LLM Advisory Review 流程：

```text
Pipeline Bundle 已由系统生成
    ↓
System Validator 完成
    ↓
Safety Checker 完成
    ↓
构建 LLM Advisory Review Prompt
    ↓
调用 LLM
    ↓
解析 LLM 原始 JSON
    ↓
Validator 检查结构、安全和非法字段
    ↓
Normalizer 归一化为系统标准结构
    ↓
写入 pipeline_json.llm_advisory_review
    ↓
前端展示 Advisory 结果
```

注意：

```text
LLM Advisory Review 的任何结果都不能改变 ready_for_execution。
```

---

# 10. Prompt 优化方案

## 10.1 Prompt 目标

新的 Prompt 必须让 LLM 明确：

1. 它不是审批器；
2. 它不能拒绝 Pipeline；
3. 它不能修改 Pipeline；
4. 它不能输出代码；
5. 它只能识别非阻塞风险；
6. 如果没有严重问题，应输出 `execution_impact = non_blocking`。

---

## 10.2 Prompt 核心指令建议

建议 Prompt 中加入以下核心规则：

```text
You are an advisory reviewer for a generated machine learning pipeline specification.

The system validator has already checked structural validity, registry validity, artifact availability, and safety constraints.

Your role is NOT to approve, reject, modify, or execute the pipeline.

Your role is only to identify non-blocking machine learning practice risks and future improvement suggestions.

Do not output executable code.
Do not output Python code.
Do not modify pipeline specifications.
Do not invent new models.
Do not invent new HPO methods.
Do not output approval_status.
Do not output approved, rejected, conditional, or needs_improvement.

If no blocking issue is found, set execution_impact to "non_blocking".
```

---

## 10.3 Review Rubric

Prompt 中应给 LLM 固定审查维度，避免泛泛评价。

推荐维度：

| 维度                                | 说明              |
| --------------------------------- | --------------- |
| `model_task_compatibility`        | 模型是否适合当前任务类型    |
| `baseline_coverage`               | 是否包含合理 baseline |
| `hpo_budget_reasonableness`       | HPO trial 数是否合理 |
| `validation_strategy_suitability` | 验证策略是否适合样本量     |
| `metric_consistency`              | 指标是否与任务类型一致     |
| `overfitting_risk`                | 是否存在过拟合风险       |
| `resource_cost_risk`              | 是否存在资源消耗风险      |
| `reproducibility_readiness`       | 是否具备可复现基础       |

每个维度只能输出：

```text
pass / warning / not_applicable
```

---

# 11. 新的 LLM 输出 Schema

## 11.1 推荐标准结构

```json
{
  "review_status": "advisory_completed",
  "execution_impact": "non_blocking",
  "risk_level": "low",
  "checklist": [
    {
      "dimension": "model_task_compatibility",
      "status": "pass",
      "comment": "All selected models are compatible with the regression task."
    },
    {
      "dimension": "hpo_budget_reasonableness",
      "status": "warning",
      "comment": "The HPO budget may be conservative for comparing multiple candidate models."
    }
  ],
  "blocking_issues": [],
  "non_blocking_risks": [
    {
      "category": "hpo_budget",
      "severity": "low",
      "message": "The current HPO budget may limit model comparison depth.",
      "suggested_action": "Consider increasing max_total_trials in future runs if runtime allows."
    }
  ],
  "resource_warnings": [],
  "future_improvement_suggestions": [
    "After training, compare validation variance across folds to assess model stability."
  ],
  "confidence_level": "medium"
}
```

---

## 11.2 字段定义

| 字段                               | 类型     | 必填 | 说明                                       |
| -------------------------------- | ------ | -: | ---------------------------------------- |
| `review_status`                  | string |  是 | `advisory_completed` / `advisory_failed` |
| `execution_impact`               | string |  是 | `non_blocking` / `potentially_blocking`  |
| `risk_level`                     | string |  是 | `none` / `low` / `medium` / `high`       |
| `checklist`                      | array  |  是 | 固定维度审查结果                                 |
| `blocking_issues`                | array  |  是 | 理论阻塞问题，通常为空                              |
| `non_blocking_risks`             | array  |  是 | 非阻塞风险                                    |
| `resource_warnings`              | array  |  是 | 资源风险                                     |
| `future_improvement_suggestions` | array  |  是 | 后续优化建议                                   |
| `confidence_level`               | string |  是 | `low` / `medium` / `high`                |

---

## 11.3 禁止字段

Validator 应拒绝或忽略以下字段：

```text
approval_status
approved
rejected
conditional
needs_improvement
final_decision
execution_allowed
ready_for_execution
modify_pipeline
recommended_code
python_code
```

如果 LLM 返回这些字段，后端不应直接展示，应交给 Normalizer 处理。

---

# 12. Normalizer 设计

## 12.1 为什么需要 Normalizer

即使 Prompt 和 Schema 写得严格，LLM 仍可能返回不完全符合预期的内容。

因此需要新增：

```text
llm_review_normalizer.py
```

负责将 LLM 原始输出转换成系统标准结构。

---

## 12.2 Normalizer 输入

可能输入：

```json
{
  "overall_assessment": "needs_improvement",
  "approval_status": "conditional",
  "confidence_score": 0
}
```

---

## 12.3 Normalizer 输出

统一转换为：

```json
{
  "review_status": "advisory_completed",
  "execution_impact": "non_blocking",
  "risk_level": "medium",
  "checklist": [],
  "blocking_issues": [],
  "non_blocking_risks": [],
  "resource_warnings": [],
  "future_improvement_suggestions": [],
  "confidence_level": "low",
  "normalization_notes": [
    "LLM returned non-standard approval-style fields. They were normalized into advisory review fields."
  ],
  "raw_llm_summary": {
    "overall_assessment": "needs_improvement",
    "approval_status": "conditional"
  }
}
```

---

## 12.4 Normalization 规则

| LLM 原始字段                                 | 处理方式                                     |
| ---------------------------------------- | ---------------------------------------- |
| `overall_assessment = needs_improvement` | 转为 `risk_level = medium`                 |
| `approval_status = conditional`          | 不参与决策，仅记录到 `raw_llm_summary`             |
| `confidence_score = 0`                   | 转为 `confidence_level = low`              |
| `approved/rejected`                      | 不参与决策，仅记录                                |
| 缺少 checklist                             | 填充空数组                                    |
| 缺少 risk_level                            | 默认 `low`                                 |
| 缺少 execution_impact                      | 默认 `non_blocking`                        |
| 出现代码片段                                   | 标记 `advisory_failed`，但不影响系统 Validator 结果 |

---

# 13. Validator 设计

## 13.1 Validator 职责

`llm_review_validator.py` 负责：

1. 校验 JSON 是否可解析；
2. 校验字段类型；
3. 校验枚举值；
4. 检查禁止字段；
5. 检查禁止代码内容；
6. 判断是否可以进入 Normalizer；
7. 输出 validation warnings。

---

## 13.2 安全扫描规则

必须扫描以下内容：

```text
import
def
class
eval(
exec(
subprocess
os.system
open(
write(
delete
remove
shutil
sklearn.
model.fit
Pipeline(
optuna.create_study
```

发现后：

* 不执行；
* 不采纳；
* 记录为 `llm_review_safety_warning`；
* 将 `review_status` 归一化为 `advisory_failed` 或 `advisory_completed_with_warning`。

---

# 14. 后端数据结构调整

## 14.1 PipelineGenerationResponse 中的字段建议

将原来的：

```text
llm_pipeline_review
```

调整为：

```text
llm_advisory_review
```

结构如下：

```json
{
  "enabled": true,
  "review_status": "advisory_completed",
  "execution_impact": "non_blocking",
  "risk_level": "low",
  "confidence_level": "medium",
  "checklist": [],
  "blocking_issues": [],
  "non_blocking_risks": [],
  "resource_warnings": [],
  "future_improvement_suggestions": [],
  "normalization_notes": [],
  "raw_llm_summary": {}
}
```

---

## 14.2 保留 raw response

数据库中可以继续保留：

```text
llm_response_json
```

但前端默认不直接展示 raw response。

如需调试，可放入 Full JSON 或 Debug 区域。

---

# 15. ready_for_execution 决策规则

必须明确：

```text
ready_for_execution 不受 LLM Advisory Review 影响。
```

唯一决策公式：

```text
ready_for_execution =
    pipeline_validation_result.is_valid
    AND safety_check_result.is_safe
    AND artifact_manifest.is_complete
    AND n_pipeline_specs > 0
```

LLM Advisory Review 只能影响：

```text
warnings
advisory_notes
future_improvement_suggestions
human_review_items
```

---

# 16. 前端设计

## 16.1 标题调整

当前标题：

```text
LLM Pipeline Review
```

建议改为：

```text
LLM Advisory Review
```

或中文：

```text
LLM 建议性审查
```

副标题：

```text
Non-blocking machine learning risk notes. System Validator determines execution readiness.
```

中文：

```text
仅提供非阻塞的机器学习风险提示。是否可执行由系统 Validator 和 Safety Checker 决定。
```

---

## 16.2 信息层级调整

前端展示优先级应调整为：

```text
1. Pipeline Generation Status
2. System Validator Result
3. Safety Checker Result
4. Ready for Execution
5. LLM Advisory Review
6. Full JSON
```

不要把 LLM Review 作为主结论。

---

## 16.3 推荐展示样式

### 主状态区

```text
Pipeline Generation: Generated
System Validation: Passed
Safety Check: Passed
Ready for Execution: Yes
```

### LLM Advisory 区

```text
LLM Advisory Review
Impact: Non-blocking
Risk Level: Medium
Review Confidence: Low

The LLM found improvement suggestions, but no system-blocking issue was detected.
```

---

## 16.4 不推荐展示

不要直接展示：

```text
Confidence: 0%
needs_improvement
conditional
```

---

## 16.5 Confidence 展示规则

后端输出：

```text
confidence_level: low / medium / high
```

前端展示：

| confidence_level | 展示文案                      |
| ---------------- | ------------------------- |
| `low`            | Review confidence: Low    |
| `medium`         | Review confidence: Medium |
| `high`           | Review confidence: High   |

如需提示：

```text
Low confidence is expected before actual training metrics are available.
```

中文：

```text
在尚未执行训练、缺少真实指标结果前，LLM 审查置信度较低是正常现象。
```

---

## 16.6 风险等级展示

| risk_level | 颜色         | 文案                                           |
| ---------- | ---------- | -------------------------------------------- |
| `none`     | green      | No notable advisory risk                     |
| `low`      | blue       | Low advisory risk                            |
| `medium`   | orange     | Medium advisory risk                         |
| `high`     | red/orange | High advisory risk, human review recommended |

注意：

即使 `risk_level = high`，也不自动阻止执行。是否阻止执行仍由系统 Validator 决定。

---

# 17. 前端组件调整

建议调整或新增组件：

```text
frontend/src/modules/pipelineGeneration/components/
    ├── LLMPipelineReviewCard.tsx      ← 可重命名
    ├── LLMAdvisoryReviewCard.tsx      ← 推荐新名称
    ├── AdvisoryRiskList.tsx
    ├── AdvisoryChecklistTable.tsx
    └── AdvisoryNotice.tsx
```

---

## 17.1 LLMAdvisoryReviewCard 展示内容

包含：

1. Advisory Only 提示；
2. execution impact；
3. risk level；
4. confidence level；
5. checklist；
6. non-blocking risks；
7. resource warnings；
8. future improvement suggestions；
9. normalization notes；
10. raw response 折叠调试区，可选。

---

# 18. API 输出示例

## 18.1 正常输出示例

```json
{
  "success": true,
  "message": "Pipeline generation completed successfully",
  "data": {
    "pipeline_generation_id": "pg_a1b2c3d4",
    "status": "generated",
    "ready_for_execution": true,
    "pipeline_validation_result": {
      "is_valid": true
    },
    "safety_check_result": {
      "is_safe": true
    },
    "llm_advisory_review": {
      "enabled": true,
      "review_status": "advisory_completed",
      "execution_impact": "non_blocking",
      "risk_level": "medium",
      "confidence_level": "low",
      "checklist": [
        {
          "dimension": "model_task_compatibility",
          "status": "pass",
          "comment": "All selected models are compatible with the regression task."
        },
        {
          "dimension": "hpo_budget_reasonableness",
          "status": "warning",
          "comment": "The HPO budget may be conservative for the number of candidate models."
        }
      ],
      "blocking_issues": [],
      "non_blocking_risks": [
        {
          "category": "hpo_budget",
          "severity": "medium",
          "message": "The trial budget may limit search depth.",
          "suggested_action": "Consider increasing max_total_trials in future runs if runtime allows."
        }
      ],
      "resource_warnings": [],
      "future_improvement_suggestions": [
        "After training, inspect validation variance across folds."
      ],
      "normalization_notes": []
    }
  }
}
```

---

## 18.2 LLM 自创字段后的归一化输出示例

LLM 原始输出：

```json
{
  "overall_assessment": "needs_improvement",
  "approval_status": "conditional",
  "confidence_score": 0
}
```

后端标准输出：

```json
{
  "enabled": true,
  "review_status": "advisory_completed",
  "execution_impact": "non_blocking",
  "risk_level": "medium",
  "confidence_level": "low",
  "checklist": [],
  "blocking_issues": [],
  "non_blocking_risks": [],
  "resource_warnings": [],
  "future_improvement_suggestions": [],
  "normalization_notes": [
    "LLM returned non-standard approval-style fields. They were normalized into advisory review fields."
  ],
  "raw_llm_summary": {
    "overall_assessment": "needs_improvement",
    "approval_status": "conditional"
  }
}
```

---

# 19. 异常与降级策略

## 19.1 LLM Review 调用失败

如果 LLM Review 调用失败：

* Pipeline Generation 主流程不失败；
* `ready_for_execution` 不受影响；
* 输出 fallback advisory review。

示例：

```json
{
  "enabled": true,
  "review_status": "advisory_unavailable",
  "execution_impact": "non_blocking",
  "risk_level": "unknown",
  "confidence_level": "low",
  "non_blocking_risks": [],
  "future_improvement_suggestions": [],
  "normalization_notes": [
    "LLM advisory review was unavailable. System validation remains authoritative."
  ]
}
```

---

## 19.2 LLM 输出非法代码

如果 LLM 输出代码：

* 标记 LLM Review 为失败或带警告；
* 不采纳该输出；
* 不影响系统 Validator；
* 不影响 ready 状态；
* 记录安全警告。

---

# 20. 配置项建议

可在 settings 中增加：

```text
PIPELINE_REVIEW_LLM_ENABLED=true
PIPELINE_REVIEW_STRICT_SCHEMA=true
PIPELINE_REVIEW_NORMALIZE_NONSTANDARD_OUTPUT=true
PIPELINE_REVIEW_SHOW_RAW_OUTPUT=false
PIPELINE_REVIEW_TIMEOUT_SECONDS=60
```

---

# 21. 验收标准

## 21.1 后端验收标准

必须满足：

1. LLM Review 输出字段统一为 `llm_advisory_review`；
2. 不再将 `approval_status` 作为业务字段；
3. 不再让 `overall_assessment` 直接作为前端主结论；
4. `ready_for_execution` 不依赖 LLM Review；
5. LLM 原始输出经过 Validator；
6. LLM 原始输出经过 Normalizer；
7. LLM 返回非标准字段时系统可正常处理；
8. LLM 返回 `confidence_score = 0` 时前端不显示 `0%`；
9. LLM 调用失败时 Pipeline Generation 不失败；
10. LLM 输出代码时不会被采纳；
11. raw LLM response 仅用于调试或 JSON 查看；
12. 所有结果持久化到数据库。

---

## 21.2 前端验收标准

必须满足：

1. 页面标题改为 `LLM Advisory Review`；
2. 明确显示 `Advisory Only`；
3. 主状态区域优先展示 System Validator；
4. `ready_for_execution` 显示不受 LLM Review 影响；
5. 不直接显示 `needs_improvement` 作为主结论；
6. 不显示 `Confidence: 0%`；
7. 显示 `Review confidence: Low / Medium / High`；
8. 显示 `Impact: Non-blocking`；
9. 风险和建议以列表展示；
10. raw response 默认折叠或隐藏。

---

## 21.3 安全验收标准

必须满足：

1. LLM 不得生成可执行代码；
2. LLM 不得修改 PipelineSpec；
3. LLM 不得新增模型；
4. LLM 不得新增 HPO 方法；
5. LLM 不得改变 ready 状态；
6. LLM 不得绕过 System Validator；
7. 所有 LLM 输出都必须经过安全扫描。

---

# 22. 推荐实现优先级

## P0：必须完成

1. 修改 Prompt；
2. 修改标准 Schema；
3. 新增 Normalizer；
4. 增强 Validator；
5. 修改 ready_for_execution 依赖逻辑确认；
6. 修改前端标题和展示文案；
7. 不再显示 `Confidence: 0%`。

---

## P1：建议完成

1. 增加 checklist 展示；
2. 增加 risk level 显示；
3. 增加 normalization notes；
4. 增加 raw response 折叠查看；
5. 增加配置项控制 LLM Review 是否启用。

---

## P2：后续迭代

1. 根据训练结果进一步增强 LLM Review；
2. 在 Result Diagnosis 阶段复用 advisory notes；
3. 增加历史 Pipeline Review 对比；
4. 增加模型组合质量评分；
5. 增加领域知识规则库。

---

# 23. 总结

本次优化的核心不是让 LLM “更乐观”，而是让 LLM 扮演正确的角色。

当前问题的根源是：

```text
LLM Review 被设计得像审批器。
```

优化后的设计应变为：

```text
LLM Advisory Review 是非阻塞的风险提示器。
```

最终架构应保持：

```text
System Validator 决定结构是否合法；
Safety Checker 决定是否安全；
Artifact Resolver 决定输入是否完整；
LLM Advisory Review 只提供机器学习实践建议；
ready_for_execution 不受 LLM Review 影响。
```

这样既保留了 LLM 深度参与，又不会破坏 MLAgent “安全、稳定、可控、LLM 不直接执行代码”的核心原则。
