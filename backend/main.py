import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Setting the agent model name from environment variables
AGENT_MODEL_NAME = os.getenv("AGENT_MODEL", "gemma2:2b")

# Setting up FastAPI application instance
app = FastAPI(
    title="AI Agent Simulation Backend",
    description="offering backend services for AI scam attack-defense simulations.",
    version="0.1.0"
)

# --- API routes ---

@app.get("/")
def read_root():
    """ Root route for health check """
    return {"status": "Backend is running", "model_in_use": AGENT_MODEL_NAME}

# WebSocket interface for frontend
# This is the core port for your partner to connect in the future
@app.websocket("/ws/simulation/{simulation_id}")
async def websocket_endpoint(websocket: WebSocket, simulation_id: str):
    """ Handling real-time WebSocket communication for simulation process """
    await websocket.accept()
    print(f"Frontend connected for simulation: {simulation_id}")
    try:
        # This is where the future ADK simulator will interact with the frontend
        # We first send a connection success message
        await websocket.send_json({
            "event_type": "connection_success",
            "payload": {"simulation_id": simulation_id}
        })
        while True:
            # Keep the connection open to receive messages from the frontend or push events from the backend
            # In a real application, this would be an event loop
            await websocket.receive_text() # Wait for frontend messages (currently not processed)

    except WebSocketDisconnect:
        print(f"Frontend disconnected from simulation: {simulation_id}")
    except Exception as e:
        print(f"An error occurred in WebSocket: {e}")
        await websocket.close(code=1011, reason="Server error")


# --- Server Startup ---

if __name__ == "__main__":
    print(f"Starting server with model: {AGENT_MODEL_NAME}")
    # uvicorn.run("filename:FastAPI_instance_name", ...other_parameters)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)