# IMPORTS
import sys # Used for system-specific parameters and functions, e.g., exiting the application
import random # Used for shuffling the deck and dealing cards randomly
import math # Not explicitly used in the provided code, but often useful for mathematical operations
import sqlite3 # Used for interacting with the SQLite database (CasinoDB.db)

# PyQt6 GUI components imports
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtGui import QIntValidator # Used to validate integer input in QLineEdit
from PyQt6.QtCore import Qt # Used for alignment flags and other core Qt functionalities

# Matplotlib imports for plotting graphs
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas # For embedding Matplotlib figures into PyQt6 applications
from matplotlib.figure import Figure # To create Matplotlib figures

from cheaters import log_cheater # Import the cheater logging function from a separate module

# Define the database path
DB_PATH = "CasinoDB.db" # Path to the SQLite database file

class Card:
    """
    Represents a single playing card with a rank and a suit.
    Rank: 1 (Ace) to 13 (King). Ace is high for comparison in Poker (represented as 13 for high, 1 for low in straight logic).
    Suit: 1 (Spades), 2 (Hearts), 3 (Diamonds), 4 (Clubs).
    """
    def __init__(self, suit, rank):
        """
        Initializes a Card object.
        Args:
            suit (int): The suit of the card (1=Spades, 2=Hearts, 3=Diamonds, 4=Clubs).
            rank (int): The rank of the card (1=Ace, 2-10, 11=Jack, 12=Queen, 13=King).
        """
        self.rank = rank
        self.suit = suit

    def __lt__(self, other):
        """
        Defines the less-than comparison for Card objects.
        Used for sorting cards, primarily by rank, then by suit for tie-breaking.
        Args:
            other (Card): The other Card object to compare against.
        Returns:
            bool: True if this card is less than the other, False otherwise.
        """
        # Compare by rank first
        if self.rank != other.rank:
            return self.rank < other.rank
        # If ranks are equal, compare by suit
        return self.suit < other.suit

    def printCard(self):
        """
        Returns a string representation of the card (e.g., "Ace of Spades").
        Maps integer ranks and suits to their string equivalents.
        Returns:
            str: A human-readable string representing the card.
        """
        rank_str = ""
        # Map numerical rank to string rank
        if self.rank == 1:
            rank_str = "Ace"
        elif self.rank < 10:
            rank_str = str(self.rank + 1) # Ranks 2-9 are directly mapped
        elif self.rank == 10:
            rank_str = "Jack"
        elif self.rank == 11:
            rank_str = "Queen"
        elif self.rank == 12:
            rank_str = "King"
        elif self.rank == 13:
            rank_str = "Ace" # Ace is 13 for high card in poker, but 1 for straight logic

        suit_str = ""
        # Map numerical suit to string suit
        if self.suit == 1:
            suit_str = "Spades"
        elif self.suit == 2:
            suit_str = "Hearts"
        elif self.suit == 3:
            suit_str = "Diamonds"
        elif self.suit == 4:
            suit_str = "Clubs"
        return f"{rank_str} of {suit_str}"


class Poker(QMainWindow): # Changed to QMainWindow for consistency with other games
    def __init__(self, player_id, parent_menu=None):
        """
        Initializes the Poker game window and game state.
        
        Args:
            player_id (int): The ID of the current player.
            parent_menu (QWidget): Reference to the main menu window to return to.
        """
        super().__init__() # Call the constructor of the parent QMainWindow class
        self.setWindowTitle("Texas Hold'em Poker") # Set the window title
        self.setGeometry(100, 100, 800, 600) # Set a reasonable window size (x, y, width, height)

        self.player_id = player_id # Store the player's unique ID
        self.parent_menu = parent_menu # Store reference to the main menu

        # Database connection and player data
        self.conn = sqlite3.connect(DB_PATH) # Establish connection to the SQLite database
        self.cursor = self.conn.cursor() # Create a cursor object for executing SQL queries
        self.balance = self.fetch_balance_from_db() # Fetch the player's current balance from DB
        self.full_name = self.fetch_player_name() # Fetch the player's full name from DB

        # Game state variables
        self.player_hand = [] # List to store the player's two hole cards
        self.dealer_hand = [] # List to store the dealer's two hole cards
        self.community_cards = [] # List to store the five community cards (Flop, Turn, River)
        self.deck = [] # List representing the current deck of cards

        self.current_bet = 0.0 # Stores the player's bet for the current round

        # Session tracking for database logging and cheater detection
        self.session_number = self.get_next_session_number() # Get the next available session number for this game launch
        self.total_winnings_session = 0.0 # Accumulates net winnings (profit/loss) for this entire game launch
        self.total_bets_session = 0.0     # Accumulates total money bet in this game launch
        self.wins_session = 0             # Counts total rounds won in this game launch
        self.losses_session = 0           # Counts total rounds lost in this game launch
        self.session_history = []         # Stores win/loss (True/False) for cheater detection (last 20 games)

        self.setup_ui() # Call method to set up the graphical user interface
        self.update_balance_label() # Update the balance display on the UI

    def fetch_player_name(self):
        """
        Fetches the player's full name (first_name + last_name) from the PLAYERS table in the database.
        Returns the full name as a string, or the player ID as a string if not found or an error occurs.
        """
        try:
            # Execute SQL query to concatenate first and last names
            self.cursor.execute("SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?", (self.player_id,))
            result = self.cursor.fetchone() # Fetch the first (and only) result
            return result[0] if result else str(self.player_id) # Return name if found, else ID
        except Exception as e:
            print(f"Error fetching player name: {e}") # Print error for debugging
            return str(self.player_id) # Fallback to player ID

    def fetch_balance_from_db(self):
        """
        Fetches the player's current balance from the PLAYERS table in the database.
        Returns the balance as a float, or 100.0 as a default if not found or an error occurs.
        """
        try:
            # Execute SQL query to get the player's balance
            self.cursor.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))
            result = self.cursor.fetchone() # Fetch the result
            return float(result[0]) if result else 100.0 # Return balance if found, else default
        except Exception as e:
            print(f"Error fetching balance: {e}") # Print error for debugging
            return 100.0 # Fallback to default balance

    def get_next_session_number(self):
        """
        Determines the next sequential session number for the current player in the Poker game.
        Queries the Poker table for the maximum existing session number for the player
        and returns that number incremented by 1. If no sessions exist, returns 1.
        """
        try:
            # Query for the maximum session number for the current player in the Poker table
            self.cursor.execute("""
                SELECT MAX(session_number)
                FROM Poker
                WHERE player_name=?
            """, (self.full_name,))
            result = self.cursor.fetchone() # Fetch the result
            return (result[0] or 0) + 1 # If result is None (no sessions), use 0 then add 1
        except Exception as e:
            print(f"Error fetching next session number: {e}") # Print error for debugging
            return 1 # Fallback to session 1

    def setup_ui(self):
        """Sets up the graphical user interface for the Poker game."""
        central_widget = QWidget() # Create a central widget for the QMainWindow
        self.setCentralWidget(central_widget) # Set it as the central widget
        self.vbox = QVBoxLayout(central_widget) # Create a vertical box layout for the central widget

        # Top section: Balance, Bet Input, Play Button
        top_layout = QHBoxLayout() # Horizontal layout for top elements
        self.balance_label = QLabel(f"Balance: ${self.balance:.2f}") # Label to display current balance
        self.balance_label.setStyleSheet("font-size: 16px; font-weight: bold;") # Apply CSS styling
        top_layout.addWidget(self.balance_label) # Add balance label to top layout

        top_layout.addWidget(QLabel("Bet:")) # Label for bet input
        self.betLine = QLineEdit() # Line edit for entering bet amount
        self.betLine.setValidator(QIntValidator(5, 100)) # Set validator for integer input between 5 and 100
        self.betLine.setPlaceholderText("Min $5, Max $100") # Placeholder text for bet input
        self.betLine.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 5px;") # Apply CSS styling
        top_layout.addWidget(self.betLine) # Add bet input to top layout

        self.playButton = QPushButton("PLAY") # Button to start the game round
        self.playButton.clicked.connect(self.validateBet) # Connect button click to validateBet method
        self.playButton.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 15px; border-radius: 5px; font-size: 14px; font-weight: bold;") # Apply CSS styling
        top_layout.addWidget(self.playButton) # Add play button to top layout
        self.vbox.addLayout(top_layout) # Add the top horizontal layout to the main vertical layout

        # Card display sections
        self.vbox.addWidget(QLabel("<b>Player's Cards:</b>").setStyleSheet("font-weight: bold; margin-top: 10px;")) # Label for player's cards
        self.player_cards_layout = QHBoxLayout() # Horizontal layout for player's cards
        self.vbox.addLayout(self.player_cards_layout) # Add to main layout

        self.vbox.addWidget(QLabel("<b>Dealer's Cards:</b>").setStyleSheet("font-weight: bold; margin-top: 10px;")) # Label for dealer's cards
        self.dealer_cards_layout = QHBoxLayout() # Horizontal layout for dealer's cards
        self.vbox.addLayout(self.dealer_cards_layout) # Add to main layout

        self.vbox.addWidget(QLabel("<b>Community Cards:</b>").setStyleSheet("font-weight: bold; margin-top: 10px;")) # Label for community cards
        self.community_cards_layout = QHBoxLayout() # Horizontal layout for community cards
        self.vbox.addLayout(self.community_cards_layout) # Add to main layout

        # Result message
        self.label_win = QLabel("") # Label to display game outcome (win/loss/tie)
        self.label_win.setStyleSheet("font-size: 18px; font-weight: bold; color: blue; margin-top: 20px;") # Apply CSS styling
        self.label_win.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center-align the text
        self.vbox.addWidget(self.label_win) # Add result label to main layout

        # Action buttons (Net Winnings, Back to Main Menu)
        action_button_layout = QHBoxLayout() # Horizontal layout for action buttons

        net_winnings_button = QPushButton("View Net Winnings") # Button to view net winnings graph
        net_winnings_button.setStyleSheet("background-color: #9C27B0; color: white; padding: 10px; border-radius: 8px; font-size: 14px;") # Apply CSS styling
        net_winnings_button.clicked.connect(self.plot_net_winnings) # Connect button click to plot_net_winnings method
        action_button_layout.addWidget(net_winnings_button) # Add button to action layout

        back_button = QPushButton("Back to Main Menu") # Button to return to the main menu
        back_button.setStyleSheet("background-color: #607D8B; color: white; padding: 10px; border-radius: 8px; font-size: 14px;") # Apply CSS styling
        back_button.clicked.connect(self.back_to_menu) # Connect button click to back_to_menu method
        action_button_layout.addWidget(back_button) # Add button to action layout

        self.vbox.addLayout(action_button_layout) # Add the action buttons layout to the main layout

        self.update_card_displays() # Initialize empty card displays on startup

    def update_balance_label(self):
        """Updates the balance label on the UI with the current player balance."""
        self.balance_label.setText(f"Balance: ${self.balance:.2f}")

    def update_card_displays(self):
        """
        Clears existing card display labels and updates them with the current cards
        in player's hand, dealer's hand, and community cards.
        Dealer's first card is hidden until the game ends.
        """
        # Clear existing cards from all layouts
        for layout in [self.player_cards_layout, self.dealer_cards_layout, self.community_cards_layout]:
            while layout.count(): # Loop while there are widgets in the layout
                child = layout.takeAt(0) # Take the first item from the layout
                if child.widget(): # If the item is a widget
                    child.widget().deleteLater() # Delete the widget to free resources

        # Display player's cards
        for card_obj in self.player_hand:
            label = QLabel(card_obj.printCard()) # Create a label for each card
            label.setStyleSheet("border: 1px solid black; padding: 5px; background-color: white;") # Apply styling
            self.player_cards_layout.addWidget(label) # Add label to player's card layout

        # Display dealer's cards (only reveal after game ends)
        for i, card_obj in enumerate(self.dealer_hand):
            # If the play button is enabled, it means the game is in progress, so hide dealer's first card
            if self.playButton.isEnabled():
                label = QLabel("Hidden Card" if i == 0 else card_obj.printCard()) # Hide first card, show others
            else: # Game has ended, reveal all dealer cards
                label = QLabel(card_obj.printCard())
            label.setStyleSheet("border: 1px solid black; padding: 5px; background-color: white;") # Apply styling
            self.dealer_cards_layout.addWidget(label) # Add label to dealer's card layout

        # Display community cards
        for card_obj in self.community_cards:
            label = QLabel(card_obj.printCard()) # Create a label for each community card
            label.setStyleSheet("border: 1px solid black; padding: 5px; background-color: lightgray;") # Apply styling
            self.community_cards_layout.addWidget(label) # Add label to community card layout

    # HAND EVALUATION FUNCTIONS (These functions determine the type of poker hand)
    def Flush(self, hand):
        """
        Checks if a hand contains a Flush (5 or more cards of the same suit).
        Args:
            hand (list): A list of Card objects.
        Returns:
            bool: True if a flush exists, False otherwise.
        """
        held = [0, 0, 0, 0] # Initialize counts for each suit (Spades, Hearts, Diamonds, Clubs)
        for card_obj in hand:
            held[card_obj.suit - 1] += 1 # Increment count for the card's suit
        for count in held:
            if count >= 5: # If any suit has 5 or more cards
                return True # Returns True if a flush exists
        return False # No flush found

    def Straight(self, hand):
        """
        Checks if a hand contains a Straight (5 consecutive ranks).
        Handles Ace as both high (13) and low (0, for A-2-3-4-5).
        Args:
            hand (list): A list of Card objects.
        Returns:
            int: The highest rank of the straight if found, 0 otherwise.
        """
        # Extract ranks and sort them in ascending order
        sorted_ranks = sorted([card_obj.rank for card_obj in hand])
        # Get unique ranks to handle duplicates (e.g., in pairs, three of a kind)
        unique_ranks = sorted(list(set(sorted_ranks)))

        # Handle Ace as both 1 and 13 (high) for straight detection
        if 13 in unique_ranks: # If Ace is present (rank 13)
            unique_ranks.insert(0, 0) # Add a 'low' Ace (rank 0) to check for A-2-3-4-5 straight

        if len(unique_ranks) < 5:
            return 0 # Not enough unique ranks for a straight

        # Iterate through unique ranks to find 5 consecutive cards
        for i in range(len(unique_ranks) - 4):
            # Check if the 5th card in the sequence is exactly 4 ranks higher than the first
            if unique_ranks[i+4] == unique_ranks[i] + 4:
                return unique_ranks[i+4] # Return the highest rank of the straight
        return 0 # No straight found

    def StraightFlush(self, hand):
        """
        Checks if a hand contains a Straight Flush (5 consecutive ranks of the same suit).
        Args:
            hand (list): A list of Card objects.
        Returns:
            bool: True if a straight flush exists, False otherwise.
        """
        # Group cards by suit
        suits_grouped = {s: [] for s in range(1, 5)} # Dictionary to hold cards grouped by suit
        for card_obj in hand:
            suits_grouped[card_obj.suit].append(card_obj) # Add card to its respective suit list
            
        for suit in suits_grouped:
            if len(suits_grouped[suit]) >= 5: # If a suit has at least 5 cards
                # Check for a straight within this group of same-suited cards
                if self.Straight(suits_grouped[suit]) != 0:
                    return True # Straight Flush exists
        return False # No straight flush found

    def N_of_a_Kind(self, hand, n):
        """
        Checks for N-of-a-Kind (e.g., 2 for Pair, 3 for Three of a Kind, 4 for Four of a Kind).
        Args:
            hand (list): A list of Card objects.
            n (int): The number of cards of the same rank to check for.
        Returns:
            int: The rank of the N-of-a-kind if found, 0 otherwise.
        """
        ranks = [card_obj.rank for card_obj in hand] # Extract ranks from the hand
        from collections import Counter # Import Counter for easy counting of occurrences
        counts = Counter(ranks) # Count occurrences of each rank
        for rank, count in counts.items():
            if count == n: # If a rank appears 'n' times
                return rank # Return the rank of the N-of-a-kind
        return 0 # No N-of-a-kind found

    def OnePair(self, hand):
        """Convenience method to check for One Pair."""
        return self.N_of_a_Kind(hand, 2)

    def TwoPair(self, hand):
        """
        Checks if a hand contains Two Pair.
        Args:
            hand (list): A list of Card objects.
        Returns:
            int: The rank of the higher pair if two pairs exist, 0 otherwise.
        """
        ranks = [card_obj.rank for card_obj in hand] # Extract ranks
        from collections import Counter
        counts = Counter(ranks) # Count occurrences of each rank
        pairs = [rank for rank, count in counts.items() if count >= 2] # Find ranks with at least 2 cards
        if len(pairs) >= 2: # If two or more pairs are found
            return max(pairs) # Return the rank of the higher pair
        return 0 # No two pair found

    def ThreeKind(self, hand):
        """Convenience method to check for Three of a Kind."""
        return self.N_of_a_Kind(hand, 3)

    def FourKind(self, hand):
        """Convenience method to check for Four of a Kind."""
        return self.N_of_a_Kind(hand, 4)

    def FullHouse(self, hand):
        """
        Checks if a hand contains a Full House (Three of a Kind and a Pair).
        Args:
            hand (list): A list of Card objects.
        Returns:
            int: The rank of the three-of-a-kind if a full house exists, 0 otherwise.
        """
        ranks = [card_obj.rank for card_obj in hand] # Extract ranks
        from collections import Counter
        counts = Counter(ranks) # Count occurrences of each rank
        
        three_of_a_kind_rank = 0
        pair_rank = 0

        # Find the rank of the three-of-a-kind and a pair
        for rank, count in counts.items():
            if count == 3:
                three_of_a_kind_rank = rank
            elif count >= 2: # Use >=2 to catch cases like 3-of-a-kind and another 3-of-a-kind (which still forms a pair)
                pair_rank = rank
        
        # A full house requires both a three-of-a-kind and at least one pair.
        # Ensure the pair rank is not the same as the three-of-a-kind rank for a valid full house.
        if three_of_a_kind_rank != 0 and pair_rank != 0 and three_of_a_kind_rank != pair_rank:
            return three_of_a_kind_rank # Return the rank of the three-of-a-kind as the primary indicator
        # Handle case where there might be two sets of three-of-a-kind (e.g., 3 Kings, 3 Queens)
        # The higher three-of-a-kind forms the primary part, and one of the other cards forms the pair.
        if three_of_a_kind_rank != 0 and len([r for r, c in counts.items() if c >= 2]) >= 2:
            return three_of_a_kind_rank
        
        return 0 # No full house found

    def RoyalFlush(self, hand):
        """
        Checks if a hand contains a Royal Flush (10, J, Q, K, A of the same suit).
        Args:
            hand (list): A list of Card objects.
        Returns:
            bool: True if a royal flush exists, False otherwise.
        """
        # A Royal Flush is a Straight Flush (10, J, Q, K, A) of the same suit.
        # Check for Straight Flush first
        if not self.StraightFlush(hand):
            return False
        
        # Group cards by suit to check for the specific ranks within a suit
        suits_grouped = {s: [] for s in range(1, 5)}
        for card_obj in hand:
            suits_grouped[card_obj.suit].append(card_obj)
            
        for suit in suits_grouped:
            if len(suits_grouped[suit]) >= 5:
                # Get ranks of cards in this specific suit
                ranks_in_suit = sorted([c.rank for c in suits_grouped[suit]])
                # Check if the required ranks for a Royal Flush (10, J, Q, K, A) are present
                # Ranks: 9 (10), 10 (J), 11 (Q), 12 (K), 13 (A)
                if 9 in ranks_in_suit and 10 in ranks_in_suit and 11 in ranks_in_suit and 12 in ranks_in_suit and 13 in ranks_in_suit:
                    return True # Royal Flush found
        return False # No Royal Flush found

    def get_hand_rank(self, hand):
        """
        Determines the rank of the best possible 5-card poker hand from a given 7 cards (hole + community).
        It iterates through all 5-card combinations and evaluates each, returning the best one.
        Returns a tuple: (hand_type_rank, primary_rank, secondary_rank, kicker_ranks...)
        Hand types ranks (higher is better):
        9: Royal Flush
        8: Straight Flush
        7: Four of a Kind
        6: Full House
        5: Flush
        4: Straight
        3: Three of a Kind
        2: Two Pair
        1: One Pair
        0: High Card
        """
        # Import combinations from itertools for generating 5-card subsets
        from itertools import combinations
        best_rank = (0, 0) # Initialize with High Card (lowest possible hand)

        # Iterate through all possible 5-card combinations from the 7 available cards
        for five_card_hand in combinations(hand, 5):
            current_hand_rank = self._evaluate_five_card_hand(list(five_card_hand)) # Evaluate the current 5-card hand
            
            # Compare current hand with the best hand found so far
            if current_hand_rank[0] > best_rank[0]: # If current hand type is better
                best_rank = current_hand_rank
            elif current_hand_rank[0] == best_rank[0]: # If hand types are the same, apply tie-breaking rules
                # Tie-breaking logic based on primary rank, then secondary, then kickers
                if current_hand_rank[1] > best_rank[1]: # Compare primary rank (e.g., rank of pair, rank of straight)
                    best_rank = current_hand_rank
                elif current_hand_rank[1] == best_rank[1]:
                    # For hands like Two Pair, compare the second pair, then kicker
                    # This logic extends to compare subsequent elements in the hand rank tuple (kickers)
                    if len(current_hand_rank) > 2 and current_hand_rank[2] > best_rank[2]:
                        best_rank = current_hand_rank
                    elif len(current_hand_rank) > 2 and current_hand_rank[2] == best_rank[2]:
                        if len(current_hand_rank) > 3 and current_hand_rank[3] > best_rank[3]:
                            best_rank = current_hand_rank
                        elif len(current_hand_rank) > 3 and current_hand_rank[3] == best_rank[3]:
                            if len(current_hand_rank) > 4 and current_hand_rank[4] > best_rank[4]:
                                best_rank = current_hand_rank
                            elif len(current_hand_rank) > 4 and current_hand_rank[4] == best_rank[4]:
                                if len(current_hand_rank) > 5 and current_hand_rank[5] > best_rank[5]:
                                    best_rank = current_hand_rank
        return best_rank # Return the best hand rank found

    def _evaluate_five_card_hand(self, hand):
        """
        Helper function to evaluate a specific 5-card hand and determine its type and relevant ranks.
        Args:
            hand (list): A list of 5 Card objects.
        Returns:
            tuple: (hand_type_rank, primary_rank, secondary_rank, kicker_ranks...)
        """
        ranks = sorted([c.rank for c in hand], reverse=True) # Extract ranks and sort descending
        unique_ranks = sorted(list(set(ranks)), reverse=True) # Get unique ranks, sorted descending
        from collections import Counter
        counts = Counter(ranks) # Count occurrences of each rank

        is_flush = self.Flush(hand) # Check for a flush
        straight_high_card = self.Straight(hand) # Check for a straight

        # Evaluate hand types in descending order of poker hand strength

        # Royal Flush (highest possible hand)
        if self.RoyalFlush(hand):
            return (9, 13) # Hand type rank 9, Ace (13) as the high card

        # Straight Flush
        if straight_high_card != 0 and is_flush:
            return (8, straight_high_card) # Hand type rank 8, highest card of the straight

        # Four of a Kind
        four_kind_rank = self.N_of_a_Kind(hand, 4)
        if four_kind_rank != 0:
            # Find the kicker (the remaining card not part of the four-of-a-kind)
            kicker = next(r for r in unique_ranks if r != four_kind_rank)
            return (7, four_kind_rank, kicker) # Hand type rank 7, rank of 4-of-a-kind, kicker

        # Full House
        three_kind_rank = self.N_of_a_Kind(hand, 3)
        # Find a pair that is not part of the three-of-a-kind
        pair_rank = next((r for r, count in counts.items() if count >= 2 and r != three_kind_rank), 0)
        if three_kind_rank != 0 and pair_rank != 0:
            return (6, three_kind_rank, pair_rank) # Hand type rank 6, rank of 3-of-a-kind, rank of pair

        # Flush
        if is_flush:
            # Return hand type rank 5 and all 5 ranks as kickers (for tie-breaking)
            return (5, ranks[0], ranks[1], ranks[2], ranks[3], ranks[4])

        # Straight
        if straight_high_card != 0:
            return (4, straight_high_card) # Hand type rank 4, highest card of the straight

        # Three of a Kind
        if three_kind_rank != 0:
            # Find the two kickers (remaining cards not part of the three-of-a-kind)
            kickers = sorted([r for r in unique_ranks if r != three_kind_rank], reverse=True)
            return (3, three_kind_rank, kickers[0], kickers[1]) # Hand type rank 3, rank of 3-of-a-kind, two kickers

        # Two Pair
        pairs = sorted([rank for rank, count in counts.items() if count >= 2], reverse=True)
        if len(pairs) >= 2:
            # Find the kicker (the single remaining card)
            kicker = next(r for r in unique_ranks if r not in pairs)
            return (2, pairs[0], pairs[1], kicker) # Hand type rank 2, higher pair, lower pair, kicker

        # One Pair
        if len(pairs) == 1:
            # Find the three kickers (remaining cards not part of the pair)
            kicker_ranks = sorted([r for r in unique_ranks if r != pairs[0]], reverse=True)
            return (1, pairs[0], kicker_ranks[0], kicker_ranks[1], kicker_ranks[2]) # Hand type rank 1, rank of pair, three kickers

        # High Card (lowest hand type)
        # Return hand type rank 0 and all 5 ranks as kickers (for tie-breaking)
        return (0, ranks[0], ranks[1], ranks[2], ranks[3], ranks[4])


    def playGame(self):
        """
        Executes one round of Texas Hold'em Poker.
        Handles betting, dealing, hand evaluation, determining winner, and updating balance.
        """
        try:
            bet = float(self.betLine.text()) # Get bet amount from input field
            # Validate bet amount against game rules
            if not (5 <= bet <= 100):
                QMessageBox.warning(self, "Invalid Bet", "Bet must be between $5 and $100.")
                return
            # Validate bet amount against player's balance
            if bet > self.balance:
                QMessageBox.warning(self, "Insufficient Funds", f"You do not have enough balance. Your current balance is ${self.balance:.2f}.")
                return
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for your bet.")
            return

        self.current_bet = bet # Store the validated bet
        self.balance -= self.current_bet # Deduct bet from player's balance at the start of the round
        self.total_bets_session += self.current_bet # Accumulate total money bet for the session
        self.update_balance_label() # Update balance display on UI
        self.playButton.setEnabled(False) # Disable play button while game is in progress

        # Reset hands and deck for a new round
        self.player_hand.clear()
        self.dealer_hand.clear()
        self.community_cards.clear()
        self.deck.clear()
        self.label_win.setText("") # Clear previous win/loss message

        # Create a fresh standard 52-card deck
        full_deck = []
        for suit in range(1, 5): # Suits 1 to 4
            for rank in range(1, 14): # Ranks 1 (Ace) to 13 (King)
                full_deck.append(Card(suit, rank))
        random.shuffle(full_deck) # Shuffle the new deck
        self.deck = full_deck # Assign the shuffled deck to the game's deck

        # Deal hole cards (2 to player, 2 to dealer)
        self.player_hand.append(self.deck.pop()) # Deal first card to player
        self.dealer_hand.append(self.deck.pop()) # Deal first card to dealer
        self.player_hand.append(self.deck.pop()) # Deal second card to player
        self.dealer_hand.append(self.deck.pop()) # Deal second card to dealer

        # Deal community cards (Flop, Turn, River)
        # Flop (3 cards)
        self.community_cards.append(self.deck.pop())
        self.community_cards.append(self.deck.pop())
        self.community_cards.append(self.deck.pop())
        # Turn (1 card)
        self.community_cards.append(self.deck.pop())
        # River (1 card)
        self.community_cards.append(self.deck.pop())

        self.update_card_displays() # Update UI to show dealt cards (dealer's first card still hidden)

        # Determine best 5-card hands for player and dealer using their hole cards and community cards
        player_combined = self.player_hand + self.community_cards # Combine player's hole cards with community cards
        dealer_combined = self.dealer_hand + self.community_cards # Combine dealer's hole cards with community cards

        player_best_hand = self.get_hand_rank(player_combined) # Evaluate player's best hand
        dealer_best_hand = self.get_hand_rank(dealer_combined) # Evaluate dealer's best hand

        win_message = ""
        net_profit_loss_for_round = 0.0 # This will be the value saved to money_won in DB (profit/loss for this round)

        # Compare hands to determine the winner
        if player_best_hand > dealer_best_hand:
            win_message = f"You win with a {self._hand_type_to_string(player_best_hand[0])}!"
            self.balance += self.current_bet * 2 # Player gets original bet back + 1x profit
            net_profit_loss_for_round = self.current_bet # Player's profit is the bet amount
            self.wins_session += 1 # Increment session wins
            self.session_history.append(True) # Record win for cheater detection
        elif dealer_best_hand > player_best_hand:
            win_message = f"Dealer wins with a {self._hand_type_to_string(dealer_best_hand[0])}!"
            net_profit_loss_for_round = -self.current_bet # Player's loss is the bet amount
            self.losses_session += 1 # Increment session losses
            self.session_history.append(False) # Record loss for cheater detection
        else: # It's a tie
            win_message = "It's a tie! Bet returned."
            self.balance += self.current_bet # Return original bet to player
            net_profit_loss_for_round = 0.0 # No profit, no loss
            self.session_history.append(False) # Treat tie as non-win for cheater detection

        self.total_winnings_session += net_profit_loss_for_round # Accumulate the profit/loss for the entire session
        self.label_win.setText(win_message) # Display the game outcome message
        self.update_balance_label() # Update balance display on UI
        self.save_user() # Save current game state to the database after each round

        # Cheater detection logic: Check if win rate is suspiciously high over the last 20 games
        if len(self.session_history) >= 20: # Ensure at least 20 games have been played
            recent_results = self.session_history[-20:] # Get the results of the last 20 games
            win_rate = sum(recent_results) / 20.0 # Calculate the win rate (sum of True's / 20)
            if win_rate >= 0.8: # If win rate is 80% or higher
                log_cheater(self.player_id, "Poker", win_rate) # Log the player as a cheater
                QMessageBox.warning(self, "Cheater Detected", f"You won {win_rate*100:.1f}% of your last 20 games and have been flagged.")
                self.back_to_menu() # Return player to main menu
                return

        # Check for game over condition (player runs out of money)
        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You ran out of money!")
            self.playButton.setEnabled(False) # Disable play button
            self.betLine.setEnabled(False) # Disable bet input
        else:
            self.playButton.setEnabled(True) # Re-enable play button for the next round

    def _hand_type_to_string(self, hand_type_rank):
        """
        Converts a numerical hand type rank to a human-readable string (e.g., 9 -> "Royal Flush").
        Args:
            hand_type_rank (int): The numerical rank of the poker hand type.
        Returns:
            str: The string representation of the hand type.
        """
        hand_types = {
            9: "Royal Flush", 8: "Straight Flush", 7: "Four of a Kind",
            6: "Full House", 5: "Flush", 4: "Straight",
            3: "Three of a Kind", 2: "Two Pair", 1: "One Pair", 0: "High Card"
        }
        return hand_types.get(hand_type_rank, "Unknown Hand") # Return string, or "Unknown Hand" if rank not found


    def validateBet(self):
        """
        This method is called when the PLAY button is clicked.
        It initiates the game round by calling playGame, which now handles its own validation.
        """
        self.playGame() # playGame now handles validation


    def save_user(self):
        """
        Saves the current game state (player balance) and session statistics (bets, wins, losses, net winnings)
        for the Poker game to the database.
        It updates an existing session entry or inserts a new one.
        """
        try:
            # Update player's general balance in the PLAYERS table
            self.cursor.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.player_id))

            # Check if an entry for the current session_number and player exists in the Poker table
            self.cursor.execute("SELECT 1 FROM Poker WHERE player_name=? AND session_number=?", (self.full_name, self.session_number))
            exists = self.cursor.fetchone() # Fetch result to see if entry exists

            # If an entry exists, update it
            if exists:
                self.cursor.execute("""
                    UPDATE Poker
                    SET number_of_bets = ?,
                        bet_amount = ?,
                        wins = ?,
                        losses = ?,
                        money_won = ?
                    WHERE player_name = ? AND session_number = ?
                """, (
                    self.wins_session + self.losses_session, # total rounds played in this session
                    self.total_bets_session, # total money bet in this session
                    self.wins_session, # total wins for this session
                    self.losses_session, # total losses for this session
                    self.total_winnings_session, # This is the accumulated net profit/loss for the session
                    self.full_name, # player's full name
                    self.session_number # current session number
                ))
            # If no entry exists, insert a new one
            else:
                self.cursor.execute("""
                    INSERT INTO Poker (player_name, number_of_bets, bet_amount, wins, losses, money_won, session_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.full_name,
                    self.wins_session + self.losses_session,
                    self.total_bets_session,
                    self.wins_session,
                    self.losses_session,
                    self.total_winnings_session, # This is the accumulated net profit/loss for the session
                    self.session_number
                ))
            self.conn.commit() # Commit changes to the database
        except Exception as e:
            print(f"DB Save Error: {e}") # Print error for debugging
            QMessageBox.critical(self, "Database Error", f"Failed to save game data: {e}") # Show critical error message

    def back_to_menu(self):
        """
        Returns to the main casino menu.
        Saves current game state before closing the Poker game window.
        """
        self.save_user() # Save current game state before exiting
        self.conn.close() # Close the database connection
        self.close() # Close the current Poker game window
        if self.parent_menu: # If a parent menu reference exists
            self.parent_menu.show() # Show the parent menu

    def plot_net_winnings(self):
        """
        Plots the cumulative net winnings over sessions for the Poker game.
        Fetches session data from the database and displays it as a line graph.
        """
        try:
            # Query for session number and money_won (net profit/loss) for the current player
            self.cursor.execute("""
                SELECT session_number, money_won FROM Poker
                WHERE player_name=? ORDER BY session_number
            """, (self.full_name,))
            rows = self.cursor.fetchall() # Fetch all results

            if not rows: # If no data is found for the player
                QMessageBox.information(self, "No Data", "No winnings history available for this player.")
                return

            cumulative_net_winnings = [] # List to store cumulative net winnings for plotting
            session_numbers = [] # List to store session numbers for plotting
            current_total_net = 0.0 # Running total of net winnings

            # Iterate through fetched rows to calculate cumulative net winnings
            for session_num, money_won_from_db in rows:
                if session_num is not None: # Ensure session number is valid
                    # money_won_from_db already represents the net profit/loss for that session
                    current_total_net += money_won_from_db # Add to the running total
                    cumulative_net_winnings.append(current_total_net) # Append cumulative total
                    session_numbers.append(int(session_num)) # Append session number

            # Create a new QWidget to host the graph window
            self.graph_window = QWidget() # Store as instance variable to prevent premature garbage collection
            self.graph_window.setWindowTitle("Net Winnings - Poker") # Set window title
            self.graph_window.setGeometry(150, 150, 600, 400) # Set window geometry

            layout = QVBoxLayout() # Create a vertical layout for the graph window
            self.graph_window.setLayout(layout) # Set the layout

            fig = Figure(figsize=(5, 4)) # Create a Matplotlib figure
            canvas = FigureCanvas(fig) # Create a FigureCanvas to embed the figure in PyQt6
            ax = fig.add_subplot(111) # Add a subplot to the figure

            # Plot the cumulative net winnings data
            ax.plot(session_numbers, cumulative_net_winnings, marker='o', color='brown')
            ax.set_title("Cumulative Net Winnings - Poker") # Set chart title
            ax.set_xlabel("Session Number") # Set x-axis label
            ax.set_ylabel("Net Winnings ($)") # Set y-axis label
            ax.grid(True) # Enable grid lines
            ax.set_xticks(session_numbers) # Set x-axis ticks to show all session numbers

            # Create a QLabel to display the final total net winnings
            total_label = QLabel(f"Total Net Winnings: ${current_total_net:.2f}")
            total_label.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center-align the label

            layout.addWidget(canvas) # Add the Matplotlib canvas to the layout
            layout.addWidget(total_label) # Add the total winnings label to the layout

            self.graph_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose) # Ensure widget is deleted on close
            self.graph_window.show() # Show the graph window
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot winnings: {e}") # Show error message if plotting fails
