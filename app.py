from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os
import uuid
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt

# App config
app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Init
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(64))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            filename = f"{uuid.uuid4()}_{file.filename}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            session["uploaded_file"] = path
            flash("File uploaded successfully!", "success")
            return redirect(url_for("summary"))
        else:
            flash("Invalid file. Please upload a CSV.", "danger")
    return render_template("upload.html")

@app.route("/manual-entry", methods=["GET", "POST"])
@login_required
def manual_entry():
    if request.method == "POST":
        raw_data = request.form["raw_data"]
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(raw_data))
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_manual.csv")
            df.to_csv(temp_path, index=False)
            session["uploaded_file"] = temp_path
            flash("Manual data saved successfully!", "success")
            return redirect(url_for("summary"))
        except Exception as e:
            flash(f"Error parsing manual input: {str(e)}", "danger")
    return render_template("manual_entry.html")

@app.route("/summary")
@login_required
def summary():
    file_path = session.get("uploaded_file")
    if not file_path or not os.path.exists(file_path):
        flash("No file found. Please upload or enter data.", "warning")
        return redirect(url_for("upload"))
    df = pd.read_csv(file_path)
    summary_stats = df.describe(include='all').to_html(classes="table table-bordered")
    return render_template("summary.html", table=summary_stats, columns=df.columns.tolist())

@app.route("/methods", methods=["GET", "POST"])
@login_required
def methods():
    file_path = session.get("uploaded_file")
    result = None
    plot_div = None
    columns = []

    if file_path and os.path.exists(file_path):
        df = pd.read_csv(file_path)
        columns = df.columns.tolist()

        if request.method == "POST":
            method = request.form.get("method")
            col1 = request.form.get("col1")
            col2 = request.form.get("col2")

            try:
                if method == "correlation":
                    corr_val = df[col1].corr(df[col2])
                    fig = px.scatter(df, x=col1, y=col2, title=f"Correlation = {corr_val:.3f}")
                    plot_div = pio.to_html(fig, full_html=False)
                    result = f"Correlation between {col1} and {col2}: {corr_val:.3f}"
                elif method == "summary":
                    result = df[[col1]].describe().to_html(classes="table table-bordered")
                else:
                    result = "Method not yet implemented."
            except Exception as e:
                result = f"Error: {str(e)}"
    else:
        flash("Upload or enter data first.", "warning")
        return redirect(url_for("upload"))

    return render_template("methods.html", columns=columns, result=result, plot_div=plot_div)

@app.route("/results")
@login_required
def results():
    return render_template("results.html")

@app.route("/download-csv")
@login_required
def download_csv():
    file_path = session.get("uploaded_file")
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    flash("No file to download.", "danger")
    return redirect(url_for("home"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["username"]
        pwd = request.form["password"]
        user = User.query.filter_by(username=uname, password=pwd).first()
        if user:
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form["username"]
        pwd = request.form["password"]
        if User.query.filter_by(username=uname).first():
            flash("Username already exists.", "danger")
        else:
            db.session.add(User(username=uname, password=pwd))
            db.session.commit()
            flash("User registered. You can log in now.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

# Create DB if not exists
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
