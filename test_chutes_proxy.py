import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_chutes_with_proxy():
    api_key = os.getenv("CHUTES_API_KEY")
    proxy_url = os.getenv("PROXY_URL", "http://127.0.0.1:12334")
    
    print(f"Proxy: {proxy_url}")
    print(f"API Key: {api_key[:20]}...")
    
    # Пробуем разные URL
    urls = [
        "https://llm.chutes.ai/v1/chat/completions",
        "https://chutes.ai/v1/chat/completions",
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            print(f"\nTesting: {url}")
            try:
                async with session.post(url, json=payload, headers=headers, proxy=proxy_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    print(f"Status: {resp.status}")
                    text = await resp.text()
                    print(f"Response: {text[:200]}")
            except Exception as e:
                print(f"Error: {str(e)[:200]}")

asyncio.run(test_chutes_with_proxy())
