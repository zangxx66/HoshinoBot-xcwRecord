import sqlite3
import os

DB_PATH = os.path.expanduser('~/.hoshino/arena_cache.db')


class JijianCounter:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = None
        self.cursor = None
        self._create_table()

    def _connect(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def _create_table(self):
        try:
            self._connect()
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS JIJIAN
            (GID INTEGER PRIMARY KEY AUTOINCREMENT,
            ATTACK VARCHAR(4000) NOT NULL,
            DEFEND VARCHAR(4000) NOT NULL
            );''')
            self.conn.commit()
        except Exception as e:
            print(e)

    def add_attack(self, attack, result):
        try:
            self.cursor.execute("INSERT OR REPLACE INTO JIJIAN (ATTACK, DEFEND) \
                         VALUES (?, ?)", (attack, result))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    def del_attack(self, attack):
        try:
            self.cursor.execute("DELETE FROM JIJIAN WHERE ATTACK=?", [attack])
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(e)

    def get_attack(self, attack):
        try:
            result = self.cursor.execute("SELECT DEFEND FROM JIJIAN WHERE ATTACK=?", [attack]).fetchall()
            if len(result) == 0:
                return None
            else:
                return result[0]
        except Exception as e:
            print(e)
            return None

    def del_all(self):
        try:
            self.cursor.execute("DELETE FROM JIJIAN")
            self.conn.commit()
        except Exception as e:
            print(e)
