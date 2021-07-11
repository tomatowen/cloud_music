import aiohttp

# 获取HTTP请求信息
async def fetch_info(url):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36 Edg/91.0.864.48',
        'referer': url
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            return {
              'status': response.status,
              'url': str(response.url)
            }