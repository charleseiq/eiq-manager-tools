# GitHub Review Analysis: {{ username }}

**Analysis Period**: {{ analysis_period }}

---

## Executive Summary

{{ executive_summary }}

**Key Metrics:**
- **PRs Reviewed**: {{ prs_reviewed_count }} PRs analyzed in {{ analysis_period }}
- **Comment Distribution**: {{ architecture_pct }}% Architecture, {{ logic_pct }}% Logic, {{ nits_pct }}% Nits
- **PR Description Quality**: {{ avg_context_score }}/5 Context, {{ avg_risk_score }}/5 Risk, {{ avg_clarity_score }}/5 Clarity
- **Cross-Boundary Reviews**: {{ cross_boundary_count }} PR reviewed outside their primary team's repositories
- **Response Time**: PRs typically addressed within {{ response_time_range }} hours after feedback

---

## 1. Bikeshedding vs Architecture

### Comment Classification Summary

| Category | Count | Percentage |
|----------|-------|------------|
| **Architecture** | {{ architecture_count }} | {{ architecture_pct }}% |
| **Logic** | {{ logic_count }} | {{ logic_pct }}% |
| **Nits** | {{ nits_count }} | {{ nits_pct }}% |
| **Total** | {{ total_comments }} | 100% |

**Analysis**: {{ comment_analysis }}

### Top Architecture Feedback Examples

{{ architecture_examples }}

---

## 2. PR Description Quality

### Analysis of PRs Reviewed

{{ pr_description_table }}

### Average Scores

- **Average Context Score**: {{ avg_context_score }}/5
- **Average Risk Score**: {{ avg_risk_score }}/5
- **Average Clarity Score**: {{ avg_clarity_score }}/5
- **Template Usage**: {{ template_usage_pct }}%
- **Template Fill Rate**: {{ template_fill_pct }}%

**Analysis**: 
{{ pr_description_analysis }}

---

## 3. Cross-Boundary Influence

### Contributions Outside Primary Team's Repositories

{{ cross_boundary_table }}

**Summary**: {{ username }} reviewed **{{ cross_boundary_count }} PR(s)** outside their primary team's repositories:
- **Cross-boundary reviews**: {{ cross_boundary_count }} PRs
- **With comments**: {{ cross_boundary_with_comments }} PRs
- **Repositories**: {{ cross_boundary_repos_count }} different repo(s) ({{ cross_boundary_repos }})
- **Nature**: {{ cross_boundary_nature }}

---

## 4. Conflict Management

### PRs Where Changes Were Requested or Questions Raised

{{ conflict_management_examples }}

**Analysis**: 
{{ conflict_analysis }}

---

## 5. Most Significant Changes

{{ significant_changes }}

---

## Summary

{{ summary }}

---

## Recommendations

{{ recommendations }}
