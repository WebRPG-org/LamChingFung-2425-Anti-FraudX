from pydantic import BaseModel
from typing import Optional, Dict , List

# used for fraud detection requests and responses
class FraudCheckRequest(BaseModel):
    entity_name: str

class FraudCheckResponse(BaseModel):
    risk_level: str
    message: str
    details: Optional[List[Dict]] = None

# used for triggering async tasks response
class TaskResponse(BaseModel):
    message: str
    task_id: str