Analyze the Google Docs technical design documents for {{ name }} ({{ username }}) during {{ analysis_period }} and generate a comprehensive markdown report.

**Configuration:**
- Name: {{ name }}
- Username: {{ username }}
- Period: {{ analysis_period }}
- Documents Analyzed: {{ documents_count }}

**Documents:**
{{ documents_json }}

**Instructions:**

1. **Document Quality Evaluation:**
   - Assess clarity: Is the document easy to understand? Does it explain technical concepts clearly?
   - Evaluate completeness: Does it cover all necessary aspects (problem statement, solution design, alternatives considered, risks, implementation plan)?
   - Measure technical depth: Does it demonstrate deep technical understanding? Are technical decisions well-reasoned?
   - Review structure: Is the document well-organized with clear sections? Does it follow a logical flow?

2. **Comment Response Quality:**
   - Analyze how authors responded to comments and feedback
   - Evaluate whether feedback was incorporated thoughtfully
   - Assess if authors addressed concerns raised by reviewers
   - Note if authors provided clarifications or additional context when requested

3. **Team Engagement:**
   - Measure comment volume and discussion depth
   - Assess collaboration patterns: Did multiple team members engage?
   - Evaluate review quality: Were comments constructive and helpful?
   - Note engagement timeline: How quickly did discussions happen?

4. **Generate a comprehensive markdown report** using the following template structure. Fill in all placeholders with your analysis:

{{ report_template }}

Replace all {{ '{{' }} placeholder {{ '}}' }} values with actual analysis. Return ONLY the completed markdown report with all placeholders filled in. Do not include markdown code blocks or explanations.
