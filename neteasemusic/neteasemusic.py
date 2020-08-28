import requests
from hoshino import Service
from aiocqhttp.message import MessageSegment

sv = Service('search_music', enable_on_default=True)

URL = 'http://music.163.com/api/search/get/web?csrf_token=hlpretag=&hlposttag=&type=1&offset=0&total=true&limit=3'


def query(keyword):
    requrl = f'{URL}&s={keyword}'
    try:
        with requests.get(requrl, timeout=20) as resp:
            res = resp.json()
            code = int(res['code'])
            if code != 200:
                return f'查询错误Code:{code}'
            songs = res['result']['songs']
            if len(songs) < 1:
                return f'没有查询到关于{keyword}的歌曲信息'
            id = songs[0]['id']
            return int(id)
    except Exception as ex:
        sv.logger.error(f'[query ERROR]:{ex}')
        return '查询异常...'


@sv.on_prefix('点歌')
async def diansong(bot, event):
    msg = event.message.extract_plain_text().strip()
    if not msg:
        await bot.send(event, '歌名都没有你点个锤子噢')
        return
    mid = query(msg)
    if isinstance(mid, int) is False:
        await bot.send(event, id)
        return
    music = MessageSegment.music(type_='163', id_=mid)
    sv.logger.info(f'{music}')
    await bot.send(event, music)
