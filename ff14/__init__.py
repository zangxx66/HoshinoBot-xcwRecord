from hoshino import Service
from nonebot import MessageSegment


sv = Service('ff14', enable_on_default=True)
from .fishtool import Fish
fish = Fish()
help_text = '''
ff14钓鱼笔记帮助指北
(钓鱼笔记|钓鱼日记)+需查询的鱼的名字
钓鱼区域+地图名称
'''.strip()


@sv.on_prefix(('钓鱼笔记', '钓鱼日记'))
async def diaoyu(bot, event):
    uid = event.user_id
    msg = event.message.extract_plain_text().strip()
    if not msg:
        await bot.finish(event, help_text)
    result = fish.search_fish(msg)
    if result is None:
        await bot.send(event, '没有查询到结果呢，输入有误或者数据未收录', at_sender=True)
    else:
        at = MessageSegment.at(uid)
        reply = f'已为{at}找到如下结果：\n{result}'
        await bot.send(event, reply)


@sv.on_prefix('钓鱼区域')
async def area(bot, event):
    uid = event.user_id
    msg = event.message.extract_plain_text().strip()
    if not msg:
        await bot.finish(event, help_text)
    result = fish.search_area(msg)
    if result is None:
        await bot.send(event, '所选区域有误', at_sender=True)
    else:
        at = MessageSegment.at(uid)
        reply = f'已为{at}找到如下结果：\n{result}'
        await bot.send(event, reply)
