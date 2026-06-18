"""
Flask frontend for the AI-powered code reviewer.

Renders the UI and proxies requests to the FastAPI backend.
"""

import json
import os

import markdown2
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")


def call_backend(method: str, path: str, **kwargs):
    url = f"{BACKEND_URL}{path}"
    try:
        resp = requests.request(method, url, timeout=120, **kwargs)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend service. Make sure the FastAPI server is running."
    except requests.exceptions.Timeout:
        return None, "Request timed out. The AI review is taking longer than expected."
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/review", methods=["POST"])
def submit_review():
    code = request.form.get("code", "").strip()
    language = request.form.get("language", "").strip() or None

    if not code:
        return render_template("index.html", error="Please enter some code to review.")

    data, error = call_backend(
        "POST",
        "/api/review",
        json={"code": code, "language": language},
    )

    if error:
        return render_template("index.html", error=error, submitted_code=code)

    review_html = markdown2.markdown(
        data.get("review_markdown", ""),
        extras=["fenced-code-blocks", "tables", "header-ids", "strike", "task_list"],
    )

    return render_template(
        "result.html",
        review_html=review_html,
        review_data=data,
        submitted_code=code,
    )


@app.route("/history")
def history():
    data, error = call_backend("GET", "/api/reviews?limit=50")
    if error:
        return render_template("history.html", error=error, reviews=[])
    reviews = data.get("reviews", [])
    for r in reviews:
        if isinstance(r.get("tags"), str):
            try:
                r["tags"] = json.loads(r["tags"])
            except Exception:
                r["tags"] = []
    return render_template("history.html", reviews=reviews)


@app.route("/review/<int:review_id>")
def view_review(review_id):
    data, error = call_backend("GET", f"/api/reviews/{review_id}")
    if error:
        return render_template("index.html", error=error)

    if isinstance(data.get("tags"), str):
        try:
            data["tags"] = json.loads(data["tags"])
        except Exception:
            data["tags"] = []

    review_html = markdown2.markdown(
        data.get("review_markdown", ""),
        extras=["fenced-code-blocks", "tables", "header-ids", "strike", "task_list"],
    )
    return render_template(
        "result.html",
        review_html=review_html,
        review_data=data,
        submitted_code=data.get("code", ""),
    )


@app.route("/api/health")
def health():
    backend_data, error = call_backend("GET", "/api/health")
    return jsonify({
        "frontend": "ok",
        "backend": backend_data if backend_data else {"error": error},
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
