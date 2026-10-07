# **Code added by Cursor**
# Jordan's agents call CLIENT.chat.completions, but CLIENT is never created
# and no key is in the project. This wrapper uses a model only when
# OPENAI_API_KEY is present. Otherwise the agents compose from retrieved
# records. Their call shape was close; the client and the key were missing.

import json
import os

import research_tools


def model_available() -> bool:
    research_tools.load_local_env()
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def complete(messages: list[dict], model: str, temperature: float = 0.3, tools: list | None = None):
    if not model_available():
        raise RuntimeError("No model key is configured.")
    from openai import OpenAI

    client = OpenAI()
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**kwargs)


def load_json_output(llm_output: str) -> dict:
    """Accept raw JSON or a fenced block. Their loaders rejected the fence."""
    candidate = (llm_output or "").strip()
    if candidate.startswith("```"):
        candidate = candidate.split("\n", 1)[-1]
        if "```" in candidate:
            candidate = candidate[: candidate.rfind("```")]
    try:
        data = json.loads(candidate.strip())
    except json.JSONDecodeError as exc:
        raise Exception("The output of the LLM was not valid JSON. Adjust your prompt.") from exc
    if not isinstance(data, dict):
        raise Exception("The output of the LLM was not valid JSON. Adjust your prompt.")
    return data
