"""Головне вікно програми."""
import tkinter as tk
from tkinter import ttk

from config import ROLE_UA
from tabs import AnalyticsTab, DirectoriesTab, ResultsTab, SurveyTab, UsersTab


class App(tk.Tk):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.logged_out = False
        self.title("EduQuality Monitor - АІС моніторингу якості освітніх послуг")
        self.geometry("1100x700")
        self.minsize(900, 560)
        ttk.Style(self).theme_use("clam")

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Змінити користувача", command=self.logout)
        file_menu.add_command(label="Вихід", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.config(menu=menubar)

        ttk.Label(self, text=f"{user.full_name}  |  {ROLE_UA.get(user.role, user.role)}",
                  relief="sunken", anchor="w", padding=(8, 2)).pack(side="bottom", fill="x")

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        if user.role in ("admin", "methodist"):
            self.nb.add(DirectoriesTab(self.nb), text="Довідники")
            self.nb.add(ResultsTab(self.nb), text="Результати")
            self.nb.add(AnalyticsTab(self.nb), text="Аналітика")
        if user.role == "admin":
            self.nb.add(UsersTab(self.nb, user), text="Користувачі")
        if user.role == "student":
            self.nb.add(SurveyTab(self.nb, user), text="Анкета")

        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.reload_current())
        self.after(50, self.reload_current)

    def reload_current(self):
        name = self.nb.select()
        if name:
            widget = self.nametowidget(name)
            if hasattr(widget, "reload"):
                widget.reload()

    def logout(self):
        self.logged_out = True
        self.destroy()
