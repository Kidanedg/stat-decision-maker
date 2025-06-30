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

                # ✅ STEP 4: Re-render the page with columns loaded
                return render_template("index.html", columns=columns, result=result)

            except Exception as e:
                result = {"error": f"Error reading file: {str(e)}"}

        else:
            result = {"error": "Please upload a valid CSV file."}

    # Renders the default form when visiting the page for the first time
    return render_template("index.html", columns=columns, result=result)


if __name__ == "__main__":
    app.run(debug=True)
