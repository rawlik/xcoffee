import pywebio
import sqlite3
import hashlib
from functools import partial
from pywebio.input import actions, input, FLOAT, TEXT, PASSWORD
from pywebio.output import popup, close_popup, put_table, put_column, put_text, put_buttons, clear, put_markdown, put_collapse
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

def gettotalbalance():
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute("SELECT SUM(balance) FROM users").fetchone()[0]
    con.close()

    return res

def gettotal():
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute("SELECT SUM(total) FROM users").fetchone()[0]
    con.close()

    return res



def xcoffee(username=None):
    clear()
    put_markdown(f"""
            # The coffee machine of the x-ray imaging group
            **DO NOT CHANGE ANY SETTINGS ON THE GRINDER AND THE MACHINE!**

            A coffee is {price:.2f}Fr, a cup of hot water {price * waterfraction:.2f}Fr.
        """)
    put_collapse("Manual",
        put_markdown("""
                ## Grind
                1. Put the porta filter on the grinder's fork. All the way in, so that it presses the button. One press is start. The second is stop.
                2. Wait for the grinding to finish. You don't need to hold the porta filter during the process.
                3. Place the porta filter on the mat, and use the tamper to get a nice, flat surface.

                ## Brew
                4. Put the porta filter in the coffee machine at 8 o'clock and twist it to 6 o'clock.
                5. For a less strong coffee (americano), fill it with water from the water spout before brewing the coffee.
                6. **Shortly** flip the second switch from the left down. **Do not hold it** (holding programmes the amount of water).

                ## Clean
                7. Take out the porta filter, and dump the grounds into the knock box.
                8. Flip the second switch **shortly** up to flush the grouphead.
                9. Clean the porta filter under the faucet.
            """))
    put_markdown("# Pay")
    if username is None:
        put_buttons([
                dict(label="login", value="login", color="success"),
                dict(label="register", value="register", color="primary")
            ],
            onclick=rowaction)
    else:
        put_buttons([
                dict(label="☕ on credit", value="☕", color="success"),
                dict(label="☕ for cash", value="☕ + 💰", color="success"),
                dict(label="🚰 on credit 💰", value="🚰", color="primary"),
                dict(label="🚰 for cash 💰", value="🚰 + 💰", color="primary"),
                dict(label="pay credit", value="pay", color="warning"),
                dict(label="logout", value="logout", color="danger")
                # dict(label="delete", value="delete", color="danger")
            ],
            onclick=partial(rowaction, username=username))
    put_table(
        [["", "Balance", "Total"]] + \
        [
            [
                put_markdown(("**" if thisusername == username else "") + name + ("**" if thisusername == username else "")),
                put_text(f"{balance:.1f}"),
                put_text(f"{total:.1f}")
            ]
            for thisusername, name, balance, total in getusers()
        ] + \
        [["SUM", put_markdown(f"**{gettotalbalance():.0f}**"), put_markdown(f"**{gettotal():.0f}**")]]
    )


def rowaction(action, username=None):
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
        revoke_auth(token_name="xcoffee")
        xcoffee()

    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()

    if action == "☕":
        cur.execute(f"UPDATE users SET balance = balance + 1 WHERE username = '{username}'")
        cur.execute(f"UPDATE users SET total = total + 1 WHERE username = '{username}'")
    elif action == "☕ + 💰":
        popup(
            title=f"{username} is paying for coffee",
            content=put_column([
                put_text(f"Please put {price:.2f}Fr (or {price / 2:.2f}Fr if you are a student) into the cash box."),
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


if __name__ == '__main__':
    con = sqlite3.connect("xcoffee.db")
    cur = con.cursor()
    res = cur.execute("SELECT name FROM sqlite_master WHERE name='users'")
    if res.fetchone() is None:
        cur.execute("CREATE TABLE users(username, name, password, balance, total)")
    con.close()

    pywebio.start_server(xcoffee, port=5999)
