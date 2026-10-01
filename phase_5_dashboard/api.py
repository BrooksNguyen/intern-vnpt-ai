import os
import uvicorn
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from phase_5_dashboard.backend_service import ChatBackendService

app = FastAPI(title="ScyllaDB Chat API", version="1.0.0")

# Khởi tạo kết nối db
db_service = ChatBackendService()

@app.on_event("startup")
def startup_event():
    db_service.connect()

@app.on_event("shutdown")
def shutdown_event():
    db_service.close()

@app.get("/")
def read_root():
    return {"message": "ScyllaDB Chat API is running"}

@app.get("/messages")
def get_messages(
    room_id: str = Query(..., description="ID của phòng chat"),
    limit: int = Query(50, description="Số lượng tin nhắn tối đa"),
    state: Optional[str] = Query(None, description="Token phân trang (có thể là paging_state gốc hoặc bucket_id)")
):
    """
    API lấy danh sách tin nhắn có hỗ trợ phân trang lùi bucket.
    """
    try:
        # Nếu có state (bucket_id) thì truy vấn trực tiếp bucket đó
        if state and "-" in state:  # Định dạng YYYY-MM
            messages = db_service.query_bucket(room_id, state, limit)
            # Logic đơn giản: token tiếp theo là tháng trước đó (chỉ mô phỏng)
            year, month = map(int, state.split("-"))
            month -= 1
            if month == 0:
                month = 12
                year -= 1
            next_state = f"{year:04d}-{month:02d}"
        else:
            # Nếu không truyền state, chạy thuật toán backtracking tự động tìm tin nhắn mới nhất
            messages = db_service.get_messages(room_id, limit=limit)
            
            # Gán state tiếp theo dựa trên timestamp của tin nhắn cuối cùng (nếu có)
            next_state = None
            if messages:
                last_msg = messages[-1]
                if last_msg["timestamp"]:
                    next_state = last_msg["timestamp"].strftime("%Y-%m")
        
        return {
            "room_id": room_id,
            "data": messages,
            "paging_state": next_state,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
