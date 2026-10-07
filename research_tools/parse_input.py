# **Code added by Cursor**
# Agent 2 and Agent 3 both call research_tools.parse_input. No definition
# exists in the uploaded project. They were close in how they use it: the
# docstring says the editor should accept raw text or a messages list.
# This helper does that, and it also accepts the dicts later agents return,
# so a linear handoff can pass the previous result through unchanged.

import json


def parse_input(report) -> str:
    if report is None:
        return ""
    if isinstance(report, str):
        return report.strip()
    if isinstance(report, dict):
        for key in (
            "final_paper",
            "revised_report",
            "first_draft",
            "paper",
            "content",
            "text",
        ):
            value = report.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(report, indent=2)
    if isinstance(report, list):
        parts = []
        for item in report:
            if isinstance(item, dict):
                content = item.get("content")
                if content:
                    parts.append(str(content))
            elif item:
                parts.append(str(item))
        return "\n\n".join(parts).strip()
    return str(report).strip()
