# **Original code commented out**
# Jordan's Agent 1 is preserved unchanged in Agent1.txt and is not executed.
# It cannot run. The system string is unclosed, the completion method is
# spelled creat, the message is read as `response,choices`, the lookup stores
# tool_fun and then calls tool_func, the handler catches Exceptions, and the
# return sits outside the function. CLIENT and TOOL_MAPPING were never defined.
#
# **Code added by Cursor**
# The sketch was close. It already had the right job: a system prompt, the
# arXiv and Tavily tools, a loop of at most ten turns, and a returned first
# text. Those names are kept. When a model key is configured, the loop runs.
# When it is not, the same tools run once each and the brief is composed from
# what they actually return. The prompt's other catalogs (Clarivate, Scopus,
# IEEE) are not called, because tools.txt does not define them.

import json

import research_tools
from app.compose import research_brief
from app.llm import complete, model_available

SYSTEM_PROMPT = """You are an academic scholar designated with researching topics and producing notable, trusted, scholarly websites and sources to be eventually used in writing a paper.
Your goals:
- Gather clear concise information to be presented in an orderly and readable fashion
- Review articles found from the available search tools about the topic in question
- Compare peer-reviewed articles to find unbiased, research driven answers
- Notate any fallthrough in the information available, leading you to be unable to give a full and complete answer

You have the following tools available:
- arxiv_search: to find papers on arXiv
- tavily_search: to search the web for relevant sources

Use the tools. Do not invent citations. If the tools return little, say so."""


def res_ag(prompt: str, model: str = "gpt-4o") -> str:
    if not model_available():
        print("arxiv_search")
        arxiv = research_tools.arxiv_search(prompt)
        print("tavily_search")
        web = research_tools.tavily_search(prompt)
        # The first 400 characters of the brief are mostly the arXiv note.
        # Print the Tavily status and titles on their own so a keyless
        # failure is not mistaken for an empty success.
        print(
            f"tavily_search status={web.get('status')} "
            f"key_present={'yes' if web.get('key_present') else 'no'} "
            f"pages={len(web.get('results') or [])} mode={web.get('mode')}"
        )
        for item in web.get("results") or []:
            print(f"tavily: {item.get('title')} {item.get('url')}")
        if web.get("note"):
            print(f"tavily note: {web.get('note')}")
        first_text = research_brief(prompt, arxiv, web)
        print("First answer:")
        print(first_text[:400])
        return first_text

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    tools = [research_tools.arxiv_tool_def, research_tools.tavily_tool_def]
    max_turns = 10
    first_text = ""

    for _ in range(max_turns):
        response = complete(messages, model=model, tools=tools, temperature=1)
        msg = response.choices[0].message
        messages.append(_assistant_message(msg))
        if not msg.tool_calls:
            first_text = msg.content or ""
            print("First answer:")
            print(first_text)
            break
        for call in msg.tool_calls:
            tool_name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            print(f"{tool_name}({args})")
            try:
                tool_func = research_tools.TOOL_MAPPING[tool_name]
                result = tool_func(**args)
            except Exception as exc:
                result = {"error": str(exc)}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": tool_name,
                    "content": json.dumps(result),
                }
            )
    if not first_text:
        first_text = "The research agent stopped before it produced a brief."
    return first_text


def _assistant_message(msg) -> dict:
    payload = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        payload["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments or "{}",
                },
            }
            for call in msg.tool_calls
        ]
    return payload
