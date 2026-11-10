"""Власні віджети: список з id, панель фільтрів, діаграма на Canvas."""
import datetime
import tkinter as tk
import tkinter.font as tkfont
from tkinter import messagebox, ttk

import analytics
import repo
from analytics import Filter


class IdCombo(ttk.Combobox):
    """Combobox, що зберігає відповідність 'назва -> id'."""

    def __init__(self, parent, width=30):
        super().__init__(parent, state="readonly", width=width)
        self._map = {}

    def set_items(self, items, all_text=None):
        prev = self.get()
        self._map = {}
        names = []
        if all_text:
            names.append(all_text)
            self._map[all_text] = None
        for item_id, name in items:
            names.append(name)
            self._map[name] = item_id
        self["values"] = names
        self.set(prev if prev in self._map else (names[0] if names else ""))

    def selected_id(self):
        return self._map.get(self.get())


class FilterBar(ttk.Frame):
    """Фільтри: дисципліна, група, період."""

    def __init__(self, parent, on_apply):
        super().__init__(parent, padding=(6, 6))
        today = datetime.date.today()
        self.subject = IdCombo(self, 22)
        self.group = IdCombo(self, 14)
        self.d_from = tk.StringVar(value=(today - datetime.timedelta(days=365)).isoformat())
        self.d_to = tk.StringVar(value=today.isoformat())

        ttk.Label(self, text="Дисципліна:").pack(side="left", padx=(0, 4))
        self.subject.pack(side="left", padx=(0, 10))
        ttk.Label(self, text="Група:").pack(side="left", padx=(0, 4))
        self.group.pack(side="left", padx=(0, 10))
        ttk.Label(self, text="З:").pack(side="left", padx=(0, 4))
        ttk.Entry(self, textvariable=self.d_from, width=11).pack(side="left", padx=(0, 10))
        ttk.Label(self, text="По:").pack(side="left", padx=(0, 4))
        ttk.Entry(self, textvariable=self.d_to, width=11).pack(side="left", padx=(0, 10))
        ttk.Button(self, text="Застосувати", command=on_apply).pack(side="left")

    def reload(self):
        self.subject.set_items(repo.items("subjects"), "Усі")
        self.group.set_items(repo.items("groups"), "Усі")

    def current(self):
        """Повертає Filter або None, якщо дати введено неправильно."""
        d_from, d_to = self.d_from.get().strip(), self.d_to.get().strip()
        try:
            datetime.date.fromisoformat(d_from)
            datetime.date.fromisoformat(d_to)
        except ValueError:
            messagebox.showwarning("Увага", "Дата має бути у форматі РРРР-ММ-ДД, наприклад 2026-09-01")
            return None
        return Filter(self.subject.selected_id(), self.group.selected_id(), d_from, d_to)


class ChartCanvas(tk.Canvas):
    """Діаграма: горизонтальні стовпці або лінія динаміки."""

    def __init__(self, parent):
        super().__init__(parent, bg="white", highlightthickness=1, highlightbackground="#cccccc")
        self._data, self._line, self._title = [], False, ""
        self._bold = tkfont.nametofont("TkDefaultFont").copy()
        self._bold.configure(weight="bold")
        self.bind("<Configure>", lambda e: self.redraw())

    def show_bars(self, data, title):
        self._data, self._line, self._title = list(data), False, title
        self.redraw()

    def show_line(self, data, title):
        self._data, self._line, self._title = list(data), True, title
        self.redraw()

    def redraw(self):
        self.delete("all")
        self.create_text(10, 8, anchor="nw", text=self._title, font=self._bold)
        if not self._data:
            self.create_text(10, 40, anchor="nw", fill="gray", text="Немає даних за обраними фільтрами")
            return
        (self._draw_line if self._line else self._draw_bars)()

    def _draw_bars(self):
        w, h = self.winfo_width(), self.winfo_height()
        left, top, right, n = 250, 55, 70, len(self._data)
        span = w - left - right
        if span < 50:
            return
        row_h = max(24, min(60, (h - top - 20) // n))
        bar_h = row_h * 2 // 3
        for k in range(6):
            x = left + span * k / 5
            self.create_line(x, top - 6, x, top + n * row_h, fill="#e5e5e5")
            self.create_text(x, top - 18, text=str(k), fill="gray")
        for i, (label, value) in enumerate(self._data):
            y = top + i * row_h + (row_h - bar_h) / 2
            bar_w = span * value / 5
            text = label if len(label) <= 34 else label[:33] + "…"
            self.create_text(left - 10, y + bar_h / 2, anchor="e", text=text)
            self.create_rectangle(left, y, left + bar_w, y + bar_h, fill=analytics.level_color(value), width=0)
            self.create_text(left + bar_w + 8, y + bar_h / 2, anchor="w", text=f"{value:.2f}")

    def _draw_line(self):
        w, h = self.winfo_width(), self.winfo_height()
        l, t, r, b = 60, 55, 30, 50
        pw, ph = w - l - r, h - t - b
        if pw < 60 or ph < 60:
            return
        for k in range(6):
            y = t + ph - ph * k / 5
            self.create_line(l, y, l + pw, y, fill="#e5e5e5")
            self.create_text(l - 14, y, text=str(k), fill="gray")
        n = len(self._data)
        pts = []
        for i, (label, value) in enumerate(self._data):
            x = l + pw / 2 if n == 1 else l + pw * i / (n - 1)
            pts.append((x, t + ph - ph * value / 5))
        if n > 1:
            self.create_line(*[c for p in pts for c in p], fill="#3b82f6", width=3)
        for (x, y), (label, value) in zip(pts, self._data):
            self.create_oval(x - 5, y - 5, x + 5, y + 5, fill="white", outline="#3b82f6", width=2)
            self.create_text(x, y - 16, text=f"{value:.2f}")
            self.create_text(x, t + ph + 16, text=label, fill="gray")
