from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_babel import Babel, gettext
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO
import matplotlib.pyplot as plt
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Extensions
login_manager = LoginManager(app)
login_manager.login_view = 'login'
babel = Babel(app)
db = SQLAlchemy(app)

# Dummy User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Set locale
@babel.locale_selector
def get_locale():
    return request.accept_languages.best_match(['en', 'am'])

# ========== ROUTES ==========

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            session['csv_file'] = path
            flash("File uploaded successfully.")
            return redirect(url_for("summary"))
        else:
            flash("Invalid file. Please upload a CSV.")
    return render_template("upload.html")

@app.route("/manual-entry", methods=["GET", "POST"])
@login_required
def manual_entry():
    if request.method == "POST":
        rows = int(request.form.get("rows", 5))
        cols = int(request.form.get("cols", 2))
        data = []
        for i in range(rows):
            row = []
            for j in range(cols):
                val = request.form.get(f"cell-{i}-{j}", "")
                row.append(val)
            data.append(row)
        df = pd.DataFrame(data)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], f"manual_{uuid.uuid4().hex[:6]}.csv")
        df.to_csv(file_path, index=False, header=False)
        session['csv_file'] = file_path
        flash("Manual data submitted.")
        return redirect(url_for("summary"))
    return render_template("manual_entry.html")

@app.route("/summary")
@login_required
def summary():
    file = session.get('csv_file')
    if not file or not os.path.exists(file):
        flash("No dataset found.")
        return redirect(url_for("upload"))
    df = pd.read_csv(file)
    desc = df.describe(include='all').fillna("")
    return render_template("summary.html", tables=[desc.to_html(classes='table table-bordered', index=True)])

@app.route("/methods", methods=["GET", "POST"])
@login_required
def methods():
    file = session.get('csv_file')
    if not file or not os.path.exists(file):
        flash("No data loaded.")
        return redirect(url_for("upload"))
    df = pd.read_csv(file)
    plot_div = None
    if request.method == "POST":
        col1 = request.form.get("col1")
        col2 = request.form.get("col2")
        if col1 and col2 and col1 in df.columns and col2 in df.columns:
            fig = px.scatter(df, x=col1, y=col2, title=f"{col1} vs {col2}")
            plot_div = fig.to_html(full_html=False)
    return render_template("methods.html", columns=df.columns.tolist(), plot_div=plot_div)

@app.route("/results")
@login_required
def results():
    return render_template("results.html")

@app.route("/download-pdf")
@login_required
def download_pdf():
    return "📄 PDF download will be implemented soon"

@app.route("/download-csv")
@login_required
def download_csv():
    file = session.get('csv_file')
    if file and os.path.exists(file):
        return send_file(file, as_attachment=True)
    flash("No file found.")
    return redirect(url_for("upload"))

@app.route("/download-excel")
@login_required
def download_excel():
    file = session.get('csv_file')
    if file and os.path.exists(file):
        df = pd.read_csv(file)
        excel_io = BytesIO()
        df.to_excel(excel_io, index=False)
        excel_io.seek(0)
        return send_file(excel_io, download_name="data.xlsx", as_attachment=True)
    flash("No data found.")
    return redirect(url_for("upload"))

# ========== AUTH ROUTES ==========

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.password == request.form["password"]:
            login_user(user)
            flash("Logged in successfully.")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if User.query.filter_by(username=username).first():
            flash("User already exists.")
        else:
            db.session.add(User(username=username, password=password))
            db.session.commit()
            flash("Registration successful.")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("login"))

@app.route("/about")
def about():
    return render_template("about.html")

# ========== RUN ==========
if __name__ == "__main__":
    app.run(debug=True)
