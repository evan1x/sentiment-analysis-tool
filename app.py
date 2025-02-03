from flask import Flask, request, jsonify, render_template, send_file
import os
from werkzeug.utils import secure_filename
from docx import Document
from PyPDF2 import PdfReader
from sentiment_model import SentimentAnalyzer
import pandas as pd
import json
from datetime import datetime
import io

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'pdf'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

analyzer = SentimentAnalyzer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file):
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    try:
        if filename.endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        elif filename.endswith('.docx'):
            doc = Document(filepath)
            text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif filename.endswith('.pdf'):
            reader = PdfReader(filepath)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
        else:
            raise ValueError('Unsupported file format')
            
        return text.strip()
    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

def create_analysis_csv(result):
    """Convert analysis result to CSV format"""
    # Create DataFrames for different aspects of the analysis
    main_df = pd.DataFrame({
        'Metric': ['Sentiment', 'Polarity', 'Subjectivity', 'Word Count', 'Sentence Count'],
        'Value': [
            result['sentiment'],
            result['polarity'],
            result['subjectivity'],
            result['word_count'],
            result['sentence_count']
        ]
    })
    
    emotions_df = pd.DataFrame({
        'Emotion': list(result['emotions'].keys()),
        'Score': list(result['emotions'].values())
    })
    
    key_phrases_df = pd.DataFrame(result['key_phrases'])
    
    sentences_df = pd.DataFrame([{
        'Text': s['text'],
        'Polarity': s['polarity'],
        'Subjectivity': s['subjectivity']
    } for s in result['sentences']])
    
    # Create a buffer for the CSV file
    output = io.StringIO()
    
    # Write each section to the CSV
    output.write("MAIN METRICS\n")
    main_df.to_csv(output, index=False)
    
    output.write("\nEMOTIONS\n")
    emotions_df.to_csv(output, index=False)
    
    output.write("\nKEY PHRASES\n")
    key_phrases_df.to_csv(output, index=False)
    
    output.write("\nSENTENCE ANALYSIS\n")
    sentences_df.to_csv(output, index=False)
    
    return output.getvalue()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file and allowed_file(file.filename):
                text = extract_text_from_file(file)
            else:
                return jsonify({'error': 'Invalid file format'}), 400
        else:
            data = request.get_json()
            text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        result = analyzer.analyze(text)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/csv', methods=['POST'])
def export_csv():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        csv_content = create_analysis_csv(data)
        
        # Create a buffer for the file
        buffer = io.StringIO()
        buffer.write(csv_content)
        buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            io.BytesIO(buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sentiment_analysis_{timestamp}.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export/pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # TODO: Implement PDF generation using a library like reportlab or WeasyPrint
        return jsonify({'error': 'PDF export not implemented yet'}), 501
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
