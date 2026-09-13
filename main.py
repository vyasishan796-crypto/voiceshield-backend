import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from database import create_tables
from config import CORS_ORIGINS
from routers import auth_router, analysis_router, operator_router, government_router, admin_router, demo_router
from services.auth import verify_token

app = FastAPI(title="VoiceShield API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(operator_router, prefix="/api/v1")
app.include_router(government_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(demo_router, prefix="/api/v1")


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "version": "1.0.0"}


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_to_session(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(None)
):
    # Verify token if provided
    user = None
    if token:
        user = verify_token(token)

    await manager.connect(websocket, session_id)
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "sessionId": session_id,
            "authenticated": user is not None,
            "user": {"email": user.get("sub"), "role": user.get("role")} if user else None
        })

        while True:
            data = await websocket.receive_json()

            # Handle different message types
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "subscribe_analysis":
                analysis_id = data.get("analysisId")
                await websocket.send_json({
                    "type": "subscribed",
                    "analysisId": analysis_id,
                    "message": f"Subscribed to analysis {analysis_id}"
                })

            elif msg_type == "unsubscribe_analysis":
                analysis_id = data.get("analysisId")
                await websocket.send_json({
                    "type": "unsubscribed",
                    "analysisId": analysis_id
                })

            elif msg_type == "analysis_progress":
                # Broadcast progress to all connections in same session
                await manager.send_to_session(session_id, {
                    "type": "analysis_progress",
                    "analysisId": data.get("analysisId"),
                    "progress": data.get("progress", 0),
                    "stage": data.get("stage", "processing")
                })

            elif msg_type == "analysis_complete":
                # Broadcast completion to all connections in same session
                await manager.send_to_session(session_id, {
                    "type": "analysis_complete",
                    "analysisId": data.get("analysisId"),
                    "result": data.get("result")
                })

            elif msg_type == "threat_alert":
                # Government threat alert
                await manager.send_to_session(session_id, {
                    "type": "threat_alert",
                    "data": data.get("data")
                })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        manager.disconnect(websocket, session_id)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
