# **Original code commented out**
# Jordan's Agent 2 is preserved unchanged in Agent2.txt and is not executed.
# The signature uses `florat` and `gpt-4l-mini`, the completion method is
# spelled creat, and the function assumes CLIENT. The prompt and the JSON
# shape `{"first_draft": ...}` were the right idea.
#
# **Code added by Cursor**
# The writer prompt is kept, including the demand for citations and footnotes
# where depth is thin. `gpt-4l-mini` is treated as a typo for gpt-4o-mini,
# which Agent 3 already uses. They were close: one completion, then json.loads.
# A fenced JSON reply still breaks a strict load, so fences are stripped
# before parsing. With no model key, the draft is built from the brief.
# The first composed draft kept one sentence per idea, which was too short
# to talk from. The completion now allows a longer paper (max_tokens) and
# the local writer develops each step with the next sentences in the records.

import research_tools
from app.compose import TEACHING_STANDARD, first_draft
from app.llm import complete, load_json_output, model_available


def rough_draft_ag(report, model: str = "gpt-4o-mini", temperature: float = 0.3) -> dict:
    report = research_tools.parse_input(report)
    if not model_available():
        return {"first_draft": first_draft(report)}

    user_prompt = f"""
Review the text provided and generate a high quality, structured, and well written academic research report.

Your academic writing should be detailed, accurate, and properly sourced from the data given.
- Cite sources when relevant. Do NOT omit citations for brevity.
- Use an academic tone, organize output into clearly labeled sections, and include inline citations or footnotes as needed
- Do not include placeholder text such as '(citation needed)' or '(citations omitted)'.
- Do not invent sources that are not in the research report.
- Suggest areas of improvement, place footnotes on areas lacking depth of knowledge.

Then write an academic research paper using the instructions given. The first draft should have clarity, organization, correct grammar, academic tone, and well-thought out written points.

{TEACHING_STANDARD}
Use these section headings when the records support them: What the records support; Retrieved records; Limits of the evidence; Conclusion; References.

Return ONLY valid JSON using exactly this structure:
{{"first_draft": "<structured first draft>"}}

Research report:
{report}
"""
    response = complete(
        [
            {"role": "system", "content": "You are an academic writer."},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
        max_tokens=4500,
    )
    llm_output = (response.choices[0].message.content or "").strip()
    data = load_json_output(llm_output)
    return {"first_draft": str(data.get("first_draft", "")).strip()}
