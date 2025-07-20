# Import random module to simulate dice rolls
import random
# Import os module to work with file paths
import os
# Import sqlite3 for interacting with the SQLite database
import sqlite3
# Import necessary widgets from PyQt6 for GUI components
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, QMessageBox
)
# Import QPixmap to display dice images
from PyQt6.QtGui import QPixmap
# Import Qt for alignment and flags
from PyQt6.QtCore import Qt
# Import Matplotlib canvas for embedding plots
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# Import Figure class to create plots
from matplotlib.figure import Figure
# Import the function to flag suspected cheaters
from cheaters import log_cheater

# Define the path to the SQLite database
DB_PATH = "CasinoDB.db"

# Define the Craps game class inheriting from QMainWindow
class Craps(QMainWindow):
# Constructor for Craps game
    def __init__(self, user_id, parent_menu=None):
# Initialize parent QMainWindow
        super().__init__()
# Set window title
        self.setWindowTitle("Craps Game")
# Set window size and position
        self.setGeometry(200, 200, 600, 500)
# Store player ID
        self.user_id = user_id
# Store parent menu reference
        self.parent_menu = parent_menu
# Connect to database
        self.conn = sqlite3.connect(DB_PATH)
# Create a cursor object
        self.cur = self.conn.cursor()
# Fetch player balance
        self.cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.user_id,))
# Store player's balance
        self.balance = self.cur.fetchone()[0]
# Initialize bet amount
        self.bet = 0
# Initialize bet type
        self.bet_type = ""
# Initialize point value
        self.point = None
# Track games won
        self.games_won = 0
# Track games lost
        self.games_lost = 0
# Track total number of bets
        self.total_bets = 0
# Track total winnings
        self.winnings = 0
# Track win/loss history
        self.session_history = []
# Get the next session number
        self.session_number = self.get_next_session_number()
# Set up the GUI components
        self.setup_ui()
# Update the balance label
        self.update_balance_label()
    # Get the next session number from the database
    def get_next_session_number(self):
        # Query the highest session number for the player
        self.cur.execute("""
            SELECT MAX(session_number) FROM Craps 
            WHERE player_name = (SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?)
        """, (self.user_id,))
        # Fetch the result
        result = self.cur.fetchone()[0]
        # Return incremented or default session number
        return int(result) + 1 if result is not None else 1

    # Set up the GUI interface
    def setup_ui(self):
        # Create main widget container
        w = QWidget()
        # Set as central widget
        self.setCentralWidget(w)
        # Create main vertical layout
        layout = QVBoxLayout()

        # Label for displaying player balance
        self.balance_label = QLabel()
        # Add label to layout
        layout.addWidget(self.balance_label)

        # Horizontal layout for betting controls
        br = QHBoxLayout()
        # Input field for bet amount
        self.bet_input = QLineEdit()
        # Set placeholder text
        self.bet_input.setPlaceholderText("Enter bet amount")
        # Add input to layout
        br.addWidget(self.bet_input)
        # Dropdown for bet type selection
        self.bet_type_combo = QComboBox()
        # Add betting options
        self.bet_type_combo.addItems([
            "Pass Line", "Don't Pass", "Field", "Any 7",
            "Craps", "Hard 4", "Hard 6", "Hard 8", "Big 6 & 8"
        ])
        # Add combo box to layout
        br.addWidget(self.bet_type_combo)
        # Create place bet button
        pbtn = QPushButton("Place Bet")
        # Connect button to place_bet method
        pbtn.clicked.connect(self.place_bet)
        # Add button to layout
        br.addWidget(pbtn)
        # Add betting row to main layout
        layout.addLayout(br)

        # Horizontal layout for dice images
        dr = QHBoxLayout()
        # Label for first die
        self.die1_label = QLabel()
        # Label for second die
        self.die2_label = QLabel()
        # Loop through both dice
        for lbl in (self.die1_label, self.die2_label):
            # Set size of dice images
            lbl.setFixedSize(64, 64)
            # Add to dice row
            dr.addWidget(lbl)
        # Add dice row to main layout
        layout.addLayout(dr)

        # Create roll dice button
        self.roll_button = QPushButton("Roll Dice")
        # Disable initially until a bet is placed
        self.roll_button.setEnabled(False)
        # Connect button to roll_dice method
        self.roll_button.clicked.connect(self.roll_dice)
        # Add to layout
        layout.addWidget(self.roll_button)

        # Text box for output messages
        self.output_box = QTextEdit()
        # Make output read-only
        self.output_box.setReadOnly(True)
        # Add to layout
        layout.addWidget(self.output_box)

        # Button to view net winnings graph
        graph_btn = QPushButton("View Net Winnings")
        # Connect to graph plotting method
        graph_btn.clicked.connect(self.plot_net_winnings)
        # Add to layout
        layout.addWidget(graph_btn)

        # Button to return to main menu
        back_btn = QPushButton("Return to Main Menu")
        # Connect to back_to_menu method
        back_btn.clicked.connect(self.back_to_menu)
        # Add to layout
        layout.addWidget(back_btn)

        # Apply layout to widget
        w.setLayout(layout)
           # Append a message to the output box
    def log(self, msg):
        # Append the message to the output box
        self.output_box.append(msg)

    # Update the balance display label
    def update_balance_label(self):
        # Set the text to show current balance and player ID
        self.balance_label.setText(f"Player {self.user_id} - Balance: ${self.balance:.2f}")

    # Handle placing a new bet
    def place_bet(self):
        try:
            # Parse bet amount from input
            amt = float(self.bet_input.text())
            # Check for valid range
            if amt <= 0 or amt > self.balance:
                raise ValueError
        except ValueError:
            # Show warning on error
            QMessageBox.warning(self, "Invalid Bet", "Enter a valid amount.")
            return

        # Store bet amount
        self.bet = amt
        # Store selected bet type
        self.bet_type = self.bet_type_combo.currentText()
        # Deduct bet from balance
        self.balance -= self.bet
        # Increment total bets counter
        self.total_bets += 1
        # Update the balance label
        self.update_balance_label()
        # Log the bet
        self.log(f"Bet ${self.bet:.2f} on {self.bet_type}")
        # Enable the roll dice button
        self.roll_button.setEnabled(True)

    # Simulate rolling two dice
    def roll_dice(self):
        # Roll first die
        d1 = random.randint(1, 6)
        # Roll second die
        d2 = random.randint(1, 6)
        # Calculate total
        total = d1 + d2
        # Show dice images
        self.update_dice_images(d1, d2)
        # Resolve bet outcome
        self.resolve_bet(total, d1, d2)

    # Update dice image labels
    def update_dice_images(self, d1, d2):
        try:
            # Load image for first die and scale
            p1 = QPixmap(os.path.abspath(f"dice{d1}.png")).scaled(64, 64)
            # Load image for second die and scale
            p2 = QPixmap(os.path.abspath(f"dice{d2}.png")).scaled(64, 64)
            # Set pixmap for die 1
            self.die1_label.setPixmap(p1)
            # Set pixmap for die 2
            self.die2_label.setPixmap(p2)
        except Exception as e:
            # Log error
            self.log(f"Error loading dice images: {e}")

    # Determine result of the bet
    def resolve_bet(self, total, d1, d2):
        # Default to undetermined outcome
        won_round = None
        # Initial payout
        payout = 0
        # Default multiplier
        mult = 1
        # Initial roll message
        msg = f"Dice rolled: {d1} + {d2} = {total}"

        # Check if bet type is Any 7
        if self.bet_type == "Any 7":
            won_round = total == 7
            mult = 4
        # Check if bet type is Craps
        elif self.bet_type == "Craps":
            won_round = total in [2, 3, 12]
            mult = 7
        # Check if bet type is Field
        elif self.bet_type == "Field":
            won_round = total in [2, 3, 4, 9, 10, 11, 12]
            mult = 2
        # Default message if bet type has no logic
        else:
            msg += " No payout logic for this bet type."

        # If player won the round
        if won_round is True:
            payout = self.bet * (1 + mult)
            self.balance += payout
            self.winnings += self.bet * mult
            self.log(f"{msg} You win {mult}:1!")
            self.log(f"You won ${self.bet * mult:.2f}!")
            self.games_won += 1
        # If player lost the round
        elif won_round is False:
            self.log(f"{msg} You lose.")
            self.log(f"You lost ${self.bet:.2f}.")
            self.games_lost += 1
        # If no win/loss condition triggered
        else:
            self.log(msg)

        # Track outcome
        self.session_history.append(won_round is True)
        # Complete round
        self.finish_round()
    # Finalize the round
    def finish_round(self):
        # Disable the roll button
        self.roll_button.setEnabled(False)
        # Refresh the balance display
        self.update_balance_label()
        # Save player data to the database
        self.save_user()
        # If player is out of money
        if self.balance <= 0:
            # Notify game over
            QMessageBox.information(self, "Game Over", "You're out of money!")

    # Save current session to the database
    def save_user(self):
        # Update player balance
        self.cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.user_id))
        # Insert session summary into Craps table
        self.cur.execute("""
            INSERT INTO Craps (player_name, number_of_bets, bet_amount, wins, losses, money_won, session_number)
            VALUES ((SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID = ?), ?, ?, ?, ?, ?, ?)
        """, (self.user_id, self.total_bets, self.bet, self.games_won, self.games_lost, self.winnings, self.session_number))
        # Commit changes
        self.conn.commit()

    # Return to the main menu
    def back_to_menu(self):
        # Save user session
        self.save_user()
        # Close the current window
        self.close()
        # If parent menu exists
        if self.parent_menu:
            # Show the main menu
            self.parent_menu.show()

    # Plot cumulative net winnings by session
    def plot_net_winnings(self):
        # Query session data
        self.cur.execute("""
            SELECT session_number, money_won, bet_amount FROM Craps 
            WHERE player_name = (SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?)
            ORDER BY session_number ASC
        """, (self.user_id,))
        # Fetch all matching rows
        rows = self.cur.fetchall()

        # If no session data found
        if not rows:
            # Notify no data
            QMessageBox.information(self, "No Data", "No winnings history available for this player.")
            return

        # List to track cumulative net winnings
        cumulative = []
        # List to track session numbers
        session_numbers = []
        # Running total of net winnings
        total = 0

        # Loop through session data
        for session_number, money_won, bet_amount in rows:
            # Ensure session number exists
            if session_number is not None:
                # Calculate net gain/loss
                net = money_won - bet_amount
                # Update cumulative total
                total += net
                # Store cumulative value
                cumulative.append(total)
                # Track session number
                session_numbers.append(int(session_number))

        # Create window to show graph
        self.winnings_window = QWidget()
        # Set window title
        self.winnings_window.setWindowTitle("Net Winnings - Craps")
        # Set window size
        self.winnings_window.setGeometry(150, 150, 600, 400)

        # Create vertical layout
        layout = QVBoxLayout()
        # Set layout
        self.winnings_window.setLayout(layout)

        # Create Matplotlib figure
        figure = Figure()
        # Create canvas for figure
        canvas = FigureCanvas(figure)
        # Create subplot
        ax = figure.add_subplot(111)
        # Plot winnings
        ax.plot(session_numbers, cumulative, marker='o', color='green')
        # Set chart title
        ax.set_title("Cumulative Net Winnings - Craps")
        # Label X axis
        ax.set_xlabel("Session Number")
        # Label Y axis
        ax.set_ylabel("Net Winnings ($)")
        # Enable grid
        ax.grid(True)
        # Set x-axis ticks
        ax.set_xticks(session_numbers)

        # Create label for total net winnings
        total_label = QLabel(f"Total Net Winnings: ${total:.2f}")
        # Center-align the label
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add canvas to layout
        layout.addWidget(canvas)
        # Add total label to layout
        layout.addWidget(total_label)

        # Ensure widget is deleted on close
        self.winnings_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # Show the graph window
        self.winnings_window.show()
