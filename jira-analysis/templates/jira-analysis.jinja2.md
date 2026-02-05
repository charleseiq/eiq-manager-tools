# JIRA Analysis: {{ username }}

**Analysis Period**: {{ analysis_period }}

---

## Executive Summary

{{ executive_summary }}

**Key Metrics:**
- **Sprints Analyzed**: {{ sprints_count }} sprints in {{ analysis_period }}
- **Issues Worked**: {{ issues_count }} issues
- **Average Sprint Completion Rate**: {{ avg_completion_rate }}%
- **Average Velocity**: {{ avg_velocity }} points per sprint
- **Epic Allocation**: {{ epics_count }} epics tracked
- **Total Time Logged**: {{ total_time_logged }} hours

---

## 1. Sprint Board Management

### Sprint Loading Analysis

{{ sprint_loading_analysis }}

**Sprint Loading Metrics:**

| Sprint | Start Date | End Date | Issues Loaded | Completion Rate | Velocity |
|--------|------------|----------|---------------|-----------------|----------|
{{ sprint_loading_table }}

### Completion Rate Analysis

{{ completion_rate_analysis }}

**Key Insights:**
- **Average Completion Rate**: {{ avg_completion_rate }}%
- **Best Sprint**: {{ best_sprint }} ({{ best_completion_rate }}%)
- **Areas for Improvement**: {{ completion_improvements }}

---

## 2. Velocity Analysis

### Velocity Trends

{{ velocity_analysis }}

**Velocity Metrics:**

| Sprint | Planned Issues | Completed Issues | Velocity | Trend |
|--------|---------------|------------------|----------|-------|
{{ velocity_table }}

### Velocity Consistency

{{ velocity_consistency }}

**Key Insights:**
- **Average Velocity**: {{ avg_velocity }} points/sprint
- **Velocity Standard Deviation**: {{ velocity_std_dev }}
- **Velocity Trend**: {{ velocity_trend }}

---

## 3. Epic Allocation & Time Tracking

### Epic Time Distribution

{{ epic_allocation_analysis }}

**Epic Allocation Summary:**

| Epic | Issues | Time Spent (hours) | Time Estimate (hours) | Variance |
|------|--------|-------------------|----------------------|----------|
{{ epic_allocation_table }}

### Day Allocation Analysis

{{ day_allocation_analysis }}

**Time Allocation Breakdown:**
- **Total Time Logged**: {{ total_time_logged }} hours
- **Average per Issue**: {{ avg_time_per_issue }} hours
- **Estimation Accuracy**: {{ estimation_accuracy }}%

### Epic Focus Areas

{{ epic_focus_areas }}

**Top 3 Epics by Time Allocation:**
1. {{ top_epic_1 }}
2. {{ top_epic_2 }}
3. {{ top_epic_3 }}

---

## 4. Sprint Planning Quality

### Planning Accuracy

{{ planning_accuracy }}

**Planning Metrics:**
- **Average Sprint Load**: {{ avg_sprint_load }} issues
- **Load Consistency**: {{ load_consistency }}
- **Planning vs. Execution Variance**: {{ planning_variance }}%

### Issue Breakdown

{{ issue_breakdown }}

**Issue Type Distribution:**

| Type | Count | Percentage |
|------|-------|------------|
{{ issue_type_table }}

**Priority Distribution:**

| Priority | Count | Percentage |
|----------|-------|------------|
{{ priority_table }}

---

## 5. Worklog Patterns

### Time Logging Behavior

{{ worklog_patterns }}

**Worklog Insights:**
- **Total Worklogs**: {{ worklogs_count }}
- **Average Time per Worklog**: {{ avg_worklog_time }} hours
- **Logging Frequency**: {{ logging_frequency }}

### Time Allocation by Day

{{ time_by_day_analysis }}

**Weekly Pattern:**

| Day | Hours Logged | Issues Worked |
|-----|-------------|---------------|
{{ time_by_day_table }}

---

## 6. Recommendations

### Sprint Management

{{ sprint_management_recommendations }}

### Velocity Improvement

{{ velocity_recommendations }}

### Epic Allocation

{{ epic_allocation_recommendations }}

### Time Tracking

{{ time_tracking_recommendations }}

---

## 7. Detailed Sprint Breakdown

{{ detailed_sprint_breakdown }}

**Note:** Only sprints containing issues assigned to {{ username }} are included. Metrics are calculated based solely on the user's issues in each sprint.

---

## 8. Detailed Epic Breakdown

{{ detailed_epic_breakdown }}

---

## Appendix: Raw Data Summary

- **Total Sprints**: {{ sprints_count }}
- **Total Issues**: {{ issues_count }}
- **Total Worklogs**: {{ worklogs_count }}
- **Total Epics**: {{ epics_count }}
- **Analysis Date**: {{ analysis_date }}
