import os
from pathlib import Path
from datetime import datetime
import pandas as pd
from flask import (
    Flask, render_template, request, redirect, url_for,
    send_from_directory, flash
)
from werkzeug.utils import secure_filename
import maps2

API_KEY = "AIzaSyDEO6pfzQFbivc_btwwF_LI0K5Yt_H62Ug"
UPLOADS = Path("static/outputs")
UPLOADS.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(16)
app.config["UPLOAD_FOLDER"] = UPLOADS

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/", methods=["POST"])
def upload():
    f = request.files["file"]
    if not f or not f.filename.endswith((".xls", ".xlsx")):
        flash("Please upload a valid Excel file (.xls or .xlsx).", "danger")
        return redirect(url_for("index"))

    stem = secure_filename(f.filename.rsplit(".", 1)[0])
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    job_name = f"{stem}_{ts}"
    job_dir = UPLOADS / job_name
    job_dir.mkdir(parents=True, exist_ok=True)

    xl_path = job_dir / f.filename
    f.save(xl_path)

    maps2.API_KEY = API_KEY
    maps2.run_excel_batch(str(xl_path), out_dir=str(job_dir))

    return redirect(url_for("report", job=job_name))

@app.route("/report/<job>")
def report(job):
    job_dir = UPLOADS / job
    summary_path = job_dir / "summary.csv"
    if not summary_path.exists():
        return f"Summary file not found for job: {job}", 404

    summary = pd.read_csv(summary_path)
    rows = summary.to_dict(orient="records")
    return render_template("report.html", rows=rows, job=job)

@app.route("/outputs/<path:filename>")
def outputs(filename):
    return send_from_directory(UPLOADS, filename, as_attachment=False)

if __name__ == "__main__":
    app.run(debug=True)
