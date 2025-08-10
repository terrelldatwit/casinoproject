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

# Define the database path
DB_PATH = "CasinoDB.db"

# Define the folder where dice images are stored (assumes a 'dice_images' subdirectory
# in the same directory as this script).
DICE_IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "dice_images")


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
        self.balance = self.fetch_balance_from_db()
        # Fetch player's full name
        self.full_name = self.fetch_player_name()

        # Initialize bet amount
        self.bet = 0.0
        # Initialize bet type
        self.bet_type = ""
        # Initialize point value (None when no point is established)
        self.point = None
        # Track games won (for cheater detection)
        self.games_won = 0
        # Track games lost (for cheater detection)
        self.games_lost = 0
        # Track total number of bets (for session statistics)
        self.total_bets_session = 0.0 # Renamed for clarity, total money bet in session
        # Track total winnings (actual money won, not including original bet back)
        self.total_winnings_session = 0.0 # Renamed for clarity, total money won in session
        # Track win/loss history for cheater detection (True for win, False for loss)
        self.session_history = []
        # Get the next session number for this game launch
        self.session_number = self.get_next_session_number()

        # Initialize self.winnings_window to None, it will be assigned when plot_net_winnings is called
        self.winnings_window = None

        # Set up the GUI components
        self.setup_ui()
        # Update the balance label
        self.update_balance_label()

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
                cur.execute("SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?", (self.user_id,))
                # Fetch the result
                result = cur.fetchone()
                # Return full name or player ID if not found
                return result[0] if result else str(self.user_id)
        # Handle any exceptions during database operation
        except Exception as e:
            # Print error for debugging
            print(f"Error fetching player name: {e}")
            # Return player ID as fallback
            return str(self.user_id)

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
                cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.user_id,))
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

    # Get the next session number from the database
    def get_next_session_number(self):
        # Query the highest session number for the player
        self.cur.execute("""
            SELECT MAX(session_number) FROM Craps
            WHERE player_name = ?
        """, (self.full_name,))
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
        self.balance_label.setText(f"Player {self.full_name} - Balance: ${self.balance:.2f}")

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
            QMessageBox.warning(self, "Invalid Bet", "Enter a valid amount within your balance.")
            return

        # Store bet amount
        self.bet = amt
        # Store selected bet type
        self.bet_type = self.bet_type_combo.currentText()
        self.balance -= self.bet
        self.total_bets_session += self.bet # Accumulate total money bet for the session
        self.update_balance_label()
        self.log(f"Bet ${self.bet:.2f} on {self.bet_type}")
        self.roll_button.setEnabled(True)

    # Simulate rolling two dice
    def roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total = d1 + d2
        self.update_dice_images(d1, d2)
        self.resolve_bet(total, d1, d2)

    # Update dice image labels
    def update_dice_images(self, d1, d2):
        try:
            # Construct absolute paths for dice images using the defined folder
            image_path1 = os.path.abspath(os.path.join(DICE_IMAGE_FOLDER, f"dice{d1}.png"))
            image_path2 = os.path.abspath(os.path.join(DICE_IMAGE_FOLDER, f"dice{d2}.png"))

            # Load image for first die and scale
            p1 = QPixmap(image_path1).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            # Load image for second die and scale
            p2 = QPixmap(image_path2).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            # Check if pixmaps loaded successfully
            if not p1.isNull():
                self.die1_label.setPixmap(p1)
            else:
                self.die1_label.setText(f"D1: {d1}") # Fallback text
                self.log(f"Error: dice{d1}.png not found at {image_path1}")

            if not p2.isNull():
                self.die2_label.setPixmap(p2)
            else:
                self.die2_label.setText(f"D2: {d2}") # Fallback text
                self.log(f"Error: dice{d2}.png not found at {image_path2}")

        except Exception as e:
            # Log error
            self.log(f"Error loading dice images: {e}")
            QMessageBox.warning(self, "Image Error", f"Failed to load dice images: {e}")


    def resolve_bet(self, total, d1, d2):
        """Evaluate each bet type, pay out or lose, then finish the round."""
        mult = 1
        won_round = None # True for win, False for loss, None for no decision (continue rolling)
        msg = f"Dice rolled: {d1} + {d2} = {total}. "

        # Pass Line
        if self.bet_type == "Pass Line":
            if self.point is None: # Come-out roll
                if total in (7, 11):
                    won_round = True
                    msg += "Pass Line wins!"
                elif total in (2, 3, 12):
                    won_round = False
                    msg += "Craps! Pass Line loses."
                else:
                    self.point = total
                    self.log(msg + f"Point is now {self.point}. Roll again.")
                    return # Continue rolling
            else: # Point is established
                if total == self.point:
                    won_round = True
                    msg += "Point hit! Pass Line wins."
                    self.point = None # Reset point
                elif total == 7:
                    won_round = False
                    msg += "Seven-out. Pass Line loses."
                    self.point = None # Reset point
                else:
                    self.log(msg + f"Point is {self.point}. Roll again.")
                    return # Continue rolling

        # Don't Pass
        elif self.bet_type == "Don't Pass":
            if self.point is None: # Come-out roll
                if total in (2, 3):
                    won_round = True
                    msg += "Don't Pass wins!"
                elif total == 12:
                    won_round = None # Push
                    msg += "Push on 12. Bet returned."
                    self.balance += self.bet # Return original bet
                    self.total_winnings_session += 0 # No net gain/loss
                elif total in (7, 11):
                    won_round = False
                    msg += "Don't Pass loses."
                else:
                    self.point = total
                    self.log(msg + f"Point is now {self.point}. Roll again.")
                    return # Continue rolling
            else: # Point is established
                if total == self.point:
                    won_round = False
                    msg += "Point hit. Don't Pass loses."
                    self.point = None # Reset point
                elif total == 7:
                    won_round = True
                    msg += "Seven-out! Don't Pass wins."
                    self.point = None # Reset point
                else:
                    self.log(msg + f"Point is {self.point}. Roll again.")
                    return # Continue rolling

        # Field
        elif self.bet_type == "Field":
            if total in (3, 4, 9, 10, 11):
                won_round = True
                msg += "Field bet wins 1:1!"
                mult = 1
            elif total in (2, 12):
                won_round = True
                msg += "Field bet wins 2:1!"
                mult = 2
            else:
                won_round = False
                msg += "Field bet loses."

        # Any 7
        elif self.bet_type == "Any 7":
            if total == 7:
                won_round = True
                msg += "Any 7 wins 4:1!"
                mult = 4
            else:
                won_round = False
                msg += "Any 7 loses."

        # Craps
        elif self.bet_type == "Craps":
            if total in (2, 3, 12):
                won_round = True
                msg += "Craps wins 7:1!"
                mult = 7
            else:
                won_round = False
                msg += "Craps loses."

        # Hard 4
        elif self.bet_type == "Hard 4":
            if total == 4 and d1 == d2:
                won_round = True
                msg += "Hard 4 hits! Pays 7:1"
                mult = 7
            elif total == 4 and d1 != d2:
                won_round = False
                msg += "Easy 4 hit. Hard 4 loses."
            elif total == 7:
                won_round = False
                msg += "Seven-out. Hard 4 loses."
            else:
                self.log(msg + "No decision; roll again for Hard 4.")
                return

        # Hard 6
        elif self.bet_type == "Hard 6":
            if total == 6 and d1 == d2:
                won_round = True
                msg += "Hard 6 hits! Pays 9:1"
                mult = 9
            elif total == 6 and d1 != d2:
                won_round = False
                msg += "Easy 6 hit. Hard 6 loses."
            elif total == 7:
                won_round = False
                msg += "Seven-out. Hard 6 loses."
            else:
                self.log(msg + "No decision; roll again for Hard 6.")
                return

        # Hard 8
        elif self.bet_type == "Hard 8":
            if total == 8 and d1 == d2:
                won_round = True
                msg += "Hard 8 hits! Pays 9:1"
                mult = 9
            elif total == 8 and d1 != d2:
                won_round = False
                msg += "Easy 8 hit. Hard 8 loses."
            elif total == 7:
                won_round = False
                msg += "Seven-out. Hard 8 loses."
            else:
                self.log(msg + "No decision; roll again for Hard 8.")
                return

        # Big 6 & 8 (This bet is typically placed on the come-out roll and stays until 7-out or 6/8 hit)
        # For simplicity, implementing as a one-roll bet here.
        elif self.bet_type == "Big 6 & 8":
            if total in (6, 8):
                won_round = True
                msg += "Big 6 & 8 wins 1:1!"
                mult = 1
            else:
                won_round = False
                msg += "Big 6 & 8 loses."

        # Apply result
        if won_round is True:
            self.win(msg, multiplier=mult)
            self.games_won += 1
            self.session_history.append(True) # Record win for cheater detection
        elif won_round is False:
            self.log(msg + f" You lost ${self.bet:.2f}.")
            self.games_lost += 1
            self.session_history.append(False) # Record loss for cheater detection
        else: # This case handles pushes (like Don't Pass on 12) where bet is returned
            self.log(msg)
            self.session_history.append(False) # Treat push as non-win for cheater detection

        self.finish_round()

        # Cheater detection logic
        if len(self.session_history) >= 20: # Check if enough games have been played
            recent_results = self.session_history[-20:] # Get the last 20 results
            win_rate = sum(recent_results) / 20.0 # Calculate win rate
            if win_rate >= 0.8: # If win rate is 80% or higher
                # Log the player as a cheater
                log_cheater(self.user_id, "Craps", win_rate)
                # Show a warning message to the player
                QMessageBox.warning(self, "Cheater Detected", f"You won {win_rate*100:.1f}% of your last 20 games and have been flagged.")
                # Return to the main menu
                self.back_to_menu()
                return # Exit the method early


    def win(self, message, multiplier=1):
        # Payout is original bet + (bet * multiplier)
        payout = self.bet + (self.bet * multiplier)
        self.balance += payout
        # Only add the profit (bet * multiplier) to total_winnings_session
        self.total_winnings_session += (self.bet * multiplier)
        self.log(message + f" You won ${self.bet * multiplier:.2f}!")


    def finish_round(self):
        self.roll_button.setEnabled(False)
        self.update_balance_label()
        self.save_user()
        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You are out of money.")
            # Optionally, reset game state or return to main menu if out of money
            self.back_to_menu()


    # Save current session to the database
    def save_user(self):
        try:
            # Update player balance
            self.cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.user_id))

            # Check if an entry for the current session_number and player exists in Craps table
            self.cur.execute("SELECT 1 FROM Craps WHERE player_name=? AND session_number=?", (self.full_name, self.session_number))
            exists = self.cur.fetchone()

            # If an entry exists, update it
            if exists:
                self.cur.execute("""
                    UPDATE Craps
                    SET number_of_bets = ?,
                        bet_amount = ?,
                        wins = ?,
                        losses = ?,
                        money_won = ?
                    WHERE player_name = ? AND session_number = ?
                """, (
                    self.games_won + self.games_lost, # total rounds played in this session
                    self.total_bets_session, # total money bet in this session
                    self.games_won,
                    self.games_lost,
                    self.total_winnings_session, # This now correctly represents accumulated profit
                    self.full_name,
                    self.session_number
                ))
            # If no entry exists, insert a new one
            else:
                self.cur.execute("""
                    INSERT INTO Craps (player_name, number_of_bets, bet_amount, wins, losses, money_won, session_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.full_name,
                    self.games_won + self.games_lost,
                    self.total_bets_session,
                    self.games_won,
                    self.games_lost,
                    self.total_winnings_session, # This now correctly represents accumulated profit
                    self.session_number
                ))
            # Commit changes
            self.conn.commit()
        except Exception as e:
            print(f"DB Save Error: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to save game data: {e}")

    # Return to the main menu
    def back_to_menu(self):
        # Save user session
        self.save_user()
        # Close the current window
        self.conn.close() # Close database connection
        self.close()
        # If parent menu exists
        if self.parent_menu:
            self.parent_menu.show()

    # Plot cumulative net winnings by session
    def plot_net_winnings(self):
        try:
            # Query session data
            self.cur.execute("""
                SELECT session_number, money_won, bet_amount FROM Craps
                WHERE player_name = ?
                ORDER BY session_number ASC
            """, (self.full_name,))
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
            # Running total of net winnings - UPDATED CALCULATION
            total_net_winnings = 0.0

            # Loop through session data
            for session_number, money_won_db, bet_amount_db in rows:
                # Ensure session number exists
                if session_number is not None:
                    # Calculate net gain/loss for this session: money_won (profit) - bet_amount (money lost)
                    # UPDATED: Now calculates as money_won minus money_lost (bet_amount represents money lost)
                    net_for_session = money_won_db - bet_amount_db
                    # Update cumulative total
                    total_net_winnings += net_for_session
                    # Store cumulative value
                    cumulative.append(total_net_winnings)
                    # Track session number
                    session_numbers.append(int(session_number))

            # Create window to show graph
            # Ensure this is an instance variable to prevent premature garbage collection
            self.winnings_graph_window = QWidget()
            # Set window title
            self.winnings_graph_window.setWindowTitle("Net Winnings - Craps")
            # Set window size
            self.winnings_graph_window.setGeometry(150, 150, 600, 400)

            # Create vertical layout
            layout = QVBoxLayout()
            # Set layout
            self.winnings_graph_window.setLayout(layout)

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

            # Create label for total net winnings - UPDATED CALCULATION
            total_label = QLabel(f"Total Net Winnings: ${total_net_winnings:.2f}")
            # Center-align the label
            total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Add canvas to layout
            layout.addWidget(canvas)
            # Add total label to layout
            layout.addWidget(total_label)

            # Ensure widget is deleted on close
            self.winnings_graph_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            # Show the graph window
            self.winnings_graph_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", f"Failed to plot winnings: {e}")

