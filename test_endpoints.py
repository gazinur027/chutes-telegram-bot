import asyncio
import aiohttp

async def test_endpoints():
    urls = [
        "https://api.chutes.ai/v1/chat/completions",
        "https://llm.chutes.ai/v1/chat/completions",
        "https://chutes.ai/api/v1/chat/completions",
        "https://llm.chutes.ai/chat/completions",
        "https://chutes.ai/chat/completions",
    ]
    
    payload = {"messages": [{"role": "user", "content": "test"}]}
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            print(f"\n--- {url} ---")
            try:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    text = await resp.text()
                    if text.startswith('{'):
                        print(f"Status: {resp.status}")
                        print(f"Response: {text[:200]}")
                    else:
                        print(f"Status: {resp.status} (HTML)")
            except Exception as e:
                print(f"Error: {str(e)[:150]}")

asyncio.run(test_endpoints())
