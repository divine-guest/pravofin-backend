from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"message": "ПравоФин API работает с YandexGPT"}

@app.post("/generate")
async def generate_document(req: DocRequest):
    try:
        prompt = f"""
Тип документа: {req.docType}
Сторона 1: {req.party1}
Сторона 2: {req.party2}
Сумма: {req.amount} ₽
Срок: {req.term} дней

Составь договор. Используй официальный стиль.
"""

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": f"gpt://{FOLDER_ID}/yandexgpt",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": [
                {"role": "system", "text": "Ты юрист."},
                {"role": "user", "text": prompt}
            ]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()

        document = result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "Документ не сгенерирован")
        return {"document": document}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
