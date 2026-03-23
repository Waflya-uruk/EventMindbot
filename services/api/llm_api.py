import os
import re
import json
from gigachat import GigaChat


def get_json_promt(context: str):
    promt = f'''
    Сгенерируй JSON-объект, представляющий событие в календаре.
    Структура JSON должна строго содержать следующие поля:
    - title: строка (str), краткое название события.
    - description: строка (str), подробное описание.
    - start_time: строка в формате "YYYY-MM-DD HH:MM".
    - end_time: строка в формате "YYYY-MM-DD HH:MM".
    Контекст события: {context}
    Требования к ответу: Верни ТОЛЬКО чистый JSON без лишних пояснений, вводных слов и Markdown-разметки (просто текст).'''
    return promt

async def get_json_from_ai(event_description: str) -> str:
    async with GigaChat(credentials=os.getenv("GIGACHAT_TOKEN"), verify_ssl_certs=False) as giga:
        response = await giga.achat(event_description)
        return response.choices[0].message.content
    
def clean_and_parse_json(raw_text):
    try:
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)
        
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            print("❌ JSON не найден в ответе нейросети")
            return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга: {e}")
        return None
