from flask import Flask, render_template, request, jsonify
from sentiment_model import SentimentAnalyzer
import logging

app = Flask(__name__)
sentiment_analyzer = SentimentAnalyzer()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Log the incoming request
        logger.info(f"Analyzing text (length: {len(text)})")
        
        # Perform analysis
        result = sentiment_analyzer.analyze(text)
        
        if 'error' in result:
            logger.error(f"Analysis failed: {result['error']}")
            return jsonify(result), 500
        
        # Log successful analysis
        logger.info(f"Analysis complete: {result['sentiment']} (polarity: {result['polarity']:.2f})")
        
        return jsonify(result)
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True)
