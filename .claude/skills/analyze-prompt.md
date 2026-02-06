---
name: analyze-prompt
description: Review and suggest improvements to job analyzer LLM prompts
user-invocable: true
---

# Analyze Prompt

Review the LLM prompts used in the job analysis pipeline and suggest improvements.

## Instructions

1. Read the full prompt file: `backend/llm/prompts/job_analyzer.py`
2. Read how prompts are composed and sent: `backend/llm/client.py`
3. Identify the 4-step pipeline prompts:
   - **Step 1 - Eligibility**: `ELIGIBILITY_SYSTEM` + `ELIGIBILITY_PROMPT` (early exit if not eligible)
   - **Step 2 - Matching**: `MATCHING_SYSTEM` + `MATCHING_PROMPT` (score + job summary)
   - **Step 3 - Resume Analysis**: `RESUME_ANALYSIS_SYSTEM` + `RESUME_ANALYSIS_PROMPT` (ATS keywords + suggestions)
   - **Step 4 - Cover Letter**: `COVER_LETTER_SYSTEM` + `COVER_LETTER_PROMPT` (tailored cover letter)
   - **Legacy**: `JOB_ANALYZER_SYSTEM` + `JOB_ANALYZER_PROMPT` (single-pass, kept for backwards compat)

4. For each prompt, analyze:
   - **Clarity**: Are instructions unambiguous? Could the LLM misinterpret anything?
   - **JSON reliability**: Are output format instructions strong enough to prevent markdown/text leaking?
   - **Token efficiency**: Are there redundant instructions or verbose phrasing that could be tightened?
   - **Edge cases**: What happens with unusual job postings (non-English, very short, internships, freelance)?
   - **Consistency**: Do all prompts follow the same patterns for JSON output enforcement?
   - **Hallucination guardrails**: Are there instructions to avoid fabricating candidate skills or experience?

5. Check the JSON schemas expected in each prompt match what `client.py` actually parses.

6. Output a structured report:
   - Summary of current prompt quality (score 1-10 per prompt)
   - Specific issues found (with line references)
   - Concrete improvement suggestions with before/after diffs
   - Any structural changes recommended (e.g., shared system prompt prefix)
