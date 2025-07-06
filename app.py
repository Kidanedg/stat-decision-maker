from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import plotly.express as px
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if file.filename.endswith(".csv"):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            df = pd.read_csv(filepath)
            session["data_path"] = filepath
            return redirect(url_for("methods"))
    return render_template("upload.html")

@app.route("/manual-entry", methods=["GET", "POST"])
def manual_entry():
    return render_template("manual_entry.html")

@app.route("/methods", methods=["GET", "POST"])
def methods():
    df = pd.read_csv(session["data_path"]) if "data_path" in session else pd.DataFrame()
    columns = df.columns.tolist() if not df.empty else []
    return render_template("methods.html", columns=columns)

@app.route("/plot", methods=["GET", "POST"])
def plot():
    df = pd.read_csv(session["data_path"]) if "data_path" in session else pd.DataFrame()
    columns = df.columns.tolist() if not df.empty else []
    fig_html = None

    if request.method == "POST":
        x_col = request.form.get("x_var")
        y_col = request.form.get("y_var")
        if x_col and y_col:
            fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
            fig_html = fig.to_html(full_html=False)

    return render_template("plot.html", columns=columns, fig_html=fig_html)

@app.route("/results")
def results():
    return render_template("results.html")
