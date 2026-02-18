import sqlite3

# 1. Connect to your existing database
connection = sqlite3.connect("database.db")
cursor = connection.cursor()

# 2. Standardise status values
cursor.execute("""
    UPDATE vehicles
    SET status = 'Available'
    WHERE LOWER(status) = 'available';
""")

cursor.execute("""
    UPDATE vehicles
    SET status = 'Booked Out'
    WHERE LOWER(status) = 'booked out';
""")

# 3. Save changes and close
connection.commit()
connection.close()

print("Status values normalised.")
