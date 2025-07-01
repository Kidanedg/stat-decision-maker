from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB upload limit

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

            # Initialize result
            result = None

            # If method and columns are selected, perform analysis
            if method == "t-test" and col1 and col2 and col1 in df.columns and col2 in df.columns:
                from scipy import stats
                try:
                    group1 = df[df[col1] == df[col1].unique()[0]][col2]
                    group2 = df[df[col1] == df[col1].unique()[1]][col2]
                    t_stat, p_val = stats.ttest_ind(group1, group2)
                    result = {
                        "method": "Two-Sample t-Test",
                        "t_stat": round(t_stat, 3),
                        "p_val": round(p_val, 4)
                    }
                except Exception as e:
                    result = {"error": f"t-Test failed: {str(e)}"}

            return render_template("index.html", columns=columns, result=result)

        except Exception as e:
            result = {"error": f"Error reading CSV: {str(e)}"}

    return render_template("index.html", columns=[], result=result)



if __name__ == "__main__":
    app.run(debug=True)
