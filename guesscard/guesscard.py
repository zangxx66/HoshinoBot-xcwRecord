from nonebot import MessageSegment
from datetime import datetime, timedelta
import hoshino
from hoshino import Service, util
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
from . import chara
from . import _pcr_data
import math
import sqlite3
import os
import random
import asyncio


sv = Service('cardguess', bundle='pcr娱乐', help_='''
猜立绘 | 猜猜机器人随机发送的立绘的一小部分来自哪位角色
猜立绘群排行 | 显示猜立绘小游戏猜对次数的群排行榜(只显示前十名)
'''.strip())


PIC_SIDE_LENGTH = 128
ONE_TURN_TIME = 20
DB_PATH = os.path.expanduser('~/.hoshino/pcr_card_guess_winning_counter.db')
SCORE_DB_PATH = os.path.expanduser('~/.hoshino/pcr_running_counter.db')
DUEL_DB_PATH = os.path.expanduser('~/.hoshino/pcr_duel.db')
SCORE_DAILY_LIMIT = 3
RESET_HOUR = 0
BLACKLIST_ID = [1000]
current_path = os.path.abspath(__file__)
res_dir = os.path.abspath(os.path.dirname(current_path) + os.path.sep + ".")
full_path = os.path.abspath(os.path.join(res_dir, 'card'))


class DuelCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DUEL_DB_PATH), exist_ok=True)
        self._create_charatable()
        self._create_uidtable()
        self._create_leveltable()
        self._create_queentable()
        self._create_favortable()
        self._create_gifttable()
        self._create_warehousetable()

    def _connect(self):
        return sqlite3.connect(DUEL_DB_PATH)

    def _create_charatable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS CHARATABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except:
            raise Exception('创建角色表发生错误')

    def _create_uidtable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS UIDTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except:
            raise Exception('创建UID表发生错误')

    def _create_leveltable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS LEVELTABLE
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           LEVEL           INT    NOT NULL,
                           
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建UID表发生错误')

    def _get_card_owner(self, gid, cid):
        try:
            r = self._connect().execute(
                "SELECT UID FROM CHARATABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找角色归属发生错误')

    def _set_card_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO CHARATABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_card_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM CHARATABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )
    
    def _get_card_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM CHARATABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}

    def _get_level(self, gid, uid):
        try:
            r = self._connect().execute(
                "SELECT LEVEL FROM LEVELTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找等级发生错误')

    def _get_cards(self, gid, uid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT CID, NUM FROM UIDTABLE WHERE GID=? AND UID=? AND NUM>0", (
                    gid, uid)
            ).fetchall()
        return [c[0] for c in r] if r else {}

    def _get_card_num(self, gid, uid, cid):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT NUM FROM UIDTABLE WHERE GID=? AND UID=? AND CID=?", (
                    gid, uid, cid)
            ).fetchone()
            return r[0] if r else 0

    def _add_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        if cid != 9999:
            self._set_card_owner(gid, cid, uid)
            self._set_favor(gid, uid, cid, 0)

    def _delete_card(self, gid, uid, cid, increment=1):
        num = self._get_card_num(gid, uid, cid)
        num -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO UIDTABLE (GID, UID, CID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, num),
            )
        self._delete_card_owner(gid, cid)
        self._delete_favor(gid, uid, cid)

    def _add_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level += increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _reduce_level(self, gid, uid, increment=1):
        level = self._get_level(gid, uid)
        level -= increment
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _set_level(self, gid, uid, level):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO LEVELTABLE (GID, UID, LEVEL) VALUES (?, ?, ?)",
                (gid, uid, level),
            )

    def _get_level_num(self, gid, level):
        with self._connect() as conn:
            r = conn.execute(
                "SELECT COUNT(UID) FROM LEVELTABLE WHERE GID=? AND LEVEL=? ", (gid, level)
            ).fetchone()
            return r[0] if r else 0
    
    def _create_queentable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS QUEENTABLE
                          (GID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           PRIMARY KEY(GID, CID));''')
        except:
            raise Exception('创建皇后表发生错误')

    def _get_queen_owner(self, gid, cid):
        try:
            r = self._connect().execute(
                "SELECT UID FROM QUEENTABLE WHERE GID=? AND CID=?", (gid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找皇后归属发生错误')

    def _set_queen_owner(self, gid, cid, uid):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO QUEENTABLE (GID, CID, UID) VALUES (?, ?, ?)",
                (gid, cid, uid),
            )

    def _delete_queen_owner(self, gid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM QUEENTABLE  WHERE GID=? AND CID=?",
                (gid, cid),
            )

    def _get_queen_list(self, gid):
        with self._connect() as conn:
            r = conn.execute(
                f"SELECT CID FROM QUEENTABLE WHERE GID={gid}").fetchall()
            return [c[0] for c in r] if r else {}
    
    def _search_queen(self, gid, uid):
        try:
            r = self._connect().execute(
                "SELECT CID FROM QUEENTABLE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找皇后发生错误')
    
    def _create_favortable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS FAVORTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           CID             INT    NOT NULL,
                           FAVOR           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, CID));''')
        except:
            raise Exception('创建好感表发生错误')

    def _set_favor(self, gid, uid, cid, favor):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _get_favor(self, gid, uid, cid):
        try:
            r = self._connect().execute("SELECT FAVOR FROM FAVORTABLE WHERE GID=? AND UID=? AND CID=?",
                                        (gid, uid, cid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找好感发生错误')

    def _add_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        if favor == None:
            favor = 0
        favor += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _reduce_favor(self, gid, uid, cid, num):
        favor = self._get_favor(gid, uid, cid)
        favor -= num
        favor = max(favor, 0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO FAVORTABLE (GID, UID, CID, FAVOR) VALUES (?, ?, ?, ?)",
                (gid, uid, cid, favor),
            )

    def _delete_favor(self, gid, uid, cid):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM FAVORTABLE  WHERE GID=? AND UID=? AND CID=?",
                (gid, uid, cid),
            )
    
    def _create_gifttable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS GIFTTABLE
                          (
                           GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           GFID             INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID, GFID));''')
        except:
            raise Exception('创建礼物表发生错误')

    def _get_gift_num(self, gid, uid, gfid):
        try:
            r = self._connect().execute("SELECT NUM FROM GIFTTABLE WHERE GID=? AND UID=? AND GFID=?",
                                        (gid, uid, gfid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找礼物发生错误')

    def _add_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        if giftnum == None:
            giftnum = 0
        giftnum += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            )

    def _reduce_gift(self, gid, uid, gfid, num=1):
        giftnum = self._get_gift_num(gid, uid, gfid)
        giftnum -= num
        giftnum = max(giftnum, 0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO GIFTTABLE (GID, UID, GFID, NUM) VALUES (?, ?, ?, ?)",
                (gid, uid, gfid, giftnum),
            )
    
    def _create_warehousetable(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WAREHOUSE
                          (GID             INT    NOT NULL,
                           UID           INT    NOT NULL,
                           NUM           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建仓库上限表发生错误')

    def _get_warehouse(self, gid, uid):
        try:
            r = self._connect().execute(
                "SELECT NUM FROM WAREHOUSE WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找上限发生错误')

    def _add_warehouse(self, gid, uid, num):
        housenum = self._get_warehouse(gid, uid)
        housenum += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO WAREHOUSE (GID, UID, NUM) VALUES (?, ?, ?)",
                (gid, uid, housenum),
            )


class WinnerJudger:
    def __init__(self):
        self.on = {}
        self.winner = {}
        self.correct_chara_id = {}

    def record_winner(self, gid, uid):
        self.winner[gid] = str(uid)

    def get_winner(self, gid):
        return self.winner[gid] if self.winner.get(gid) is not None else ''

    def get_on_off_status(self, gid):
        return self.on[gid] if self.on.get(gid) is not None else False

    def set_correct_chara_id(self, gid, cid):
        self.correct_chara_id[gid] = cid

    def get_correct_chara_id(self, gid):
        return self.correct_chara_id[gid] if self.correct_chara_id.get(gid) is not None else chara.UNKNOWN

    def turn_on(self, gid):
        self.on[gid] = True

    def turn_off(self, gid):
        self.on[gid] = False
        self.winner[gid] = ''
        self.correct_chara_id[gid] = chara.UNKNOWN


winner_judger = WinnerJudger()


class WinningCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._create_table()

    def _connect(self):
        return sqlite3.connect(DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS WINNINGCOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           COUNT           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')

    def _record_winning(self, gid, uid):
        try:
            winning_number = self._get_winning_number(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO WINNINGCOUNTER (GID,UID,COUNT) \
                                VALUES (?,?,?)", (gid, uid, winning_number+1))
            conn.commit()
        except:
            raise Exception('更新表发生错误')

    def _get_winning_number(self, gid, uid):
        try:
            r = self._connect().execute(
                "SELECT COUNT FROM WINNINGCOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')


class RecordDAO:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS limiter"
                "(key TEXT NOT NULL, num INT NOT NULL, date INT, PRIMARY KEY(key))"
            )

    def exist_check(self, key):
        try:
            key = str(key)
            with self.connect() as conn:
                conn.execute(
                    "INSERT INTO limiter (key,num,date) VALUES (?, 0,-1)", (key,), )
            return
        except:
            return

    def get_num(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT num FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def clear_key(self, key):
        key = str(key)
        self.exist_check(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET num=0 WHERE key=?", (key,), )
        return

    def increment_key(self, key, num):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute(
                "UPDATE limiter SET num=num+? WHERE key=?", (num, key,))
        return

    def get_date(self, key):
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            r = conn.execute(
                "SELECT date FROM limiter WHERE key=? ", (key,)
            ).fetchall()
            r2 = r[0]
        return r2[0]

    def set_date(self, date, key):
        print(date)
        self.exist_check(key)
        key = str(key)
        with self.connect() as conn:
            conn.execute("UPDATE limiter SET date=? WHERE key=?",
                         (date, key,), )
        return


# 以下用于贵族游戏和赛跑联动，金币互通
db = RecordDAO(DB_PATH)


class DailyAmountLimiter(DailyNumberLimiter):
    def __init__(self, types, max_num, reset_hour):
        super().__init__(max_num)
        self.reset_hour = reset_hour
        self.type = types

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < self.max)

    def check10(self, key) -> bool:
        now = datetime.now(self.tz)
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        day = (now - timedelta(hours=self.reset_hour)).day
        if day != db.get_date(key):
            db.set_date(day, key)
            db.clear_key(key)
        return bool(db.get_num(key) < 10)

    def get_num(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        return db.get_num(key)

    def increase(self, key, num=1):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.increment_key(key, num)

    def reset(self, key):
        key = list(key)
        key.append(self.type)
        key = tuple(key)
        db.clear_key(key)


daily_score_limiter = DailyAmountLimiter('score', SCORE_DAILY_LIMIT, RESET_HOUR)


class ScoreCounter2:
    def __init__(self):
        os.makedirs(os.path.dirname(SCORE_DB_PATH), exist_ok=True)
        self._create_table()
        self._create_pres_table()

    def _connect(self):
        return sqlite3.connect(SCORE_DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS SCORECOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           SCORE           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')

    def _add_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            conn = self._connect()
            conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score + score))
            conn.commit()
        except:
            raise Exception('更新表发生错误')

    def _reduce_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, current_score - score))
                conn.commit()
            else:
                conn = self._connect()
                conn.execute("INSERT OR REPLACE INTO SCORECOUNTER (GID,UID,SCORE) \
                                VALUES (?,?,?)", (gid, uid, 0))
                conn.commit()
        except:
            raise Exception('更新表发生错误')

    def _get_score(self, gid, uid):
        try:
            r = self._connect().execute(
                "SELECT SCORE FROM SCORECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return 0 if r is None else r[0]
        except:
            raise Exception('查找表发生错误')

    # 判断金币是否足够下注
    def _judge_score(self, gid, uid, score):
        try:
            current_score = self._get_score(gid, uid)
            if current_score >= score:
                return 1
            else:
                return 0
        except Exception as e:
            raise Exception(str(e))

    # 记录国王声望数据
    def _create_pres_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS PRESTIGECOUNTER
                          (GID             INT    NOT NULL,
                           UID             INT    NOT NULL,
                           PRESTIGE           INT    NOT NULL,
                           PRIMARY KEY(GID, UID));''')
        except:
            raise Exception('创建表发生错误')

    def _set_prestige(self, gid, uid, prestige):
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )

    def _get_prestige(self, gid, uid):
        try:
            r = self._connect().execute(
                "SELECT PRESTIGE FROM PRESTIGECOUNTER WHERE GID=? AND UID=?", (gid, uid)).fetchone()
            return None if r is None else r[0]
        except:
            raise Exception('查找声望发生错误')

    def _add_prestige(self, gid, uid, num):
        prestige = self._get_prestige(gid, uid)
        prestige += num
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )

    def _reduce_prestige(self, gid, uid, num):
        prestige = self._get_prestige(gid, uid)
        prestige -= num
        prestige = max(prestige, 0)
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO PRESTIGECOUNTER (GID, UID, PRESTIGE) VALUES (?, ?, ?)",
                (gid, uid, prestige),
            )


async def get_user_card_dict(bot, group_id):
    mlist = await bot.get_group_member_list(group_id=group_id)
    d = {}
    for m in mlist:
        d[m['user_id']] = m['card'] if m['card'] != '' else m['nickname']
    return d


def uid2card(uid, user_card_dict):
    return str(uid) if uid not in user_card_dict.keys() else user_card_dict[uid]


@sv.on_fullmatch(('猜立绘排行榜', '猜立绘群排行'))
async def description_guess_group_ranking(bot, ev: CQEvent):
    try:
        user_card_dict = await get_user_card_dict(bot, ev.group_id)
        card_winningcount_dict = {}
        winning_counter = WinningCounter()
        for uid in user_card_dict.keys():
            if uid != ev.self_id:
                card_winningcount_dict[user_card_dict[uid]] = winning_counter._get_winning_number(
                    ev.group_id, uid)
        group_ranking = sorted(
            card_winningcount_dict.items(), key=lambda x: x[1], reverse=True)
        msg = '猜立绘小游戏此群排行为:\n'
        for i in range(min(len(group_ranking), 10)):
            if group_ranking[i][1] != 0:
                msg += f'第{i+1}名: {group_ranking[i][0]}, 猜对次数: {group_ranking[i][1]}次\n'
        await bot.send(ev, msg.strip())
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_fullmatch('猜立绘')
async def avatar_guess(bot, ev: CQEvent):
    if winner_judger.get_on_off_status(ev.group_id):
        await bot.send(ev, "此轮游戏还没结束，请勿重复使用指令")
        return
    winner_judger.turn_on(ev.group_id)
    chara_id_list = list(_pcr_data.CHARA_NAME.keys())
    list_len = len(chara_id_list) - 1
    while True:
        index = random.randint(0, list_len)
        if chara_id_list[index] not in BLACKLIST_ID:
            idx = chara_id_list[index]
            starlist = [3, 6]
            star = random.choice(starlist)
            img_path = os.path.join(full_path, f'icon_unit_{idx}{star}1.png')
            if os.path.exists(img_path):
                break
    winner_judger.set_correct_chara_id(ev.group_id, chara_id_list[index])
    current_path = os.path.abspath(__file__)
    absPath = os.path.abspath(os.path.dirname(
        current_path) + os.path.sep + ".")
    dir_path = os.path.join(absPath, 'card')
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    c = chara.fromid(chara_id_list[index])
    img = c.icon.open()
    left = math.floor(random.random()*(1409-PIC_SIDE_LENGTH))
    upper = math.floor(random.random()*(793-PIC_SIDE_LENGTH))
    cropped = img.crop(
        (left, upper, left+PIC_SIDE_LENGTH, upper+PIC_SIDE_LENGTH))
    cropped = MessageSegment.image(util.pic2b64(cropped))
    msg = f'猜猜这个图片是哪位角色立绘的一部分?({ONE_TURN_TIME}s后公布答案){cropped}'
    await bot.send(ev, msg)
    await asyncio.sleep(ONE_TURN_TIME)
    if winner_judger.get_winner(ev.group_id) != '':
        winner_judger.turn_off(ev.group_id)
        return
    msg = f'正确答案是: {c.name}{c.icon.cqcode}\n很遗憾，没有人答对~'
    winner_judger.turn_off(ev.group_id)
    await bot.send(ev, msg)


@sv.on_message()
async def on_input_chara_name(bot, ev: CQEvent):
    try:
        if winner_judger.get_on_off_status(ev.group_id):
            s = ev.message.extract_plain_text()
            cid = chara.name2id(s)
            if cid != chara.UNKNOWN and cid == winner_judger.get_correct_chara_id(ev.group_id) and winner_judger.get_winner(ev.group_id) == '':
                winner_judger.record_winner(ev.group_id, ev.user_id)
                winning_counter = WinningCounter()
                winning_counter._record_winning(ev.group_id, ev.user_id)
                winning_count = winning_counter._get_winning_number(
                    ev.group_id, ev.user_id)
                user_card_dict = await get_user_card_dict(bot, ev.group_id)
                user_card = uid2card(ev.user_id, user_card_dict)
                msg_part = f'{user_card}猜对了，真厉害！TA已经猜对{winning_count}次了~\n(此轮游戏将在时间到后自动结束，请耐心等待)'
                duel = DuelCounter()
                gid = ev.group_id
                uid = ev.user_id
                guid = gid, uid
                if duel._get_level(gid, uid) != 0 and daily_score_limiter.check(guid):
                    score = random.randint(100, 300)
                    score_counter = ScoreCounter2()
                    score_counter._add_score(gid, uid, score)
                    daily_score_limiter.increase(guid)
                    msg_part += f'\n获得金币{score}'
                c = chara.fromid(
                    winner_judger.get_correct_chara_id(ev.group_id))
                msg = f'正确答案是: {c.name}{c.icon.cqcode}\n{msg_part}'
                await bot.send(ev, msg)
    except Exception as e:
        await bot.send(ev, '错误:\n' + str(e))


@sv.on_fullmatch('刷新猜立绘')
async def update_chara(bot, ev: CQEvent):
    uid = ev.user_id
    if uid not in hoshino.config.SUPERUSERS:
        return
    chara.roster.update()
    await bot.send(ev, '我好了')
