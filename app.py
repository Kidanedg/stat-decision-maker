from flask import Flask, render_template, request
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy import stats

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max upload

# Ensure required folders exist
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

                # Run analysis if all inputs provided
                if method == "t-test" and col1 and col2 and col1 in df.columns and col2 in df.columns:
                    try:
                        group_values = df[col1].dropna().unique()
                        if len(group_values) != 2:
                            raise ValueError("Column '{}' must have exactly 2 groups.".format(col1))

                        group1 = df[df[col1] == group_values[0]][col2].dropna()
                        group2 = df[df[col1] == group_values[1]][col2].dropna()

                        t_stat, p_val = stats.ttest_ind(group1, group2)
                        decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"

                        # Generate and save plot
                        plt.figure(figsize=(6, 4))
                        plt.hist(group1, alpha=0.6, label=str(group_values[0]))
                        plt.hist(group2, alpha=0.6, label=str(group_values[1]))
                        plt.title("Histogram of {}".format(col2))
                        plt.xlabel(col2)
                        plt.ylabel("Frequency")
                        plt.legend()
                        plot_path = os.path.join(STATIC_FOLDER, "plot.png")
                        plt.savefig(plot_path)
                        plt.close()

                        result = {
                            "test": "Two-Sample t-Test",
                            "statistic": round(t_stat, 3),
                            "p_value": round(p_val, 4),
                            "decision": decision,
                            "plot": "plot.png"
                        }

                    except Exception as e:
                        result = {"error": f"Analysis failed: {str(e)}"}

                else:
                    result = {"error": "Please select valid method and columns."}

                return render_template("index.html", columns=columns, result=result)

            except Exception as e:
                result = {"error": f"Error reading CSV: {str(e)}"}

        else:
            result = {"error": "Please upload a valid CSV file."}

    return render_template("index.html", columns=[], result=result)

if __name__ == "__main__":
    app.run(debug=True)
