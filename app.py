from flask import Flask, render_template, request, session, redirect, url_for, flash
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import plotly.express as px
import os

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "replace-with-a-secure-random-secret-key"

# Upload directory
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Supported methods
methods_info = {
    "desc": "Descriptive Statistics",
    "one_t": "One-Sample t-Test",
    "two_t": "Two-Sample t-Test",
    "anova1": "One-Way ANOVA",
    "reg_simple": "Simple Linear Regression",
    "corr": "Pearson Correlation",
    "chi_indep": "Chi-Square Test of Independence",
    "tsa": "Time Series Plot"
}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            session["data_path"] = filepath
            return redirect(url_for("methods"))
        flash("Please upload a valid CSV file.")
    return render_template("upload.html")

@app.route("/methods", methods=["GET", "POST"])
def methods():
    df = pd.read_csv(session.get("data_path")) if session.get("data_path") else pd.DataFrame()
    columns = df.columns.tolist() if not df.empty else []
    
    if request.method == "POST":
        session["method"] = request.form["method"]
        session["var1"] = request.form.get("var1")
        session["var2"] = request.form.get("var2")
        return redirect(url_for("results"))

    return render_template("methods.html", columns=columns, methods=methods_info)

@app.route("/results")
def results():
    if not session.get("data_path") or not session.get("method"):
        flash("Please upload a dataset and select a method first.")
        return redirect(url_for("upload"))

    df = pd.read_csv(session["data_path"])
    method = session["method"]
    var1 = session.get("var1")
    var2 = session.get("var2")

    result_html = ""
    plot_html = ""

    try:
        if method == "desc":
            result_html = df.describe(include="all").to_html(classes="table table-striped")

        elif method == "one_t":
            data = df[var1].dropna().astype(float)
            t_stat, p_val = stats.ttest_1samp(data, popmean=0)
            result_html = f"<p>One-Sample t-Test<br>t = {t_stat:.3f}, p = {p_val:.4f}</p>"

        elif method == "two_t":
            groups = df[var2].dropna().unique()
            if len(groups) < 2:
                raise ValueError("Need exactly two groups for two-sample t-test.")
            g1 = df[df[var2] == groups[0]][var1].dropna().astype(float)
            g2 = df[df[var2] == groups[1]][var1].dropna().astype(float)
            t_stat, p_val = stats.ttest_ind(g1, g2)
            result_html = f"<p>Two-Sample t-Test<br>t = {t_stat:.3f}, p = {p_val:.4f}</p>"

        elif method == "anova1":
            model = smf.ols(f"{var1} ~ C({var2})", data=df.dropna(subset=[var1, var2])).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)
            result_html = anova_table.to_html(classes="table table-bordered")

        elif method == "reg_simple":
            x = df[var1].dropna().astype(float)
            y = df[var2].dropna().astype(float)
            combined = pd.concat([x, y], axis=1).dropna()
            model = sm.OLS(combined[var2], sm.add_constant(combined[var1])).fit()
            result_html = model.summary().tables[1].as_html()

        elif method == "corr":
            corr_matrix = df[[var1, var2]].corr()
            result_html = corr_matrix.to_html(classes="table table-bordered")

        elif method == "chi_indep":
            contingency = pd.crosstab(df[var1], df[var2])
            chi2, p_val, _, _ = stats.chi2_contingency(contingency)
            result_html = f"<p>Chi-Square Test<br>chi² = {chi2:.3f}, p = {p_val:.4f}</p>"

        elif method == "tsa":
            data = df[var1].dropna().astype(float)
            fig = px.line(data, title=f"Time Series Plot of {var1}")
            plot_html = fig.to_html(full_html=False)

        else:
            result_html = "<p class='text-danger'>Selected method is not implemented.</p>"

    except Exception as e:
        result_html = f"<div class='alert alert-danger'>Error occurred: {str(e)}</div>"

    return render_template("results.html",
        method_name=methods_info.get(method, method),
        result_html=result_html,
        plot_html=plot_html
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
