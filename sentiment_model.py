import nltk
from textblob import TextBlob
import re

class SentimentAnalyzer:
    def __init__(self):
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stopwords = set(nltk.corpus.stopwords.words('english'))

    def preprocess_text(self, text):
        """Clean and preprocess the input text."""
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text

    def analyze(self, text):
        """Analyze the sentiment of the given text."""
        # Preprocess the text
        cleaned_text = self.preprocess_text(text)
        
        # Create TextBlob object
        blob = TextBlob(cleaned_text)
        
        # Get the sentiment polarity (-1 to 1)
        polarity = blob.sentiment.polarity
        
        # Get the subjectivity (0 to 1)
        subjectivity = blob.sentiment.subjectivity
        
        # Determine sentiment label
        if polarity > 0:
            sentiment = 'positive'
        elif polarity < 0:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'text': text,
            'sentiment': sentiment,
            'polarity': polarity,
            'subjectivity': subjectivity
        }
