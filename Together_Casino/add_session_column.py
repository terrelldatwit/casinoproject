import sqlite3  #Import the sqlite3 library to interact with SQLite databases

#Connect to the existing CasinoDB
conn = sqlite3.connect("CasinoDB.db")  #Establish connection to the CasinoDB database
cur = conn.cursor()  #Create a cursor to execute SQL commands

#Function to safely add a column if it doesn't exist
def add_column_if_missing(table_name, column_name, column_type):  #Define a function to add a column if it's missing
    #Check if column exists
    cur.execute(f"PRAGMA table_info({table_name})")  #Retrieve current table schema information
    columns = [col[1] for col in cur.fetchall()]  #Extract column names from the result
    
    if column_name not in columns:  #If the target column is not present
        try:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")  #Add the missing column
            print(f"Added column '{column_name}' to table '{table_name}'.")  #Confirm column was added
        except sqlite3.OperationalError as e:  #Catch potential SQL error
            print(f"Error adding column '{column_name}' to '{table_name}': {e}")  #Print error message
    else:
        print(f"Column '{column_name}' already exists in table '{table_name}'.")  #Notify column already exists

#Add session_number to both tables
add_column_if_missing("Roulette", "session_number", "INTEGER")  #Add session_number column to Roulette table if missing
add_column_if_missing("Craps", "session_number", "INTEGER")  #Add session_number column to Craps table if missing
add_column_if_missing("Blackjack", "session_number", "INTEGER")  #Add session_number column to Craps table if missing


conn.commit()  #Commit all database changes
conn.close()  #Close the database connection
