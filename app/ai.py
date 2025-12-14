import requests
import json
import re

# === Данные YandexGPT ===
IAM_TOKEN = "t1.9euelZqUzJLKzp2SzIvLlJzPk8nKme3rnpWals-Pi5COkM2PyZPJkJrHj5Hl8_diBgU2-e90GEVb_t3z9yI1Ajb573QYRVv-zef1656Vmp6Sz8eeiYmSyY6bjpyXlc6V7_zF656Vmp6Sz8eeiYmSyY6bjpyXlc6V.IAOqkhF9PG98_-7KEisdBP-m_VlZIpv1D83rXCCjYzEXZWJlJWUPy_YeyzFKmMj3tB5-FLUP1MTUtaFZwRT1Cg"
FOLDER_ID = "b1gpr8douqjgn3bn9bab"

# === История сообщений ===
messages = [
    {
        "role": "system",
        "text": """
Ты — эксперт по IT-кейсам и техническим заданиям.

Твоя задача:
на основе входного описания кейса создать 4 РАЗНЫХ кейса для IT-специалистов.

ОБЯЗАТЕЛЬНЫЕ ТРЕБОВАНИЯ:
- Создай РОВНО 4 разных кейса
- Каждый кейс должен быть уникальным
- Используй JSON формат для ответа
- Каждый кейс должен иметь структуру:
{
  "title": "Название кейса",
  "level": "junior/middle/senior",
  "duration": "например, 2 недели",
  "short_description": "Краткое описание (3-5 предложений)",
  "full_description": "Полное описание со всей структурой"
}

СТРУКТУРА full_description:
## Общая информация
- **Сложность:** 
- **Уровень:** (junior / middle / senior)
- **Оценка времени:** 

## Описание задачи
Краткое описание задачи в 3–5 предложениях.

## Функциональные требования
- ...
- ...
- ...

## Технические требования
- Язык программирования
- Использование ООП
- Обработка ошибок
- Проверка корректности ввода

## Ожидаемый результат
Что именно должно уметь приложение после выполнения кейса.

ВАЖНО:
- Ответ должен быть ТОЛЬКО в формате JSON
- Не добавляй никакого текста кроме JSON
- Пример ответа:
{
  "cases": [
    {
      "title": "...",
      "level": "...",
      "duration": "...",
      "short_description": "...",
      "full_description": "..."
    },
    ...
  ]
}
"""
    }
]


def ask_agent(user_message):
    """
    Отправляет запрос к YandexGPT и получает ответ в формате JSON
    """
    # Добавляем сообщение пользователя
    messages.append({"role": "user", "text": f"Создай 4 кейса на основе: {user_message}"})

    # Подготовка запроса к YandexGPT
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": messages
    }

    headers = {
        "Authorization": f"Bearer {IAM_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        headers=headers,
        data=json.dumps(data)
    )

    result = response.json()
    answer_text = result["result"]["alternatives"][0]["message"]["text"]
    
    # Добавляем ответ модели в историю
    messages.append({"role": "assistant", "text": answer_text})

    # Пытаемся извлечь JSON из ответа
    try:
        # Ищем JSON в тексте (на случай, если модель добавила что-то кроме JSON)
        json_match = re.search(r'\{.*\}', answer_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            data = json.loads(json_str)
            return data
        else:
            # Если не нашли JSON, возвращаем пустую структуру
            return {"cases": []}
    except Exception as e:
        print(f"Ошибка парсинга JSON: {e}")
        print(f"Ответ ИИ: {answer_text}")
        return {"cases": []}