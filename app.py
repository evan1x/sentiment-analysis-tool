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
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from io import BytesIO
import matplotlib.pyplot as plt
import base64

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

def create_emotion_chart_image(emotions):
    """Create a pie chart for emotions and return it as a BytesIO object."""
    plt.figure(figsize=(6, 6))
    plt.pie(
        list(emotions.values()),
        labels=list(emotions.keys()),
        colors=['#dc3545', '#28a745', '#ffc107', '#6c757d'],
        autopct='%1.1f%%'
    )
    plt.title('Emotion Distribution')
    
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    plt.close()
    img_buffer.seek(0)
    return img_buffer

def create_analysis_pdf(result):
    """Generate a PDF report of the sentiment analysis."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Custom style for metrics
    metric_style = ParagraphStyle(
        'MetricStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )
    
    # Story (content elements)
    story = []
    
    # Title
    story.append(Paragraph('Sentiment Analysis Report', title_style))
    story.append(Spacer(1, 24))
    
    # Overall Metrics
    story.append(Paragraph('Overall Metrics', heading_style))
    story.append(Spacer(1, 12))
    
    metrics_data = [
        ['Metric', 'Value'],
        ['Sentiment', result['sentiment'].capitalize()],
        ['Polarity', f"{result['polarity']:.2f}"],
        ['Subjectivity', f"{result['subjectivity']:.2f}"],
        ['Word Count', str(result['word_count'])],
        ['Sentence Count', str(result['sentence_count'])]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 24))
    
    # Emotion Distribution Chart
    if result.get('emotions'):
        story.append(Paragraph('Emotion Distribution', heading_style))
        story.append(Spacer(1, 12))
        
        img_buffer = create_emotion_chart_image(result['emotions'])
        img = Image(img_buffer, width=4*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 24))
    
    # Key Phrases
    if result.get('key_phrases'):
        story.append(Paragraph('Key Phrases', heading_style))
        story.append(Spacer(1, 12))
        
        phrases_data = [['Phrase', 'Count']]
        for phrase in result['key_phrases']:
            phrases_data.append([phrase['phrase'], str(phrase['count'])])
        
        phrases_table = Table(phrases_data, colWidths=[4*inch, 1*inch])
        phrases_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(phrases_table)
        story.append(Spacer(1, 24))
    
    # Sentence Analysis
    if result.get('sentences'):
        story.append(Paragraph('Sentence Analysis', heading_style))
        story.append(Spacer(1, 12))
        
        for sentence in result['sentences']:
            # Sentence text
            story.append(Paragraph(f"<b>Text:</b> {sentence['text']}", normal_style))
            story.append(Spacer(1, 6))
            
            # Sentence metrics
            metrics = [
                f"Polarity: {sentence['polarity']:.2f}",
                f"Subjectivity: {sentence['subjectivity']:.2f}"
            ]
            story.append(Paragraph(", ".join(metrics), metric_style))
            story.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

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
        print("PDF export started")
        data = request.get_json()
        print("Received data:", data)
        
        if not data:
            print("No data provided")
            return jsonify({'error': 'No data provided'}), 400
            
        print("Creating PDF buffer")
        pdf_buffer = create_analysis_pdf(data)
        
        print("PDF created successfully")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'sentiment_analysis_{timestamp}.pdf'
        )
        
    except Exception as e:
        print("Error in PDF export:", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
