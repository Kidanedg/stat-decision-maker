from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import plotly.express as px
import os

app = Flask(__name__)
app.secret_key = "secret-key"

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# In-memory user store for demonstration
users = {}

class User(UserMixin):
    def __init__(self, id_, username, password_hash):
        self.id = id_
        self.username = username
        self.password_hash = password_hash

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Home
@app.route("/")
def home():
    return render_template("home.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_id = str(len(users) + 1)
        password_hash = generate_password_hash(password)
        users[user_id] = User(user_id, username, password_hash)
        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        for user_id, user in users.items():
            if user.username == username and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Login successful.")
                return redirect(url_for("home"))
        flash("Invalid credentials.")
    return render_template("login.html")

# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("home"))

# Upload CSV
@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if file and file.filename.endswith(".csv"):
            df = pd.read_csv(file)
            session["data"] = df.to_json()
            flash("File uploaded successfully.")
            return redirect(url_for("summary"))
        else:
            flash("Invalid file format. Upload a CSV file.")
    return render_template("upload.html")

# Manual entry
@app.route("/manual-entry", methods=["GET", "POST"])
@login_required
def manual_entry():
    if request.method == "POST":
        try:
            data = request.form["data"]
            df = pd.read_csv(pd.compat.StringIO(data))
            session["data"] = df.to_json()
            flash("Data entered successfully.")
            return redirect(url_for("summary"))
        except Exception as e:
            flash(f"Error: {e}")
    return render_template("manual_entry.html")

# Summary
@app.route("/summary")
@login_required
def summary():
    if "data" not in session:
        flash("No data available. Please upload or enter data.")
        return redirect(url_for("upload"))
    df = pd.read_json(session["data"])
    return render_template("summary.html", table=df.head().to_html(classes="table table-striped", index=False))

# Methods
@app.route("/methods", methods=["GET", "POST"])
@login_required
def methods():
    if request.method == "POST":
        session["method"] = request.form["method"]
        return redirect(url_for("results"))
    return render_template("methods.html")

# Results with Plotly
@app.route("/results")
@login_required
def results():
    if "data" not in session:
        flash("Please upload or enter data first.")
        return redirect(url_for("upload"))

    df = pd.read_json(session["data"])
    method = session.get("method", "summary")

    # Example visualization (scatterplot)
    if "x" in df.columns and "y" in df.columns:
        fig = px.scatter(df, x="x", y="y", title="Scatter Plot")
        plot_html = fig.to_html(full_html=False)
    else:
        plot_html = "<p>No 'x' and 'y' columns to plot.</p>"

    return render_template("results.html", method=method, plot_html=plot_html)

# About
@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
