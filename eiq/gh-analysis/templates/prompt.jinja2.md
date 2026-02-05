Analyze the GitHub PR review data for {{ username }} during {{ analysis_period }} and generate a comprehensive markdown report.

**Configuration:**
- Username: {{ username }}
- Organization: {{ organization }}
- Period: {{ analysis_period }}

**Review Data Summary:**
- Total PRs Reviewed: {{ prs_reviewed_count }}
- Total Reviews: {{ total_reviews }}
- Total Review Comments: {{ total_review_comments }}
- Total PRs Authored: {{ authored_prs_count }}

**PR Details (Reviewed):**
{{ pr_details_json }}

**Review Comments:**
{{ review_comments_json }}

**PR Descriptions (Reviewed):**
{{ pr_descriptions_json }}

**Authored PRs (for significant changes analysis):**
{{ authored_prs_json }}

**Instructions:**

1. Classify comments as:
   - **Architecture**: Design patterns, scalability, security, breaking changes, system design
   - **Logic**: Bugs, edge cases, test coverage, correctness issues
   - **Nits**: Formatting, typos, variable naming, style issues

2. Score PR descriptions (1-5 scale):
   - **Context**: Does it explain why the change is needed?
   - **Risk**: Does it mention potential downsides or testing steps?
   - **Clarity**: Could a non-expert understand the goal?

3. Generate a comprehensive markdown report using the following template structure. Fill in all placeholders with your analysis:

{{ report_template }}

Replace all {{ '{{' }} placeholder {{ '}}' }} values with actual analysis. Return ONLY the completed markdown report with all placeholders filled in. Do not include markdown code blocks or explanations.
