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
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
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
        'Metric': ['Sentiment', 'Polarity'],
        'Value': [
            result.get('sentiment', 'N/A'),
            result.get('polarity', 0)
        ]
    })
    
    # Handle emotions data with metadata
    emotions = result.get('emotions', {})
    emotions_df = pd.DataFrame([
        {
            'Emotion': emotion,
            'Score': data['score'],
            'Description': data['description']
        }
        for emotion, data in emotions.items()
    ]) if emotions else pd.DataFrame(columns=['Emotion', 'Score', 'Description'])
    
    # Sort emotions by score
    if not emotions_df.empty:
        emotions_df = emotions_df.sort_values('Score', ascending=False)
    
    # Handle key phrases data
    key_phrases = result.get('key_phrases', [])
    key_phrases_df = pd.DataFrame({'Phrase': key_phrases}) if key_phrases else pd.DataFrame(columns=['Phrase'])
    
    # Handle sentence analysis data
    sentence_analysis = result.get('sentence_analysis', [])
    if sentence_analysis:
        sentences_df = pd.DataFrame([{
            'Text': s.get('text', ''),
            'Sentiment': s.get('sentiment', ''),
            'Confidence': s.get('confidence', 0)
        } for s in sentence_analysis])
    else:
        sentences_df = pd.DataFrame(columns=['Text', 'Sentiment', 'Confidence'])
    
    # Create a buffer for the CSV file
    output = io.StringIO()
    
    # Write each section to the CSV with headers
    output.write("MAIN METRICS\n")
    main_df.to_csv(output, index=False)
    output.write("\n\nEMOTIONS\n")
    emotions_df.to_csv(output, index=False)
    output.write("\n\nKEY PHRASES\n")
    key_phrases_df.to_csv(output, index=False)
    output.write("\n\nSENTENCE ANALYSIS\n")
    sentences_df.to_csv(output, index=False)
    
    return output.getvalue()

def create_emotion_chart_image(emotions):
    """Create a pie chart for emotions and return it as a BytesIO object."""
    plt.figure(figsize=(6, 6))
    plt.pie(
        [data['score'] for data in emotions.values()],
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
    """Generate a PDF report of the sentiment analysis"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    # Prepare the story (content)
    story = []
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph("Sentiment Analysis Report", title_style))
    story.append(Spacer(1, 12))
    
    # Main Metrics
    story.append(Paragraph("Overall Sentiment", heading_style))
    story.append(Spacer(1, 6))
    
    data = [
        ["Metric", "Value"],
        ["Sentiment", result.get('sentiment', 'N/A')],
        ["Polarity", f"{result.get('polarity', 0):.2f}"]
    ]
    
    t = Table(data, colWidths=[200, 200])
    t.setStyle(TableStyle([
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
    story.append(t)
    story.append(Spacer(1, 20))
    
    # Emotions
    story.append(Paragraph("Emotion Analysis", heading_style))
    story.append(Spacer(1, 6))
    
    emotions = result.get('emotions', {})
    if emotions:
        emotion_data = [["Emotion", "Score", "Description"]]
        for emotion, data in sorted(emotions.items(), key=lambda x: x[1]['score'], reverse=True):
            emotion_data.append([
                emotion,
                f"{data['score']*100:.1f}%",
                data['description']
            ])
        
        t = Table(emotion_data, colWidths=[100, 100, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (-1, -1), True)
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No emotion data available", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Key Phrases
    if result.get('key_phrases'):
        story.append(Paragraph("Key Phrases", heading_style))
        story.append(Spacer(1, 6))
        phrases = [Paragraph(f"• {phrase}", normal_style) for phrase in result['key_phrases']]
        for phrase in phrases:
            story.append(phrase)
        story.append(Spacer(1, 20))
    
    # Sentence Analysis
    if result.get('sentence_analysis'):
        story.append(Paragraph("Sentence Analysis", heading_style))
        story.append(Spacer(1, 6))
        
        for sentence in result['sentence_analysis']:
            p = Paragraph(
                f"<b>{sentence['text']}</b><br/>"
                f"Sentiment: {sentence['sentiment']}, "
                f"Confidence: {sentence['confidence']*100:.1f}%",
                normal_style
            )
            story.append(p)
            story.append(Spacer(1, 12))
    
    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        print("Starting text analysis")
        if 'file' in request.files:
            print("Processing uploaded file")
            file = request.files['file']
            if file and allowed_file(file.filename):
                text = extract_text_from_file(file)
                print(f"Extracted text from file: {file.filename}")
            else:
                print("Invalid file format")
                return jsonify({'error': 'Invalid file format'}), 400
        else:
            print("Processing JSON data")
            data = request.get_json()
            if data is None:
                print("No JSON data received")
                return jsonify({'error': 'No data provided'}), 400
            text = data.get('text', '').strip()
        
        if not text:
            print("No text provided")
            return jsonify({'error': 'No text provided'}), 400
            
        print(f"Analyzing text (length: {len(text)})")
        result = analyzer.analyze(text)
        print("Analysis completed successfully")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'An error occurred during analysis: {str(e)}'}), 500

@app.route('/export/csv', methods=['POST'])
def export_csv():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        csv_content = create_analysis_csv(data)
        
        # Create a binary buffer for the file
        buffer = io.BytesIO()
        buffer.write(csv_content.encode('utf-8'))
        buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'sentiment_analysis_{timestamp}.csv'
        )
        
    except Exception as e:
        print(f"CSV Export Error: {str(e)}")
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
