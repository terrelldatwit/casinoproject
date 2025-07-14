import random
import tkinter as tk
from tkinter import messagebox

m = tk.Tk()
m.title('7s Frenzy')
m.geometry("400x400")

total_money = 100
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

    result_label.config(text=" | ".join(symbols))

    win = 0

    if (numbers[0] == numbers[1]) or (numbers[1] == numbers[2]):
        match = numbers[1]
        multiplier = {
            1: 10,
            2: 8,
            3: 6,
            4: 5,
            5: 4,
            6: 3,
            7: 2
        }.get(match, 0)
        win = current_bet * multiplier

    if numbers[0] == numbers[1] == numbers[2]:
        match = numbers[0]
        multiplier = {
            1: 200,
            2: 100,
            3: 75,
            4: 50,
            5: 25,
            6: 20,
            7: 15
        }.get(match, 0)
        win = current_bet * multiplier
        result_label.config(text=result_label.cget("text") + "\n🎉 JACKPOT! 🎉")

    total_money += (win - current_bet)
    total_var.set(f"Total: ${total_money}")

tk.Button(m, text='Spin', width=25, command=spin_slots).pack(pady=5)
tk.Button(m, text='End', width=25, command=m.destroy).pack(pady=5)
tk.Label(m, textvariable=total_var, font=("Helvetica", 12, "bold")).pack(pady=10)

m.mainloop()
