# A simple script to calculate BMI
import pywebio
from functools import partial
from pywebio.input import actions, input, FLOAT, TEXT
from pywebio.output import popup, close_popup, put_table, put_column, put_text, put_button, put_buttons, clear

users = {"Michał": 0}
price = 1.5

def xcoffee():
    clear()
    put_table(
        [["User", "Balance", "Actions"]] + \
        [
            [
                put_text(s),
                f"{users[s]}",
                put_buttons(
                    [
                        dict(label="☕", value="☕", color="success"),
                        dict(label="pay", value="pay", color="warning"),
                        dict(label="delete", value="delete", color="danger")
                    ],
                    onclick=partial(rowaction, user=s)) ]
            for s in users
        ] + \
        [[ put_button("add name", onclick=adduser), put_text(""), put_text("")]])


def rowaction(action, user):
    if action == "☕":
        if user in users.keys():
            users[user] += 1
        xcoffee()
    elif action == "pay":
        popup(
            title=f"{user} is paying for coffee",
            content=put_column([
                put_text(f"Please twint {users[user] * price:.2f}Fr (or {users[user] * price / 2:.2f}Fr if you are a student) to Michał (+41 76 787 22 83)."),
                put_buttons(
                    [ dict(label="paid", value="paid", color="success"),
                     dict(label="cancel", value="cancel", color="danger")],
                     onclick=partial(paypopupaction, user=user))]))
    elif action == "delete":
        if input("Password?", type=TEXT) == "KooharkQuoba4":
            del users[user]
            xcoffee()

def paypopupaction(action, user):
    if action == "cancel":
        close_popup()
    if action == "paid":
        users[user] = 0
        close_popup()
        xcoffee()


def adduser():
    name = input("What is your name?", type=TEXT)
    if name not in users.keys():
        users[name] = 0
    xcoffee()


if __name__ == '__main__':
    xcoffee()
