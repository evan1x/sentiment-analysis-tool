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
                       'excited', 'thrilled', 'overjoyed', 'blissful', 'ecstatic', 'merry', 'jolly', 'lively', 'enthusiastic',
                       'radiant', 'beaming', 'uplifted', 'euphoric', 'gleeful', 'blessed', 'gratified', 'sunny', 'chipper',
                       'playful', 'lighthearted', 'carefree', 'buoyant', 'exuberant', 'vivacious', 'jovial', 'mirthful',
                       'dancing', 'singing', 'laughing', 'grinning', 'smiling', 'bouncing', 'floating', 'soaring', 'glowing',
                       'sparkling', 'shining', 'radiating', 'celebrating', 'rejoicing', 'reveling', 'jubilating', 'triumphant',
                       'victorious', 'accomplished', 'fulfilled', 'peaceful', 'serene', 'tranquil', 'harmonious', 'balanced'],
                
                'sadness': ['sad', 'unhappy', 'depressed', 'gloomy', 'miserable', 'heartbroken', 'downcast', 'grieving', 'sorrowful',
                           'melancholy', 'despair', 'dejected', 'hopeless', 'disappointed', 'regretful', 'lonely', 'hurt',
                           'desolate', 'anguished', 'devastated', 'forlorn', 'woeful', 'disheartened', 'crestfallen', 'blue',
                           'despondent', 'inconsolable', 'mournful', 'bereft', 'somber', 'wistful', 'heavy-hearted', 'crushed',
                           'broken', 'shattered', 'torn', 'wounded', 'damaged', 'suffering', 'aching', 'pained', 'tormented',
                           'tortured', 'afflicted', 'distressed', 'traumatized', 'grief-stricken', 'lamenting', 'weeping',
                           'crying', 'sobbing', 'tearful', 'sniffling', 'whimpering', 'moaning', 'sighing', 'yearning'],
                
                'anger': ['angry', 'furious', 'irritated', 'annoyed', 'enraged', 'hostile', 'mad', 'outraged', 'bitter', 'hate',
                         'resentful', 'frustrated', 'agitated', 'irate', 'livid', 'indignant', 'offended', 'provoked',
                         'seething', 'fuming', 'wrathful', 'incensed', 'infuriated', 'antagonized', 'exasperated', 'heated',
                         'raging', 'storming', 'vexed', 'cross', 'disgruntled', 'sullen', 'temperamental', 'inflamed',
                         'explosive', 'volcanic', 'burning', 'boiling', 'steaming', 'fierce', 'violent', 'ferocious', 'savage',
                         'wild', 'berserk', 'rabid', 'vengeful', 'vindictive', 'spiteful', 'malicious', 'hateful', 'loathing'],
                
                'fear': ['afraid', 'scared', 'fearful', 'terrified', 'anxious', 'worried', 'nervous', 'panicked', 'frightened',
                        'threatened', 'alarmed', 'horrified', 'paranoid', 'insecure', 'uneasy', 'apprehensive', 'dread',
                        'petrified', 'phobic', 'timid', 'spooked', 'jittery', 'jumpy', 'shaken', 'trembling', 'intimidated',
                        'terrorized', 'aghast', 'disturbed', 'frantic', 'restless', 'stressed', 'tense', 'wary',
                        'quaking', 'quivering', 'shivering', 'tremulous', 'unnerved', 'rattled', 'startled', 'shocked',
                        'horrified', 'terrifying', 'nightmarish', 'spine-chilling', 'blood-curdling', 'hair-raising'],
                
                'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'startled', 'stunned', 'bewildered', 'dumbfounded',
                            'awestruck', 'wonder', 'unexpected', 'incredible', 'unbelievable', 'remarkable', 'extraordinary',
                            'flabbergasted', 'thunderstruck', 'staggered', 'taken aback', 'astounded', 'speechless', 'spellbound',
                            'perplexed', 'mystified', 'baffled', 'overwhelmed', 'wonderstruck', 'dazed', 'stupefied',
                            'gobsmacked', 'mind-blown', 'floored', 'blindsided', 'caught off guard', 'jolted', 'electrified',
                            'mesmerized', 'entranced', 'captivated', 'transfixed', 'riveted', 'fascinated', 'intrigued'],
                
                'disgust': ['disgusted', 'repulsed', 'revolted', 'sickened', 'appalled', 'horrified', 'loathing', 'hateful',
                           'repugnant', 'offensive', 'distasteful', 'nauseated', 'repelled', 'averse', 'detestable',
                           'abhorrent', 'odious', 'contemptuous', 'repulsive', 'objectionable', 'despicable', 'deplorable',
                           'revolting', 'hideous', 'unseemly', 'unsavory', 'unpalatable', 'foul', 'gross', 'nasty',
                           'stomach-turning', 'queasy', 'nauseous', 'bilious', 'ill', 'sour', 'rancid', 'putrid', 'fetid',
                           'rank', 'rotten', 'decaying', 'decomposing', 'moldy', 'musty', 'stinking', 'reeking'],
                
                'trust': ['trust', 'believe', 'confident', 'faithful', 'reliable', 'dependable', 'honest', 'sincere', 'loyal',
                         'trustworthy', 'devoted', 'dedicated', 'committed', 'assured', 'certain', 'secure',
                         'steadfast', 'unwavering', 'staunch', 'authentic', 'genuine', 'credible', 'truthful', 'upright',
                         'principled', 'ethical', 'honorable', 'respectable', 'upstanding', 'virtuous', 'true',
                         'constant', 'stable', 'solid', 'steady', 'firm', 'unshakeable', 'resolute', 'determined',
                         'unfailing', 'unflinching', 'unfaltering', 'unswerving', 'undeviating', 'reliable'],

                'anticipation': ['expect', 'anticipate', 'await', 'eager', 'hopeful', 'looking forward', 'prepared', 'ready',
                                'watchful', 'vigilant', 'alert', 'excited', 'enthusiastic', 'optimistic', 'keen',
                                'expectant', 'poised', 'primed', 'geared up', 'psyched', 'pumped', 'charged', 'thrilled',
                                'impatient', 'yearning', 'longing', 'aspiring', 'ambitious', 'determined',
                                'waiting', 'counting down', 'preparing', 'planning', 'foreseeing', 'predicting',
                                'projecting', 'envisioning', 'imagining', 'dreaming', 'fantasizing', 'visualizing'],

                'love': ['love', 'adore', 'cherish', 'affection', 'fond', 'caring', 'romantic', 'passionate', 'tender',
                        'devoted', 'warmth', 'intimate', 'attachment', 'desire', 'yearning', 'compassion',
                        'enamored', 'smitten', 'infatuated', 'enchanted', 'besotted', 'devoted', 'doting', 'ardent',
                        'amorous', 'beloved', 'treasured', 'precious', 'darling', 'dear', 'cherished',
                        'worshiping', 'idolizing', 'venerating', 'revering', 'admiring', 'attracted', 'drawn to',
                        'captivated', 'enthralled', 'spellbound', 'mesmerized', 'fascinated', 'intrigued'],

                'serenity': ['calm', 'peaceful', 'tranquil', 'relaxed', 'composed', 'collected', 'centered', 'balanced',
                            'harmonious', 'zen', 'meditative', 'mindful', 'contemplative', 'still', 'quiet',
                            'undisturbed', 'untroubled', 'placid', 'serene', 'gentle', 'mild', 'soothing',
                            'comforting', 'restful', 'easy', 'mellow', 'settled', 'grounded', 'stable'],

                'anxiety': ['anxious', 'worried', 'nervous', 'uneasy', 'concerned', 'troubled', 'distressed',
                           'agitated', 'restless', 'edgy', 'tense', 'stressed', 'pressured', 'overwhelmed',
                           'flustered', 'ruffled', 'uncomfortable', 'awkward', 'self-conscious', 'insecure',
                           'uncertain', 'hesitant', 'doubtful', 'apprehensive', 'fearful', 'scared'],

                'nostalgia': ['nostalgic', 'reminiscent', 'remembering', 'longing', 'yearning', 'wistful',
                             'sentimental', 'retrospective', 'dreamy', 'misty-eyed', 'emotional', 'touched',
                             'moved', 'affected', 'tender', 'warm', 'fond', 'attached', 'connected'],

                'guilt': ['guilty', 'remorseful', 'regretful', 'sorry', 'apologetic', 'ashamed', 'conscience-stricken',
                         'contrite', 'penitent', 'repentant', 'self-reproachful', 'culpable', 'blameworthy',
                         'at fault', 'responsible', 'answerable', 'liable', 'wrong'],

                'pride': ['proud', 'accomplished', 'confident', 'satisfied', 'fulfilled', 'successful', 'achieving',
                         'triumphant', 'victorious', 'winning', 'superior', 'distinguished', 'excellent',
                         'outstanding', 'exceptional', 'remarkable', 'notable', 'worthy'],

                'shame': ['ashamed', 'embarrassed', 'humiliated', 'mortified', 'disgraced', 'dishonored',
                         'stigmatized', 'degraded', 'debased', 'belittled', 'demeaned', 'devalued',
                         'worthless', 'inferior', 'small', 'insignificant', 'unworthy'],

                'confusion': ['confused', 'puzzled', 'perplexed', 'bewildered', 'baffled', 'mystified',
                            'disoriented', 'lost', 'uncertain', 'unsure', 'unclear', 'ambiguous',
                            'vague', 'indistinct', 'muddled', 'mixed up', 'addled', 'befuddled'],

                'determination': ['determined', 'resolved', 'committed', 'dedicated', 'focused', 'driven',
                                'motivated', 'ambitious', 'aspiring', 'striving', 'pursuing', 'persevering',
                                'persistent', 'tenacious', 'steadfast', 'unwavering', 'resolute'],

                'exhaustion': ['exhausted', 'tired', 'fatigued', 'drained', 'spent', 'worn out', 'weary',
                             'depleted', 'empty', 'burned out', 'overwhelmed', 'overworked', 'stressed',
                             'strained', 'taxed', 'overtaxed', 'overextended']
            }

            # Emotion metadata including symbols and descriptions
            self.emotion_metadata = {
                'joy': {
                    'symbol': '😊',
                    'description': 'Feeling of great pleasure and happiness'
                },
                'sadness': {
                    'symbol': '😢',
                    'description': 'Feeling of sorrow or unhappiness'
                },
                'anger': {
                    'symbol': '😠',
                    'description': 'Strong feeling of annoyance or hostility'
                },
                'fear': {
                    'symbol': '😨',
                    'description': 'Feeling of being afraid or anxious'
                },
                'surprise': {
                    'symbol': '😲',
                    'description': 'Feeling of being amazed or astonished'
                },
                'disgust': {
                    'symbol': '🤢',
                    'description': 'Feeling of revulsion or strong disapproval'
                },
                'trust': {
                    'symbol': '🤝',
                    'description': 'Feeling of confidence and reliability'
                },
                'anticipation': {
                    'symbol': '🔮',
                    'description': 'Feeling of excitement about future events'
                },
                'love': {
                    'symbol': '❤️',
                    'description': 'Deep feeling of affection and attachment'
                },
                'serenity': {
                    'symbol': '🧘',
                    'description': 'State of being calm and peaceful'
                },
                'anxiety': {
                    'symbol': '😰',
                    'description': 'Feeling of worry and unease'
                },
                'nostalgia': {
                    'symbol': '📷',
                    'description': 'Sentimental longing for the past'
                },
                'guilt': {
                    'symbol': '😣',
                    'description': 'Feeling of remorse for wrongdoing'
                },
                'pride': {
                    'symbol': '🦁',
                    'description': 'Feeling of satisfaction from achievements'
                },
                'shame': {
                    'symbol': '🙈',
                    'description': 'Feeling of humiliation or distress'
                },
                'confusion': {
                    'symbol': '🤔',
                    'description': 'State of being uncertain or puzzled'
                },
                'determination': {
                    'symbol': '💪',
                    'description': 'Firm resolution to achieve goals'
                },
                'exhaustion': {
                    'symbol': '😫',
                    'description': 'State of extreme physical or mental fatigue'
                }
            }

            # Emotion intensifiers and diminishers
            self.emotion_modifiers = {
                'intensifiers': ['very', 'extremely', 'incredibly', 'absolutely', 'totally', 'completely', 'really',
                               'thoroughly', 'utterly', 'entirely', 'deeply', 'strongly', 'highly', 'intensely',
                               'exceptionally', 'tremendously', 'extraordinarily', 'immensely', 'profoundly',
                               'remarkably', 'supremely', 'vastly', 'overwhelmingly', 'abundantly', 'excessively',
                               'enormously', 'substantially', 'significantly', 'markedly', 'notably',
                               'insanely', 'ridiculously', 'unbelievably', 'phenomenally', 'outrageously',
                               'mind-blowingly', 'staggeringly', 'astonishingly', 'shockingly', 'astoundingly',
                               'monumentally', 'colossally', 'massively', 'hugely', 'immeasurably',
                               'unimaginably', 'inconceivably', 'indescribably', 'unspeakably', 'incomparably'],
                               
                'diminishers': ['somewhat', 'slightly', 'barely', 'hardly', 'scarcely', 'kind of', 'sort of',
                              'a little', 'rather', 'quite', 'fairly', 'pretty', 'moderately',
                              'mildly', 'partially', 'relatively', 'nominally', 'marginally', 'minimally',
                              'faintly', 'vaguely', 'lightly', 'tenuously', 'tentatively', 'insignificantly',
                              'hardly', 'barely', 'scarcely', 'negligibly', 'imperceptibly', 'minutely',
                              'infinitesimally', 'microscopically', 'fractionally', 'nominally', 'technically',
                              'theoretically', 'virtually', 'practically', 'essentially', 'more or less']
            }

            # Context modifiers
            self.context_modifiers = {
                'negations': ['not', 'never', 'no', "n't", 'neither', 'nor', 'none', 'cannot', 'without',
                            'unlikely', 'impossible', 'nowhere', 'nothing', 'nobody', 'non', 'un', 'dis',
                            'hardly', 'barely', 'scarcely', 'rarely', 'seldom', 'refuse', 'deny', 'reject',
                            'prevent', 'avoid', 'stop', 'exclude', 'eliminate', 'remove', 'ban', 'prohibit'],
                            
                'temporal': ['now', 'then', 'before', 'after', 'during', 'while', 'when', 'always', 'never',
                           'sometimes', 'often', 'rarely', 'usually', 'occasionally', 'frequently', 'constantly',
                           'continuously', 'persistently', 'intermittently', 'periodically', 'regularly',
                           'sporadically', 'temporarily', 'permanently', 'momentarily', 'briefly', 'lastingly'],
                           
                'certainty': ['definitely', 'certainly', 'surely', 'undoubtedly', 'absolutely', 'obviously',
                            'clearly', 'evidently', 'apparently', 'presumably', 'probably', 'possibly',
                            'maybe', 'perhaps', 'conceivably', 'supposedly', 'allegedly', 'seemingly',
                            'ostensibly', 'reportedly', 'reputedly', 'supposedly', 'doubtfully'],
                            
                'comparison': ['more', 'less', 'better', 'worse', 'most', 'least', 'best', 'worst',
                             'similar', 'different', 'like', 'unlike', 'same', 'opposite', 'equal',
                             'unequal', 'comparable', 'incomparable', 'analogous', 'contrasting',
                             'matching', 'mismatching', 'corresponding', 'diverging'],
                             
                'causation': ['because', 'since', 'therefore', 'thus', 'hence', 'consequently',
                            'as a result', 'due to', 'owing to', 'thanks to', 'based on', 'leads to',
                            'results in', 'causes', 'affects', 'influences', 'impacts', 'determines']
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
            
            # Process text in sentences for better context understanding
            sentences = [sent for sent in self.nlp(text).sents]
            
            # Initialize emotion tracking
            emotions = {emotion: 0.0 for emotion in self.emotion_words}
            confidence_scores = {emotion: 0.0 for emotion in self.emotion_words}
            total_emotional_content = 0.0
            
            # Analyze each sentence for emotions
            for sent in sentences:
                sent_text = sent.text.lower()
                sent_doc = self.nlp(sent_text)
                
                # Track context for the sentence
                context = {
                    'negated': False,
                    'intensity': 1.0,
                    'conditional': False
                }
                
                # First pass: check for modifiers
                for token in sent_doc:
                    word = token.text.lower()
                    
                    # Check for negations
                    if word in self.context_modifiers['negations']:
                        context['negated'] = not context['negated']
                    
                    # Check for intensifiers/diminishers
                    if word in self.emotion_modifiers['intensifiers']:
                        context['intensity'] *= 1.5
                    elif word in self.emotion_modifiers['diminishers']:
                        context['intensity'] *= 0.5
                
                # Second pass: analyze emotions
                for emotion, words in self.emotion_words.items():
                    # Count emotion words in sentence
                    emotion_words_found = [word for word in sent_doc if word.text.lower() in words]
                    if emotion_words_found:
                        # Calculate base score for this emotion in this sentence
                        base_score = len(emotion_words_found) * context['intensity']
                        
                        # Apply negation if present
                        if context['negated']:
                            # When negated, reduce the score and potentially contribute to opposite emotions
                            base_score *= -0.5
                            
                            # Map emotions to their opposites
                            opposite_emotions = {
                                'joy': 'sadness',
                                'sadness': 'joy',
                                'anger': 'serenity',
                                'serenity': 'anger',
                                'trust': 'disgust',
                                'disgust': 'trust',
                                'fear': 'determination',
                                'determination': 'fear',
                                'surprise': 'anticipation',
                                'anticipation': 'surprise',
                                'love': 'hate',
                                'pride': 'shame',
                                'shame': 'pride'
                            }
                            
                            # Add score to opposite emotion if it exists
                            if emotion in opposite_emotions:
                                emotions[opposite_emotions[emotion]] += abs(base_score) * 0.7
                        
                        # Add the score to the emotion
                        emotions[emotion] += abs(base_score)
                        total_emotional_content += abs(base_score)
                        
                        # Update confidence score for this emotion
                        confidence_scores[emotion] = max(confidence_scores[emotion], abs(base_score))
            
            # Normalize emotion scores if there was any emotional content
            if total_emotional_content > 0:
                emotions = {k: v/total_emotional_content for k, v in emotions.items()}
                
                # Filter out weak emotions (less than 10% contribution)
                threshold = 0.1
                emotions = {k: v for k, v in emotions.items() if v > threshold}
                
                # Re-normalize after filtering
                total = sum(emotions.values())
                if total > 0:  # Ensure we don't divide by zero
                    emotions = {k: v/total for k, v in emotions.items()}
            
            # If no significant emotions were found or sentiment is neutral, return neutral
            if not emotions or (overall_sentiment['sentiment'] == 'neutral' and overall_sentiment['polarity'] < 0.2):
                return {
                    'sentiment': 'neutral',
                    'polarity': overall_sentiment['polarity'],
                    'emotions': {
                        'neutral': {
                            'score': 1.0,
                            'symbol': '😐',
                            'description': 'No strong emotions detected'
                        }
                    },
                    'key_phrases': [],
                    'sentence_analysis': []
                }
            
            # Prepare final emotions output with metadata
            emotions_with_metadata = {}
            for emotion, score in emotions.items():
                metadata = self.emotion_metadata.get(emotion, {})
                emotions_with_metadata[emotion] = {
                    'score': score,
                    'symbol': metadata.get('symbol', '❓'),
                    'description': metadata.get('description', 'No description available')
                }
            
            # Extract key phrases (nouns and noun phrases)
            key_phrases = []
            for chunk in self.nlp(text).noun_chunks:
                if chunk.root.pos_ in ['NOUN', 'PROPN']:
                    key_phrases.append(chunk.text)
            
            # Prepare sentence-level analysis
            sentence_analysis = []
            for sent in sentences:
                sent_doc = self.nlp(sent.text)
                sent_blob = TextBlob(sent.text)
                
                # Get sentence-level sentiment
                sent_sentiment = self.sentiment_pipeline(sent.text)[0] if self.sentiment_pipeline else {
                    'label': 'positive' if sent_blob.sentiment.polarity > 0 else 'negative' if sent_blob.sentiment.polarity < 0 else 'neutral',
                    'score': (sent_blob.sentiment.polarity + 1) / 2
                }
                
                sentence_analysis.append({
                    'text': sent.text,
                    'sentiment': sent_sentiment['label'],
                    'confidence': sent_sentiment['score']
                })
            
            return {
                'sentiment': overall_sentiment['sentiment'],
                'polarity': overall_sentiment['polarity'],
                'emotions': emotions_with_metadata,
                'key_phrases': key_phrases,
                'sentence_analysis': sentence_analysis
            }
            
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'emotions': {'neutral': {'score': 1.0, 'symbol': '😐', 'description': 'No strong emotions detected'}},
                'key_phrases': [],
                'sentence_analysis': []
            }

    def analyze_file(self, file_content):
        """Analyze the sentiment of a file's content."""
        return self.analyze(file_content)
