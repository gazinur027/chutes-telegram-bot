import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY не найден!")
        return
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = os.getenv("MODEL_NAME", "llama-3.3-70b-specdec")
    
    print(f"API Key: {api_key[:20]}...")
    print(f"URL: {url}")
    print(f"Model: {model}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Привет, как дела?"}],
        "max_tokens": 100,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")

asyncio.run(test_groq())
