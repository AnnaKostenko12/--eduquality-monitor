"""Операції з довідниками, користувачами та збереження анкет."""
import datetime
import sqlite3
from contextlib import closing

import auth
from database import connect, execute, query

DICTS = {
    "teachers": ("teachers", "teacher_id"),
    "subjects": ("subjects", "subject_id"),
    "groups": ("student_groups", "group_id"),
}


def items(kind):
    table = DICTS[kind][0]
    return query(f"SELECT id, name FROM {table} ORDER BY name")


def add_item(kind, name):
    table = DICTS[kind][0]
    try:
        execute(f"INSERT INTO {table}(name) VALUES(?)", (name,))
    except sqlite3.IntegrityError:
        raise ValueError("Такий запис уже існує")


def in_use(kind, item_id):
    fk = DICTS[kind][1]
    return bool(query(f"SELECT 1 FROM surveys WHERE {fk} = ? LIMIT 1", (item_id,)))


def delete_item(kind, item_id):
    table = DICTS[kind][0]
    execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))


def users():
    return query("SELECT id, login, full_name, role FROM users ORDER BY login")


def add_user(login, full_name, password, role):
    try:
        auth.create_user(login, full_name, password, role)
    except sqlite3.IntegrityError:
        raise ValueError("Користувач з таким логіном уже існує")


def delete_user(user_id):
    execute("DELETE FROM users WHERE id = ?", (user_id,))


def save_survey(student_id, teacher_id, subject_id, group_id, comment, scores):
    try:
        with closing(connect()) as c, c:
            cur = c.execute(
                "INSERT INTO surveys(created, teacher_id, subject_id, group_id, student_id, comment) "
                "VALUES(?,?,?,?,?,?)",
                (datetime.date.today().isoformat(), teacher_id, subject_id, group_id, student_id, comment),
            )
            c.executemany(
                "INSERT INTO answers(survey_id, criterion, score) VALUES(?,?,?)",
                [(cur.lastrowid, i, s) for i, s in enumerate(scores)],
            )
    except sqlite3.IntegrityError:
        raise ValueError("Ви вже оцінювали цього викладача з цієї дисципліни")
