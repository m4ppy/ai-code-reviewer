"""
FastAPI backend for the AI-powered code reviewer.

Endpoints:
  POST /api/review      - Submit code for review (full RAG + AI pipeline)
  GET  /api/reviews     - List past reviews
  GET  /api/reviews/:id - Get a specific review
  GET  /api/health      - Health check
"""

import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ast_analyzer import ASTAnalyzer, detect_language
from database import get_recent_reviews, get_review_by_id, save_review
from rag_engine import build_rag_context, retrieve_similar_reviews
from ai_reviewer import generate_review

app = FastAPI(
    title="AI Code Reviewer API",
    description="FastAPI backend for RAG-powered AI code reviews",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    code: str
    language: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    language: str
    review_markdown: str
    ast_summary: str
    issues_count: int
    severity: str
    tags: list
    rag_context_used: bool
    similar_reviews_count: int


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "AI Code Reviewer FastAPI"}


@app.post("/api/review", response_model=ReviewResponse)
def create_review(request: ReviewRequest):
    code = request.code.strip()
    if not code:
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    if len(code) > 50_000:
        raise HTTPException(status_code=400, detail="Code exceeds 50,000 character limit")

    language = request.language or detect_language(code)

    analyzer = ASTAnalyzer(code) if language == "python" else None
    if analyzer:
        analysis = analyzer.analyze()
        ast_summary = analysis.get("summary", "")
        ast_issues = analysis.get("issues", [])
        severity = analysis.get("severity", "info")
        tags = analysis.get("tags", [])
    else:
        ast_summary = f"Static analysis not available for {language} (only Python is supported)."
        ast_issues = []
        severity = "info"
        tags = []

    similar_reviews = retrieve_similar_reviews(code, language=language, top_k=3)
    rag_context = build_rag_context(similar_reviews)

    review_markdown = generate_review(
        code=code,
        language=language,
        ast_summary=ast_summary,
        ast_issues=ast_issues,
        rag_context=rag_context,
    )

    issues_count = len(ast_issues)

    review_id = save_review(
        code=code,
        language=language,
        review_markdown=review_markdown,
        ast_summary=ast_summary,
        issues_count=issues_count,
        severity=severity,
        tags=tags,
    )

    return ReviewResponse(
        id=review_id,
        language=language,
        review_markdown=review_markdown,
        ast_summary=ast_summary,
        issues_count=issues_count,
        severity=severity,
        tags=tags,
        rag_context_used=len(similar_reviews) > 0,
        similar_reviews_count=len(similar_reviews),
    )


@app.get("/api/reviews")
def list_reviews(limit: int = 20):
    reviews = get_recent_reviews(limit=min(limit, 100))
    for r in reviews:
        if isinstance(r.get("tags"), str):
            try:
                r["tags"] = json.loads(r["tags"])
            except Exception:
                r["tags"] = []
    return {"reviews": reviews, "count": len(reviews)}


@app.get("/api/reviews/{review_id}")
def get_review(review_id: int):
    review = get_review_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if isinstance(review.get("tags"), str):
        try:
            review["tags"] = json.loads(review["tags"])
        except Exception:
            review["tags"] = []
    return review


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("FASTAPI_PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
