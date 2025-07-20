import random
import os
import sqlite3
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from cheaters import log_cheater

DB_PATH = "CasinoDB.db"

class Craps(QMainWindow):
    def __init__(self, user_id, parent_menu=None):
        super().__init__()
        self.setWindowTitle("Craps Game")
        self.setGeometry(200, 200, 600, 500)
        self.user_id = user_id
        self.parent_menu = parent_menu

        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        self.cur.execute("SELECT balance FROM PLAYERS WHERE ID=?", (self.user_id,))
        self.balance = self.cur.fetchone()[0]

        self.bet = 0
        self.bet_type = ""
        self.point = None
        self.games_won = 0
        self.games_lost = 0
        self.total_bets = 0
        self.winnings = 0
        self.session_history = []

        self.setup_ui()
        self.update_balance_label()

    def setup_ui(self):
        w = QWidget()
        self.setCentralWidget(w)
        layout = QVBoxLayout()

        self.balance_label = QLabel()
        layout.addWidget(self.balance_label)

        br = QHBoxLayout()
        self.bet_input = QLineEdit()
        self.bet_input.setPlaceholderText("Enter bet amount")
        br.addWidget(self.bet_input)
        self.bet_type_combo = QComboBox()
        self.bet_type_combo.addItems([
            "Pass Line", "Don't Pass", "Field", "Any 7",
            "Craps", "Hard 4", "Hard 6", "Hard 8", "Big 6 & 8"
        ])
        br.addWidget(self.bet_type_combo)
        pbtn = QPushButton("Place Bet")
        pbtn.clicked.connect(self.place_bet)
        br.addWidget(pbtn)
        layout.addLayout(br)

        dr = QHBoxLayout()
        self.die1_label = QLabel()
        self.die2_label = QLabel()
        for lbl in (self.die1_label, self.die2_label):
            lbl.setFixedSize(64, 64)
            dr.addWidget(lbl)
        layout.addLayout(dr)

        self.roll_button = QPushButton("Roll Dice")
        self.roll_button.setEnabled(False)
        self.roll_button.clicked.connect(self.roll_dice)
        layout.addWidget(self.roll_button)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        layout.addWidget(self.output_box)

        graph_btn = QPushButton("View Net Winnings")
        graph_btn.clicked.connect(self.plot_net_winnings)
        layout.addWidget(graph_btn)

        back_btn = QPushButton("Return to Main Menu")
        back_btn.clicked.connect(self.back_to_menu)
        layout.addWidget(back_btn)

        w.setLayout(layout)

    def log(self, msg):
        self.output_box.append(msg)

    def update_balance_label(self):
        self.balance_label.setText(f"Player {self.user_id} - Balance: ${self.balance:.2f}")

    def place_bet(self):
        try:
            amt = float(self.bet_input.text())
            if amt <= 0 or amt > self.balance:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Bet", "Enter a valid amount.")
            return
        self.bet = amt
        self.bet_type = self.bet_type_combo.currentText()
        self.balance -= self.bet
        self.total_bets += 1
        self.update_balance_label()
        self.log(f"Bet ${self.bet:.2f} on {self.bet_type}")
        self.roll_button.setEnabled(True)

    def roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        total = d1 + d2
        self.update_dice_images(d1, d2)
        self.resolve_bet(total, d1, d2)

    def update_dice_images(self, d1, d2):
        try:
            p1 = QPixmap(os.path.abspath(f"dice{d1}.png")).scaled(64, 64)
            p2 = QPixmap(os.path.abspath(f"dice{d2}.png")).scaled(64, 64)
            self.die1_label.setPixmap(p1)
            self.die2_label.setPixmap(p2)
        except Exception as e:
            self.log(f"Error loading dice images: {e}")

    def resolve_bet(self, total, d1, d2):
        won_round = None
        payout = 0
        mult = 1
        msg = f"Dice rolled: {d1} + {d2} = {total}"

        if self.bet_type == "Any 7":
            if total == 7:
                won_round = True
                mult = 4
                msg += " You win 4:1!"
            else:
                won_round = False
                msg += " You lose."
        elif self.bet_type == "Craps":
            if total in [2, 3, 12]:
                won_round = True
                mult = 7
                msg += " You win 7:1!"
            else:
                won_round = False
                msg += " You lose."
        elif self.bet_type == "Field":
            if total in [2, 3, 4, 9, 10, 11, 12]:
                won_round = True
                mult = 2
                msg += " You win 2:1!"
            else:
                won_round = False
                msg += " You lose."

        if won_round is True:
            payout = self.bet * (1 + mult)
            self.balance += payout
            self.winnings += self.bet * mult
            self.log(msg)
            self.log(f"You won ${self.bet * mult:.2f}!")
            self.games_won += 1
        elif won_round is False:
            self.log(msg)
            self.log(f"You lost ${self.bet:.2f}.")
            self.games_lost += 1
        else:
            self.log(msg)

        self.session_history.append(won_round is True)
        self.finish_round()

    def finish_round(self):
        self.roll_button.setEnabled(False)
        self.update_balance_label()
        self.save_user()
        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You're out of money!")

    def save_user(self):
        self.cur.execute("UPDATE PLAYERS SET balance=? WHERE ID=?", (self.balance, self.user_id))
        self.cur.execute(
            """INSERT INTO Craps (player_name, number_of_bets, bet_amount, wins, losses, money_won)
               VALUES ((SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID = ?), ?, ?, ?, ?, ?)""",
            (self.user_id, self.total_bets, self.bet, self.games_won, self.games_lost, self.winnings)
        )
        self.conn.commit()

    def back_to_menu(self):
        self.save_user()
        self.close()
        if self.parent_menu:
            self.parent_menu.show()

    def plot_net_winnings(self):
        self.winnings_window = QWidget()
        self.winnings_window.setWindowTitle("Net Winnings - Craps")
        self.winnings_window.setGeometry(150, 150, 600, 400)

        layout = QVBoxLayout()
        self.winnings_window.setLayout(layout)

        self.cur.execute("""
            SELECT money_won, bet_amount FROM Craps 
            WHERE player_name = (SELECT first_name || ' ' || last_name FROM PLAYERS WHERE ID=?)
        """, (self.user_id,))
        rows = self.cur.fetchall()

        if not rows:
            QMessageBox.information(self, "No Data", "No winnings history available for this player.")
            return

        cumulative = []
        total = 0
        for money_won, bet_amount in rows:
            net = money_won - bet_amount
            total += net
            cumulative.append(total)

        figure = Figure()
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        ax.plot(range(1, len(cumulative) + 1), cumulative, marker='o', color='green')
        ax.set_title("Cumulative Net Winnings - Craps")
        ax.set_xlabel("Session Number")
        ax.set_ylabel("Net Winnings ($)")
        ax.grid(True)

        total_label = QLabel(f"Total Net Winnings: ${total:.2f}")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(canvas)
        layout.addWidget(total_label)

        self.winnings_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.winnings_window.show()
