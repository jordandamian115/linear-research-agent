# **Original code commented out**
# Nothing in tools.txt was commented out. That file is preserved unchanged and
# is executed below so arxiv_tool_def and tavily_tool_def stay Jordan's.
#
# **Code added by Cursor**
# tools.txt is close: the two function schemas are valid and match the tool
# names Agent 1 tries to call (arxiv_search, tavily_search). It was not
# sufficient, because a schema does not search anything, and Agent 2 and
# Agent 3 call research_tools.parse_input, which was never defined.

import os
from pathlib import Path

from research_tools.arxiv_search import arxiv_search
from research_tools.parse_input import parse_input
from research_tools.tavily_search import tavily_search

_ROOT = Path(__file__).resolve().parents[1]
_namespace = {}
exec(compile((_ROOT / "tools.txt").read_text(encoding="utf-8"), "tools.txt", "exec"), _namespace)

arxiv_tool_def = _namespace["arxiv_tool_def"]
tavily_tool_def = _namespace["tavily_tool_def"]

TOOL_MAPPING = {
    "arxiv_search": arxiv_search,
    "tavily_search": tavily_search,
}


def load_local_env() -> None:
    """Read an untracked .env without overriding variables already set."""
    path = _ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env()

__all__ = [
    "TOOL_MAPPING",
    "arxiv_search",
    "arxiv_tool_def",
    "load_local_env",
    "parse_input",
    "tavily_search",
    "tavily_tool_def",
]
