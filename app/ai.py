#
import requests
import json
import os
import time

GROQ_API_KEY = "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"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

if not GROQ_API_KEY:
    raise RuntimeError("❌ Не задан GROQ_API_KEY в переменных окружения")


SYSTEM_PROMPT = """Ты — генератор IT-кейсов.

СТРОГИЕ ПРАВИЛА:
1. Отвечай ТОЛЬКО валидным JSON
2. Никакого текста вне JSON
3. JSON должен быть полностью закрыт
4. Верни РОВНО 4 кейса
5. Каждый кейс ОБЯЗАН содержать:
   - title
   - level
   - duration
   - short_description
   - full_description
6. В full_description используй \\n для переносов строк

Формат ответа:
{
  "cases": [
    {
      "title": "",
      "level": "",
      "duration": "",
      "short_description": "",
      "full_description": ""
    }
  ]
}
"""


def ask_agent(topic, retries=2):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Создай 4 разных IT-кейса на тему: {topic}"}
    ]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    for attempt in range(retries + 1):
        try:
            response = requests.post(
                API_URL,
                headers=headers,
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": 2000
                },
                timeout=30
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )

            content = response.json()["choices"][0]["message"]["content"].strip()

            # ⛔ без regex — сразу JSON
            data = json.loads(content)

            if "cases" not in data or not isinstance(data["cases"], list):
                raise ValueError("Нет массива cases")

            if len(data["cases"]) != 4:
                raise ValueError("Должно быть ровно 4 кейса")

            valid_cases = []
            for case in data["cases"]:
                required = (
                    "title",
                    "level",
                    "duration",
                    "short_description",
                    "full_description"
                )

                if not all(k in case for k in required):
                    raise ValueError("Неполный кейс")

                case["full_description"] = case["full_description"].replace("\n", "\\n")
                valid_cases.append(case)

            return {"cases": valid_cases}

        except Exception as e:
            print(f"❌ Попытка {attempt + 1}: {e}")

            messages.append({
                "role": "user",
                "content": (
                    "Ты вернул невалидный JSON. "
                    "Исправь и верни ТОЛЬКО валидный JSON "
                    "в исходном формате."
                )
            })

            time.sleep(1)

    return {"cases": []}


if __name__ == "__main__":
    topic = "веб-приложения для мониторинга"
    print(f"🔹 Тема: {topic}")

    result = ask_agent(topic)

    print("\n" + "=" * 50)
    if result["cases"]:
        print(f"✅ Сгенерировано {len(result['cases'])} кейсов:\n")
        for i, case in enumerate(result["cases"], 1):
            print(f"{i}. {case['title']} ({case['level']}, {case['duration']})")
            print(f"   {case['short_description']}\n")
    else:
        print("❌ Кейсы не сгенерированы")
