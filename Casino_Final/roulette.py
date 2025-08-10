#Import the random module for simulating the roulette spin
import random
#Import sqlite3 to interact with the CasinoDB SQLite database
import sqlite3
#Import pyplot from matplotlib for plotting graphs
import matplotlib.pyplot as plt
#Import PyQt6 widgets to build the GUI
from PyQt6.QtWidgets import (
    #Import necessary UI elements
    QWidget, QLabel, QPushButton, QLineEdit,
    #Import layouts and message box
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox, QTableWidget, QTableWidgetItem
)
#Import abstract item view for edit triggers
from PyQt6.QtWidgets import QAbstractItemView
#Import Qt for alignment and text formatting
from PyQt6.QtCore import Qt
#Import function to log cheaters based on high win rates
from cheaters import log_cheater
#Import canvas for displaying matplotlib graph in GUI
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#Import Figure to create custom plot figures
from matplotlib.figure import Figure

#Define path to the SQLite database
DB_PATH = "CasinoDB.db"

#Create the RouletteGame class that inherits from QWidget
class RouletteGame(QWidget):
    #Constructor to initialize the game window
    def __init__(self, player_id, parent_menu=None):
        #Call the parent constructor
        super().__init__()
        #Set the title of the window
        self.setWindowTitle("Roulette")
        #Set window position and size
        self.setGeometry(100, 100, 800, 700)
        #Store the current player's ID
        self.player_id = player_id
        #Store the reference to the main menu for navigation
        self.parent_menu = parent_menu

        #Connect to the SQLite database
        self.conn = sqlite3.connect(DB_PATH)
        #Create a cursor to execute SQL queries
        self.cur = self.conn.cursor()
        #Fetch the current player's balance
        self.cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))
        #Store the retrieved balance
        self.balance = self.cur.fetchone()[0]

        #Determine the next session number for the player
        self.session_number = self.get_next_session_number()

        #Initialize total number of wins
        self.winner = 0
        #Initialize total number of losses
        self.loser = 0
        #Initialize win percentage
        self.wl = 0
        #Initialize total number of bets played
        self.tot_bet_played = 0
        #Initialize total money bet
        self.tot_bet_money = 0
        #Initialize total money won
        self.r_tot_won = 0
        #Initialize total money lost
        self.r_tot_loss = 0
        #Initialize history to track wins/losses per spin
        self.session_history = []
        # Initialize self.graph_window to None, it will be assigned when plot_net_winnings is called
        self.graph_window = None
        
        self.bets = {}

        #Define set of red numbers
        self.red = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        #Define set of black numbers
        self.black = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
        #Define set of green numbers (only 0 in roulette)
        self.green = {0}

        #Create the main vertical layout for the GUI
        main_layout = QVBoxLayout()

        #Create label to display current balance
        self.balance_label = QLabel(f"Player Balance: ${self.balance}")
        #Instructional label for bet amount
        self.bet_help_label = QLabel("Place Bet Amount by Clicking on Displayed Values<br>or Enter a Value in the Text box")
        #Enable HTML formatting for the label
        self.bet_help_label.setTextFormat(Qt.TextFormat.RichText)
        #Instructional label for bet type
        self.bet_directions_label = QLabel("Place Bet Type by Clicking on Displayed Values<br>or Enter a Value in the Text box")
        #Enable HTML formatting for the label
        self.bet_directions_label.setTextFormat(Qt.TextFormat.RichText)

        #Input field for entering bet amount
        self.bet_amount_input = QLineEdit()
        #Set placeholder text
        self.bet_amount_input.setPlaceholderText("Enter bet amount (e.g., 5)")
        #Input field for entering bet type
        self.bet_type_input = QLineEdit()
        #Set placeholder text
        self.bet_type_input.setPlaceholderText("Enter bet (e.g., 17, red, 1-12, even)")
        
        self.add_bet_button = QPushButton("Add Bet")
        self.add_bet_button.clicked.connect(self.add_bet)

        #Button to trigger the roulette spin
        self.spin_button = QPushButton("Spin")
        #Connect button to spin handler
        self.spin_button.clicked.connect(self.play_spin)
        #Button to return to the main menu
        back_button = QPushButton("Back to Menu")
        #Connect button to back handler
        back_button.clicked.connect(self.back_to_menu)

        #Button to view net winnings graph
        net_button = QPushButton("Net Winnings")
        #Connect button to graph plotter
        net_button.clicked.connect(self.plot_net_winnings)

        #Create horizontal layout for input widgets
        input_layout = QHBoxLayout()
        #Add bet amount input field
        input_layout.addWidget(self.bet_amount_input)
        #Add bet type input field
        input_layout.addWidget(self.bet_type_input)
        input_layout.addWidget(self.add_bet_button)
        #Add spin button
        input_layout.addWidget(self.spin_button)
        #Add back button
        input_layout.addWidget(back_button)
        #Add net winnings button
        input_layout.addWidget(net_button)

        #Add balance label to main layout
        main_layout.addWidget(self.balance_label)
        #Add bet help label to main layout
        main_layout.addWidget(self.bet_help_label)
        #Add bet directions label to main layout
        main_layout.addWidget(self.bet_directions_label)
        #Add input layout to main layout
        main_layout.addLayout(input_layout)

        #List of chip denominations
        chip_values = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        #Chip colors
        chip_colors = ["#2196F3", "#4CAF50", "#9C27B0", "#F44336", "#FF9800",
                       "#B2DFDB", "#FFC107", "#673AB7", "#FFEB3B", "#00BCD4",
                       "#E91E63", "#8BC34A"]

        #Create grid layout for chips
        chip_layout = QGridLayout()
        #Loop through each chip value
        for index, value in enumerate(chip_values):
            #Create button for chip
            chip_button = QPushButton(f"${value}")
            #Set chip button size
            chip_button.setFixedSize(60, 60)
            #Style the chip
            chip_button.setStyleSheet(f"border-radius: 30px; border: 2px solid black; background-color: {chip_colors[index]}; font-weight: bold; color: black;")
            #Connect chip to selection handler
            chip_button.clicked.connect(lambda checked, v=value: self.select_chip_amount(v))
            #Add chip to layout
            chip_layout.addWidget(chip_button, index // 6, index % 6)

        #Add chip layout to main layout
        main_layout.addLayout(chip_layout)

        #Create layout for roulette table
        self.table_grid = QGridLayout()
        #Populate the roulette betting table
        self.build_roulette_grid()
        #Add roulette layout to main layout
        main_layout.addLayout(self.table_grid)
        
        self.bets_table = QTableWidget()
        self.bets_table.setColumnCount(2)
        self.bets_table.setHorizontalHeaderLabels(["Bet Type", "Amount"])
        self.bets_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.bets_table)
        
        remove_bet_button = QPushButton("Remove Bet")
        remove_bet_button.clicked.connect(self.remove_bet)
        main_layout.addWidget(remove_bet_button)


        #Label for game messages
        self.output_label = QLabel("Player place your bet and spin the wheel!")
        #Enable word wrap
        self.output_label.setWordWrap(True)
        #Add output label to layout
        main_layout.addWidget(self.output_label)

        #Set the final layout for the window
        self.setLayout(main_layout)
        
        # Add a rules button to the roulette window
        rules_button = QPushButton("Rules")
        rules_button.clicked.connect(self.show_rules)
        main_layout.addWidget(rules_button)
        

    # Method to show the rules of the game
    def show_rules(self):
        rules_text = (
            "Roulette Rules:\n\n"
            "Goal: Predict which number the ball will land on.\n"
            "Gameplay:\n"
            "1. Place your bet(s) on the table by entering an amount and bet type (e.g., '17', 'red', '1-12', 'even').\n"
            "2. Click the 'Add Bet' button to add multiple bets for a single spin.\n"
            "3. Click 'Spin' to spin the wheel.\n"
            "4. The payout depends on the type of bet:\n"
            "   - Single number (straight up): 35 to 1\n"
            "   - Red/Black, Even/Odd: 1 to 1\n"
            "   - Dozens (1-12, 13-24, 25-36): 2 to 1"
        )
        QMessageBox.information(self, "Roulette Rules", rules_text)

    def add_bet(self):
        try:
            bet_amount = float(self.bet_amount_input.text())
            bet_type = self.bet_type_input.text().strip().lower()

            if not bet_type:
                QMessageBox.warning(self, "Invalid Input", "Please enter a bet type.")
                return
            if bet_amount <= 0 or bet_amount > self.balance:
                QMessageBox.warning(self, "Invalid Bet", f"Enter a valid bet amount, not exceeding your balance of ${self.balance:.2f}.")
                return

            self.bets[bet_type] = self.bets.get(bet_type, 0) + bet_amount
            self.balance -= bet_amount
            self.update_balance_label()
            self.update_bets_table()

            self.bet_amount_input.clear()
            self.bet_type_input.clear()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for the bet amount.")


    def remove_bet(self):
        selected_rows = self.bets_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a bet to remove.")
            return

        row = selected_rows[0].row()
        bet_type = self.bets_table.item(row, 0).text()
        amount_to_remove = self.bets[bet_type]

        del self.bets[bet_type]
        self.balance += amount_to_remove
        self.update_balance_label()
        self.update_bets_table()


    def update_bets_table(self):
        self.bets_table.setRowCount(len(self.bets))
        for i, (bet_type, amount) in enumerate(self.bets.items()):
            self.bets_table.setItem(i, 0, QTableWidgetItem(bet_type))
            self.bets_table.setItem(i, 1, QTableWidgetItem(f"${amount:.2f}"))
            
    def update_balance_label(self):
        self.balance_label.setText(f"Player Balance: ${self.balance:.2f}")

    #Retrieve the next session number from DB
    def get_next_session_number(self):
        #Fetch max session
        self.cur.execute("SELECT MAX(session_number) FROM Roulette WHERE player_name = (SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?)", (self.player_id,))
        result = self.cur.fetchone()[0]
        #Increment for new session
        return (result or 0) + 1

    #Add buttons for roulette grid
    def build_roulette_grid(self):
        #Green 0
        self.add_table_cell("0", 0, 0, color="green")
        #Three rows of numbers in roulette
        numbers = [[3,6,9,12,15,18,21,24,27,30,33,36],
                   [2,5,8,11,14,17,20,23,26,29,32,35],
                   [1,4,7,10,13,16,19,22,25,28,31,34]]
        #Loop through rows
        for row, nums in enumerate(numbers):
            #Loop through numbers
            for col, num in enumerate(nums):
                #Set color
                color = "red" if num in self.red else "black"
                #Add number
                self.add_table_cell(str(num), row, col+1, color)

        #First dozen
        self.add_table_cell("1-12", 3, 1, colspan=4)
        #Second dozen
        self.add_table_cell("13-24", 3, 5, colspan=4)
        #Third dozen
        self.add_table_cell("25-36", 3, 9, colspan=4)
        #Even
        self.add_table_cell("Even", 4, 1, colspan=2)
        #Odd
        self.add_table_cell("Odd", 4, 3, colspan=2)
        #Black
        self.add_table_cell("Black", 4, 5, colspan=2, color="black")
        #Red
        self.add_table_cell("Red", 4, 7, colspan=2, color="red")
    #Add a button cell to the roulette grid with optional color and column span
    def add_table_cell(self, text, row, col, color=None, colspan=1):
        #Create a button with the given text
        button = QPushButton(text)
        #Set fixed height for uniform appearance
        button.setFixedHeight(40)
        #If the cell should be red
        if color == "red":
            #Style for red cell
            button.setStyleSheet("background-color: red; color: white;")
        #If the cell should be black
        elif color == "black":
            #Style for black cell
            button.setStyleSheet("background-color: black; color: white;")
        #If the cell should be green
        elif color == "green":
            #Style for green cell
            button.setStyleSheet("background-color: green; color: white;")
        #Connect button click to bet type setter
        button.clicked.connect(lambda: self.handle_bet_selection(text.lower()))
        #Add the button to the grid layout
        self.table_grid.addWidget(button, row, col, 1, colspan)

    #Handle a table button click to populate bet type input
    def handle_bet_selection(self, bet_text):
        #Set the selected text as the bet type
        self.bet_type_input.setText(bet_text)

    #Handle a chip button click to populate bet amount input
    def select_chip_amount(self, amount):
        #Set the selected chip value as the bet amount
        self.bet_amount_input.setText(str(amount))

    #Main function to process a roulette spin
    def play_spin(self):
        if not self.bets:
            QMessageBox.warning(self, "No Bets", "Please place at least one bet before spinning.")
            return

        #Simulate roulette spin with a number from 0 to 36
        rolled = random.randint(0, 36)
        total_winnings = 0
        total_bet_for_round = sum(self.bets.values())
        
        # Process each bet
        for bet_type, bet_amount in self.bets.items():
            win = False
            payout = 0

            #If betting on a specific number
            if bet_type.isdigit():
                if int(bet_type) == rolled:
                    win = True
                    payout = bet_amount * 36
            #Betting on even
            elif bet_type == "even" and rolled != 0 and rolled % 2 == 0:
                win = True
                payout = bet_amount * 2
            #Betting on odd
            elif bet_type == "odd" and rolled % 2 == 1:
                win = True
                payout = bet_amount * 2
            #Betting on 1-12 range
            elif bet_type == "1-12" and 1 <= rolled <= 12:
                win = True
                payout = bet_amount * 3
            #Betting on 13-24 range
            elif bet_type == "13-24" and 13 <= rolled <= 24:
                win = True
                payout = bet_amount * 3
            #Betting on 25-36 range
            elif bet_type == "25-36" and 25 <= rolled <= 36:
                win = True
                payout = bet_amount * 3
            #Betting on red
            elif bet_type == "red" and rolled in self.red:
                win = True
                payout = bet_amount * 2
            #Betting on black
            elif bet_type == "black" and rolled in self.black:
                win = True
                payout = bet_amount * 2
            #Betting on green
            elif bet_type == "green" and rolled == 0:
                win = True
                payout = bet_amount * 35
                
            if win:
                total_winnings += payout

        net_winnings_for_round = total_winnings - total_bet_for_round
        
        self.balance += total_winnings
        
        if net_winnings_for_round > 0:
            self.session_history.append(True)
        else:
            self.session_history.append(False)
        
        self.tot_bet_money += total_bet_for_round
        self.tot_bet_played += 1
        self.r_tot_won += net_winnings_for_round
        self.r_tot_loss += total_bet_for_round

        # Update player balance in DB
        self.cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.player_id))
        
        self.cur.execute("""
            INSERT INTO Roulette (player_name, number_of_bets, bet_amount, wins, losses, money_won, session_number)
            VALUES ((SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID = ?), ?, ?, ?, ?, ?, ?)
        """, (self.player_id, self.tot_bet_played, self.tot_bet_money, self.winner, self.loser, self.r_tot_won, self.session_number))
        self.conn.commit()
        
        # Cheater detection logic
        if len(self.session_history) >= 20:
            recent = self.session_history[-20:]
            rate = sum(recent) / 20
            if rate >= 0.8:
                log_cheater(self.player_id, "Roulette", rate)
                QMessageBox.warning(self, "Cheater Detected", f"You won {rate*100:.1f}% of your last 20 games and have been flagged.")
                self.close()
                return

        # Update GUI
        self.bets.clear()
        self.bets_table.clearContents()
        self.bets_table.setRowCount(0)
        self.update_balance_label()
        
        result_message = f"Rolled: {rolled}\n"
        if net_winnings_for_round > 0:
            result_message += f"You WON ${net_winnings_for_round:.2f}!"
        elif net_winnings_for_round < 0:
            result_message += f"You LOST ${-net_winnings_for_round:.2f}."
        else:
            result_message += "It was a push."
        
        self.output_label.setText(
            f"{result_message}\n"
            f"Wins: {self.winner} | Losses: {self.loser} | Win %: {self.wl:.2f}%\n"
            f"Total Bets: {self.tot_bet_played} | Bet Total: ${self.tot_bet_money:.2f}\n"
            f"Total Winnings: ${self.r_tot_won:.2f} | Total Losses: ${self.r_tot_loss:.2f}"
        )

        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You're out of money!")
            self.spin_button.setEnabled(False)


    #Return to the parent menu
    def back_to_menu(self):
        #Close the DB connection
        self.conn.close()
        #Show the parent menu window
        self.parent_menu.show()
        #Close this game window
        self.close()

    def plot_net_winnings(self):
        #Query previous game sessions for this player
        self.cur.execute("""
            SELECT money_won, money_lost, session_number FROM Roulette
            WHERE player_name = (SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?)
            ORDER BY session_number
        """, (self.player_id,))
        #Fetch all results
        rows = self.cur.fetchall()

        #If there are no results
        if not rows:
            #Show info
            QMessageBox.information(self, "No Data", "No winnings history available for this player.")
            #Exit function
            return

        #List to hold cumulative net winnings
        cumulative = []
        #List to hold session numbers
        session_numbers = []
        #Initialize cumulative total
        total = 0
        #Iterate over result rows
        for money_won, money_lost, session_number in rows:
            #Skip if session number is missing
            if session_number is None:
                continue
            #Calculate net winnings for session
            net = money_won - money_lost
            #Add to cumulative total
            total += net
            #Store current total
            cumulative.append(total)
            #Store session number
            session_numbers.append(int(session_number))

        #Create a new window for the graph
        self.graph_window = QWidget()
        #Set window title
        self.graph_window.setWindowTitle("Net Winnings Graph")
        #Set window size and position
        self.graph_window.setGeometry(150, 150, 600, 400)

        #Create vertical layout for graph
        layout = QVBoxLayout()

        #Create matplotlib figure
        fig = Figure(figsize=(5, 4))
        #Create canvas to embed in GUI
        canvas = FigureCanvas(fig)
        #Add subplot to figure
        ax = fig.add_subplot(111)
        #Plot net winnings line
        ax.plot(session_numbers, cumulative, marker='o', color='blue')
        #Set x-axis ticks to session numbers
        ax.set_xticks(session_numbers)
        #Set graph title
        ax.set_title("Cumulative Net Winnings - Roulette")
        #Set x-axis label
        ax.set_xlabel("Session Number")
        #Set y-axis label
        ax.set_ylabel("Net Winnings ($)")
        #Enable grid lines
        ax.grid(True)

        #Add canvas to layout
        layout.addWidget(canvas)

        #Create label showing total net winnings
        total_label = QLabel(f"Total Net Winnings: ${total:.2f}")
        #Center the label text
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #Style the label
        total_label.setStyleSheet("font-size: 16px; font-weight: bold; padding-top: 10px;")
        #Add label to layout
        layout.addWidget(total_label)

        #Set layout for the graph window
        self.graph_window.setLayout(layout)
        #Show the graph window
        self.graph_window.show()

