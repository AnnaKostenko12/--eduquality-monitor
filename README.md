# Курсова робота - EduQuality Monitor. Костенко Анна - 44 група
АІС моніторингу якості освітніх послуг закладу. Python 3.8+, Tkinter, SQLite - без сторонніх бібліотек.

## Запуск
    python main.py

(на Linux, якщо немає Tkinter: sudo apt install python3-tk)

## Демо-акаунти
| Логін     | Пароль     | Роль          |
|-----------|------------|---------------|
| admin     | admin123   | Адміністратор |
| methodist | method123  | Методист      |
| student   | student123 | Студент       |

## Структура
- main.py - точка входу, цикл входу/виходу
- config.py - критерії, ролі, прапорець демо-даних (SEED_DEMO)
- database.py - SQLite, схема
- auth.py - PBKDF2-хеші паролів, вхід
- repo.py - довідники, користувачі, збереження анкет
- analytics.py - середні оцінки, рівні якості, динаміка, коментарі
- seed.py - демо-дані
- widgets.py - IdCombo, FilterBar, ChartCanvas
- tabs.py - вкладки (Довідники, Анкета, Результати, Аналітика, Користувачі)
- login.py, app.py - вікно входу та головне вікно

Щоб скинути дані - видаліть quality.db.
