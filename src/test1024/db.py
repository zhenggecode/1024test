"""Only DML statements are executed through the restricted application user."""

import hashlib
import hmac
import os

import pymysql


def password_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)


class Accounts:
    def __init__(self, config):
        self.config = config

    def connect(self):
        return pymysql.connect(
            host=self.config["db_host"],
            port=self.config["db_port"],
            user=self.config["db_user"],
            password=self.config["db_password"],
            database=self.config["db_name"],
            charset="utf8mb4",
            connect_timeout=3,
            read_timeout=3,
            write_timeout=3,
        )

    def check(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM accounts LIMIT 1")

    def create(self, username, password):
        salt = os.urandom(16)
        digest = password_hash(password, salt)
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO accounts (username, salt, password_hash) VALUES (%s, %s, %s)",
                        (username, salt, digest),
                    )
                conn.commit()
            return True
        except pymysql.err.IntegrityError as exc:
            if exc.args and exc.args[0] == 1062:
                return False
            raise

    def login(self, username, password):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT salt, password_hash FROM accounts WHERE username = %s", (username,)
                )
                row = cur.fetchone()
        if row is None:
            return "missing"
        return "ok" if hmac.compare_digest(password_hash(password, row[0]), row[1]) else "wrong"

    def exists(self, username):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM accounts WHERE username = %s", (username,))
                return cur.fetchone() is not None
