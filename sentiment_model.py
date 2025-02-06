import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import spacy
from nltk.tokenize import sent_tokenize
import numpy as np
from textblob import TextBlob
import nltk
from string import punctuation

class SentimentAnalyzer:
    def __init__(self):
        # Initialize NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        # Initialize device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Device set to use {self.device}")
        
        # Load models for different analysis tasks
        print("Loading sentiment analysis models...")
        
        try:
            # General sentiment analysis model
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=self.device
            )
            
            # Comprehensive emotion lexicon based on Plutchik's wheel and NRC emotion lexicon
            self.emotion_words = {
                'joy': ['happy', 'joyful', 'delighted', 'pleased', 'glad', 'cheerful', 'content', 'satisfied', 'elated', 'jubilant',
                       'excited', 'thrilled', 'overjoyed', 'blissful', 'ecstatic', 'merry', 'jolly', 'lively', 'enthusiastic'],
                
                'sadness': ['sad', 'unhappy', 'depressed', 'gloomy', 'miserable', 'heartbroken', 'downcast', 'grieving', 'sorrowful',
                           'melancholy', 'despair', 'dejected', 'hopeless', 'disappointed', 'regretful', 'lonely', 'hurt'],
                
                'anger': ['angry', 'furious', 'irritated', 'annoyed', 'enraged', 'hostile', 'mad', 'outraged', 'bitter', 'hate',
                         'resentful', 'frustrated', 'agitated', 'irate', 'livid', 'indignant', 'offended', 'provoked'],
                
                'fear': ['afraid', 'scared', 'fearful', 'terrified', 'anxious', 'worried', 'nervous', 'panicked', 'frightened',
                        'threatened', 'alarmed', 'horrified', 'paranoid', 'insecure', 'uneasy', 'apprehensive', 'dread'],
                
                'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'startled', 'stunned', 'bewildered', 'dumbfounded',
                            'awestruck', 'wonder', 'unexpected', 'incredible', 'unbelievable', 'remarkable', 'extraordinary'],
                
                'disgust': ['disgusted', 'repulsed', 'revolted', 'sickened', 'appalled', 'horrified', 'loathing', 'hateful',
                           'repugnant', 'offensive', 'distasteful', 'nauseated', 'repelled', 'averse', 'detestable'],
                
                'trust': ['trust', 'believe', 'confident', 'faithful', 'reliable', 'dependable', 'honest', 'sincere', 'loyal',
                         'trustworthy', 'devoted', 'dedicated', 'committed', 'assured', 'certain', 'secure'],
                
                'anticipation': ['expect', 'anticipate', 'await', 'eager', 'hopeful', 'looking forward', 'prepared', 'ready',
                                'watchful', 'vigilant', 'alert', 'excited', 'enthusiastic', 'optimistic', 'keen'],
                
                'love': ['love', 'adore', 'cherish', 'affection', 'fond', 'caring', 'romantic', 'passionate', 'tender',
                        'devoted', 'warmth', 'intimate', 'attachment', 'desire', 'yearning', 'compassion'],
                
                'admiration': ['admire', 'respect', 'appreciate', 'value', 'esteem', 'regard', 'praise', 'honor', 'revere',
                              'look up to', 'idolize', 'impressed', 'awed', 'inspired', 'marvel'],
                
                'optimism': ['optimistic', 'hopeful', 'positive', 'confident', 'upbeat', 'encouraged', 'promising', 'bright',
                            'assured', 'cheerful', 'enthusiastic', 'motivated', 'inspired', 'determined'],
                
                'pessimism': ['pessimistic', 'negative', 'doubtful', 'skeptical', 'cynical', 'distrustful', 'suspicious',
                             'discouraged', 'hopeless', 'despairing', 'gloomy', 'bleak', 'worried']
            }
            
            # Emotion intensifiers and diminishers
            self.emotion_modifiers = {
                'intensifiers': ['very', 'extremely', 'incredibly', 'absolutely', 'totally', 'completely', 'really',
                               'thoroughly', 'utterly', 'entirely', 'deeply', 'strongly', 'highly', 'intensely'],
                'diminishers': ['somewhat', 'slightly', 'barely', 'hardly', 'scarcely', 'kind of', 'sort of',
                              'a little', 'rather', 'quite', 'fairly', 'pretty', 'moderately']
            }
            
            # Context modifiers
            self.context_modifiers = {
                'negations': ['not', 'never', 'no', "n't", 'neither', 'nor', 'none', 'cannot', 'without',
                            'refuse', 'reject', 'deny', 'oppose', 'against'],
                'conditionals': ['if', 'unless', 'whether', 'while', 'although', 'though', 'however',
                               'but', 'despite', 'nevertheless', 'regardless', 'notwithstanding']
            }
            
        except Exception as e:
            print(f"Error loading transformer models: {str(e)}")
            print("Falling back to basic sentiment analysis...")
            self.sentiment_pipeline = None
        
        # Load spaCy model for text processing and key phrase extraction
        try:
            self.nlp = spacy.load('en_core_web_sm')
        except OSError:
            print("Downloading spaCy model...")
            spacy.cli.download('en_core_web_sm')
            self.nlp = spacy.load('en_core_web_sm')

    def analyze(self, text):
        """Analyze the sentiment and emotions of the given text."""
        if not text or not text.strip():
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'subjectivity': 0.0,
                'emotions': {'neutral': 1.0},
                'confidence_scores': {'neutral': 1.0},
                'key_phrases': [],
                'sentence_analysis': []
            }

        # Preprocess text
        text = text.strip()
        
        try:
            # Get overall sentiment using transformers if available
            if self.sentiment_pipeline:
                sentiment_result = self.sentiment_pipeline(text)[0]
                overall_sentiment = {
                    'sentiment': sentiment_result['label'],
                    'polarity': sentiment_result['score']
                }
            else:
                # Fallback to TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                overall_sentiment = {
                    'sentiment': 'positive' if polarity > 0 else 'negative' if polarity < 0 else 'neutral',
                    'polarity': (polarity + 1) / 2  # Convert to 0-1 range
                }
            
            # Get emotion scores using enhanced rule-based approach
            doc = self.nlp(text.lower())
            emotion_scores = {emotion: 0.0 for emotion in self.emotion_words}
            word_count = len([token for token in doc if not token.is_punct])
            
            # Process text in sentences for better context understanding
            sentences = [sent for sent in doc.sents]
            for sent in sentences:
                # Track context for each sentence
                context = {
                    'negated': False,
                    'intensity': 1.0,
                    'conditional': False
                }
                
                # First pass: check for context modifiers
                for token in sent:
                    word = token.text.lower()
                    
                    # Check for negations
                    if word in self.context_modifiers['negations']:
                        context['negated'] = not context['negated']
                    
                    # Check for conditionals
                    if word in self.context_modifiers['conditionals']:
                        context['conditional'] = True
                    
                    # Check for intensifiers/diminishers
                    if word in self.emotion_modifiers['intensifiers']:
                        context['intensity'] *= 1.5
                    elif word in self.emotion_modifiers['diminishers']:
                        context['intensity'] *= 0.5
                
                # Second pass: analyze emotions with context
                for token in sent:
                    word = token.text.lower()
                    
                    # Check each emotion category
                    for emotion, words in self.emotion_words.items():
                        if word in words:
                            # Calculate score based on context
                            score = context['intensity']
                            if context['negated']:
                                # When negated, reduce the score and potentially add to opposite emotions
                                score *= -0.5
                            if context['conditional']:
                                score *= 0.7
                            
                            emotion_scores[emotion] += score
            
            # Normalize emotion scores
            total_score = sum(abs(score) for score in emotion_scores.values()) or 1
            emotions = {k: max(0, v/total_score) for k, v in emotion_scores.items() if abs(v) > 0}
            
            # Remove emotions with very low scores (less than 5%)
            emotions = {k: v for k, v in emotions.items() if v >= 0.05}
            
            if not emotions:
                emotions = {'neutral': 1.0}
            
            # Normalize again after filtering
            total = sum(emotions.values())
            emotions = {k: v/total for k, v in emotions.items()}
            
            # Calculate confidence scores based on context and word frequency
            confidence_scores = {}
            for emotion, score in emotions.items():
                # Base confidence on score magnitude and supporting evidence
                base_confidence = score
                word_evidence = sum(1 for token in doc if token.text.lower() in self.emotion_words.get(emotion, []))
                context_penalty = 0.2 if any(token.text.lower() in self.context_modifiers['conditionals'] for token in doc) else 0
                
                confidence = min(0.95, (base_confidence + word_evidence/word_count)/2 - context_penalty)
                confidence_scores[emotion] = max(0.1, confidence)
            
            # Extract key phrases and analyze sentences (rest of the code remains the same)
            key_phrases = []
            seen_phrases = set()
            
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) > 1:
                    phrase = chunk.text.lower().strip()
                    if phrase not in seen_phrases:
                        key_phrases.append({
                            'phrase': phrase,
                            'count': 1,
                            'type': 'noun_phrase'
                        })
                        seen_phrases.add(phrase)
            
            for ent in doc.ents:
                if len(ent.text.split()) > 1:
                    phrase = ent.text.lower().strip()
                    if phrase not in seen_phrases:
                        key_phrases.append({
                            'phrase': phrase,
                            'count': 1,
                            'type': ent.label_
                        })
                        seen_phrases.add(phrase)
            
            # Analyze individual sentences
            sentence_analysis = []
            for sentence in sentences:
                if sentence.text.strip():
                    # Get sentence-level emotions
                    sent_emotions = {emotion: 0 for emotion in self.emotion_words}
                    sent_context = {
                        'negated': False,
                        'intensity': 1.0,
                        'conditional': False
                    }
                    
                    # Analyze sentence context and emotions
                    for token in sentence:
                        word = token.text.lower()
                        
                        # Update context
                        if word in self.context_modifiers['negations']:
                            sent_context['negated'] = not sent_context['negated']
                        elif word in self.context_modifiers['conditionals']:
                            sent_context['conditional'] = True
                        elif word in self.emotion_modifiers['intensifiers']:
                            sent_context['intensity'] *= 1.5
                        elif word in self.emotion_modifiers['diminishers']:
                            sent_context['intensity'] *= 0.5
                        
                        # Check emotions
                        for emotion, words in self.emotion_words.items():
                            if word in words:
                                score = sent_context['intensity']
                                if sent_context['negated']:
                                    score *= -0.5
                                if sent_context['conditional']:
                                    score *= 0.7
                                sent_emotions[emotion] += score
                    
                    # Get dominant emotion
                    max_emotion = max(sent_emotions.items(), key=lambda x: abs(x[1]))
                    dominant_emotion = max_emotion[0] if abs(max_emotion[1]) > 0 else 'neutral'
                    emotion_score = abs(max_emotion[1]) / len(sentence) if len(sentence) > 0 else 0
                    
                    # Get sentence sentiment
                    blob = TextBlob(sentence.text)
                    sent_polarity = (blob.sentiment.polarity + 1) / 2
                    
                    sentence_analysis.append({
                        'text': sentence.text,
                        'sentiment': 'positive' if sent_polarity > 0.6 else 'negative' if sent_polarity < 0.4 else 'neutral',
                        'polarity': sent_polarity,
                        'dominant_emotion': dominant_emotion,
                        'emotion_score': min(0.95, emotion_score + 0.2)  # Add small boost but cap at 0.95
                    })
            
            return {
                'sentiment': overall_sentiment['sentiment'],
                'polarity': overall_sentiment['polarity'],
                'subjectivity': len([p for p in key_phrases if p['type'] in ['PERSON', 'ORG', 'GPE']]) / len(key_phrases) if key_phrases else 0.0,
                'emotions': emotions,
                'confidence_scores': confidence_scores,
                'key_phrases': key_phrases,
                'sentence_analysis': sentence_analysis
            }
            
        except Exception as e:
            print(f"Error in analysis: {str(e)}")
            # Return a basic analysis using TextBlob as fallback
            blob = TextBlob(text)
            return {
                'sentiment': 'positive' if blob.sentiment.polarity > 0 else 'negative' if blob.sentiment.polarity < 0 else 'neutral',
                'polarity': (blob.sentiment.polarity + 1) / 2,
                'subjectivity': blob.sentiment.subjectivity,
                'emotions': {'neutral': 1.0},
                'confidence_scores': {'neutral': 0.5},
                'key_phrases': [],
                'sentence_analysis': []
            }

    def analyze_file(self, file_content):
        """Analyze the sentiment of a file's content."""
        return self.analyze(file_content)
