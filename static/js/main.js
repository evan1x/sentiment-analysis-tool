let emotionChart = null;

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysisForm');
    const resultsSection = document.getElementById('results');
    const submitButton = form.querySelector('button[type="submit"]');
    const buttonText = submitButton.querySelector('.button-text');
    const spinner = submitButton.querySelector('.spinner-border');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const text = document.getElementById('text').value.trim();
        if (!text) return;

        // Show loading state
        submitButton.disabled = true;
        buttonText.textContent = 'Analyzing...';
        spinner.classList.remove('d-none');
        resultsSection.classList.remove('visible');

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();
            
            if (response.ok) {
                displayResults(data);
                resultsSection.classList.add('visible');
            } else {
                alert(data.error || 'An error occurred during analysis');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while connecting to the server');
        } finally {
            // Reset button state
            submitButton.disabled = false;
            buttonText.textContent = 'Analyze Text';
            spinner.classList.add('d-none');
        }
    });
});

function displayResults(data) {
    // Display overall sentiment
    updateSentimentDisplay(data);
    
    // Display emotion chart
    updateEmotionChart(data.emotions);
    
    // Display key phrases
    displayKeyPhrases(data.key_phrases);
    
    // Display sentence analysis
    displaySentenceAnalysis(data.sentences);
}

function updateSentimentDisplay(data) {
    const sentimentSpan = document.getElementById('sentimentResult');
    const polaritySpan = document.getElementById('polarityResult');
    const subjectivitySpan = document.getElementById('subjectivityResult');
    const wordCountSpan = document.getElementById('wordCountResult');

    // Remove any existing sentiment classes
    sentimentSpan.classList.remove('positive', 'negative', 'neutral');
    
    // Add appropriate class and set text
    const sentiment = data.sentiment.charAt(0).toUpperCase() + data.sentiment.slice(1);
    sentimentSpan.textContent = sentiment;
    sentimentSpan.classList.add(data.sentiment.toLowerCase());
    
    // Set polarity and subjectivity
    polaritySpan.textContent = data.polarity.toFixed(2);
    subjectivitySpan.textContent = data.subjectivity.toFixed(2);
    
    // Set word count
    wordCountSpan.textContent = data.word_count;
}

function updateEmotionChart(emotions) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    
    if (emotionChart) {
        emotionChart.destroy();
    }
    
    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(emotions).map(emotion => 
                emotion.charAt(0).toUpperCase() + emotion.slice(1)
            ),
            datasets: [{
                data: Object.values(emotions),
                backgroundColor: [
                    '#dc3545', // anger - red
                    '#198754', // joy - green
                    '#ffc107', // neutral - yellow
                    '#6c757d'  // sadness - gray
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        boxWidth: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Emotion Distribution',
                    padding: {
                        top: 10,
                        bottom: 20
                    },
                    font: {
                        size: 16
                    }
                }
            },
            layout: {
                padding: {
                    bottom: 20
                }
            }
        }
    });
}

function displayKeyPhrases(phrases) {
    const phrasesDiv = document.getElementById('keyPhrasesResult');
    phrasesDiv.innerHTML = '';
    
    if (Array.isArray(phrases)) {
        phrases.forEach(item => {
            const phraseElement = document.createElement('div');
            phraseElement.className = 'key-phrase';
            phraseElement.textContent = `${item.phrase} (${item.count})`;
            phrasesDiv.appendChild(phraseElement);
        });
    } else if (phrases && typeof phrases === 'object') {
        // Fallback for object format
        Object.entries(phrases).forEach(([phrase, count]) => {
            const phraseElement = document.createElement('div');
            phraseElement.className = 'key-phrase';
            phraseElement.textContent = `${phrase} (${count})`;
            phrasesDiv.appendChild(phraseElement);
        });
    }
}

function displaySentenceAnalysis(sentences) {
    const sentencesDiv = document.getElementById('sentenceAnalysis');
    sentencesDiv.innerHTML = '';
    
    sentences.forEach(sentence => {
        const sentenceElement = document.createElement('div');
        sentenceElement.className = 'p-3 bg-light rounded mb-3';
        
        const sentimentClass = getSentimentClass(sentence.polarity);
        sentenceElement.innerHTML = `
            <div class="mb-2">${sentence.text}</div>
            <div class="d-flex gap-3">
                <small class="text-muted">Polarity: <span class="${sentimentClass}">${sentence.polarity.toFixed(2)}</span></small>
                <small class="text-muted">Subjectivity: ${sentence.subjectivity.toFixed(2)}</small>
            </div>
        `;
        
        sentencesDiv.appendChild(sentenceElement);
    });
}

function getSentimentClass(polarity) {
    if (polarity > 0.1) return 'text-success';
    if (polarity < -0.1) return 'text-danger';
    return 'text-secondary';
}
