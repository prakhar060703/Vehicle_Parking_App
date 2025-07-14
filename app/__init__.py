from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key'
    
    # SQLite setup
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Create DB
    with app.app_context():
        from .models import models
        db.create_all()

    # Register blueprints
    from .controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp)

    return app
