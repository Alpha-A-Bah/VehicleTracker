import sqlite3

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("SELECT * FROM vehicles;")
rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()
