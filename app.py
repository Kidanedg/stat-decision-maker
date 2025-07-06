from flask import Flask, render_template, request, session, redirect, url_for, flash
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import plotly.express as px
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

methods_info = {
    "desc": "Descriptive Statistics",
    "one_t": "One-Sample t-Test",
    "two_t": "Two-Sample t-Test",
    "anova1": "One-Way ANOVA",
    "anova2": "Two-Way ANOVA",
    "reg_simple": "Simple Linear Regression",
    "reg_multiple": "Multiple Linear Regression",
    "corr": "Pearson Correlation",
    "chi_good": "Chi-Square Goodness of Fit",
    "chi_indep": "Chi-Square Test of Independence",
    "chi_homog": "Chi-Square Test of Homogeneity",
    "tsa": "Time Series Analysis"
}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            session["data_path"] = path
            return redirect(url_for("methods"))
        else:
            flash("Upload a valid CSV.")
    return render_template("upload.html")


@app.route("/methods", methods=["GET", "POST"])
def methods():
    df = pd.read_csv(session["data_path"]) if session.get("data_path") else pd.DataFrame()
    cols = df.columns.tolist()
    if request.method == "POST":
        session["method"] = request.form["method"]
        session["var1"] = request.form.get("var1")
        session["var2"] = request.form.get("var2")
        return redirect(url_for("results"))
    return render_template("methods.html", columns=cols, methods=methods_info)


@app.route("/plot", methods=["GET", "POST"])
def plot():
    df = pd.read_csv(session["data_path"])
    fig_html = None
    if request.method == "POST":
        x, y = request.form["x_var"], request.form["y_var"]
        fig = px.scatter(df, x=x, y=y, title=f"{y} vs {x}")
        fig_html = fig.to_html(full_html=False)
    return render_template("plot.html", columns=df.columns.tolist(), fig_html=fig_html)


@app.route("/results")
def results():
    if not session.get("data_path") or not session.get("method"):
        flash("Upload data and choose a method first.")
        return redirect(url_for("upload"))

    df = pd.read_csv(session["data_path"])
    method = session["method"]
    col1 = session.get("var1")
    col2 = session.get("var2")
    result_html = ""
    plot_html = ""

    try:
        if method == "desc":
            result_html = df.describe().to_html(classes="table table-bordered")
        elif method == "one_t":
            data = df[col1].dropna().astype(float)
            t, p = stats.ttest_1samp(data, popmean=0)
            result_html = f"<p>t = {t:.3f}, p = {p:.4f}</p>"
        elif method == "two_t":
            g1 = df[df[col2] == df[col2].unique()[0]][col1].dropna().astype(float)
            g2 = df[df[col2] == df[col2].unique()[1]][col1].dropna().astype(float)
            t, p = stats.ttest_ind(g1, g2)
            result_html = f"<p>t = {t:.3f}, p = {p:.4f}</p>"
        elif method == "anova1":
            df2 = df[[col1, col2]].dropna()
            df2.columns = ["value", "group"]
            model = smf.ols('value ~ C(group)', data=df2).fit()
            result_html = sm.stats.anova_lm(model).to_html(classes="table table-bordered")
        elif method == "anova2":
            df2 = df[[col1, col2]].dropna()
            df2.columns = ["y", "x"]
            result_html = "<p>Requires two categorical factors. Please pre-format data.</p>"
        elif method == "reg_simple":
            x, y = df[col1].dropna().astype(float), df[col2].dropna().astype(float)
            model = sm.OLS(y, sm.add_constant(x)).fit()
            result_html = model.summary().tables[1].as_html()
        elif method == "reg_multiple":
            df2 = df[[col2] + [col1]].dropna().astype(float)  # need multi
            result_html = "To be implemented."
        elif method == "corr":
            result_html = df[[col1, col2]].corr().to_html(classes="table table-bordered")
        elif method in ("chi_good", "chi_indep", "chi_homog"):
            tb = pd.crosstab(df[col1], df[col2])
            chi2, p, _, _ = stats.chi2_contingency(tb)
            result_html = f"<p>chi2 = {chi2:.3f}, p = {p:.4f}</p>"
        elif method == "tsa":
            data = df[col1].dropna().astype(float)
            fig = px.line(data, title=f"Time Series: {col1}")
            plot_html = fig.to_html(full_html=False)
        else:
            result_html = "<p>Method not implemented.</p>"

    except Exception as e:
        result_html = f"<div class='alert alert-danger'>Error: {e}</div>"

    return render_template("results.html", result_html=result_html, plot_html=plot_html, method_name=methods_info[method])
