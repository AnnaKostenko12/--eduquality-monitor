"""Шар доступу до SQLite: підключення, запити, схема."""
import os
import sqlite3
from contextlib import closing
import sys

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "quality.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    login TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    salt TEXT NOT NULL,
    hash TEXT NOT NULL,
    role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS teachers(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS student_groups(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS surveys(
    id INTEGER PRIMARY KEY,
    created TEXT NOT NULL,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    group_id INTEGER NOT NULL REFERENCES student_groups(id),
    student_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    comment TEXT,
    UNIQUE(student_id, teacher_id, subject_id)
);
CREATE TABLE IF NOT EXISTS answers(
    survey_id INTEGER NOT NULL REFERENCES surveys(id) ON DELETE CASCADE,
    criterion INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5)
);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(sql, args=()):
    with closing(connect()) as c:
        return c.execute(sql, args).fetchall()


def execute(sql, args=()):
    with closing(connect()) as c:
        cur = c.execute(sql, args)
        c.commit()
        return cur.lastrowid


def init_schema():
    with closing(connect()) as c:
        c.executescript(SCHEMA)
