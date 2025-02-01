let emotionChart = null;

document.getElementById('sentimentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const text = document.getElementById('textInput').value.trim();
    if (!text) return;

    // Show loading spinner
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('result').style.display = 'none';

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
        } else {
            alert(data.error || 'An error occurred during analysis');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while connecting to the server');
    } finally {
        document.getElementById('loadingSpinner').style.display = 'none';
    }
});

function displayResults(data) {
    const resultDiv = document.getElementById('result');
    
    // Display overall sentiment
    updateSentimentDisplay(data);
    
    // Display emotion chart
    updateEmotionChart(data.emotions);
    
    // Display key phrases
    displayKeyPhrases(data.key_phrases);
    
    // Display sentence analysis
    displaySentenceAnalysis(data.sentences);
    
    // Show results
    resultDiv.style.display = 'block';
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
    
    // Destroy existing chart if it exists
    if (emotionChart) {
        emotionChart.destroy();
    }
    
    // Create new chart
    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(emotions).map(emotion => 
                emotion.charAt(0).toUpperCase() + emotion.slice(1)
            ),
            datasets: [{
                data: Object.values(emotions),
                backgroundColor: [
                    '#198754', // joy - green
                    '#dc3545', // sadness - red
                    '#ffc107', // anger - yellow
                    '#6c757d'  // neutral - gray
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Emotion Distribution'
                }
            }
        }
    });
}

function displayKeyPhrases(phrases) {
    const phrasesDiv = document.getElementById('keyPhrasesResult');
    phrasesDiv.innerHTML = '';
    
    phrases.forEach(({ phrase, count }) => {
        const phraseElement = document.createElement('span');
        phraseElement.className = 'key-phrase';
        phraseElement.innerHTML = `
            ${phrase}
            <span class="count">${count}</span>
        `;
        phrasesDiv.appendChild(phraseElement);
    });
}

function displaySentenceAnalysis(sentences) {
    const sentencesDiv = document.getElementById('sentencesResult');
    sentencesDiv.innerHTML = '';
    
    sentences.forEach(sentence => {
        const sentiment = getSentimentClass(sentence.polarity);
        const sentenceElement = document.createElement('div');
        sentenceElement.className = `sentence-item ${sentiment}`;
        
        sentenceElement.innerHTML = `
            <div class="sentence-text">${sentence.text}</div>
            <div class="sentence-metrics">
                <span>Polarity: ${sentence.polarity.toFixed(2)}</span>
                <span>Subjectivity: ${sentence.subjectivity.toFixed(2)}</span>
            </div>
        `;
        
        sentencesDiv.appendChild(sentenceElement);
    });
}

function getSentimentClass(polarity) {
    if (polarity > 0.1) return 'positive';
    if (polarity < -0.1) return 'negative';
    return 'neutral';
}
