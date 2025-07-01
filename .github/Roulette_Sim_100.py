from sqlite3 import Cursor
import sys  
import random
import sqlite3

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox
)

from PyQt6.QtCore import Qt

# Database (FIXED: raw string to prevent unicodeescape error)
conn = sqlite3.connect(r"C:\Users\Anthony Magliozzi\OneDrive - Wentworth Institute of Technology\Applied_Programming_Concepts\Projects\Casino_Sim_100\CasinoDB.db")
cursor = conn.cursor()

class CasinoGame(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Roulette Game")
        self.setGeometry(100, 100, 800, 700)

        # Initialize the player's stats
        self.balance = 20000000
        self.winner = 0
        self.loser = 0
        self.wl = 0
        self.tot_bet_played = 0
        self.tot_bet_money = 0
        self.r_tot_won = 0
        self.r_tot_loss = 0

        # Roulette colors
        self.red = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
        self.black = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
        self.green = {0}

        # GUI layout
        main_layout = QVBoxLayout()

        # Inputs
        self.balance_label = QLabel(f"Player Balance: ${self.balance}")
        self.bet_help_label = QLabel("Place Bet Amount by Clicking on Displayed Values<br>or Enter a Value in the Text box")
        self.bet_help_label.setTextFormat(Qt.TextFormat.RichText)
        self.bet_help_label.setStyleSheet("QLabel { line-height: 115%; margin: 0px; padding: 0px; }")

        self.bet_directions_label = QLabel("Place Bet Type by Clicking on Displayed Values<br>or Enter a Value in the Text box")
        self.bet_directions_label.setTextFormat(Qt.TextFormat.RichText)
        self.bet_directions_label.setStyleSheet("QLabel { line-height: 115%; margin: 0px; padding: 0px; }")

        self.bet_amount_input = QLineEdit()
        self.bet_amount_input.setPlaceholderText("Enter bet amount (e.g., 5)")
        self.bet_type_input = QLineEdit()
        self.bet_type_input.setPlaceholderText("Enter bet (e.g., 17, red, 1-12, even)")
        self.spin_button = QPushButton("Spin")
        self.spin_button.clicked.connect(self.play_spin)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.bet_amount_input)
        input_layout.addWidget(self.bet_type_input)
        input_layout.addWidget(self.spin_button)

        main_layout.addWidget(self.balance_label)
        main_layout.addWidget(self.bet_help_label)
        main_layout.addWidget(self.bet_directions_label)
        main_layout.addLayout(input_layout)

        # Chips
        chip_values = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
        chip_colors = [
            "#2196F3", "#4CAF50", "#9C27B0", "#F44336", "#FF9800",
            "#B2DFDB", "#FFC107", "#673AB7", "#FFEB3B", "#00BCD4",
            "#E91E63", "#8BC34A"
        ]

        chip_layout = QGridLayout()
        for index, value in enumerate(chip_values):
            chip_button = QPushButton(f"${value}")
            chip_button.setFixedSize(60, 60)
            chip_button.setStyleSheet(
                f"border-radius: 30px; border: 2px solid black; background-color: {chip_colors[index]};"
                "font-weight: bold; color: black;"
            )
            chip_button.clicked.connect(lambda checked, v=value: self.select_chip_amount(v))
            chip_layout.addWidget(chip_button, index // 6, index % 6)

        main_layout.addLayout(chip_layout)

        # Roulette grid
        self.table_grid = QGridLayout()
        self.build_roulette_grid()
        main_layout.addLayout(self.table_grid)

        self.output_label = QLabel("Player place your bet and spin the wheel!")
        self.output_label.setWordWrap(True)
        main_layout.addWidget(self.output_label)

        self.setLayout(main_layout)

        # Run simulation of 100 games on startup
        self.simulate_100_games()

    def build_roulette_grid(self):
        self.add_table_cell("0", 0, 0, color="green")
        numbers = [
            [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36],
            [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35],
            [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
        ]
        for row, nums in enumerate(numbers):
            for col, num in enumerate(nums):
                color = "red" if num in self.red else "black"
                self.add_table_cell(str(num), row, col + 1, color)

        self.add_table_cell("1-12", 3, 1, colspan=4)
        self.add_table_cell("13-24", 3, 5, colspan=4)
        self.add_table_cell("25-36", 3, 9, colspan=4)
        self.add_table_cell("Even", 4, 1, colspan=2)
        self.add_table_cell("Odd", 4, 3, colspan=2)
        self.add_table_cell("Black", 4, 5, colspan=2, color="black")
        self.add_table_cell("Red", 4, 7, colspan=2, color="red")

    def add_table_cell(self, text, row, col, color=None, colspan=1):
        button = QPushButton(text)
        button.setFixedHeight(40)
        button.setStyleSheet("border: 1px solid black; font-weight: bold;")
        if color == "red":
            button.setStyleSheet("background-color: red; color: white; border: 1px solid black;")
        elif color == "black":
            button.setStyleSheet("background-color: black; color: white; border: 1px solid black;")
        elif color == "green":
            button.setStyleSheet("background-color: green; color: white; border: 1px solid black;")
        button.clicked.connect(lambda: self.handle_bet_selection(text.lower()))
        self.table_grid.addWidget(button, row, col, 1, colspan)

    def handle_bet_selection(self, bet_text):
        self.bet_type_input.setText(bet_text)

    def select_chip_amount(self, amount):
        self.bet_amount_input.setText(str(amount))

    def play_spin(self):
        try:
            bet_amount = float(self.bet_amount_input.text())
            if bet_amount < 1 or bet_amount > self.balance:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid bet amount within your balance.")
            return

        bet_choice = self.bet_type_input.text().strip().lower()
        if not bet_choice:
            QMessageBox.warning(self, "Invalid Input", "Enter a bet type (number, red, black, etc.)")
            return

        rolled = random.randint(0, 36)
        win = False
        payout = 0

        red_check = rolled in self.red
        black_check = rolled in self.black
        green_check = rolled in self.green

        if bet_choice.isdigit() and int(bet_choice) == rolled:
            win = True
            payout = bet_amount * 36
        elif bet_choice == "even" and rolled != 0 and rolled % 2 == 0:
            win = True
            payout = bet_amount * 2
        elif bet_choice == "odd" and rolled % 2 != 0:
            win = True
            payout = bet_amount * 2
        elif bet_choice == "1-12" and 1 <= rolled <= 12:
            win = True
            payout = bet_amount * 3
        elif bet_choice == "13-24" and 13 <= rolled <= 24:
            win = True
            payout = bet_amount * 3
        elif bet_choice == "25-36" and 25 <= rolled <= 36:
            win = True
            payout = bet_amount * 3
        elif bet_choice == "red" and red_check:
            win = True
            payout = bet_amount * 2
        elif bet_choice == "black" and black_check:
            win = True
            payout = bet_amount * 2
        elif bet_choice == "green" and green_check:
            win = True
            payout = bet_amount * 35

        self.tot_bet_money += bet_amount
        self.tot_bet_played += 1

        cursor.execute("""INSERT OR IGNORE INTO Roulette VALUES(0, 0, ?, 0, 0);""", (bet_amount,))

        if win:
            self.balance += payout - bet_amount
            self.winner += 1
            self.r_tot_won += payout - bet_amount
            cursor.execute("""UPDATE Roulette SET wins = ? WHERE number_of_bets = 0""", (self.winner,))
            cursor.execute("""UPDATE Roulette SET money_won = ? WHERE number_of_bets = 0""", (self.r_tot_won,))
        else:
            self.balance -= bet_amount
            self.loser += 1
            self.r_tot_loss += bet_amount
            cursor.execute("""UPDATE Roulette SET losses = ? WHERE number_of_bets = 0""", (self.loser,))
            cursor.execute("""UPDATE Roulette SET money_lost = ? WHERE number_of_bets = 0""", (self.r_tot_loss,))

        conn.commit()

        if self.tot_bet_played > 0:
            self.wl = (self.winner * 100) / self.tot_bet_played

        self.balance_label.setText(f"Player Balance: ${self.balance}")
        self.output_label.setText(
            f"Rolled: {rolled}\n{'You WON' if win else 'You LOST'}\n"
            f"Wins: {self.winner} | Losses: {self.loser} | Win %: {self.wl:.2f}%\n"
            f"Total Number of Bets: {self.tot_bet_played} | Bet Total: ${self.tot_bet_money}\n"
            f"Total Roulette Winnings: ${self.r_tot_won} | Total Roulette Losses: ${self.r_tot_loss}"
        )

        self.bet_amount_input.clear()
        self.bet_type_input.clear()

        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You're out of money. Game over.")
            self.spin_button.setEnabled(False)

    def simulate_100_games(self):
        bet_options = ["even", "odd", "red", "black", "green", "1-12", "13-24", "25-36"] + [str(i) for i in range(0, 37)]
        chip_values = [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]

        for _ in range(100):
            if self.balance <= 0:
                break

            bet_amount = random.choice(chip_values)
            bet_choice = random.choice(bet_options)

            if bet_amount > self.balance:
                continue

            self.bet_amount_input.setText(str(bet_amount))
            self.bet_type_input.setText(str(bet_choice))
            self.play_spin()

# Entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CasinoGame()
    window.show()
    sys.exit(app.exec())
