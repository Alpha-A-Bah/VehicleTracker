import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS vehicles (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               reg TEXT NOT NULL,
               vin TEXT NOT NULL,
               model TEXT NOT NULL,
               status TEXT,
               current_user TEXT,
               current_mileage INTEGER,
               last_checkin TEXT,
               last_checkout TEXT
                     
               );
""")

connection.commit()
connection.close()