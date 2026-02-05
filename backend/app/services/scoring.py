from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.models.llm_analysis import LLMAnalysis
from app.models.job import Job


@dataclass
class ScoreResult:
    stack_match_score: float
    seniority_match_score: float
    sponsorship_score: float
    quality_score: float
    total_score: float
    stack_match_details: int


class ScoringService:
    SENIORITY_LEVELS = {
        "junior": 1,
        "mid": 2,
        "senior": 3,
        "staff": 4,
        "principal": 5,
    }

    def __init__(
        self,
        target_stack: list[str] = None,
        target_seniority: str = "mid",
    ):
        self.target_stack = [s.lower() for s in (target_stack or [])]
        self.target_seniority = target_seniority.lower()
        self.target_seniority_level = self.SENIORITY_LEVELS.get(self.target_seniority, 2)

    def compute_score(
        self,
        job: Job,
        analysis: LLMAnalysis,
    ) -> ScoreResult:
        stack_score, matched_count = self._compute_stack_match(analysis.detected_stack)
        seniority_score = self._compute_seniority_match(analysis.seniority_level)
        sponsorship_score = self._compute_sponsorship_score(analysis.sponsorship_likelihood)
        quality_score = self._compute_quality_score(job, analysis)

        total_score = (
            stack_score * settings.weight_stack_match +
            seniority_score * settings.weight_seniority +
            sponsorship_score * settings.weight_sponsorship +
            quality_score * settings.weight_quality
        )

        return ScoreResult(
            stack_match_score=round(stack_score, 2),
            seniority_match_score=round(seniority_score, 2),
            sponsorship_score=round(sponsorship_score, 2),
            quality_score=round(quality_score, 2),
            total_score=round(total_score, 2),
            stack_match_details=matched_count,
        )

    def _compute_stack_match(self, detected_stack: list[str]) -> tuple[float, int]:
        if not self.target_stack:
            return 50.0, 0

        detected_lower = [s.lower() for s in detected_stack]

        matched = 0
        for target_tech in self.target_stack:
            for detected_tech in detected_lower:
                if target_tech in detected_tech or detected_tech in target_tech:
                    matched += 1
                    break

        if len(self.target_stack) == 0:
            return 50.0, 0

        match_ratio = matched / len(self.target_stack)

        score = min(100, match_ratio * 100 + (len(detected_stack) * 2))

        return score, matched

    def _compute_seniority_match(self, detected_seniority: Optional[str]) -> float:
        if not detected_seniority or detected_seniority == "unknown":
            return 50.0

        detected_level = self.SENIORITY_LEVELS.get(detected_seniority.lower(), 2)
        diff = abs(detected_level - self.target_seniority_level)

        if diff == 0:
            return 100.0
        elif diff == 1:
            return 75.0
        elif diff == 2:
            return 40.0
        else:
            return 20.0

    def _compute_sponsorship_score(self, likelihood: Optional[float]) -> float:
        if likelihood is None:
            return 50.0

        return likelihood * 100

    def _compute_quality_score(self, job: Job, analysis: LLMAnalysis) -> float:
        score = 50.0

        if job.salary_min or job.salary_max:
            score += 20.0

        if analysis.remote_policy and analysis.remote_policy != "unknown":
            score += 10.0

        if analysis.key_responsibilities and len(analysis.key_responsibilities) >= 3:
            score += 10.0

        if job.description and len(job.description) > 500:
            score += 10.0

        return min(100.0, score)


scoring_service = ScoringService()
