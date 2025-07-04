from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
import uuid

app = Flask(__name__)
app.secret_key = 'statapp-secret'

# Folders
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
RESULT_FOLDER = 'results'
for folder in [UPLOAD_FOLDER, STATIC_FOLDER, RESULT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Store global result (can replace with session/db)
analysis_result = {}
current_df = None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global current_df
    columns = []
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            flash("❌ Please upload a valid CSV file.")
            return redirect(request.url)

        filename = f"{uuid.uuid4().hex}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        try:
            current_df = pd.read_csv(filepath)
            columns = current_df.columns.tolist()
            flash("✅ File uploaded successfully. Choose a method.")
            return redirect(url_for('methods'))
        except Exception as e:
            flash(f"❌ Error reading file: {e}")
            return redirect(request.url)

    return render_template('upload.html', columns=columns)

@app.route('/manual-entry', methods=['GET', 'POST'])
def manual_entry():
    global current_df
    message = ''
    if request.method == 'POST':
        try:
            raw_text = request.form['data']
            lines = raw_text.strip().split('\n')
            headers = lines[0].split(',')
            data = [line.split(',') for line in lines[1:]]
            current_df = pd.DataFrame(data, columns=headers)
            for col in current_df.columns:
                current_df[col] = pd.to_numeric(current_df[col], errors='ignore')
            flash("✅ Data entry accepted.")
            return redirect(url_for('methods'))
        except Exception as e:
            message = f"❌ Invalid data format: {e}"
    return render_template('manual_entry.html', message=message)

@app.route('/methods', methods=['GET', 'POST'])
def methods():
    global current_df, analysis_result

    if current_df is None:
        flash("⚠️ Please upload or enter data first.")
        return redirect(url_for('upload'))

    columns = current_df.columns.tolist()

    if request.method == 'POST':
        method = request.form.get('method')
        col1 = request.form.get('col1')
        col2 = request.form.get('col2')

        if not method or col1 not in columns or (method != 'timeseries' and col2 not in columns):
            flash("❌ Please select valid method and columns.")
            return redirect(request.url)

        df = current_df.dropna()
        plot_name = f"plot_{uuid.uuid4().hex}.png"
        plot_path = os.path.join(STATIC_FOLDER, plot_name)

        try:
            if method == "t-test":
                groups = df[col1].dropna().unique()
                if len(groups) < 2:
                    raise ValueError("Need 2 groups for t-test.")
                g1 = df[df[col1] == groups[0]][col2]
                g2 = df[df[col1] == groups[1]][col2]
                t_stat, p_val = stats.ttest_ind(g1, g2)
                decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                interp = "Significant difference" if p_val < 0.05 else "No significant difference"
                for g in groups:
                    plt.hist(df[df[col1] == g][col2], alpha=0.5, label=str(g))
                plt.legend()

            elif method == "anova":
                groups = df[col1].dropna().unique()
                data_groups = [df[df[col1] == g][col2] for g in groups]
                t_stat, p_val = stats.f_oneway(*data_groups)
                decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                interp = "Group means differ" if p_val < 0.05 else "Group means similar"
                for g in groups:
                    plt.hist(df[df[col1] == g][col2], alpha=0.5, label=str(g))
                plt.legend()

            elif method == "regression":
                x = df[[col1]]
                y = df[col2]
                model = LinearRegression().fit(x, y)
                t_stat = model.coef_[0]
                p_val = model.score(x, y)
                decision = f"y = {model.intercept_:.2f} + {model.coef_[0]:.2f}x"
                interp = "Good fit" if p_val > 0.5 else "Poor fit"
                plt.scatter(x, y)
                plt.plot(x, model.predict(x), color='red')

            elif method == "correlation":
                x = df[col1]
                y = df[col2]
                t_stat, p_val = stats.pearsonr(x, y)
                decision = "Significant correlation" if p_val < 0.05 else "No correlation"
                interp = f"r = {round(t_stat, 3)}"
                plt.scatter(x, y)

            elif method == "chi-square":
                table = pd.crosstab(df[col1], df[col2])
                t_stat, p_val, _, _ = stats.chi2_contingency(table)
                decision = "Reject H₀" if p_val < 0.05 else "Fail to Reject H₀"
                interp = "Variables are dependent" if p_val < 0.05 else "Variables are independent"
                table.plot(kind='bar', stacked=True)
                plt.xticks(rotation=45)

            elif method == "timeseries":
                series = df[col1]
                t_stat = p_val = None
                decision = "Time Series Plot"
                interp = "Sequential data trend"
                plt.plot(series)

            else:
                raise ValueError("Unknown method.")

            plt.title(f"{method.upper()} of {col2} by {col1}" if col2 else method.upper())
            plt.tight_layout()
            plt.savefig(plot_path)
            plt.close()

            analysis_result = {
                "test": method.upper(),
                "statistic": round(t_stat, 4) if t_stat is not None else "N/A",
                "p_value": round(p_val, 4) if p_val is not None else "N/A",
                "decision": decision,
                "interpretation": interp,
                "plot": plot_name
            }

            return redirect(url_for('results'))

        except Exception as e:
            flash(f"❌ Analysis error: {e}")
            return redirect(request.url)

    return render_template('methods.html', columns=columns)

@app.route('/results')
def results():
    if not analysis_result:
        flash("No analysis result available.")
    return render_template('results.html', result=analysis_result)

@app.route('/summary')
def summary():
    global current_df
    if current_df is not None:
        desc = current_df.describe(include='all').to_html(classes='table table-bordered table-striped')
        return render_template('summary.html', summary_table=desc)
    flash("⚠️ No dataset to summarize.")
    return redirect(url_for('upload'))

@app.route('/download_csv')
def download_csv():
    global current_df
    if current_df is not None:
        file_path = os.path.join(RESULT_FOLDER, "result.csv")
        current_df.to_csv(file_path, index=False)
        return send_file(file_path, as_attachment=True)
    flash("No data to download.")
    return redirect(url_for('results'))

@app.route('/download_pdf')
def download_pdf():
    # Placeholder for real PDF export logic
    flash("PDF download not yet implemented.")
    return redirect(url_for('results'))

@app.route('/download_excel')
def download_excel():
    global current_df
    if current_df is not None:
        file_path = os.path.join(RESULT_FOLDER, "result.xlsx")
        current_df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)
    flash("No data to export.")
    return redirect(url_for('results'))

if __name__ == '__main__':
    app.run(debug=True)
