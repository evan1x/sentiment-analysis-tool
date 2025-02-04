let emotionChart = null;
let lastAnalysisResult = null;

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysisForm');
    const resultsSection = document.getElementById('results');
    const submitButton = form.querySelector('button[type="submit"]');
    const buttonText = submitButton.querySelector('.button-text');
    const spinner = submitButton.querySelector('.spinner-border');
    const textInput = document.getElementById('text');
    const fileInput = document.getElementById('fileInput');
    const exportPDFButton = document.getElementById('exportPDF');
    const exportCSVButton = document.getElementById('exportCSV');

    // Handle file input changes
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            textInput.value = ''; // Clear text input
            textInput.disabled = true;
            buttonText.textContent = 'Analyze File';
        } else {
            textInput.disabled = false;
            buttonText.textContent = 'Analyze Text';
        }
    });

    // Handle text input changes
    textInput.addEventListener('input', function() {
        if (textInput.value.trim()) {
            fileInput.value = ''; // Clear file input
        }
    });

    // Add real-time analysis with debouncing
    const debouncedAnalysis = debounce(performAnalysis, 1000);
    textInput.addEventListener('input', (e) => {
        const text = e.target.value.trim();
        if (text.length >= 50) {  // Only analyze substantial text
            debouncedAnalysis(text);
        }
    });

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        
        if (fileInput.files.length > 0) {
            formData.append('file', fileInput.files[0]);
            await performFileAnalysis(formData);
        } else {
            const text = textInput.value.trim();
            if (!text) return;
            await performAnalysis(text);
        }
    });

    // Handle export buttons
    exportCSVButton.addEventListener('click', async function() {
        if (!lastAnalysisResult) return;
        
        try {
            const response = await fetch('/export/csv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(lastAnalysisResult)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `sentiment_analysis_${new Date().toISOString().slice(0,19).replace(/[:]/g, '')}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            } else {
                const error = await response.json();
                alert(error.error || 'Failed to export CSV');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to export CSV');
        }
    });

    exportPDFButton.addEventListener('click', async function() {
        if (!lastAnalysisResult) return;
        
        try {
            const response = await fetch('/export/pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(lastAnalysisResult)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `sentiment_analysis_${new Date().toISOString().slice(0,19).replace(/[:]/g, '')}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            } else {
                const error = await response.json();
                alert(error.error || 'Failed to export PDF');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to export PDF');
        }
    });
});

// Debounce function for real-time analysis
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function performFileAnalysis(formData) {
    const submitButton = document.querySelector('button[type="submit"]');
    const buttonText = submitButton.querySelector('.button-text');
    const spinner = submitButton.querySelector('.spinner-border');
    const resultsSection = document.getElementById('results');
    
    try {
        submitButton.disabled = true;
        buttonText.textContent = 'Analyzing File...';
        spinner.classList.remove('d-none');
        resultsSection.classList.remove('visible');

        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            lastAnalysisResult = data;
            displayResults(data);
            resultsSection.classList.add('visible');
        } else {
            alert(data.error || 'An error occurred during analysis');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while analyzing the file');
    } finally {
        submitButton.disabled = false;
        buttonText.textContent = 'Analyze File';
        spinner.classList.add('d-none');
    }
}

async function performAnalysis(text) {
    const submitButton = document.querySelector('button[type="submit"]');
    const buttonText = submitButton.querySelector('.button-text');
    const spinner = submitButton.querySelector('.spinner-border');
    const resultsSection = document.getElementById('results');

    try {
        submitButton.disabled = true;
        buttonText.textContent = 'Analyzing...';
        spinner.classList.remove('d-none');
        resultsSection.classList.remove('visible');

        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();
        
        if (response.ok) {
            lastAnalysisResult = data;
            displayResults(data);
            resultsSection.classList.add('visible');
        } else {
            alert(data.error || 'An error occurred during analysis');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while connecting to the server');
    } finally {
        submitButton.disabled = false;
        buttonText.textContent = 'Analyze Text';
        spinner.classList.add('d-none');
    }
}

function displayResults(data) {
    // Display text summary if available
    if (data.summary) {
        document.getElementById('textSummary').textContent = data.summary;
    }
    
    // Display overall sentiment
    updateSentimentDisplay(data);
    
    // Display emotion chart
    updateEmotionChart(data.emotions);
    
    // Display readability metrics if available
    if (data.readability) {
        displayReadabilityMetrics(data.readability);
    }
    
    // Display key phrases
    displayKeyPhrases(data.key_phrases);
    
    // Display sentence analysis
    displaySentenceAnalysis(data.sentences);
    
    // Update statistics
    document.getElementById('wordCountResult').textContent = data.word_count;
    document.getElementById('sentenceCountResult').textContent = data.sentence_count;
}

function displayReadabilityMetrics(metrics) {
    const container = document.getElementById('readabilityMetrics');
    container.innerHTML = '';
    
    const metricNames = {
        'flesch_reading_ease': 'Flesch Reading Ease',
        'flesch_kincaid_grade': 'Flesch-Kincaid Grade',
        'gunning_fog': 'Gunning Fog',
        'smog_index': 'SMOG Index',
        'automated_readability_index': 'ARI',
        'coleman_liau_index': 'Coleman-Liau',
        'difficult_words': 'Difficult Words'
    };
    
    Object.entries(metrics).forEach(([key, value]) => {
        const col = document.createElement('div');
        col.className = 'col-6';
        col.innerHTML = `
            <div class="p-3 bg-light rounded">
                <div class="metric-value">${typeof value === 'number' ? value.toFixed(1) : value}</div>
                <div class="metric-label">${metricNames[key] || key}</div>
            </div>
        `;
        container.appendChild(col);
    });
}

function updateSentimentDisplay(data) {
    const sentimentSpan = document.getElementById('sentimentResult');
    const polaritySpan = document.getElementById('polarityResult');
    const subjectivitySpan = document.getElementById('subjectivityResult');

    // Add appropriate class and set text
    const sentiment = data.sentiment.charAt(0).toUpperCase() + data.sentiment.slice(1);
    sentimentSpan.textContent = sentiment;
    
    // Set polarity and subjectivity
    polaritySpan.textContent = data.polarity.toFixed(2);
    subjectivitySpan.textContent = data.subjectivity.toFixed(2);
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
                    '#28a745', // joy - green
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
        
        // Create emotion badges
        const emotionBadges = Object.entries(sentence.emotions || {})
            .filter(([_, value]) => value > 0.1)
            .map(([emotion, value]) => `
                <span class="badge bg-${getEmotionColor(emotion)} me-2">
                    ${emotion}: ${(value * 100).toFixed(0)}%
                </span>
            `).join('');
        
        // Create entity badges if available
        const entityBadges = sentence.structure?.entities
            ? sentence.structure.entities.map(([text, label]) => `
                <span class="badge bg-info me-2" title="${label}">
                    ${text}
                </span>
              `).join('')
            : '';
        
        // Show sentence structure if available
        const structure = sentence.structure
            ? `<div class="mt-2 small">
                ${sentence.structure.subject ? `<span class="text-primary">Subject: ${sentence.structure.subject}</span> ` : ''}
                ${sentence.structure.action ? `<span class="text-success">Action: ${sentence.structure.action}</span> ` : ''}
                ${sentence.structure.object ? `<span class="text-info">Object: ${sentence.structure.object}</span>` : ''}
               </div>`
            : '';
        
        sentenceElement.innerHTML = `
            <div class="mb-2">${sentence.text}</div>
            <div class="d-flex flex-wrap gap-2 align-items-center">
                <small class="text-muted">Polarity: 
                    <span class="${sentimentClass}">${sentence.polarity.toFixed(2)}</span>
                </small>
                <small class="text-muted">Subjectivity: ${sentence.subjectivity.toFixed(2)}</small>
            </div>
            ${emotionBadges ? `<div class="mt-2">${emotionBadges}</div>` : ''}
            ${entityBadges ? `<div class="mt-2">${entityBadges}</div>` : ''}
            ${structure}
        `;
        
        sentencesDiv.appendChild(sentenceElement);
    });
}

function getSentimentClass(polarity) {
    if (polarity > 0.1) return 'text-success';
    if (polarity < -0.1) return 'text-danger';
    return 'text-secondary';
}

function getEmotionColor(emotion) {
    const colors = {
        'joy': 'success',
        'sadness': 'secondary',
        'anger': 'danger',
        'neutral': 'warning'
    };
    return colors[emotion] || 'primary';
}
