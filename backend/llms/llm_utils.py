"""
Shared LLM utility functions.
Extracted from ollama_llm.py and gemini_llm.py to eliminate duplication (DUP-001).
"""

from typing import List
from google.genai import types
from utils.logger import log


def extract_text_from_contents(
    contents: List[types.Content],
    max_history: int = 10,
    log_prefix: str = "LLM",
) -> str:
    """
    Convert a list of ADK Content objects into a flat prompt string.

    - Truncates to the most recent `max_history` turns to reduce token pressure.
    - Preserves role-prefixed lines (騙徒:/專家:/etc.) verbatim.
    - Wraps other turns with 【對話 N】 labels; marks the last turn as 【當前輸入】.

    Args:
        contents:     List of google.genai.types.Content objects from LlmRequest.
        max_history:  Maximum number of turns to keep (default 10).
        log_prefix:   Prefix for log messages (e.g. "OLLAMA" or "GEMINI_LLM").

    Returns:
        A flat string suitable for use as an LLM prompt.
    """
    if not contents:
        return ""

    lines: List[str] = []

    # Truncate to most recent turns
    if len(contents) > max_history:
        contents = contents[-max_history:]
        log.info(f"[{log_prefix}] 對話歷史截斷至最近 {max_history} 條")

    if len(contents) > 1:
        total_length = sum(
            len(getattr(p, "text", ""))
            for c in contents
            if getattr(c, "parts", None)
            for p in c.parts
        )

        if total_length > 4000:
            log.warning(
                f"[{log_prefix}] ⚠️ Prompt 長度 ({total_length} 字元)，已截斷至最近記錄"
            )

        for i, c in enumerate(contents, 1):
            if not getattr(c, "parts", None):
                continue
            role = getattr(c, "role", "user")
            for p in c.parts:
                txt = getattr(p, "text", None)
                if not txt:
                    continue
                # Role-prefixed lines (scammer/expert/victim dialogue) — keep as-is
                if any(
                    prefix in txt
                    for prefix in ["騙徒:", "受騙者:", "專家:", "記錄人:", "你（", "第"]
                ):
                    lines.append(txt)
                else:
                    role_label = "AI" if role == "assistant" else "輸入"
                    if i == len(contents):
                        lines.append(f"【當前輸入】\n{txt}")
                    else:
                        lines.append(f"【對話 {i}】{role_label}: {txt}")

        return "\n\n".join(lines).strip()

    # Single-turn: just concatenate all text parts
    for c in contents:
        if not getattr(c, "parts", None):
            continue
        for p in c.parts:
            txt = getattr(p, "text", None)
            if txt:
                lines.append(txt)

    return "\n".join(lines).strip()
