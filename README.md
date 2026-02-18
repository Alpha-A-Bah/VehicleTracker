🚗 Vehicle Usage Tracker
A lightweight Flask web application designed to track prototype vehicle usage, check‑ins/check‑outs, and maintain accurate mileage and audit history. Built with Python, Flask, and SQLite.

📌 Features (Current)
Home and About pages

SQLite database initialization script

Vehicles table with:

Registration

VIN

Model

Status (available / checked_out)

Current user

Current mileage

Last check‑in / check‑out timestamps

🛠️ Tech Stack
Python 3

Flask

SQLite

HTML / Jinja templates

VS Code

📂 Project Structure
Code
project/
│
├── app.py               # Main Flask application
├── init_db.py           # Database creation script
├── database.db          # (Ignored by Git) SQLite database file
├── .gitignore           # Git ignore rules
│
└── templates/           # HTML templates
    ├── home.html
    └── about.html
    
🧱 Database Setup
To create the database and the vehicles table, run:

Code
python init_db.py
This will generate database.db with the correct schema.

▶️ Running the App
Start the Flask development server:

Code
python app.py
Then open your browser and go to:

Code
http://127.0.0.1:5000
🔧 Future Features (Planned)
Vehicle check‑in / check‑out workflow

Usage logs table (start/end mileage per trip)

Appraisal notes

User authentication (Flask‑Login)

Manager dashboard

Search and filtering

Bootstrap UI styling

📜 License
MIT License (optional — add if you want)