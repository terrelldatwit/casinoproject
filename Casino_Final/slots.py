# Import necessary modules for GUI, random operations, database, and plotting
import sys
import random
import sqlite3
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox, QGridLayout
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# Import the cheaters logging function
from cheaters import log_cheater

# Define the database path
DB_PATH = "CasinoDB.db"

# Define the SlotsGame class, inheriting from QWidget for GUI capabilities
class SlotsGame(QWidget):
    # Constructor for the Slots game
    def __init__(self, player_id, parent_menu=None):
        # Call the parent QWidget constructor
        super().__init__()
        # Set the window title
        self.setWindowTitle("7s Frenzy Slots")
        # Set the window's position and size
        self.setGeometry(400, 150, 500, 650) # Adjusted geometry for better layout

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

        # Game state variables
        self.current_bet = 0.0
        self.total_winnings_session = 0.0 # Total net winnings for this entire game launch
        self.total_bets_session = 0.0 # Total money bet in this game launch
        self.wins_session = 0 # Total rounds won in this game launch
        self.losses_session = 0 # Total rounds lost in this game launch
        self.session_history = [] # Stores win/loss (True/False) for cheater detection

        # Get the next session number for this game launch
        self.session_number = self.get_next_session_number()

        # Initialize self.graph_window to None
        self.graph_window = None

        # Set up the graphical user interface elements
        self.setup_ui()
        # Update the balance display on the UI
        self.update_balance_label()

        # Show the Slots game window
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

    # Method to get the next available session number for the player in Slots game
    def get_next_session_number(self):
        try:
            # Execute query to find the maximum session number for the current player
            self.cur.execute("""
                SELECT MAX(session_number)
                FROM Slots
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

    # Map numbers to slot machine symbols
    def get_symbol(self, number):
        return {
            1: "🍒", # Cherry
            2: "🍋", # Lemon
            3: "🍇", # Grape
            4: "🍉", # Watermelon
            5: "🔔", # Bell
            6: "💎", # Diamond
            7: "💰"  # Money Bag (Jackpot symbol)
        }.get(number, "")

    # Set up the graphical user interface
    def setup_ui(self):
        # Create the main vertical layout for the window
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Balance label
        self.balance_label = QLabel(f"Balance: ${self.balance:.2f}")
        self.balance_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; margin-bottom: 15px;")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.balance_label)

        # Slot reels display
        self.reel_labels = []
        reel_layout = QHBoxLayout()
        for _ in range(3):
            label = QLabel("❓") # Placeholder for symbols
            label.setFixedSize(120, 120)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 60px; background-color: #f0f0f0; border: 2px solid #555; border-radius: 10px;")
            self.reel_labels.append(label)
            reel_layout.addWidget(label)
        main_layout.addLayout(reel_layout)

        # Result message label
        self.result_label = QLabel("Place your bet and spin!")
        self.result_label.setStyleSheet("font-size: 18px; font-style: italic; margin-top: 15px; margin-bottom: 15px;")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.result_label)

        # Bet input and spin button
        bet_layout = QHBoxLayout()
        self.bet_input = QLineEdit()
        self.bet_input.setPlaceholderText("Enter bet amount")
        self.bet_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 8px; font-size: 16px;")
        bet_layout.addWidget(self.bet_input)

        self.spin_button = QPushButton("Spin")
        self.spin_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.spin_button.clicked.connect(self.spin_slots)
        bet_layout.addWidget(self.spin_button)
        main_layout.addLayout(bet_layout)

        # Statistics section
        stats_group_box_layout = QVBoxLayout()
        stats_group_box = QWidget()
        stats_group_box.setLayout(stats_group_box_layout)
        stats_group_box.setStyleSheet("border: 1px solid #ddd; border-radius: 10px; padding: 10px; margin-top: 20px;")

        stats_group_box_layout.addWidget(QLabel("<b>Simulation Statistics:</b>").setStyleSheet("font-size: 16px; margin-bottom: 5px;"))
        self.total_bet_label = QLabel("Total Bet: $0.00")
        self.total_won_label = QLabel("Total Won by Player: $0.00")
        self.rtp_label = QLabel("Return to Player (RTP): 0.00%")
        self.house_edge_label = QLabel("House Edge: 0.00%")

        stats_group_box_layout.addWidget(self.total_bet_label)
        stats_group_box_layout.addWidget(self.total_won_label)
        stats_group_box_layout.addWidget(self.rtp_label)
        stats_group_box_layout.addWidget(self.house_edge_label)
        main_layout.addWidget(stats_group_box)

        # Action buttons (Net Winnings, Back to Main Menu)
        action_button_layout = QHBoxLayout()

        net_winnings_button = QPushButton("View Net Winnings")
        net_winnings_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #8e24aa;
            }
        """)
        net_winnings_button.clicked.connect(self.plot_net_winnings)
        action_button_layout.addWidget(net_winnings_button)

        back_button = QPushButton("Back to Main Menu")
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 10px;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        back_button.clicked.connect(self.back_to_menu)
        action_button_layout.addWidget(back_button)

        main_layout.addLayout(action_button_layout)

    # Update the balance display label on the GUI
    def update_balance_label(self):
        self.balance_label.setText(f"Balance: ${self.balance:.2f}")

    # Method to validate the bet amount entered by the user
    def validate_bet(self):
        try:
            bet = float(self.bet_input.text())
            if bet <= 0:
                QMessageBox.warning(self, "Invalid Bet", "Bet must be a positive number.")
                return None
            if bet > self.balance:
                QMessageBox.warning(self, "Invalid Bet", "You cannot bet more than your balance!")
                return None
            return bet
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for your bet.")
            return None

    # Simulate a spin of the slot machine
    def spin_slots(self):
        bet = self.validate_bet()
        if bet is None:
            return

        self.current_bet = bet
        self.balance -= self.current_bet
        self.total_bets_session += self.current_bet
        self.update_balance_label()

        symbols_rolled = []
        numbers_rolled = []
        for i in range(3):
            num = random.randint(1, 7)
            numbers_rolled.append(num)
            symbols_rolled.append(self.get_symbol(num))
            self.reel_labels[i].setText(symbols_rolled[i]) # Update reel display

        win_amount = 0.0
        win_message = ""
        won_round = False

        # Check for 3-line wins
        if numbers_rolled[0] == numbers_rolled[1] == numbers_rolled[2]:
            match = numbers_rolled[0]
            multiplier = {
                1: 50.0, # 777
                2: 30.0, # Lemon
                3: 20.0, # Grape
                4: 15.0, # Watermelon
                5: 10.0, # Bell
                6: 8.0,  # Diamond
                7: 6.0   # Money Bag
            }.get(match, 0.0)
            win_amount = self.current_bet * multiplier
            win_message = f"JACKPOT! Three {self.get_symbol(match)}s! Won ${win_amount:.2f}"
            won_round = True
        # Check for 2-line wins (consecutive)
        elif (numbers_rolled[0] == numbers_rolled[1]) or \
             (numbers_rolled[1] == numbers_rolled[2]):
            # Determine the matching symbol for the 2-line win
            match_num = numbers_rolled[1] if numbers_rolled[0] == numbers_rolled[1] else numbers_rolled[2]
            multiplier = {
                1: 2.5, # 7x
                2: 2.2, # Lemon
                3: 2.0, # Grape
                4: 1.8, # Watermelon
                5: 1.6, # Bell
                6: 1.4, # Diamond
                7: 1.2  # Money Bag
            }.get(match_num, 0.0)
            win_amount = self.current_bet * multiplier
            win_message = f"Two {self.get_symbol(match_num)}s! Won ${win_amount:.2f}"
            won_round = True
        else:
            win_message = "No win. Try again!"
            won_round = False

        self.balance += win_amount # Add winnings to balance
        self.total_winnings_session += win_amount # Accumulate total winnings for session

        if won_round:
            self.wins_session += 1
            self.session_history.append(True)
        else:
            self.losses_session += 1
            self.session_history.append(False)

        self.result_label.setText(f"{' | '.join(symbols_rolled)} - {win_message}")
        self.update_balance_label()
        self.save_user() # Save state after each spin

        self.update_statistics() # Update RTP/House Edge display

        # Cheater detection logic
        if len(self.session_history) >= 20: # Check if enough games have been played
            recent_results = self.session_history[-20:] # Get the last 20 results
            win_rate = sum(recent_results) / 20.0 # Calculate win rate
            if win_rate >= 0.8: # If win rate is 80% or higher
                # Log the player as a cheater
                log_cheater(self.player_id, "Slots", win_rate)
                # Show a warning message to the player
                QMessageBox.warning(self, "Cheater Detected", f"You won {win_rate*100:.1f}% of your last 20 games and have been flagged.")
                # Return to the main menu
                self.back_to_menu()
                return # Exit the method early

        # Check for game over (balance <= 0)
        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You ran out of money! Game resetting.")
            self.balance = self.fetch_balance_from_db() # Reload balance or set a default
            self.update_balance_label()
            self.result_label.setText("Game over. Please deposit more funds or restart.")
            self.spin_button.setEnabled(False) # Disable spin button
            self.bet_input.setEnabled(False)


    # Update RTP and House Edge statistics
    def update_statistics(self):
        total_spins = self.wins_session + self.losses_session
        if total_spins > 0:
            # Calculate total money won by player (gross winnings)
            # This needs to be the sum of all 'win_amount' from each spin
            # The current self.total_winnings_session already accumulates this
            total_gross_winnings = self.total_winnings_session

            # Calculate RTP based on total gross winnings and total bets
            rtp = (total_gross_winnings / self.total_bets_session) * 100 if self.total_bets_session > 0 else 0.0
            house_edge = 100.0 - rtp
        else:
            rtp = 0.0
            house_edge = 0.0

        self.total_bet_label.setText(f"Total Bet: ${self.total_bets_session:.2f}")
        self.total_won_label.setText(f"Total Won by Player: ${self.total_winnings_session:.2f}")
        self.rtp_label.setText(f"Return to Player (RTP): {rtp:.2f}%")
        self.house_edge_label.setText(f"House Edge: {house_edge:.2f}%")


    # Method to save current game state and session statistics to the database
    def save_user(self):
        try:
            # Update player's general balance in the PLAYERS table
            self.cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.player_id))

            # Check if an entry for the current session_number and player exists in Slots table
            self.cur.execute("SELECT 1 FROM Slots WHERE player_name=? AND session_number=?", (self.full_name, self.session_number))
            exists = self.cur.fetchone()

            # If an entry exists, update it
            if exists:
                self.cur.execute("""
                    UPDATE Slots
                    SET number_of_bets = ?,
                        bet_amount = ?,
                        wins = ?,
                        money_won = ?
                    WHERE player_name = ? AND session_number = ?
                """, (
                    self.wins_session + self.losses_session, # total rounds played in this session
                    self.total_bets_session,
                    self.wins_session,
                    self.total_winnings_session, # This is the accumulated gross winnings
                    self.full_name,
                    self.session_number
                ))
            # If no entry exists, insert a new one
            else:
                self.cur.execute("""
                    INSERT INTO Slots (player_name, number_of_bets, bet_amount, wins, money_won, session_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    self.full_name,
                    self.wins_session + self.losses_session,
                    self.total_bets_session,
                    self.wins_session,
                    self.total_winnings_session, # This is the accumulated gross winnings
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

    # Method to plot cumulative net winnings over sessions for Slots game
    def plot_net_winnings(self):
        try:
            # Execute query to fetch session data for plotting
            self.cur.execute("""
                SELECT session_number, money_won, bet_amount FROM Slots
                WHERE player_name=? ORDER BY session_number
            """, (self.full_name,))
            # Fetch all results
            rows = self.cur.fetchall()

            # If no data is found, show an information message
            if not rows:
                QMessageBox.information(self, "No Data", "No winnings history available for this player.")
                return

            # Initialize lists for cumulative net winnings and session numbers
            cumulative_net_winnings = []
            session_numbers = []
            current_total_net = 0.0 # Overall total net winnings for plotting

            # Iterate through fetched rows
            for session_num, money_won, bet_amount in rows:
                # Ensure session number is not None
                if session_num is not None:
                    # Calculate net winnings for this session (gross won - total bet for that session)
                    net_for_session = money_won - bet_amount
                    current_total_net += net_for_session # Add to overall cumulative total
                    cumulative_net_winnings.append(current_total_net) # Add to cumulative list
                    session_numbers.append(int(session_num)) # Add session number

            # Create a new QWidget for the graph window and store it as an instance variable
            # This prevents the window from being garbage collected and closing immediately
            self.graph_window = QWidget()
            # Set window title
            self.graph_window.setWindowTitle("Net Winnings - Slots")
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
            # Plot the cumulative net winnings
            ax.plot(session_numbers, cumulative_net_winnings, marker='o', color='purple')
            # Set chart title
            ax.set_title("Cumulative Net Winnings - Slots")
            # Set x-axis label
            ax.set_xlabel("Session Number")
            # Set y-axis label
            ax.set_ylabel("Net Winnings ($)")
            # Enable grid
            ax.grid(True)
            # Set x-axis ticks
            ax.set_xticks(session_numbers)

            # Create label for total net winnings (final value)
            total_label = QLabel(f"Total Net Winnings: ${current_total_net:.2f}")
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
