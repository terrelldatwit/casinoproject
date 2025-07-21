# Import necessary modules for GUI, random operations, database, and plotting
import sys
import random
import sqlite3
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import the cheaters logging function
from cheaters import log_cheater

# Define the database path
DB_PATH = "CasinoDB.db"

# Card setup: Define suits and ranks for a standard deck
suits = ['hearts', 'diamonds', 'clubs', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
# Map ranks to numerical values for comparison in High/Low game.
# Ace (A) is typically the highest in High/Low.
rank_values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13, 'A': 14
}

# Define the folder where card images are stored (assumes a 'Cards' subdirectory
# in the same directory as this script).
# Example: If highlow.py is in 'Casino_Full_Game', then 'Cards' folder should also be
# inside 'Casino_Full_Game'.
CARD_IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "Cards")

# Function to create and shuffle a deck of cards
def create_shuffled_deck(num_decks=4):
    deck = []
    # Loop to create multiple decks
    for _ in range(num_decks):
        # Create card strings in "Rank of Suit" format (e.g., "Ace of Spades")
        deck += [f"{rank} of {suit}" for suit in suits for rank in ranks]
    # Shuffle the combined deck
    random.shuffle(deck)
    return deck

# HighLowGame class, inheriting from QWidget for GUI capabilities
class HighLowGame(QWidget):
    # Constructor for the HighLow game
    def __init__(self, player_id, parent_menu=None):
        # Call the parent QWidget constructor
        super().__init__()
        # Set the window title
        self.setWindowTitle("Higher or Lower!")
        # Set the window's position and size
        self.setGeometry(500, 200, 400, 600) # Adjusted geometry for better layout

        # Store the player's ID
        self.player_id = player_id
        # Store a reference to the parent menu for navigation
        self.parent_menu = parent_menu

        # Establish a connection to the SQLite database
        self.conn = sqlite3.connect(DB_PATH)
        # Create a cursor object for executing SQL queries
        self.cur = self.conn.cursor()

        # Fetch player's current balance from the database
        self.balance = self.fetch_balance_from_db()
        # Fetch the player's full name from the database
        self.full_name = self.fetch_player_name()

        # Game state variables for the current streak
        self.last_card = None # Stores the previously drawn card
        self.cashout = 0.0 # Winnings accumulated in the current winning streak
        self.cards_dealt_in_streak = 0 # Number of consecutive correct guesses (streak length)

        # Deck management variables
        self.num_decks = 4 # Number of decks to use
        self.total_cards_in_full_deck = 52 * self.num_decks # Total cards when deck is full
        # Define the threshold for reshuffling (25% of total cards remaining)
        self.shuffle_threshold = int(self.total_cards_in_full_deck * 0.25)

        # Create and shuffle the initial deck
        self.deck = create_shuffled_deck(self.num_decks)

        # Session tracking variables for database logging (per game launch)
        self.session_number = self.get_next_session_number() # Get a new session number for this launch
        self.total_winnings_session = 0.0 # Total net winnings for this entire game launch
        self.total_bets_session = 0.0 # Total money bet in this game launch
        self.wins_session = 0 # Total rounds won in this game launch
        self.losses_session = 0 # Total rounds lost in this game launch
        self.session_history = [] # Stores win/loss (True/False) for cheater detection

        # Initialize self.graph_window to None, it will be assigned when plot_net_winnings is called
        self.graph_window = None

        # Set up the graphical user interface elements
        self.setup_ui()
        # Update the balance display on the UI
        self.update_balance_label()

        # Show the HighLow game window
        self.show()


    # Method to fetch the player's full name from the database
    def fetch_player_name(self):
        try:
            # Connect to the database (using a new connection for this specific query)
            with sqlite3.connect(DB_PATH) as conn:
                # Set journaling mode for better performance
                conn.execute("PRAGMA journal_mode=WAL")
                # Create a cursor
                cur = conn.cursor()
                # Execute query to get player's full name
                cur.execute("SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?", (self.player_id,))
                # Fetch the result
                result = cur.fetchone()
                # Return full name or player ID if not found
                return result[0] if result else str(self.player_id)
        # Handle any exceptions during database operation
        except Exception as e:
            # Print error for debugging
            print(f"Error fetching player name: {e}")
            # Return player ID as fallback
            return str(self.player_id)

    # Method to fetch the player's balance from the database
    def fetch_balance_from_db(self):
        try:
            # Connect to the database
            with sqlite3.connect(DB_PATH) as conn:
                # Set journaling mode
                conn.execute("PRAGMA journal_mode=WAL")
                # Create a cursor
                cur = conn.cursor()
                # Execute query to get player's balance
                cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))
                # Fetch the result
                result = cur.fetchone()
                # Return balance as float or default to 100.0 if not found
                return float(result[0]) if result else 100.0
        # Handle any exceptions
        except Exception as e:
            # Print error for debugging
            print(f"Error fetching balance: {e}")
            # Return default balance as fallback
            return 100.0

    # Method to get the next available session number for the player in HighLow game
    def get_next_session_number(self):
        try:
            # Execute query to find the maximum session number for the current player
            self.cur.execute("""
                SELECT MAX(session_number)
                FROM HighLow
                WHERE player_name=?
            """, (self.full_name,))
            # Fetch the result
            result = self.cur.fetchone()
            # Return max session number + 1, or 1 if no previous sessions
            return (result[0] or 0) + 1
        # Handle any exceptions
        except Exception as e:
            # Print error for debugging
            print(f"Error fetching next session number: {e}")
            # Return 1 as fallback
            return 1

    # Method to set up the graphical user interface
    def setup_ui(self):
        # Create the main vertical layout for the window
        layout = QVBoxLayout()

        # Label to display player's current balance
        self.balance_label = QLabel(f"Balance: ${self.balance:.2f}")
        # Apply CSS styling to the balance label
        self.balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        # Add the balance label to the layout
        layout.addWidget(self.balance_label)

        # Label to indicate the current card
        self.current_card_label = QLabel("Current Card:")
        # Apply CSS styling
        self.current_card_label.setStyleSheet("font-size: 16px; margin-top: 10px;")
        # Add to layout
        layout.addWidget(self.current_card_label)

        # QLabel to display the card image
        self.card_image = QLabel(self)
        # Set fixed size for the card image display area
        self.card_image.setFixedSize(150, 220)
        # Apply CSS styling for border, rounded corners, and background
        self.card_image.setStyleSheet("border: 2px solid #555; border-radius: 10px; background-color: #eee;")
        # Center the content within the label
        self.card_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Add the card image label to the layout, centered horizontally
        layout.addWidget(self.card_image, alignment=Qt.AlignmentFlag.AlignCenter)

        # Label to display the current winning streak length
        self.cards_dealt_label = QLabel(f"Streak: {self.cards_dealt_in_streak}")
        # Apply CSS styling
        self.cards_dealt_label.setStyleSheet("font-size: 16px; margin-top: 5px;")
        # Add to layout
        layout.addWidget(self.cards_dealt_label)

        # QLineEdit for entering bet amount
        self.bet_input = QLineEdit()
        # Set placeholder text
        self.bet_input.setPlaceholderText("Enter your bet amount")
        # Apply CSS styling
        self.bet_input.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px;")
        # Add to layout
        layout.addWidget(self.bet_input)

        # Create a vertical layout for action buttons
        button_layout = QVBoxLayout()

        # Button to draw the first card for a new streak
        self.draw_button = QPushButton("Draw Starting Card")
        # Apply CSS styling for appearance
        self.draw_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 8px; font-size: 16px;")
        # Connect button click to draw_starting_card method
        self.draw_button.clicked.connect(self.draw_starting_card)
        # Add to button layout
        button_layout.addWidget(self.draw_button)

        # Create a horizontal layout for Higher/Lower guess buttons
        guess_button_layout = QHBoxLayout()
        # Button for guessing "Higher"
        self.higher_button = QPushButton("Higher")
        # Apply CSS styling
        self.higher_button.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; border-radius: 8px; font-size: 16px;")
        # Connect button click to make_guess with expect_higher=True
        self.higher_button.clicked.connect(lambda: self.make_guess(expect_higher=True))
        # Add to guess button layout
        guess_button_layout.addWidget(self.higher_button)

        # Button for guessing "Lower"
        self.lower_button = QPushButton("Lower")
        # Apply CSS styling
        self.lower_button.setStyleSheet("background-color: #F44336; color: white; padding: 10px; border-radius: 8px; font-size: 16px;")
        # Connect button click to make_guess with expect_higher=False
        self.lower_button.clicked.connect(lambda: self.make_guess(expect_higher=False))
        # Add to guess button layout
        guess_button_layout.addWidget(self.lower_button)
        # Add the horizontal guess button layout to the main button layout
        button_layout.addLayout(guess_button_layout)

        # Button to cash out current streak winnings
        self.cashout_button = QPushButton(f"Cash Out ${self.cashout:.2f}")
        # Apply CSS styling
        self.cashout_button.setStyleSheet("background-color: #FFC107; color: black; padding: 10px; border-radius: 8px; font-size: 16px;")
        # Connect button click to cash_out method
        self.cashout_button.clicked.connect(self.cash_out)
        # Add to button layout
        button_layout.addWidget(self.cashout_button)

        # Button to view net winnings graph for High/Low game
        net_winnings_button = QPushButton("View Net Winnings")
        # Apply CSS styling
        net_winnings_button.setStyleSheet("background-color: #9C27B0; color: white; padding: 10px; border-radius: 8px; font-size: 16px;")
        # Connect button click to plot_net_winnings method
        net_winnings_button.clicked.connect(self.plot_net_winnings)
        # Add to button layout
        button_layout.addWidget(net_winnings_button)

        # Button to return to the main casino menu
        back_button = QPushButton("Back to Main Menu")
        # Apply CSS styling
        back_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 8px; font-size: 16px;")
        # Connect button click to back_to_menu method
        back_button.clicked.connect(self.back_to_menu)
        # Add to button layout
        button_layout.addWidget(back_button)

        # Add the action buttons layout to the main layout
        layout.addLayout(button_layout)

        # Label to display game status messages
        self.status_label = QLabel("Welcome! Draw a card to start.")
        # Apply CSS styling
        self.status_label.setStyleSheet("font-size: 16px; font-style: italic; margin-top: 10px;")
        # Center align the status message
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Add to layout
        layout.addWidget(self.status_label)

        # Set the main layout for the window
        self.setLayout(layout)

        # Set initial button states: disable guess and cashout buttons
        self.toggle_guess_buttons(False)
        self.cashout_button.setEnabled(False)

    # Helper method to enable/disable Higher/Lower guess buttons
    def toggle_guess_buttons(self, enable):
        self.higher_button.setEnabled(enable)
        self.lower_button.setEnabled(enable)
        # Disable draw button when guessing is active, enable when not
        self.draw_button.setEnabled(not enable)

    # Method to update the balance display label on the GUI
    def update_balance_label(self):
        self.balance_label.setText(f"Balance: ${self.balance:.2f}")

    # Method to check if the deck needs reshuffling and perform it
    def check_and_shuffle_deck(self):
        # If the number of cards remaining in the deck is below the shuffle threshold
        if len(self.deck) <= self.shuffle_threshold:
            # Update status label to inform user about reshuffling
            self.status_label.setText("Deck low - reshuffling!")
            # Create a new shuffled deck
            self.deck = create_shuffled_deck(self.num_decks)
            # Reset streak-related variables after reshuffle
            self.cards_dealt_in_streak = 0
            self.cashout = 0.0
            self.last_card = None
            # Update UI elements to reflect reset streak
            self.cards_dealt_label.setText(f"Streak: {self.cards_dealt_in_streak}")
            self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
            self.show_card_image(None) # Clear the displayed card image
            # Use a QTimer to display a message after a short delay
            QTimer.singleShot(1500, lambda: self.status_label.setText("Deck reshuffled. Draw a new starting card."))
            # Disable guess buttons until a new starting card is drawn
            self.toggle_guess_buttons(False)
            # Enable the draw button
            self.draw_button.setEnabled(True)

    # Method to draw the first card for a new round/streak
    def draw_starting_card(self):
        # Check if the deck needs reshuffling before drawing
        self.check_and_shuffle_deck()

        # If the deck is empty after checking/reshuffling
        if not self.deck:
            self.status_label.setText("Deck is empty! Please restart the game.")
            return

        # Reset streak-related variables for a new starting card
        self.cards_dealt_in_streak = 0
        self.cashout = 0.0
        # Update UI elements for reset streak
        self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
        self.cards_dealt_label.setText(f"Streak: {self.cards_dealt_in_streak}")
        self.cashout_button.setEnabled(False) # Disable cashout until there's a win

        # Draw a card from the deck
        card = self.deck.pop()
        # Display the drawn card image
        self.show_card_image(card)
        # Update status message
        self.status_label.setText(f"Current card: {card}. Guess Higher or Lower?")
        # Set the drawn card as the last_card for the next guess
        self.last_card = card
        # Enable guess buttons
        self.toggle_guess_buttons(True)
        # Disable the draw button until a guess is made or streak ends
        self.draw_button.setEnabled(False)

    # Method to validate the bet amount entered by the user
    def validate_bet(self):
        try:
            # Get text from bet input and convert to float
            bet = float(self.bet_input.text())
            # Check if bet is positive
            if bet <= 0:
                raise ValueError("Bet must be a positive number.")
            # Check if bet exceeds player's balance
            if bet > self.balance:
                # Show warning if bet is too high
                QMessageBox.warning(self, "Invalid Bet", "You cannot bet more than your balance!")
                return None
            # Return valid bet amount
            return bet
        # Handle specific ValueError (e.g., non-numeric input or negative bet)
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Bet", str(e))
            return None
        # Handle any other unexpected errors
        except Exception as e:
            QMessageBox.warning(self, "Error", f"An unexpected error occurred with bet input: {e}")
            return None

    # Method to process the player's guess (Higher or Lower)
    def make_guess(self, expect_higher):
        # If no starting card has been drawn, prompt user
        if not self.last_card:
            self.status_label.setText("Draw a starting card first!")
            return

        # Validate the bet amount
        bet = self.validate_bet()
        # If bet is invalid, stop here
        if bet is None:
            return

        # Deduct bet from balance immediately for the round
        self.balance -= bet
        # Update balance display
        self.update_balance_label()
        # Accumulate total bets for the session
        self.total_bets_session += bet

        # Check for reshuffle before drawing the next card
        self.check_and_shuffle_deck()

        # If deck is empty after reshuffle check
        if not self.deck:
            self.status_label.setText("Deck is empty! Please restart the game.")
            self.toggle_guess_buttons(False)
            self.draw_button.setEnabled(True)
            return

        # Draw the new card
        new_card = self.deck.pop()
        # Display the new card image
        self.show_card_image(new_card)

        # Get numerical values of the last card and the new card
        rank1_value = rank_values[self.last_card.split()[0]]
        rank2_value = rank_values[new_card.split()[0]]

        # Determine if the guess was correct
        win_round = False
        if expect_higher:
            win_round = (rank2_value > rank1_value)
        else: # expect_lower
            win_round = (rank2_value < rank1_value)

        # Handle ties (new card has same value as last card)
        if rank2_value == rank1_value:
            self.status_label.setText(f"Rolled: {new_card}. It's a tie! No win or loss. Streak reset.")
            self.session_history.append(False) # Treat tie as non-win for cheater detection
            self.cards_dealt_in_streak = 0 # Reset streak on tie
            self.cashout = 0.0 # Reset cashout
            # Update UI for reset streak
            self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
            self.cards_dealt_label.setText(f"Streak: {self.cards_dealt_in_streak}")
            self.last_card = None # Force new starting card after tie
            # Disable guess buttons, enable draw button
            self.toggle_guess_buttons(False)
            self.draw_button.setEnabled(True)
            self.save_user() # Save state after round
            return # Exit method for tie

        # If the player won the guess
        if win_round:
            self.cards_dealt_in_streak += 1 # Increment streak length
            # Multiplier calculation: 1 * (1 + 0.3) ^ (cards_dealt_in_streak - 1)
            # For streak 1 (first correct guess), exponent is 0, multiplier is 1.0
            # For streak 2 (second correct guess), exponent is 1, multiplier is 1.3
            multiplier = (1 + 0.3) ** (self.cards_dealt_in_streak - 1)
            # Calculate winnings from this specific bet
            current_winnings_from_bet = bet * multiplier

            self.cashout += current_winnings_from_bet # Add to current streak's cashout
            # Update status message with win details and current streak winnings
            self.status_label.setText(f"Rolled: {new_card}. Winner! Streak: {self.cards_dealt_in_streak}. Current Winnings: ${self.cashout:.2f}")
            self.cashout_button.setEnabled(True) # Enable cashout button
            self.wins_session += 1 # Increment total wins for this game launch
            self.total_winnings_session += current_winnings_from_bet # Accumulate total winnings for session
            self.session_history.append(True) # Record win for cheater detection
            self.last_card = new_card # Continue streak: new card becomes the last card
            # Guess buttons remain enabled for the next guess in the streak
        # If the player lost the guess
        else:
            self.status_label.setText(f"Rolled: {new_card}. You lost the bet. Streak reset.")
            self.cashout = 0.0 # Reset cashout on loss
            self.cards_dealt_in_streak = 0 # Reset streak on loss
            self.cashout_button.setEnabled(False) # Disable cashout
            self.losses_session += 1 # Increment total losses for this game launch
            self.session_history.append(False) # Record loss for cheater detection
            self.last_card = None # Force new starting card after loss
            # Disable guess buttons, enable draw button
            self.toggle_guess_buttons(False)
            self.draw_button.setEnabled(True)

        # Update UI elements
        self.cards_dealt_label.setText(f"Streak: {self.cards_dealt_in_streak}")
        self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")

        # Check for game over (balance <= 0)
        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You ran out of money! Game resetting.")
            self.reset_game_state() # Reset only game state, not balance for next launch
            self.status_label.setText("Game over. Please deposit more funds or restart.")
            self.toggle_guess_buttons(False) # Disable all action buttons
            self.draw_button.setEnabled(False)
            self.bet_input.setEnabled(False)
        else:
            self.save_user() # Save user data to DB after each round

        # Cheater detection logic
        if len(self.session_history) >= 20: # Check if enough games have been played
            recent_results = self.session_history[-20:] # Get the last 20 results
            win_rate = sum(recent_results) / 20.0 # Calculate win rate
            if win_rate >= 0.8: # If win rate is 80% or higher
                # Log the player as a cheater
                log_cheater(self.player_id, "HighLow", win_rate)
                # Show a warning message to the player
                QMessageBox.warning(self, "Cheater Detected", f"You won {win_rate*100:.1f}% of your last 20 games and have been flagged.")
                # Return to the main menu
                self.back_to_menu()
                return # Exit the method early

    # Method to cash out current streak winnings
    def cash_out(self):
        # If there are winnings to cash out
        if self.cashout > 0:
            self.balance += self.cashout # Add cashed out amount to player's balance
            self.update_balance_label() # Update balance display
            QMessageBox.information(self, "Cash Out", f"You've cashed out ${self.cashout:.2f}!")

            # Add cashed out amount to session's total winnings
            self.total_winnings_session += self.cashout

            # Reset streak-related variables after cashout
            self.cashout = 0.0
            self.cards_dealt_in_streak = 0
            self.last_card = None
            # Update UI elements for reset streak
            self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
            self.cashout_button.setEnabled(False) # Disable cashout until next win
            self.cards_dealt_label.setText(f"Streak: {self.cards_dealt_in_streak}")
            self.show_card_image(None) # Clear the displayed card image
            self.status_label.setText("Winnings cashed out. Draw a new starting card.")
            # Disable guess buttons, enable draw button for a new streak
            self.toggle_guess_buttons(False)
            self.draw_button.setEnabled(True)
            self.save_user() # Save state after cashout
        # If no winnings to cash out
        else:
            QMessageBox.information(self, "Cash Out", "No winnings to cash out.")

    # Method to reset game state (used after game over or for a fresh start within a session)
    def reset_game_state(self):
        self.last_card = None # Clear the last card
        self.cashout = 0.0 # Reset cashout winnings
        self.cards_dealt_in_streak = 0 # Reset streak length
        self.deck = create_shuffled_deck(self.num_decks) # Reshuffle the deck
        # Update UI elements
        self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
        self.cards_dealt_label.setText(f"Streak: {self.cards_dealt_in_streak}")
        self.show_card_image(None) # Clear displayed card image

    # Method to display a card image on the GUI
    def show_card_image(self, card):
        # If card is None, clear the image display
        if card is None:
            self.card_image.clear()
            return

        # Example card string: "2 of clubs" -> split into rank, "of", suit
        rank, _, suit = card.split()
        # Construct the filename for the card image (e.g., "2_of_clubs.png")
        card_filename = f"{rank}_of_{suit}.png"
        # Construct the full path to the image file using os.path.abspath
        # IMPORTANT: Ensure a 'Cards' folder exists in the same directory as highlow.py
        # and contains all card images (e.g., "2_of_clubs.png", "K_of_spades.png", etc.)
        image_path = os.path.abspath(os.path.join(CARD_IMAGE_FOLDER, card_filename))

        # Create a QPixmap from the image path
        pixmap = QPixmap(image_path)

        # If the pixmap loaded successfully
        if not pixmap.isNull():
            # Scale the pixmap to fit the label, maintaining aspect ratio and smooth transformation
            self.card_image.setPixmap(pixmap.scaled(self.card_image.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.card_image.setText("") # Clear any previous text
        # If the image failed to load
        else:
            self.card_image.setText(f"Image not found:\n{card_filename}")
            # Print an error message for debugging
            print(f"Error: Card image not found at {image_path}")

    # Method to save current game state and session statistics to the database
    def save_user(self):
        try:
            # Update player's general balance in the PLAYERS table
            self.cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.player_id))

            # Check if an entry for the current session_number and player exists in HighLow table
            self.cur.execute("SELECT 1 FROM HighLow WHERE player_name=? AND session_number=?", (self.full_name, self.session_number))
            exists = self.cur.fetchone()

            # If an entry exists, update it
            if exists:
                self.cur.execute("""
                    UPDATE HighLow
                    SET number_of_bets = ?,
                        bet_amount = ?,
                        wins = ?,
                        losses = ?,
                        money_won = ?
                    WHERE player_name = ? AND session_number = ?
                """, (
                    self.wins_session + self.losses_session, # total rounds played in this session
                    self.total_bets_session,
                    self.wins_session,
                    self.losses_session,
                    self.total_winnings_session,
                    self.full_name,
                    self.session_number
                ))
            # If no entry exists, insert a new one
            else:
                self.cur.execute("""
                    INSERT INTO HighLow (player_name, number_of_bets, bet_amount, wins, losses, money_won, session_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.full_name,
                    self.wins_session + self.losses_session,
                    self.total_bets_session,
                    self.wins_session,
                    self.losses_session,
                    self.total_winnings_session,
                    self.session_number
                ))
            # Commit the changes to the database
            self.conn.commit()
        # Handle any exceptions during database save
        except Exception as e:
            # Print error for debugging
            print(f"DB Save Error: {e}")
            # Show a critical error message box
            QMessageBox.critical(self, "Database Error", f"Failed to save game data: {e}")

    # Method to return to the main casino menu
    def back_to_menu(self):
        self.save_user() # Save current game state before exiting
        self.conn.close() # Close the database connection
        self.close() # Close the current game window
        # If a parent menu exists, show it
        if self.parent_menu:
            self.parent_menu.show()

    # Method to plot cumulative net winnings over sessions for High/Low game
    def plot_net_winnings(self):
        try:
            # Execute query to fetch session data for plotting
            self.cur.execute("""
                SELECT session_number, money_won, bet_amount FROM HighLow
                WHERE player_name=? ORDER BY session_number
            """, (self.full_name,))
            # Fetch all results
            rows = self.cur.fetchall()

            # If no data is found, show an information message
            if not rows:
                QMessageBox.information(self, "No Data", "No winnings history available for this player.")
                return

            # Initialize lists for cumulative winnings and session numbers
            cumulative = []
            session_numbers = []
            total = 0.0 # Overall total net winnings

            # Iterate through fetched rows
            for session_num, money_won, bet_amount in rows:
                # Ensure session number is not None
                if session_num is not None:
                    # Assuming 'money_won' column already stores the net winnings for the session
                    # If it stores gross winnings, you might need to adjust (money_won - bet_amount)
                    net = money_won
                    total += net # Add to overall total
                    cumulative.append(total) # Add to cumulative list
                    session_numbers.append(int(session_num)) # Add session number

            # Create a new QWidget for the graph window and store it as an instance variable
            # This prevents the window from being garbage collected and closing immediately
            self.graph_window = QWidget()
            # Set window title
            self.graph_window.setWindowTitle("Net Winnings - High/Low")
            # Set window geometry
            self.graph_window.setGeometry(150, 150, 600, 400)

            # Create vertical layout for the graph window
            layout = QVBoxLayout()
            self.graph_window.setLayout(layout)

            # Create a Matplotlib figure
            fig = Figure(figsize=(5, 4))
            # Create a FigureCanvas to embed the figure
            canvas = FigureCanvas(fig)
            # Add a subplot to the figure
            ax = fig.add_subplot(111)
            # Plot the cumulative winnings
            ax.plot(session_numbers, cumulative, marker='o', color='orange')
            # Set chart title
            ax.set_title("Cumulative Net Winnings - High/Low")
            # Set x-axis label
            ax.set_xlabel("Session Number")
            # Set y-axis label
            ax.set_ylabel("Net Winnings ($)")
            # Enable grid
            ax.grid(True)
            # Set x-axis ticks
            ax.set_xticks(session_numbers)

            # Create label for total net winnings
            total_label = QLabel(f"Total Net Winnings: ${total:.2f}")
            # Center-align the label
            total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Add canvas and label to layout
            layout.addWidget(canvas)
            layout.addWidget(total_label)

            # Ensure widget is deleted on close
            self.graph_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            # Show the graph window
            self.graph_window.show()
        # Handle any exceptions during plotting
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot winnings: {e}")

