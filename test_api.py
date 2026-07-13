import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_chutes():
    api_key = os.getenv("CHUTES_API_KEY")
    url = os.getenv("CHUTES_API_URL", "https://llm.chutes.ai/v1/chat/completions")
    model = os.getenv("MODEL_NAME", "default-model")
    
    print(f"API Key: {api_key[:20]}...")
    print(f"URL: {url}")
    print(f"Model: {model}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            print(f"Status: {resp.status}")
            text = await resp.text()
            print(f"Response: {text}")

asyncio.run(test_chutes())
