"""Демо-дані для першого запуску."""
import datetime
import random
from contextlib import closing

import auth
from config import CRITERIA
from database import connect, query


def seed_demo():
    if query("SELECT 1 FROM teachers LIMIT 1"):
        return
    auth.create_user("methodist", "Методист Олена Іванівна", "method123", "methodist")
    auth.create_user("student", "Студент Демонстраційний", "student123", "student")

    rnd = random.Random(42)
    teachers = ["Коваленко І. П.", "Шевченко О. М.", "Мельник Т. В.", "Бондаренко С. А."]
    subjects = ["Бази даних", "Програмування", "Вища математика", "Англійська мова"]
    groups = ["КН-21", "КН-22", "ІПЗ-31"]
    bias = [4.6, 4.0, 3.3, 4.2]
    comments = ["Цікаві та зрозумілі лекції", "Хотілося б більше практики", "Багато матеріалу за короткий час",
                "Дуже доброзичливий викладач", "Розклад незручний", "Чудові приклади із реальних проєктів"]
    today = datetime.date.today()

    with closing(connect()) as c, c:
        c.executemany("INSERT INTO teachers(name) VALUES(?)", [(t,) for t in teachers])
        c.executemany("INSERT INTO subjects(name) VALUES(?)", [(s,) for s in subjects])
        c.executemany("INSERT INTO student_groups(name) VALUES(?)", [(g,) for g in groups])
        for _ in range(90):
            t = rnd.randint(1, len(teachers))
            days = rnd.randint(0, 179)
            trend = (180 - days) / 180 * 0.4
            comment = rnd.choice(comments) if rnd.random() < 0.25 else ""
            cur = c.execute(
                "INSERT INTO surveys(created, teacher_id, subject_id, group_id, student_id, comment) "
                "VALUES(?,?,?,?,NULL,?)",
                ((today - datetime.timedelta(days=days)).isoformat(), t,
                 rnd.randint(1, len(subjects)), rnd.randint(1, len(groups)), comment))
            rows = []
            for k in range(len(CRITERIA)):
                noise = (rnd.random() + rnd.random() + rnd.random() - 1.5) * 1.2
                rows.append((cur.lastrowid, k, max(1, min(5, round(bias[t - 1] + trend + noise)))))
            c.executemany("INSERT INTO answers(survey_id, criterion, score) VALUES(?,?,?)", rows)
