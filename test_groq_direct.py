import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_groq_direct():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY не найден!")
        return
    
    print(f"API Key: {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-specdec",
        "messages": [{"role": "user", "content": "Привет, как дела?"}],
        "max_tokens": 100,
    }
    
    async with aiohttp.ClientSession() as session:
        url = "https://api.groq.com/openai/v1/chat/completions"
        print(f"\nTesting Groq: {url}")
        try:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"Status: {resp.status}")
                text = await resp.text()
                print(f"Response: {text[:500]}")
        except Exception as e:
            print(f"Error: {str(e)[:500]}")

asyncio.run(test_groq_direct())
