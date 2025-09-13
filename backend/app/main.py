from fastapi import FastAPI
from .services import transport_service, ai_service
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="AI-Agent")

@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/transport/bus-routes", tags=["Transport"])
def list_bus_routes():
    routes = transport_service.get_all_bus_routes()
    return {"routes": routes}

class ChatQuery(BaseModel):
    query: str

@app.post("/api/v1/chat", tags=["AI"])
def chat_with_ai(chat_query: ChatQuery):
    #get and validate all route data (from cache or API)
    all_routes = transport_service.get_all_bus_routes()
    
    if not all_routes:
        return {"response": "對不起，我暫時無法獲取交通數據，請稍後再試。"}
    
    #translate text for ai service (default in Traditional Chinese)
    #for MVP demo purpose, only use first 100 routes , refine this part in future !!
    context_text = transport_service.transform_routes_to_text(all_routes[:100], lang='tc')

    #call ai service to get suggestion
    suggestion = ai_service.generate_transport_suggestion(
        user_query=chat_query.query,
        context_text=context_text
    )
    
    return {"response": suggestion} #return AI response (suggestion)