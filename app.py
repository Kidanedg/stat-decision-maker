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

        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            try:
                df = pd.read_csv(filepath)
                columns = df.columns.tolist()
                print("✅ Columns detected:", columns)

                if method and col1 in df.columns:
                    plot_path = os.path.join(STATIC_FOLDER, "plot.png")
                    result = {}

                    if method == "t-test" and col2 in df.columns:
                        groups = df[col1].dropna().unique()
                        if len(groups) < 2:
                            raise ValueError("t-test needs 2 groups")
                        group1 = df[df[col1] == groups[0]][col2].dropna()
                        group2 = df[df[col1] == groups[1]][col2].dropna()
                        t_stat, p_val = stats.ttest_ind(group1, group2)
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
                        plot_title = f"Linear Regression: {col2} vs {col1}"

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
                        plot_title = f"Chi-Square Test: {col1} vs {col2}"

                    elif method == "timeseries":
                        series = df[col1].dropna()
                        plt.figure(figsize=(6, 4))
                        plt.plot(series, marker='o')
                        plt.title(f"Time Series Plot: {col1}")
                        plt.xlabel("Index")
                        plt.ylabel(col1)
                        plt.savefig(plot_path)
                        plt.close()
                        result = {
                            "test": "Time Series Plot",
                            "plot": "plot.png"
                        }
                        return render_template("index.html", columns=columns, result=result)

                    else:
                        result = {"error": "Invalid method or columns selected."}
                        return render_template("index.html", columns=columns, result=result)

                    # Plot (except for timeseries)
                    if method in ["t-test", "anova", "regression", "correlation", "chi-square"]:
                        plt.figure(figsize=(6, 4))
                        if method == "regression":
                            plt.scatter(df[col1], df[col2], alpha=0.7)
                            line = df[col1].sort_values()
                            model = LinearRegression().fit(df[[col1]], df[col2])
                            plt.plot(line, model.predict(line.to_frame()), color='red')
                        elif method == "correlation":
                            plt.scatter(df[col1], df[col2], alpha=0.7)
                        else:
                            for group in df[col1].dropna().unique():
                                plt.hist(df[df[col1] == group][col2].dropna(), alpha=0.5, label=str(group))
                            plt.legend()
                        plt.title(plot_title)
                        plt.xlabel(col1)
                        plt.ylabel(col2)
                        plt.savefig(plot_path)
                        plt.close()

                        result = {
                            "test": plot_title,
                            "statistic": round(t_stat, 3),
                            "p_value": round(p_val, 4),
                            "decision": decision,
                            "plot": "plot.png"
                        }

                        # Save CSV of results
                        csv_path = os.path.join(STATIC_FOLDER, "result.csv")
                        pd.DataFrame([{
                            "Test": plot_title,
                            "Statistic": round(t_stat, 3),
                            "p-Value": round(p_val, 4),
                            "Decision": decision
                        }]).to_csv(csv_path, index=False)
                        result["csv"] = "result.csv"

                else:
                    result = {"error": "Missing method or column selection."}

            except Exception as e:
                result = {"error": f"❌ Error reading CSV: {str(e)}"}

        else:
            result = {"error": "❌ Please upload a valid CSV file."}

    return render_template("index.html", columns=columns, result=result)

if __name__ == "__main__":
    app.run(debug=True)
