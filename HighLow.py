import random

class HigherLowerGame:
    def __init__(self):
        self.reset_deck()

    def reset_deck(self):
        self.cards = list(range(2, 15)) * 4  # 2–14 = 2–10, J, Q, K, A
        random.shuffle(self.cards)
        self.cards_dealt = 0
        self.correct_streak = 0
        self.cashout = 0.0

    def play_round(self, bet):
        self.reset_deck()
        balance_change = 0
        self.cards_dealt = 1
        self.correct_streak = 0

        current_card = self.cards.pop()

        while self.cards:
            next_card = self.cards.pop()
            guess = self.make_guess(current_card, next_card)

            if (guess == 'higher' and next_card > current_card) or \
               (guess == 'lower' and next_card < current_card):
                self.correct_streak += 1
                self.cards_dealt += 1
                current_card = next_card

                if self.correct_streak == 3:
                    multiplier = (1 + 0.2) ** (self.cards_dealt - 1)
                    self.cashout = round(multiplier * bet, 2)
                    return self.cashout  # Win, cash out
            else:
                return -bet  # Loss

        return 0  # Edge case if deck runs out

    def make_guess(self, current, next_card):
        # Guess based on odds — skewed lower if card is high, higher if card is low
        if current <= 7:
            return 'higher'
        else:
            return 'lower'


# Simulate 100 rounds
game = HigherLowerGame()
initial_balance = 1000
balance = initial_balance
bet = 10
wins = 0
losses = 0

for i in range(100):
    result = game.play_round(bet)

    if result > 0:
        wins += 1
        print(f"Round {i+1}: WIN - Cashout ${result}")
    else:
        losses += 1
        print(f"Round {i+1}: LOSS - Lost ${bet}")

    balance += result

print("\n--- Simulation Summary ---")
print(f"Total Rounds: 100")
print(f"Wins: {wins}, Losses: {losses}")
print(f"Final Balance: ${balance:.2f}")
print(f"Net Profit: ${balance - initial_balance:.2f}")
