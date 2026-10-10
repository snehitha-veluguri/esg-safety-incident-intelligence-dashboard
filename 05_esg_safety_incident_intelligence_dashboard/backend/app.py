
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="ESG / Safety Incident Intelligence Dashboard")

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
FRONTEND = BASE / "frontend"


class Query(BaseModel):
    text: str = ""


@app.get("/")
def home():
    index_file = FRONTEND / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "ESG / Safety Incident Intelligence Dashboard API is running",
        "docs": "/docs",
        "demo": "/api/demo",
    }


@app.get("/api/demo")
def demo():
    return {
        "case_study": "ESG / Safety Incident Intelligence Dashboard",
        "status": "starter app running",
        "expected_outcome": (
            "A dashboard that classifies incident type, severity, recurring "
            "patterns, and recommended preventive actions using NLP and "
            "summarization logic."
        ),
    }


@app.post("/api/run")
def run_case(query: Query):
    return {
        "input": query.text,
        "result": "Implement candidate solution here.",
        "evaluation_hint": (
            "Return predictions, retrieval evidence, reasoning steps, "
            "metrics, and limitations."
        ),
    }
