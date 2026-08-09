from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn
import os

app = FastAPI(title="ПравоФин API", version="1.0")

# === РАЗРЕШАЕМ ЗАПРОСЫ С ЛЮБОГО САЙТА ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ТВОИ ДАННЫЕ ===
FOLDER_ID = "b1gr9700dkd6c3qr8cte"
API_KEY = "aje1tflhh48g4v3r58j9"

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# === МОДЕЛЬ ===
class DocRequest(BaseModel):
    docType: str
    party1: str
    party2: str
    amount: str
    term: str

# === КОРЕНЬ ===
@app.get("/")
def root():
    return {"message": "ПравоФин API работает", "status": "ok"}

# === ГЕНЕРАЦИЯ ДОКУМЕНТА ===
@app.post("/generate")
async def generate_document(req: DocRequest):
    try:
        prompt = f"""
Тип документа: {req.docType}
Сторона 1: {req.party1}
Сторона 2: {req.party2}
Сумма: {req.amount} ₽
Срок выполнения: {req.term} дней

Составь полный текст документа на основе данных выше. 
Используй официально-деловой стиль.
"""
        
        headers = {
            "Authorization": f"Api-Key {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": [
                {"role": "system", "text": "Ты — профессиональный юрист."},
                {"role": "user", "text": prompt}
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(YANDEX_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

        document = result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "Документ не сгенерирован")

        return {"document": document}

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Ошибка YandexGPT: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

# === ЗАПУСК ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
