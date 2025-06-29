from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    columns = []
    result = None

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".csv"):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            try:
                df = pd.read_csv(filepath)
                columns = df.columns.tolist()

                # Only render form with dropdowns, no analysis yet
                return render_template("index.html", columns=columns, result=None)

            except Exception as e:
                result = {"error": f"Error reading file: {str(e)}"}
                return render_template("index.html", columns=[], result=result)

        else:
            result = {"error": "Please upload a valid .csv file"}
            return render_template("index.html", columns=[], result=result)

    return render_template("index.html", columns=[], result=None)

if __name__ == "__main__":
    app.run(debug=True)
