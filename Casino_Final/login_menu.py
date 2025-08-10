###Files to be updated:
#1.login_menu.py - add full name fetch and pass
#2.Casino_With_Admin.py - create DepositWindow with welcome label + cash-out feature

#Reprint of login_menu.py with required changes

import random  #Import the random module to generate random IDs and passwords
import sqlite3  #Import sqlite3 to interact with the database
from PyQt6.QtWidgets import (  #Import required PyQt6 GUI components
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)

DB_PATH = "CasinoDB.db"  #Define the path to the SQLite database
ADMIN_ID = 7589 # Hardcoded admin ID
ADMIN_PASS = "9857" # Hardcoded admin password

class LoginMenu(QWidget):  #Define the LoginMenu class inheriting from QWidget
    def __init__(self):  #Constructor for LoginMenu
        super().__init__()  #Call the constructor of QWidget
        self.setWindowTitle("Login Menu")  #Set the window title
        self.setGeometry(300, 300, 300, 250)  #Set window position and size

        layout = QVBoxLayout()  #Create a vertical layout

        self.id_input = QLineEdit()  #Create input field for user ID
        self.id_input.setPlaceholderText("Enter ID Number")  #Set placeholder text

        self.pw_input = QLineEdit()  #Create input field for password
        self.pw_input.setPlaceholderText("Enter Password")  #Set placeholder text
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)  #Set to password mode

        self.login_button = QPushButton("Login")  #Create login button
        self.login_button.clicked.connect(self.handle_login)  #Connect button to login logic

        self.create_button = QPushButton("Create New Login")  #Create account creation button
        self.create_button.clicked.connect(self.create_login_prompt)  #Connect button to open account creation window

        layout.addWidget(QLabel("Casino Login"))  #Add a label to the layout
        layout.addWidget(self.id_input)  #Add ID input field to layout
        layout.addWidget(self.pw_input)  #Add password input field to layout
        layout.addWidget(self.login_button)  #Add login button to layout
        layout.addWidget(self.create_button)  #Add account creation button to layout

        self.setLayout(layout)  #Set the main layout of the widget

    def handle_login(self):  #Function to handle login logic
        try:
            user_id_input = int(self.id_input.text())
            password = self.pw_input.text().strip()
        except ValueError:
            QMessageBox.warning(self, "Error", "Enter a valid numeric ID.")
            return

        # Admin Login Check
        if user_id_input == ADMIN_ID and password == ADMIN_PASS:
            self.launch_admin_menu()
            return

        # Player Login Logic
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT Password FROM Login WHERE ID=?", (user_id_input,))
        result = cur.fetchone()
        if not result or str(result[0]).strip() != password:
            QMessageBox.warning(self, "Login Failed", "Invalid ID or Password.")
            conn.close()
            return

        cur.execute("SELECT first_name, last_name FROM PLAYERS WHERE ID=?", (user_id_input,))
        name_result = cur.fetchone()
        conn.close()

        self.player_id = user_id_input
        self.full_name = f"{name_result[0]} {name_result[1]}" if name_result else "Player"
        self.launch_deposit()

    def launch_deposit(self):
        from Casino_With_Admin import DepositWindow
        self.deposit_window = DepositWindow(self.player_id, self.full_name)
        self.deposit_window.show()
        self.close()
        
    def launch_admin_menu(self):
        from Casino_With_Admin import AdminMainMenu
        self.admin_menu = AdminMainMenu()
        self.admin_menu.show()
        self.close()

    def create_login_prompt(self):
        self.create_window = CreateLoginWindow()
        self.create_window.show()
        self.close()


class CreateLoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Create New Login")
        self.setGeometry(300, 300, 300, 250)

        layout = QVBoxLayout()

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Enter First Name")

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Enter Last Name")

        self.submit_button = QPushButton("Create Account")
        self.submit_button.clicked.connect(self.create_account)

        layout.addWidget(QLabel("Create New Player"))
        layout.addWidget(self.first_name_input)
        layout.addWidget(self.last_name_input)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def create_account(self):
        fname = self.first_name_input.text().strip()
        lname = self.last_name_input.text().strip()

        if not fname or not lname:
            QMessageBox.warning(self, "Missing Info", "Please enter first and last name.")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        while True:
            new_id = random.randint(1000, 9999)
            cur.execute("SELECT 1 FROM PLAYERS WHERE ID=?", (new_id,))
            if not cur.fetchone():
                break

        while True:
            new_pw = str(random.randint(1000, 9999))
            cur.execute("SELECT 1 FROM Login WHERE Password=?", (new_pw,))
            if not cur.fetchone():
                break

        # Initialize total_deposit to 0 for new players
        cur.execute("INSERT INTO PLAYERS (ID, balance, first_name, last_name, total_deposit) VALUES (?, 0, ?, ?, 0)", (new_id, fname, lname))
        cur.execute("INSERT INTO Login (ID, Password) VALUES (?, ?)", (new_id, new_pw))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Account Created",
            f"Your ID: {new_id}\nYour Password: {new_pw}\nSave this info to log in.")

        from Casino_With_Admin import DepositWindow
        self.deposit_window = DepositWindow(new_id, f"{fname} {lname}")
        self.deposit_window.show()
        self.close()
