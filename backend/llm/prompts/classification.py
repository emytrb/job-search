CLASSIFICATION_PROMPT = """Analyze this job posting and extract structured information.

Job Title: {title}

Job Description:
{description}

Please extract the following information and respond with ONLY a JSON object (no other text):

{{
  "seniority_level": "junior|mid|senior|staff|principal",
  "detected_stack": ["list", "of", "technologies"],
  "required_experience_years": number or null,
  "sponsorship_likelihood": 0.0 to 1.0 (how likely they sponsor visas, based on company size, mentions of visa, international candidates, etc.),
  "remote_policy": "remote|hybrid|onsite|unknown",
  "key_responsibilities": ["list", "of", "main", "responsibilities"],
  "nice_to_haves": ["list", "of", "nice", "to", "have", "skills"]
}}

Guidelines:
- seniority_level: Infer from title and requirements. "SDE II" or "Software Engineer II" is typically mid-level. Look for keywords like "lead", "principal", "staff" for senior roles.
- detected_stack: Extract programming languages, frameworks, databases, cloud services, and tools mentioned.
- required_experience_years: Extract the minimum years if mentioned, null if not specified.
- sponsorship_likelihood:
  - 1.0 if they explicitly mention sponsoring visas
  - 0.8 if large tech company or mentions international/global team
  - 0.5 if no mention either way
  - 0.2 if small company with no international presence
  - 0.0 if they explicitly say no sponsorship
- remote_policy: Look for "remote", "hybrid", "office-based", "onsite" keywords.
- key_responsibilities: Extract 3-5 main job duties.
- nice_to_haves: Extract optional/preferred qualifications.

Respond with ONLY the JSON object, no explanation or markdown formatting."""
