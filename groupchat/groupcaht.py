import random
import os

from nonebot import MessageSegment
import hoshino
from hoshino import R, Service, priv, util
from nonebot import NoticeSession


sv = Service('groupchat', enable_on_default=True)


@sv.on_fullmatch('迫害龙王')
async def who_is_longwang(bot, ev):
    gid = ev.group_id
    img_path = R.img('longwang/').path
    data = await bot.get_group_honor_info(group_id=gid, type='talkative')
    talkative = data['current_talkative']
    uid = talkative['user_id']
    files = os.listdir(img_path)
    filename = random.choice(files)
    img = R.img('longwang/', filename)
    at = MessageSegment.at(uid)
    msg = f'{at}\n{img.cqcode}'
    await bot.send(ev, msg)


@sv.on_notice('notify')
async def new_longwang(session: NoticeSession):
    if session.event['sub_type'] == 'honor' and session.event['honor_type'] == 'talkative':
        uid = session.event['user_id']
        at = MessageSegment.at(uid)
        msg = f'新的龙王已经出现{at}'
        await session.send(msg)


@sv.on_prefix('设置管理员')
async def set_admin(bot, event):
    gid = event.group_id
    u_priv = priv.get_user_priv(event)
    if u_priv >= sv.manage_priv:
        for m in event.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                user = int(m.data['qq'])
                await bot.set_group_admin(group_id=gid, user_id=user, enable=True)
        await bot.send(event, '我好了')
    else:
        await bot.send(event, '才不听你的呢')


@sv.on_prefix('取消管理员')
async def unset_admin(bot, event):
    gid = event.group_id
    u_priv = priv.get_user_priv(event)
    if u_priv >= sv.manage_priv:
        for m in event.message:
            if m.type == 'at' and m.data['qq'] != 'all':
                user = int(m.data['qq'])
                await bot.set_group_admin(group_id=gid, user_id=user, enable=False)
        await bot.send(event, '我好了')
    else:
        await bot.send(event, '才不听你的呢')


@sv.on_prefix('设置群名')
async def set_group_name(bot, event):
    gid = event.group_id
    name = event.message.extract_plain_text().strip()
    if not name:
        await bot.finish(event, '群名都没有的你设置个锤子')
    u_priv = priv.get_user_priv(event)
    if u_priv >= sv.manage_priv:
        await bot.set_group_name(group_id=gid, group_name=name)
        await bot.send(event, '我好了')
    else:
        await bot.send(event, '才不听你的呢')


@sv.on_prefix('戳一戳')
async def send_poke(bot, event):
    msg = event.message
    for m in msg:
        if m.type == 'at' and m.data['qq'] != 'all':
            u = int(m.data['qq'])
            if u != event.self_id:
                poke_other = MessageSegment(type_='poke', data={'qq': u})
                await bot.send(event, poke_other)


@sv.on_notice('notify')
async def get_poke(session: NoticeSession):
    event = session.event
    if event['sub_type'] == 'poke' and event['self_id'] == event['target_id']:
        send_id = event['user_id']
        poke = MessageSegment(type_='poke', data={'qq': send_id})
        await session.send(poke)


@sv.on_prefix('申请头衔')
async def set_group_title(bot, ctx):
    msg = ctx.message.extract_plain_text().strip()
    group = ctx.group_id
    uid = ctx.user_id
    try:
        await bot.set_group_special_title(group_id=group, user_id=uid, special_title=msg, duration=-1)
        await bot.send(ctx, f'申请头衔{msg}成功')
    except Exception as ex:
        sv.logger.exception(ex)
        await bot.send(ctx, f'申请头衔{msg}失败了')
