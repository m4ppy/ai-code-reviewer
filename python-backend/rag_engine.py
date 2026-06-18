"""
RAG (Retrieval-Augmented Generation) engine.

Stores past code reviews in SQLite and retrieves the most relevant ones
using TF-IDF + cosine similarity when building prompts for new reviews.
"""

import json
import re
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import get_all_reviews_for_rag


def _tokenize_code(code: str) -> str:
    """Convert code into a bag-of-words string suitable for TF-IDF."""
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[+\-*/=<>!]+|\d+", code)
    return " ".join(tokens)


def retrieve_similar_reviews(
    query_code: str,
    language: Optional[str] = None,
    top_k: int = 3,
) -> list:
    """
    Given a piece of code, retrieve the top_k most semantically similar
    past reviews from the database using TF-IDF cosine similarity.

    Returns a list of dicts with keys:
      - code
      - language
      - review_markdown
      - ast_summary
      - similarity_score
    """
    past_reviews = get_all_reviews_for_rag(language=language)

    if not past_reviews:
        return []

    corpus = [_tokenize_code(r["code"]) for r in past_reviews]
    query_tok = _tokenize_code(query_code)

    all_docs = corpus + [query_tok]

    vectorizer = TfidfVectorizer(
        max_features=5000,
        sublinear_tf=True,
        min_df=1,
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(all_docs)
    except ValueError:
        return []

    query_vec = tfidf_matrix[-1]
    corpus_vecs = tfidf_matrix[:-1]

    sims = cosine_similarity(query_vec, corpus_vecs).flatten()

    top_indices = np.argsort(sims)[::-1][:top_k]

    results = []
    for idx in top_indices:
        if sims[idx] < 0.05:
            continue
        review = past_reviews[idx]
        results.append(
            {
                "code": review["code"],
                "language": review["language"],
                "review_markdown": review["review_markdown"],
                "ast_summary": review.get("ast_summary", ""),
                "similarity_score": float(sims[idx]),
            }
        )

    return results


def build_rag_context(similar_reviews: list) -> str:
    """
    Format retrieved reviews into a context block for the LLM prompt.
    """
    if not similar_reviews:
        return ""

    parts = ["## Relevant Past Code Reviews (for context)\n"]
    for i, review in enumerate(similar_reviews, 1):
        score_pct = int(review["similarity_score"] * 100)
        lang = review.get("language", "unknown")
        parts.append(f"### Past Review {i} (similarity: {score_pct}%, language: {lang})")
        code_snippet = review["code"]
        if len(code_snippet) > 400:
            code_snippet = code_snippet[:400] + "\n... [truncated]"
        parts.append(f"```{lang}\n{code_snippet}\n```")
        if review.get("ast_summary"):
            parts.append(f"**Static analysis:** {review['ast_summary']}")
        parts.append("**Previous review excerpt:**")
        review_excerpt = review["review_markdown"]
        if len(review_excerpt) > 600:
            review_excerpt = review_excerpt[:600] + "\n... [truncated]"
        parts.append(review_excerpt)
        parts.append("---")

    return "\n".join(parts)
