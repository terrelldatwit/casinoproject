
import sqlite3  #Import the sqlite3 library to interact with the SQLite database
from datetime import datetime  #Import datetime for logging timestamps

DB_PATH = "CasinoDB.db"  #Define the path to the SQLite database

#Unified cheater logging function for any game
def log_cheater(player_id, game_name, win_rate):  #Define a function to log cheaters based on win rate
    conn = sqlite3.connect(DB_PATH)  #Connect to the database
    cur = conn.cursor()  #Create a cursor to execute SQL commands

    #Ensure CHEAT_LOG exists
    cur.execute("""  #Create the CHEAT_LOG table if it does not already exist
        CREATE TABLE IF NOT EXISTS CHEAT_LOG (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            details TEXT
        )
    """)

    #Ensure is_flagged column exists in PLAYERS
    cur.execute("PRAGMA table_info(PLAYERS)")  #Get column information for the PLAYERS table
    cols = [row[1] for row in cur.fetchall()]  #Extract the column names
    if "is_flagged" not in cols:  #If the 'is_flagged' column is missing
        cur.execute("ALTER TABLE PLAYERS ADD COLUMN is_flagged INTEGER DEFAULT 0")  #Add the 'is_flagged' column with a default value of 0

    #Insert log entry
    cur.execute("""  #Insert a new cheater log entry into the CHEAT_LOG table
        INSERT INTO CHEAT_LOG (player_id, event_type, details)
        VALUES (?, ?, ?)
    """, (player_id, game_name, f"{win_rate * 100:.1f}% win rate over 20 games"))  #Insert player ID, game, and win rate details

    #Flag the player
    cur.execute("UPDATE PLAYERS SET is_flagged=1 WHERE ID=?", (player_id,))  #Mark the player as flagged in the PLAYERS table

    conn.commit()  #Commit all changes to the database
    conn.close()  #Close the connection

