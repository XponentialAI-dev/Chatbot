import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.genai.types import Part, Content
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from starlette.middleware import Middleware

from rag.agent import root_agent

# Load environment variables
load_dotenv()

# Configuration
APP_NAME = "XponentialAI Bot"
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"
session_service = InMemorySessionService()

# Middleware configuration
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"] if not IS_PRODUCTION else [
            "http://localhost:8000/",
            "https://chatbot-727q.onrender.com"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

app = FastAPI(
    title="XponentialAI Assistant Bot",
    description="API service for an Assistant Chatbot",
    middleware=middleware
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if IS_PRODUCTION:
        response.headers.update({
            "Content-Security-Policy": (
                "default-src 'self'; "
                "connect-src 'self' wss:; "  # Allow WebSocket connections
                "style-src 'self' 'unsafe-inline'; "  # Allow inline styles
                "script-src 'self' 'unsafe-inline'"   # Allow inline scripts
            ),
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        })
    return response

def start_agent_session(session_id: str):
    """Starts an agent session"""
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
    )

    runner = Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=session_service,
    )

    run_config = RunConfig(response_modalities=["TEXT"])
    live_request_queue = LiveRequestQueue()

    live_events = runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )
    return live_events, live_request_queue

async def agent_to_client_messaging(websocket: WebSocket, live_events):
    """Agent to client communication"""
    try:
        while True:
            async for event in live_events:
                if event.turn_complete:
                    await websocket.send_text(json.dumps({"turn_complete": True}))
                    print("[TURN COMPLETE]")

                if event.interrupted:
                    await websocket.send_text(json.dumps({"interrupted": True}))
                    print("[INTERRUPTED]")

                part: Part = (
                    event.content and event.content.parts and event.content.parts[0]
                )
                if not part or not event.partial:
                    continue

                text = event.content and event.content.parts and event.content.parts[0].text
                if not text:
                    continue

                await websocket.send_text(json.dumps({"message": text}))
                print(f"[AGENT TO CLIENT]: {text}")
                await asyncio.sleep(0)
    except WebSocketDisconnect:
        print("WebSocket disconnected (agent_to_client_messaging)")

async def client_to_agent_messaging(websocket: WebSocket, live_request_queue: LiveRequestQueue):
    """Client to agent communication"""
    try:
        while True:
            text = await websocket.receive_text()
            content = Content(role="user", parts=[Part.from_text(text=text)])
            live_request_queue.send_content(content=content)
            print(f"[CLIENT TO AGENT]: {text}")
            await asyncio.sleep(0)
    except WebSocketDisconnect:
        print("WebSocket disconnected (client_to_agent_messaging)")

# Static files setup
STATIC_DIR = Path("static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    return FileResponse(STATIC_DIR / "favicon.ico")

@app.get("/")
async def root():
    """Serves the index.html"""
    return FileResponse(STATIC_DIR / "index.html")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: int):
    """Secure WebSocket endpoint"""
    # Enforce WSS in production
    if IS_PRODUCTION and websocket.url.scheme != "wss":
        await websocket.close(code=1003)  # 1003 = Forbidden
        return

    await websocket.accept()
    print(f"Client #{session_id} connected")

    session_id = str(session_id)
    live_events, live_request_queue = start_agent_session(session_id)

    try:
        agent_task = asyncio.create_task(
            agent_to_client_messaging(websocket, live_events)
        )
        client_task = asyncio.create_task(
            client_to_agent_messaging(websocket, live_request_queue)
        )
        await asyncio.gather(agent_task, client_task)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print(f"Client #{session_id} disconnected")


@app.get("/pinecone-status")
async def pinecone_status():
    try:
        stats = pinecone_retriever.vectorstore.index.describe_index_stats()
        return {
            "status": "connected",
            "index_stats": stats,
            "index_name": pinecone_retriever.index_name
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        ssl_certfile=os.getenv("SSL_CERTFILE"),
        ssl_keyfile=os.getenv("SSL_KEYFILE"),
        reload=not IS_PRODUCTION
    )