"""Utilities for parsing and accessing organizational ladder criteria."""

import re
from html.parser import HTMLParser
from pathlib import Path


class LadderTableParser(HTMLParser):
    """Parser for the organizational ladder HTML table."""

    def __init__(self):
        super().__init__()
        self.in_td = False
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []
        self.current_cell = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002
        if tag == "td" or tag == "th":
            self.in_td = True
            self.current_cell = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" or tag == "th":
            self.in_td = False
            # Clean up the cell content
            cell_content = self.current_cell.strip()
            # Remove extra whitespace and normalize
            cell_content = re.sub(r"\s+", " ", cell_content)
            self.current_row.append(cell_content)
        elif tag == "tr":
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []

    def handle_data(self, data: str) -> None:
        if self.in_td:
            self.current_cell += data


def parse_ladder_matrix(ladder_file: Path) -> dict[str, dict[str, list[str]]]:
    """
    Parse the ladder matrix HTML file and extract criteria by level.

    Returns:
        Dictionary mapping level (L3-L8) to competency areas and their criteria.
        Format: {
            "L3": {
                "Technical skills - Quality - Writing code": ["criteria1", ...],
                "Technical skills - Quality - Testing & evaluating": [...],
                ...
            },
            ...
        }
    """
    with open(ladder_file, encoding="utf-8") as f:
        content = f.read()

    parser = LadderTableParser()
    parser.feed(content)

    # Find header row (row with L3, L4, L5, etc.)
    level_columns: dict[str, int] = {}
    header_row_idx = None

    for i, row in enumerate(parser.rows):
        # Look for row containing level headers
        row_text = " ".join(row)
        if "L3" in row_text and "L4" in row_text:
            header_row_idx = i
            # Find column indices for each level
            for j, cell in enumerate(row):
                cell_clean = cell.strip()
                if cell_clean.startswith("L") and len(cell_clean) == 2:
                    level_columns[cell_clean] = j
            break

    if not level_columns:
        return {}

    # Extract criteria by level
    ladder_data: dict[str, dict[str, list[str]]] = {level: {} for level in level_columns}

    # Process data rows (skip header rows - typically first 5 rows)
    current_dimension = ""
    current_attribute = ""
    if header_row_idx is None:
        return ladder_data
    start_row = header_row_idx + 3  # Skip title/focus rows

    for row in parser.rows[start_row:]:
        if len(row) < max(level_columns.values()) + 1:
            continue

        # Skip row number column (first column is often just row number)
        # Extract cells - skip first column if it's just a number
        cells = row[1:] if row[0].strip().isdigit() else row
        if len(cells) < 3:
            continue

        dim_cell = cells[0].strip() if len(cells) > 0 else ""
        attr_cell = cells[1].strip() if len(cells) > 1 else ""
        comp_cell = cells[2].strip() if len(cells) > 2 else ""

        # Update current dimension
        if dim_cell in [
            "Technical skills",
            "Delivery",
            "Feedback, Communication, Collaboration",
            "Leadership",
        ]:
            current_dimension = dim_cell
            # Attribute might be in the next cell
            if len(cells) > 1:
                attr_candidate = cells[1].strip()
                if attr_candidate in [
                    "Quality",
                    "Operational Excellence",
                    "Design & architecture",
                    "Incremental value delivery",
                    "Self-organization",
                    "Feedback",
                    "Communication",
                    "Collaboration",
                    "Process thinking",
                    "Influence",
                    "Strategy",
                ]:
                    current_attribute = attr_candidate
                else:
                    current_attribute = ""
            else:
                current_attribute = ""

        # Update current attribute (can be in column 1 or 2)
        if attr_cell in [
            "Quality",
            "Operational Excellence",
            "Design & architecture",
            "Incremental value delivery",
            "Self-organization",
            "Feedback",
            "Communication",
            "Collaboration",
            "Process thinking",
            "Influence",
            "Strategy",
        ]:
            current_attribute = attr_cell

        # Extract criteria for competencies
        # Competency can be in column 1 (when it's a sub-row) or column 2
        competency = ""
        if comp_cell and comp_cell.lower() not in [
            "n/a",
            "title",
            "focus",
            "scaling of competencies",
            "",
        ]:
            competency = comp_cell
        elif (
            dim_cell
            and dim_cell
            not in [
                "Technical skills",
                "Delivery",
                "Feedback, Communication, Collaboration",
                "Leadership",
            ]
            and dim_cell.lower() not in ["n/a", "title", "focus", "scaling of competencies"]
            and not dim_cell.strip().isdigit()
        ):
            # Sometimes competency is in the first cell
            competency = dim_cell

        if competency:
            # Extract criteria for each level
            for level, col_idx in level_columns.items():
                # Adjust column index for actual data columns
                actual_col_idx = col_idx
                if row[0].strip().isdigit():
                    actual_col_idx = col_idx  # Already accounts for row number

                if actual_col_idx < len(row):
                    criteria = row[actual_col_idx].strip()
                    # Skip empty, n/a, or "see Lx" references
                    if (
                        criteria
                        and criteria.lower()
                        not in ["n/a", "see l3", "see l4", "see l5", "see l7", ""]
                        and not criteria.lower().startswith("see l")
                    ):
                        # Create key combining dimension, attribute, and competency
                        if current_dimension and current_attribute:
                            key = f"{current_dimension} - {current_attribute} - {competency}"
                        elif current_dimension:
                            key = f"{current_dimension} - {competency}"
                        else:
                            key = competency

                        if key not in ladder_data[level]:
                            ladder_data[level][key] = []
                        if criteria:
                            ladder_data[level][key].append(criteria)

    return ladder_data


def get_level_criteria(level: str, ladder_file: Path | None = None) -> dict[str, list[str]]:
    """
    Get criteria for a specific level.

    Args:
        level: Level string (e.g., "L4", "L5")
        ladder_file: Path to ladder matrix HTML file (defaults to ladder/Matrix.html)

    Returns:
        Dictionary mapping competency areas to their criteria for the level.
    """
    if ladder_file is None:
        # Default to ladder/Matrix.html relative to this file
        ladder_file = Path(__file__).parent.parent.parent / "ladder" / "Matrix.html"

    if not ladder_file.exists():
        return {}

    ladder_data = parse_ladder_matrix(ladder_file)

    return ladder_data.get(level, {})


def format_level_criteria_for_prompt(
    level: str, ladder_file: Path | None = None, include_next_level: bool = True
) -> str:
    """
    Format level criteria as a string for inclusion in prompts.

    Args:
        level: Level string (e.g., "L4", "L5")
        ladder_file: Path to ladder matrix HTML file
        include_next_level: If True, also include next level criteria as growth areas

    Returns:
        Formatted string with level criteria organized by competency area.
    """
    criteria = get_level_criteria(level, ladder_file)

    if not criteria:
        return ""

    lines = [f"## Level {level} Expectations\n"]
    lines.append("The following criteria should be used to evaluate performance at this level:\n")

    # Group by dimension
    dimensions: dict[str, list[tuple[str, list[str]]]] = {}
    for key, values in criteria.items():
        parts = key.split(" - ")
        if len(parts) >= 3:
            dimension = parts[0]
            if dimension not in dimensions:
                dimensions[dimension] = []
            dimensions[dimension].append((key, values))
        elif len(parts) == 2:
            # Try to infer dimension from key
            if parts[0] in [
                "Technical skills",
                "Delivery",
                "Feedback, Communication, Collaboration",
                "Leadership",
            ]:
                dimension = parts[0]
                if dimension not in dimensions:
                    dimensions[dimension] = []
                dimensions[dimension].append((key, values))
            else:
                # Unclassified - add to a general section
                if "Other" not in dimensions:
                    dimensions["Other"] = []
                dimensions["Other"].append((key, values))
        else:
            # Single part - unclassified
            if "Other" not in dimensions:
                dimensions["Other"] = []
            dimensions["Other"].append((key, values))

    for dimension in [
        "Technical skills",
        "Delivery",
        "Feedback, Communication, Collaboration",
        "Leadership",
        "Other",
    ]:
        if dimension in dimensions:
            lines.append(f"\n### {dimension}\n")
            for key, values in dimensions[dimension]:
                # Extract competency name (last part of key)
                parts = key.split(" - ")
                competency = parts[-1] if parts else key
                lines.append(f"**{competency}:**")
                for value in values:
                    lines.append(f"- {value}")
                lines.append("")

    # Include next level criteria as growth areas if requested
    if include_next_level:
        # Determine next level (L3 -> L4, L4 -> L5, etc.)
        level_num = int(level[1]) if len(level) == 2 and level[1].isdigit() else None
        if level_num and level_num < 8:
            next_level = f"L{level_num + 1}"
            next_criteria = get_level_criteria(next_level, ladder_file)
            if next_criteria:
                lines.append(f"\n## Next Level ({next_level}) Growth Areas\n")
                lines.append(
                    "The following criteria represent expectations for the next level. "
                    "Use these to identify growth opportunities and areas for development "
                    "toward promotion readiness. These should NOT be the primary evaluation criteria, "
                    "but rather areas to highlight where the engineer is already demonstrating next-level "
                    "capabilities or where they should focus development efforts:\n"
                )

                # Group next level by dimension
                next_dimensions: dict[str, list[tuple[str, list[str]]]] = {}
                for key, values in next_criteria.items():
                    parts = key.split(" - ")
                    if len(parts) >= 3:
                        dimension = parts[0]
                        if dimension not in next_dimensions:
                            next_dimensions[dimension] = []
                        next_dimensions[dimension].append((key, values))
                    elif len(parts) == 2:
                        if parts[0] in [
                            "Technical skills",
                            "Delivery",
                            "Feedback, Communication, Collaboration",
                            "Leadership",
                        ]:
                            dimension = parts[0]
                            if dimension not in next_dimensions:
                                next_dimensions[dimension] = []
                            next_dimensions[dimension].append((key, values))
                        else:
                            if "Other" not in next_dimensions:
                                next_dimensions["Other"] = []
                            next_dimensions["Other"].append((key, values))
                    else:
                        if "Other" not in next_dimensions:
                            next_dimensions["Other"] = []
                        next_dimensions["Other"].append((key, values))

                for dimension in [
                    "Technical skills",
                    "Delivery",
                    "Feedback, Communication, Collaboration",
                    "Leadership",
                    "Other",
                ]:
                    if dimension in next_dimensions:
                        lines.append(f"\n### {dimension}\n")
                        for key, values in next_dimensions[dimension]:
                            parts = key.split(" - ")
                            competency = parts[-1] if parts else key
                            lines.append(f"**{competency}:**")
                            for value in values:
                                lines.append(f"- {value}")
                            lines.append("")

    return "\n".join(lines)
