from flask import Flask, render_template, request, send_from_directory
import os
import uuid
from detect_changes import detect_forgery
from detect_forgery_single_image import detect_invoice_field_anomalies
from deep_metadata_utils import extract_deep_metadata  # Updated import

app = Flask(__name__)
UPLOAD_FOLDER = 'static/results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/forgery-detection', methods=['GET', 'POST'])
def forgery_detection():
    result = {}
    if request.method == 'POST':
        original = request.files['original']
        edited = request.files['edited']
        if original and edited:
            orig_path = os.path.join(UPLOAD_FOLDER, f"original_{uuid.uuid4().hex}.png")
            edit_path = os.path.join(UPLOAD_FOLDER, f"edited_{uuid.uuid4().hex}.png")
            original.save(orig_path)
            edited.save(edit_path)
            score = detect_forgery(orig_path, edit_path, UPLOAD_FOLDER)
            result['ssim_score'] = f"{score:.4f}"
            result['diff_map'] = "ssim_diff_map.png"
            result['output_image'] = "differences_detected.png"
    return render_template('forgery.html', result=result)

@app.route('/tampering-detection', methods=['GET', 'POST'])
def tampering_detection():
    result = {}
    if request.method == 'POST':
        invoice = request.files['invoice']
        if invoice:
            input_path = os.path.join(UPLOAD_FOLDER, f"invoice_{uuid.uuid4().hex}.png")
            invoice.save(input_path)
            output_path = os.path.splitext(input_path)[0] + "_analyzed_fields.png"
            detect_invoice_field_anomalies(input_path, output_path)
            result['analyzed_invoice'] = os.path.basename(output_path)
            result['metadata'] = extract_deep_metadata(input_path)
    return render_template('tampering.html', result=result)

@app.route('/static/results/<filename>')
def send_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
