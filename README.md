# 🚗 Vehicle Parking App

A simple Flask-based multi-user web application to manage vehicle parking lots. Supports user signup/login and is backed by SQLite.

## 📦 Tech Stack
- Flask (Backend)
- Jinja2 + Bootstrap (Frontend)
- SQLite (Database)

## 🚀 Getting Started

1. Clone the repo & navigate to the folder:
   
   git clone https://github.com/your-username/Vehicle_Parking_App.git
   cd Vehicle_Parking_App

2. Create & activate virtual environment (Windows):

    python -m venv venv
    
    venv\Scripts\activate

3. Install dependencies:

    pip install -r requirements.txt

4. Run the app:

    python run.py
    App runs at: http://127.0.0.1:5000/

    Database (instance/app.db) is auto-created on first run.



📁 Project Structure

    app/
    ├── controllers/
    ├── models/
    ├── static/
    ├── templates/
    ├── __init__.py
    instance/
    ├── app.db
    run.py
    requirements.txt