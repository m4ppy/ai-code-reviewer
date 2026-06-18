import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("SQLITE_DB_PATH", "code_reviews.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS code_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            language TEXT NOT NULL,
            review_markdown TEXT NOT NULL,
            ast_summary TEXT,
            issues_count INTEGER DEFAULT 0,
            severity TEXT DEFAULT 'info',
            tags TEXT DEFAULT '[]',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_reviews_language ON code_reviews (language);
        CREATE INDEX IF NOT EXISTS idx_reviews_created_at ON code_reviews (created_at);
    """)
    conn.commit()
    conn.close()


def save_review(
    code: str,
    language: str,
    review_markdown: str,
    ast_summary: str,
    issues_count: int,
    severity: str,
    tags: list,
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO code_reviews
          (code, language, review_markdown, ast_summary, issues_count, severity, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            code,
            language,
            review_markdown,
            ast_summary,
            issues_count,
            severity,
            json.dumps(tags),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    review_id = cursor.lastrowid
    conn.close()
    return review_id


def get_recent_reviews(limit: int = 20) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, code, language, review_markdown, ast_summary,
               issues_count, severity, tags, created_at
        FROM code_reviews
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_reviews_for_rag(language: Optional[str] = None) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if language:
        cursor.execute(
            """
            SELECT id, code, language, review_markdown, ast_summary, tags
            FROM code_reviews
            WHERE language = ?
            ORDER BY created_at DESC
            LIMIT 200
            """,
            (language,),
        )
    else:
        cursor.execute(
            """
            SELECT id, code, language, review_markdown, ast_summary, tags
            FROM code_reviews
            ORDER BY created_at DESC
            LIMIT 200
            """
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_review_by_id(review_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM code_reviews WHERE id = ?",
        (review_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


init_db()
