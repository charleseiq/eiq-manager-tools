---
name: pr-review-analysis
description: Analyzes GitHub PR review quality by classifying comments (Architecture/Logic/Nits), scoring PR descriptions, identifying cross-boundary contributions, analyzing conflict management, and summarizing significant changes. Use when analyzing PR review performance, generating review quality reports, or evaluating code review effectiveness for team members.
---

# PR Review Analysis

Generates comprehensive analysis reports of GitHub PR review contributions using LangGraph workflows and Vertex AI.

## Quick Start

Use the CLI tool:

```bash
gh-analyze <username> --start <YYYY-MM-DD> --end <YYYY-MM-DD>
```

The CLI handles all workflow execution internally.

## Implementation

All implementation code is located in `pr-review-analysis/` at the repository root:

- **Workflows**: `pr-review-analysis/workflows/` - LangGraph workflow implementation
- **Scripts**: `pr-review-analysis/scripts/` - Utility scripts for data fetching
- **Templates**: `pr-review-analysis/templates/` - Report templates
- **Documentation**: `pr-review-analysis/docs/` - Detailed documentation

See `pr-review-analysis/README.md` for full documentation.

## What Gets Analyzed

1. **Comment Classification**: Architecture vs Logic vs Nits
2. **PR Description Quality**: Context, Risk, Clarity scores
3. **Cross-Boundary Influence**: Contributions outside primary repository
4. **Conflict Management**: Tone and resolution time analysis
5. **Significant Changes**: Most impactful contributions made by the user

## Output

Generates a comprehensive markdown report (`github-review-analysis.md`) with:
- Executive summary
- Comment distribution analysis
- PR description quality metrics
- Cross-boundary contribution summary
- Conflict management examples
- Significant changes summary
- Recommendations
