"""Support for media browsing."""
import logging, os
from homeassistant.helpers.network import get_url
from homeassistant.components.media_player import BrowseError, BrowseMedia
from homeassistant.components.media_player import MediaType
from homeassistant.components.media_player import MediaClass

PLAYABLE_MEDIA_TYPES = [
    MediaType.ALBUM,
    MediaType.ARTIST,
    MediaType.TRACK,
]

CONTAINER_TYPES_SPECIFIC_MEDIA_CLASS = {
    MediaType.ALBUM: MediaClass.ALBUM,
    MediaType.ARTIST: MediaClass.ARTIST,
    MediaType.PLAYLIST: MediaClass.PLAYLIST,
    MediaType.SEASON: MediaClass.SEASON,
    MediaType.TVSHOW: MediaClass.TV_SHOW,
}

CHILD_TYPE_MEDIA_CLASS = {
    MediaType.SEASON: MediaClass.SEASON,
    MediaType.ALBUM: MediaClass.ALBUM,
    MediaType.ARTIST: MediaClass.ARTIST,
    MediaType.MOVIE: MediaClass.MOVIE,
    MediaType.PLAYLIST: MediaClass.PLAYLIST,
    MediaType.TRACK: MediaClass.TRACK,
    MediaType.TVSHOW: MediaClass.TV_SHOW,
    MediaType.CHANNEL: MediaClass.CHANNEL,
    MediaType.EPISODE: MediaClass.EPISODE,
}

_LOGGER = logging.getLogger(__name__)


class UnknownMediaType(BrowseError):
    """Unknown media type."""


async def build_item_response(media_library, payload):
    """Create response payload for the provided media query."""
    # print(payload)
    search_id = payload["search_id"]
    search_type = payload["search_type"]
    hass = media_library._hass
    thumbnail = None
    title = None
    media = None    
    media_class = MediaClass.DIRECTORY
    can_play = False
    can_expand = True
    children = []
    base_url = get_url(hass)
    is_library = 'library_' in search_type

    properties = ["thumbnail"]
    if is_library:
        # 读取配置目录
        path = hass.config.path("media/ha_cloud_music")        
        # 获取所有文件
        music_list = media_library.api_music.get_local_media_list(search_type)
        for item in music_list:
            children.append(item_payload({
                    "label": item['name'], "type": 'music', "songid": item['url']
                }, media_library))

        title = search_type.replace('library_', '')
        media_class = MediaClass.MUSIC
        can_play = True
        can_expand = False

    response = BrowseMedia(
        media_class=media_class,
        media_content_id=search_id,
        media_content_type=search_type,
        title=title,
        can_play=can_play,
        can_expand=can_expand,
        children=children,
        thumbnail=thumbnail,
    )

    if is_library:
        response.children_media_class = MediaClass.MUSIC
    else:
        response.calculate_children_class()

    return response


def item_payload(item, media_library):
    # print(item)
    title = item["label"]
    media_class = None
    media_content_type = item["type"]

    if "songid" in item:
        # 音乐
        media_class = MediaClass.MUSIC
        media_content_id = f"{item['songid']}"
        can_play = True
        can_expand = False
    else:
        # 目录
        media_class = MediaClass.DIRECTORY       
        media_content_id = ""
        can_play = False
        can_expand = True

    return BrowseMedia(
        title=title,
        media_class=media_class,
        media_content_type=media_content_type,
        media_content_id=media_content_id,
        can_play=can_play,
        can_expand=can_expand
    )


def library_payload(media_library):
    """
    创建音乐库
    """
    library_info = BrowseMedia(
        media_class=MediaClass.DIRECTORY,
        media_content_id="library",
        media_content_type="library",
        title="Media Library",
        can_play=False,
        can_expand=True,
        children=[],
    )
    # 默认列表
    library_info.children.append(
            item_payload(
                {"label": "默认列表", "type": "library_music"},
                media_library,
            )
        )
    # 读取文件夹
    path = media_library._hass.config.path("media/ha_cloud_music")
    for filename in os.listdir(path):
        if os.path.isdir(os.path.join(path, filename)):
            library_info.children.append(
                item_payload(
                    {"label": filename, "type": f"library_{filename}"},
                    media_library,
                )
            )
    return library_info
