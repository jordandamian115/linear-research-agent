# **Code added by Cursor**
# Jordan's agents call CLIENT.chat.completions and pass model names such as
# gpt-4o and gpt-4l-mini. A later note treats Grok 4o mini as a placeholder
# for whatever model can actually run. No key is in the project, CLIENT was
# never created, and gpt-4l-mini is not a real model id. They were close:
# the call shape and a model argument are right. This uses Grok when
# XAI_API_KEY is set, otherwise the OpenAI models named in the notes when
# OPENAI_API_KEY is set. With neither key, callers compose from search
# results instead of pretending a model answered.

import json
import os

import research_tools

_OPENAI_PLACEHOLDERS = {"gpt-4l-mini", "grok-4o-mini", "grok 4o mini"}


def _xai_key() -> str:
    return os.environ.get("XAI_API_KEY", "").strip() or os.environ.get("GROK_API_KEY", "").strip()


def _openai_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def provider() -> str:
    research_tools.load_local_env()
    if _xai_key():
        return "xai"
    if _openai_key():
        return "openai"
    return "local"


def model_available() -> bool:
    return provider() != "local"


def active_model() -> str:
    """Name of the model that will run, or local when no key is set."""
    if provider() == "xai":
        return os.environ.get("XAI_MODEL", "").strip() or "grok-3-mini"
    if provider() == "openai":
        return os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    return "local"


def resolve_model(requested: str | None) -> str:
    chosen = active_model()
    if provider() == "openai":
        name = (requested or "").strip()
        if name and name not in _OPENAI_PLACEHOLDERS and not name.lower().startswith("grok"):
            return name
    return chosen


def complete(messages: list[dict], model: str, temperature: float = 0.3, tools: list | None = None):
    if not model_available():
        raise RuntimeError("No model key is configured.")
    from openai import OpenAI

    chosen = resolve_model(model)
    if provider() == "xai":
        client = OpenAI(api_key=_xai_key(), base_url="https://api.x.ai/v1")
    else:
        client = OpenAI(api_key=_openai_key())
    kwargs = {
        "model": chosen,
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
