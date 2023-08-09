import pywebio
import sqlite3
from functools import partial
from pywebio.input import actions, input, FLOAT, TEXT
from pywebio.output import popup, close_popup, put_table, put_column, put_text, put_button, put_buttons, clear

price = 1.5

def getusers():
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute("SELECT * FROM users ORDER BY name ASC").fetchall()
    con.close()

    return res


def xcoffee():
    clear()
    put_table(
        [["User", "Balance", "Total", "Actions"]] + \
        [
            [
                put_text(s),
                put_text(f"{balance}"),
                put_text(f"{total}"),
                put_buttons(
                    [
                        dict(label="☕", value="☕", color="success"),
                        dict(label="pay", value="pay", color="warning"),
                        #dict(label="delete", value="delete", color="danger")
                    ],
                    onclick=partial(rowaction, user=s)) ]
            for s, balance, total in getusers()
        ] + \
        [[ put_button("add name", onclick=adduser)]])


def rowaction(action, user):
    if action == "☕":
        con = sqlite3.connect("xcoffee.db")
        cur = con.cursor()
        cur.execute(f"UPDATE users SET balance = balance + 1 WHERE name = '{user}'")
        cur.execute(f"UPDATE users SET total = total + 1 WHERE name = '{user}'")
        con.commit()
        con.close()
        xcoffee()
    elif action == "pay":
        con = sqlite3.connect("xcoffee.db")
        cur = con.cursor()
        balance = cur.execute(f"SELECT balance FROM users WHERE name = '{user}'").fetchone()[0]
        con.commit()
        con.close()
        popup(
            title=f"{user} is paying for coffee",
            content=put_column([
                put_text(f"Please twint {balance * price:.2f}Fr (or {balance * price / 2:.2f}Fr if you are a student) to Michał (+41 76 787 22 83)."),
                put_buttons(
                    [ dict(label="paid", value="paid", color="success"),
                     dict(label="cancel", value="cancel", color="danger")],
                     onclick=partial(paypopupaction, user=user))]))
    elif action == "delete":
        if input("Password?", type=TEXT) == "KooharkQuoba4":
            con = sqlite3.connect("xcoffee.db")
            cur = con.cursor()
            cur.execute(f"DELETE FROM users WHERE name = '{user}'")
            con.commit()
            con.close()
            xcoffee()


def paypopupaction(action, user):
    if action == "cancel":
        close_popup()
    if action == "paid":
        con = sqlite3.connect("xcoffee.db")
        cur = con.cursor()
        cur.execute(f"UPDATE users SET balance = 0 WHERE name = '{user}'")
        con.commit()
        con.close()
        close_popup()
        xcoffee()


def adduser():
    name = input("What is your name?", type=TEXT)
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute(f"SELECT name FROM users WHERE name='{name}'")
    if res.fetchone() is None:
        cur.execute(f"INSERT INTO users VALUES ('{name}', 0, 0)")
        con.commit()
    con.close()
    xcoffee()


if __name__ == '__main__':
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='users'")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE users(name, balance, total)")
    con.close()

    pywebio.start_server(xcoffee, port=8080, debug=True)
