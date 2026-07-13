import asyncio
import aiohttp

async def test_urls():
    urls = [
        'https://chutes.ai/v1/chat/completions',
        'https://llm.chutes.ai/v1/chat/completions',
        'https://api.chutes.ai/v1/chat/completions',
        'https://chutes.ai/api/v1/chat/completions',
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    print(f'{url} -> {resp.status}')
            except Exception as e:
                print(f'{url} -> Error: {e}')

asyncio.run(test_urls())
