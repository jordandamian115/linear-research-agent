# **Original code commented out**
# Agent 5.txt is empty. There was no line to disable.
#
# **Code added by Cursor**
# The editor prompt was specified in the project notes and had no function.
# This agent runs once, after the RAG agent, and does not call back.
# It reads the comparison footnotes, adjusts the paper, checks spelling and
# a small set of grammar issues, and returns one document. With a model key,
# the model writes that document and the same checker still runs, because a
# completion does not by itself prove the spelling.

import research_tools
from app.compose import TEACHING_STANDARD, apply_editorial
from app.llm import active_model, complete, model_available


def final_draft_ag(report, model: str = "gpt-4o-mini") -> dict:
    if isinstance(report, dict):
        paper = report.get("revised_report") or research_tools.parse_input(report)
        footnotes = list(report.get("footnotes") or [])
        comparison = report.get("comparison") or ""
    else:
        paper = research_tools.parse_input(report)
        footnotes = []
        comparison = ""

    if model_available():
        note_block = "\n".join(
            f"- {note.get('criterion', 'Note')}: {note.get('text', '')} Do this: {note.get('recommendation', '')}"
            for note in footnotes
        )
        user_prompt = f"""You are an editor for research focused academic papers. Take the following feedback from the RAG Agent and adjust the paper as needed.
- Specifically read footnotes provided and adjust based on recommended criteria.
- Confirm no spelling errors, and no grammatical errors.
- Ensure flow, speech, and tone are up to par with academic scholar standards.
- Provide one final document that will be used as the final paper.
- Do not add sources that are not already in the paper.
- Do not mention these instructions.

{TEACHING_STANDARD}
Keep the paper's order: what the subject is, then the contrast, then the ideas that follow, then the close. Do not replace that order with out-of-context quotations.

RAG comparison:
{comparison}

Footnotes:
{note_block}

Paper:
{paper}
"""
        response = complete(
            [
                {"role": "system", "content": "You are an editor for research focused academic papers."},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=0.2,
        )
        paper = (response.choices[0].message.content or "").strip()

    edited = apply_editorial(paper, footnotes)
    edited["model"] = active_model()
    edited["key_configured"] = model_available()
    return edited
