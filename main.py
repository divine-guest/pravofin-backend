from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import uvicorn
import os
from typing import Optional

app = FastAPI(title="ПравоФин API", version="1.0")

# === РАЗРЕШАЕМ ЗАПРОСЫ С ЛЮБОГО САЙТА ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ТВОИ ДАННЫЕ YANDEX ===
# Вставь свои данные сюда или используй переменные окружения (рекомендую)
FOLDER_ID = "b1gr9700dkd6c3qr8cte"
API_KEY = "aje1tflhh48g4v3r58j9"

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

# === МОДЕЛИ ДЛЯ ЗАПРОСОВ ===
class DocRequest(BaseModel):
    docType: str
    party1: str
    party2: str
    amount: str
    term: str

class AnalyzeRequest(BaseModel):
    text: str

class TaxRequest(BaseModel):
    income: float
    expenses: float
    employees: int

class ChecklistRequest(BaseModel):
    goal: str

# === ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ YANDEXGPT ===
async def call_yandex_gpt(prompt: str, system_prompt: str = "Ты — профессиональный юрист и финансовый консультант.") -> str:
    """Отправляет запрос к YandexGPT и возвращает ответ."""
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
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": prompt}
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(YANDEX_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем текст ответа
            return result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "Ошибка: ответ не получен")
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Ошибка YandexGPT: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

# ================================================================
# === ЭНДПОИНТЫ ===
# ================================================================

@app.get("/")
def root():
    return {"message": "ПравоФин API работает на YandexGPT", "status": "ok", "version": "1.0"}

# === 1. ГЕНЕРАЦИЯ ДОКУМЕНТОВ ===
@app.post("/generate")
async def generate_document(req: DocRequest):
    prompt = f"""
Тип документа: {req.docType}
Сторона 1: {req.party1}
Сторона 2: {req.party2}
Сумма: {req.amount} ₽
Срок выполнения: {req.term} дней

Составь полный текст документа на основе данных выше. 
Используй официально-деловой стиль. Включи все необходимые реквизиты: дату, место, стороны, предмет, сроки, ответственность, подписи.
"""
    
    document = await call_yandex_gpt(prompt, "Ты — профессиональный юрист. Составляешь юридические документы.")
    return {"document": document}

# === 2. АНАЛИЗ ДОГОВОРА ===
@app.post("/analyze")
async def analyze_contract(req: AnalyzeRequest):
    prompt = f"""
Проанализируй следующий договор и выдели риски:

--- НАЧАЛО ДОГОВОРА ---
{req.text}
--- КОНЕЦ ДОГОВОРА ---

Выведи:
1. Основные риски (3-5 пунктов)
2. Рекомендации по исправлению
3. Оценку общей опасности (Низкий / Средний / Высокий риск)
"""
    
    analysis = await call_yandex_gpt(prompt, "Ты — эксперт по юридическому анализу договоров.")
    return {"analysis": analysis}

# === 3. НАЛОГОВЫЙ ПОМОЩНИК ===
@app.post("/tax")
async def tax_helper(req: TaxRequest):
    # Сначала считаем базовые цифры
    usn1 = req.income * 0.06
    usn2 = (req.income - req.expenses) * 0.15
    
    if req.expenses >= req.income:
        usn2 = 0
    
    # Формируем промпт для AI
    prompt = f"""
Доход: {req.income} ₽
Расходы: {req.expenses} ₽
Сотрудников: {req.employees}

Рассчитал:
- УСН "Доходы" (6%): {usn1:.2f} ₽
- УСН "Доходы минус расходы" (15%): {usn2:.2f} ₽

Напиши краткую рекомендацию: какой режим выгоднее в этой ситуации и почему. Дай совет по оптимизации налогов.
"""
    
    advice = await call_yandex_gpt(prompt, "Ты — налоговый консультант. Даёшь чёткие рекомендации.")
    
    # Добавляем расчёты к ответу AI
    return {
        "tax_advice": f"""
📊 Налоговый расчёт

Доход: {req.income:.2f} ₽
Расходы: {req.expenses:.2f} ₽
Сотрудников: {req.employees}

📌 УСН "Доходы" (6%): {usn1:.2f} ₽
📌 УСН "Доходы минус расходы" (15%): {usn2:.2f} ₽

🧠 Рекомендация AI:
{advice}
"""
    }

# === 4. ГЕНЕРАЦИЯ ЧЕК-ЛИСТА ===
@app.post("/checklist")
async def generate_checklist(req: ChecklistRequest):
    prompt = f"""
Создай пошаговый чек-лист для задачи: "{req.goal}"

Каждый шаг должен быть конкретным действием. Всего 5-8 шагов.
Добавь краткое пояснение к каждому шагу.
"""
    
    checklist = await call_yandex_gpt(prompt, "Ты — бизнес-консультант. Составляешь чёткие пошаговые инструкции.")
    return {"checklist": checklist}

# === ЗАПУСК ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)