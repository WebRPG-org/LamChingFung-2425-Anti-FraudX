from google import genai

# 初始化 Vertex AI 模式
client = genai.Client(
    vertexai=True,
    project="anti-fraudx",
    location="us-central1"
)

#####
response = client.models.generate_content(
    model='gemini-2.5-flash-lite',
    contents="請用一句話介紹你自己"
)
print(response.text)

# print("可用的 Gemini 模型：")
# for model in client.models.list():
#     print(f"  - {model.name}")