# Sentiment Analysis Tool

A web-based sentiment analysis tool that analyzes text and determines its emotional tone using Natural Language Processing (NLP) techniques.

## Features

- Real-time sentiment analysis
- Polarity scoring (-1 to 1)
- Subjectivity assessment (0 to 1)
- Clean, responsive user interface
- Visual feedback for different sentiment types

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## Technology Stack

- Flask (Web Framework)
- NLTK (Natural Language Processing)
- TextBlob (Sentiment Analysis)
- Bootstrap (Frontend Styling)
- JavaScript (Frontend Interactivity)

## Project Structure

```
sentiment-analyzer/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   └── index.html
├── app.py
├── sentiment_model.py
├── requirements.txt
└── README.md
```

## Contributing

Feel free to submit issues and enhancement requests!
