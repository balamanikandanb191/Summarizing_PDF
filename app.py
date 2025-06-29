from flask import Flask, request, render_template, redirect, url_for, send_file 
from transformers import pipeline
import pdfplumber
from fpdf import FPDF
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize the summarizer model with an explicit model name
summarizer = pipeline("summarization", model="Falconsai/text_summarization")


@app.route('/', methods=['GET', 'POST'])
def upload_document():
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            return redirect(url_for('summarize_document', filename=file.filename))
    return render_template('upload.html')

def process_summary(filename):
    """Helper function to generate the summary text from the PDF file."""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with pdfplumber.open(file_path) as pdf:
        text = ''.join([page.extract_text() for page in pdf.pages if page.extract_text()])
        summary = summarizer(text, max_length=130, min_length=30, do_sample=False)
        summary_text = summary[0]['summary_text']
    return summary_text

@app.route('/summary/<filename>', methods=['GET'])
def summarize_document(filename):
    summary_text = process_summary(filename)
    return render_template('summary.html', filename=filename, summary=summary_text)

@app.route('/export/<filename>', methods=['GET'])
def export_summary_pdf(filename):
    summary_text = process_summary(filename)
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Summary of Document", ln=True, align='C')
    pdf.multi_cell(0, 10, txt=summary_text)

    export_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{filename}_summary.pdf")
    pdf.output(export_path)
    return send_file(export_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
