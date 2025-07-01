from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret-key"

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Global data store
global_df = None
last_result = None


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():
    global global_df
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            try:
                global_df = pd.read_csv(filepath)
                flash("✅ File uploaded and loaded successfully.", "info")
                return redirect(url_for("methods"))
            except Exception as e:
                flash(f"❌ Error reading CSV: {str(e)}", "danger")
        else:
            flash("❌ Please upload a valid CSV file.", "warning")
    return render_template("upload.html")


@app.route("/manual", methods=["GET", "POST"])
def manual_entry():
    global global_df
    if request.method == "POST":
        headers = request.form.getlist("headers")
        cells = request.form.getlist("cell")
        rows = [cells[i:i+len(headers)] for i in range(0, len(cells), len(headers))]
        try:
            global_df = pd.DataFrame(rows, columns=headers)
            flash("✅ Data entered successfully.", "info")
            return redirect(url_for("methods"))
        except Exception as e:
            flash(f"❌ Error creating DataFrame: {str(e)}", "danger")
    return render_template("manual_entry.html", headers=["A", "B"], rows=[["", ""], ["", ""]])


@app.route("/methods", methods=["GET", "POST"])
def methods():
    global global_df, last_result
    columns = global_df.columns.tolist() if isinstance(global_df, pd.DataFrame) else []
    if request.method == "POST":
        method = request.form.get("method")
        col1 = request.form.get("col1")
        col2 = request.form.get("col2")

        try:
            if method == "t-test":
                groups = global_df[col1].dropna().unique()
                group1 = global_df[global_df[col1] == groups[0]][col2].dropna()
                group2 = global_df[global_df[col1] == groups[1]][col2].dropna()
                stat, p = stats.ttest_ind(group1, group2)
                decision = "Reject H₀" if p < 0.05 else "Fail to Reject H₀"
                last_result = {"test": "Two-Sample t-Test", "statistic": round(stat, 3), "p_value": round(p, 4), "decision": decision}

            elif method == "anova":
                groups = global_df[col1].dropna().unique()
                data_groups = [global_df[global_df[col1] == g][col2].dropna() for g in groups]
                stat, p = stats.f_oneway(*data_groups)
                decision = "Reject H₀" if p < 0.05 else "Fail to Reject H₀"
                last_result = {"test": "ANOVA", "statistic": round(stat, 3), "p_value": round(p, 4), "decision": decision}

            elif method == "regression":
                x = global_df[[col1]].dropna()
                y = global_df[col2].dropna()
                x, y = x.loc[y.index], y
                model = LinearRegression().fit(x, y)
                stat = model.coef_[0]
                p = model.score(x, y)
                decision = f"y = {round(model.intercept_, 2)} + {round(stat, 2)}x"
                last_result = {"test": "Linear Regression", "statistic": round(stat, 3), "p_value": round(p, 4), "decision": decision}

            elif method == "correlation":
                x = global_df[col1].dropna()
                y = global_df[col2].dropna()
                x, y = x.loc[y.index], y
                stat, p = stats.pearsonr(x, y)
                decision = "Significant" if p < 0.05 else "Not significant"
                last_result = {"test": "Correlation", "statistic": round(stat, 3), "p_value": round(p, 4), "decision": decision}

            elif method == "chi-square":
                table = pd.crosstab(global_df[col1], global_df[col2])
                stat, p, _, _ = stats.chi2_contingency(table)
                decision = "Reject H₀" if p < 0.05 else "Fail to Reject H₀"
                last_result = {"test": "Chi-Square", "statistic": round(stat, 3), "p_value": round(p, 4), "decision": decision}

            elif method == "timeseries":
                plt.figure()
                global_df[col1].dropna().plot(title=f"Time Series: {col1}")
                plot_path = os.path.join(STATIC_FOLDER, "plot.png")
                plt.savefig(plot_path)
                last_result = {"test": "Time Series Plot", "plot": "plot.png"}

            else:
                last_result = {"error": "Invalid method selected."}
                return redirect(url_for("results"))

            return redirect(url_for("results"))

        except Exception as e:
            last_result = {"error": str(e)}
            return redirect(url_for("results"))

    return render_template("methods.html", columns=columns)


@app.route("/results")
def results():
    return render_template("results.html", result=last_result)


@app.route("/download/pdf")
def download_pdf():
    # Placeholder
    flash("PDF export not yet implemented.", "warning")
    return redirect(url_for("results"))


@app.route("/download/csv")
def download_csv():
    global global_df
    if global_df is not None:
        buf = BytesIO()
        global_df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(buf, mimetype='text/csv', as_attachment=True, download_name="data.csv")
    flash("No data to export.", "danger")
    return redirect(url_for("results"))


@app.route("/download/excel")
def download_excel():
    global global_df
    if global_df is not None:
        buf = BytesIO()
        global_df.to_excel(buf, index=False)
        buf.seek(0)
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name="data.xlsx")
    flash("No data to export.", "danger")
    return redirect(url_for("results"))


if __name__ == "__main__":
    app.run(debug=True)
