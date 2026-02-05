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
   
   Evaluate each document rigorously against these core criteria:
   
   a. **Clarity of Problem Statement:**
      - Is the problem being addressed clearly defined?
      - Is the "why" (motivation/context) clearly explained?
      - Can a reader understand what problem this design solves without prior context?
   
   b. **Clarity of Concept and Communication:**
      - Is the proposed solution concept clearly explained?
      - Does it effectively communicate the "what" (what is being built/changed)?
      - Are technical concepts explained in a way that's accessible to the intended audience?
      - Is the document free of ambiguity that could lead to misunderstandings?
   
   c. **Clear Execution Path:**
      - Is there a concrete, actionable plan for implementation?
      - Are the steps or phases clearly defined?
      - Is it clear how to proceed from reading the document to implementing it?
      - Are dependencies, prerequisites, and sequencing made explicit?
   
   d. **Architecture Changes:**
      - If the design involves architecture changes, are diagrams included?
      - Do diagrams effectively illustrate the current vs. proposed state?
      - Are architectural decisions and their implications clearly explained?
   
   **Scoring Guidelines:**
   - Be critical and realistic. A good design doc must excel in all three core areas (problem clarity, concept clarity, execution path).
   - Missing diagrams for architecture changes is a significant gap.
   - Vague problem statements or unclear execution paths should result in lower scores.
   - Documents that don't clearly convey "what" and "why" should be marked down.

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
