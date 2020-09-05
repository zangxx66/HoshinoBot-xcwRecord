import sqlite3
import os

DB_PATH = os.path.expanduser('~/.hoshino/arena_cache.db')


class JijianCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._create_table()

    def _connect(self):
        return sqlite3.connect(DB_PATH)

    def _create_table(self):
        try:
            self._connect().execute('''CREATE TABLE IF NOT EXISTS JIJIAN
            (GID INTEGER PRIMARY KEY AUTOINCREMENT,
            ATTACK VARCHAR(4000) NOT NULL,
            DEFEND VARCHAR(4000) NOT NULL
            );''')
        except:
            raise Exception('创建击剑表错误')

    def add_attack(self, attack, result):
        try:
            conn = self._connect()
            conn.execute("INSERT INTO JIJIAN (ATTACK, DEFEND) \
                         VALUES (?, ?)", (attack, result))
            conn.commit()
        except:
            raise Exception('插入击剑错误')

    def get_attack(self, attack):
        try:
            conn = self._connect()
            result = conn.execute("SELECT DEFEND FROM JIJIAN WHERE ATTACK=?", [attack]).fetchall()
            if len(result) == 0:
                return None
            else:
                return result[0]
        except:
            raise Exception('查找击剑错误')
