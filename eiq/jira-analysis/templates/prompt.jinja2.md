Analyze the JIRA sprint and epic data for {{ username }} during {{ analysis_period }} and generate a comprehensive markdown report.

**Configuration:**
- Username: {{ username }}
- Account ID: {{ account_id }}
- JIRA URL: {{ jira_url }}
- Period: {{ analysis_period }}

**Data Summary:**
- Total Sprints: {{ sprints_count }}
- Total Issues: {{ issues_count }}
- Total Worklogs: {{ worklogs_count }}
- Total Epics: {{ epics_count }}

**Sprint Metrics (includes accomplishments - completed issues per sprint):**
{{ sprint_metrics_json }}

**Note:** Sprint metrics are calculated based ONLY on issues assigned to {{ username }}. Each sprint metric includes:
- Total issues assigned to the user in that sprint
- Completed issues (with details in the "accomplishments" field)
- Completion rate based on user's issues only
- Velocity based on story points completed (sum of story points for completed issues)

**Issues Sample (first 50):**
{{ issues_json }}

**Worklogs Sample (first 100):**
{{ worklogs_json }}

**Epic Allocation:**
{{ epics_json }}

**Instructions:**

1. **Sprint Board Management Analysis:**
   - Analyze sprint loading: How well were sprints loaded before they started?
   - Calculate completion rates: What percentage of sprint issues were completed?
   - Identify patterns: Are there consistent issues with sprint planning or execution?

2. **Velocity Analysis:**
   - Calculate velocity trends: How many story points completed per sprint?
   - Assess consistency: Is velocity stable or variable?
   - Identify factors: What might be affecting velocity?

3. **Epic Allocation & Time Tracking:**
   - Analyze time distribution: How is time allocated across epics?
   - Calculate day allocation: Break down time spent per epic for time sheet/capex reporting
   - Assess estimation accuracy: Compare estimated vs. actual time spent
   - Identify focus areas: Which epics received the most attention?

4. **Sprint Planning Quality:**
   - Evaluate planning accuracy: Were sprints appropriately loaded?
   - Analyze issue breakdown: Distribution by type and priority
   - Assess load consistency: Are sprint loads consistent?

5. **Worklog Patterns:**
   - Analyze logging behavior: How frequently are worklogs created?
   - Identify time patterns: Are there patterns in when work is logged?
   - Assess completeness: Is time tracking comprehensive?

6. **Generate Recommendations:**
   - Provide actionable insights for improving sprint management
   - Suggest velocity improvement strategies
   - Recommend epic allocation optimizations
   - Suggest time tracking improvements

7. **Generate a comprehensive markdown report using the following template structure. Fill in all placeholders with your analysis:**
   
   **CRITICAL REQUIREMENT - Sprint Metrics Section:**
   - The report MUST include a "Sprint Metrics" section that lists each sprint
   - For EACH sprint, you MUST include:
     1. Sprint name (e.g., "WC Eng - 2025 Q4 Sprint 7")
     2. Completion Rate (as a percentage)
     3. Velocity (story points completed - sum of story points for completed issues)
     4. **Accomplishments subsection** that lists ALL completed issues from the "accomplishments" array
   - Format accomplishments as: "- [ISSUE-KEY]: [Summary]" (e.g., "- WC-1234: Implemented new feature")
   - Example format:
     ```
     ### WC Eng - 2025 Q4 Sprint 7
     - Completion Rate: 50.0%
     - Velocity: 15 points
     
     **Accomplishments:**
     - WC-1234: Implemented new feature
     - WC-1235: Fixed bug in authentication
     - WC-1236: Added unit tests
     - WC-1237: Updated documentation
     ```
   - Only include sprints that contain issues assigned to {{ username }}
   - If a sprint has no accomplishments (completed_issues = 0), list it but note "No completed issues" in accomplishments

{{ report_template }}

Replace all {{ '{{' }} placeholder {{ '}}' }} values with actual analysis. Return ONLY the completed markdown report with all placeholders filled in. Do not include markdown code blocks or explanations.

**Important Notes:**
- Convert JIRA time values (seconds) to hours for readability (divide by 3600)
- Calculate completion rates as percentages (completed / total * 100)
- Provide specific examples and numbers in your analysis
- Focus on actionable insights for performance evaluation and process improvement
