from fastapi import FastAPI
from .services import transport_service, ai_service
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware # Added for CORS

load_dotenv()

app = FastAPI(title="AI-Agent")

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],    #allow all HTTP methods
    allow_headers=["*"],    #allow all headers
)



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
    
    user_keyword = chat_query.query
    relevant_routes = [
        route for route in all_routes 
        if user_keyword in (route.orig_tc or "") or user_keyword in (route.dest_tc or "")
    ]

    print(f"根據關鍵字 '{user_keyword}' 篩選出 {len(relevant_routes)} 條相關路線。")
    if not relevant_routes:
        target_routes_for_ai = all_routes[:100] 
    else:
        target_routes_for_ai = relevant_routes
    
    #translate text for ai service (default in Traditional Chinese)
    context_text = transport_service.translate_text_for_ai(target_routes_for_ai, lang='tc')

    #call ai service to get suggestion
    suggestion = ai_service.generate_transport_suggestion(
    user_query=chat_query.query,
    context_data=context_text
    )
    
    return {"response": suggestion} #return AI response (suggestion)