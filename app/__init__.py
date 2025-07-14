from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key'
    
    # SQLite setup
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/app.db'
    # If the file doesn’t exist, SQLite automatically creates it when you connect.
    # If it does exist, it just uses the existing database file.

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # It tells Tells SQLAlchemy not to track every change to objects in memory — which saves memory and avoids warnings.

    db.init_app(app)
    # I created db = SQLAlchemy() outside the app (global scope).
    # But Flask needs it to be connected to a specific app instance.
    # So calling db.init_app(app) connects SQLAlchemy to the Flask app created by create_app().

    # Create DB
    with app.app_context():
        from .models import models
        db.create_all()

    # Flask uses something called an "application context" to keep track of which app is currently running.
    # Some operations (like database access) only work inside this context.
    # db.create_all()
    # This tells SQLAlchemy to:
    # “Look at all models I imported. If the tables for them don’t exist in the database yet, create them.”

    # Register blueprints
    from .controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp)
    # Think of auth_bp as a mini-app that contains login, signup, and maybe logout routes — all grouped together.
    # It’s like saying:
    # “Hey Flask, include all the routes and logic defined in this blueprint.”

    return app
