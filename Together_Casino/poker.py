#IMPORTS
import sys
#Import rand for seeds
import random
#Import math for floor function
import math
#Import SQLite for database manipulation
import sqlite3
#Import PyQT for UI
from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QLineEdit, QVBoxLayout, QPushButton

class card:
    #Rank variable gives all cards a rank
    #1-9 is 2-10 respectively
    #10 is Jack, 11 is Queen, 12 is King, 13 is Ace
    rank = 1;
    #Suit variable gives all cards a suit
    #1 for spades, 2 for hearts, 3 for diamonds, 4 for clubs
    #Based off of alphabetical hierarchy
    suit = 1;
    
    #Call upon initializing a variable
    def __init__(self, suit, rank):
        self.rank = rank
        self.suit = suit

    #Print out data on a card
    def printCard(self):
        toPrint = ""

        #Rank to string
        if self.rank < 10:
            toPrint = toPrint+str(self.rank+1)
        elif self.rank == 10:
            toPrint = toPrint+"Jack"
        elif self.rank == 11:
            toPrint = toPrint+"Queen"
        elif self.rank == 12:
            toPrint = toPrint+"King"
        else:
            toPrint = toPrint+"Ace"
        toPrint = toPrint+" of "
        #Suit to string
        match self.suit:
            case 1:
                toPrint = toPrint+"Spades"
            case 2:
                toPrint = toPrint+"Hearts"
            case 3:
                toPrint = toPrint+"Diamonds"
            case 4:
                toPrint = toPrint+"Clubs"
        return toPrint
       


class Poker(QWidget):
    #Stores userID for database purposes
    userID = 0
    #Variables for connecting with SQLite
    connection = 0
    cursor = 0

#HANDS
    def Flush(self, hand):
        #Create array for suits
        held = [0, 0, 0, 0]

        #Add all card suits to array
        i = 0
        while i < len(hand):
            held[hand[i].suit-1] += 1
            i+=1

        #Return the suit with 5 cards or more
        i = 4
        while i > 0:
            if held[i-1] >= 5:
                return i
            i-=1

        #Return 0 if no available suit
        return 0

    def Straight(self, hand):
        #Create a temporary variable
        testVal = 0
        for i in hand:
            #Store the current card's rank
            testVal = i.rank
            #j is used to cound how many cards are in the straight
            j = 0
            while j < 4 and testVal > 0:
                #Store the current value of j
                m = j
                for k in hand:
                    #If any card's rank is 1 less than the testVal rank, add that to the straight order
                    #If a rank is 0, loop back to 13
                    if k.rank%13 == ((testVal-j)%13):
                        j+=1
                if j == m:
                    testVal = 0
            if j >= 5:
                return testVal
        return 0


    def StraightFlush(self, hand):
        straight = self.Straight(hand)
        flush = self.Flush(hand)

        if straight == 0 or flush == 0:
            return 0
        elif straight > 0 and flush > 0:
            return straight
        return 0    

    def OnePair(self, hand):
        pairRank = 0;
        for i in hand:
            for j in hand:
                if i.rank == j.rank and i.suit != j.suit:
                    pairRank = i.rank
        return pairRank;

    def TwoPair(self, hand):
        tempRank = self.OnePair(hand)
        pairRank = 0
        for i in hand:
            for j in hand:
                if i.rank == j.rank and i.suit != j.suit and i.rank != tempRank:
                    pairRank = i.rank
        return pairRank

    def ThreeKind(self, hand):
        pairRank = 0
        tempHand = []
        tempRank = 0

        for i in hand:
            for j in hand:
                if i.rank == j.rank and i.suit != j.suit and i not in tempHand and j not in tempHand:
                    tempHand.append(i)
                    tempHand.append(j)
                    tempRank = i.rank
        for k in hand:
            if k.rank == tempRank and k not in tempHand:
                return tempRank
        return 0

    def FourKind(self, hand):
        pairRank = 0
        tempHand = []
        tempRank = 0

        for i in hand:
            for j in hand:
                if i.rank == j.rank and i.suit != j.suit and i not in tempHand and j not in tempHand:
                    tempHand.append(i)
                    tempHand.append(j)
                    tempRank = i.rank
        for k in hand:
            if k == tempRank and k not in tempHand:
                tempHand.append(k)
        for l in hand:
            if l == tempRank and l not in tempHand:
                return tempRank
        return 0

    def FullHouse(self, hand):
        temp = self.ThreeKind(hand)
        twoTemp = self.TwoPair(hand)
        if temp != 0 and twoTemp != 0:
            if twoTemp > temp:
                temp = twoTemp
            return temp
        return 0


    def RoyalFlush(self, hand):
        if self.StraightFlush(hand) == 13:
            return True
        return False


    def playGame(self):
        #Seed is a string that determines what cards appear in the deck
        seed = ""
        #playerHand and dealerHand take directly from deck (see below)
        playerHand = []
        dealerHand = []
        #A set of 9 cards (starts out as an empty list)
        #   First 2 cards go in playerHand
        #   Next 2 cards go in dealerHand
        #   Remaining cards go in both hands
        deck = []
        #Boolean - Has the player won this round?
        win = False
        #Win message - changes depending on winning hand
        winMessage = ""
        #How much has the player won in cash?
        winnings = 0
        #What does the player currently have in cash?
        self.cCursor.execute("SELECT balance From PLAYERS where ID = ?", (str(self.userID),))
        currentBalS = self.cCursor.fetchone()
        #Stores the player's current bet
        bet = int(self.betLine.text())
        #Subtracts bet from currentBal
        currentBal = int(currentBalS[0])
        currentBal -= bet

        #Create a "Deck" (set of 9 cards)
        deck = random.sample(range(1,53), 9)
        #Write to seed
        for i in deck:
            seed = seed + str(i)+" "
        #Change seed to actual card objects, and add to player/dealer hands
        i = 0
        while i < len(deck):
            deck[i] = card(math.ceil(deck[i]/13),(deck[i]%13+1))
            if i < 2:
                playerHand.append(deck[i])
            elif i < 4:
                dealerHand.append(deck[i])
            else:
                playerHand.append(deck[i])
                dealerHand.append(deck[i])
            
            self.label_cards[i].setText(deck[i].printCard())
            i+=1


        #Royal Flush
        if (self.RoyalFlush(playerHand) or self.RoyalFlush(dealerHand)) and (self.RoyalFlush(playerHand) != self.RoyalFlush(dealerHand)):
            if (self.RoyalFlush(playerHand)):
                win = True
                winMessage = "You win with a Royal Flush!"
            else:
                win = False
                winMessage = "You lose to a Royal Flush!"
        #Straight Flush
        elif (self.StraightFlush(playerHand) or self.StraightFlush(dealerHand)) and (self.StraightFlush(playerHand) != self.StraightFlush(dealerHand)):
            if (self.StraightFlush(playerHand) > self.StraightFlush(dealerHand)):
                winMessage = "You win with a Straight Flush!"
                win = True
            else:
                win = False
                winMessage = "You lose to a Straight Flush!"
        #Four of a Kind
        elif (self.FourKind(playerHand) or self.FourKind(dealerHand)) and (self.FourKind(playerHand) != self.FourKind(dealerHand)):
            if (self.FourKind(playerHand) > self.FourKind(dealerHand)):
                win = True
                winMessage = "You win with a Four of a Kind!"
            else:
                win = False
                winMessage = "You lose to a Four of a Kind!"
        #Full House
        elif (self.FullHouse(playerHand) or self.FullHouse(dealerHand)) and (self.FullHouse(playerHand) != self.FullHouse(dealerHand)):
            if (self.StraightFlush(playerHand) > self.StraightFlush(dealerHand)):
                win = True
                winMessage = "You win with a Full House!"
            else:
                win = False
                winMessage = "You lose to a full house!"
        #Flush
        elif (self.Flush(playerHand) or self.Flush(dealerHand)) and (self.Flush(playerHand) != self.StraightFlush(dealerHand)):
            playerSuit = self.Flush(playerHand)
            dealerSuit = self.Flush(dealerHand)
            winningSuit = ""
            if (playerSuit > dealerSuit):
                win = True
                match playerSuit:
                    case 1:
                        winningSuit = "Spades"
                    case 2:
                        winningSuit = "Hearts"
                    case 3:
                        winningSuit = "Diamonds"
                    case 4:
                        winningSuit = "Clubs"
                winMessage = "You have won with a flush with the suit "+winningSuit+"!"
            else:
                win = False
                match dealerSuit:
                    case 1:
                        winningSuit = "Spades"
                    case 2:
                        winningSuit = "Hearts"
                    case 3:
                        winningSuit = "Diamonds"
                    case 4:
                        winningSuit = "Clubs"
                winMessage = "You have lost to a flush with the suit "+winningSuit+"!"
        #Straight
        elif (self.Straight(playerHand) or self.Straight(dealerHand)) and (self.Straight(playerHand) != self.Straight(dealerHand)):
            if (self.Straight(playerHand) > self.Straight(dealerHand)):
                win = True
                winMessage = "You have won with a straight!"
            else:
                win = False
                winMessage = "You have lost to a straight!"
        #Three of a Kind
        elif (self.ThreeKind(playerHand) or self.ThreeKind(dealerHand)) and ((playerHand) != self.ThreeKind(dealerHand)):
            if (self.ThreeKind(playerHand) > self.ThreeKind(dealerHand)):
                win = True
                winMessage = "You have won with a Three of a Kind!"
            else:
                win = False
                winMessage = "You have lost to a Three of a Kind!"
        #Two Pair
        elif (self.TwoPair(playerHand) or self.TwoPair(dealerHand)) and (self.TwoPair(playerHand) != self.TwoPair(dealerHand)):
            if (self.TwoPair(playerHand) > self.TwoPair(dealerHand)):
                win = True
                winMessage = "You have won with a two pair!"
            else:
                win = False
                winMessage = "You have lost to a two pair!"
        #One Pair
        elif (self.OnePair(playerHand) or self.OnePair(dealerHand)) and (self.OnePair(playerHand) != self.OnePair(dealerHand)):
            if (self.OnePair(playerHand) > self.OnePair(dealerHand)):
                win = True
                winMessage = "You have won with a pair!"
            else:
                win = False
                winMessage = "You have lost to a pair!"
        #High Card
        else:
            playerHigh = card(0, 0)
            dealerHigh = card(0, 0)
            i = 0
            while i == 0:
                for j in playerHand:
                    if playerHigh.rank < j.rank:
                        playerHigh = j
                    elif playerHigh.rank == j.rank:
                        if playerHigh.suit < j.suit:
                            playerHigh = j
                for j in dealerHand:
                    if dealerHigh.rank < j.rank:
                        dealerHigh = j
                    elif dealerHigh.rank == j.rank:
                        if dealerHigh.suit < j.suit:
                            dealerHigh = j
                if playerHigh == dealerHigh:
                    playerHand.remove(playerHigh)
                    dealerHand.remove(dealerHigh)
                    playerHigh = card(0, 0)
                    dealerHigh = card(0, 0)
                else:
                    if (playerHigh.rank > dealerHigh.rank):
                        win = True
                        winMessage = "You have won with a high card: "+playerHigh.printCard()
                    else:
                        win = False
                        winMessage = "You have lost to a high card: "+dealerHigh.printCard()
                    i = 1

        if win:
            winnings = bet*2
            win = 1
        else:
            win = 0
        self.label_win.setText(winMessage)

        self.cursor.execute("INSERT INTO Games(playerID, bet, win, seed) VALUES ('"+str(self.userID)+"', "+str(bet)+", "+str(win)+", '"+seed+"')")
        self.connection.commit()
        self.cCursor.execute("UPDATE PLAYERS SET balance = ? WHERE ID = ?", (str(currentBal+winnings), str(self.userID)))
        self.cConnect.commit()

        
    def validateBet(self):
        self.cCursor.execute("SELECT balance From PLAYERS where ID = ?", (str(self.userID),))
        currentBalS = self.cCursor.fetchone()
        currentBal = int(currentBalS[0])
        if self.betLine.text() != "":
            if int(self.betLine.text()) >= 5 and int(self.betLine.text()) <= 100 and int(self.betLine.text()) <= currentBal:
                self.playGame()
        





    #MAIN FUNCTION
    def __init__(self, userID, parent=None, *args, **kwargs):
        self.userID = userID
        
        #SQL Initialization
        self.connection = sqlite3.connect("Poker.db")
        self.cursor = self.connection.cursor()
        self.cConnect = sqlite3.connect("CasinoDB.db")
        self.cCursor = self.cConnect.cursor()
        #Window settings
        super().__init__(*args, **kwargs)
        #Create VBox for main menu
        self.vbox = QVBoxLayout()

        #VISUALS
        #Instructions
        self.instructions = QLabel("Instructions:"+
                                    "\nMake a bet (minimum $5, maximum $100)."+
                                    "\nUpon making a bet, two cards will be drawn for you, two for the dealer, and five cards will be drawn globally, acting as if in both hands."+
                                    "\nIf you receive a hand better than the dealer, receive double your bet back!"
                                    "\n\nAmount to bet:")
        self.instructions.setStyleSheet("font-size: 10px; color: #000000")
        self.vbox.addWidget(self.instructions)
        #Betting amount
        self.betLine = QLineEdit()
        self.betLine.setValidator(QIntValidator())
        self.vbox.addWidget(self.betLine)
        #PlayButton
        self.playButton = QPushButton("PLAY")
        self.playButton.clicked.connect(self.validateBet)
        self.playButton.setStyleSheet("color: blue; font-size: 12px")
        self.vbox.addWidget(self.playButton)

        self.label_player = QLabel("Player's Cards:")
        self.label_player.setStyleSheet("font-weight: bold")
        self.label_dealer = QLabel("Dealer's Cards:")
        self.label_dealer.setStyleSheet("font-weight: bold")
        self.label_global = QLabel("Global Cards:")
        self.label_global.setStyleSheet("font-weight: bold")
        self.label_win = QLabel("")
        self.label_win
        self.label_cards = ["", "", "", "", "", "", "", "", ""]
        
        i = 0
        while i < 9:
            match i:
                case 0:
                    self.vbox.addWidget(self.label_player)
                case 2:
                    self.vbox.addWidget(self.label_dealer)
                case 4:
                    self.vbox.addWidget(self.label_global)
            self.label_cards[i] = QLabel("")
            self.vbox.addWidget(self.label_cards[i])
            i+=1
        self.vbox.addWidget(self.label_win)

        self.setLayout(self.vbox)
