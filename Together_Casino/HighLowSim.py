import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QLineEdit, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer

# Card setup
suits = ['hearts', 'diamonds', 'clubs', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
rank_values = {rank: value for value, rank in enumerate(ranks, start=2)}

def create_shuffled_deck(num_decks=4):
    deck = []
    for _ in range(num_decks):
        deck += [f"{rank} of {suit}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

class CardGame(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Higher or Lower!")
        self.setGeometry(500, 200, 300, 400)

        self.balance = 10000  
        self.last_card = None
        self.cashout = 0
        self.cards_dealt = 0

        self.num_decks = 4
        self.total_cards = 52 * self.num_decks
        self.shuffle_threshold = int(self.total_cards * 0.25)  # 25% cards left triggers shuffle

        self.deck = create_shuffled_deck(self.num_decks)

        self.start_button = QPushButton("Start Game")
        self.start_button.clicked.connect(self.start_game)

        self.label = QLabel("")
        self.card_image = QLabel(self)
        
        self.compare_label = QLabel("")
        self.balance_label = QLabel(f"Balance: ${self.balance:.2f}")
        self.cards_dealt_label = QLabel(f"Cards Dealt: {self.cards_dealt}")
        self.bet_input = QLineEdit()
        self.bet_input.setPlaceholderText("Enter your bet amount")
        
        self.cashout_button = QPushButton(f"Cash Out ${self.cashout:.2f}")
        self.cashout_button.clicked.connect(self.cash_out)

        self.draw_button = QPushButton("Draw Card")
        self.higher_button = QPushButton("Guess Higher")
        self.lower_button = QPushButton("Guess Lower")
        
        self.draw_button.clicked.connect(self.draw_card)
        self.higher_button.clicked.connect(lambda: self.make_guess(expect_higher=True))
        self.lower_button.clicked.connect(lambda: self.make_guess(expect_higher=False))

        layout = QVBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.label)
        layout.addWidget(self.card_image)
        layout.addWidget(self.compare_label)
        layout.addWidget(self.cards_dealt_label)
        layout.addWidget(self.balance_label)
        layout.addWidget(self.cashout_button)
        layout.addWidget(self.bet_input)
        layout.addWidget(self.draw_button)
        layout.addWidget(self.higher_button)
        layout.addWidget(self.lower_button)
        
        self.setLayout(layout)

        self.toggle_game_ui(False)

    def start_game(self):
        self.start_button.hide()
        self.label.setText("Click 'Draw Card' to begin!")
        self.toggle_game_ui(True)

    def toggle_game_ui(self, show):
        self.label.setVisible(show)
        self.card_image.setVisible(show)
        self.compare_label.setVisible(show)
        self.balance_label.setVisible(show)
        self.cards_dealt_label.setVisible(show)
        self.bet_input.setVisible(show)
        self.cashout_button.setVisible(show)
        self.draw_button.setVisible(show)
        self.higher_button.setVisible(show)
        self.lower_button.setVisible(show)

    def check_and_shuffle_deck(self):
        # Shuffle only when deck is low
        if len(self.deck) <= self.shuffle_threshold:
            self.label.setText("Deck low — reshuffling!")
            self.deck = create_shuffled_deck(self.num_decks)
            self.cards_dealt = 0
            self.cashout = 0
            self.last_card = None
            self.cards_dealt_label.setText(f"Cards Dealt: {self.cards_dealt}")
            self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
            QTimer.singleShot(2000, lambda: self.label.setText("Deck reshuffled. Click 'Draw Card' to continue!"))

    def draw_card(self):
        if not self.deck:
            self.label.setText("Deck is empty!")
            return

        self.check_and_shuffle_deck()

        card = self.deck.pop()
        self.cards_dealt += 1  
        self.cards_dealt_label.setText(f"Cards Dealt: {self.cards_dealt}")
        self.show_card_image(card)
        self.compare_label.setText("")
        self.last_card = card

    def reset_game(self):
        # This resets balance and game state (not deck unless called)
        self.cards_dealt = 0
        self.cashout = 0
        self.last_card = None
        self.balance = 10000
        self.balance_label.setText(f"Balance: ${self.balance:.2f}")
        self.cards_dealt_label.setText(f"Cards Dealt: {self.cards_dealt}")
        self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
        self.label.setText("Game reset! Click 'Draw Card' to begin.")

    def make_guess(self, expect_higher):
        if not self.last_card:
            self.compare_label.setText("Draw a card first!")
            return
        if not self.deck:
            self.label.setText("Deck is empty!")
            return
        
        self.check_and_shuffle_deck()

        bet = self.validate_bet()
        if bet is None:
            return  

        new_card = self.deck.pop()
        self.cards_dealt += 1  
        self.cards_dealt_label.setText(f"Cards Dealt: {self.cards_dealt}")
        self.show_card_image(new_card)

        rank1 = self.last_card.split()[0]
        rank2 = new_card.split()[0]
        value1 = rank_values[rank1]
        value2 = rank_values[rank2]

        win = (value2 > value1 if expect_higher else value2 < value1)

        if win:
            multiplier = 1 * (1 + 0.3) ** (self.cards_dealt - 1)
            self.cashout = round(multiplier * bet, 2)
            self.compare_label.setText("Winner! You won the bet.")
             

        else:
            self.balance -= bet
            self.cashout = 0
            self.compare_label.setText("You lost the bet.")
            self.cards_dealt = 0  # Reset cards dealt after a loss

        self.balance_label.setText(f"Balance: ${self.balance:.2f}")
        self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
        self.last_card = new_card

        if self.balance <= 0:
            QMessageBox.information(self, "Game Over", "You ran out of money! Resetting game.")
            self.reset_game()
            self.toggle_game_ui(False)
            self.start_button.show()

    def cash_out(self):
        if self.cashout > 0:
            self.balance += self.cashout
            QMessageBox.information(self, "Cash Out", f"You've cashed out ${self.cashout:.2f}!")
            self.cashout = 0
            self.cashout_button.setText(f"Cash Out ${self.cashout:.2f}")
            self.cards_dealt = 0
            self.balance_label.setText(f"Balance: ${self.balance:.2f}")  # <-- This line refreshes the balance display
        else:
            QMessageBox.information(self, "Cash Out", "No winnings to cash out.")

    def validate_bet(self):
        try:
            bet = int(self.bet_input.text())
            if bet <= 0:
                raise ValueError
            if bet > self.balance:
                QMessageBox.warning(self, "Invalid Bet", "You cannot bet more than your balance!")
                return None
            return bet
        except ValueError:
            QMessageBox.warning(self, "Invalid Bet", "Please enter a valid positive number.")
            return None

    def show_card_image(self, card):
        rank, _, suit = card.split()  
        card_filename = f"{rank}_of_{suit}.png"  
        image_path = f"C:/Wentworth summer 2025/Applied Programming Concepts - Code/High or low/cards images/{card_filename}" 

        pixmap = QPixmap(image_path)

        if not pixmap.isNull():
            self.card_image.setPixmap(pixmap.scaled(100, 168, Qt.AspectRatioMode.KeepAspectRatio))
            self.card_image.setText("")  
        else:
            self.card_image.setText(f"Image not found:\n{card_filename}")


# Run the app
app = QApplication(sys.argv)
window = CardGame()
window.show()
sys.exit(app.exec())
