import auth
import config
import database
import seed
from app import App
from login import LoginWindow


def main():
    database.init_schema()
    auth.ensure_admin()
    if config.SEED_DEMO:
        seed.seed_demo()

    while True:
        win = LoginWindow()
        win.mainloop()
        if win.result is None:
            break
        app = App(win.result)
        app.mainloop()
        if not app.logged_out:
            break


if __name__ == "__main__":
    main()
