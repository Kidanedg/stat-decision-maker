from flask import Flask, render_template, request, session, redirect, url_for, flash
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import plotly.express as px
import os

app = Flask(__name__)
app.secret_key = "replace-with-your-secret"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

methods_info = {
    "desc": "Descriptive Statistics",
    "one_t": "One-Sample t-Test",
    "two_t": "Two-Sample t-Test",
    "anova1": "One-Way ANOVA",
    "reg_simple": "Simple Linear Regression",
    "corr": "Pearson Correlation",
    "chi_indep": "Chi-Square Independence",
    "tsa": "Time Series Plot"
}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        f = request.files.get("file")
        if f and f.filename.endswith(".csv"):
            p = os.path.join(UPLOAD_FOLDER, f.filename)
            f.save(p)
            session["data_path"] = p
            return redirect(url_for("methods"))
        flash("Please upload a valid CSV file.")
    return render_template("upload.html")

@app.route("/methods", methods=["GET", "POST"])
def methods():
    df = pd.read_csv(session.get("data_path")) if session.get("data_path") else pd.DataFrame()
    cols = df.columns.tolist() if not df.empty else []
    if request.method == "POST":
        session["method"] = request.form["method"]
        session["var1"] = request.form.get("var1")
        session["var2"] = request.form.get("var2")
        return redirect(url_for("results"))
    return render_template("methods.html", columns=cols, methods=methods_info)

@app.route("/results")
def results():
    if not session.get("data_path") or not session.get("method"):
        flash("Upload a dataset and select a method first.")
        return redirect(url_for("upload"))
    df = pd.read_csv(session["data_path"])
    m = session["method"]
    v1 = session.get("var1")
    v2 = session.get("var2")
    
    result_html = ""
    plot_html = ""
    
    try:
        if m == "desc":
            result_html = df.describe().to_html(classes="table table-striped")
        elif m == "one_t":
            data = df[v1].dropna().astype(float)
            t, p = stats.ttest_1samp(data, popmean=0)
            result_html = f"<p>t = {t:.3f}, p = {p:.4f}</p>"
        elif m == "two_t":
            grp = df[v2].dropna().unique()
            g1 = df[df[v2] == grp[0]][v1].dropna().astype(float)
            g2 = df[df[v2] == grp[1]][v1].dropna().astype(float)
            t, p = stats.ttest_ind(g1, g2)
            result_html = f"<p>t = {t:.3f}, p = {p:.4f}</p>"
        elif m == "anova1":
            model = smf.ols(f"{v1} ~ C({v2})", data=df.dropna(subset=[v1, v2])).fit()
            result_html = sm.stats.anova_lm(model, typ=2).to_html(classes="table table-bordered")
        elif m == "reg_simple":
            x = df[v1].dropna().astype(float)
            y = df[v2].dropna().astype(float)
            df2 = pd.concat([x, y], axis=1).dropna()
            model = sm.OLS(df2[v2], sm.add_constant(df2[v1])).fit()
            result_html = model.summary().tables[1].as_html()
        elif m == "corr":
            corr = df[[v1, v2]].corr().to_html(classes="table table-bordered")
            result_html = corr
        elif m == "chi_indep":
            tbl = pd.crosstab(df[v1], df[v2])
            chi2, p, _, _ = stats.chi2_contingency(tbl)
            result_html = f"<p>chi² = {chi2:.3f}, p = {p:.4f}</p>"
        elif m == "tsa":
            data = df[v1].dropna().astype(float)
            fig = px.line(data, title=f"Time Series: {v1}")
            plot_html = fig.to_html(full_html=False)
        else:
            result_html = "<p>Method not implemented.</p>"
    except Exception as e:
        result_html = f"<div class='alert alert-danger'>Error: {e}</div>"

    return render_template("results.html",
        method_name=methods_info.get(m, ""),
        result_html=result_html,
        plot_html=plot_html
    )
