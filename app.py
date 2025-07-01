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
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max upload

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    columns = []
    result = None

    if request.method == "POST":
        file = request.files.get("file")
        method = request.form.get("method")
        col1 = request.form.get("col1")
        col2 = request.form.get("col2")
        val1 = request.form.getlist("val1[]")
        val2 = request.form.getlist("val2[]")

        df = None

        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            try:
                df = pd.read_csv(filepath)
            except Exception as e:
                result = {"error": f"❌ Error reading CSV: {str(e)}"}
                return render_template("index.html", columns=[], result=result)

        elif val1 and val2 and any(val1) and any(val2):
            try:
                x = pd.to_numeric(val1, errors='coerce')
                y = pd.to_numeric(val2, errors='coerce')
                df = pd.DataFrame({"Var1": x, "Var2": y}).dropna()
                col1, col2 = "Var1", "Var2"
            except Exception as e:
                result = {"error": f"❌ Error processing manual entry: {str(e)}"}
                return render_template("index.html", columns=[], result=result)
        else:
            result = {"error": "❌ Please upload a valid CSV or enter data manually."}
            return render_template("index.html", columns=[], result=result)

        columns = df.columns.tolist()

        if method and col1 in df.columns:
            try:
                if method == "t-test" and col2 in df.columns:
                    groups = df[col1].dropna().unique()
                    if len(groups) < 2:
                        raise ValueError("Need at least 2 groups for t-test")
                    g1 = df[df[col1] == groups[0]][col2].dropna()
                    g2 = df[df[col1] == groups[1]][col2].dropna()
                    t_stat, p_val = stats.ttest_ind(g1, g2)
                    decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                    plot_title = f"t-Test: {col2} by {col1}"

                elif method == "anova" and col2 in df.columns:
                    groups = df[col1].dropna().unique()
                    data_groups = [df[df[col1] == g][col2].dropna() for g in groups]
                    t_stat, p_val = stats.f_oneway(*data_groups)
                    decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                    plot_title = f"ANOVA: {col2} by {col1}"

                elif method == "regression" and col2 in df.columns:
                    x = df[[col1]].dropna()
                    y = df[col2].dropna()
                    x, y = x.loc[y.index], y
                    model = LinearRegression().fit(x, y)
                    t_stat = model.coef_[0]
                    p_val = model.score(x, y)
                    decision = f"y = {round(model.intercept_, 2)} + {round(t_stat, 2)}x"
                    plot_title = f"Regression: {col2} vs {col1}"

                elif method == "correlation" and col2 in df.columns:
                    x = df[col1].dropna()
                    y = df[col2].dropna()
                    x, y = x.loc[y.index], y
                    t_stat, p_val = stats.pearsonr(x, y)
                    decision = "Significant correlation" if p_val < 0.05 else "Not significant"
                    plot_title = f"Correlation: {col1} vs {col2}"

                elif method == "chi-square" and col2 in df.columns:
                    contingency = pd.crosstab(df[col1], df[col2])
                    t_stat, p_val, _, _ = stats.chi2_contingency(contingency)
                    decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                    plot_title = f"Chi-Square: {col1} vs {col2}"

                elif method == "timeseries":
                    series = df[col1].dropna()
                    plt.figure(figsize=(6, 4))
                    plt.plot(series, marker='o')
                    plt.title(f"Time Series: {col1}")
                    plt.xlabel("Index")
                    plt.ylabel(col1)
                    plot_path = os.path.join(STATIC_FOLDER, "plot.png")
                    plt.savefig(plot_path)
                    plt.close()
                    result = {"test": "Time Series", "plot": "plot.png"}
                    return render_template("index.html", columns=columns, result=result)

                else:
                    result = {"error": "❌ Invalid method or column selection."}
                    return render_template("index.html", columns=columns, result=result)

                # Plot (all but time series)
                plt.figure(figsize=(6, 4))
                if method == "regression":
                    plt.scatter(df[col1], df[col2], alpha=0.7)
                    line = df[col1].sort_values()
                    pred = LinearRegression().fit(df[[col1]], df[col2]).predict(line.to_frame())
                    plt.plot(line, pred, color="red")
                elif method == "correlation":
                    plt.scatter(df[col1], df[col2], alpha=0.7)
                else:
                    for group in df[col1].dropna().unique():
                        plt.hist(df[df[col1] == group][col2].dropna(), alpha=0.5, label=str(group))
                    plt.legend()

                plt.title(plot_title)
                plt.xlabel(col1)
                plt.ylabel(col2)
                plot_path = os.path.join(STATIC_FOLDER, "plot.png")
                plt.savefig(plot_path)
                plt.close()

                result = {
                    "test": plot_title,
                    "statistic": round(t_stat, 3),
                    "p_value": round(p_val, 4),
                    "decision": decision,
                    "plot": "plot.png"
                }

            except Exception as e:
                result = {"error": f"❌ Analysis error: {str(e)}"}
        else:
            result = {"error": "❌ Please select valid method and columns."}

    return render_template("index.html", columns=columns, result=result)

if __name__ == "__main__":
    app.run(debug=True)
