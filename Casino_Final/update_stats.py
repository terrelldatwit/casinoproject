import sqlite3
import os

# --- Configuration ---
DATABASE_FILE = 'CasinoDB.db'

# Add the names of all your game tables to this list.
GAME_TABLES = [
    'Blackjack',
    'Craps',
    'HighLow',
    'Poker',
    'Roulette',
    'Slots'
]

def update_player_stats():
    """
    Connects to the casino database, aggregates player statistics from all game
    tables, and updates the main PLAYERS table with the totals based on the
    new calculation rules.
    """
    if not os.path.exists(DATABASE_FILE):
        print(f"Error: Database file '{DATABASE_FILE}' not found.")
        print("Please make sure the script is in the same directory as the database.")
        return

    conn = None
    try:
        # --- 1. Establish Database Connection ---
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        print(f"Successfully connected to {DATABASE_FILE}.")

        # --- 2. Get All Players ---
        cursor.execute("SELECT ID, first_name, last_name, total_deposit FROM PLAYERS")
        players = cursor.fetchall()
        print(f"Found {len(players)} players to process.")

        # --- 3. Process Each Player ---
        for player in players:
            player_id, first_name, last_name, total_deposit = player
            full_name = f"{first_name} {last_name}"

            # Initialize aggregate values for the current player.
            total_wins_count = 0        # NEW: Counts total number of winning rounds.
            total_bets_count = 0        # Counts total number of bets made.
            total_monetary_gain = 0.0   # For calculating the real balance.
            total_monetary_loss = 0.0   # For calculating the real balance.

            print(f"\nProcessing stats for player: {full_name} (ID: {player_id})")

            # --- 4. Aggregate Data from Each Game Table ---
            for table in GAME_TABLES:
                # NEW QUERY: Gathers the count of wins, number of bets, and the
                # actual monetary win/loss for balance calculation.
                query = f"""
                    SELECT
                        SUM(wins),
                        SUM(number_of_bets),
                        SUM(CASE WHEN money_won > 0 THEN money_won ELSE 0 END),
                        SUM(CASE WHEN money_won < 0 THEN -money_won ELSE 0 END)
                    FROM {table}
                    WHERE player_name = ?
                """
                cursor.execute(query, (full_name,))
                game_stats = cursor.fetchone()

                if game_stats:
                    game_wins_count = game_stats[0] or 0
                    game_bets_count = game_stats[1] or 0
                    game_monetary_gain = game_stats[2] or 0
                    game_monetary_loss = game_stats[3] or 0

                    total_wins_count += game_wins_count
                    total_bets_count += game_bets_count
                    total_monetary_gain += game_monetary_gain
                    total_monetary_loss += game_monetary_loss
                    
                    if game_bets_count > 0:
                        print(f"  - From {table}: Wins={game_wins_count}, Bets={game_bets_count}")

            # --- 5. Perform New Calculations ---
            # The 'Lost' column is now calculated as Total Bets - Total Wins.
            final_lost_count = total_bets_count - total_wins_count
            
            # The player's balance is still calculated from their actual monetary performance.
            new_balance = (total_deposit or 0) + total_monetary_gain - total_monetary_loss
            
            # --- 6. Update the PLAYERS Table ---
            # The 'money_won' and 'money_loss' columns are repurposed to store the win/loss counts.
            update_query = """
                UPDATE PLAYERS
                SET
                    money_won = ?,
                    Bets = ?,
                    money_loss = ?,
                    balance = ?
                WHERE
                    ID = ?
            """
            cursor.execute(update_query, (
                total_wins_count,
                total_bets_count,
                final_lost_count,
                new_balance,
                player_id
            ))
            
            print(f"  -> Updated Totals: Won (rounds)={total_wins_count}, Lost (rounds)={final_lost_count}, Total Bets={total_bets_count}")
            print(f"  -> New Monetary Balance: ${new_balance:,.2f}")

        # --- 7. Commit Changes ---
        conn.commit()
        print("\nAll player statistics have been successfully updated with the new logic!")

    except sqlite3.Error as e:
        print(f"\nAn error occurred: {e}")
        if conn:
            conn.rollback()
            print("Transaction has been rolled back.")
            
    finally:
        # --- 8. Close Connection ---
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    update_player_stats()