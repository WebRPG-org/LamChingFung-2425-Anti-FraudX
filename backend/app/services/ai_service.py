import os
import google.generativeai as genai
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("錯誤：找不到 GOOGLE_API_KEY 環境變數。請檢查您的 .env 檔案。")

genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-2.5-flash-lite')


def generate_transport_suggestion(user_query: str, context_data: list):
    # 這是核心的 Prompt Engineering
    prompt = f"""
    你是一個專業的香港交通顧問。請根據以下提供的香港巴士路線資料，跟據用戶輸入的語言(中文繁體 / 中文简体 / English)回答使用者的問題。
    你的回答應該清晰、簡潔，並優先使用我提供的資料。如果資料不足，請誠實地說你無法提供準確建議。

    [巴士路線資料]
    {context_data}

    [使用者問題]
    {user_query}

    [你的建議]
    """

    response = model.generate_content(prompt)
    return response.text