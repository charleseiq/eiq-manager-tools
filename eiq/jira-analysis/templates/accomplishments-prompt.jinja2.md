Generate a realistic, human-readable summary of accomplishments for {{ username }} during {{ analysis_period }}.

**Context:**
- Username: {{ username }}
- Analysis Period: {{ analysis_period }}
- Total Sprints: {{ sprints_count }}
- Total Issues: {{ total_issues }}

**Quality Metrics:**
{{ quality_metrics_json }}

**Quality Percentages:**
{{ quality_percentages_json }}

**Epic-Level Accomplishments:**
{{ epic_accomplishments_json }}

**Fix Version Accomplishments (Actual Deliveries):**
{{ fix_version_accomplishments_json }}

**Instructions:**

Write a realistic, nuanced summary that focuses on:

1. **Quality of Work**: Analyze the quality metrics provided:
   - How complete are issue descriptions?
   - What percentage of tickets have acceptance criteria?
   - How often are references to other docs included?
   - How often are definitions provided?
   - What percentage are planning tickets (TDDs, spikes, design docs)?

2. **Epic-Level Value Delivery**: Focus on epic-level accomplishments rather than individual tickets:
   - What epics were worked on?
   - Which epics had actual value delivery (completed issues)?
   - Distinguish between planning work (TDDs, design) and actual implementation/delivery

3. **Fix Version Deliveries**: Highlight actual deliveries via fix versions:
   - What fix versions were delivered?
   - What value was delivered in each fix version?

4. **Realistic Assessment**: Be honest about what was accomplished:
   - Many tickets are planning/design tickets (TDDs) - acknowledge this
   - Actual value delivery happens at epic or fix version level
   - Focus on quality indicators (acceptance criteria, references, definitions) as measures of thoroughness
   - Don't assume all completed tickets represent delivered value

**Format Requirements:**
- Write in clear, professional language suitable for performance reviews
- Use bullet points or short paragraphs for readability
- Be realistic and nuanced - distinguish planning from delivery
- Focus on quality metrics and epic-level value, not just ticket counts
- Keep it concise but comprehensive (aim for 3-5 paragraphs or equivalent in bullet points)
- Do NOT include markdown code blocks or explanations - return ONLY the summary text

**Example Structure:**
```
During [period], [Name] worked on [X] issues across [Y] sprints. Quality analysis shows [quality insights].

Epic-level work focused on:
- [Epic 1]: [What was accomplished, distinguishing planning vs delivery]
- [Epic 2]: [What was accomplished]

Actual value deliveries (via fix versions):
- [Fix Version 1]: [What was delivered]
- [Fix Version 2]: [What was delivered]

Quality indicators show [strengths/areas for improvement] in ticket documentation, with [X]% having acceptance criteria and [Y]% including references to other documentation.
```

Generate the summary now:
