#Import os module to work with file paths
import os

#Import random module to shuffle and deal cards
import random

#Import tkinter for GUI components
import tkinter as tk

#Import sqlite3 to interact with the database
import sqlite3

#Import matplotlib components for graphing
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

#Import messagebox for popup alerts
from tkinter import messagebox

#Define the database path
DB_PATH = os.path.join(os.path.dirname(__file__), "CasinoDB.db")

#Function to build a numeric Blackjack deck
def build_deck_numeric():
    return [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4

#Function to deal a card from the deck
def deal_card(deck):
    return deck.pop()

#Function to calculate hand score with Ace handling
def calculate_score(hand):
    if sum(hand) == 21 and len(hand) == 2:
        return 0
    while sum(hand) > 21 and 11 in hand:
        hand[hand.index(11)] = 1
    return sum(hand)

#Function to compare scores and return result with multiplier
def compare(player_score, dealer_score):
    if player_score > 21:
        return "You bust! Dealer wins.", -1
    elif dealer_score > 21:
        return "Dealer busts! You win.", 1
    elif player_score == dealer_score:
        return "Push. It's a tie.", 0
    elif player_score == 0:
        return "Blackjack! You win.", 1.5
    elif dealer_score == 0:
        return "Dealer has Blackjack! You lose.", -1
    elif player_score > dealer_score:
        return "You win!", 1
    else:
        return "Dealer wins.", -1

#Set card image folder and card back file
CARD_IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "Cards")
CARD_BACK_FILENAME = "card_back.png"

#Load card back image
TK_BACK_IMAGE = None
try:
    for fname in os.listdir(CARD_IMAGE_FOLDER):
        if fname.lower() == CARD_BACK_FILENAME.lower():
            path = os.path.join(CARD_IMAGE_FOLDER, fname)
            TK_BACK_IMAGE = tk.PhotoImage(file=path)
            break
except:
    pass

#Map numeric values to card ranks
NUMERIC_TO_RANK = {1:"A", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7", 8:"8", 9:"9", 10:"10", 11:"A"}

#Define card suits and their symbols
SUIT_SYMBOL = {"clubs":"♣", "diamonds":"♦", "hearts":"♥", "spades":"♠"}
SUITS = ["clubs","diamonds","hearts","spades"]

#Main Blackjack game class
class Blackjack:
    def __init__(self, player_id, parent_menu=None):
        self.player_id = player_id
        self.parent_menu = parent_menu

        self.root = tk.Tk()
        self.root.title("Casino Blackjack")
        self.root.geometry("900x700")
        self.root.configure(bg="#2E7D32")

        self.full_name = self.fetch_player_name()
        self.balance = self.fetch_balance_from_db()

        self.bet = 0.0
        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        self.in_round = False

        # Get the next session number for a new game launch
        self.session_number = self.get_next_session_number()
        # Reset cumulative stats for this new game launch
        self.total_winnings = 0
        self.total_bets = 0
        self.wins = 0
        self.losses = 0

        self.setup_ui()
        # Ensure the balance display is updated after UI setup
        self.balance_var.set(f"{self.balance:.2f}")
        self.root.mainloop()

    def fetch_player_name(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                cur = conn.cursor()
                cur.execute("SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?", (self.player_id,))
                result = cur.fetchone()
                return result[0] if result else str(self.player_id)
        except Exception as e:
            print(f"Error fetching player name: {e}")
            return str(self.player_id)

    def fetch_balance_from_db(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                cur = conn.cursor()
                cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))
                result = cur.fetchone()
                return float(result[0]) if result else 100.0
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 100.0

    def setup_ui(self):
        top = tk.Frame(self.root, bg="#1B5D20", pady=10)
        top.pack(fill="x")
        tk.Button(top, text="Net Winnings", font=("Arial",14), command=self.plot_net_winnings).pack(side="left", padx=10)
        tk.Label(top, text="Balance:", font=("Arial",14), fg="white", bg="#1B5D20").pack(side="left", padx=10)

        # Changed from tk.Entry to tk.Label for balance display
        self.balance_var = tk.StringVar(value=f"{self.balance:.2f}")
        self.balance_label = tk.Label(top, width=8, font=("Arial",14), textvariable=self.balance_var, fg="white", bg="#1B5D20", anchor="w")
        self.balance_label.pack(side="left")

        tk.Label(top, text="Bet:", font=("Arial",14), fg="white", bg="#1B5D20").pack(side="left", padx=10)
        self.bet_entry = tk.Entry(top, width=8, font=("Arial",14))
        self.bet_entry.pack(side="left")
        self.deal_btn = tk.Button(top, text="Deal", font=("Arial",14), fg="white", bg="black", command=self.start_round)
        self.deal_btn.pack(side="left", padx=20)

        mid = tk.Frame(self.root, bg="#2E7D32", pady=10)
        mid.pack(fill="both", expand=True)
        tk.Label(mid, text="Dealer’s Hand:", font=("Arial",20,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(0,5))
        self.dealer_frame = tk.Frame(mid, bg="#2E7D32")
        self.dealer_frame.pack(anchor="n", pady=10)
        self.dealer_total = tk.StringVar(value="")
        tk.Label(mid, textvariable=self.dealer_total, font=("Arial",16,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(0,30))
        tk.Label(mid, text="Player’s Hand:", font=("Arial",20,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(72,5))
        self.player_frame = tk.Frame(mid, bg="#2E7D32")
        self.player_frame.pack(anchor="n", pady=10)
        self.player_total = tk.StringVar(value="")
        tk.Label(mid, textvariable=self.player_total, font=("Arial",16,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(0,20))

        bot = tk.Frame(self.root, bg="#1B5D20", pady=10)
        bot.pack(fill="x")
        self.hit_btn = tk.Button(bot, text="Hit", font=("Arial",14), fg="white", bg="black", state="disabled", command=self.hit)
        self.hit_btn.pack(side="left", padx=20)
        self.stand_btn = tk.Button(bot, text="Stand", font=("Arial",14), fg="white", bg="black", state="disabled", command=self.stand)
        self.stand_btn.pack(side="left", padx=10)
        self.exit_btn = tk.Button(bot, text="Exit", font=("Arial",14), fg="white", bg="black", command=self.return_to_main)
        self.exit_btn.pack(side="right", padx=20)
        self.status_var = tk.StringVar(value="")
        tk.Label(bot, textvariable=self.status_var, font=("Arial",14), fg="white", bg="#1B5D20").pack(side="left", padx=20)

    def start_round(self):
        try:
            bet = float(self.bet_entry.get())
            if not (0 < bet <= self.balance):
                raise ValueError
        except ValueError:
            return messagebox.showerror("Invalid Bet", f"Bet must be >0 and ≤${self.balance:.2f}")
        except Exception as e:
            return messagebox.showerror("Error", f"An unexpected error occurred with bet input: {e}")

        self.bet = bet
        self.deck = build_deck_numeric()
        random.shuffle(self.deck)
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.in_round = True
        for f in (self.dealer_frame, self.player_frame):
            for w in f.winfo_children():
                w.destroy()
        self.status_var.set("")
        self.player_total.set("")
        self.dealer_total.set("")
        self.player_hand.extend([deal_card(self.deck), deal_card(self.deck)])
        self.dealer_hand.extend([deal_card(self.deck), deal_card(self.deck)])
        self._display(self.dealer_frame, self.dealer_hand, hide_first=True)
        self._display(self.player_frame, self.player_hand, hide_first=False)
        self.hit_btn.config(state="normal")
        self.stand_btn.config(state="normal")
        self.deal_btn.config(state="disabled")
        self.bet_entry.config(state="disabled")
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
        self._display(self.dealer_frame, self.dealer_hand, hide_first=False)
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

        # Update cumulative stats for the current session
        self.total_winnings += net
        self.total_bets += self.bet
        if net > 0:
            self.wins += 1
        elif net < 0:
            self.losses += 1

        self.hit_btn.config(state="disabled")
        self.stand_btn.config(state="disabled")
        if self.balance > 0:
            self.deal_btn.config(state="normal")
            self.bet_entry.config(state="normal")
        else:
            messagebox.showinfo("Game Over", "You’ve run out of money!")
        self.in_round = False
        self.log_blackjack_session() # Log the current session's cumulative stats

    def log_blackjack_session(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                cur = conn.cursor()

                # Attempt to update the existing session record first
                cur.execute("""
                    UPDATE Blackjack
                    SET number_of_bets = ?,
                        bet_amount = ?,
                        wins = ?,
                        losses = ?,
                        money_won = ?
                    WHERE player_name = ? AND session_number = ?
                """, (
                    self.wins + self.losses, # total rounds played in this session
                    self.total_bets,
                    self.wins,
                    self.losses,
                    self.total_winnings,
                    self.full_name,
                    self.session_number
                ))

                # If no rows were updated, it means this is a new session record to insert
                if cur.rowcount == 0:
                    cur.execute("""
                        INSERT INTO Blackjack (player_name, number_of_bets, bet_amount, wins, losses, money_won, session_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.full_name,
                        self.wins + self.losses,
                        self.total_bets,
                        self.wins,
                        self.losses,
                        self.total_winnings,
                        self.session_number
                    ))

                # Always update the PLAYERS table balance, bets, winnings, etc.
                cur.execute("""
                    UPDATE PLAYERS
                    SET balance = ?,
                        bets = bets + ?,
                        winnings = winnings + ?,
                        Won = Won + ?,
                        Lost = Lost + ?
                    WHERE ID = ?
                """, (
                    self.balance,
                    self.total_bets, # This will add to total bets in PLAYERS
                    self.total_winnings, # This will add to total winnings in PLAYERS
                    self.wins, # This will add to total Won in PLAYERS
                    self.losses, # This will add to total Lost in PLAYERS
                    self.player_id
                ))
                conn.commit()
        except Exception as e:
            print("DB Log Error:", e)
            messagebox.showerror("Database Error", f"Failed to log session: {e}")


    def return_to_main(self):
        self.root.destroy()  # Destroy the Tkinter root window
        if self.parent_menu:
            self.parent_menu.show()

    def get_next_session_number(self):
        """
        Determines the next session number for the player.
        This ensures a new session number for each game launch.
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                cur = conn.cursor()
                cur.execute("""
                    SELECT MAX(session_number)
                    FROM Blackjack
                    WHERE player_name=?
                """, (self.full_name,))
                result = cur.fetchone()
                # If there are existing sessions, return the max + 1. Otherwise, start with 1.
                return (result[0] or 0) + 1
        except Exception as e:
            print(f"Error fetching next session number: {e}")
            return 1 # Fallback to session 1 if an error occurs


    def plot_net_winnings(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                cur = conn.cursor()
                cur.execute("SELECT session_number, money_won FROM Blackjack WHERE player_name=? ORDER BY session_number", (self.full_name,))
                data = cur.fetchall()
                if not data:
                    return messagebox.showinfo("No Data", "No session data available.")
                sessions = [row[0] for row in data]
                winnings = [row[1] for row in data]
                fig = Figure(figsize=(5, 4), dpi=100)
                ax = fig.add_subplot(111)
                ax.plot(sessions, winnings, marker='o')
                ax.set_title("Net Winnings Over Sessions")
                ax.set_xlabel("Session")
                ax.set_ylabel("Net Winnings ($)")
                win = tk.Toplevel(self.root)
                win.title("Net Winnings")
                canvas = FigureCanvasTkAgg(fig, master=win)
                canvas.draw()
                canvas.get_tk_widget().pack()
        except Exception as e:
            messagebox.showerror("Plot Error", str(e))

    def _display(self, frame, hand, hide_first):
        for w in frame.winfo_children():
            w.destroy()
        for i, val in enumerate(hand):
            if i == 0 and hide_first:
                if TK_BACK_IMAGE:
                    lbl = tk.Label(frame, image=TK_BACK_IMAGE, bg="#2E7D32")
                    lbl.image = TK_BACK_IMAGE
                else:
                    lbl = tk.Label(frame, text="?", font=("Arial",32), fg="red", bg="white", width=4, height=2, relief="raised", bd=2)
                lbl.pack(side="left", padx=10)
            else:
                rank = NUMERIC_TO_RANK[val]
                suit = random.choice(SUITS)
                symbol = SUIT_SYMBOL[suit]
                txt = rank + symbol
                lbl = tk.Label(frame, text=txt, font=("Arial",32), fg="red", bg="white", width=4, height=2, relief="raised", bd=2)
                lbl.pack(side="left", padx=10)
