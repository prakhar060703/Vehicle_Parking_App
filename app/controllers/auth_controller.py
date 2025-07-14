from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from .. import db
from ..models.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        user = User.query.filter_by(username=uname, password=pwd).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('auth.home'))
        flash("Invalid credentials")
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if User.query.filter_by(username=uname).first():
            flash('Username already exists!')
            return redirect(url_for('auth.signup'))
        new_user = User(username=uname, password=pwd)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('home.html', username=session.get('username'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
