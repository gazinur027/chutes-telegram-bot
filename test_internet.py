import asyncio
import aiohttp

async def test_internet():
    urls = [
        'https://google.com',
        'https://github.com',
        'https://api.groq.com',
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    print(f'{url} -> {resp.status}')
            except Exception as e:
                print(f'{url} -> Error: {str(e)[:100]}')

asyncio.run(test_internet())
