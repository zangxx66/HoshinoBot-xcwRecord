import random
import os
import requests
import math
import re
import subprocess
import time

from nonebot import MessageSegment
import hoshino
from hoshino import R, Service, priv, util, Thread
from nonebot import NoticeSession


sv = Service('groupchat', enable_on_default=True)
lmt = util.DailyNumberLimiter(5)


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
        gid = session.event['group_id']
        at = MessageSegment.at(uid)
        bot = hoshino.get_bot()
        data = await bot.get_group_honor_info(group_id=gid, type='talkative')
        current_talkactive = data['current_talkative']
        day = current_talkactive['day_count']
        msg = f'新的龙王已经出现{at}，已蝉联{day}天'
        await session.send(msg)


@sv.on_fullmatch('当前龙王')
async def current_long(bot, event):
    gid = event.group_id
    data = await bot.get_group_honor_info(group_id=gid, type='talkative')
    current_talkactive = data['current_talkative']
    day = current_talkactive['day_count']
    uid = current_talkactive['user_id']
    at = MessageSegment.at(uid)
    msg = f'群龙王{at}，已蝉联{day}天'
    await bot.send(event, msg)


@sv.on_prefix('设置管理员')
async def set_admin(bot, event):
    gid = event.group_id
    sid = event.self_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(event, '咱又不是管理，你找错人了')
        return
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
    sid = event.self_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(event, '咱又不是管理，你找错人了')
        return
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
    sid = event.self_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(event, '咱又不是管理，你找错人了')
        return
    u_priv = priv.get_user_priv(event)
    if u_priv >= sv.manage_priv:
        await bot.set_group_name(group_id=gid, group_name=name)
        await bot.send(event, '我好了')
    else:
        await bot.send(event, '才不听你的呢')


@sv.on_prefix('设置群公告')
async def set_group_notice(bot, event):
    gid = event.group_id
    content = event.message.extract_plain_text().strip()
    if not content:
        return
    sid = event.self_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(event, '咱又不是管理，你找错人了')
        return
    u_priv = priv.get_user_priv(event)
    if u_priv >= sv.manage_priv:
        await bot._send_group_notice(group_id=gid, content=content)
        await bot.send(event, '我好了')
    else:
        await bot.send(event, '才不听你的呢')


@sv.on_prefix('设置名片')
async def set_group_card(bot, event):
    gid = event.group_id
    msg = event.raw_message.replace('设置名片', '').strip()
    sid = event.self_id
    uid = event.user_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(event, '你喉辣么大声赣神魔，要改群名片去找管理啊()')
        return
    if not msg:
        await bot.set_group_card(group_id=gid, user_id=uid)
        await bot.send(event, '我好了')
        return
    match = re.match(r'^\[CQ:at,qq=(\d+)\] *(\S+)$', msg)
    if not match:
        await bot.set_group_card(group_id=gid, user_id=uid, card=msg)
        await bot.send(event, '我好了')
        return
    at = match.group(1) and int(match.group(1))
    card = match.group(2)
    u_priv = priv.get_user_priv(event)
    if u_priv >= sv.manage_priv:
        await bot.set_group_card(group_id=gid, user_id=at, card=card)
        await bot.send(event, '我好了')
    else:
        await bot.send(event, '只有管理以上才能修改他人群名片')


@sv.on_prefix('禁言')
async def ban_user(bot, event):
    gid = event.group_id
    u_priv = priv.get_user_priv(event)
    if u_priv < sv.manage_priv:
        return
    msg = event.message.extract_plain_text().strip()
    sid = event.self_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(event, '咱又不是管理，你找错人了')
        return
    try:
        uid = int(event.message[0].data['qq'])
        min = 1 if not msg else int(msg)
        ban = min * 60
        await bot.set_group_ban(group_id=gid, user_id=uid, duration=ban)
        await bot.send(event, '我好了')
    except Exception as ex:
        sv.logger.error(ex)
        # await bot.send(event, '禁言...禁言它失败了')


@sv.on_prefix('解禁')
async def unban_user(bot, event):
    gid = event.group_id
    u_priv = priv.get_user_priv(event)
    if u_priv < sv.manage_priv:
        return
    sid = event.self_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(event, '咱又不是管理，你找错人了')
        return
    try:
        uid = int(event.message[0].data['qq'])
        await bot.set_group_ban(group_id=gid, user_id=uid, duration=0)
        await bot.send(event, '我好了')
    except Exception as ex:
        sv.logger.error(ex)


@sv.on_prefix('申请头衔')
async def set_group_title(bot, ctx):
    msg = ctx.message.extract_plain_text().strip()
    group = ctx.group_id
    uid = ctx.user_id
    sid = ctx.self_id
    gid = ctx.group_id
    owner = await bot.get_group_member_info(user_id=sid, group_id=gid)
    role = owner['role']
    if role == 'member':
        await bot.send(ctx, '咱又不是管理，你找错人了')
        return
    try:
        await bot.set_group_special_title(group_id=group, user_id=uid, special_title=msg, duration=-1)
        await bot.send(ctx, f'申请头衔{msg}成功')
    except Exception as ex:
        sv.logger.error(ex)
        await bot.send(ctx, f'申请头衔{msg}失败了')


@sv.on_fullmatch('夸我', only_to_me=True)
async def kuangwo(bot, event):
    uid = event.user_id
    url = 'https://chp.shadiao.app/api.php'
    txt = requests.get(url=url, timeout=10).text
    msg = MessageSegment(type_='text', data={'text': txt})
    await bot.send(event, msg, at_sender=True)
    if not lmt.check(uid):
        return
    lmt.increase(uid)
    giftlist = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
    gift = random.choice(giftlist)
    sendgift = MessageSegment(type_='gift', data={'qq': uid, 'id': gift})
    await bot.send(event, sendgift)


@sv.on_fullmatch('来点鸡汤', only_to_me=True)
async def jitang(bot, event):
    url = 'https://du.shadiao.app/api.php'
    txt = requests.get(url=url, timeout=10).text
    await bot.send(event, txt, at_sender=True)


@sv.on_fullmatch('今日一言', only_to_me=True)
async def yiyan(bot, event):
    juzi_type = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k']
    c = random.choice(juzi_type)
    url = f'https://international.v1.hitokoto.cn?c={c}&encode=text&charset=utf-8'
    try:
        txt = requests.get(url=url, timeout=10).text
        await bot.send(event, txt, at_sender=True)
    except Exception as ex:
        sv.logger.exception(ex)


@sv.on_prefix('跟我学', only_to_me=True)
async def txt_to_voice(bot, event):
    msg = event.message.extract_plain_text().strip()
    if not msg:
        return
    tts = MessageSegment(type_='tts', data={'text': msg})
    await bot.send(event, tts)


@sv.on_fullmatch('龙王排行榜')
async def longwangbang(bot, event):
    gid = event.group_id
    data = await bot.get_group_honor_info(group_id=gid, type='talkative')
    group = await bot.get_group_info(group_id=gid, no_cache=False)
    group_name = group['group_name']
    talkactive_list = data['talkative_list']
    msg = ''
    for index in range(len(talkactive_list)):
        rank = index + 1
        talkactive = talkactive_list[index]
        nickname = talkactive['nickname']
        desc = talkactive['description']
        msg += f'{rank}：{nickname}获得龙王{desc}\n'
    res = f'''群【{group_name}】龙王排行榜：
{msg}
'''.strip()
    await bot.send(event, res)


@sv.on_prefix('合刀')
async def hedao(bot, event):
    shanghai = event.message.extract_plain_text().strip()
    shanghai = shanghai.split()
    if not shanghai:
        msg = '请输入：合刀 刀1伤害 刀2伤害 剩余血量\n如：合刀 50 60 70'
        await bot.finish(event, msg)
    if len(shanghai) != 3:
        return
    if is_number(shanghai[0]) is False:
        return
    if is_number(shanghai[1]) is False:
        return
    if is_number(shanghai[2]) is False:
        return
    dao_a = int(shanghai[0])
    dao_b = int(shanghai[1])
    current_hp = int(shanghai[2])
    if dao_a + dao_b < current_hp:
        await bot.finish(event, '当前合刀造成的伤害不能击杀boss')
    # a先出
    a_out = current_hp - dao_a
    a_per = a_out / dao_b
    a_t = (1 - a_per) * 90 + 10
    a_result = math.ceil(a_t)
    if a_result > 90:
        a_result = 90
    # b先出
    b_out = current_hp - dao_b
    b_per = b_out / dao_a
    b_t = (1 - b_per) * 90 + 10
    b_result = math.ceil(b_t)
    if b_result > 90:
        b_result = 90
    msg = f'{dao_a}先出，另一刀可获得{a_result}秒补偿刀\n{dao_b}先出，另一刀可获得{b_result}秒补偿刀'
    await bot.send(event, msg)


@sv.on_prefix('/video')
async def down_video(bot, event):
    url = event.message.extract_plain_text().strip()
    if not url:
        return
    match = re.match(r'https?:/{2}\w.+$', url)
    if not match:
        await bot.send(event, '参数不合法')
        return

    timespan = int(time.time())
    filename = f'{timespan}'
    foloder = R.get('temp/').path
    file = R.get('temp/', f'{filename}.mp4')
    fileabs = os.path.abspath(file.path)
    cover = R.get('temp/', f'{filename}.mp4.jpg')
    # coverabs = os.path.abspath(cover.path)

    if not os.path.exists(foloder):
        os.mkdir(foloder)
    try:
        info_thread = Thread.MyThread(get_video_info, args=(url,))
        info_thread.start()
        info_thread.join()
        info = info_thread.get_result()
        match = re.search(r'MPEG-4 video(.*)\s*Size:(.*)MiB', info)
        if not match:
            await bot.send(event, '参数不正确')
            return
        info_type = match.group(1).strip()
        if info_type != '(video/mp4)':
            await bot.send(event, '未找到视频信息')
            return
        info_size = match.group(2).strip()
        if not util.is_number(info_size):
            await bot.send(event, '无法获取视频大小')
            return
        size = float(info_size)
        if size >= 6.0:
            await bot.send(event, '视频体积过大')
            return

        await bot.send(event, '正在发送...')

        down_thread = Thread.MyThread(
            download_video, args=(url, foloder, filename,))
        down_thread.start()
        down_thread.join()
    except Exception as e:
        sv.logger.error(e)
        await bot.send(event, '获取视频失败了')
        os.remove(file.path)
        os.remove(cover.path)
        return

    # video = MessageSegment(type_='video', data={'file': fileabs, 'cover': coverabs, 'c': 2})
    video = f'[CQ:video,file=file:///{fileabs}]'
    try:
        await bot.send(event, video)
    except:
        await bot.send(event, '发送失败了')
    os.remove(file.path)
    os.remove(cover.path)


def get_video_info(url):
    res = subprocess.getoutput(f'you-get -i {url}')
    return res


def download_video(url, filepath, filename):
    subprocess.getoutput(f'you-get -o {filepath} -O {filename} {url}')


def is_number(s):
    '''判断是否是数字'''
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False
