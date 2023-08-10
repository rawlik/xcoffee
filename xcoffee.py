import pywebio
import sqlite3
import hashlib
from functools import partial
from pywebio.input import actions, input, input_group, FLOAT, TEXT, PASSWORD
from pywebio.output import popup, close_popup, put_table, put_column, put_text, put_button, put_buttons, clear, put_info
from pywebio.pin import put_input
from pywebio_battery import popup_input, basic_auth, revoke_auth


price = 1.5
waterfraction = 0.2

def getusers():
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute("SELECT username, name, balance, total FROM users ORDER BY name ASC").fetchall()
    con.close()

    return res


def xcoffee(username=None):
    clear()
    put_column([
        put_table(
            [["", "Balance", "Total", ""]] + \
            [
                [
                    put_text(name),
                    put_text(f"{balance:.1f}"),
                    put_text(f"{total:.1f}"),
                    put_buttons([
                            dict(label="☕ on credit", value="☕", color="success"),
                            dict(label="☕ + 💰", value="☕ + 💰", color="success"),
                            dict(label="🚰", value="🚰", color="success"),
                            dict(label="🚰 + 💰", value="🚰 + 💰", color="success"),
                            dict(label="pay", value="pay", color="warning"),
                            # dict(label="delete", value="delete", color="danger")
                        ],
                        onclick=partial(rowaction, username=thisusername)) \
                    if thisusername == username else put_text("") ]
                for thisusername, name, balance, total in getusers()
            ]
        ),
        put_buttons(
            [
                dict(label="logout", value="logout", color="danger")
            ] if username is not None else \
            [
                dict(label="login", value="login", color="success"),
                dict(label="register", value="register", color="danger")
            ],
            onclick=homebutton
        ),
    ])


def rowaction(action, username):
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()

    if action == "☕":
        cur.execute(f"UPDATE users SET balance = balance + 1 WHERE username = '{username}'")
        cur.execute(f"UPDATE users SET total = total + 1 WHERE username = '{username}'")
    elif action == "☕ + 💰":
        popup(
            title=f"{username} is paying for coffee",
            content=put_column([
                put_text(f"Please put {price:.2f}Fr (or {price / 2:.2f}Fr into the cash box."),
                put_buttons(
                    [ dict(label="paid", value="paid", color="success"),
                     dict(label="cancel", value="cancel", color="danger")],
                     onclick=partial(drinkandpaypopupaction, username=username, n=1))]))
    elif action == "🚰":
        cur.execute(f"UPDATE users SET balance = balance + {waterfraction} WHERE username = '{username}'")
        cur.execute(f"UPDATE users SET total = total + {waterfraction} WHERE username = '{username}'")
    elif action == "🚰 + 💰":
        popup(
            title=f"{username} is paying for coffee",
            content=put_column([
                put_text(f"Please put {price * waterfraction:.2f}Fr (or {price * waterfraction / 2:.2f}Fr if you are a student) into the cash box."),
                put_buttons(
                    [ dict(label="paid", value="paid", color="success"),
                     dict(label="cancel", value="cancel", color="danger")],
                     onclick=partial(drinkandpaypopupaction, username=username, n=waterfraction))]))
    elif action == "pay":
        balance = cur.execute(f"SELECT balance FROM users WHERE username = '{username}'").fetchone()[0]

    con.commit()
    con.close()

    if action == "pay":
        popup(
            title=f"{username} is paying for coffee",
            content=put_column([
                put_text(f"Please twint {balance * price:.2f}Fr (or {balance * price / 2:.2f}Fr if you are a student) to Michał (+41 76 787 22 83)."),
                put_buttons(
                    [ dict(label="paid", value="paid", color="success"),
                     dict(label="cancel", value="cancel", color="danger")],
                     onclick=partial(paypopupaction, username=username, n=balance))]))
    else:
        xcoffee(username)


def drinkandpaypopupaction(action, username, n=1):
    if action == "cancel":
        close_popup()
    if action == "paid":
        con = sqlite3.connect("xcoffee.db")
        cur = con.cursor()
        cur.execute(f"UPDATE users SET total = total + {n} WHERE username = '{username}'")
        con.commit()
        con.close()
        close_popup()
        xcoffee(username)


def paypopupaction(action, username, n=1):
    if action == "cancel":
        close_popup()
    if action == "paid":
        con = sqlite3.connect("xcoffee.db")
        cur = con.cursor()
        cur.execute(f"UPDATE users SET balance = balance - {n} WHERE username = '{username}'")
        con.commit()
        con.close()
        close_popup()
        xcoffee(username)


def hashpass(password):
    return hashlib.blake2b(password.encode()).hexdigest()


def checkauth(username, password):
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute(f"SELECT password FROM users WHERE username='{username}'")
    res = res.fetchone()
    if res is None:
        return False
    con.close()
    return res[0] == hashpass(password)


def homebutton(action):
    if action == "login":
        clear()
        username = basic_auth(checkauth, secret="aslkdjflksajdflkj", expire_days=60, token_name="xcoffee")
        xcoffee(username)

    elif action == "register":
        form = popup_input(
            [
                put_input("username", label="username"),
                put_input("name", label="display name"),
                put_input("password", type=PASSWORD, label="password"),
                put_text("If you forget your password, please contact Michał."),
            ],
            title="Register"
        )
        clear()
        username = form["username"]
        name = form["name"]
        password = hashpass(form["password"])
        print("PASS: ", password)

        con = sqlite3.connect("xcoffee.db")
        cur = con.cursor()
        res = cur.execute(f"SELECT name FROM users WHERE username='{username}'").fetchone()
        if res is None:
            cur.execute(f"INSERT INTO users VALUES ('{username}', '{name}', '{password}', 0, 0)")
            con.commit()
            put_text("Successfully registered.")
        else:
            put_text("User already exists.")

        con.close()
        actions(buttons=["okay"])
        xcoffee()
    elif action == "logout":
        revoke_auth()
        xcoffee()


if __name__ == '__main__':
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='users'")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE users(username, name, password, balance, total)")
    con.close()

    pywebio.start_server(xcoffee, port=8080, debug=True)
