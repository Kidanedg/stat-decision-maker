from flask import Flask, render_template, request, send_from_directory
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
import logging
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Max 2MB

# Setup folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET", "POST"])
def index():
    columns = []
    result = None
    uploaded_files = []

    # Show existing files
    uploaded_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".csv")]

    if request.method == "POST":
        files = request.files.getlist("file")
        method = request.form.get("method")
        col1 = request.form.get("col1")
        col2 = request.form.get("col2")

        # Process first valid uploaded file
        df = None
        for file in files:
            if file and file.filename.endswith(".csv"):
                safe_name = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4()}_{safe_name}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_name)
                file.save(filepath)
                logging.info(f"✅ Uploaded: {filepath}")

                try:
                    df = pd.read_csv(filepath)
                    columns = df.columns.tolist()
                    break  # use the first valid CSV
                except Exception as e:
                    result = {"error": f"Error reading CSV: {str(e)}"}
                    return render_template("index.html", columns=[], result=result, uploaded_files=uploaded_files)

        if df is not None and method and col1:
            try:
                if col1 not in df.columns:
                    raise ValueError("Column 1 not found.")

                if method == "t-test" and col2 in df.columns:
                    groups = df[col1].dropna().unique()
                    if len(groups) < 2:
                        raise ValueError("t-test needs 2 groups.")
                    g1 = df[df[col1] == groups[0]][col2].dropna()
                    g2 = df[df[col1] == groups[1]][col2].dropna()
                    t_stat, p_val = stats.ttest_ind(g1, g2)
                    decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                    plot_title = f"t-Test: {col2} by {col1}"

                elif method == "anova" and col2 in df.columns:
                    groups = df[col1].dropna().unique()
                    data = [df[df[col1] == g][col2].dropna() for g in groups]
                    t_stat, p_val = stats.f_oneway(*data)
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
                    plot_title = f"Chi-Square: {col1} vs {col2}"

                elif method == "timeseries":
                    series = df[col1].dropna()
                    plt.figure(figsize=(6, 4))
                    plt.plot(series, marker='o')
                    plt.title(f"Time Series Plot: {col1}")
                    plt.xlabel("Index")
                    plt.ylabel(col1)
                    plot_path = os.path.join(STATIC_FOLDER, "plot.png")
                    plt.savefig(plot_path)
                    plt.close()
                    result = {
                        "test": "Time Series Plot",
                        "plot": "plot.png"
                    }
                    return render_template("index.html", columns=columns, result=result, uploaded_files=uploaded_files)

                else:
                    raise ValueError("Please select valid method and columns.")

                # Create histogram or scatter plot
                plt.figure(figsize=(6, 4))
                if method == "regression":
                    plt.scatter(df[col1], df[col2], alpha=0.7)
                    line = df[col1].sort_values()
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
                result = {"error": str(e)}
        else:
            result = {"error": "Missing method or column selection."}

    return render_template("index.html", columns=columns, result=result, uploaded_files=uploaded_files)


@app.route("/uploads/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/delete/<filename>")
def delete_file(filename):
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        os.remove(path)
        logging.info(f"🗑️ Deleted file: {filename}")
    except Exception as e:
        logging.error(f"Failed to delete {filename}: {str(e)}")
    return render_template("index.html", result=None, columns=[], uploaded_files=os.listdir(UPLOAD_FOLDER))


if __name__ == "__main__":
    app.run(debug=True)
