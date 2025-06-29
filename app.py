from flask import Flask, request, render_template
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.stats import ttest_ind, f_oneway, linregress

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PLOT_FOLDER = 'static/plots'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(PLOT_FOLDER, exist_ok=True)

def save_plot(fig, filename):
    path = os.path.join(PLOT_FOLDER, filename)
    fig.savefig(path)
    plt.close(fig)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = {}
    columns = []

    if request.method == 'POST':
        file = request.files['file']
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            df = pd.read_csv(filepath)
            columns = df.columns.tolist()

            method = request.form.get('method')
            col1 = request.form.get('col1')
            col2 = request.form.get('col2')

            try:
                if method == "t_test":
                    stat, p = ttest_ind(df[col1], df[col2])
                    result = {
                        "test": "Two-Sample t-Test",
                        "statistic": round(stat, 4),
                        "p_value": round(p, 4),
                        "decision": "Reject H₀" if p < 0.05 else "Fail to Reject H₀"
                    }

                elif method == "anova":
                    groups = [df[col].dropna() for col in [col1, col2]]
                    stat, p = f_oneway(*groups)
                    result = {
                        "test": "One-way ANOVA",
                        "statistic": round(stat, 4),
                        "p_value": round(p, 4),
                        "decision": "Reject H₀" if p < 0.05 else "Fail to Reject H₀"
                    }

                elif method == "histogram":
                    fig, ax = plt.subplots()
                    df[col1].dropna().hist(bins=20, ax=ax)
                    ax.set_title(f"Histogram of {col1}")
                    save_plot(fig, "histogram.png")
                    result = {"plot": "histogram.png"}

                elif method == "timeseries":
                    fig, ax = plt.subplots()
                    df[col1].dropna().plot(ax=ax)
                    ax.set_title(f"Time Series of {col1}")
                    save_plot(fig, "timeseries.png")
                    result = {"plot": "timeseries.png"}

                elif method == "regression":
                    x = df[col1].dropna()
                    y = df[col2].dropna()
                    common_len = min(len(x), len(y))
                    x, y = x[:common_len], y[:common_len]

                    slope, intercept, r_value, p_value, std_err = linregress(x, y)
                    fig, ax = plt.subplots()
                    ax.scatter(x, y)
                    ax.plot(x, slope * x + intercept, color='red')
                    ax.set_title(f"Regression: {col2} vs {col1}")
                    save_plot(fig, "regression.png")

                    result = {
                        "test": "Simple Linear Regression",
                        "statistic": f"R² = {r_value**2:.4f}, p = {p_value:.4f}",
                        "slope": slope,
                        "intercept": intercept,
                        "plot": "regression.png"
                    }

            except Exception as e:
                result = {"error": str(e)}

    return render_template("index.html", columns=columns, result=result)

if __name__ == '__main__':
    app.run(debug=True)
