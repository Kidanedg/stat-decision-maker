from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import plotly.express as px
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy user store
users = {'admin': {'password': 'admin123'}}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash('User already exists.')
        else:
            users[username] = {'password': password}
            flash('User registered. You can log in now.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            df = pd.read_csv(file)
            session['data'] = df.to_json()
            flash('File uploaded successfully.')
            return redirect(url_for('results'))
    return render_template('upload.html')

@app.route('/results')
@login_required
def results():
    if 'data' not in session:
        flash("No data uploaded.")
        return redirect(url_for('upload'))
    df = pd.read_json(session['data'])

    # Plotly plot
    fig = px.histogram(df, x=df.columns[0], title='Distribution Plot')
    graph_html = fig.to_html(full_html=False)

    return render_template('results.html', table=df.head().to_html(classes='table'), graph_html=graph_html)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/methods')
@login_required
def methods():
    return render_template('methods.html')

@app.route('/manual-entry')
@login_required
def manual_entry():
    return render_template('manual_entry.html')
