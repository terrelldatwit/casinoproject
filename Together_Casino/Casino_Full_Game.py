import sys  #Import system module for application arguments
import sqlite3  #Import sqlite3 to interact with the SQLite database
from PyQt6.QtWidgets import (  #Import required PyQt6 GUI classes
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QLineEdit, QMessageBox, QInputDialog
)
from login_menu import LoginMenu  #Import the LoginMenu class
from roulette import RouletteGame  #Import the RouletteGame class
from craps import Craps  #Import the Craps class
from HighLowSim import HighLowSim #import Highlow class

DB_PATH = "CasinoDB.db"  #Set constant path to the database

class MainMenu(QWidget):  #Main menu class inheriting from QWidget
    def __init__(self, player_id):  #Initialize the menu with player ID
        super().__init__()  #Initialize QWidget
        self.setWindowTitle("Casino Menu")  #Set window title
        self.setGeometry(300, 300, 300, 250)  #Set window size and position
        self.player_id = player_id  #Store player ID for use in menu

        layout = QVBoxLayout()  #Create vertical layout
        layout.addWidget(QLabel("Choose a game or exit:"))  #Instruction label

        btn_roulette = QPushButton("Play Roulette")  #Create roulette button
        btn_roulette.clicked.connect(self.launch_roulette)  #Connect to roulette launch method
        layout.addWidget(btn_roulette)  #Add to layout

        btn_craps = QPushButton("Play Craps")  #Create craps button
        btn_craps.clicked.connect(self.launch_craps)  #Connect to craps launch method
        layout.addWidget(btn_craps)  #Add to layout

        btn_craps = QPushButton("Play High Low")  #Create craps button
        btn_craps.clicked.connect(self.launch_HighLowSim)  #Connect to craps launch method
        layout.addWidget(btn_highlow)  #Add to layout

        btn_exit = QPushButton("Exit Casino")  #Create exit button
        btn_exit.clicked.connect(self.cash_out_on_exit)  #Connect to cash out method
        layout.addWidget(btn_exit)  #Add to layout

        self.setLayout(layout)  #Apply layout to window

    def launch_roulette(self):  #Launch the roulette game
        self.game_window = RouletteGame(self.player_id, self)  #Create Roulette game window
        self.game_window.show()  #Display it
        self.hide()  #Hide the menu window

    def launch_craps(self):  #Launch the craps game
        self.game_window = Craps(self.player_id, self)  #Create Craps game window
        self.game_window.show()  #Display it
        self.hide()  #Hide the menu window

    def launch_HighLow(self) 
        self.game_window = HighLow(self.player_id, self) 
        self.game_window.show()  #Display it
        self.hide()  #Hide the menu window

    def cash_out_on_exit(self):  #Handle player cash out
        conn = sqlite3.connect(DB_PATH)  #Connect to the database
        cur = conn.cursor()  #Create cursor
        cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))  #Fetch balance
        result = cur.fetchone()  #Store result
        conn.close()  #Close connection

        if not result:  #If no player found
            QMessageBox.warning(self, "Error", "Player not found.")  #Show warning
            self.close()  #Close window
            return  #Stop execution

        current_balance = result[0]  #Extract balance value

        cashout_amt, ok = QInputDialog.getDouble(self, "Cash Out", f"Your balance is ${current_balance:.2f}. How much would you like to cash out?", decimals=2)  #Prompt for cash out amount

        if ok:  #If user confirms
            if cashout_amt < 0:  #Negative values not allowed
                QMessageBox.warning(self, "Invalid Amount", "Amount must be greater than 0.")  #Show error
                return
            if cashout_amt > current_balance:  #Cannot cash out more than balance
                QMessageBox.warning(self, "Insufficient Funds", "You do not have enough balance.")  #Show error
                return

            new_balance = current_balance - cashout_amt  #Calculate new balance
            conn = sqlite3.connect(DB_PATH)  #Reconnect to database
            cur = conn.cursor()  #Create new cursor
            cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (new_balance, self.player_id))  #Update balance
            conn.commit()  #Save changes
            conn.close()  #Close connection

            QMessageBox.information(self, "Cash Out", f"You cashed out ${cashout_amt:.2f}")  #Show confirmation

        self.close()  #Close main menu window


class DepositWindow(QWidget):  #Deposit window class
    def __init__(self, player_id, full_name):  #Initialize with player ID and name
        super().__init__()  #Initialize QWidget
        self.setWindowTitle("Deposit")  #Set window title
        self.setGeometry(300, 300, 350, 250)  #Set geometry
        self.player_id = player_id  #Store player ID
        self.full_name = full_name  #Store player full name

        self.layout = QVBoxLayout()  #Create layout
        self.setLayout(self.layout)  #Apply layout

        self.welcome_label = QLabel(f"Welcome {self.full_name}!")  #Welcome message
        self.layout.addWidget(self.welcome_label)  #Add to layout

        self.deposit_input = QLineEdit()  #Input field for deposit
        self.deposit_input.setPlaceholderText("Enter deposit amount")  #Set placeholder
        self.layout.addWidget(self.deposit_input)  #Add to layout

        deposit_button = QPushButton("Deposit")  #Create deposit button
        deposit_button.clicked.connect(self.handle_deposit)  #Bind event
        self.layout.addWidget(deposit_button)  #Add to layout

        self.start_button = QPushButton("Enter Casino")  #Create start button
        self.start_button.setEnabled(False)  #Disable initially
        self.start_button.clicked.connect(self.go_to_main_menu)  #Bind event
        self.layout.addWidget(self.start_button)  #Add to layout

    def handle_deposit(self):  #Handle deposit logic
        try:
            amount = float(self.deposit_input.text())  #Convert text to float
            if amount < 0:  #Negative amounts not allowed
                raise ValueError

            conn = sqlite3.connect(DB_PATH)  #Connect to DB
            cur = conn.cursor()  #Create cursor
            cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))  #Fetch current balance
            result = cur.fetchone()  #Store result
            if not result:  #No match
                QMessageBox.warning(self, "Error", "Player not found.")  #Show error
                conn.close()  #Close connection
                return

            new_balance = result[0] + amount  #Calculate new balance
            cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (new_balance, self.player_id))  #Update record
            conn.commit()  #Commit changes
            conn.close()  #Close DB

            QMessageBox.information(self, "Deposit Successful", f"You deposited ${amount:.2f}")  #Success message
            self.start_button.setEnabled(True)  #Enable casino entry

        except:  #If any error occurs
            QMessageBox.warning(self, "Invalid Input", "Enter a valid number.")  #Show error

    def go_to_main_menu(self):  #Launch main menu
        self.main_menu = MainMenu(self.player_id)  #Create menu instance
        self.main_menu.show()  #Show menu
        self.close()  #Close deposit window


if __name__ == "__main__":  #If this script is the main entry
    app = QApplication(sys.argv)  #Create Qt application
    login = LoginMenu()  #Launch login window
    login.show()  #Display login window
    sys.exit(app.exec())  #Start application event loop
