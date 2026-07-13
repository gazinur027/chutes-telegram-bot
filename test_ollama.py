import asyncio
import aiohttp

async def test_ollama():
    url = "http://localhost:8000/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Qwen/Qwen3-8B",
        "messages": [{"role": "user", "content": "Привет"}],
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                print(f"Status: {resp.status}")
                text = await resp.text()
                print(f"Response: {text[:500]}")
    except Exception as e:
        print(f"Error: {str(e)[:500]}")

asyncio.run(test_ollama())
