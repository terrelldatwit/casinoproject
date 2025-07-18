# blackjack.py

import random

# ──────────────────────────────────────────────────────────────────────────────
# 1) BUILD A NUMERIC 52-CARD DECK
# ──────────────────────────────────────────────────────────────────────────────

def build_deck_numeric():
    """
    Return a full “deck” of 52 numeric values:
      - 2 through 9 appear four times each (one per suit)
      - 10 appears 16 times total (10, Jack, Queen, King across four suits)
      - 11 appears 4 times (Ace)
    """
    deck = []
    for num in range(2, 12):
        if num == 11:
            # 4 Aces (each Ace initially counts as 11)
            deck.extend([11] * 4)
        elif num == 10:
            # 16 “tens” (10, J, Q, K) each valued as 10
            deck.extend([10] * 16)
        else:
            # 4 of each rank 2–9
            deck.extend([num] * 4)
    return deck

# ──────────────────────────────────────────────────────────────────────────────
# 2) DEAL A CARD
# ──────────────────────────────────────────────────────────────────────────────

def deal_card(deck):
    """
    Remove and return one random card (integer) from the deck list.
    """
    return deck.pop(random.randrange(len(deck)))

# ──────────────────────────────────────────────────────────────────────────────
# 3) CALCULATE BLACKJACK SCORE
# ──────────────────────────────────────────────────────────────────────────────

def calculate_score(hand):
    """
    hand: list of integers (2–11). 11 = Ace, 10 = Ten/Jack/Queen/King.
    Returns the Blackjack score (0 if natural Blackjack).
    """
    total = sum(hand)
    num_aces = hand.count(11)

    # Natural Blackjack: exactly two cards summing to 21
    if total == 21 and len(hand) == 2:
        return 0

    # If over 21 and there are Aces counted as 11, convert Ace(s) from 11 to 1
    while total > 21 and num_aces:
        total -= 10  # count one Ace as 1 instead of 11
        num_aces -= 1

    return total

# ──────────────────────────────────────────────────────────────────────────────
# 4) COMPARE SCORES AND DETERMINE RESULT
# ──────────────────────────────────────────────────────────────────────────────

def compare(player_score, dealer_score):
    """
    Compare final player and dealer scores. Returns (message, multiplier):
      - Dealer has Blackjack (0) & player doesn’t: loss (-1.0)
      - Player has Blackjack (0) & dealer doesn’t: win 3:2 (1.5)
      - Both have Blackjack: push (0.0)
      - Player busts (>21): loss (-1.0)
      - Dealer busts (>21): win (1.0)
      - Otherwise: player>dealer → win (1.0), player<dealer → loss (-1.0), tie → push (0.0)
    """
    # Dealer Blackjack
    if dealer_score == 0 and player_score != 0:
        return ("Dealer has Blackjack. You lose.", -1.0)

    # Player Blackjack
    if player_score == 0 and dealer_score != 0:
        return ("You got a Blackjack! Payout 3:2.", 1.5)

    # Both Blackjack → push
    if player_score == 0 and dealer_score == 0:
        return ("Both have Blackjack. Push.", 0.0)

    # Busts
    if player_score > 21:
        return ("Bust! You lose your bet.", -1.0)
    if dealer_score > 21:
        return ("Dealer busts! You win.", 1.0)

    # Normal compare
    if player_score > dealer_score:
        return ("You win!", 1.0)
    elif player_score < dealer_score:
        return ("You lose.", -1.0)
    else:
        return ("Push. Bet returned.", 0.0)
