"""
FastAPI Backend — Phase 5
Web service API supporting Backtracking Pagination
to query chat data from ScyllaDB.

Run: uvicorn phase_5_dashboard.api:app --reload --host 0.0.0.0 --port 8000
"""
import os
import uvicorn
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
try:
    from .backend_service import ChatBackendService
except ImportError:
    from backend_service import ChatBackendService

# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated on_event)
# ---------------------------------------------------------------------------
db_service = ChatBackendService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to DB on startup, close on shutdown."""
    db_service.connect()
    yield
    db_service.close()


app = FastAPI(
    title="ScyllaDB Chat API",
    version="1.0.0",
    description="API to query chat messages from ScyllaDB with Backtracking Pagination support",
    lifespan=lifespan,
)

# CORS configuration to allow Streamlit dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/")
@app.get("/api/")
def read_root():
    return {"message": "ScyllaDB Chat API is running", "version": "1.0.0"}


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Check database connection status."""
    connected = db_service.session is not None
    return {"status": "healthy" if connected else "unhealthy", "database": "ScyllaDB"}


@app.get("/messages")
@app.get("/api/messages")
def get_messages(
    room_id: str = Query(..., description="Chat Room ID"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of messages"),
    state: Optional[str] = Query(None, description="Pagination token (bucket_id format YYYY-MM)")
):
    """
    API to fetch messages supporting bucket backtracking pagination.

    - If `state` is not provided: automatically backtracks from the current month
    - If `state` is provided (e.g., `2026-09`): queries that specific bucket directly
    """
    try:
        if state and "-" in state:
            # Query specific bucket directly
            messages = db_service.query_bucket(room_id, state, limit)
            # Next token: previous month
            year, month = map(int, state.split("-"))
            month -= 1
            if month == 0:
                month = 12
                year -= 1
            next_state = f"{year:04d}-{month:02d}"
        else:
            # Backtracking pagination from current month
            messages = db_service.get_messages(room_id, limit=limit)
            next_state = None
            if messages:
                last_msg = messages[-1]
                if last_msg["timestamp"]:
                    next_state = last_msg["timestamp"].strftime("%Y-%m")

        return {
            "room_id": room_id,
            "data": messages,
            "count": len(messages),
            "paging_state": next_state,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rooms")
@app.get("/api/rooms")
def get_rooms():
    """Get list of all available room_ids in the system."""
    try:
        rooms = db_service.get_available_rooms()
        return {"rooms": rooms, "count": len(rooms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
@app.get("/api/stats")
def get_stats():
    """Get statistics of message count per room."""
    try:
        stats = db_service.get_room_stats()
        total = sum(s["message_count"] for s in stats)
        return {"stats": stats, "total_messages": total, "total_rooms": len(stats)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/kaggle")
@app.get("/api/analyze/kaggle")
def analyze_kaggle(
    dataset: str = Query(..., description="Kaggle Dataset Slug (e.g., 'kazanova/sentiment140')"),
    text_column: Optional[str] = Query(None, description="Optional specific column name to analyze")
):
    """
    Downloads a dataset from Kaggle and performs NLP analysis on it.
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
    """
    try:
        try:
            from .kaggle_analyzer import analyze_kaggle_dataset
        except ImportError:
            from kaggle_analyzer import analyze_kaggle_dataset
            
        result = analyze_kaggle_dataset(dataset, text_column)
        return result
    except HTTPException as he:
        raise he
    except BaseException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/ai-feedback")
@app.post("/api/analyze/ai-feedback")
def analyze_ai_feedback(payload: dict):
    """
    Receives the universal data profile from kaggle_analyzer and asks Gemini to:
    1. Select the best chart types for each interesting column
    2. Generate a professional data-analyst narrative
    Returns JSON with { charts: [...], narrative: "..." }
    """
    import urllib.request
    import json

    profile = payload.get("profile", {})
    if not profile:
        raise HTTPException(status_code=400, detail="No profile data provided")

    columns_summary = ""
    cols = profile.get("columns", {})
    for col_name, col_info in cols.items():
        col_type = col_info.get("type", "unknown")
        columns_summary += f"\n- Column '{col_name}' (type={col_type})"
        if col_type == "numeric":
            s = col_info.get("stats", {})
            columns_summary += f": mean={s.get('mean')}, median={s.get('median')}, std={s.get('std')}, min={s.get('min')}, max={s.get('max')}, skewness={s.get('skewness')}"
        elif col_type == "categorical":
            dist = col_info.get("distribution", [])[:5]
            columns_summary += f": unique={col_info.get('unique_count')}, top values={[d['label'] for d in dist]}"
        elif col_type == "text":
            tw = col_info.get("top_words", [])[:5]
            columns_summary += f": avg_length={col_info.get('avg_length')}, top words={[w['word'] for w in tw]}"
        elif col_type == "datetime":
            s = col_info.get("stats", {})
            columns_summary += f": range from {s.get('min')} to {s.get('max')}, {s.get('range_days')} days"

    has_correlation = profile.get("correlation") is not None

    prompt = f"""You are an expert Data Analyst. Given the following dataset profile, do TWO things:

1. **CHARTS**: Choose 2-4 of the most insightful Chart.js charts to visualize this data.
   For each chart, output a JSON object with:
   - "title": a human-readable chart title
   - "type": one of "bar", "line", "doughnut", "pie", "radar", "polarArea", "scatter", "bubble"
   - "column": which column(s) this chart visualizes
   - "data": the actual {{ labels: [...], datasets: [...] }} object for Chart.js (use colors from this palette: #0ea5e9, #22c55e, #ef4444, #f59e0b, #8b5cf6, #ec4899, #14b8a6, #64748b)
   - "options": any Chart.js options (e.g. indexAxis for horizontal bar)

2. **NARRATIVE**: Write a 2-3 paragraph professional analysis summary.

Dataset: {profile.get('dataset')}
File: {profile.get('csv_analyzed')}
Dimensions: {profile.get('total_rows')} rows x {profile.get('total_cols')} columns
Missing Rate: {profile.get('missing_rate')}%
Columns: {columns_summary}
Has Correlation Matrix: {has_correlation}

IMPORTANT: Respond ONLY with valid JSON in this exact structure (no markdown, no code fences):
{{
  "charts": [ {{ "title": "...", "type": "...", "column": "...", "data": {{ "labels": [...], "datasets": [...] }}, "options": {{}} }} ],
  "narrative": "..."
}}"""

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _fallback_charts(profile)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"

    req_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        }
    }

    req_http = urllib.request.Request(
        url,
        data=json.dumps(req_body).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req_http, timeout=30) as response:
            result = json.loads(response.read().decode())
            text = result['candidates'][0]['content']['parts'][0]['text']
            # Parse the JSON response from Gemini
            parsed = json.loads(text)
            return parsed
    except Exception as e:
        # Fallback: generate charts locally without AI
        fallback = _fallback_charts(profile)
        fallback["ai_error"] = str(e)
        return fallback


def _fallback_charts(profile: dict) -> dict:
    """Generate sensible chart configs locally when Gemini is unavailable."""
    charts = []
    cols = profile.get("columns", {})
    palette = ['#0ea5e9', '#22c55e', '#ef4444', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#64748b']

    chart_count = 0
    for col_name, col_info in cols.items():
        if chart_count >= 4:
            break
        col_type = col_info.get("type", "unknown")

        if col_type == "numeric" and col_info.get("distribution"):
            dist = col_info["distribution"]
            charts.append({
                "title": f"Distribution of {col_name}",
                "type": "bar",
                "column": col_name,
                "data": {
                    "labels": [d["bin"] for d in dist],
                    "datasets": [{"label": "Frequency", "data": [d["count"] for d in dist],
                                  "backgroundColor": palette[chart_count % len(palette)], "borderRadius": 4}]
                },
                "options": {}
            })
            chart_count += 1

            # Add trend line if available
            if col_info.get("trend") and chart_count < 4:
                trend = col_info["trend"]
                charts.append({
                    "title": f"Trend of {col_name} (First {len(trend)} rows)",
                    "type": "line",
                    "column": col_name,
                    "data": {
                        "labels": list(range(1, len(trend) + 1)),
                        "datasets": [{"label": col_name, "data": trend,
                                      "borderColor": palette[chart_count % len(palette)],
                                      "backgroundColor": f"{palette[chart_count % len(palette)]}1A",
                                      "fill": True, "tension": 0.3, "pointRadius": 0}]
                    },
                    "options": {}
                })
                chart_count += 1

        elif col_type == "categorical" and col_info.get("distribution"):
            dist = col_info["distribution"]
            if len(dist) <= 6:
                charts.append({
                    "title": f"Distribution of {col_name}",
                    "type": "doughnut",
                    "column": col_name,
                    "data": {
                        "labels": [d["label"] for d in dist],
                        "datasets": [{"data": [d["count"] for d in dist],
                                      "backgroundColor": palette[:len(dist)], "borderWidth": 0}]
                    },
                    "options": {}
                })
            else:
                charts.append({
                    "title": f"Top Categories in {col_name}",
                    "type": "bar",
                    "column": col_name,
                    "data": {
                        "labels": [d["label"] for d in dist[:10]],
                        "datasets": [{"label": "Count", "data": [d["count"] for d in dist[:10]],
                                      "backgroundColor": palette[chart_count % len(palette)], "borderRadius": 4}]
                    },
                    "options": {"indexAxis": "y"}
                })
            chart_count += 1

        elif col_type == "text" and col_info.get("top_words"):
            words = col_info["top_words"][:10]
            charts.append({
                "title": f"Top Keywords in {col_name}",
                "type": "bar",
                "column": col_name,
                "data": {
                    "labels": [w["word"] for w in words],
                    "datasets": [{"label": "Frequency", "data": [w["count"] for w in words],
                                  "backgroundColor": palette[chart_count % len(palette)], "borderRadius": 4}]
                },
                "options": {"indexAxis": "y"}
            })
            chart_count += 1

    # Narrative fallback
    narrative = f"This dataset contains {profile.get('total_rows', '?')} rows and {profile.get('total_cols', '?')} columns "
    narrative += f"with a {profile.get('missing_rate', '?')}% missing data rate. "

    col_types = {}
    for c in cols.values():
        t = c.get("type", "unknown")
        col_types[t] = col_types.get(t, 0) + 1
    narrative += f"Column breakdown: {', '.join(f'{v} {k}' for k, v in col_types.items())}. "
    narrative += "AI-powered analysis is unavailable — charts were generated using rule-based heuristics."

    return {"charts": charts, "narrative": narrative}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

