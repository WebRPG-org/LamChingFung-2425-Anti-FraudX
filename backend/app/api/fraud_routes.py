from fastapi import APIRouter
from .schemas import FraudCheckRequest, FraudCheckResponse
from ..fraud_detect import checker
from pydantic import BaseModel
from ..ai_service import generate_response

router = APIRouter()

@router.post(
    "/fraud-check/entity", 
    response_model=FraudCheckResponse, 
    tags=["Fraud Detect"]
)
async def fraud_check_entity(request: FraudCheckRequest):
    result = await checker.check_entity(request.entity_name)
    return result

class FraudCheckTextRequest(BaseModel):
    text_content: str

@router.post("/fraud-check/text", tags=["Fraud Detection"])
def fraud_check_text(request: FraudCheckTextRequest):
    """
    接收文本塊，並利用 AI 模型分析其詐騙風險。
    """
    # 1. here assemble the complete prompt
    prompt_template = f"""
    你是一個專注於香港金融市場的詐騙分析專家...
    
    使用者提供的文本如下：
    ---
    {request.text_content}
    ---
    請開始你的分析。
    """

    # 2. call the AI service to analyze the text
    analysis_result = generate_response(prompt=prompt_template)
    
    # 3. process the response from AI service
    if "error" in analysis_result:
        # if error, return unknown risk level
        return {"risk_level": "UNKNOWN", "message": analysis_result["error"]}
    
    # if success, parse the AI response (assuming it's JSON formatted)
    # ...
    
    return {"ai_analysis": analysis_result["response"]}