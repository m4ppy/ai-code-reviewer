"""
AI reviewer module. Calls the OpenAI-compatible endpoint (Replit AI proxy)
to generate a structured Markdown code review.
"""

import os
from openai import OpenAI

AI_BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
AI_API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "dummy")

client = OpenAI(
    base_url=AI_BASE_URL,
    api_key=AI_API_KEY,
)

SYSTEM_PROMPT = """You are an expert code reviewer with deep knowledge of software engineering best practices, design patterns, security, and performance optimization.

You will receive:
1. Code to review
2. Static analysis results from Python AST
3. Relevant past code reviews from the knowledge base (RAG context)

Produce a comprehensive, structured Markdown code review following this exact format:

---

# Code Review

## Summary
Brief 2-3 sentence overview of the code's purpose and overall quality.

## Static Analysis Results
Summarize the AST analysis findings (errors, warnings, suggestions).

## Issues Found

### 🔴 Critical Issues
List critical bugs, security vulnerabilities, or crashes. If none, write "None found."

### 🟡 Warnings  
List code smells, anti-patterns, performance concerns. If none, write "None found."

### 🟢 Suggestions
List style improvements, documentation gaps, refactoring ideas.

## Security Analysis
Analyze for: injection vulnerabilities, unsafe operations, hardcoded secrets, insecure patterns.

## Performance Analysis
Assess algorithmic complexity, inefficient patterns, resource management.

## Best Practices Assessment
Evaluate: SOLID principles, DRY, naming conventions, error handling, testability.

## Positive Highlights
What the code does well — always include at least one positive point.

## Recommended Refactoring
Provide a short, concrete code snippet showing the most important improvement.

## Overall Score
Rate the code: **X/10** — one sentence justification.

---

Be specific, actionable, and constructive. Reference line numbers when possible.
"""


def generate_review(
    code: str,
    language: str,
    ast_summary: str,
    ast_issues: list,
    rag_context: str,
) -> str:
    """Call the AI to generate a structured code review."""

    issues_text = "\n".join(
        f"- [{i['severity'].upper()}] Line {i.get('line', '?')}: {i['message']}"
        for i in ast_issues
    ) or "No static analysis issues detected."

    user_prompt = f"""Please review the following {language} code:

```{language}
{code}
```

## Static Analysis Summary
{ast_summary}

## Detailed AST Issues
{issues_text}

{rag_context}

Please provide a thorough code review following the structured format in your instructions.
"""

    response = client.chat.completions.create(
        model="gpt-5.2",
        max_completion_tokens=8192,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content or "No review generated."
