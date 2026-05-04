import json
import re
from typing import Dict, Any
from app.modules.model_search_context.exceptions import LLMOutputParseException

CODE_BLOCK_PATTERN = re.compile(
    r"```(?:json)?\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)


def has_executable_code(text: str) -> bool:
    code_patterns = [
        r"```python",
        r"```shell",
        r"```bash",
        r"```sql",
        r"```sh",
        r"import\s+(os|sys|subprocess|pickle|eval|exec)\b",
        r"__import__\s*\(",
        r"eval\s*\(",
        r"exec\s*\(",
        r"subprocess\.",
        r"os\.(system|popen|exec)",
        r"def\s+\w+\s*\(.*\)\s*:",
    ]
    for pattern in code_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def parse_llm_response(raw_text: str) -> Dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise LLMOutputParseException("LLM returned empty response.")

    if has_executable_code(raw_text):
        raise LLMOutputParseException(
            "LLM response contains executable code, which is forbidden."
        )

    cleaned = raw_text.strip()

    match = re.search(CODE_BLOCK_PATTERN, cleaned)
    if match:
        cleaned = match.group(1).strip()
        if has_executable_code(cleaned):
            raise LLMOutputParseException(
                "LLM response code block contains executable code, which is forbidden."
            )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise LLMOutputParseException(
            f"Failed to parse LLM output as JSON: {str(e)}. "
            f"Raw text (first 500 chars): {raw_text[:500]}"
        )
