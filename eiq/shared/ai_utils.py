"""Shared utilities for AI/LLM operations."""

import os
from pathlib import Path

# Use new langchain-google-genai package (supports Vertex AI)
# Set Vertex AI mode before importing
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    # Fallback to deprecated package if new one not available
    try:
        from langchain_google_vertexai import (  # type: ignore[import-untyped]
            ChatVertexAI as ChatGoogleGenerativeAI,
        )
    except ImportError:
        ChatGoogleGenerativeAI = None  # type: ignore[assignment, misc]


def get_vertex_ai_llm(project: str, location: str = "us-east4", temperature: float = 0.3):
    """
    Get a Vertex AI LLM instance.

    Args:
        project: Google Cloud project ID
        location: Vertex AI location (default: us-east4)
        temperature: Model temperature (default: 0.3)

    Returns:
        ChatGoogleGenerativeAI instance

    Raises:
        ImportError: If langchain_google_genai or langchain_google_vertexai not available
    """
    if ChatGoogleGenerativeAI is None:
        raise ImportError(
            "langchain_google_genai or langchain_google_vertexai not available. Install with: uv sync"
        )

    # Set quota project
    os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = project

    return ChatGoogleGenerativeAI(
        model="gemini-2.5-pro",
        project=project,
        location=location,
        temperature=temperature,
    )


def load_ladder_criteria(level: str, include_next_level: bool = True) -> str:
    """
    Load ladder criteria for a level.

    Args:
        level: Level string (e.g., "L4", "L5")
        include_next_level: If True, also include next level criteria as growth areas

    Returns:
        Formatted string with level criteria, or empty string if not available
    """
    try:
        from eiq.shared.ladder_utils import format_level_criteria_for_prompt

        ladder_file = Path("ladder/Matrix.html")
        if ladder_file.exists():
            return format_level_criteria_for_prompt(
                level, ladder_file, include_next_level=include_next_level
            )
    except (ImportError, Exception):
        pass
    return ""
