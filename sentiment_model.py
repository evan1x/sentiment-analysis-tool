import nltk
from textblob import TextBlob
import re
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from collections import Counter
from string import punctuation

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
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger')
        
        self.stopwords = set(stopwords.words('english'))
        self.punctuation = set(punctuation)

    def preprocess_text(self, text):
        """Clean and preprocess the input text."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters and digits
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def get_key_phrases(self, text, num_phrases=5):
        """Extract key phrases from the text."""
        # Tokenize and tag parts of speech
        tokens = word_tokenize(text)
        tagged = pos_tag(tokens)
        
        # Extract noun phrases (simplified)
        phrases = []
        current_phrase = []
        
        for word, tag in tagged:
            if tag.startswith(('JJ', 'NN')):  # Adjectives and nouns
                current_phrase.append(word)
            elif current_phrase:
                phrases.append(' '.join(current_phrase))
                current_phrase = []
        
        if current_phrase:
            phrases.append(' '.join(current_phrase))
        
        # Count phrase frequencies
        phrase_counter = Counter(phrases)
        
        # Return most common phrases
        return [{'phrase': phrase, 'count': count} 
                for phrase, count in phrase_counter.most_common(num_phrases)]

    def get_emotion_scores(self, polarity):
        """Convert polarity score into emotion intensities."""
        emotions = {
            'joy': 0,
            'sadness': 0,
            'anger': 0,
            'neutral': 0
        }
        
        if polarity > 0.5:
            emotions['joy'] = polarity
        elif polarity < -0.5:
            emotions['anger'] = abs(polarity)
        elif polarity < 0:
            emotions['sadness'] = abs(polarity)
        else:
            emotions['neutral'] = 1 - abs(polarity)
            
        return emotions

    def analyze(self, text):
        """Analyze the sentiment of the given text."""
        if not text:
            return {
                'error': 'No text provided'
            }
        
        try:
            # Preprocess the text
            cleaned_text = self.preprocess_text(text)
            
            # Create TextBlob object
            blob = TextBlob(cleaned_text)
            
            # Get the sentiment polarity (-1 to 1)
            polarity = blob.sentiment.polarity
            
            # Get the subjectivity (0 to 1)
            subjectivity = blob.sentiment.subjectivity
            
            # Determine sentiment label
            if polarity > 0.1:
                sentiment = 'positive'
            elif polarity < -0.1:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            # Get emotion scores
            emotions = self.get_emotion_scores(polarity)
            
            # Get key phrases
            key_phrases = self.get_key_phrases(cleaned_text)
            
            # Get sentence-level analysis
            sentences = []
            for sentence in blob.sentences:
                sentences.append({
                    'text': str(sentence),
                    'polarity': sentence.sentiment.polarity,
                    'subjectivity': sentence.sentiment.subjectivity
                })
            
            return {
                'text': text,
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'emotions': emotions,
                'key_phrases': key_phrases,
                'sentences': sentences,
                'word_count': len(cleaned_text.split())
            }
            
        except Exception as e:
            return {
                'error': f'Analysis failed: {str(e)}'
            }
