import requests
import json
import re

OPENROUTER_API_KEY = "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"
MODEL = "meta-llama/llama-3-8b-instruct"  # ← ЭТА МОДЕЛЬ ТОЧНО РАБОТАЕТ

system_prompt = """
Ты — эксперт по IT-кейсам и техническим заданиям.

Создай РОВНО 4 РАЗНЫХ кейса по входному описанию.

ВАЖНО:
- Выведи ТОЛЬКО валидный JSON, без пояснений, без ```json```, без текста до/после.
- Значение поля "full_description" должно быть СТРОКОЙ, содержащей весь текст кейса.
- Внутри "full_description" можно использовать markdown (##, **...**), переносы строк (\\n), но ВСЁ ЭТО — ОДНА СТРОКА в JSON.
- Не создавай вложенные JSON-объекты внутри "full_description".

Пример КОРРЕКТНОГО фрагмента:
{
  "title": "Кейс про калькулятор",
  "level": "junior",
  "duration": "1 неделя",
  "short_description": "Сделать консольный калькулятор",
  "full_description": "## Общая информация\\n- **Сложность:** junior\\n- **Оценка времени:** 1 неделя\\n\\n## Описание задачи\\nНужно реализовать калькулятор..."
}

Твоя задача — сгенерировать 4 таких кейса в формате:
{
  "cases": [
    { "title": "...", "level": "...", "duration": "...", "short_description": "...", "full_description": "..." },
    ...
  ]
}

НЕ ДОБАВЛЯЙ НИЧЕГО КРОМЕ ВАЛИДНОГО JSON.
"""

def ask_agent(user_message):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Создай 4 кейса на основе: {user_message}"}
    ]

    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2500
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=45  # даём время на генерацию
        )
    except requests.Timeout:
        print("Таймаут: модель слишком долго отвечает")
        return {"cases": []}

    if response.status_code != 200:
        print(f"Ошибка OpenRouter: {response.status_code} — {response.text}")
        return {"cases": []}

    try:
        answer_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Ошибка извлечения ответа: {e}")
        return {"cases": []}

    # Очистка от ```json ... ```
    cleaned = re.sub(r'^```(?:json)?\s*', '', answer_text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*```$', '', cleaned)

    try:
        # Извлекаем JSON
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        else:
            print("JSON не найден в ответе")
            return {"cases": []}
    except Exception as e:
        print(f"Ошибка парсинга JSON: {e}")
        print("Ответ:", answer_text)
        return {"cases": []}

# Тест
if __name__ == "__main__":
    result = ask_agent("Консольное приложение для управления задачами (To-Do list)")
    print(json.dumps(result, ensure_ascii=False, indent=2))



