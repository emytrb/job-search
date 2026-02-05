import asyncio
import json
import re
import time
import logging
from typing import Optional
from dataclasses import dataclass

import litellm
from litellm.exceptions import RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from llm.prompts.job_analyzer import (
    ATS_GUIDELINES_SECTION,
    COVER_LETTER_GUIDELINES_SECTION,
    ELIGIBILITY_SYSTEM,
    ELIGIBILITY_PROMPT,
    MATCHING_SYSTEM,
    MATCHING_PROMPT,
    RESUME_ANALYSIS_SYSTEM,
    RESUME_ANALYSIS_PROMPT,
    COVER_LETTER_SYSTEM,
    COVER_LETTER_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class ResumeSuggestion:
    section: str
    suggestion: str
    reason: str


@dataclass
class ATSKeyword:
    keyword: str
    found_in_resume: bool
    importance: str


@dataclass
class JobSummary:
    title: str
    company: str
    key_requirements: list[str]


@dataclass
class EligibilityResult:
    status: str  # "eligible" | "partially_eligible" | "not_eligible"
    reasons: list[str]


@dataclass
class MatchingResult:
    score: int
    explanation: str
    job_summary: JobSummary


@dataclass
class ResumeAnalysisResult:
    suggestions: list[ResumeSuggestion]
    ats_keywords: list[ATSKeyword]


@dataclass
class JobOfferAnalysis:
    eligibility_status: str
    eligibility_reasons: list[str]
    matching_score: int
    matching_explanation: str
    job_summary: JobSummary
    resume_suggestions: list[ResumeSuggestion]
    ats_keywords: list[ATSKeyword]
    cover_letter: str
    raw_response: dict
    model_used: str
    processing_time_ms: int


class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.api_key = None

        # Configure model string based on provider
        if self.provider == "ollama":
            self.model = f"ollama/{settings.ollama_model}"
            self.base_url = settings.ollama_base_url
            litellm.api_base = self.base_url
        elif self.provider == "groq":
            self.model = f"groq/{settings.llm_model}"
            self.base_url = None
            self.api_key = settings.groq_api_key
        elif self.provider == "openai":
            self.model = settings.llm_model  # e.g., "gpt-4o"
            self.base_url = None
            self.api_key = settings.openai_api_key
        elif self.provider == "anthropic":
            self.model = settings.llm_model  # e.g., "claude-3-5-sonnet-20241022"
            self.base_url = None
            self.api_key = settings.anthropic_api_key
        else:
            # Default to provider/model format for other LiteLLM-supported providers
            self.model = f"{self.provider}/{settings.llm_model}"
            self.base_url = None

        # Maximum retries when hitting rate limits (429)
        self.max_rate_limit_retries = 10
        # Default wait time if retry-after header is missing
        self.default_retry_wait = 5

        logger.info(f"LLM client initialized with provider={self.provider}, model={self.model}")

    def _get_completion_kwargs(self, **kwargs):
        """Build completion kwargs with appropriate auth for the provider."""
        completion_kwargs = {"model": self.model, **kwargs}
        if self.base_url:
            completion_kwargs["api_base"] = self.base_url
        if self.api_key:
            completion_kwargs["api_key"] = self.api_key
        return completion_kwargs

    def _parse_retry_after(self, error: RateLimitError) -> Optional[float]:
        """
        Parse the retry-after header from a rate limit error.

        Groq returns headers like:
        - retry-after: 2  (seconds to wait)
        - x-ratelimit-remaining-requests: 14370
        - x-ratelimit-remaining-tokens: 17997
        """
        try:
            # LiteLLM exposes response headers in llm_provider_response_headers
            if hasattr(error, 'llm_provider_response_headers') and error.llm_provider_response_headers:
                headers = error.llm_provider_response_headers
                retry_after = headers.get('retry-after') or headers.get('Retry-After')
                if retry_after:
                    logger.info(f"Found retry-after header: {retry_after}")
                    return float(retry_after)

            # Try to get from response object if available
            if hasattr(error, 'response') and error.response:
                if hasattr(error.response, 'headers'):
                    headers = error.response.headers
                    retry_after = headers.get('retry-after') or headers.get('Retry-After')
                    if retry_after:
                        logger.info(f"Found retry-after in response headers: {retry_after}")
                        return float(retry_after)

            # Try to parse from error message (fallback)
            error_str = str(error)
            # Look for patterns like "retry after 2 seconds" or "retry-after: 2"
            match = re.search(r'retry[_\-\s]?after[:\s]+(\d+(?:\.\d+)?)', error_str, re.IGNORECASE)
            if match:
                retry_after = float(match.group(1))
                logger.info(f"Parsed retry-after from error message: {retry_after}")
                return retry_after

            return None

        except Exception as e:
            logger.warning(f"Failed to parse retry-after header: {e}")
            return None

    async def _rate_limited_completion(self, **kwargs):
        """
        Make a completion request with automatic 429 retry handling.

        Uses Groq's retry-after header to know exactly how long to wait.
        """
        retries = 0

        while True:
            try:
                return await litellm.acompletion(**self._get_completion_kwargs(**kwargs))

            except RateLimitError as e:
                retries += 1

                if retries > self.max_rate_limit_retries:
                    logger.error(f"Max rate limit retries ({self.max_rate_limit_retries}) exceeded")
                    raise

                # Parse retry-after from Groq's response headers
                retry_after = self._parse_retry_after(e)

                if retry_after is None:
                    # Fallback: exponential backoff if header not available
                    retry_after = min(60, self.default_retry_wait * (2 ** (retries - 1)))
                    logger.warning(
                        f"No retry-after header found, using fallback: {retry_after}s"
                    )

                logger.warning(
                    f"Rate limit hit (429), waiting {retry_after}s before retry "
                    f"({retries}/{self.max_rate_limit_retries})"
                )

                await asyncio.sleep(retry_after)

    def _parse_response(self, content: str) -> dict:
        try:
            json_match = content

            # Strip <think>...</think> blocks (used by reasoning models)
            if "<think>" in json_match:
                logger.info("Stripping <think> block from response")
                json_match = re.sub(r'<think>.*?</think>', '', json_match, flags=re.DOTALL)
                logger.info(f"After stripping think block: {json_match[:500]}")

            if "```json" in json_match:
                json_match = json_match.split("```json")[1].split("```")[0]
            elif "```" in json_match:
                json_match = json_match.split("```")[1].split("```")[0]

            json_match = json_match.strip()
            logger.info(f"Attempting to parse JSON: {json_match[:300]}...")
            return json.loads(json_match)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            logger.warning(f"Full response content:\n{content}")
            # Try to fix truncated JSON by adding missing closing braces/brackets
            fixed = self._try_fix_truncated_json(content)
            if fixed:
                return fixed
            return self._fallback_parse(content)

    def _try_fix_truncated_json(self, content: str) -> dict | None:
        """Try to fix truncated JSON responses (common with cover letters)."""
        try:
            # Extract just the JSON part
            json_match = content.strip()
            if "```json" in json_match:
                json_match = json_match.split("```json")[1].split("```")[0]
            elif "```" in json_match:
                json_match = json_match.split("```")[1].split("```")[0]
            json_match = json_match.strip()

            # Try adding missing closing characters
            # Count open/close braces and brackets
            open_braces = json_match.count('{') - json_match.count('}')
            open_brackets = json_match.count('[') - json_match.count(']')

            # Check if we're inside a string (unclosed quote)
            # Simple heuristic: odd number of unescaped quotes
            in_string = False
            i = 0
            while i < len(json_match):
                if json_match[i] == '"' and (i == 0 or json_match[i-1] != '\\'):
                    in_string = not in_string
                i += 1

            # If in string, close it
            if in_string:
                json_match += '"'

            # Add missing closing characters
            json_match += ']' * open_brackets
            json_match += '}' * open_braces

            result = json.loads(json_match)
            logger.info("Successfully fixed truncated JSON")
            return result
        except Exception as e:
            logger.warning(f"Failed to fix truncated JSON: {e}")
            return None

    def _fallback_parse(self, content: str) -> dict:
        """Return empty dict as last resort when JSON parsing fails."""
        logger.warning("Returning empty dict as fallback parse result")
        return {}

    async def _analyze_eligibility(
        self,
        job_text: str,
        cv_text: str,
        job_requirements_context: str,
    ) -> EligibilityResult:
        """Step 1: Check if candidate is eligible for the job."""
        logger.info("Starting eligibility analysis...")

        prompt = ELIGIBILITY_PROMPT.format(
            cv_text=cv_text[:10000],
            job_requirements_context=job_requirements_context or "No additional context provided.",
            job_text=job_text[:10000],
        )

        response = await self._rate_limited_completion(
            messages=[
                {"role": "system", "content": ELIGIBILITY_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )

        content = response.choices[0].message.content
        logger.info(f"Eligibility raw response:\n{content}")
        parsed = self._parse_response(content)

        return EligibilityResult(
            status=parsed.get("eligibility_status", "partially_eligible"),
            reasons=parsed.get("eligibility_reasons", []),
        )

    async def _analyze_matching(
        self,
        job_text: str,
        cv_text: str,
        job_requirements_context: str,
    ) -> MatchingResult:
        """Step 2: Score how well candidate matches and summarize the job."""
        logger.info("Starting matching analysis...")

        prompt = MATCHING_PROMPT.format(
            cv_text=cv_text[:10000],
            job_requirements_context=job_requirements_context or "No additional context provided.",
            job_text=job_text[:10000],
        )

        response = await self._rate_limited_completion(
            messages=[
                {"role": "system", "content": MATCHING_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )

        content = response.choices[0].message.content
        logger.info(f"Matching raw response:\n{content}")
        parsed = self._parse_response(content)

        job_summary_data = parsed.get("job_summary", {})
        job_summary = JobSummary(
            title=job_summary_data.get("title", "Unknown"),
            company=job_summary_data.get("company", "Unknown"),
            key_requirements=job_summary_data.get("key_requirements", []),
        )

        return MatchingResult(
            score=parsed.get("matching_score", 50),
            explanation=parsed.get("matching_explanation", ""),
            job_summary=job_summary,
        )

    async def _analyze_resume(
        self,
        job_text: str,
        cv_text: str,
        ats_guidelines: str,
    ) -> ResumeAnalysisResult:
        """Step 3: Analyze resume gaps and identify ATS keywords."""
        logger.info("Starting resume analysis...")

        ats_section = ""
        if ats_guidelines.strip():
            ats_section = ATS_GUIDELINES_SECTION.format(ats_guidelines=ats_guidelines)

        prompt = RESUME_ANALYSIS_PROMPT.format(
            cv_text=cv_text[:10000],
            job_text=job_text[:10000],
            ats_guidelines_section=ats_section,
        )

        response = await self._rate_limited_completion(
            messages=[
                {"role": "system", "content": RESUME_ANALYSIS_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2048,
        )

        content = response.choices[0].message.content
        logger.info(f"Resume analysis raw response:\n{content}")
        parsed = self._parse_response(content)

        suggestions = [
            ResumeSuggestion(
                section=s.get("section", ""),
                suggestion=s.get("suggestion", ""),
                reason=s.get("reason", ""),
            )
            for s in parsed.get("resume_suggestions", [])
        ]

        ats_keywords = [
            ATSKeyword(
                keyword=k.get("keyword", ""),
                found_in_resume=k.get("found_in_resume", False),
                importance=k.get("importance", "preferred"),
            )
            for k in parsed.get("ats_keywords", [])
        ]

        return ResumeAnalysisResult(
            suggestions=suggestions,
            ats_keywords=ats_keywords,
        )

    async def _generate_cover_letter(
        self,
        job_text: str,
        cv_text: str,
        cover_letter_guidelines: str,
        job_summary: JobSummary,
    ) -> str:
        """Step 4: Generate tailored cover letter."""
        logger.info("Starting cover letter generation...")

        cover_letter_section = ""
        if cover_letter_guidelines.strip():
            cover_letter_section = COVER_LETTER_GUIDELINES_SECTION.format(
                cover_letter_guidelines=cover_letter_guidelines
            )

        key_requirements_str = ", ".join(job_summary.key_requirements) if job_summary.key_requirements else "Not specified"

        prompt = COVER_LETTER_PROMPT.format(
            cv_text=cv_text[:10000],
            job_text=job_text[:10000],
            job_title=job_summary.title,
            job_company=job_summary.company,
            key_requirements=key_requirements_str,
            cover_letter_guidelines_section=cover_letter_section,
        )

        response = await self._rate_limited_completion(
            messages=[
                {"role": "system", "content": COVER_LETTER_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Slightly higher for more creative writing
            max_tokens=3000,  # Increased for longer cover letters
        )

        content = response.choices[0].message.content
        logger.info(f"Cover letter raw response:\n{content}")
        parsed = self._parse_response(content)

        return parsed.get("cover_letter", "")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def analyze_job_offer(
        self,
        job_text: str,
        cv_text: str,
        job_requirements_context: str = "",
        ats_guidelines: str = "",
        cover_letter_guidelines: str = "",
    ) -> JobOfferAnalysis:
        """
        Analyze a job offer against the candidate's CV.

        This method runs 4 sequential LLM calls:
        1. Eligibility check (early exit if not_eligible)
        2. Matching score and job summary
        3. Resume analysis and ATS keywords
        4. Cover letter generation
        """
        start_time = time.time()
        all_raw_responses = {}

        try:
            # Step 1: Eligibility check
            eligibility = await self._analyze_eligibility(
                job_text, cv_text, job_requirements_context
            )
            all_raw_responses["eligibility"] = {
                "status": eligibility.status,
                "reasons": eligibility.reasons,
            }
            logger.info(f"Eligibility status: {eligibility.status}")

            # Early exit if not eligible
            if eligibility.status == "not_eligible":
                processing_time = int((time.time() - start_time) * 1000)
                logger.info("Candidate not eligible, skipping remaining analysis")
                return JobOfferAnalysis(
                    eligibility_status=eligibility.status,
                    eligibility_reasons=eligibility.reasons,
                    matching_score=0,
                    matching_explanation="Candidate not eligible for this position.",
                    job_summary=JobSummary(title="", company="", key_requirements=[]),
                    resume_suggestions=[],
                    ats_keywords=[],
                    cover_letter="",
                    raw_response=all_raw_responses,
                    model_used=self.model,
                    processing_time_ms=processing_time,
                )

            # Step 2: Matching score
            matching = await self._analyze_matching(
                job_text, cv_text, job_requirements_context
            )
            all_raw_responses["matching"] = {
                "score": matching.score,
                "explanation": matching.explanation,
                "job_summary": {
                    "title": matching.job_summary.title,
                    "company": matching.job_summary.company,
                    "key_requirements": matching.job_summary.key_requirements,
                },
            }

            # Step 3: Resume analysis
            resume_analysis = await self._analyze_resume(
                job_text, cv_text, ats_guidelines
            )
            all_raw_responses["resume_analysis"] = {
                "suggestions": [
                    {"section": s.section, "suggestion": s.suggestion, "reason": s.reason}
                    for s in resume_analysis.suggestions
                ],
                "ats_keywords": [
                    {"keyword": k.keyword, "found_in_resume": k.found_in_resume, "importance": k.importance}
                    for k in resume_analysis.ats_keywords
                ],
            }

            # Step 4: Cover letter generation
            cover_letter = await self._generate_cover_letter(
                job_text, cv_text, cover_letter_guidelines, matching.job_summary
            )
            all_raw_responses["cover_letter"] = cover_letter

            processing_time = int((time.time() - start_time) * 1000)

            return JobOfferAnalysis(
                eligibility_status=eligibility.status,
                eligibility_reasons=eligibility.reasons,
                matching_score=matching.score,
                matching_explanation=matching.explanation,
                job_summary=matching.job_summary,
                resume_suggestions=resume_analysis.suggestions,
                ats_keywords=resume_analysis.ats_keywords,
                cover_letter=cover_letter,
                raw_response=all_raw_responses,
                model_used=self.model,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Job offer analysis failed: {e}")
            raise


llm_client = LLMClient()
