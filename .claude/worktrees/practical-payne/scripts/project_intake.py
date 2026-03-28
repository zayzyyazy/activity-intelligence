#!/usr/bin/env python3
"""
project_intake.py — Interactive project intake mode.

Reads any existing project_context.md, asks focused questions, and
synthesizes the answers into structured output ready to save as files.

Usage:
    python3 scripts/project_intake.py           # prints to terminal
    python3 scripts/project_intake.py --save    # also saves to data/intake_TIMESTAMP.md
    python3 scripts/project_intake.py > intake.md  # redirect stdout, prompts go to stderr
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from app.config import OPENAI_API_KEY

PROJECT_ROOT = Path(__file__).parent.parent
CONTEXT_FILE = PROJECT_ROOT / "project_context.md"
DATA_DIR     = PROJECT_ROOT / "data"

client = OpenAI(api_key=OPENAI_API_KEY)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _err(msg: str) -> None:
    """Print to stderr so stdout stays clean for redirection."""
    print(msg, file=sys.stderr)


def _input(prompt: str = "> ") -> str:
    """Read a line from stdin; prompt goes to stderr so it is not captured."""
    sys.stderr.write(prompt)
    sys.stderr.flush()
    return sys.stdin.readline().strip()


# ── Phase 1: generate questions ───────────────────────────────────────────────

def _read_existing_context() -> str:
    if CONTEXT_FILE.exists():
        return CONTEXT_FILE.read_text().strip()
    return ""


def _generate_questions(existing_context: str) -> list:
    context_section = (
        f"\nExisting project_context.md:\n{existing_context}\n"
        if existing_context else ""
    )

    prompt = f"""You are helping gather background information about a software project so an AI assistant can understand it before helping build it.
{context_section}
Generate 4-5 short, practical questions that would help understand:
- What the project is and does
- Who it is for
- The tech stack
- Current state and what is already done
- What success looks like

Rules:
- One sentence per question
- Practical and direct
- Skip questions already answered by the existing context above
- Return ONLY a JSON array of strings, no explanation

Example: ["question 1", "question 2", ...]"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        lines = [l for l in content.splitlines() if not l.strip().startswith("```")]
        content = "\n".join(lines).strip()

    try:
        questions = json.loads(content)
        if isinstance(questions, list) and questions:
            return questions
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback questions if parsing fails
    return [
        "What does this project do, in one or two sentences?",
        "Who is it for — just you, a team, or end users?",
        "What is the tech stack?",
        "What is already working, and what is not built yet?",
        "What does success look like for this project?",
    ]


# ── Phase 2: collect answers ──────────────────────────────────────────────────

def _ask_questions(questions: list) -> dict:
    _err("\n── Project Intake ──────────────────────────────────")
    _err("Answer each question. Press Enter to skip.")
    _err("────────────────────────────────────────────────────\n")

    answers = {}
    for i, question in enumerate(questions, 1):
        _err(f"[{i}/{len(questions)}] {question}")
        answer = _input("> ")
        answers[question] = answer
        _err("")

    return answers


# ── Phase 3: generate output ──────────────────────────────────────────────────

def _generate_output(existing_context: str, answers: dict) -> str:
    answered = {q: a for q, a in answers.items() if a}
    qa_block  = "\n".join(f"Q: {q}\nA: {a}" for q, a in answered.items())

    prompt = f"""You are synthesizing project intake answers into structured output for an AI build assistant.

Existing context (if any):
{existing_context or "(none)"}

Intake Q&A:
{qa_block or "(no answers provided)"}

Generate this exact structure. Keep each section short and practical:

## Project understanding
(2-3 sentences: what it is, who it is for, current state)

## Open questions
(gaps or unclear areas — list up to 3, or write "None" if all clear)

## Suggested project_context.md
(a clean markdown file with: Project name, Goal, Stack, Current task, Success criteria)

## Suggested current_step.md
(a single paragraph written as a direct prompt for an AI build assistant — describing the most logical next implementation step)

Rules:
- Be concise
- No filler words
- Write the file sections as ready-to-use file content, not as commentary about them"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    save_to_file = "--save" in sys.argv

    existing_context = _read_existing_context()
    if existing_context:
        _err("Found existing project_context.md — using it as a starting point.\n")

    questions = _generate_questions(existing_context)
    answers   = _ask_questions(questions)

    _err("Generating output...\n")

    output = _generate_output(existing_context, answers)

    # Always print to stdout (captured if user redirects)
    print(output)

    if save_to_file:
        DATA_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outfile   = DATA_DIR / f"intake_{timestamp}.md"
        outfile.write_text(output)
        _err(f"Saved to {outfile}")


if __name__ == "__main__":
    main()
