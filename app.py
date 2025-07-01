from flask import Flask, render_template, request
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

def save_plot(fig, name="plot.png"):
    path = os.path.join(STATIC_FOLDER, name)
    fig.savefig(path)
    plt.close(fig)
    return name

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/summary", methods=["GET", "POST"])
def summary():
    result = None
    if request.method == "POST":
        file = request.files["file"]
        if file:
            df = pd.read_csv(file)
            result = df.describe(include='all').to_html(classes="table table-bordered")
    return render_template("summary.html", result=result)

@app.route("/t_tests", methods=["GET", "POST"])
def t_tests():
    result = None
    columns = []
    if request.method == "POST":
        file = request.files["file"]
        method = request.form.get("test_type")
        col1 = request.form.get("col1")
        col2 = request.form.get("col2")
        if file:
            df = pd.read_csv(file)
            columns = df.columns.tolist()
            try:
                if method == "independent":
                    g = df[col1].dropna().unique()
                    g1 = df[df[col1] == g[0]][col2].dropna()
                    g2 = df[df[col1] == g[1]][col2].dropna()
                    stat, p = stats.ttest_ind(g1, g2)
                    decision = "Reject H₀" if p < 0.05 else "Fail to Reject H₀"
                    result = {
                        "test": "Independent t-Test",
                        "statistic": round(stat, 4),
                        "p_value": round(p, 4),
                        "decision": decision
                    }
            except Exception as e:
                result = {"error": str(e)}
    return render_template("t_tests.html", columns=columns, result=result)

@app.route("/regression", methods=["GET", "POST"])
def regression():
    result = None
    if request.method == "POST":
        file = request.files["file"]
        col1 = request.form.get("xcol")
        col2 = request.form.get("ycol")
        if file:
            df = pd.read_csv(file)
            try:
                x = df[[col1]].dropna()
                y = df[col2].dropna()
                x, y = x.loc[y.index], y
                model = LinearRegression().fit(x, y)
                result = {
                    "test": "Linear Regression",
                    "slope": round(model.coef_[0], 3),
                    "intercept": round(model.intercept_, 3),
                    "r_squared": round(model.score(x, y), 3)
                }
            except Exception as e:
                result = {"error": str(e)}
    return render_template("regression.html", result=result)

@app.route("/anova", methods=["GET", "POST"])
def anova():
    result = None
    if request.method == "POST":
        file = request.files["file"]
        group = request.form.get("group")
        value = request.form.get("value")
        if file:
            df = pd.read_csv(file)
            try:
                groups = df[group].dropna().unique()
                samples = [df[df[group] == g][value].dropna() for g in groups]
                f_stat, p_val = stats.f_oneway(*samples)
                decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                result = {
                    "test": "One-Way ANOVA",
                    "statistic": round(f_stat, 3),
                    "p_value": round(p_val, 4),
                    "decision": decision
                }
            except Exception as e:
                result = {"error": str(e)}
    return render_template("anova.html", result=result)

@app.route("/chi_square", methods=["GET", "POST"])
def chi_square():
    result = None
    if request.method == "POST":
        file = request.files["file"]
        row = request.form.get("row")
        col = request.form.get("col")
        if file:
            df = pd.read_csv(file)
            try:
                table = pd.crosstab(df[row], df[col])
                stat, p, _, _ = stats.chi2_contingency(table)
                decision = "Reject H₀" if p < 0.05 else "Fail to Reject H₀"
                result = {
                    "test": "Chi-Square Test",
                    "statistic": round(stat, 3),
                    "p_value": round(p, 4),
                    "decision": decision
                }
            except Exception as e:
                result = {"error": str(e)}
    return render_template("chi_square.html", result=result)

@app.route("/correlation", methods=["GET", "POST"])
def correlation():
    result = None
    if request.method == "POST":
        file = request.files["file"]
        xcol = request.form.get("xcol")
        ycol = request.form.get("ycol")
        if file:
            df = pd.read_csv(file)
            try:
                x = df[xcol].dropna()
                y = df[ycol].dropna()
                stat, p = stats.pearsonr(x, y)
                result = {
                    "test": "Pearson Correlation",
                    "statistic": round(stat, 3),
                    "p_value": round(p, 4)
                }
            except Exception as e:
                result = {"error": str(e)}
    return render_template("correlation.html", result=result)

@app.route("/timeseries", methods=["GET", "POST"])
def timeseries():
    plot_file = None
    if request.method == "POST":
        file = request.files["file"]
        col = request.form.get("column")
        if file:
            df = pd.read_csv(file)
            try:
                fig, ax = plt.subplots()
                ax.plot(df[col])
                ax.set_title(f"Time Series of {col}")
                plot_file = save_plot(fig)
            except Exception as e:
                return render_template("timeseries.html", error=str(e))
    return render_template("timeseries.html", plot_file=plot_file)

if __name__ == "__main__":
    app.run(debug=True)
