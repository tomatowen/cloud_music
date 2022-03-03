import os, hashlib, asyncio, threading, time, json, urllib, mutagen
try:
    from edge_tts import Communicate
except (ImportError, ModuleNotFoundError):
    from edgeTTS import Communicate
from mutagen.mp3 import MP3
from homeassistant.helpers.network import get_url
from homeassistant.helpers import template
from homeassistant.const import (STATE_PLAYING)

class ApiTTS():
    def __init__(self, media, cfg):
        self.hass = media._hass
        self.media = media
        self.media_position = None
        self.media_url = None
        self.thread = None        
        self.tts_before_message = cfg['tts_before_message']
        self.tts_after_message = cfg['tts_after_message']
        tts_mode = cfg['tts_mode']        
        if [1, 2, 3, 4].count(tts_mode) == 0:
            tts_mode = 4
        tts_volume = 0
        tts_config = media.api_config.get_tts()
        if tts_config is not None:
            tts_mode = tts_config.get('mode', 4)
            tts_volume = tts_config.get('volume', 0)
        # TTS声音模式
        self.tts_mode = tts_mode
        # TTS音量
        self.tts_volume = tts_volume
    
    def log(self, name,value):
        self.media.log('【文本转语音】%s：%s',name,value)

    # 异步进行TTS逻辑
    def async_tts(self, text):
        # 如果当前正在播放，则暂停当前播放，保存当前播放进度
        if self.media._media_player != None and self.media.state == STATE_PLAYING:
           self.media.media_pause()
           self.media_position = self.media.media_position
           self.media_url = self.media.media_url
        # 播放当前文字内容
        self.play_url(text)
        # 恢复当前播放到保存的进度
        if self.media_url is not None:
            self.log('恢复当前播放URL', self.media_url)
            #self.media._media_player.load(self.media_url)
            #time.sleep(2)
            self.log('恢复当前进度', self.media_position)            
            #self.media._media_player.seek(self.media_position)
            #self.media._media_player.play()
            self.media._media_player.reloadURL(self.media_url, self.media_position)
            self.media_url = None

    # 获取语音URL
    def play_url(self, text):
        # 如果传入的是链接
        if text.find('voice-') == 0:
            f_name = text
        else:
            # 生成文件名
            f_name = 'tts-' + self.media.api_config.md5(text + str(self.tts_mode)) + ".mp3"
        # 创建目录名称
        _dir =  self.hass.config.path("tts")
        self.media.api_config.mkdir(_dir)
        # 生成缓存文件名称
        ob_name = _dir + '/' + f_name
        self.log('本地文件路径', ob_name)
        # 文件不存在，则获取下载
        if os.path.isfile(ob_name) == False:
            voice_list = ['zh-CN-XiaomoNeural', 'zh-CN-XiaoxuanNeural', 'zh-CN-XiaohanNeural', 'zh-CN-XiaoxiaoNeural']
            voice = voice_list[self.tts_mode - 1]
            asyncio.run(self.write_tts_file(ob_name, voice, text))
            time.sleep(2)
        else:
            # 如果没有下载，则延时1秒
            time.sleep(1)
        # 生成播放地址
        local_url = get_url(self.hass).strip('/') + '/tts-local/' + f_name
        self.log('本地URL', local_url)

        if self.media._media_player != None:
            self.media._media_player.is_tts = True
            # 保存当前音量
            volume_level = self.media.volume_level
            # 如果设置的TTS音量不为0，则改变音量
            if self.tts_volume > 0:
                print('设置TTS音量：%s'%(self.tts_volume))
                self.media._media_player.set_volume_level(self.tts_volume / 100)
            # 保存播放速度
            rate = self.media._media_player.rate
            # 播放TTS链接
            self.media._media_player.load(local_url)
            # 计算当前文件时长，设置超时播放时间
            audio = MP3(ob_name)
            self.log('音频时长', audio.info.length)
            time.sleep(audio.info.length + 3)
            self.media._media_player.is_tts = False
            # 恢复播放速度
            self.media._media_player.set_rate(rate)
            # 恢复音量
            print('恢复音量：%s'%(volume_level))
            self.media._media_player.set_volume_level(volume_level)            

    # 获取TTS文件
    async def write_tts_file(self, ob_name, voice, text):
        communicate = Communicate()
        lang = 'zh-CN'
        message = text
        xml = '<speak version="1.0"' \
                ' xmlns="http://www.w3.org/2001/10/synthesis"' \
                ' xmlns:mstts="https://www.w3.org/2001/mstts"' \
                f' xml:lang="{lang}">' \
                f'<voice name="{voice}">' \
                f'{message}</voice></speak>'
        with open(ob_name, 'wb') as fp:
            async for i in communicate.run(xml, customspeak=True):
                if i[2] is not None:
                    fp.write(i[2])
        
        # 修改MP3文件属性
        meta = mutagen.File(ob_name, easy=True)
        meta['title'] = text
        meta.save()
        return fp.name

    async def speak(self, call):
        try:
            if isinstance(call, str):
                text = call
            else:
                text = call.data.get('text', '')
                if text == '':
                    # 解析模板
                    tpl = template.Template(call.data['message'], self.hass)
                    text = self.tts_before_message + tpl.async_render(None) + self.tts_after_message

            self.log('解析后的内容', text)
            if self.thread != None:
                self.thread.join()

            self.thread = threading.Thread(target=self.async_tts, args=(text,))
            self.thread.start()
        except Exception as ex:
            self.log('出现异常', ex)