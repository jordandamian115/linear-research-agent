# **Original code commented out**
# Jordan's Agent 3 is preserved unchanged in "Agent 3.txt" and is not executed.
# The signature is missing a closing parenthesis (`temerature: float = 0.3 -> dict`),
# the completion method is spelled creat, and CLIENT is undefined. The return
# keys `reflection` and `revised_report` match the prompt. They were close.
#
# **Code added by Cursor**
# The reviewer prompt is kept. The parameter name temperature is spelled as in
# ordinary Python; Agent 3's `temerature` would not run. The prompt mentions
# tools, but the function never passes a tools list, so this pass does not
# search and does not call an earlier agent. With no model key, the revision
# reorganizes the draft already in hand.

import research_tools
from app.compose import TEACHING_STANDARD, revised_report
from app.llm import complete, load_json_output, model_available


def revise_draft_ag(report, model: str = "gpt-4o-mini", temperature: float = 0.3) -> dict:
    report = research_tools.parse_input(report)
    if not model_available():
        return revised_report(report)

    user_prompt = f"""
Review the following academic research report and provide a structured reflection
and an improved revised version of the report.

Your reflection should discuss:
- Strengths of the report
- Limitations or fallthrough
- Assess footnotes already discussing lack of depth of knowledge. Do not call another agent. Work only with the report in front of you.
- Suggestions for improvement
- Opportunities for further improvement or development

Then revise the report using your reflection. The revised report should improve
clarity, organization, accuracy, depth of knowledge, and academic tone while preserving
the important information from the original report. Do not invent sources.

{TEACHING_STANDARD}
Keep the order already in the draft: what the subject is, then the contrast, then the ideas that follow, then the close. Do not turn the paper back into a list of excerpts.

Return ONLY valid JSON using exactly this structure:
{{"reflection": "<structured reflection text>", "revised_report": "<improved version of the report>"}}

Research report:
{report}
"""
    response = complete(
        [
            {"role": "system", "content": "You are an academic reviewer and editor."},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
        temperature=temperature,
    )
    llm_output = (response.choices[0].message.content or "").strip()
    data = load_json_output(llm_output)
    return {
        "reflection": str(data.get("reflection", "")).strip(),
        "revised_report": str(data.get("revised_report", "")).strip(),
    }
