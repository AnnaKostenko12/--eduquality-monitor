"""Вкладки головного вікна."""
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import analytics
import repo
from config import CRITERIA, ROLE_UA
from widgets import ChartCanvas, FilterBar, IdCombo

class DirectoryPanel(ttk.LabelFrame):
    def __init__(self, parent, title, kind):
        super().__init__(parent, text=title, padding=8)
        self.kind, self.ids = kind, []
        self.lb = tk.Listbox(self, exportselection=False)
        self.lb.pack(fill="both", expand=True)
        self.entry = ttk.Entry(self)
        self.entry.pack(fill="x", pady=6)
        self.entry.bind("<Return>", lambda e: self.add())
        row = ttk.Frame(self)
        row.pack(fill="x")
        ttk.Button(row, text="Додати", command=self.add).pack(side="left", expand=True, fill="x")
        ttk.Button(row, text="Видалити", command=self.remove).pack(side="left", expand=True, fill="x")
        self.load()

    def load(self):
        rows = repo.items(self.kind)
        self.ids = [r[0] for r in rows]
        self.lb.delete(0, "end")
        for _, name in rows:
            self.lb.insert("end", name)

    def add(self):
        name = self.entry.get().strip()
        if not name:
            return
        try:
            repo.add_item(self.kind, name)
        except ValueError as e:
            messagebox.showwarning("Увага", str(e))
            return
        self.entry.delete(0, "end")
        self.load()

    def remove(self):
        sel = self.lb.curselection()
        if not sel:
            return
        item_id = self.ids[sel[0]]
        if repo.in_use(self.kind, item_id):
            messagebox.showwarning("Увага", "Запис використовується в анкетах, видалити його не можна")
            return
        repo.delete_item(self.kind, item_id)
        self.load()


class DirectoriesTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.panels = [
            DirectoryPanel(self, "Викладачі", "teachers"),
            DirectoryPanel(self, "Дисципліни", "subjects"),
            DirectoryPanel(self, "Групи", "groups"),
        ]
        for i, p in enumerate(self.panels):
            p.grid(row=0, column=i, sticky="nsew", padx=6)
            self.columnconfigure(i, weight=1, uniform="dir")
        self.rowconfigure(0, weight=1)

    def reload(self):
        for p in self.panels:
            p.load()

class SurveyTab(ttk.Frame):
    def __init__(self, parent, user):
        super().__init__(parent, padding=24)
        self.user = user
        ttk.Label(self, text="Оцінювання якості освітніх послуг", font=("", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.teacher, self.subject, self.group = IdCombo(self, 40), IdCombo(self, 40), IdCombo(self, 40)
        for r, (label, cb) in enumerate([("Викладач", self.teacher), ("Дисципліна", self.subject),
                                         ("Група", self.group)], start=1):
            ttk.Label(self, text=label).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 20))
            cb.grid(row=r, column=1, sticky="w", pady=4)

        ttk.Label(self, text="Оцініть за шкалою від 1 (дуже погано) до 5 (відмінно):").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(16, 6))
        self.scores = []
        for i, name in enumerate(CRITERIA):
            var = tk.IntVar(value=5)
            ttk.Label(self, text=name).grid(row=5 + i, column=0, sticky="w", pady=3, padx=(0, 20))
            ttk.Spinbox(self, from_=1, to=5, textvariable=var, width=5, state="readonly").grid(
                row=5 + i, column=1, sticky="w")
            self.scores.append(var)

        ttk.Label(self, text="Коментар").grid(row=11, column=0, sticky="nw", pady=10)
        self.comment = tk.Text(self, width=48, height=4)
        self.comment.grid(row=11, column=1, sticky="w", pady=10)
        ttk.Button(self, text="Зберегти анкету", command=self.save).grid(row=12, column=1, sticky="w")

    def reload(self):
        self.teacher.set_items(repo.items("teachers"))
        self.subject.set_items(repo.items("subjects"))
        self.group.set_items(repo.items("groups"))

    def save(self):
        t, s, g = self.teacher.selected_id(), self.subject.selected_id(), self.group.selected_id()
        if None in (t, s, g):
            messagebox.showwarning("Увага", "Заповніть усі поля вибору")
            return
        student_id = self.user.id if self.user.role == "student" else None
        try:
            repo.save_survey(student_id, t, s, g, self.comment.get("1.0", "end").strip(),
                             [v.get() for v in self.scores])
        except ValueError as e:
            messagebox.showwarning("Увага", str(e))
            return
        self.comment.delete("1.0", "end")
        for v in self.scores:
            v.set(5)
        messagebox.showinfo("Готово", "Дякуємо! Анкету збережено")

class ResultsTab(ttk.Frame):
    TAGS = {"Високий": "#d7f0e0", "Достатній": "#dbe8fd", "Середній": "#fdecc8", "Низький": "#fbd5d5"}

    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.stats = []
        self.bar = FilterBar(self, self.refresh)
        self.bar.pack(fill="x")

        cols = ["teacher", "n"] + [f"k{i + 1}" for i in range(len(CRITERIA))] + ["avg", "level"]
        heads = ["Викладач", "Анкет"] + [f"К{i + 1}" for i in range(len(CRITERIA))] + ["Середній", "Рівень"]
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=9, selectmode="browse")
        for c, h in zip(cols, heads):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=170 if c in ("teacher", "level") else 70, anchor="center")
        for lvl, color in self.TAGS.items():
            self.tree.tag_configure(lvl, background=color)
        self.tree.pack(fill="x", pady=(6, 4))
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.load_comments())

        legend = "   ".join(f"К{i + 1} - {n}" for i, n in enumerate(CRITERIA))
        ttk.Label(self, text=legend, foreground="#555555", wraplength=1000).pack(anchor="w")

        box = ttk.LabelFrame(self, text="Коментарі студентів (оберіть викладача в таблиці)", padding=6)
        box.pack(fill="both", expand=True, pady=6)
        self.comments = tk.Listbox(box, height=6)
        self.comments.pack(fill="both", expand=True)

        ttk.Button(self, text="Експорт у CSV", command=self.export_csv).pack(anchor="e")

    def reload(self):
        self.bar.reload()
        self.refresh()

    def refresh(self):
        f = self.bar.current()
        if f is None:
            return
        self.stats = analytics.teacher_stats(f)
        self.tree.delete(*self.tree.get_children())
        for s in self.stats:
            lvl = analytics.level(s.avg)
            values = [s.name, s.surveys] + [f"{x:.2f}" for x in s.scores] + [f"{s.avg:.2f}", lvl]
            self.tree.insert("", "end", iid=str(s.teacher_id), values=values, tags=(lvl,))
        self.load_comments()

    def load_comments(self):
        self.comments.delete(0, "end")
        sel = self.tree.selection()
        if not sel:
            return
        f = self.bar.current()
        if f is None:
            return
        for line in analytics.comments(f, int(sel[0])):
            self.comments.insert("end", line)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="report.csv",
                                            filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["Викладач", "Анкет"] + CRITERIA + ["Середній", "Рівень"])
            for s in self.stats:
                w.writerow([s.name, s.surveys] + [f"{x:.2f}" for x in s.scores]
                           + [f"{s.avg:.2f}", analytics.level(s.avg)])
        messagebox.showinfo("Готово", "Файл збережено")

class AnalyticsTab(ttk.Frame):
    MODES = ["Рейтинг викладачів", "Середні оцінки за критеріями", "Динаміка по місяцях"]

    def __init__(self, parent):
        super().__init__(parent, padding=8)
        self.bar = FilterBar(self, self.draw)
        self.bar.pack(fill="x")

        row = ttk.Frame(self, padding=(6, 0))
        row.pack(fill="x")
        ttk.Label(row, text="Показати:").pack(side="left", padx=(0, 4))
        self.mode = ttk.Combobox(row, state="readonly", values=self.MODES, width=30)
        self.mode.current(0)
        self.mode.pack(side="left", padx=(0, 14))
        ttk.Label(row, text="Викладач (для динаміки):").pack(side="left", padx=(0, 4))
        self.teacher = IdCombo(row, 24)
        self.teacher.pack(side="left")
        self.mode.bind("<<ComboboxSelected>>", lambda e: self.draw())
        self.teacher.bind("<<ComboboxSelected>>", lambda e: self.draw())

        self.summary = ttk.Label(self, font=("", 10, "bold"), padding=(6, 8))
        self.summary.pack(fill="x")
        self.chart = ChartCanvas(self)
        self.chart.pack(fill="both", expand=True)

    def reload(self):
        self.bar.reload()
        self.teacher.set_items(repo.items("teachers"), "Усі викладачі")
        self.draw()

    def draw(self):
        f = self.bar.current()
        if f is None:
            return
        idx = self.mode.current()
        self.teacher.configure(state="readonly" if idx == 2 else "disabled")
        count, avg = analytics.summary(f)
        self.summary.config(text="Немає анкет за обраними фільтрами" if count == 0 else
                            f"Анкет: {count}     Загальний середній бал: {avg:.2f}     "
                            f"Рівень якості: {analytics.level(avg)}")
        if idx == 0:
            self.chart.show_bars([(s.name, s.avg) for s in analytics.teacher_stats(f)],
                                 "Рейтинг викладачів (середня оцінка, 1-5)")
        elif idx == 1:
            self.chart.show_bars(list(zip(CRITERIA, analytics.criteria_averages(f))),
                                 "Середні оцінки за критеріями (1-5)")
        else:
            self.chart.show_line(analytics.monthly(f, self.teacher.selected_id()),
                                 "Динаміка якості по місяцях (середня оцінка, 1-5)")

class UsersTab(ttk.Frame):
    def __init__(self, parent, me):
        super().__init__(parent, padding=8)
        self.me = me
        self.login = tk.StringVar()
        self.name = tk.StringVar()
        self.password = tk.StringVar()
        self.role_ua_to_key = {v: k for k, v in ROLE_UA.items()}

        form = ttk.Frame(self)
        form.pack(fill="x", pady=(0, 8))
        ttk.Label(form, text="Логін:").pack(side="left", padx=(0, 4))
        ttk.Entry(form, textvariable=self.login, width=12).pack(side="left", padx=(0, 10))
        ttk.Label(form, text="ПІБ:").pack(side="left", padx=(0, 4))
        ttk.Entry(form, textvariable=self.name, width=24).pack(side="left", padx=(0, 10))
        ttk.Label(form, text="Пароль:").pack(side="left", padx=(0, 4))
        ttk.Entry(form, textvariable=self.password, width=12, show="*").pack(side="left", padx=(0, 10))
        ttk.Label(form, text="Роль:").pack(side="left", padx=(0, 4))
        self.role = ttk.Combobox(form, state="readonly", width=14,
                                 values=[ROLE_UA["student"], ROLE_UA["methodist"], ROLE_UA["admin"]])
        self.role.current(0)
        self.role.pack(side="left", padx=(0, 10))
        ttk.Button(form, text="Додати", command=self.add).pack(side="left")

        self.tree = ttk.Treeview(self, columns=("login", "name", "role"), show="headings", selectmode="browse")
        for c, h, w in [("login", "Логін", 150), ("name", "ПІБ", 300), ("role", "Роль", 150)]:
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True)
        ttk.Button(self, text="Видалити обраного користувача", command=self.delete).pack(fill="x", pady=(8, 0))

    def reload(self):
        self.tree.delete(*self.tree.get_children())
        for uid, login, name, role in repo.users():
            self.tree.insert("", "end", iid=str(uid), values=(login, name, ROLE_UA.get(role, role)))

    def add(self):
        login, name, pw = self.login.get().strip(), self.name.get().strip(), self.password.get()
        if not login or not name:
            messagebox.showwarning("Увага", "Вкажіть логін і ПІБ")
            return
        if len(pw) < 6:
            messagebox.showwarning("Увага", "Пароль має містити щонайменше 6 символів")
            return
        try:
            repo.add_user(login, name, pw, self.role_ua_to_key[self.role.get()])
        except ValueError as e:
            messagebox.showwarning("Увага", str(e))
            return
        self.login.set("")
        self.name.set("")
        self.password.set("")
        self.reload()

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            return
        if int(sel[0]) == self.me.id:
            messagebox.showwarning("Увага", "Не можна видалити власний обліковий запис")
            return
        if messagebox.askyesno("Підтвердження", "Видалити користувача?"):
            repo.delete_user(int(sel[0]))
            self.reload()
