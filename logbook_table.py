import sqlite3

# Connect to your existing database
connection = sqlite3.connect("database.db")
cursor = connection.cursor()

# Function to check if a column exists
def column_exists(table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

# Add available_date column
if not column_exists("jobcards", "available_date"):
    cursor.execute("""
    ALTER TABLE jobcards
    ADD COLUMN available_date TEXT;
    """)
    print("Added column: available_date")
else:
    print("Column available_date already exists, skipping.")

# Add required_by column
if not column_exists("jobcards", "required_by"):
    cursor.execute("""
    ALTER TABLE jobcards
    ADD COLUMN required_by TEXT;
    """)
    print("Added column: required_by")
else:
    print("Column required_by already exists, skipping.")

connection.commit()
connection.close()

print("Jobcards table updated successfully.")
