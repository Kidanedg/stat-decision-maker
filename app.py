from flask import Flask, render_template, request, session, redirect, url_for, send_file
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import werkzeug.utils

app = Flask(__name__)
app.secret_key = 'secret'

UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def safe_save_plot(df, plot_title):
    plt.figure()
    df.plot(kind='line' if 'Series' in plot_title else 'hist', legend=True)
    plt.title(plot_title)
    fn = os.path.join(STATIC_FOLDER, "plot.png")
    plt.savefig(fn); plt.close()
    return "plot.png"

def run_test(df, method, col1, col2):
    res = {'test': method, 'plot': None}
    if method == 'wilcoxon':
        if col1 in df.columns and col2 in df.columns:
            stat, p = stats.wilcoxon(df[col1].dropna(), df[col2].dropna())
            res.update(statistic=round(stat,3), p_value=round(p,4),
                       decision='Reject H₀' if p < .05 else 'Fail to Reject H₀',
                       interpretation=f"Wilcoxon: stat={stat:.3f}, p={p:.4f}")
    elif method == 'kruskal':
        groups = df[col1].dropna().unique()
        data = [df[df[col1]==g][col2].dropna() for g in groups]
        stat, p = stats.kruskal(*data)
        res.update(statistic=round(stat,3), p_value=round(p,4),
                   decision='Reject H₀' if p < .05 else 'Fail to Reject H₀',
                   interpretation=f"Kruskal–Wallis: H={stat:.3f}, p={p:.4f}")
    # Add prior methods...
    return res

@app.route("/", methods=["GET","POST"])
def home():
    if request.method=="POST":
        data = request.form.get('grid')
        df = pd.read_json(data, orient='split')
        session['data'] = df.to_json()
        session['columns'] = df.columns.tolist()
        return redirect(url_for('methods'))
    return render_template("home.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method=="POST":
        f = request.files.get('file')
        if f and f.filename.endswith('.csv'):
            fn = werkzeug.utils.secure_filename(f.filename)
            path = os.path.join(UPLOAD_FOLDER, fn)
            f.save(path)
            df = pd.read_csv(path)
            session['data'] = df.to_json()
            session['columns'] = df.columns.tolist()
            return redirect(url_for('methods'))
    return render_template("upload.html")

@app.route("/methods", methods=["GET","POST"])
def methods():
    df = pd.read_json(session['data'])
    cols = session['columns']
    extra = ['wilcoxon','kruskal']
    if request.method=="POST":
        m = request.form['method']; c1=request.form['col1']; c2=request.form['col2']
        result = run_test(df, m, c1, c2)
        session['result'] = result
        return redirect(url_for('results'))
    return render_template("methods.html", columns=cols, methods=extra+['t-test','anova','regression','correlation','chi-square','timeseries'])

@app.route("/results")
def results():
    r = session.get('result')
    return render_template("results.html", result=r)

@app.route("/download/pdf")
def download_pdf():
    r = session.get('result')
    if not r: return "No result"
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 700, f"Test: {r['test']}")
    if r.get('statistic') is not None:
        c.drawString(100, 680, f"Stat: {r['statistic']}, p={r['p_value']}")
    c.drawString(100, 660, f"Decision: {r['decision']}")
    c.drawString(100, 640, r.get('interpretation',''))
    c.drawImage(os.path.join(STATIC_FOLDER,r['plot']), 100, 400, width=400, height=200)
    c.save()
    buf.seek(0)
    return send_file(buf, download_name="result.pdf", as_attachment=True)

if __name__=="__main__":
    app.run(debug=True)
