# casino_admin.py

import sys
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox, QGridLayout
)
from PyQt6.QtCore import Qt

# Define the database path
DB_PATH = "CasinoDB.db"
# Define the hardcoded ID for the casino stats row
CASINO_ID = 7589

class CasinoAdminPanel(QWidget):
    """
    A panel for casino administrators to view aggregated statistics for the entire casino.
    """
    def __init__(self, parent_menu=None):
        super().__init__()
        self.setWindowTitle("Casino Admin Panel")
        self.setGeometry(400, 200, 500, 450)
        self.parent_menu = parent_menu
        
        # Define the list of game tables to aggregate data from
        self.game_tables = ["Blackjack", "Craps", "HighLow", "Poker", "Roulette", "Slots"]

        self.setup_ui()
        self.update_stats()

    def setup_ui(self):
        """
        Sets up the user interface with labels for each statistic and a refresh button.
        """
        main_layout = QVBoxLayout()
        grid_layout = QGridLayout()

        # Create labels for displaying stats
        self.id_label = QLabel("N/A")
        self.money_won_label = QLabel("$0.00")
        self.bets_label = QLabel("0")
        self.won_label = QLabel("0")
        self.lost_label = QLabel("0")
        self.money_loss_label = QLabel("$0.00")
        self.net_profit_label = QLabel("$0.00")
        self.total_cash_label = QLabel("$0.00")

        # Add labels to the grid layout for a clean presentation
        grid_layout.addWidget(QLabel("<b>Casino ID:</b>"), 0, 0)
        grid_layout.addWidget(self.id_label, 0, 1)
        grid_layout.addWidget(QLabel("<b>Casino Gross Profit (money_won):</b>"), 1, 0)
        grid_layout.addWidget(self.money_won_label, 1, 1)
        grid_layout.addWidget(QLabel("<b>Casino Gross Loss (money_loss):</b>"), 2, 0)
        grid_layout.addWidget(self.money_loss_label, 2, 1)
        grid_layout.addWidget(QLabel("<b>Casino Net Profit:</b>"), 3, 0)
        grid_layout.addWidget(self.net_profit_label, 3, 1)
        grid_layout.addWidget(QLabel("<b>Casino Net Cash:</b>"), 4, 0) 
        grid_layout.addWidget(self.total_cash_label, 4, 1)
        grid_layout.addWidget(QLabel("<b>Total Bets Placed:</b>"), 5, 0)
        grid_layout.addWidget(self.bets_label, 5, 1)
        grid_layout.addWidget(QLabel("<b>Total Casino Wins (Player Losses):</b>"), 6, 0)
        grid_layout.addWidget(self.won_label, 6, 1)
        grid_layout.addWidget(QLabel("<b>Total Casino Losses (Player Wins):</b>"), 7, 0)
        grid_layout.addWidget(self.lost_label, 7, 1)


        main_layout.addLayout(grid_layout)

        # Refresh button to update stats
        self.refresh_button = QPushButton("Refresh & Update Database")
        self.refresh_button.clicked.connect(self.update_stats)
        main_layout.addWidget(self.refresh_button)
        
        # Back button
        if self.parent_menu:
            back_button = QPushButton("Back to Main Menu")
            back_button.clicked.connect(self.back_to_menu)
            main_layout.addWidget(back_button)

        self.setLayout(main_layout)

    def update_stats(self):
        """
        Calculates stats from all game tables, updates the CASINO table in the database,
        and then refreshes the display with the new data.
        """
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                
                # Ensure necessary columns exist in CASINO table
                cur.execute("PRAGMA table_info(CASINO)")
                columns = [info[1] for info in cur.fetchall()]
                if 'total_cashout' not in columns:
                    cur.execute("ALTER TABLE CASINO ADD COLUMN total_cashout REAL DEFAULT 0")
                if 'total_cash' not in columns:
                    cur.execute("ALTER TABLE CASINO ADD COLUMN total_cash REAL DEFAULT 0")
                conn.commit()


                total_bets = 0
                total_player_wins = 0
                total_player_losses = 0
                total_player_net_winnings = 0.0

                # Aggregate data from all individual game tables
                for table in self.game_tables:
                    try:
                        cur.execute(f"PRAGMA table_info({table})")
                        columns = [info[1] for info in cur.fetchall()]
                        
                        query = "SELECT SUM(number_of_bets), SUM(wins), SUM(bet_amount), SUM(money_won)"
                        if 'losses' in columns:
                            query += ", SUM(losses)"
                        else:
                            query += ", 0"
                            
                        query += f" FROM {table}"
                        
                        cur.execute(query)
                        result = cur.fetchone()
                        
                        if result and result[0] is not None:
                            total_bets += result[0]
                            total_player_wins += result[1]
                            
                            bet_amount = result[2] if result[2] is not None else 0.0
                            money_won = result[3] if result[3] is not None else 0.0
                            losses = result[4] if result[4] is not None else 0
                            total_player_losses += losses

                            if table in ["Slots", "HighLow"]:
                                total_player_net_winnings += (money_won - bet_amount)
                            else:
                                total_player_net_winnings += money_won
                    except sqlite3.OperationalError:
                        print(f"Warning: Table '{table}' not found or query failed. Skipping.")
                        continue
                
                # Get total deposits by summing from the PLAYERS table
                cur.execute("SELECT SUM(total_deposit) FROM PLAYERS")
                deposit_result = cur.fetchone()
                total_deposits = deposit_result[0] if deposit_result and deposit_result[0] is not None else 0.0
                
                # Get total cashouts from CASINO table
                cur.execute("SELECT total_cashout FROM CASINO WHERE id=?", (CASINO_ID,))
                cashout_result = cur.fetchone()
                total_cashouts = cashout_result[0] if cashout_result and cashout_result[0] is not None else 0.0

                # Define casino stats
                casino_profit = -total_player_net_winnings if total_player_net_winnings < 0 else 0
                casino_loss = total_player_net_winnings if total_player_net_winnings > 0 else 0
                casino_net_profit = casino_profit - casino_loss
                
                # New calculation for total_cash
                casino_total_cash = max(0, total_deposits + casino_net_profit - total_cashouts)

                
                # Update the CASINO table
                cur.execute("""
                    UPDATE CASINO
                    SET money_won = ?, Bets = ?, Won = ?, Lost = ?,
                        money_loss = ?, net_profit = ?,
                        total_cash = ?
                    WHERE id = ?
                """, (
                    casino_profit, total_bets, total_player_losses,
                    total_player_wins, casino_loss,
                    casino_net_profit, casino_total_cash, CASINO_ID
                ))
                conn.commit()

                # Fetch the newly updated data from the CASINO table to display it
                cur.execute("SELECT id, money_won, Bets, Won, Lost, money_loss, net_profit, total_cash FROM CASINO WHERE id=?", (CASINO_ID,))
                stats = cur.fetchone()
                if stats:
                    self.id_label.setText(str(stats[0]))
                    self.money_won_label.setText(f"${stats[1]:.2f}")
                    self.bets_label.setText(str(stats[2]))
                    self.won_label.setText(str(stats[3]))
                    self.lost_label.setText(str(stats[4]))
                    self.money_loss_label.setText(f"${stats[5]:.2f}")
                    self.net_profit_label.setText(f"${stats[6]:.2f}")
                    self.total_cash_label.setText(f"${stats[7]:.2f}")
                
                QMessageBox.information(self, "Success", "Casino statistics have been updated.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while updating stats: {e}")

    def back_to_menu(self):
        """
        Closes the admin panel and shows the parent menu.
        """
        self.close()
        if self.parent_menu:
            self.parent_menu.show()

# This allows the script to be run directly for testing
if __name__ == '__main__':
    app = QApplication(sys.argv)
    admin_panel = CasinoAdminPanel()
    admin_panel.show()
    sys.exit(app.exec())
