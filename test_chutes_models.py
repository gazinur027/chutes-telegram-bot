import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_chutes_models():
    api_key = os.getenv("CHUTES_API_KEY")
    
    print(f"API Key: {api_key[:20]}...")
    
    # Пробуем разные модели
    models = [
        "deepseek-ai/DeepSeek-V3.2-TEE",
        "google/gemma-4-31B-turbo-TEE",
        "Qwen/Qwen2.5-72B-Instruct",
        "default",
    ]
    
    payload_base = {
        "messages": [{"role": "user", "content": "Привет, как дела?"}],
        "max_tokens": 100,
    }
    
    async with aiohttp.ClientSession() as session:
        for model in models:
            print(f"\n--- Testing model: {model} ---")
            payload = {**payload_base, "model": model}
            try:
                async with session.post(
                    "https://chutes.ai/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    print(f"Status: {resp.status}")
                    text = await resp.text()
                    print(f"Response: {text[:300]}")
            except Exception as e:
                print(f"Error: {str(e)[:200]}")

asyncio.run(test_chutes_models())
