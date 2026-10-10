
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
import re

app = FastAPI(title="ESG / Safety Incident Intelligence Dashboard")

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
FRONTEND = BASE / "frontend"
CSV_FILE = DATA / "safety_esg_incidents.csv"


class Query(BaseModel):
    text: str = ""


def load_incidents():
    if CSV_FILE.exists():
        return pd.read_csv(CSV_FILE).fillna("")
    return pd.DataFrame(
        columns=["incident_id", "narrative", "target_category", "target_severity"]
    )


def classify_incident(text):
    t = text.lower()

    if any(word in t for word in [
        "waste segregation", "compliance", "regulatory", "policy deviation"
    ]):
        return "esg_compliance"

    if any(word in t for word in [
        "oil", "spill", "seepage", "water usage", "water leak",
        "valve leakage", "environment", "emission", "pollution", "waste"
    ]):
        return "environment"

    return "safety"


def assess_severity(text):
    t = text.lower()

    high_signals = [
        "fracture", "fractured", "hospital", "fatal", "serious injury",
        "near miss", "cable trench", "oil seepage", "spill", "fire",
        "electric shock", "high severity"
    ]
    low_signals = [
        "waste segregation", "minor observation", "paperwork",
        "administrative", "low severity"
    ]

    if any(word in t for word in high_signals):
        return "high"
    if any(word in t for word in low_signals):
        return "low"
    return "medium"


def recommend_actions(category, text):
    t = text.lower()
    actions = []

    if any(word in t for word in ["slip", "wet", "oil", "spill"]):
        actions.extend([
            "Clean and contain spills promptly.",
            "Place warning signs and restrict access until the area is safe.",
            "Inspect walkways and maintenance areas routinely."
        ])

    if any(word in t for word in ["ppe", "protective equipment", "panel cleaning"]):
        actions.extend([
            "Verify appropriate PPE before work begins.",
            "Conduct toolbox talks and supervisor safety checks."
        ])

    if any(word in t for word in ["vehicle", "cable trench", "near miss"]):
        actions.extend([
            "Separate vehicle routes from pedestrian and trench work areas.",
            "Review traffic controls, lighting, and barriers for night shifts."
        ])

    if any(word in t for word in ["water", "valve", "leak"]):
        actions.extend([
            "Inspect valves and repair leaks promptly.",
            "Monitor water consumption for unusual increases."
        ])

    if any(word in t for word in ["waste", "segregation"]):
        actions.extend([
            "Provide clearly labelled waste segregation bins.",
            "Audit contractor waste handling and provide refresher training."
        ])

    if category == "environment" and not actions:
        actions.append("Investigate the environmental source and document containment or corrective actions.")

    if category == "esg_compliance" and not actions:
        actions.append("Review the relevant procedure, document the deviation, and verify corrective action.")

    if category == "safety" and not actions:
        actions.append("Investigate the hazard, correct unsafe conditions, and brief workers on preventive controls.")

    return list(dict.fromkeys(actions))


def find_evidence(text, incidents):
    words = set(re.findall(r"[a-z]{3,}", text.lower()))
    matches = []

    for _, row in incidents.iterrows():
        narrative = str(row["narrative"])
        other_words = set(re.findall(r"[a-z]{3,}", narrative.lower()))
        common = sorted(words & other_words)

        if common:
            matches.append({
                "incident_id": str(row["incident_id"]),
                "narrative": narrative,
                "category": str(row["target_category"]),
                "severity": str(row["target_severity"]),
                "matching_terms": common
            })

    matches.sort(key=lambda item: len(item["matching_terms"]), reverse=True)
    return matches[:3]


@app.get("/")
def home():
    index_file = FRONTEND / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "ESG / Safety Incident Intelligence Dashboard API is running",
        "docs": "/docs",
        "demo": "/api/demo"
    }


@app.get("/api/demo")
def demo():
    return {
        "case_study": "ESG / Safety Incident Intelligence Dashboard",
        "status": "running",
        "dataset_records": len(load_incidents())
    }


@app.get("/api/summary")
def summary():
    incidents = load_incidents()

    if incidents.empty:
        return {"total_incidents": 0, "category_counts": {}, "severity_counts": {}}

    return {
        "total_incidents": int(len(incidents)),
        "category_counts": {
            str(k): int(v)
            for k, v in incidents["target_category"].value_counts().items()
        },
        "severity_counts": {
            str(k): int(v)
            for k, v in incidents["target_severity"].value_counts().items()
        },
        "note": "Counts describe the supplied sample dataset only."
    }


@app.post("/api/run")
def run_case(query: Query):
    text = query.text.strip()

    if not text:
        return {"error": "Please provide an incident narrative in the text field."}

    incidents = load_incidents()
    category = classify_incident(text)
    severity = assess_severity(text)
    evidence = find_evidence(text, incidents)

    return {
        "input": text,
        "predicted_category": category,
        "predicted_severity": severity,
        "recommended_actions": recommend_actions(category, text),
        "matching_dataset_incidents": evidence,
        "dataset_size": int(len(incidents)),
        "method": "Transparent keyword-based baseline; not a trained ML model.",
        "limitations": [
            "Predictions depend on predefined keywords and may be incorrect.",
            "Severity should be reviewed by a qualified safety professional.",
            "The supplied dataset contains only six sample incidents."
        ]
    }
