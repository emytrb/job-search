# Legacy prompts (kept for backwards compatibility)
JOB_ANALYZER_SYSTEM = """You are a JSON API that analyzes job postings. You MUST respond with valid JSON only. No markdown, no explanations, no text outside the JSON object. Your entire response must be parseable by JSON.parse()."""

JOB_ANALYZER_PROMPT = """Analyze this job posting against the candidate's CV.

CANDIDATE CV:
{cv_text}

CANDIDATE CONTEXT:
{job_requirements_context}

JOB POSTING:
{job_text}

{ats_guidelines_section}

{cover_letter_guidelines_section}

OUTPUT REQUIREMENTS:
- Response must be ONLY valid JSON
- No markdown code blocks
- No explanations before or after
- No ```json``` tags
- Start your response with {{ and end with }}

Required JSON structure (replace ALL values with your actual analysis):
{{
  "matching_score": <YOUR_CALCULATED_SCORE_0_TO_100>,
  "matching_explanation": "<YOUR_SPECIFIC_ANALYSIS>",
  "job_summary": {{
    "title": "<ACTUAL_JOB_TITLE>",
    "company": "<ACTUAL_COMPANY_NAME>",
    "key_requirements": ["<ACTUAL_REQ_1>", "<ACTUAL_REQ_2>", "<ACTUAL_REQ_3>"]
  }},
  "resume_suggestions": [
    {{"section": "<SECTION>", "suggestion": "<SPECIFIC_SUGGESTION>", "reason": "<REASON>"}}
  ],
  "ats_keywords": [
    {{"keyword": "<KEYWORD>", "found_in_resume": <true_or_false>, "importance": "<required_or_preferred>"}}
  ],
  "cover_letter": "<YOUR_COMPLETE_UNIQUE_COVER_LETTER>"
}}

Scoring guide:
- 90-100: Perfect match
- 70-89: Good match with minor gaps
- 50-69: Moderate match
- Below 50: Significant gaps

IMPORTANT: Output ONLY the JSON object, nothing else."""

ATS_GUIDELINES_SECTION = """ATS GUIDELINES:
{ats_guidelines}"""

COVER_LETTER_GUIDELINES_SECTION = """COVER LETTER STYLE:
{cover_letter_guidelines}"""

# =============================================================================
# Step 1: Eligibility Check
# =============================================================================

ELIGIBILITY_SYSTEM = """You are an expert tech recruiter that evaluates job eligibility for candidates. You MUST respond with valid JSON only. No markdown, no explanations, no text outside the JSON object. Your entire response must be parseable by a JSON parser."""

ELIGIBILITY_PROMPT = """Evaluate whether this candidate is eligible for the job position.

CANDIDATE CV:
{cv_text}

CANDIDATE REQUIREMENTS (CRITICAL - these are dealbreakers if not met):
{job_requirements_context}

JOB POSTING:
{job_text}

=== DEALBREAKER CHECKS (any FAIL = not_eligible) ===

1. JOB TYPE CHECK:
   - Is this a PERMANENT position? (not contract, not freelance, not fixed-term)
   - If the job is contract/freelance/fixed-term → FAIL
   - Otherwise → PASS

2. VISA SPONSORSHIP CHECK (IMPORTANT - read carefully):
   - ONLY FAIL if the job EXPLICITLY states they CANNOT or WILL NOT sponsor visas
   - Look for explicit phrases like: "no visa sponsorship", "cannot sponsor", "won't sponsor",
     "must have right to work in UK", "UK residents only", "no sponsorship available"
   - If NO such explicit rejection phrase exists → PASS (assume sponsorship is possible)
   - The job being in London/UK is EXPECTED and REQUIRED - this is NOT a reason to fail
   - If the job doesn't mention sponsorship at all → PASS (silence means possible)

3. PRIMARY TECH STACK CHECK (IMPORTANT - use ecosystem matching):

   These are the SAME ECOSYSTEM and should PASS:
   - JVM languages: Java ↔ Kotlin ↔ Scala ↔ Groovy (all run on JVM, interoperable)
   - JVM frameworks: Spring ↔ Spring Boot ↔ Vert.x ↔ Quarkus ↔ Micronaut (all JVM)
   - JavaScript ecosystem: JavaScript ↔ TypeScript ↔ Node.js
   - Python ecosystem: Python ↔ Django ↔ FastAPI ↔ Flask
   - .NET ecosystem: C# ↔ F# ↔ .NET

   ONLY FAIL for completely DIFFERENT ecosystems with no overlap:
   - JVM (Java/Kotlin) vs Systems (Rust/C++/Go) → FAIL
   - Python vs Systems (Rust/C++/Go) → FAIL
   - Frontend-only (React/Vue) vs Backend-only (no frontend experience) → FAIL

   If candidate has experience in the SAME ecosystem as the job requires → PASS
   Example: Job wants Kotlin/Spring, candidate knows Java/Spring → PASS (same JVM ecosystem)

4. SENIORITY/EXPERIENCE LEVEL CHECK (use this exact logic):

   STEP A - Check for EXPLICIT years of experience requirement:
   - Look for patterns like "5+ years", "3-5 years experience", "minimum 4 years", "at least 3 years"
   - If years ARE explicitly mentioned:
     * Compare to candidate's years of experience from CV
     * If candidate meets the minimum → PASS
     * If candidate is below the minimum → FAIL
     * STOP HERE if years were found (do not check seniority keywords)

   STEP B - Only if NO years mentioned, check for EXPLICIT seniority keywords:
   - Look for these EXACT words in the job title or description: "Junior", "Senior", "Staff", "Principal", "Lead", "Entry Level", "Mid-Level", "Graduate", "Intern", "Director", "VP", "Head of"
   - The word MUST appear explicitly (e.g., "Senior Software Engineer" or "Looking for a junior developer")
   - Do NOT infer seniority from requirements or responsibilities
   - If explicit seniority keyword found:
     * Check if it matches candidate's acceptable seniority levels (from CANDIDATE REQUIREMENTS)
     * Default acceptable levels are: "Mid-Level" and "Senior"
     * If seniority matches acceptable levels → PASS
     * If seniority is "Junior", "Graduate", "Intern", "Entry Level" → FAIL (too junior)
     * If seniority is "Staff", "Principal", "Lead", "Director", "VP", "Head of" → FAIL (too senior)

   STEP C - If NEITHER years NOR seniority keywords are explicitly mentioned → PASS
   - Do NOT assume seniority based on the complexity of requirements
   - If the job doesn't explicitly state years or seniority level, it passes this check


5. LOCATION CHECK:
   - Job MUST be in London or UK (this is a requirement from CANDIDATE REQUIREMENTS)
   - If job is in London/UK → PASS
   - If job is remote-friendly for UK → PASS
   - If job is in a completely different country with no UK/remote option → FAIL

=== EVALUATION ===

For each check above, determine if it's a PASS or FAIL.
If ANY check is FAIL → eligibility_status = "not_eligible"
If all checks PASS but minor concerns exist → eligibility_status = "partially_eligible"
If all checks PASS with no concerns → eligibility_status = "eligible"

OUTPUT REQUIREMENTS:
- Response must be ONLY valid JSON
- No markdown code blocks
- No explanations before or after
- Start your response with {{ and end with }}
- You MUST analyze the ACTUAL job posting and CV provided - do NOT copy example values

Required JSON structure (replace ALL placeholder values with your actual analysis):
{{
  "eligibility_status": "<eligible OR partially_eligible OR not_eligible>",
  "eligibility_reasons": [
    "<PASS/FAIL>: <Your analysis of job type for THIS specific job>",
    "<PASS/FAIL>: <Your analysis of visa sponsorship for THIS specific job>",
    "<PASS/FAIL>: <Your analysis of tech stack match for THIS specific job and candidate>",
    "<PASS/FAIL>: <Your analysis of seniority for THIS specific job>",
    "<PASS/FAIL>: <Your analysis of location for THIS specific job>"
  ]
}}

=== EXAMPLES TO LEARN FROM ===

Visa sponsorship examples:
- Job says "We sponsor visas" → PASS
- Job says nothing about sponsorship → PASS (silence = possible)
- Job says "Must have right to work in UK" → FAIL (explicit rejection)
- Job is in London, candidate needs sponsorship, no mention of sponsorship → PASS

Tech stack examples:
- Job: Kotlin/Vert.x, Candidate: Java/Spring → PASS (both JVM ecosystem)
- Job: TypeScript/Node, Candidate: JavaScript/Express → PASS (same ecosystem)
- Job: Rust/Tokio, Candidate: Java/Spring → FAIL (completely different ecosystems)
- Job: Python/FastAPI, Candidate: Java/Spring → FAIL (different ecosystems)

Seniority examples:
- Job says "5+ years experience" and candidate has 4 years → FAIL
- Job says "3-5 years experience" and candidate has 4 years → PASS
- Job title is "Senior Software Engineer" with no years mentioned → PASS (Senior is acceptable)
- Job title is "Staff Engineer" with no years mentioned → FAIL (Staff is too senior)
- Job title is "Junior Developer" with no years mentioned → FAIL (Junior is too junior)
- Job says "Software Engineer" with no years/seniority keywords → PASS (nothing explicit)

IMPORTANT: Only FAIL when there is EXPLICIT evidence against the candidate. When in doubt or when information is missing, PASS. Output ONLY the JSON object, nothing else."""

# =============================================================================
# Step 2: Matching Score
# =============================================================================

MATCHING_SYSTEM = """You are a JSON API that scores job-candidate matches. You understand technology ecosystems and recognize that related technologies within the same ecosystem are highly transferable. You MUST respond with valid JSON only. No markdown, no explanations, no text outside the JSON object. Your entire response must be parseable by JSON.parse()."""

MATCHING_PROMPT = """Score how well this candidate matches the job and summarize the position.

CANDIDATE CV:
{cv_text}

CANDIDATE CONTEXT:
{job_requirements_context}

JOB POSTING:
{job_text}

=== CRITICAL: TECHNOLOGY ECOSYSTEM RULES ===

BEFORE scoring, you MUST understand these ecosystem equivalencies:

**JVM LANGUAGES ARE INTERCHANGEABLE (treat as SAME language):**
- Java, Kotlin, Scala, Groovy all run on the JVM
- A Java developer CAN write Kotlin (and vice versa) with minimal learning curve
- These are NOT different languages for scoring purposes - they are the SAME ecosystem
- "Java or Kotlin" or "Java, Kotlin, or similar" = Java developer qualifies fully

**SPRING FRAMEWORK VARIANTS ARE THE SAME FRAMEWORK:**
- Spring, Spring Boot, Spring MVC, Spring WebFlux, Spring Cloud, Spring Data, Spring Security
- These are ALL part of the Spring ecosystem - NOT different frameworks
- A Spring Boot developer knows Spring. A Spring developer can use Spring Boot.
- Spring WebFlux is just reactive Spring - same framework, different paradigm

**OTHER ECOSYSTEM EQUIVALENCIES:**
- JavaScript ↔ TypeScript ↔ Node.js (same ecosystem)
- Python ↔ Django ↔ FastAPI ↔ Flask (same ecosystem)
- React ↔ Next.js (same ecosystem)
- Vue ↔ Nuxt.js (same ecosystem)
- .NET ↔ C# ↔ F# (same ecosystem)

=== SCORING RULES ===

1. ECOSYSTEM MATCH (60% of score):
   - SAME ECOSYSTEM (Java↔Kotlin, Spring↔Spring Boot↔Spring WebFlux): 55-60 points
   - RELATED ECOSYSTEM (JVM↔.NET, Python↔Ruby): 30-40 points
   - DIFFERENT ECOSYSTEM (JVM↔Rust, Python↔C++): 10-20 points
   - COMPLETELY UNRELATED (Backend↔iOS native): 0-10 points

2. SPECIFIC SKILLS OVERLAP (25% of score):
   - Databases, cloud platforms, DevOps tools, methodologies
   - Score 0-25 based on overlap

3. DOMAIN/INDUSTRY EXPERIENCE (15% of score):
   - Relevant industry experience, architecture patterns
   - Score 0-15 based on relevance

=== SCORE GUIDELINES ===

- 85-100: Same ecosystem, strong skills overlap (Java dev → Kotlin/Spring job)
- 70-84: Same ecosystem, some gaps in secondary skills
- 55-69: Related ecosystem or significant secondary skill gaps
- 40-54: Different but adjacent ecosystems
- Below 40: Fundamentally different tech stacks

=== EXAMPLES ===

SAME ECOSYSTEM (score 85-95):
- Java/Spring Boot dev → Kotlin/Spring WebFlux job: 85-92
- Java/Spring Boot dev → Java/Vert.x job: 82-90
- Java dev → "Java, Kotlin, or similar" job: 88-95
- TypeScript/React dev → JavaScript/Next.js job: 85-92

RELATED ECOSYSTEM (score 55-75):
- Java dev → C#/.NET job: 55-65
- Python/Django dev → Python/FastAPI job: 88-95 (same ecosystem!)
- React dev → Vue job: 70-78

DIFFERENT ECOSYSTEM (score 25-45):
- Java dev → Python job: 35-45
- Python dev → Go job: 30-40
- Frontend React dev → Backend Rust job: 25-35

OUTPUT REQUIREMENTS:
- Response must be ONLY valid JSON
- No markdown code blocks
- Start your response with {{ and end with }}
- You MUST analyze the ACTUAL job posting and CV provided - do NOT copy example values

Required JSON structure (replace ALL placeholder values with your actual analysis):
{{
  "matching_score": <YOUR_CALCULATED_SCORE>,
  "matching_explanation": "<YOUR_ANALYSIS_OF_THIS_SPECIFIC_JOB_AND_CANDIDATE>",
  "job_summary": {{
    "title": "<ACTUAL_JOB_TITLE_FROM_POSTING>",
    "company": "<ACTUAL_COMPANY_NAME_FROM_POSTING>",
    "key_requirements": ["<ACTUAL_REQ_1>", "<ACTUAL_REQ_2>", "<ACTUAL_REQ_3>"]
  }}
}}

CRITICAL: You must provide a UNIQUE analysis based on the ACTUAL job posting and CV above. Do NOT use generic or example values. The matching_explanation must specifically reference:
1. The actual technologies mentioned in THIS job posting
2. The actual skills from THIS candidate's CV
3. How they specifically relate to each other

IMPORTANT: Recognize ecosystem equivalencies. A Java developer IS qualified for Kotlin jobs. A Spring Boot developer IS qualified for Spring WebFlux jobs. Only give low scores when ecosystems are fundamentally different. Output ONLY the JSON object, nothing else."""

# =============================================================================
# Step 3: Resume Analysis
# =============================================================================

RESUME_ANALYSIS_SYSTEM = """You are a JSON API that analyzes resumes against job postings. You MUST respond with valid JSON only. No markdown, no explanations, no text outside the JSON object. Your entire response must be parseable by JSON.parse()."""

RESUME_ANALYSIS_PROMPT = """Analyze the candidate's resume against this job posting. Identify ATS keywords and suggest resume improvements.

CANDIDATE CV:
{cv_text}

JOB POSTING:
{job_text}

{ats_guidelines_section}

=== CRITICAL RULES - READ CAREFULLY ===

1. NEVER SUGGEST LYING OR INVENTING EXPERIENCE:
   - NEVER suggest adding skills, technologies, or experience the candidate does NOT have
   - NEVER suggest claiming knowledge of tools not mentioned in the CV
   - If the job requires Kotlin but the CV only shows Java, do NOT suggest "Add Kotlin to your skills"
   - Only suggest highlighting, rephrasing, or emphasizing EXISTING experience

2. WHAT YOU CAN SUGGEST:
   - Reword existing experience to use job posting terminology (e.g., "microservices" instead of "distributed systems")
   - Move relevant experience higher/make it more prominent
   - Add metrics or quantify achievements already mentioned
   - Emphasize transferable skills that ARE in the CV
   - Use exact keywords from job posting IF the candidate actually has that experience
   - Restructure bullet points to lead with relevant technologies
   - Highlight equivalent/related technologies (Java experience IS relevant for Kotlin jobs)

3. PROVIDE AS MANY SUGGESTIONS AS NEEDED:
   - Do NOT limit yourself to a fixed number
   - Provide ALL suggestions that would genuinely improve the match
   - Group by section (Skills, Experience, Summary, Education, etc.)
   - Each suggestion should be actionable and specific

=== EXAMPLES OF GOOD vs BAD SUGGESTIONS ===

BAD (inventing experience):
- "Add Kotlin to your skills section" (when CV has no Kotlin)
- "Include Vert.x framework experience" (when CV doesn't mention it)
- "Add Kubernetes certification" (when candidate doesn't have it)

GOOD (highlighting existing experience):
- "Reword 'built distributed backend services' to 'developed microservices architecture' to match job terminology"
- "Move your Java/Spring experience to the top as it's directly relevant to this JVM role"
- "Emphasize your REST API work from Project X as the job specifically requires API development"
- "Your experience with Docker is relevant - add it to the Skills section if missing there"
- "Quantify your backend work: 'handled X requests/day' or 'reduced latency by Y%'"

OUTPUT REQUIREMENTS:
- Response must be ONLY valid JSON
- No markdown code blocks
- No explanations before or after
- Start your response with {{ and end with }}
- You MUST analyze the ACTUAL job posting and CV provided - do NOT copy example values

Required JSON structure (replace ALL placeholder values with your actual analysis):
{{
  "resume_suggestions": [
    {{
      "section": "<ACTUAL_SECTION_NAME>",
      "suggestion": "<YOUR_SPECIFIC_SUGGESTION_FOR_THIS_CANDIDATE>",
      "reason": "<WHY_THIS_HELPS_FOR_THIS_SPECIFIC_JOB>"
    }}
  ],
  "ats_keywords": [
    {{"keyword": "<KEYWORD_FROM_THIS_JOB_POSTING>", "found_in_resume": <true_or_false>, "importance": "<required_or_preferred>"}}
  ]
}}

Guidelines:
- Provide ALL suggestions that would improve the match (no artificial limit)
- Multiple suggestions per section are encouraged if relevant
- Identify 5-15 important ATS keywords from the job posting
- Mark keywords as found_in_resume: true ONLY if they appear in the CV
- Mark importance as "required" or "preferred" based on job posting language
- Focus on making existing experience more visible, not inventing new experience

IMPORTANT: NEVER suggest adding skills or experience the candidate does not have. Output ONLY the JSON object, nothing else."""

# =============================================================================
# Step 4: Cover Letter Generation
# =============================================================================

COVER_LETTER_SYSTEM = """You are a professional cover letter writer. You MUST respond with valid JSON only. No markdown, no explanations, no text outside the JSON object. Your entire response must be parseable by JSON.parse()."""

COVER_LETTER_PROMPT = """Write a tailored cover letter for this candidate applying to this job.

CANDIDATE CV:
{cv_text}

JOB POSTING:
{job_text}

JOB SUMMARY:
- Title: {job_title}
- Company: {job_company}
- Key Requirements: {key_requirements}

{cover_letter_guidelines_section}

OUTPUT REQUIREMENTS:
- Response must be ONLY valid JSON
- No markdown code blocks
- No explanations before or after
- Start your response with {{ and end with }}
- You MUST write a UNIQUE cover letter for THIS specific candidate and job

Required JSON structure:
{{
  "cover_letter": "<YOUR_COMPLETE_COVER_LETTER_TEXT_HERE>"
}}

The cover_letter field must contain a COMPLETE, UNIQUE cover letter written specifically for this candidate applying to this job. Do NOT use placeholder text or generic templates.

Cover letter guidelines:
- Keep it concise (3-4 paragraphs)
- Highlight specific skills that match the job requirements
- Show enthusiasm for the company and role
- Include a clear call to action
- Use professional but engaging tone
- Reference specific technologies or requirements from the job posting

IMPORTANT: Output ONLY the JSON object, nothing else."""
