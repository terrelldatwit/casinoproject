import random
import sqlite3
import tkinter as tk
from tkinter import messagebox

DB_PATH = "CasinoDB.db"
current_user = 1056 
total_money = 0  

def load_balance_from_db():
    global total_money
    total_money = 0 
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM PLAYERS WHERE ID = ?", (current_user,))
        result = cursor.fetchone()
        if result:
            total_money = result[0]
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Could not load balance: {e}")

def update_balance_in_db(new_balance):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE PLAYERS SET balance = ? WHERE ID = ?", (new_balance, current_user))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Could not update balance: {e}")

load_balance_from_db()

m = tk.Tk()
m.title('7s Frenzy')
m.geometry("400x400")

total_var = tk.StringVar()
total_var.set(f"Total: ${total_money}")

result_label = tk.Label(m, text="", font=("Helvetica", 14))
result_label.pack(pady=10)

tk.Label(m, text="Enter your bet:").pack()
bet_entry = tk.Entry(m)
bet_entry.pack()

def get_symbol(number):
    return {
        1: "7",
        2: "bar",
        3: "bar-bar",
        4: "bar-bar-bar",
        5: "cherry",
        6: "lemon",
        7: "grape"
    }.get(number, "")

def spin_slots():
    global total_money
    try:
        current_bet = int(bet_entry.get())
        if current_bet <= 0:
            raise ValueError
        if current_bet > total_money:
            messagebox.showerror("Error", "You don't have enough money to bet that amount.")
            return
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid positive number.")
        return

    symbols = []
    numbers = []

    for _ in range(3):
        num = random.randint(1, 7)
        numbers.append(num)
        symbols.append(get_symbol(num))

    result_text = " | ".join(symbols)
    win = 0

    if (numbers[0] == numbers[1]) or (numbers[1] == numbers[2]):
        match = numbers[1]
        multiplier = {
            1: 2.5,
            2: 2.2,
            3: 2.0,
            4: 1.8,
            5: 1.6,
            6: 1.4,
            7: 1.2
        }.get(match, 0)
        win = int(current_bet * multiplier)

    if numbers[0] == numbers[1] == numbers[2]:
        match = numbers[0]
        multiplier = {
            1: 50,
            2: 30,
            3: 20,
            4: 15,
            5: 10,
            6: 8,
            7: 6
        }.get(match, 0)
        win = int(current_bet * multiplier)
        if multiplier == 200 | 100 | 75:
            result_text += " JACKPOT! "

    total_money += (win - current_bet)
    total_var.set(f"Total: ${total_money}")
    result_label.config(text=result_text)
    update_balance_in_db(total_money)

tk.Button(m, text='Spin', width=25, command=spin_slots).pack(pady=5)
tk.Button(m, text='End', width=25, command=m.destroy).pack(pady=5)
tk.Label(m, textvariable=total_var, font=("Helvetica", 12, "bold")).pack(pady=10)

m.mainloop()
