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
        if file and file.filename.endswith(".csv"):
            print("✅ Received file:", file.filename)

            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            try:
                df = pd.read_csv(filepath)
                columns = df.columns.tolist()
                print("✅ Columns detected:", columns)

                return render_template("index.html", columns=columns, result=result)

            except Exception as e:
                print("❌ Error reading CSV:", str(e))
                result = {"error": f"Error reading CSV: {str(e)}"}

        else:
            print("❌ Invalid file uploaded")
            result = {"error": "Please upload a valid CSV file."}

    return render_template("index.html", columns=columns, result=result)


if __name__ == "__main__":
    app.run(debug=True)
