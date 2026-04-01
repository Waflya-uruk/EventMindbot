import os
from gigachat import GigaChat

async def ask_ai(question: str) -> str:
    async with GigaChat(credentials=os.getenv("GIGACHAT_TOKEN"), verify_ssl_certs=False) as giga:
        response = await giga.achat(question)
        return response.choices[0].message.content
