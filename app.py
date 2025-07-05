from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import os
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)
app.secret_key = 'your-secret-key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dummy user model
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Dummy user store
users = {'test': User('1', 'test')}

@login_manager.user_loader
def load_user(user_id):
    return users.get('test') if user_id == '1' else None

# -----------------------
# Routes
# -----------------------

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username in users:
            login_user(users[username])
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            df.to_csv('uploaded.csv', index=False)
            flash('CSV uploaded successfully!', 'success')
            return redirect(url_for('results'))
        else:
            flash('Please upload a valid CSV file.', 'danger')
    return render_template('upload.html')

@app.route('/manual-entry', methods=['GET', 'POST'])
@login_required
def manual_entry():
    if request.method == 'POST':
        raw_data = request.form.get('data')
        with open('uploaded.csv', 'w') as f:
            f.write(raw_data)
        flash('Manual data entry saved!', 'success')
        return redirect(url_for('results'))
    return render_template('manual_entry.html')

@app.route('/methods')
@login_required
def methods():
    return render_template('methods.html')

@app.route('/results')
@login_required
def results():
    try:
        df = pd.read_csv('uploaded.csv')
        fig = px.histogram(df, x=df.columns[0])
        graph_html = pio.to_html(fig, full_html=False)
        return render_template('results.html', tables=[df.to_html(classes='table table-striped')], graph_html=graph_html)
    except Exception as e:
        flash('Please upload or enter data first.', 'warning')
        return redirect(url_for('upload'))

@app.route('/download_csv')
@login_required
def download_csv():
    if os.path.exists('uploaded.csv'):
        return send_file('uploaded.csv', as_attachment=True)
    flash('No file available to download.', 'warning')
    return redirect(url_for('results'))

# Run the app (only for local testing)
if __name__ == '__main__':
    app.run(debug=True)
