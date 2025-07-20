###Files to be updated:
#1.login_menu.py - add full name fetch and pass
#2.Casino_Full_Game.py - create DepositWindow with welcome label + cash-out feature

#Reprint of login_menu.py with required changes

import random  #Import the random module to generate random IDs and passwords
import sqlite3  #Import sqlite3 to interact with the database
from PyQt6.QtWidgets import (  #Import required PyQt6 GUI components
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)

DB_PATH = "CasinoDB.db"  #Define the path to the SQLite database

class LoginMenu(QWidget):  #Define the LoginMenu class inheriting from QWidget
    def __init__(self):  #Constructor for LoginMenu
        super().__init__()  #Call the constructor of QWidget
        self.setWindowTitle("Login Menu")  #Set the window title
        self.setGeometry(300, 300, 300, 250)  #Set window position and size

        layout = QVBoxLayout()  #Create a vertical layout

        self.id_input = QLineEdit()  #Create input field for user ID
        self.id_input.setPlaceholderText("Enter Player ID")  #Set placeholder text

        self.pw_input = QLineEdit()  #Create input field for password
        self.pw_input.setPlaceholderText("Enter Password")  #Set placeholder text
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Normal)  #Visible for testing

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
            self.player_id = int(self.id_input.text())  #Get and convert ID input
            password = self.pw_input.text().strip()  #Get and strip password input
        except:  #If input is invalid
            QMessageBox.warning(self, "Error", "Enter valid credentials.")  #Show error message
            return  #Exit function

        conn = sqlite3.connect(DB_PATH)  #Connect to the database
        cur = conn.cursor()  #Create a cursor object
        cur.execute("SELECT Password FROM Login WHERE ID=?", (self.player_id,))  #Query for password
        result = cur.fetchone()  #Fetch the result
        if not result or str(result[0]).strip() != password:  #Check if password is incorrect
            QMessageBox.warning(self, "Login Failed", "Invalid ID or Password.")  #Show error message
            conn.close()  #Close database connection
            return  #Exit function

        cur.execute("SELECT first_name, last_name FROM PLAYERS WHERE ID=?", (self.player_id,))  #Query for player name
        name_result = cur.fetchone()  #Fetch name result
        conn.close()  #Close the database connection

        self.full_name = f"{name_result[0]} {name_result[1]}"  #Combine first and last name
        self.launch_deposit()  #Launch deposit window

    def launch_deposit(self):  #Function to open the deposit window
        from Casino_Full_Game import DepositWindow  #Import DepositWindow class
        self.deposit_window = DepositWindow(self.player_id, self.full_name)  #Create deposit window instance
        self.deposit_window.show()  #Show the deposit window
        self.close()  #Close the login window

    def create_login_prompt(self):  #Function to open account creation screen
        self.create_window = CreateLoginWindow()  #Create instance of CreateLoginWindow
        self.create_window.show()  #Show the new window
        self.close()  #Close the current login window


class CreateLoginWindow(QWidget):  #Define the CreateLoginWindow class
    def __init__(self):  #Constructor for CreateLoginWindow
        super().__init__()  #Call the constructor of QWidget
        self.setWindowTitle("Create New Login")  #Set the window title
        self.setGeometry(300, 300, 300, 250)  #Set window position and size

        layout = QVBoxLayout()  #Create a vertical layout

        self.first_name_input = QLineEdit()  #Create input for first name
        self.first_name_input.setPlaceholderText("Enter First Name")  #Set placeholder

        self.last_name_input = QLineEdit()  #Create input for last name
        self.last_name_input.setPlaceholderText("Enter Last Name")  #Set placeholder

        self.submit_button = QPushButton("Create Account")  #Create submission button
        self.submit_button.clicked.connect(self.create_account)  #Connect button to account creation logic

        layout.addWidget(QLabel("Create New Player"))  #Add title label
        layout.addWidget(self.first_name_input)  #Add first name input
        layout.addWidget(self.last_name_input)  #Add last name input
        layout.addWidget(self.submit_button)  #Add submit button

        self.setLayout(layout)  #Set layout for the widget

    def create_account(self):  #Function to handle account creation
        fname = self.first_name_input.text().strip()  #Get and strip first name input
        lname = self.last_name_input.text().strip()  #Get and strip last name input

        if not fname or not lname:  #If either name is missing
            QMessageBox.warning(self, "Missing Info", "Please enter first and last name.")  #Show warning message
            return  #Exit function

        conn = sqlite3.connect(DB_PATH)  #Connect to the database
        cur = conn.cursor()  #Create a cursor

        while True:  #Generate unique player ID
            new_id = random.randint(1000, 9999)  #Generate random 4-digit ID
            cur.execute("SELECT 1 FROM PLAYERS WHERE ID=?", (new_id,))  #Check if ID already exists
            if not cur.fetchone():  #If ID is unique
                break  #Break loop

        while True:  #Generate unique password
            new_pw = str(random.randint(1000, 9999))  #Generate random 4-digit password
            cur.execute("SELECT 1 FROM Login WHERE Password=?", (new_pw,))  #Check if password already exists
            if not cur.fetchone():  #If password is unique
                break  #Break loop

        cur.execute("INSERT INTO PLAYERS (ID, balance, first_name, last_name) VALUES (?, 0, ?, ?)", (new_id, fname, lname))  #Insert new player
        cur.execute("INSERT INTO Login (ID, Password) VALUES (?, ?)", (new_id, new_pw))  #Insert login credentials
        conn.commit()  #Commit the transaction
        conn.close()  #Close the connection

        QMessageBox.information(self, "Account Created",  #Show success message
            f"Your ID: {new_id}\nYour Password: {new_pw}\nSave this info to log in.")  #Show new credentials

        from Casino_Full_Game import DepositWindow  #Import DepositWindow
        self.deposit_window = DepositWindow(new_id, f"{fname} {lname}")  #Create deposit window with new credentials
        self.deposit_window.show()  #Show deposit window
        self.close()  #Close account creation window
