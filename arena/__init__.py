from .reqbot import *
from . import arena
import re
import time
import os
from collections import defaultdict

import hoshino
from hoshino import R
from hoshino.typing import *
from hoshino.util import FreqLimiter, concat_pic, pic2b64
from PIL import Image, ImageSequence, ImageDraw, ImageFont
from nonebot import MessageSegment, on_command, CommandSession
from .db import JijianCounter

from .. import chara
from . import data


lmt = FreqLimiter(5)
jijian = JijianCounter()
current_path = os.path.abspath(__file__)
absPath = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
font_path = f'{absPath}/font/seguiemj.ttf'


aliases = ('怎么拆', '怎么解', '怎么打', '如何拆', '如何解', '如何打',
           '怎麼拆', '怎麼解', '怎麼打', 'jjc查询', 'jjc查詢')
aliases_b = tuple('b' + a for a in aliases) + tuple('B' + a for a in aliases)
aliases_tw = tuple('台' + a for a in aliases)
aliases_jp = tuple('日' + a for a in aliases)


@on_command('query_arena', aliases=aliases, only_to_me=False)
async def arena_query(session: CommandSession):
    await _arena_query(session, region=1)


@on_command('query_arena_b', aliases=aliases_b, only_to_me=False)
async def arena_query_b(session: CommandSession):
    await _arena_query(session, region=2)


@on_command('query_arena_tw', aliases=aliases_tw, only_to_me=False)
async def arena_query_tw(session: CommandSession):
    await _arena_query(session, region=3)


@on_command('query_arena_jp', aliases=aliases_jp, only_to_me=False)
async def arena_query_jp(session: CommandSession):
    await _arena_query(CommandSession, region=4)


async def _arena_query(session: CommandSession, region: int, refresh=False):

    arena.refresh_quick_key_dic()
    ev = session.event
    uid = ev.user_id
    isAt = True if session.event.detail_type == 'group' else False

    if not lmt.check(uid):
        await session.finish('您查询得过于频繁，请稍等片刻', at_sender=isAt)
    lmt.start_cd(uid)

    # 处理输入数据
    defen = session.current_arg
    defen = re.sub(r'[?？，,_]', '', defen)
    defen, unknown = chara.roster.parse_team(defen)

    if unknown:
        _, name, score = chara.guess_id(unknown)
        if score < 70 and not defen:
            return  # 忽略无关对话
        msg = f'无法识别"{unknown}"' if score < 70 else f'无法识别"{unknown}" 您说的有{score}%可能是{name}'
        await session.finish(msg, at_sender=isAt)
    if not defen:
        await session.finish('查询请发送"怎么拆+防守队伍"，无需+号', at_sender=isAt)
    if len(defen) > 5:
        await session.finish('编队不能多于5名角色', at_sender=isAt)
    if len(defen) < 5:
        await session.finish('编队不能少于5名角色', at_sender=isAt)
    if len(defen) != len(set(defen)):
        await session.finish('编队中含重复角色', at_sender=isAt)
    if any(chara.is_npc(i) for i in defen):
        await session.finish('编队中含未实装角色', at_sender=isAt)
    if 1004 in defen:
        await session.send('\n⚠️您正在查询普通版炸弹人\n※万圣版可用万圣炸弹人/瓜炸等别称', at_sender=isAt)

    # 预处理缓存图片
    outpath = R.img('tmp/').path
    defen_list = defen.copy()
    defen_list.sort()
    filename = '-'.join(str(v) for v in defen_list)
    filename = f'{filename}.jpg'
    if os.path.exists(outpath) is False:
        os.mkdir(outpath)
    save_path = R.img('tmp/', filename).path

    if refresh and os.path.exists(save_path):
        os.remove(save_path)

    # 执行查询
    # sv.logger.info('Doing query...')
    res = await arena.do_query(id_list=defen, user_id=uid, region=region, force=refresh)
    # sv.logger.info('Got response!')

    # 处理查询结果
    if isinstance(res, str):
        await session.finish(f'查询出错，{res}', at_sender=isAt)
    if not len(res):
        await session.finish('抱歉没有查询到解法\n※没有作业说明随便拆 发挥你的想象力～★\n作业上传请前往pcrdfans.com', at_sender=isAt)
    res = res[:min(6, len(res))]    # 限制显示数量，截断结果

    # 第一次查询，无本地缓存
    if os.path.exists(save_path) is False:
        size = len(res)
        target = Image.new('RGBA', (64*6, 64*size), (255, 255, 255, 255))
        draw = ImageDraw.Draw(target)
        ttffont = ImageFont.truetype(font_path, 16)
        index = 0
        for v in res:
            atk = v['atk']
            team_pic = chara.gen_team_pic(atk)
            up = v['up'] + v['my_up']
            down = v['down'] + v['my_down']
            qkey = v['qkey']
            pingjia = f'{qkey}\n\U0001F44D{up}\n\U0001F44E{down}'
            draw.text((64*5, 64*index), pingjia, font=ttffont, fill='#000000')
            target.paste(team_pic, (0, 64*index))
            index += 1
        target = optimize_pic(target)
        target.save(save_path, format='JPEG', quality=50,
                    optimize=True, progressive=True)
    # 拼接回复
    atk_team = MessageSegment.image(f'file:///{os.path.abspath(save_path)}')
    defen = [chara.fromid(x).name for x in defen]
    defen = f"防守方【{' '.join(defen)}】"
    at = str(MessageSegment.at(ev.user_id)) if isAt else ev.sender['nickname']

    msg = [
        defen,
        f'已为骑士{at}查询到以下进攻方案：',
        str(atk_team),
        '※发送"点赞/点踩"可进行评价'
    ]

    msg.append('Support by pcrdfans_com')

    await session.send('\n'.join(msg))
    # sv.logger.debug('Arena result sent!')


def optimize_pic(img: Image):
    im = Image.new('RGB', img.size, '#ffffff')
    im.paste(img, None, img)
    w, h = im.size
    im.thumbnail((w / 0.9, h / 0.9), Image.ANTIALIAS)
    return im


@on_command('query_arena_like', aliases='点赞', only_to_me=False)
async def arena_like(session: CommandSession):
    await _arena_feedback(session, 1)


@on_command('query_arena_unlike', aliases='点踩', only_to_me=False)
async def arena_dislike(session: CommandSession):
    await _arena_feedback(session, -1)


rex_qkey = re.compile(r'^[0-9a-zA-Z]{5}$')


async def _arena_feedback(session: CommandSession, action: int):
    action_tip = '赞' if action > 0 else '踩'
    ev = session.event
    qkey = ev.message.extract_plain_text().strip()
    if not qkey:
        await session.finish(f'请发送"点{action_tip}+作业id"，如"点{action_tip}ABCDE"，不分大小写')
    if not rex_qkey.match(qkey):
        await session.finish(f'您要点{action_tip}的作业id不合法')
    try:
        await arena.do_like(qkey, ev.user_id, action)
    except KeyError:
        await session.finish('无法找到作业id！您只能评价您最近查询过的作业')
    await session.send('感谢您的反馈！')


def get_atk_id(chara_list):
    res = ''
    for v in chara_list:
        res += f'{v.id},'
    res_len = len(res) - 1
    res = res[0:res_len]
    return res


@on_command('query_arena_code', aliases='查询jjc错误码', only_to_me=False)
async def query_error_code(session: CommandSession):
    code = data.ERROR_CODE
    res = ''
    msg = session.event.message.extract_plain_text()
    if not msg:
        for index in code:
            res += f'{index}:{code[index]}\n'
        res = res.strip()
        res = f'''
常见错误码如下：
{res}
'''.strip()
    else:
        msg = int(msg)
        res = code[msg]
    await session.send(res)


@on_command('query_arena_refresh_deffend', aliases='刷新作业', only_to_me=False)
async def refresh_deffend(session: CommandSession):
    # 执行查询
    await _arena_query(session, 1, True)


@on_command('query_arena_del_deffend', aliases='删除作业', only_to_me=False)
async def del_deffend(session: CommandSession):
    ev = session.event
    uid = ev.user_id
    bot = hoshino.get_bot()
    if uid not in bot.config.SUPERUSERS:
        return
    defen = ev.message.extract_plain_text()
    defen = re.sub(r'[?？，,_]', '', defen)
    defen, unknown = chara.roster.parse_team(defen)

    if unknown:
        _, name, score = chara.guess_id(unknown)
        if score < 70 and not defen:
            return  # 忽略无关对话
        msg = f'无法识别"{unknown}"' if score < 70 else f'无法识别"{unknown}" 您说的有{score}%可能是{name}'
        await session.finish(msg)
    if not defen:
        return
    if len(defen) > 5:
        await session.finish('编队不能多于5名角色')
    if len(defen) < 5:
        await session.finish('编队不能少于5名角色')
    if len(defen) != len(set(defen)):
        await session.finish('编队中含重复角色')
    if any(chara.is_npc(i) for i in defen):
        await session.finish('编队中含未实装角色')
    if 1004 in defen:
        await session.send('\n⚠️您正在查询普通版炸弹人\n※万圣版可用万圣炸弹人/瓜炸等别称')

    # 预处理缓存图片
    defen_list = defen.copy()
    defen_list.sort()
    filename = '-'.join(str(v) for v in defen_list)
    filename = f'{filename}.jpg'
    save_path = R.img('tmp/', filename).path
    if os.path.exists(save_path):
        os.remove(save_path)

    attack = ",".join(str(v) for v in defen_list)
    # zuoye = jijian.get_attack(attack)
    # if zuoye is None:
    #     await bot.send(ev, '作业不存在')
    # else:
    #     jijian.del_attack(attack)
    #     await bot.send(ev, '删除作业完了')
    jijian.del_attack(attack)
    await session.send('删除作业完了')
