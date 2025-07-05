from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import plotly.express as px
import json

app = Flask(__name__)
app.secret_key = "supersecret"

login_manager = LoginManager()
login_manager.init_app(app)

# Dummy user
class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {"admin": {"password": "pass"}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username]["password"] == password:
            login_user(User(username))
            return redirect(url_for("methods"))
        else:
            flash("Invalid login")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/methods", methods=["GET", "POST"])
@login_required
def methods():
    if request.method == "POST":
        session["method"] = request.form["method"]
        return redirect(url_for("results"))
    return render_template("methods.html")

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
            session["data"] = df.to_json()
            flash("File uploaded successfully!")
            return redirect(url_for("methods"))
        else:
            flash("Please upload a CSV file.")
    return render_template("upload.html")

@app.route("/results")
@login_required
def results():
    if "data" not in session:
        flash("No data found. Please upload first.")
        return redirect(url_for("upload"))

    df = pd.read_json(session["data"])
    method = session.get("method", "descriptive")
    results_html = ""
    plot_html = ""

    try:
        if method == "descriptive":
            results_html = df.describe().to_html(classes="table table-bordered")

        elif method == "t1":
            col = df.select_dtypes(include="number").columns[0]
            t_stat, p_val = stats.ttest_1samp(df[col], popmean=0)
            results_html = f"<p><strong>t = {t_stat:.3f}</strong>, p = {p_val:.3f}</p>"

        elif method == "t2":
            col = df.select_dtypes(include="number").columns[0]
            group_col = df.select_dtypes(include="object").columns[0]
            g1, g2 = [df[df[group_col] == val][col] for val in df[group_col].unique()]
            t_stat, p_val = stats.ttest_ind(g1, g2)
            results_html = f"<p><strong>t = {t_stat:.3f}</strong>, p = {p_val:.3f}</p>"

        elif method == "anova1":
            df.columns = ['value', 'group']
            model = smf.ols('value ~ C(group)', data=df).fit()
            anova_table = sm.stats.anova_lm(model)
            results_html = anova_table.to_html(classes="table table-bordered")

        elif method == "anova2":
            model = smf.ols('value ~ C(factor1) + C(factor2) + C(factor1):C(factor2)', data=df).fit()
            anova_table = sm.stats.anova_lm(model)
            results_html = anova_table.to_html(classes="table table-bordered")

        elif method == "reg_simple":
            x, y = df.columns[:2]
            model = smf.ols(f"{y} ~ {x}", data=df).fit()
            results_html = model.summary().tables[1].as_html()

        elif method == "reg_multiple":
            y = df.columns[0]
            X = "+".join(df.columns[1:])
            model = smf.ols(f"{y} ~ {X}", data=df).fit()
            results_html = model.summary().tables[1].as_html()

        elif method == "correlation":
            results_html = df.corr().to_html(classes="table table-bordered")

        elif method == "chi_indep":
            table = pd.crosstab(df.iloc[:, 0], df.iloc[:, 1])
            chi2, p, dof, _ = stats.chi2_contingency(table)
            results_html = f"<p><strong>Chi² = {chi2:.2f}</strong>, p = {p:.3f}</p>"

        elif method == "chi_goodness":
            observed = df.iloc[:, 0].value_counts()
            expected = [len(df)/len(observed)] * len(observed)
            chi2, p = stats.chisquare(f_obs=observed, f_exp=expected)
            results_html = f"<p><strong>Chi² = {chi2:.2f}</strong>, p = {p:.3f}</p>"

        elif method == "chi_homogeneity":
            table = pd.crosstab(df.iloc[:, 0], df.iloc[:, 1])
            chi2, p, dof, _ = stats.chi2_contingency(table)
            results_html = f"<p><strong>Chi² = {chi2:.2f}</strong>, p = {p:.3f}</p>"

        elif method == "tsa":
            col = df.select_dtypes(include="number").columns[0]
            fig = px.line(df, y=col, title=f"Time Series Plot of {col}")
            plot_html = fig.to_html(full_html=False)

        else:
            results_html = "<p>Method not implemented.</p>"

    except Exception as e:
        results_html = f"<div class='alert alert-danger'>Error: {e}</div>"

    return render_template("results.html", method=method, results_html=results_html, plot_html=plot_html)
