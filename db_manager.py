import sqlite3
import pickle
from cryptography.fernet import Fernet
import requests

class DBManager:
    def __init__(self, db_path, secret_key):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.fernet = Fernet(secret_key.encode())
        self._create_tables()

    def _create_tables(self):
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS USERS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                full_name TEXT,
                phone TEXT,
                moodle_token TEXT
            );
            CREATE TABLE IF NOT EXISTS SESSIONS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                cookies BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES USERS(id)
            );
        ''')
        self.conn.commit()

    def encrypt(self, text):
        return self.fernet.encrypt(text.encode()).decode()

    def decrypt(self, token):
        return self.fernet.decrypt(token.encode()).decode()

    def get_user_id(self, username, password=None):
        self.cursor.execute('SELECT id FROM USERS WHERE username=?', (username,))
        row = self.cursor.fetchone()
        if row:
            return row[0]
        elif password:
            enc_pass = self.encrypt(password)
            self.cursor.execute('INSERT INTO USERS (username, password) VALUES (?, ?)', (username, enc_pass))
            self.conn.commit()
            return self.cursor.lastrowid
        else:
            raise Exception("المستخدم غير موجود ولم يتم تمرير كلمة مرور لإضافته.")

    def save_session(self, user_id, session):
        cookies = pickle.dumps(session.cookies.get_dict())
        self.cursor.execute('INSERT INTO SESSIONS (user_id, cookies) VALUES (?, ?)', (user_id, cookies))
        self.conn.commit()

    def load_session(self, username):
        self.cursor.execute('''
            SELECT SESSIONS.cookies FROM SESSIONS
            JOIN USERS ON USERS.id = SESSIONS.user_id
            WHERE USERS.username = ?
            ORDER BY SESSIONS.created_at DESC
            LIMIT 1
        ''', (username,))
        row = self.cursor.fetchone()
        if row:
            cookies = pickle.loads(row[0])
            session = requests.Session()
            session.cookies.update(cookies)
            return session
        return None

    def save_token(self, user_id, token):
        encrypted_token = self.encrypt(token)
        self.cursor.execute('UPDATE USERS SET moodle_token=? WHERE id=?', (encrypted_token, user_id))
        self.conn.commit()

    def get_decrypted_token(self, username):
        self.cursor.execute('SELECT moodle_token FROM USERS WHERE username=?', (username,))
        row = self.cursor.fetchone()
        if row and row[0]:
            return self.decrypt(row[0])
        return None
