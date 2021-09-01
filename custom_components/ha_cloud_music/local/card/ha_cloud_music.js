window.ha_cloud_music = {
    media_player: null,
    recorder: null,
    eventQueue: {},
    get hass() {
        return document.querySelector('home-assistant').hass
    },
    get entity_id() {
        return 'media_player.yun_yin_le'
    },
    get entity() {
        try {
            return this.hass.states[this.entity_id]
        } catch {
            return null
        }
    },
    get version() {
        return this.entity.attributes.version
    },
    fetchApi(params) {
        return this.hass.fetchWithAuth('/ha_cloud_music-api', {
            method: 'POST',
            body: JSON.stringify(params)
        }).then(res => res.json())
    },
    initAudio() {
        if (document.querySelector('#ha_cloud_music-recorder')) return;
        const script = document.createElement('script')
        script.id = 'ha_cloud_music-recorder'
        script.src = 'https://cdn.jsdelivr.net/gh/shaonianzhentan/lovelace-voice-speak@master/dist/recorder.mp3.min.js'
        script.onload = () => {

        }
        document.body.appendChild(script)
    },
    startRecording() {
        const recorder = Recorder({ type: "mp3", sampleRate: 16000 });
        recorder.open(function () {
            // 开始录音
            recorder.start();
        }, function (msg, isUserNotAllow) {
            // 用户拒绝未授权或不支持
            console.log((isUserNotAllow ? "UserNotAllow，" : "") + "无法录音:" + msg);
            // 如果没有权限，则显示提示
            if (isUserNotAllow) {
                ha_cloud_music.toast('无法录音：' + msg)
            }
        });
        window.ha_cloud_music.recorder = recorder
    },
    stopRecording() {
        const { recorder, toast, hass } = window.ha_cloud_music
        recorder.stop(async (blob, duration) => {
            // 到达指定条件停止录音
            // console.log((window.URL || webkitURL).createObjectURL(blob), "时长:" + duration + "ms");
            recorder.close(); // 释放录音资源
            if (duration > 2000) {
                // 已经拿到blob文件对象想干嘛就干嘛：立即播放、上传
                let formData = new FormData()
                formData.append('mp3', blob)
                const res = await hass.fetchWithAuth('/ha_cloud_music-api', { method: 'PUT', body: formData }).then(res => res.json())
                toast(res.msg)
            } else {
                toast('当前录音时间没有2秒')
            }
        }, function (msg) {
            toast("录音失败:" + msg);
        });
    },
    callService(service_name, service_data = {}) {
        let arr = service_name.split('.')
        let domain = arr[0]
        let service = arr[1]
        this.hass.callService(domain, service, service_data)
    },
    // 媒体服务
    callMediaPlayerService(service_name, service_data = {}) {
        this.hass.callService('media_player', service_name, {
            entity_id: this.entity_id,
            ...service_data
        })
    },
    fire(type, data) {
        const event = new Event(type, {
            bubbles: true,
            cancelable: false,
            composed: true
        });
        event.detail = data;
        document.querySelector('home-assistant').dispatchEvent(event);
    },
    toast(message) {
        ha_cloud_music.fire("hass-notification", { message })
    },
    onmessage(type, data) {
        this.eventQueue[type](data)
    },
    addEventListener(type, func) {
        this.eventQueue[type] = func
    },
    async load(name) {
        if (Array.isArray(name)) {
            const arr = name.map(ele => {
                return this.load(ele)
            })
            return Promise.all(arr)
        }
        const tagName = `ha_cloud_music-${name}`
        const result = await import(`./${tagName}.js?ver=${this.version}`)
        return {
            tagName,
            result
        }
    }
};

(() => {
    const timer = setInterval(() => {
        if (!ha_cloud_music.entity) return
        clearInterval(timer)
        // 加载模块
        ha_cloud_music.load('player')
        ha_cloud_music.load('tabs').then(async () => {
            await ha_cloud_music.load(['playlist', 'lovelist', 'search', 'setting', 'voice', 'fmlist', 'version'])
            ha_cloud_music.load('panel')
        })
    }, 2000)
})();

