import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(vehicles);")
print(cursor.fetchall())

conn.close()
