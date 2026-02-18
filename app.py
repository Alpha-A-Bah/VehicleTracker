from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/vehicles")
def vehicles():
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM vehicles;")
    rows = cursor.fetchall()

    connection.close()

    return render_template("vehicles.html", vehicles=rows)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
