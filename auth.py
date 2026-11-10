"""Автентифікація: паролі зберігаються як PBKDF2-хеш із сіллю."""
import hashlib
import hmac
import os
from collections import namedtuple

from database import execute, query

User = namedtuple("User", "id login full_name role")
ITERATIONS = 100_000


def _hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)


def create_user(login, full_name, password, role):
    salt = os.urandom(16)
    execute(
        "INSERT INTO users(login, full_name, salt, hash, role) VALUES(?,?,?,?,?)",
        (login, full_name, salt.hex(), _hash(password, salt).hex(), role),
    )


def login(login_, password):
    rows = query("SELECT id, login, full_name, salt, hash, role FROM users WHERE login = ?", (login_,))
    if not rows:
        return None
    uid, lg, name, salt, pw_hash, role = rows[0]
    calc = _hash(password, bytes.fromhex(salt))
    if hmac.compare_digest(calc, bytes.fromhex(pw_hash)):
        return User(uid, lg, name, role)
    return None


def ensure_admin():
    if not query("SELECT 1 FROM users LIMIT 1"):
        create_user("admin", "Адміністратор системи", "admin123", "admin")
