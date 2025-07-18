# gui.py

import os
import random
import tkinter as tk
from tkinter import messagebox

from blackjack import deal_card, calculate_score, compare, build_deck_numeric


BASE_DIR           = os.path.dirname(__file__)
CARD_IMAGE_FOLDER  = os.path.join(BASE_DIR, "Cards")
CARD_BACK_FILENAME = "card_back.png"

print("Looking in:", CARD_IMAGE_FOLDER)
try:
    files = os.listdir(CARD_IMAGE_FOLDER)
    print("Found files:", files)
except FileNotFoundError:
    print("ERROR: 'Cards/' folder not found.")
    files = []

TK_BACK_IMAGE = None
for fname in files:
    if fname.lower() == CARD_BACK_FILENAME.lower():
        path = os.path.join(CARD_IMAGE_FOLDER, fname)
        try:
            TK_BACK_IMAGE = tk.PhotoImage(file=path)
            print("Loaded hole-card image:", fname)
        except tk.TclError:
            print("Could not load hole-card image:", fname)
        break
if TK_BACK_IMAGE is None:
    print("Hole-card image not found; using '?' instead.")

NUMERIC_TO_RANK = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"10",11:"A"}
SUIT_SYMBOL     = {"clubs":"♣","diamonds":"♦","hearts":"♥","spades":"♠"}
SUITS           = ["clubs","diamonds","hearts","spades"]

class BlackjackGUI:
    def __init__(self, root):
        self.root = root
        root.title("Casino Blackjack")
        root.geometry("900x700")
        root.configure(bg="#2E7D32")

        # Game state
        self.balance = 100.0
        self.bet     = 0.0
        self.deck    = []
        self.player_hand = []
        self.dealer_hand = []
        self.in_round    = False

        # Balance Entry, Bet, Deal 
        top = tk.Frame(root, bg="#1B5D20", pady=10)
        top.pack(fill="x")
        tk.Label(top, text="Balance:", font=("Arial",14), fg="white", bg="#1B5D20")\
          .pack(side="left", padx=10)
        self.balance_var = tk.StringVar(value=f"{self.balance:.2f}")
        self.balance_entry = tk.Entry(top, width=8, font=("Arial",14),
                                      textvariable=self.balance_var)
        self.balance_entry.pack(side="left")
        tk.Label(top, text="Bet:", font=("Arial",14), fg="white", bg="#1B5D20")\
          .pack(side="left", padx=10)
        self.bet_entry = tk.Entry(top, width=8, font=("Arial",14))
        self.bet_entry.pack(side="left")
        self.deal_btn = tk.Button(top, text="Deal", font=("Arial",14),
                                  fg="white", bg="black",
                                  command=self.start_round)
        self.deal_btn.pack(side="left", padx=20)

        # Dealer & Player Hands 
        mid = tk.Frame(root, bg="#2E7D32", pady=10)
        mid.pack(fill="both", expand=True)

        # Dealer
        tk.Label(mid, text="Dealer’s Hand:", font=("Arial",20,"bold"),
                 fg="white", bg="#2E7D32").pack(anchor="n", pady=(0,5))
        self.dealer_frame = tk.Frame(mid, bg="#2E7D32")
        self.dealer_frame.pack(anchor="n", pady=10)
        self.dealer_total = tk.StringVar(value="")
        tk.Label(mid, textvariable=self.dealer_total,
                 font=("Arial",16,"bold"), fg="white", bg="#2E7D32")\
          .pack(anchor="n", pady=(0,30))

        # Player 
        tk.Label(mid, text="Player’s Hand:", font=("Arial",20,"bold"),
                 fg="white", bg="#2E7D32").pack(anchor="n", pady=(72,5))
        self.player_frame = tk.Frame(mid, bg="#2E7D32")
        self.player_frame.pack(anchor="n", pady=10)
        self.player_total = tk.StringVar(value="")
        tk.Label(mid, textvariable=self.player_total,
                 font=("Arial",16,"bold"), fg="white", bg="#2E7D32")\
          .pack(anchor="n", pady=(0,20))

        # Hit, Stand, Exit, Status 
        bot = tk.Frame(root, bg="#1B5D20", pady=10)
        bot.pack(fill="x")
        self.hit_btn = tk.Button(bot, text="Hit", font=("Arial",14),
                                 fg="white", bg="black", state="disabled",
                                 command=self.hit)
        self.hit_btn.pack(side="left", padx=20)
        self.stand_btn = tk.Button(bot, text="Stand", font=("Arial",14),
                                   fg="white", bg="black", state="disabled",
                                   command=self.stand)
        self.stand_btn.pack(side="left", padx=10)
        self.exit_btn = tk.Button(bot, text="Exit", font=("Arial",14),
                                  fg="white", bg="black",
                                  command=root.destroy)
        self.exit_btn.pack(side="right", padx=20)
        self.status_var = tk.StringVar(value="")
        tk.Label(bot, textvariable=self.status_var,
                 font=("Arial",14), fg="white", bg="#1B5D20")\
          .pack(side="left", padx=20)

    def start_round(self):
        
        try:
            self.balance = float(self.balance_var.get())
        except:
            return messagebox.showerror("Invalid Balance",
               "Please enter a numeric balance.")
        # Validate bet
        try:
            bet = float(self.bet_entry.get())
            if not (0 < bet <= self.balance):
                raise ValueError
        except:
            return messagebox.showerror("Invalid Bet",
               f"Bet must be >0 and ≤${self.balance:.2f}")
        self.bet = bet

        # Shuffle
        self.deck = build_deck_numeric()
        random.shuffle(self.deck)
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.in_round = True

        # Clear UI
        for f in (self.dealer_frame, self.player_frame):
            for w in f.winfo_children():
                w.destroy()
        self.status_var.set("")
        self.player_total.set("")
        self.dealer_total.set("")

        # Deal
        self.player_hand.extend([deal_card(self.deck), deal_card(self.deck)])
        self.dealer_hand.extend([deal_card(self.deck), deal_card(self.deck)])

        # Display
        self._display(self.dealer_frame, self.dealer_hand, hide_first=True)
        self._display(self.player_frame, self.player_hand, hide_first=False)

        # Buttons
        self.hit_btn.config(state="normal")
        self.stand_btn.config(state="normal")
        self.deal_btn.config(state="disabled")
        self.bet_entry.config(state="disabled")

        # Totals & status
        p = calculate_score(self.player_hand)
        self.player_total.set(str(p))
        self.dealer_total.set("?")
        self.status_var.set(f"Player: {p}   Dealer: ?")

        if p == 0 or p > 21:
            self.end_round()

    def hit(self):
        if not self.in_round:
            return
        self.player_hand.append(deal_card(self.deck))
        self._display(self.player_frame, self.player_hand, hide_first=False)
        p = calculate_score(self.player_hand)
        self.player_total.set(str(p))
        if p > 21:
            self.end_round()
        else:
            self.status_var.set(f"Player: {p}   Dealer: ?")

    def stand(self):
        if not self.in_round:
            return
        self.end_round()

    def end_round(self):
        # Reveal dealer
        self._display(self.dealer_frame, self.dealer_hand, hide_first=False)
        # Dealer draws to 17+
        d = calculate_score(self.dealer_hand)
        while 0 < d < 17:
            self.dealer_hand.append(deal_card(self.deck))
            self._display(self.dealer_frame, self.dealer_hand, hide_first=False)
            d = calculate_score(self.dealer_hand)

        
        p = calculate_score(self.player_hand)
        self.player_total.set(str(p))
        self.dealer_total.set(str(d))

        
        msg, mul = compare(p, d)
        net = mul * self.bet
        self.balance += net
        self.balance_var.set(f"{self.balance:.2f}")
        self.status_var.set(f"{msg} {'+' if net>0 else ''}${net:.2f}")

        
        self.hit_btn.config(state="disabled")
        self.stand_btn.config(state="disabled")
        if self.balance > 0:
            self.deal_btn.config(state="normal")
            self.bet_entry.config(state="normal")
        else:
            messagebox.showinfo("Game Over", "You’ve run out of money!")
        self.in_round = False

    def _display(self, frame, hand, hide_first):
        # Clear old
        for w in frame.winfo_children():
            w.destroy()
        for i, val in enumerate(hand):
            if i == 0 and hide_first:
                # Face-down
                if TK_BACK_IMAGE:
                    lbl = tk.Label(frame, image=TK_BACK_IMAGE, bg="#2E7D32")
                    lbl.image = TK_BACK_IMAGE
                else:
                    lbl = tk.Label(frame, text="?", font=("Arial",32),
                                   fg="red", bg="white",
                                   width=4, height=2,
                                   relief="raised", bd=2)
                lbl.pack(side="left", padx=10)
            else:
                # Face-up two-character label
                rank   = NUMERIC_TO_RANK[val]
                suit   = random.choice(SUITS)
                symbol = SUIT_SYMBOL[suit]
                txt    = rank + symbol
                lbl = tk.Label(frame, text=txt, font=("Arial",32),
                               fg="red", bg="white",
                               width=4, height=2,
                               relief="raised", bd=2)
                lbl.pack(side="left", padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    app  = BlackjackGUI(root)
    root.mainloop()
