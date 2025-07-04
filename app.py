from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_babel import Babel, _
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
import pandas as pd
import plotly.express as px
import io
import uuid

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['LANGUAGES'] = ['en', 'fr']
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Extensions ---
babel = Babel(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Dummy User Class (for testing) ---
class User(UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = f"user{id}"
        self.email = f"user{id}@example.com"

# Dummy user store
users = {'test': User(id='test')}

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

# --- Routes ---

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = users.get('test')  # Dummy login
        login_user(user)
        flash(_('Logged in successfully.'))
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'))
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            session['uploaded_file'] = filepath
            flash(_('File uploaded successfully!'))
            return redirect(url_for('summary'))
        else:
            flash(_('Please upload a valid CSV file.'))
    return render_template('upload.html')

@app.route('/manual-entry', methods=['GET', 'POST'])
@login_required
def manual_entry():
    if request.method == 'POST':
        data = request.form.get('data')
        try:
            df = pd.read_csv(io.StringIO(data))
            temp_file = os.path.join(app.config['UPLOAD_FOLDER'], f"manual_{uuid.uuid4().hex}.csv")
            df.to_csv(temp_file, index=False)
            session['uploaded_file'] = temp_file
            flash(_('Manual data submitted successfully!'))
            return redirect(url_for('summary'))
        except Exception as e:
            flash(_('Error processing data: ') + str(e))
    return render_template('manual_entry.html')

@app.route('/summary')
@login_required
def summary():
    file_path = session.get('uploaded_file')
    if not file_path or not os.path.exists(file_path):
        flash(_('No uploaded data found.'))
        return redirect(url_for('upload'))

    df = pd.read_csv(file_path)
    summary = df.describe(include='all').to_html(classes='table table-striped', border=0)
    return render_template('summary.html', table=summary)

@app.route('/methods', methods=['GET', 'POST'])
@login_required
def methods():
    file_path = session.get('uploaded_file')
    if not file_path or not os.path.exists(file_path):
        flash(_('Please upload data first.'))
        return redirect(url_for('upload'))

    df = pd.read_csv(file_path)
    columns = df.select_dtypes(include='number').columns.tolist()
    plot_html = None
    result = None

    if request.method == 'POST':
        method = request.form.get('method')
        x = request.form.get('col1')
        y = request.form.get('col2')

        if method == 'scatter' and x in df.columns and y in df.columns:
            fig = px.scatter(df, x=x, y=y, title=f"{x} vs {y}")
            plot_html = fig.to_html(full_html=False)
            result = f"Scatter plot of {x} vs {y}"

    return render_template('methods.html', columns=columns, plot_html=plot_html, result=result)

@app.route('/results')
@login_required
def results():
    return render_template('results.html')

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error=str(e)), 500

# --- Run ---
if __name__ == '__main__':
    app.run(debug=True)
