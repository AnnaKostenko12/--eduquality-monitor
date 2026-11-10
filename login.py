"""Вікно входу в систему."""
import tkinter as tk
from tkinter import messagebox, ttk

import auth


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.result = None
        self.title("EduQuality Monitor - вхід")
        self.resizable(False, False)
        ttk.Style(self).theme_use("clam")

        frame = ttk.Frame(self, padding=24)
        frame.pack()
        ttk.Label(frame, text="Вхід до системи", font=("", 14, "bold")).grid(row=0, column=0, pady=(0, 12), sticky="w")
        ttk.Label(frame, text="Логін").grid(row=1, column=0, sticky="w")
        self.login = ttk.Entry(frame, width=34)
        self.login.grid(row=2, column=0, pady=(0, 10))
        ttk.Label(frame, text="Пароль").grid(row=3, column=0, sticky="w")
        self.password = ttk.Entry(frame, width=34, show="*")
        self.password.grid(row=4, column=0, pady=(0, 14))
        ttk.Button(frame, text="Увійти", command=self.try_login).grid(row=5, column=0, sticky="ew")
        ttk.Label(frame, text="Демо-доступ: admin / admin123", foreground="gray").grid(
            row=6, column=0, pady=(12, 0), sticky="w")

        self.bind("<Return>", lambda e: self.try_login())
        self.login.focus()
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 3
        self.geometry(f"+{x}+{y}")

    def try_login(self):
        user = auth.login(self.login.get().strip(), self.password.get())
        if user is None:
            messagebox.showwarning("Помилка входу", "Невірний логін або пароль")
            self.password.delete(0, "end")
            return
        self.result = user
        self.destroy()
