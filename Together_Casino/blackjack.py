# Import os module to work with file paths
import os

# Import random module to shuffle and deal cards
import random

# Import tkinter for GUI components
import tkinter as tk

# Import sqlite3 to interact with the database
import sqlite3

# Import matplotlib components for graphing
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
# Import Figure class to create plots
from matplotlib.figure import Figure

# Import messagebox for popup alerts
from tkinter import messagebox

# Import the function to flag suspected cheaters
from cheaters import log_cheater

# Define the database path
DB_PATH = os.path.join(os.path.dirname(__file__), "CasinoDB.db")

# Function to build a numeric Blackjack deck
def build_deck_numeric():
    # Returns a list representing a standard deck of 52 cards,
    # where face cards (J, Q, K) are represented by 10, and Ace by 11.
    # The list is multiplied by 4 to represent four suits.
    return [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4

# Function to deal a card from the deck
def deal_card(deck):
    # Removes and returns the last card from the deck list.
    return deck.pop()

# Function to calculate hand score with Ace handling
def calculate_score(hand):
    # If the hand is a natural blackjack (21 with two cards), return 0 for special handling.
    if sum(hand) == 21 and len(hand) == 2:
        return 0
    # Loop while the hand total is over 21 and there's an Ace (11) in the hand.
    while sum(hand) > 21 and 11 in hand:
        # Change one Ace's value from 11 to 1 to reduce the total.
        hand[hand.index(11)] = 1
    # Return the final sum of the hand.
    return sum(hand)

# Function to compare scores and return result with multiplier
def compare(player_score, dealer_score):
    # If the player's score is over 21 (bust).
    if player_score > 21:
        return "You bust! Dealer wins.", -1
    # If the dealer's score is over 21 (bust).
    elif dealer_score > 21:
        return "Dealer busts! You win.", 1
    # If player and dealer scores are equal (push).
    elif player_score == dealer_score:
        return "Push. It's a tie.", 0
    # If the player has a Blackjack (score 0 indicates natural 21).
    elif player_score == 0:
        return "Blackjack! You win.", 1.5
    # If the dealer has a Blackjack (score 0 indicates natural 21).
    elif dealer_score == 0:
        return "Dealer has Blackjack! You lose.", -1
    # If the player's score is higher than the dealer's.
    elif player_score > dealer_score:
        return "You win!", 1
    # If none of the above, the dealer wins.
    else:
        return "Dealer wins.", -1

# Set card image folder path
CARD_IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "Cards")
# Define the filename for the card back image
CARD_BACK_FILENAME = "card_back.png"

# Initialize a variable to hold the Tkinter PhotoImage for the card back
TK_BACK_IMAGE = None
# Try to load the card back image
try:
    # Iterate through files in the card image folder
    for fname in os.listdir(CARD_IMAGE_FOLDER):
        # Check if the current filename matches the card back filename (case-insensitive)
        if fname.lower() == CARD_BACK_FILENAME.lower():
            # Construct the full path to the image file
            path = os.path.join(CARD_IMAGE_FOLDER, fname)
            # Load the image as a Tkinter PhotoImage
            TK_BACK_IMAGE = tk.PhotoImage(file=path)
            # Exit the loop once the image is found
            break
# Catch any exceptions that occur during image loading (e.g., file not found)
except:
    # Pass silently if an error occurs, TK_BACK_IMAGE will remain None
    pass

# Map numeric card values to their common rank symbols
NUMERIC_TO_RANK = {1:"A", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6", 7:"7", 8:"8", 9:"9", 10:"10", 11:"A"}

# Define card suits and their Unicode symbols
SUIT_SYMBOL = {"clubs":"♣", "diamonds":"♦", "hearts":"♥", "spades":"♠"}
# Define a list of available suits
SUITS = ["clubs","diamonds","hearts","spades"]

# Main Blackjack game class
class Blackjack:
    # Constructor for the Blackjack game
    def __init__(self, player_id, parent_menu=None):
        # Store the player's ID
        self.player_id = player_id
        # Store a reference to the parent menu (for returning)
        self.parent_menu = parent_menu

        # Create the main Tkinter window
        self.root = tk.Tk()
        # Set the window title
        self.root.title("Casino Blackjack")
        # Set the window dimensions
        self.root.geometry("900x700")
        # Set the background color of the window
        self.root.configure(bg="#2E7D32")

        # Fetch the player's full name from the database
        self.full_name = self.fetch_player_name()
        # Fetch the player's current balance from the database
        self.balance = self.fetch_balance_from_db()

        # Initialize the current bet amount
        self.bet = 0.0
        # Initialize an empty list for the game deck
        self.deck = []
        # Initialize empty lists for player's and dealer's hands
        self.player_hand = []
        self.dealer_hand = []
        # Flag to indicate if a round is currently in progress
        self.in_round = False

        # Get the next session number for this new game launch
        self.session_number = self.get_next_session_number()
        # Reset cumulative statistics for this new game launch
        self.total_winnings = 0
        # Reset total money bet in this session
        self.total_bets = 0
        # Reset total wins in this session
        self.wins = 0
        # Reset total losses in this session
        self.losses = 0
        # Initialize session history for cheater detection
        self.session_history = []

        # Set up the graphical user interface
        self.setup_ui()
        # Ensure the balance display is updated after UI setup
        self.balance_var.set(f"{self.balance:.2f}")
        # Start the Tkinter event loop
        self.root.mainloop()

    # Method to fetch the player's full name from the database
    def fetch_player_name(self):
        try:
            # Connect to the SQLite database
            with sqlite3.connect(DB_PATH) as conn:
                # Set journaling mode for better concurrency and performance
                conn.execute("PRAGMA journal_mode=WAL")
                # Create a cursor object to execute SQL queries
                cur = conn.cursor()
                # Execute a query to get the concatenated first and last name for the player ID
                cur.execute("SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?", (self.player_id,))
                # Fetch the first result
                result = cur.fetchone()
                # Return the full name if found, otherwise return the player ID as a string
                return result[0] if result else str(self.player_id)
        # Catch any exceptions during database operation
        except Exception as e:
            # Print the error to console
            print(f"Error fetching player name: {e}")
            # Return player ID as a string in case of error
            return str(self.player_id)

    # Method to fetch the player's balance from the database
    def fetch_balance_from_db(self):
        try:
            # Connect to the SQLite database
            with sqlite3.connect(DB_PATH) as conn:
                # Set journaling mode for better concurrency and performance
                conn.execute("PRAGMA journal_mode=WAL")
                # Create a cursor object
                cur = conn.cursor()
                # Execute a query to get the balance for the player ID
                cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))
                # Fetch the first result
                result = cur.fetchone()
                # Return the balance as a float if found, otherwise default to 100.0
                return float(result[0]) if result else 100.0
        # Catch any exceptions during database operation
        except Exception as e:
            # Print the error to console
            print(f"Error fetching balance: {e}")
            # Return default balance in case of error
            return 100.0

    # Method to set up the user interface
    def setup_ui(self):
        # Create a top frame for controls (Net Winnings, Balance, Bet, Deal buttons)
        top = tk.Frame(self.root, bg="#1B5D20", pady=10)
        # Pack the top frame to fill the width
        top.pack(fill="x")
        # Create a button to view net winnings graph
        tk.Button(top, text="Net Winnings", font=("Arial",14), command=self.plot_net_winnings).pack(side="left", padx=10)
        # Create a label for "Balance:"
        tk.Label(top, text="Balance:", font=("Arial",14), fg="white", bg="#1B5D20").pack(side="left", padx=10)

        # Create a StringVar to dynamically update the balance display
        self.balance_var = tk.StringVar(value=f"{self.balance:.2f}")
        # Create a label to display the player's balance (text-only)
        self.balance_label = tk.Label(top, width=8, font=("Arial",14), textvariable=self.balance_var, fg="white", bg="#1B5D20", anchor="w")
        # Pack the balance label
        self.balance_label.pack(side="left")

        # Create a label for "Bet:"
        tk.Label(top, text="Bet:", font=("Arial",14), fg="white", bg="#1B5D20").pack(side="left", padx=10)
        # Create an entry widget for the player to input their bet amount
        self.bet_entry = tk.Entry(top, width=8, font=("Arial",14))
        # Pack the bet entry widget
        self.bet_entry.pack(side="left")
        # Create the "Deal" button to start a new round
        self.deal_btn = tk.Button(top, text="Deal", font=("Arial",14), fg="white", bg="black", command=self.start_round)
        # Pack the deal button
        self.deal_btn.pack(side="left", padx=20)

        # Create a middle frame for dealer's and player's hands
        mid = tk.Frame(self.root, bg="#2E7D32", pady=10)
        # Pack the middle frame to fill and expand
        mid.pack(fill="both", expand=True)
        # Label for "Dealer’s Hand:"
        tk.Label(mid, text="Dealer’s Hand:", font=("Arial",20,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(0,5))
        # Frame to display dealer's cards
        self.dealer_frame = tk.Frame(mid, bg="#2E7D32")
        # Pack the dealer's card frame
        self.dealer_frame.pack(anchor="n", pady=10)
        # StringVar to display dealer's total score
        self.dealer_total = tk.StringVar(value="")
        # Label to display dealer's total score
        tk.Label(mid, textvariable=self.dealer_total, font=("Arial",16,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(0,30))
        # Label for "Player’s Hand:"
        tk.Label(mid, text="Player’s Hand:", font=("Arial",20,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(72,5))
        # Frame to display player's cards
        self.player_frame = tk.Frame(mid, bg="#2E7D32")
        # Pack the player's card frame
        self.player_frame.pack(anchor="n", pady=10)
        # StringVar to display player's total score
        self.player_total = tk.StringVar(value="")
        # Label to display player's total score
        tk.Label(mid, textvariable=self.player_total, font=("Arial",16,"bold"), fg="white", bg="#2E7D32").pack(anchor="n", pady=(0,20))

        # Create a bottom frame for game action buttons (Hit, Stand, Exit) and status messages
        bot = tk.Frame(self.root, bg="#1B5D20", pady=10)
        # Pack the bottom frame to fill the width
        bot.pack(fill="x")
        # Create the "Hit" button
        self.hit_btn = tk.Button(bot, text="Hit", font=("Arial",14), fg="white", bg="black", state="disabled", command=self.hit)
        # Pack the hit button
        self.hit_btn.pack(side="left", padx=20)
        # Create the "Stand" button
        self.stand_btn = tk.Button(bot, text="Stand", font=("Arial",14), fg="white", bg="black", state="disabled", command=self.stand)
        # Pack the stand button
        self.stand_btn.pack(side="left", padx=10)
        # Create the "Exit" button
        self.exit_btn = tk.Button(bot, text="Exit", font=("Arial",14), fg="white", bg="black", command=self.return_to_main)
        # Pack the exit button
        self.exit_btn.pack(side="right", padx=20)
        # StringVar to display game status messages
        self.status_var = tk.StringVar(value="")
        # Label to display game status messages
        tk.Label(bot, textvariable=self.status_var, font=("Arial",14), fg="white", bg="#1B5D20").pack(side="left", padx=20)

    # Method to start a new round of Blackjack
    def start_round(self):
        try:
            # Get the bet amount from the entry widget and convert to float
            bet = float(self.bet_entry.get())
            # Check if the bet is valid (greater than 0 and less than or equal to balance)
            if not (0 < bet <= self.balance):
                # Raise a ValueError if the bet is invalid
                raise ValueError
        # Handle ValueError for invalid bet amount
        except ValueError:
            # Show an error message box
            return messagebox.showerror("Invalid Bet", f"Bet must be >0 and ≤${self.balance:.2f}")
        # Catch any other unexpected exceptions
        except Exception as e:
            # Show a general error message box
            return messagebox.showerror("Error", f"An unexpected error occurred with bet input: {e}")

        # Set the current bet amount
        self.bet = bet
        # Build a new numeric deck
        self.deck = build_deck_numeric()
        # Shuffle the deck randomly
        random.shuffle(self.deck)
        # Clear both player's and dealer's hands
        self.player_hand.clear()
        self.dealer_hand.clear()
        # Set the in_round flag to True
        self.in_round = True
        # Destroy all existing card widgets in dealer's and player's frames
        for f in (self.dealer_frame, self.player_frame):
            for w in f.winfo_children():
                w.destroy()
        # Clear status messages and total scores
        self.status_var.set("")
        self.player_total.set("")
        self.dealer_total.set("")
        # Deal two cards to the player
        self.player_hand.extend([deal_card(self.deck), deal_card(self.deck)])
        # Deal two cards to the dealer
        self.dealer_hand.extend([deal_card(self.deck), deal_card(self.deck)])
        # Display the dealer's hand (hiding the first card)
        self._display(self.dealer_frame, self.dealer_hand, hide_first=True)
        # Display the player's hand
        self._display(self.player_frame, self.player_hand, hide_first=False)
        # Enable the "Hit" and "Stand" buttons
        self.hit_btn.config(state="normal")
        self.stand_btn.config(state="normal")
        # Disable the "Deal" and bet entry buttons
        self.deal_btn.config(state="disabled")
        self.bet_entry.config(state="disabled")
        # Calculate the player's score
        p = calculate_score(self.player_hand)
        # Update the player's total score display
        self.player_total.set(str(p))
        # Set the dealer's total score display to "?"
        self.dealer_total.set("?")
        # Update the status message
        self.status_var.set(f"Player: {p}   Dealer: ?")
        # If player has Blackjack (score 0) or busts (score > 21), end the round immediately
        if p == 0 or p > 21:
            self.end_round()

    # Method for the player to "Hit" (take another card)
    def hit(self):
        # If no round is in progress, do nothing
        if not self.in_round:
            return
        # Deal one more card to the player
        self.player_hand.append(deal_card(self.deck))
        # Redisplay the player's hand
        self._display(self.player_frame, self.player_hand, hide_first=False)
        # Calculate the player's new score
        p = calculate_score(self.player_hand)
        # Update the player's total score display
        self.player_total.set(str(p))
        # If player busts (score > 21), end the round
        if p > 21:
            self.end_round()
        # Otherwise, update the status message
        else:
            self.status_var.set(f"Player: {p}   Dealer: ?")

    # Method for the player to "Stand" (stop taking cards)
    def stand(self):
        # If no round is in progress, do nothing
        if not self.in_round:
            return
        # End the current round
        self.end_round()

    # Method to conclude the current round of Blackjack
    def end_round(self):
        # Display the dealer's hand, revealing the hidden card
        self._display(self.dealer_frame, self.dealer_hand, hide_first=False)
        # Calculate the dealer's score
        d = calculate_score(self.dealer_hand)
        # Dealer hits until score is 17 or more (or busts)
        while 0 < d < 17:
            # Deal a card to the dealer
            self.dealer_hand.append(deal_card(self.deck))
            # Redisplay the dealer's hand
            self._display(self.dealer_frame, self.dealer_hand, hide_first=False)
            # Recalculate dealer's score
            d = calculate_score(self.dealer_hand)
        # Calculate the player's final score
        p = calculate_score(self.player_hand)
        # Update player's total score display
        self.player_total.set(str(p))
        # Update dealer's total score display
        self.dealer_total.set(str(d))
        # Compare player and dealer scores to determine the result
        msg, mul = compare(p, d)
        # Calculate net winnings for the round
        net = mul * self.bet
        # Update player's balance
        self.balance += net
        # Update balance display
        self.balance_var.set(f"{self.balance:.2f}")
        # Update status message with round result and net gain/loss
        self.status_var.set(f"{msg} {'+' if net>0 else ''}${net:.2f}")

        # Update cumulative stats for the current session
        self.total_winnings += net
        self.total_bets += self.bet
        # If player won the round
        if net > 0:
            self.wins += 1
            self.session_history.append(True) # Record win for cheater detection
        # If player lost the round
        elif net < 0:
            self.losses += 1
            self.session_history.append(False) # Record loss for cheater detection
        # If it's a push/tie
        else:
            self.session_history.append(False) # Treat push as non-win for cheater detection

        # Disable "Hit" and "Stand" buttons
        self.hit_btn.config(state="disabled")
        self.stand_btn.config(state="disabled")
        # If player still has balance, enable "Deal" and bet entry for next round
        if self.balance > 0:
            self.deal_btn.config(state="normal")
            self.bet_entry.config(state="normal")
        # If player runs out of money, show game over message
        else:
            messagebox.showinfo("Game Over", "You’ve run out of money!")
        # Set in_round flag to False
        self.in_round = False
        # Log the current session's cumulative statistics to the database
        self.log_blackjack_session()

        # Cheater detection logic
        # Check if there are at least 20 game results in session history
        if len(self.session_history) >= 20:
            # Get the last 20 game results
            recent_results = self.session_history[-20:]
            # Calculate the win rate over the last 20 games
            win_rate = sum(recent_results) / 20.0
            # If the win rate is 80% or higher
            if win_rate >= 0.8:
                # Log the player as a cheater
                log_cheater(self.player_id, "Blackjack", win_rate)
                # Display a warning message to the player
                messagebox.warning(self.root, "Cheater Detected", f"You won {win_rate*100:.1f}% of your last 20 games and have been flagged.")
                # Destroy the current Blackjack window
                self.root.destroy()
                # If there's a parent menu, show it
                if self.parent_menu:
                    self.parent_menu.show()
                # Exit the method to prevent further execution in this game instance
                return

    # Method to log Blackjack session data to the database
    def log_blackjack_session(self):
        try:
            # Connect to the SQLite database
            with sqlite3.connect(DB_PATH) as conn:
                # Set journaling mode for better concurrency and performance
                conn.execute("PRAGMA journal_mode=WAL")
                # Create a cursor object
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

                # If no rows were updated (meaning it's a new session record to insert)
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
                # Commit the changes to the database
                conn.commit()
        # Catch any exceptions during database operation
        except Exception as e:
            # Print the error to console
            print("DB Log Error:", e)
            # Show an error message box
            messagebox.showerror("Database Error", f"Failed to log session: {e}")

    # Method to return to the main menu
    def return_to_main(self):
        # Destroy the Tkinter root window
        self.root.destroy()
        # If a parent menu exists, show it
        if self.parent_menu:
            self.parent_menu.show()

    # Method to determine the next session number for the player
    def get_next_session_number(self):
        """
        Determines the next session number for the player.
        This ensures a new session number for each game launch.
        """
        try:
            # Connect to the SQLite database
            with sqlite3.connect(DB_PATH) as conn:
                # Set journaling mode for better concurrency and performance
                conn.execute("PRAGMA journal_mode=WAL")
                # Create a cursor object
                cur = conn.cursor()
                # Execute a query to get the maximum session number for the current player
                cur.execute("""
                    SELECT MAX(session_number)
                    FROM Blackjack
                    WHERE player_name=?
                """, (self.full_name,))
                # Fetch the result
                result = cur.fetchone()
                # If there are existing sessions, return the maximum session number + 1.
                # Otherwise, start with session number 1.
                return (result[0] or 0) + 1
        # Catch any exceptions during database operation
        except Exception as e:
            # Print the error to console
            print(f"Error fetching next session number: {e}")
            # Fallback to session 1 if an error occurs
            return 1

    # Method to plot the player's net winnings over sessions
    def plot_net_winnings(self):
        try:
            # Connect to the SQLite database
            with sqlite3.connect(DB_PATH) as conn:
                # Set journaling mode for better concurrency and performance
                conn.execute("PRAGMA journal_mode=WAL")
                # Create a cursor object
                cur = conn.cursor()
                # Execute a query to get session number and money won, ordered by session number
                cur.execute("SELECT session_number, money_won FROM Blackjack WHERE player_name=? ORDER BY session_number", (self.full_name,))
                # Fetch all results
                data = cur.fetchall()
                # If no data is available, show an info message
                if not data:
                    return messagebox.showinfo("No Data", "No session data available.")
                # Extract session numbers from the fetched data
                sessions = [row[0] for row in data]
                # Extract winnings from the fetched data
                winnings = [row[1] for row in data]
                # Create a Matplotlib figure
                fig = Figure(figsize=(5, 4), dpi=100)
                # Add a subplot to the figure
                ax = fig.add_subplot(111)
                # Plot the winnings data with markers
                ax.plot(sessions, winnings, marker='o')
                # Set the title of the plot
                ax.set_title("Net Winnings Over Sessions")
                # Set the label for the x-axis
                ax.set_xlabel("Session")
                # Set the label for the y-axis
                ax.set_ylabel("Net Winnings ($)")
                # Create a new Tkinter Toplevel window for the plot
                win = tk.Toplevel(self.root)
                # Set the title of the plot window
                win.title("Net Winnings")
                # Create a FigureCanvasTkAgg to embed the Matplotlib figure in the Tkinter window
                canvas = FigureCanvasTkAgg(fig, master=win)
                # Draw the canvas
                canvas.draw()
                # Pack the Tkinter widget of the canvas
                canvas.get_tk_widget().pack()
        # Catch any exceptions during plotting
        except Exception as e:
            # Show an error message box
            messagebox.showerror("Plot Error", str(e))

    # Helper method to display cards in a given frame
    def _display(self, frame, hand, hide_first):
        # Destroy all existing widgets (cards) in the frame
        for w in frame.winfo_children():
            w.destroy()
        # Iterate through each card in the hand
        for i, val in enumerate(hand):
            # If it's the first card and it needs to be hidden (for dealer's first card)
            if i == 0 and hide_first:
                # If a card back image is loaded
                if TK_BACK_IMAGE:
                    # Create a label with the card back image
                    lbl = tk.Label(frame, image=TK_BACK_IMAGE, bg="#2E7D32")
                    # Keep a reference to the image to prevent garbage collection
                    lbl.image = TK_BACK_IMAGE
                # If no card back image is loaded, use a "?" placeholder
                else:
                    lbl = tk.Label(frame, text="?", font=("Arial",32), fg="red", bg="white", width=4, height=2, relief="raised", bd=2)
                # Pack the card label to the left
                lbl.pack(side="left", padx=10)
            # If it's not the first card or doesn't need to be hidden
            else:
                # Get the rank symbol for the card's numeric value
                rank = NUMERIC_TO_RANK[val]
                # Randomly choose a suit for display (since numeric deck doesn't store suits)
                suit = random.choice(SUITS)
                # Get the Unicode symbol for the chosen suit
                symbol = SUIT_SYMBOL[suit]
                # Combine rank and symbol for display text
                txt = rank + symbol
                # Create a label to display the card
                lbl = tk.Label(frame, text=txt, font=("Arial",32), fg="red", bg="white", width=4, height=2, relief="raised", bd=2)
                # Pack the card label to the left
                lbl.pack(side="left", padx=10)
