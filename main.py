from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ТВОИ ДАННЫЕ
FOLDER_ID = "b1gr9700dkd6c3qr8cte"
API_KEY = "aje1tflhh48g4v3r58j9"

class DocRequest(BaseModel):
    docType: str
    party1: str
    party2: str
    amount: str
    term: str

@app.get("/")
def root():
    return {"message": "ПравоФин API работает"}

@app.post("/generate")
async def generate_document(req: DocRequest):
    try:
        # 1. Формируем простой промпт
        prompt = f"Составь договор {req.docType} между {req.party1} и {req.party2} на сумму {req.amount} ₽ со сроком {req.term} дней."

        # 2. Готовим запрос к YandexGPT
        headers = {
            "Authorization": f"Api-Key {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.1,
                "maxTokens": 500
            },
            "messages": [
                {"role": "user", "text": prompt}
            ]
        }

        # 3. Отправляем запрос
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()

        # 4. Извлекаем текст
        document = result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "Документ не сгенерирован")
        return {"document": document}

    except httpx.HTTPStatusError as e:
        # Логируем ошибку от YandexGPT
        raise HTTPException(status_code=e.response.status_code, detail=f"Ошибка YandexGPT: {e.response.text}")
    except Exception as e:
        # Логируем любую другую ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
