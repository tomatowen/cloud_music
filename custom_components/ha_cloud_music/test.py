import asyncio
import tempfile, shutil
import edgeTTS

async def main():
    communicate = edgeTTS.Communicate()
    lang = 'zh-CN'
    voice = 'zh-CN-XiaoxiaoNeural'
    message = '测试一下'
    xml = '<speak version="1.0"' \
              ' xmlns="http://www.w3.org/2001/10/synthesis"' \
              ' xmlns:mstts="https://www.w3.org/2001/mstts"' \
              f' xml:lang="{lang}">' \
              f'<voice name="{voice}">' \
              f'{message}</voice></speak>'
    with open('test.mp3', 'wb') as fp:
        async for i in communicate.run(xml, customspeak=True):
            if i[2] is not None:
                fp.write(i[2])
        print(fp.name)

if __name__ == "__main__":
    asyncio.run(main())