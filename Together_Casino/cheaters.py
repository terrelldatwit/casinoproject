import sqlite3
from datetime import datetime

DB_PATH = "CasinoDB.db"

# Unified cheater logging function for any game
def log_cheater(player_id, game_name, win_rate):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Ensure CHEAT_LOG exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS CHEAT_LOG (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER NOT NULL,
            event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL,
            details TEXT
        )
    """)

    # Ensure is_flagged column exists in PLAYERS
    cur.execute("PRAGMA table_info(PLAYERS)")
    cols = [row[1] for row in cur.fetchall()]
    if "is_flagged" not in cols:
        cur.execute("ALTER TABLE PLAYERS ADD COLUMN is_flagged INTEGER DEFAULT 0")

    # Insert log entry
    cur.execute("""
        INSERT INTO CHEAT_LOG (player_id, event_type, details)
        VALUES (?, ?, ?)
    """, (player_id, game_name, f"{win_rate * 100:.1f}% win rate over 20 games"))

    # Flag the player
    cur.execute("UPDATE PLAYERS SET is_flagged=1 WHERE ID=?", (player_id,))

    conn.commit()
    conn.close()
