import nltk
from textblob import TextBlob
import re
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from collections import Counter
from string import punctuation
from rake_nltk import Rake
import spacy
from transformers import pipeline
import torch

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
        
        # Initialize RAKE for keyword extraction
        self.rake = Rake()
        
        # Load spaCy model for entity recognition and dependency parsing
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            spacy.cli.download('en_core_web_sm')
            self.nlp = spacy.load('en_core_web_sm')
        
        # Initialize transformer model for sentiment analysis
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=0 if torch.cuda.is_available() else -1
        )

    def preprocess_text(self, text):
        """Clean and preprocess the input text."""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s.!?]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def get_key_phrases(self, text, num_phrases=5):
        """Extract key phrases using multiple methods."""
        # Use RAKE for keyword extraction
        self.rake.extract_keywords_from_text(text)
        rake_phrases = self.rake.get_ranked_phrases_with_scores()
        
        # Use spaCy for noun phrase extraction
        doc = self.nlp(text)
        noun_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        # Use NLTK for additional phrase extraction
        tokens = word_tokenize(text)
        tagged = pos_tag(tokens)
        
        # Extract phrases based on patterns
        phrases = []
        current_phrase = []
        
        for word, tag in tagged:
            if tag.startswith(('JJ', 'NN', 'VB')):  # Include verbs for action phrases
                current_phrase.append(word)
            elif current_phrase:
                phrases.append(' '.join(current_phrase))
                current_phrase = []
        
        if current_phrase:
            phrases.append(' '.join(current_phrase))
        
        # Combine all phrases and count frequencies
        all_phrases = (
            [phrase for _, phrase in rake_phrases] +
            noun_phrases +
            phrases
        )
        
        phrase_counter = Counter(all_phrases)
        
        # Return most common meaningful phrases
        return [{'phrase': phrase, 'count': count} 
                for phrase, count in phrase_counter.most_common(num_phrases)
                if len(phrase.split()) > 1 and phrase.strip()]

    def get_emotion_scores(self, text):
        """Enhanced emotion detection using transformer models."""
        # Use the transformer model for more accurate sentiment
        result = self.sentiment_pipeline(text)[0]
        sentiment_score = result['score'] if result['label'] == 'POSITIVE' else -result['score']
        
        # Calculate emotion intensities
        emotions = {
            'joy': max(0, sentiment_score) if sentiment_score > 0 else 0,
            'sadness': max(0, -sentiment_score) if sentiment_score < 0 else 0,
            'anger': max(0, -sentiment_score * 0.5) if sentiment_score < -0.5 else 0,
            'neutral': 1 - abs(sentiment_score) if abs(sentiment_score) < 0.3 else 0
        }
        
        # Normalize emotions to sum to 1
        total = sum(emotions.values())
        if total > 0:
            emotions = {k: v/total for k, v in emotions.items()}
        
        return emotions

    def analyze_sentence_structure(self, text):
        """Analyze sentence structure using spaCy."""
        doc = self.nlp(text)
        
        sentence_analysis = []
        for sent in doc.sents:
            # Get main subject and object
            subject = None
            obj = None
            action = None
            
            for token in sent:
                if "subj" in token.dep_:
                    subject = token.text
                elif "obj" in token.dep_:
                    obj = token.text
                elif token.pos_ == "VERB":
                    action = token.text
            
            # Get named entities
            entities = [(ent.text, ent.label_) for ent in sent.ents]
            
            sentence_analysis.append({
                'text': sent.text,
                'subject': subject,
                'object': obj,
                'action': action,
                'entities': entities,
                'length': len(sent),
                'complexity': len([token for token in sent if token.pos_ in ['NOUN', 'VERB', 'ADJ']])
            })
        
        return sentence_analysis

    def analyze(self, text):
        """Analyze the sentiment of the given text."""
        if not text:
            return {
                'error': 'No text provided'
            }
        
        try:
            # Preprocess the text
            cleaned_text = self.preprocess_text(text)
            
            # Create TextBlob object for basic sentiment
            blob = TextBlob(cleaned_text)
            
            # Get the sentiment polarity (-1 to 1)
            polarity = blob.sentiment.polarity
            
            # Get the subjectivity (0 to 1)
            subjectivity = blob.sentiment.subjectivity
            
            # Get enhanced emotion scores
            emotions = self.get_emotion_scores(cleaned_text)
            
            # Determine sentiment label
            sentiment = 'positive' if polarity > 0.1 else 'negative' if polarity < -0.1 else 'neutral'
            
            # Get key phrases with enhanced extraction
            key_phrases = self.get_key_phrases(cleaned_text)
            
            # Get detailed sentence analysis
            sentence_analysis = self.analyze_sentence_structure(cleaned_text)
            
            # Get sentence-level sentiment
            sentences = []
            for sent in blob.sentences:
                sent_text = str(sent)
                sent_emotions = self.get_emotion_scores(sent_text)
                
                sentences.append({
                    'text': sent_text,
                    'polarity': sent.sentiment.polarity,
                    'subjectivity': sent.sentiment.subjectivity,
                    'emotions': sent_emotions,
                    'structure': next((s for s in sentence_analysis if s['text'] == sent_text), None)
                })
            
            return {
                'text': text,
                'sentiment': sentiment,
                'polarity': polarity,
                'subjectivity': subjectivity,
                'emotions': emotions,
                'key_phrases': key_phrases,
                'sentences': sentences,
                'word_count': len(cleaned_text.split()),
                'sentence_count': len(sentences)
            }
            
        except Exception as e:
            return {
                'error': f'Analysis error: {str(e)}'
            }
