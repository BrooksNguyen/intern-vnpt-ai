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
def read_root():
    return {"message": "ScyllaDB Chat API is running", "version": "1.0.0"}


@app.get("/health")
def health_check():
    """Check database connection status."""
    connected = db_service.session is not None
    return {"status": "healthy" if connected else "unhealthy", "database": "ScyllaDB"}


@app.get("/messages")
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
def get_rooms():
    """Get list of all available room_ids in the system."""
    try:
        rooms = db_service.get_available_rooms()
        return {"rooms": rooms, "count": len(rooms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    """Get statistics of message count per room."""
    try:
        stats = db_service.get_room_stats()
        total = sum(s["message_count"] for s in stats)
        return {"stats": stats, "total_messages": total, "total_rooms": len(stats)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/kaggle")
def analyze_kaggle(
    dataset: str = Query(..., description="Kaggle Dataset Slug (e.g., 'kazanova/sentiment140')"),
    text_column: Optional[str] = Query(None, description="Optional specific column name to analyze")
):
    """
    Downloads a dataset from Kaggle and performs NLP analysis on it.
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
    """
    try:
        from kaggle_analyzer import analyze_kaggle_dataset
        result = analyze_kaggle_dataset(dataset, text_column)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
