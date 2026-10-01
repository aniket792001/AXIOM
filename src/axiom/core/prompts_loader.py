"""Prompt template loader for Axiom.

Loads decoupled Markdown/Jinja prompt templates from src/axiom/core/prompts/.
Uses safe variable injection so JSON formatting brackets in prompts are preserved.
"""

from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(template_name: str, **kwargs: str) -> str:
    """Load a markdown prompt template and replace {variable} placeholders safely."""
    file_path = PROMPTS_DIR / f"{template_name}.md"
    if not file_path.exists():
        raise FileNotFoundError(f"Prompt template '{template_name}.md' not found at {file_path}")

    content = file_path.read_text(encoding="utf-8")
    for key, value in kwargs.items():
        content = content.replace(f"{{{key}}}", str(value))
    return content
