# Casino_With_Admin.py

# Import system module for application arguments
import sys
# Import sqlite3 to interact with the SQLite database
import sqlite3
# Import required PyQt6 GUI classes
from PyQt6.QtWidgets import (
    # Import QApplication for managing the application's event loop
    QApplication,
    # Import QWidget as the base class for all user interface objects
    QWidget,
    # Import QLabel for displaying text or image information
    QLabel,
    # Import QPushButton for clickable buttons
    QPushButton,
    # Import QVBoxLayout for vertical arrangement of widgets
    QVBoxLayout,
    # Import QLineEdit for single-line text input
    QLineEdit,
    # Import QMessageBox for displaying modal dialogs with messages
    QMessageBox,
    # Import QInputDialog for simple input dialogs
    QInputDialog,
    QScrollArea
)
# Import FigureCanvasQTAgg for embedding Matplotlib figures into PyQt6 applications
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# Import Figure class from Matplotlib for creating plots
from matplotlib.figure import Figure
# Import Qt core for alignment and flags
from PyQt6.QtCore import Qt
# Import LoginMenu for the login screen
from login_menu import LoginMenu
# Import RouletteGame for the roulette game GUI
from roulette import RouletteGame
# Import Craps for the craps game GUI
from craps import Craps
# Import Blackjack for the blackjack game (Tkinter GUI)
from blackjack import Blackjack
# Import HighLowGame for the High/Low game
from highlow import HighLowGame
# Import SlotsGame for the Slots game
from slots import SlotsGame
# Import Poker for the Poker game
from poker import Poker 
# Import the CasinoAdminPanel
from casino_admin import CasinoAdminPanel


# Define the database path
DB_PATH = "CasinoDB.db"
CASINO_ID = 7589

class AdminMainMenu(QWidget):
    """
    A simple main menu for the administrator, providing access to the admin panel.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Menu")
        self.setGeometry(300, 300, 300, 150)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Welcome, Administrator!"))

        btn_admin_panel = QPushButton("Launch Admin Panel")
        btn_admin_panel.clicked.connect(self.launch_admin_panel)
        layout.addWidget(btn_admin_panel)

        # Add a button to go back to the login menu
        btn_back_to_login = QPushButton("Back to Login Menu")
        btn_back_to_login.clicked.connect(self.back_to_login)
        layout.addWidget(btn_back_to_login)

        self.setLayout(layout)

    def launch_admin_panel(self):
        """Launches the casino administration panel."""
        self.admin_window = CasinoAdminPanel(self)
        self.admin_window.show()
        self.hide()

    def back_to_login(self):
        """Closes the admin menu and re-opens the login menu."""
        self.login_menu = LoginMenu()
        self.login_menu.show()
        self.close()

# Define the MainMenu class inheriting from QWidget
class MainMenu(QWidget):
    # Constructor for MainMenu
    def __init__(self, player_id):
        # Initialize QWidget parent class
        super().__init__()
        # Set window title
        self.setWindowTitle("Casino Menu")
        # Set window size and position
        self.setGeometry(300, 300, 300, 250)
        # Store player ID
        self.player_id = player_id

        # Fetch the player's full name based on player_id
        self.full_name = self.fetch_player_name(player_id)


        # Create a vertical layout for the main menu
        layout = QVBoxLayout()
        # Add a label to the layout with instructions
        layout.addWidget(QLabel("Choose a game or exit:"))

        # Create a button for playing Roulette
        btn_roulette = QPushButton("Play Roulette")
        # Connect the button's clicked signal to the launch_roulette method
        btn_roulette.clicked.connect(self.launch_roulette)
        # Add the roulette button to the layout
        layout.addWidget(btn_roulette)

        # Create a button for playing Craps
        btn_craps = QPushButton("Play Craps")
        # Connect the button's clicked signal to the launch_craps method
        btn_craps.clicked.connect(self.launch_craps)
        # Add the craps button to the layout
        layout.addWidget(btn_craps)

        # Create a button for playing Blackjack
        btn_blackjack = QPushButton("Play Blackjack")
        # Connect the button's clicked signal to the launch_blackjack method
        btn_blackjack.clicked.connect(self.launch_blackjack)
        # Add the blackjack button to the layout
        layout.addWidget(btn_blackjack)

        # Create a button for playing High/Low
        btn_highlow = QPushButton("Play High/Low")
        # Connect the button's clicked signal to the launch_highlow method
        btn_highlow.clicked.connect(self.launch_highlow)
        # Add the High/Low button to the layout
        layout.addWidget(btn_highlow)

        # Create a button for playing Slots
        btn_slots = QPushButton("Play Slots")
        # Connect the button's clicked signal to the launch_slots method
        btn_slots.clicked.connect(self.launch_slots)
        # Add the Slots button to the layout
        layout.addWidget(btn_slots)

        # Create a button for playing Poker
        btn_poker = QPushButton("Play Poker")
        # Connect the button's clicked signal to the launch_poker method
        btn_poker.clicked.connect(self.launch_poker)
        # Add the Poker button to the layout
        layout.addWidget(btn_poker)

        # Create a button to view total net winnings
        btn_net = QPushButton("View Net Winnings")
        # Connect the button's clicked signal to the plot_total_net_winnings method
        btn_net.clicked.connect(self.plot_total_net_winnings)
        # Add the net winnings button to the layout
        layout.addWidget(btn_net)
        
        # Add a button to display the rules of all games
        rules_button = QPushButton("Game Rules")
        rules_button.clicked.connect(self.show_game_rules)
        layout.addWidget(rules_button)


        # Create an exit button for the casino
        btn_exit = QPushButton("Exit Casino")
        # Connect the button's clicked signal to the cash_out_on_exit method
        btn_exit.clicked.connect(self.cash_out_on_exit)
        # Add the exit button to the layout
        layout.addWidget(btn_exit)

        # Apply the created layout to the window
        self.setLayout(layout)

    # Method to display the rules for all games
    def show_game_rules(self):
        rules_text = (
            "**Blackjack Rules:**\n"
            "Goal: Beat the dealer's hand without going over 21.\n"
            "Card values: Face cards (J, Q, K) are 10, Aces are 11 or 1, others are their number value.\n"
            "Gameplay: You and the dealer get two cards. You can Hit (take a card), Stand (keep your hand), Double Down (double bet and take one card), or Split (if cards are the same value).\n\n"

            "**Roulette Rules:**\n"
            "Goal: Predict which number the ball will land on.\n"
            "Gameplay: Place your bet(s) on numbers, colors (red/black), or groups (e.g., odds/evens, dozens). The wheel is spun and the winning number is announced.\n\n"
            
            "**Craps Rules:**\n"
            "Goal: Bet on the outcome of a pair of dice.\n"
            "Gameplay: On the 'come-out' roll, a 7 or 11 wins for 'Pass Line' bets. A 2, 3, or 12 loses. Any other number becomes the 'point'. The shooter then rolls until they hit the 'point' (win) or a 7 (lose).\n\n"
            
            "**High/Low Rules:**\n"
            "Goal: Guess if the next card will be higher or lower than the current card.\n"
            "Gameplay: Place a bet and a starting card is drawn. Guess 'Higher' or 'Lower'. A correct guess lets you continue the streak and build up winnings to cash out. An incorrect guess or a tie ends the streak.\n\n"
            
            "**Slots Rules:**\n"
            "Goal: Match symbols on a spinning reel.\n"
            "Gameplay: Place a bet and spin the reels. Winnings are paid out based on matching symbols in various combinations.\n\n"
            
            "**Poker Rules:**\n"
            "Goal: Create the best five-card poker hand using your two 'hole' cards and five community cards.\n"
            "Gameplay: The game is a simplified Texas Hold'em. You place a bet, and the winner is determined by who has the best hand after all community cards are dealt.\n"
        )
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Game Rules")
        msg_box.setText(rules_text)
        msg_box.show()

    # Method to fetch the player's full name from the database
    def fetch_player_name(self, player_id):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                cur = conn.cursor()
                cur.execute("SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?", (player_id,))
                result = cur.fetchone()
                return result[0] if result else str(player_id)
        except Exception as e:
            print(f"Error fetching player name: {e}")
            return str(player_id)

    # Method to launch the Roulette game
    def launch_roulette(self):
        # Create an instance of the RouletteGame, passing player ID and self (MainMenu) as parent
        self.game_window = RouletteGame(self.player_id, self)
        # Show the roulette game window
        self.game_window.show()
        # Hide the current MainMenu window
        self.hide()

    # Method to launch the Craps game
    def launch_craps(self):
        # Create an instance of the Craps game, passing player ID and self (MainMenu) as parent
        self.game_window = Craps(self.player_id, self)
        # Show the craps game window
        self.game_window.show()
        # Hide the current MainMenu window
        self.hide()

    # Method to launch the Blackjack game (which uses Tkinter)
    def launch_blackjack(self):
        # Hide the MainMenu BEFORE launching Blackjack to prevent display issues
        self.hide()
        # Create an instance of the Blackjack game, passing player ID and self (MainMenu) as parent
        self.blackjack_game = Blackjack(self.player_id, self) # Keep reference to the game instance

    # Method to launch the High/Low game
    def launch_highlow(self):
        # Hide the MainMenu BEFORE launching High/Low
        self.hide()
        # Create an instance of the HighLowGame, passing player ID and self (MainMenu) as parent
        self.highlow_game = HighLowGame(self.player_id, self) # Keep reference to the game instance

    # Method to launch the Slots game
    def launch_slots(self):
        # Hide the MainMenu BEFORE launching Slots
        self.hide()
        # Create an instance of the SlotsGame, passing player ID and self (MainMenu) as parent
        self.slots_game = SlotsGame(self.player_id, self) # Keep reference to the game instance

    # Method to launch the Poker game
    def launch_poker(self):
        # Hide the MainMenu BEFORE launching Poker
        self.hide()
        # Create an instance of the Poker game, passing player ID and self (MainMenu) as parent
        self.poker_game = Poker(self.player_id, self) # Keep reference to the game instance
        self.poker_game.show() # Show the Poker game window

    # Method to handle cashing out when exiting the casino
    def cash_out_on_exit(self):
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        # Create a cursor object
        cur = conn.cursor()
        # Execute a query to get the player's current balance
        cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))
        # Fetch the result
        result = cur.fetchone()
        
        # If player not found in the database
        if not result:
            # Show a warning message
            QMessageBox.warning(self, "Error", "Player not found.")
            # Close the database connection
            conn.close()
            # Close the current window
            self.close()
            # Exit the method
            return

        # Get the current balance from the query result
        current_balance = result[0]

        # Open an input dialog to ask the user how much they want to cash out
        cashout_amt, ok = QInputDialog.getDouble(
            self, "Cash Out",
            f"Your balance is ${current_balance:.2f}. How much would you like to cash out?",
            decimals=2
        )

        # If the user clicked OK in the input dialog
        if ok:
            if not (0 < cashout_amt <= current_balance):
                QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than 0 and not exceed your balance.")
                conn.close()
                return

            # Calculate the new balance after cashout
            new_balance = current_balance - cashout_amt
            
            # Update the player's balance in the PLAYERS table
            cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (new_balance, self.player_id))
            
            # Update the total_cashout in the CASINO table
            cur.execute("UPDATE CASINO SET total_cashout = total_cashout + ? WHERE id = ?", (cashout_amt, CASINO_ID))

            # Commit the changes to the database
            conn.commit()
            
            # Show an information message confirming the cashout
            QMessageBox.information(self, "Cash Out", f"You cashed out ${cashout_amt:.2f}")

        # Close the database connection
        conn.close()
        # Close the current MainMenu window
        self.close()

    # Method to plot total net winnings across all games for the logged-in player
    def plot_total_net_winnings(self):
        # Connect to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        # Create a cursor object
        cur = conn.cursor()

        # Get the player's full name for querying game tables
        player_name = self.full_name

        # List of game tables to query for winnings data
        game_tables = ["Blackjack", "Craps", "HighLow", "Poker", "Roulette", "Slots"]

        # Initialize a list to store all individual session net winnings
        all_session_data = []

        # Iterate through each game table
        for game_table in game_tables:
            try:
                # Query for session_number, money_won, and bet_amount for the current player
                cur.execute(f"""
                    SELECT session_number, money_won, bet_amount FROM {game_table}
                    WHERE player_name=?
                """, (player_name,))
                rows = cur.fetchall()

                # Collect session data, ensuring session number is valid
                for session_num, money_won, bet_amount in rows:
                    if session_num is not None:
                        # Handle inconsistent money_won column
                        if game_table in ["Slots", "HighLow"]:
                            net_for_session = money_won - bet_amount
                        else:
                            net_for_session = money_won
                        all_session_data.append((int(session_num), net_for_session))
            except sqlite3.OperationalError:
                # If a table doesn't exist, skip it
                print(f"Table {game_table} not found or accessible. Skipping.")
                continue
            except Exception as e:
                print(f"Error fetching data from {game_table}: {e}")
                continue

        # Close the database connection
        conn.close()

        # If no winnings data is available across all games for the player
        if not all_session_data:
            QMessageBox.information(self, "No Data", "No total winnings history available for this player across all games.")
            return

        # Sort all session data by session number to maintain the correct order for the plot
        all_session_data.sort(key=lambda x: x[0])

        # Extract sorted session numbers and net winnings
        sorted_session_numbers = [item[0] for item in all_session_data]
        sorted_net_winnings = [item[1] for item in all_session_data]

        # Calculate cumulative net winnings
        cumulative_winnings = []
        current_sum = 0.0
        for net_value in sorted_net_winnings:
            current_sum += net_value
            cumulative_winnings.append(current_sum)

        # Generate session numbers for plotting (simple sequential numbers for the cumulative plot)
        plot_session_numbers = list(range(1, len(cumulative_winnings) + 1))

        # Create a new QWidget for the graph window
        self.graph_window = QWidget()
        self.graph_window.setWindowTitle(f"Total Net Winnings - {player_name}")
        self.graph_window.setGeometry(150, 150, 800, 500)

        # Create vertical layout for the graph window
        layout = QVBoxLayout()
        self.graph_window.setLayout(layout)

        # Create a Matplotlib figure
        fig = Figure(figsize=(8, 6))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # Plot the cumulative net winnings
        ax.plot(plot_session_numbers, cumulative_winnings, marker='o', linestyle='-', color='blue')
        ax.set_title(f"Cumulative Net Winnings Across All Games for {player_name}")
        ax.set_xlabel("Session Number (across all games)")
        ax.set_ylabel("Net Winnings ($)")
        ax.grid(True)
        
        # Set x-axis ticks to show all session numbers if not too many
        if len(plot_session_numbers) <= 20:
            ax.set_xticks(plot_session_numbers)
        else:
            step = max(1, len(plot_session_numbers) // 10)
            ax.set_xticks(plot_session_numbers[::step])


        # Create label for total net winnings (final value of the cumulative sum)
        total_label = QLabel(f"Overall Net Winnings: ${cumulative_winnings[-1]:.2f}")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 10px;")

        # Add canvas and label to layout
        layout.addWidget(canvas)
        layout.addWidget(total_label)

        # Ensure widget is deleted when closed to free up resources
        self.graph_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # Show the graph window
        self.graph_window.show()

# Define the DepositWindow class inheriting from QWidget
class DepositWindow(QWidget):
    # Constructor for DepositWindow
    def __init__(self, player_id, full_name):
        # Initialize QWidget parent class
        super().__init__()
        # Set the window title
        self.setWindowTitle("Deposit")
        # Set the window size and position
        self.setGeometry(300, 300, 350, 250)
        # Store the player ID
        self.player_id = player_id
        # Store the player's full name
        self.full_name = full_name

        # Create a vertical layout
        self.layout = QVBoxLayout()
        # Set the layout for the window
        self.setLayout(self.layout)

        # Create a welcome label displaying the player's name
        self.welcome_label = QLabel(f"Welcome {self.full_name}!")
        # Add the welcome label to the layout
        self.layout.addWidget(self.welcome_label)

        # Create a QLineEdit for deposit amount input
        self.deposit_input = QLineEdit()
        # Set placeholder text for the deposit input field
        self.deposit_input.setPlaceholderText("Enter deposit amount")
        # Add the deposit input field to the layout
        self.layout.addWidget(self.deposit_input)

        # Create a deposit button
        deposit_button = QPushButton("Deposit")
        # Connect the deposit button's clicked signal to the handle_deposit method
        deposit_button.clicked.connect(self.handle_deposit)
        # Add the deposit button to the layout
        self.layout.addWidget(deposit_button)

        # Create a button to enter the casino
        self.start_button = QPushButton("Enter Casino")
        # Disable the start button initially
        self.start_button.setEnabled(False)
        # Connect the start button's clicked signal to the go_to_main_menu method
        self.start_button.clicked.connect(self.go_to_main_menu)
        # Add the start button to the layout
        self.layout.addWidget(self.start_button)

    # Method to handle the deposit action
    def handle_deposit(self):
        try:
            # Convert the text in the deposit input field to a float
            amount = float(self.deposit_input.text())
            # If the amount is negative
            if amount < 0:
                QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than 0.")
                return
            # Connect to the SQLite database
            conn = sqlite3.connect(DB_PATH)
            # Create a cursor object
            cur = conn.cursor()
            
            # Update the player's balance and total deposit in the PLAYERS table
            cur.execute("""
                UPDATE PLAYERS 
                SET balance = balance + ?, 
                    total_deposit = total_deposit + ?
                WHERE ID = ?
            """, (amount, amount, self.player_id))

            # Commit the changes to the database
            conn.commit()
            # Close the database connection
            conn.close()
            # Enable the start button after successful deposit
            self.start_button.setEnabled(True)
            QMessageBox.information(self, "Success", f"${amount:.2f} has been added to your balance.")
            
        # Catch any exceptions (e.g., ValueError for non-numeric input)
        except ValueError:
            # Show a warning message for invalid input
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred during deposit: {e}")


    # Method to navigate to the main menu
    def go_to_main_menu(self):
        # Create an instance of the MainMenu
        self.main_menu = MainMenu(self.player_id)
        # Show the main menu window
        self.main_menu.show()
        # Close the current DepositWindow
        self.close()

# Only launch the application if the script is run directly (not imported as a module)
if __name__ == "__main__":
    # Create a QApplication instance
    app = QApplication(sys.argv)
    # Create an instance of the LoginMenu
    login = LoginMenu()
    # Show the login menu window
    login.show()
    # Start the application's event loop
    sys.exit(app.exec())
