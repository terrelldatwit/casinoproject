import random

#create money variable
#Read money variable for user from database
total = 100
print("Current Balance: $", total)
current_bet_in = input("What would you like to bet: $")
current_bet = int(current_bet_in)

print("\n")

number1 = random.randint(1, 7)
if number1 == 1:
    print("7")
elif number1 == 2:
    print("bar")    
elif number1 == 3:
    print("bar-bar")
elif number1 == 4:
    print("bar-bar-bar")
elif number1 == 5:
    print("cherry")
elif number1 == 6:
    print("lemon")
elif number1 == 7:
    print("grape")

number2 = random.randint(1, 7)
if number2 == 1:
    print("7")
elif number2 == 2:
    print("bar")    
elif number2 == 3:
    print("bar-bar")
elif number2 == 4:
    print("bar-bar-bar")
elif number2 == 5:
    print("cherry")
elif number2 == 6:
    print("lemon")
elif number2 == 7:
    print("grape")

number3 = random.randint(1, 7)
if number3 == 1:
    print("7")
elif number3 == 2:
    print("bar")    
elif number3 == 3:
    print("bar-bar")
elif number3 == 4:
    print("bar-bar-bar")
elif number3 == 5:
    print("cherry")
elif number3 == 6:
    print("lemon")
elif number3 == 7:
    print("grape")

print("\n")

win = 0

if ((number1 == 1 and number2 == 1) or (number2 == 1 and number3 == 1)):
    win = current_bet * 10
    print("Win 7-7")
elif((number1 == 2 and number2 == 2) or (number2 == 2 and number3 == 2)):
    win = current_bet * 8
    print("Win bar-bar-bar - bar-bar-bar")
elif((number1 == 3 and number2 == 3) or (number2 == 3 and number3 == 3)):
    win = current_bet * 6
    print("Win bar-bar - bar-bar")
elif((number1 == 4 and number2 == 4) or (number2 == 4 and number3 == 4)):
    win = current_bet * 5
    print("Win bar - bar")
elif((number1 == 5 and number2 == 5) or (number2 == 5 and number3 == 5)):
    win = current_bet * 4
    print("Win cherry - cherry")
elif((number1 == 6 and number2 == 6) or (number2 == 6 and number3 == 6)):
    win = current_bet * 3
    print("Win lemon - lemon")
elif((number1 == 7 and number2 == 7) or (number2 == 7 and number3 == 7)):
    win = current_bet * 2
    print("Win grape - grape")

if (number1 == 1 and number2 == 1 and number3 == 1):
    win = current_bet * 200
    print("!!!!!JACKPOT!!!!!")
    print("Win 7 - 7 - 7")
elif(number1 == 2 and number2 == 2 and number3 == 2):
    win = current_bet * 100
    print("Win bar-bar-bar - bar-bar-bar - bar-bar-bar")
elif(number1 == 3 and number2 == 3 and number3 == 3):
    win = current_bet * 75
    print("Win bar-bar - bar-bar - bar-bar")
elif(number1 == 4 and number2 == 4 and number3 == 4):
    win = current_bet * 50
    print("Win bar - bar - bar")
elif(number1 == 5 and number2 == 5 and number3 == 5):
    win = current_bet * 25
    print("Win cherry - cherry - cherry")
elif(number1 == 6 and number2 == 6 and number3 == 6):
    win = current_bet * 20
    print("Win lemon - lemon - lemon")
elif(number1 == 7 and number2 == 7 and number3 == 7):
    win = current_bet * 15
    print("Win grape - grape - grape")

total = win + total
total = total - current_bet

print("New total: $", total)

print("\n")

#Create exit back to main after user is done with machine