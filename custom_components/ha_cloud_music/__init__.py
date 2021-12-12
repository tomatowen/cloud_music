async def async_setup_entry(hass, config_entry):
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, "media_player"))
    return True

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, PLATFORMS, NAME, ICON, DOMAIN, ROOT_PATH, VERSION

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def update_listener(hass, entry):
    """Handle options update."""
    config = entry.options
    mp = hass.data[DOMAIN]
    mp.api_tts.tts_before_message = config.get('tts_before_message', '')
    mp.api_tts.tts_after_message = config.get('tts_after_message', '')
    mp.api_music.find_api_url = config.get('find_api_url', '')
    mp.api_music.user = config.get('user', '')
    mp.api_music.password = config.get('password', '')
    def login_callback(uid):
        hass.components.frontend.async_remove_panel(DOMAIN)
        # 注册菜单栏
        hass.components.frontend.async_register_built_in_panel(
            "iframe", NAME, ICON, DOMAIN,
            { "url": ROOT_PATH + "/index.html?ver=" + VERSION + "&show_mode=default&uid=" + uid },
            require_admin=False
        )
    # 开始登录
    if mp.api_music.user != '' and mp.api_music.password != '':
        await mp.api_music.login(login_callback)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)