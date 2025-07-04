from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_babel import Babel, gettext as _
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import pandas as pd

# --- Flask setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Flask extensions ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
babel = Babel(app)

# --- User model ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            flash(_('Logged in successfully.'), 'success')
            return redirect(url_for('home'))
        flash(_('Invalid credentials.'), 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('Logged out successfully.'), 'info')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        existing_user = User.query.filter_by(username=request.form['username']).first()
        if existing_user:
            flash(_('Username already taken.'), 'danger')
            return redirect(url_for('register'))
        new_user = User(username=request.form['username'])
        new_user.set_password(request.form['password'])
        db.session.add(new_user)
        db.session.commit()
        flash(_('Account created successfully. Please login.'), 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        message = request.form['message']
        # Save or handle feedback as needed
        flash(_('Thanks for your feedback!'), 'success')
        return redirect(url_for('home'))
    return render_template('feedback.html')

# Example protected route
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# --- Locale selector ---
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['en', 'am'])

# --- Initialize DB ---
@app.before_first_request
def create_tables():
    db.create_all()

# --- Run app ---
if __name__ == '__main__':
    app.run(debug=True)
