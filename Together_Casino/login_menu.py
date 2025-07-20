### Files to be updated:
# 1. login_menu.py - add full name fetch and pass
# 2. Casino_Full_Game.py - create DepositWindow with welcome label + cash-out feature

# Reprint of login_menu.py with required changes

import random
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)

DB_PATH = "CasinoDB.db"

class LoginMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Menu")
        self.setGeometry(300, 300, 300, 250)

        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Player ID")

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Enter Password")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Normal)  # Visible for testing

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)

        self.create_button = QPushButton("Create New Login")
        self.create_button.clicked.connect(self.create_login_prompt)

        layout.addWidget(QLabel("Casino Login"))
        layout.addWidget(self.id_input)
        layout.addWidget(self.pw_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.create_button)

        self.setLayout(layout)

    def handle_login(self):
        try:
            self.player_id = int(self.id_input.text())
            password = self.pw_input.text().strip()
        except:
            QMessageBox.warning(self, "Error", "Enter valid credentials.")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT Password FROM Login WHERE ID=?", (self.player_id,))
        result = cur.fetchone()
        if not result or str(result[0]).strip() != password:
            QMessageBox.warning(self, "Login Failed", "Invalid ID or Password.")
            conn.close()
            return

        cur.execute("SELECT first_name, last_name FROM PLAYERS WHERE ID=?", (self.player_id,))
        name_result = cur.fetchone()
        conn.close()

        self.full_name = f"{name_result[0]} {name_result[1]}"
        self.launch_deposit()

    def launch_deposit(self):
        from Casino_Full_Game import DepositWindow
        self.deposit_window = DepositWindow(self.player_id, self.full_name)
        self.deposit_window.show()
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

        cur.execute("INSERT INTO PLAYERS (ID, balance, first_name, last_name) VALUES (?, 0, ?, ?)", (new_id, fname, lname))
        cur.execute("INSERT INTO Login (ID, Password) VALUES (?, ?)", (new_id, new_pw))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Account Created",
            f"Your ID: {new_id}\nYour Password: {new_pw}\nSave this info to log in.")

        from Casino_Full_Game import DepositWindow
        self.deposit_window = DepositWindow(new_id, f"{fname} {lname}")
        self.deposit_window.show()
        self.close()
