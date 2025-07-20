import random
import sqlite3
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from cheaters import log_cheater
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


DB_PATH = "CasinoDB.db"

class RouletteGame(QWidget):
    def __init__(self, player_id, parent_menu=None):
        super().__init__()
        self.setWindowTitle("Roulette")
        self.setGeometry(100, 100, 800, 700)
        self.player_id = player_id
        self.parent_menu = parent_menu

        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.player_id,))
        self.balance = self.cur.fetchone()[0]

        self.winner = 0
        self.loser = 0
        self.wl = 0
        self.tot_bet_played = 0
        self.tot_bet_money = 0
        self.r_tot_won = 0
        self.r_tot_loss = 0
        self.session_history = []

        self.red = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        self.black = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}
        self.green = {0}

        main_layout = QVBoxLayout()

        self.balance_label = QLabel(f"Player Balance: ${self.balance}")
        self.bet_help_label = QLabel("Place Bet Amount by Clicking on Displayed Values<br>or Enter a Value in the Text box")
        self.bet_help_label.setTextFormat(Qt.TextFormat.RichText)
        self.bet_directions_label = QLabel("Place Bet Type by Clicking on Displayed Values<br>or Enter a Value in the Text box")
        self.bet_directions_label.setTextFormat(Qt.TextFormat.RichText)

        self.bet_amount_input = QLineEdit()
        self.bet_amount_input.setPlaceholderText("Enter bet amount (e.g., 5)")
        self.bet_type_input = QLineEdit()
        self.bet_type_input.setPlaceholderText("Enter bet (e.g., 17, red, 1-12, even)")
        self.spin_button = QPushButton("Spin")
        self.spin_button.clicked.connect(self.play_spin)

        back_button = QPushButton("Back to Menu")
        back_button.clicked.connect(self.back_to_menu)

        net_button = QPushButton("Net Winnings")
        net_button.clicked.connect(self.plot_net_winnings)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.bet_amount_input)
        input_layout.addWidget(self.bet_type_input)
        input_layout.addWidget(self.spin_button)
        input_layout.addWidget(back_button)
        input_layout.addWidget(net_button)

        main_layout.addWidget(self.balance_label)
        main_layout.addWidget(self.bet_help_label)
        main_layout.addWidget(self.bet_directions_label)
        main_layout.addLayout(input_layout)

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

        self.table_grid = QGridLayout()
        self.build_roulette_grid()
        main_layout.addLayout(self.table_grid)

        self.output_label = QLabel("Player place your bet and spin the wheel!")
        self.output_label.setWordWrap(True)
        main_layout.addWidget(self.output_label)

        self.setLayout(main_layout)

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
        if color == "red":
            button.setStyleSheet("background-color: red; color: white;")
        elif color == "black":
            button.setStyleSheet("background-color: black; color: white;")
        elif color == "green":
            button.setStyleSheet("background-color: green; color: white;")
        button.clicked.connect(lambda: self.handle_bet_selection(text.lower()))
        self.table_grid.addWidget(button, row, col, 1, colspan)

    def handle_bet_selection(self, bet_text):
        self.bet_type_input.setText(bet_text)

    def select_chip_amount(self, amount):
        self.bet_amount_input.setText(str(amount))

    def play_spin(self):
        try:
            bet_amount = float(self.bet_amount_input.text())
            if bet_amount <= 0 or bet_amount > self.balance:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Enter a valid bet amount.")
            return

        bet_choice = self.bet_type_input.text().strip().lower()
        if not bet_choice:
            QMessageBox.warning(self, "Invalid Input", "Enter a bet type.")
            return

        rolled = random.randint(0, 36)
        win = False
        payout = 0

        if bet_choice.isdigit() and int(bet_choice) == rolled:
            win = True
            payout = bet_amount * 36
        elif bet_choice == "even" and rolled != 0 and rolled % 2 == 0:
            win = True
            payout = bet_amount * 2
        elif bet_choice == "odd" and rolled % 2 == 1:
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
        elif bet_choice == "red" and rolled in self.red:
            win = True
            payout = bet_amount * 2
        elif bet_choice == "black" and rolled in self.black:
            win = True
            payout = bet_amount * 2
        elif bet_choice == "green" and rolled == 0:
            win = True
            payout = bet_amount * 35

        self.tot_bet_money += bet_amount
        self.tot_bet_played += 1

        if win:
            self.session_history.append(True)
            self.balance += payout - bet_amount
            self.winner += 1
            self.r_tot_won += payout - bet_amount
            result = f"You WON ${payout - bet_amount:.2f}!"
        else:
            self.session_history.append(False)
            self.balance -= bet_amount
            self.loser += 1
            self.r_tot_loss += bet_amount
            result = f"You LOST ${bet_amount:.2f}."

        self.wl = (self.winner * 100) / self.tot_bet_played if self.tot_bet_played > 0 else 0

        if len(self.session_history) >= 20:
            recent = self.session_history[-20:]
            rate = sum(recent) / 20
            if rate >= 0.8:
                log_cheater(self.player_id, "Roulette", rate)
                QMessageBox.warning(self, "Cheater Detected", f"You won {rate*100:.1f}% of your last 20 games and have been flagged.")
                self.close()
                return

        self.cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.player_id))
        self.cur.execute("""
            INSERT INTO Roulette (player_name, number_of_bets, bet_amount, wins, losses, money_won)
            VALUES ((SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID = ?), ?, ?, ?, ?, ?)""",
            (self.player_id, self.tot_bet_played, self.tot_bet_money, self.winner, self.loser, self.r_tot_won)
        )
        self.conn.commit()

        self.balance_label.setText(f"Player Balance: ${self.balance:.2f}")
        self.output_label.setText(
            f"Rolled: {rolled}\n{result}\n"
            f"Wins: {self.winner} | Losses: {self.loser} | Win %: {self.wl:.2f}%\n"
            f"Total Bets: {self.tot_bet_played} | Bet Total: ${self.tot_bet_money:.2f}\n"
            f"Total Winnings: ${self.r_tot_won:.2f} | Total Losses: ${self.r_tot_loss:.2f}"
        )

        self.bet_amount_input.clear()
        self.bet_type_input.clear()

        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You're out of money!")
            self.spin_button.setEnabled(False)

    def back_to_menu(self):
        self.conn.close()
        self.parent_menu.show()
        self.close()

    def plot_net_winnings(self):
        # Fetch winnings data from the database
        self.cur.execute("SELECT money_won FROM Roulette WHERE player_name = (SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?)", (self.player_id,))
        rows = self.cur.fetchall()

        if not rows:
            QMessageBox.information(self, "No Data", "No winnings history available for this player.")
            return

        winnings = [row[0] for row in rows]
        cumulative = []
        total = 0
        for amount in winnings:
            total += amount
            cumulative.append(total)

        # Create a new window to host the graph and label
        self.graph_window = QWidget()
        self.graph_window.setWindowTitle("Net Winnings Graph")
        self.graph_window.setGeometry(150, 150, 600, 400)

        layout = QVBoxLayout()

        # Create matplotlib figure
        fig = Figure(figsize=(5, 4))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        ax.plot(range(1, len(cumulative) + 1), cumulative, marker='o', color='blue')
        ax.set_title("Cumulative Net Winnings - Roulette")
        ax.set_xlabel("Session Number")
        ax.set_ylabel("Net Winnings ($)")
        ax.grid(True)

        # Add canvas and total winnings label to layout
        layout.addWidget(canvas)

        total_label = QLabel(f"Total Net Winnings: ${total:.2f}")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_label.setStyleSheet("font-size: 16px; font-weight: bold; padding-top: 10px;")
        layout.addWidget(total_label)

        self.graph_window.setLayout(layout)
        self.graph_window.show()
