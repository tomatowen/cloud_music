import aiohttp

# 获取HTTP请求信息
async def fetch_info(url):
    headers = {'referer': url}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            return {
              'status': response.status,
              'url': str(response.url)
            }