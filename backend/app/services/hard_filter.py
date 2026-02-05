import re
from dataclasses import dataclass
from typing import Optional, Set
from app.models.job import Job, JobType


@dataclass
class FilterResult:
    passed: bool
    reason: Optional[str] = None


class HardFilter:
    # Location patterns for London, UK
    LONDON_PATTERNS = [
        r"\blondon\b",
        r"\buk\b",
        r"\bunited kingdom\b",
        r"\bengland\b",
        r"\bremote.*uk\b",
        r"\buk.*remote\b",
    ]

    # Patterns indicating no visa sponsorship
    NO_SPONSORSHIP_PATTERNS = [
        r"uk\s*residents?\s*only",
        r"no\s*visa\s*sponsor",
        r"must\s*(have|already\s*have)\s*(the\s*)?(right|eligibility)\s*to\s*work",
        r"right\s*to\s*work\s*(in\s*(the\s*)?uk|required)",
        r"not\s*(able\s*to\s*)?sponsor",
        r"cannot\s*sponsor",
        r"won'?t\s*sponsor",
        r"do\s*not\s*sponsor",
        r"sponsorship\s*(is\s*)?(not|un)available",
        r"no\s*sponsorship",
        r"uk\s*work\s*(permit|visa)\s*required",
        r"must\s*be\s*(eligible|authorized)\s*to\s*work",
        r"only\s*(applicants|candidates)\s*(with|who\s*have)\s*(the\s*)?right\s*to\s*work",
    ]

    # Patterns indicating security clearance requirement
    SECURITY_CLEARANCE_PATTERNS = [
        r"security\s*clearance",
        r"\bsc\s*clearance\b",
        r"\bdv\s*clearance\b",
        r"\bcts\s*clearance\b",
        r"developed\s*vetting",
        r"counter\s*terrorist\s*check",
        r"bpss\s*clearance",
        r"nato\s*clearance",
        r"must\s*(hold|have|obtain)\s*(a\s*)?(valid\s*)?security\s*clearance",
        r"clearance\s*(is\s*)?required",
        r"eligible\s*for\s*security\s*clearance",
    ]

    # Patterns for contract/temporary positions
    CONTRACT_PATTERNS = [
        r"\bcontract\b",
        r"\bcontractor\b",
        r"\bfreelance\b",
        r"\btemporary\b",
        r"\btemp\s+position\b",
        r"\bfixed\s*term\b",
        r"\b\d+\s*month(s)?\s*(contract|position)\b",
    ]

    # Experience requirement patterns - captures min and optionally max years
    EXPERIENCE_PATTERNS = [
        # "5+ years" or "5 years"
        r"(\d+)\+?\s*years?\s*(of\s*)?(experience|exp)",
        # "minimum 5 years"
        r"minimum\s*(\d+)\s*years?",
        # "at least 5 years"
        r"at\s*least\s*(\d+)\s*years?",
    ]

    # Range patterns for experience - captures min and max
    EXPERIENCE_RANGE_PATTERNS = [
        # "3-5 years" or "3 to 5 years"
        r"(\d+)\s*[-–—to]+\s*(\d+)\s*years?",
    ]

    # Explicit seniority keywords - must match exactly these words
    SENIORITY_KEYWORDS = {
        "junior": "junior",
        "senior": "senior",
        "staff": "staff",
        "principal": "principal",
        "lead": "lead",
        "entry level": "entry-level",
        "entry-level": "entry-level",
        "mid-level": "mid-level",
        "mid level": "mid-level",
        "graduate": "graduate",
        "intern": "intern",
        "head of": "head",
        "director": "director",
        "vp": "vp",
        "vice president": "vp",
    }

    # Seniority levels the candidate is targeting (will pass if matched)
    DEFAULT_ACCEPTABLE_SENIORITIES = {"junior", "mid-level"}

    def __init__(
        self,
        cv_experience_years: int = 4,
        acceptable_seniorities: Optional[set[str]] = None,
    ):
        self.cv_experience_years = cv_experience_years
        self.acceptable_seniorities = (
            acceptable_seniorities
            if acceptable_seniorities is not None
            else self.DEFAULT_ACCEPTABLE_SENIORITIES
        )

    def check(self, job: Job) -> FilterResult:
        text = self._get_searchable_text(job)

        # 1. Check location
        location_result = self._check_location(job.location, text)
        if not location_result.passed:
            return location_result

        # 2. Check job type (permanent only)
        type_result = self._check_job_type(job.job_type, text)
        if not type_result.passed:
            return type_result

        # 3. Check sponsorship
        sponsorship_result = self._check_sponsorship(text)
        if not sponsorship_result.passed:
            return sponsorship_result

        # 4. Check security clearance
        clearance_result = self._check_security_clearance(text)
        if not clearance_result.passed:
            return clearance_result

        # 5. Check experience/seniority requirements
        experience_result = self._check_experience(job)
        if not experience_result.passed:
            return experience_result

        return FilterResult(passed=True)

    def _get_searchable_text(self, job: Job) -> str:
        parts = [
            job.title or "",
            job.description or "",
            job.location or "",
        ]
        return " ".join(parts).lower()

    def _check_location(self, location: Optional[str], text: str) -> FilterResult:
        if not location:
            return FilterResult(passed=True)

        location_lower = location.lower()
        combined_text = f"{location_lower} {text}"

        for pattern in self.LONDON_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                return FilterResult(passed=True)

        return FilterResult(passed=False, reason="Location not in London/UK")

    def _check_job_type(self, job_type: Optional[JobType], text: str) -> FilterResult:
        if job_type == JobType.CONTRACT:
            return FilterResult(passed=False, reason="Contract position")

        for pattern in self.CONTRACT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if not re.search(r"(permanent|full[\s-]*time)", text, re.IGNORECASE):
                    return FilterResult(passed=False, reason="Contract/temporary position")

        return FilterResult(passed=True)

    def _check_sponsorship(self, text: str) -> FilterResult:
        for pattern in self.NO_SPONSORSHIP_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return FilterResult(passed=False, reason="No visa sponsorship")

        return FilterResult(passed=True)

    def _check_security_clearance(self, text: str) -> FilterResult:
        for pattern in self.SECURITY_CLEARANCE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return FilterResult(passed=False, reason="Security clearance required")

        return FilterResult(passed=True)

    def _check_experience(self, job: Job) -> FilterResult:
        """
        Check experience/seniority requirements:
        1. If years of experience explicitly mentioned, compare to CV years
        2. If no years mentioned, check for explicit seniority keywords
        3. If neither mentioned, pass
        """
        title = (job.title or "").lower()
        description = (job.description or "").lower()
        text = f"{title} {description}"

        # Step 1: Check for explicit years of experience
        years_result = self._check_explicit_years(text)
        if years_result is not None:
            return years_result

        # Step 2: Check for explicit seniority keywords
        seniority_result = self._check_explicit_seniority(title, description)
        if seniority_result is not None:
            return seniority_result

        # Step 3: Neither years nor seniority mentioned - pass
        return FilterResult(passed=True)

    def _check_explicit_years(self, text: str) -> Optional[FilterResult]:
        """
        Check if years of experience are explicitly mentioned.
        Returns None if no years found, otherwise returns pass/fail result.
        """
        # First check for range patterns (e.g., "3-5 years")
        for pattern in self.EXPERIENCE_RANGE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                min_years = int(match.group(1))
                max_years = int(match.group(2))
                if self.cv_experience_years < min_years:
                    return FilterResult(
                        passed=False,
                        reason=f"Requires {min_years}-{max_years} years (CV: {self.cv_experience_years})"
                    )
                # Within or above range - pass
                return FilterResult(passed=True)

        # Check for minimum patterns (e.g., "5+ years", "at least 5 years")
        for pattern in self.EXPERIENCE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                min_years = int(match.group(1))
                if self.cv_experience_years < min_years:
                    return FilterResult(
                        passed=False,
                        reason=f"Requires {min_years}+ years (CV: {self.cv_experience_years})"
                    )
                # CV meets minimum - pass
                return FilterResult(passed=True)

        # No explicit years found
        return None

    def _check_explicit_seniority(
        self, title: str, description: str
    ) -> Optional[FilterResult]:
        """
        Check for explicit seniority keywords in title or description.
        Only matches exact seniority words like "Senior", "Junior", etc.
        Returns None if no seniority found, otherwise returns pass/fail result.
        """
        # Check title first (stronger signal)
        for keyword, seniority in self.SENIORITY_KEYWORDS.items():
            # Use word boundaries to match exact words
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, title, re.IGNORECASE):
                if seniority in self.acceptable_seniorities:
                    return FilterResult(passed=True)
                return FilterResult(
                    passed=False,
                    reason=f"Seniority mismatch: {seniority}"
                )

        # Check description
        for keyword, seniority in self.SENIORITY_KEYWORDS.items():
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, description, re.IGNORECASE):
                if seniority in self.acceptable_seniorities:
                    return FilterResult(passed=True)
                return FilterResult(
                    passed=False,
                    reason=f"Seniority mismatch: {seniority}"
                )

        # No explicit seniority found
        return None


hard_filter = HardFilter()
