"""Аналітичні запити: середні оцінки, рівні якості, динаміка, коментарі."""
from collections import namedtuple

from config import CRITERIA
from database import query

Filter = namedtuple("Filter", "subject_id group_id date_from date_to")
TeacherStat = namedtuple("TeacherStat", "teacher_id name surveys scores avg")

_FROM = " FROM surveys s JOIN answers a ON a.survey_id = s.id"


def _where(f, teacher_id=None):
    sql = " WHERE s.created BETWEEN ? AND ?"
    args = [f.date_from, f.date_to]
    if f.subject_id:
        sql += " AND s.subject_id = ?"
        args.append(f.subject_id)
    if f.group_id:
        sql += " AND s.group_id = ?"
        args.append(f.group_id)
    if teacher_id:
        sql += " AND s.teacher_id = ?"
        args.append(teacher_id)
    return sql, args


def level(avg):
    if avg >= 4.5:
        return "Високий"
    if avg >= 3.5:
        return "Достатній"
    if avg >= 2.5:
        return "Середній"
    return "Низький"


def level_color(avg):
    if avg >= 4.5:
        return "#2e9e5b"
    if avg >= 3.5:
        return "#3b82f6"
    if avg >= 2.5:
        return "#f59e0b"
    return "#ef4444"


def teacher_stats(f):
    w, a = _where(f)
    rows = query(
        "SELECT t.id, t.name, a.criterion, AVG(a.score), COUNT(*) "
        "FROM surveys s JOIN teachers t ON t.id = s.teacher_id JOIN answers a ON a.survey_id = s.id"
        + w + " GROUP BY t.id, t.name, a.criterion", a)
    data = {}
    for tid, name, crit, avg, n in rows:
        d = data.setdefault(tid, {"name": name, "n": n, "scores": [0.0] * len(CRITERIA)})
        d["scores"][crit] = avg
        d["n"] = max(d["n"], n)
    stats = [TeacherStat(tid, d["name"], d["n"], d["scores"], sum(d["scores"]) / len(CRITERIA))
             for tid, d in data.items()]
    return sorted(stats, key=lambda s: -s.avg)


def criteria_averages(f):
    w, a = _where(f)
    res = [0.0] * len(CRITERIA)
    for crit, avg in query("SELECT a.criterion, AVG(a.score)" + _FROM + w + " GROUP BY a.criterion", a):
        res[crit] = avg
    return res


def monthly(f, teacher_id=None):
    w, a = _where(f, teacher_id)
    return query("SELECT substr(s.created, 1, 7), AVG(a.score)" + _FROM + w +
                 " GROUP BY substr(s.created, 1, 7) ORDER BY substr(s.created, 1, 7)", a)


def summary(f):
    w, a = _where(f)
    count, avg = query("SELECT COUNT(DISTINCT s.id), AVG(a.score)" + _FROM + w, a)[0]
    return count, (avg or 0.0)


def comments(f, teacher_id):
    w, a = _where(f, teacher_id)
    rows = query("SELECT s.created, s.comment FROM surveys s" + w +
                 " AND s.comment IS NOT NULL AND s.comment <> '' ORDER BY s.created DESC LIMIT 100", a)
    return [f"{d}:  {c}" for d, c in rows]
