let emotionChart = null;
let lastAnalysisResult = null;

document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('analyzeButton');
    const form = document.getElementById('analysisForm');
    const resultsSection = document.getElementById('results');
    const spinner = analyzeButton.querySelector('.spinner-border');
    const buttonText = analyzeButton.querySelector('.button-text');
    const textInput = document.getElementById('text');
    const fileInput = document.getElementById('fileInput');
    const exportPDFButton = document.getElementById('exportPDFButton');
    const exportCSVButton = document.getElementById('exportCSV');

    function initFileUpload() {
        const dropZone = document.getElementById('dropZone');
        const browseButton = document.getElementById('browseButton');
        const fileInput = document.getElementById('fileInput');

        function updateFileName(file) {
            const uploadText = dropZone.querySelector('.upload-text');
            if (file) {
                uploadText.innerHTML = `<span>${file.name}</span>`;
            } else {
                uploadText.innerHTML = '<span>Drop your file here or</span><button type="button" class="btn btn-link p-0 mx-1" id="browseButton">browse</button>';
            }
        }

        dropZone.addEventListener('click', (e) => {
            if (e.target !== browseButton && !browseButton.contains(e.target)) {
                fileInput.click();
            }
        });

        browseButton.addEventListener('click', (e) => {
            e.preventDefault(); 
            fileInput.click();
        });

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            });
        });

        dropZone.addEventListener('drop', handleDrop);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            fileInput.files = files;
            
            if (files.length > 0) {
                updateFileName(files[0]);
                textInput.value = ''; 
                textInput.disabled = true;
                buttonText.innerHTML = '<i class="fas fa-search me-2"></i>Analyze File';
            }
        }

        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                updateFileName(file);
                textInput.value = ''; 
                textInput.disabled = true;
                buttonText.innerHTML = '<i class="fas fa-search me-2"></i>Analyze File';
            } else {
                textInput.disabled = false;
                buttonText.innerHTML = '<i class="fas fa-search me-2"></i>Analyze';
            }
        });

        textInput.addEventListener('input', function() {
            if (textInput.value.trim()) {
                fileInput.value = ''; 
                textInput.disabled = false;
            }
        });
    }

    function initTheme() {
        const themeToggle = document.querySelector('.theme-toggle');
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        
        // Get theme from localStorage or system preference
        const currentTheme = localStorage.getItem('theme') || 
                            (prefersDarkScheme.matches ? 'dark' : 'light');
        
        // Set initial theme
        document.documentElement.setAttribute('data-theme', currentTheme);
        updateThemeIcon(currentTheme);
        
        // Toggle theme on button click
        themeToggle.addEventListener('click', () => {
            const newTheme = document.documentElement.getAttribute('data-theme') === 'dark' 
                ? 'light' 
                : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        const icon = document.querySelector('.theme-toggle i');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }

    initTheme();
    initFileUpload();

    analyzeButton.addEventListener('click', async function() {
        spinner.classList.remove('d-none');
        buttonText.textContent = 'Analyzing...';
        
        try {
            let response;
            
            if (fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
            } else {
                const text = textInput.value.trim();
                if (!text) {
                    throw new Error('Please enter some text to analyze');
                }
                response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: text })
                });
            }

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to analyze text');
            }

            lastAnalysisResult = data;
            displayResults(data);
            resultsSection.classList.add('visible');
            
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'An error occurred during analysis');
        } finally {
            spinner.classList.add('d-none');
            buttonText.innerHTML = '<i class="fas fa-search me-2"></i>Analyze';
        }
    });

    // Export button handlers
    exportCSVButton.addEventListener('click', async function() {
        if (!lastAnalysisResult) {
            alert('Please analyze some text before exporting');
            return;
        }
        
        try {
            const response = await fetch('/export/csv', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(lastAnalysisResult)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to export CSV');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            
            // Get filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
            a.download = filenameMatch ? filenameMatch[1] : `sentiment_analysis_${new Date().toISOString().slice(0,19).replace(/[:]/g, '')}.csv`;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Failed to export CSV');
        }
    });

    exportPDFButton.addEventListener('click', async function() {
        if (!lastAnalysisResult) {
            alert('Please analyze some text before exporting to PDF');
            return;
        }
        
        try {
            const response = await fetch('/export/pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(lastAnalysisResult)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to export PDF');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            const contentDisposition = response.headers.get('Content-Disposition');
            const filenameMatch = contentDisposition && contentDisposition.match(/filename="(.+)"/);
            a.download = filenameMatch ? filenameMatch[1] : 'sentiment_analysis.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Error:', error);
            alert(error.message || 'Failed to export PDF');
        }
    });
});

function displayResults(data) {
    const results = document.getElementById('results');
    
    // Update sentiment values with null checks
    document.getElementById('sentimentValue').textContent = data.sentiment || '-';
    document.getElementById('polarityValue').textContent = typeof data.polarity === 'number' ? data.polarity.toFixed(2) : '-';
    document.getElementById('subjectivityValue').textContent = typeof data.subjectivity === 'number' ? data.subjectivity.toFixed(2) : '-';
    
    // Update emotion chart
    if (data.emotions && Object.keys(data.emotions).length > 0) {
        updateEmotionChart(data.emotions);
    }
    
    // Update key phrases
    const keyPhrasesContainer = document.getElementById('keyPhrases');
    keyPhrasesContainer.innerHTML = '';
    if (data.key_phrases && Array.isArray(data.key_phrases)) {
        data.key_phrases.forEach(phrase => {
            if (phrase && typeof phrase === 'object') {
                const phraseEl = document.createElement('div');
                phraseEl.className = 'phrase-card';
                phraseEl.textContent = phrase.phrase || phrase.text || 'Unknown phrase';
                if (phrase.type) {
                    phraseEl.title = `Type: ${phrase.type}`;
                }
                keyPhrasesContainer.appendChild(phraseEl);
            }
        });
    }
    
    // Update sentence analysis
    const sentenceContainer = document.getElementById('sentenceAnalysis');
    sentenceContainer.innerHTML = '';
    
    if (data.sentence_analysis && Array.isArray(data.sentence_analysis)) {
        data.sentence_analysis.forEach(sentence => {
            if (sentence && typeof sentence === 'object' && sentence.text) {
                const sentenceEl = document.createElement('div');
                const polarity = typeof sentence.polarity === 'number' ? sentence.polarity : 0;
                sentenceEl.className = `sentence-item ${getSentimentClass(polarity)}`;
                
                // Build the metrics HTML with null checks
                const metricsHtml = [];
                if (typeof sentence.polarity === 'number') {
                    metricsHtml.push(`<span>Polarity: ${sentence.polarity.toFixed(2)}</span>`);
                }
                if (sentence.dominant_emotion) {
                    metricsHtml.push(`<span>Emotion: ${sentence.dominant_emotion}</span>`);
                }
                if (typeof sentence.emotion_score === 'number') {
                    metricsHtml.push(`<span>Confidence: ${sentence.emotion_score.toFixed(2)}</span>`);
                }
                
                sentenceEl.innerHTML = `
                    <p>${sentence.text}</p>
                    ${metricsHtml.length > 0 ? `<div class="sentence-metrics">${metricsHtml.join('')}</div>` : ''}
                `;
                sentenceContainer.appendChild(sentenceEl);
            }
        });
    }
    
    // Make results visible
    results.classList.add('visible');
}

function updateEmotionChart(emotions) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    
    // Define emotion colors
    const emotionColors = {
        'joy': '#FFD700',        // Gold
        'sadness': '#4169E1',    // Royal Blue
        'anger': '#DC143C',      // Crimson
        'fear': '#800080',       // Purple
        'surprise': '#FFA500',   // Orange
        'disgust': '#006400',    // Dark Green
        'trust': '#20B2AA',      // Light Sea Green
        'anticipation': '#FF69B4',// Hot Pink
        'love': '#FF1493',       // Deep Pink
        'admiration': '#9370DB',  // Medium Purple
        'optimism': '#98FB98',   // Pale Green
        'pessimism': '#708090',  // Slate Gray
        'neutral': '#808080'     // Gray
    };

    // Sort emotions by intensity
    const sortedEmotions = Object.entries(emotions)
        .sort(([, a], [, b]) => b - a)
        .filter(([, value]) => value >= 0.05); // Only show emotions with at least 5% intensity

    const labels = sortedEmotions.map(([emotion]) => emotion);
    const data = sortedEmotions.map(([, value]) => (value * 100).toFixed(1));
    const colors = sortedEmotions.map(([emotion]) => emotionColors[emotion] || '#808080');

    // Destroy previous chart if it exists
    if (emotionChart) {
        emotionChart.destroy();
    }

    // Create new chart
    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(255, 255, 255, 0.5)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: document.body.classList.contains('dark-mode') ? '#fff' : '#333',
                        font: {
                            size: 12
                        },
                        generateLabels: (chart) => {
                            const data = chart.data;
                            if (data.labels.length && data.datasets.length) {
                                return data.labels.map((label, i) => ({
                                    text: `${label} (${data.datasets[0].data[i]}%)`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    strokeStyle: data.datasets[0].borderColor,
                                    lineWidth: data.datasets[0].borderWidth,
                                    hidden: isNaN(data.datasets[0].data[i]),
                                    index: i
                                }));
                            }
                            return [];
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return `${label}: ${value}%`;
                        }
                    }
                }
            },
            cutout: '60%',
            animation: {
                animateScale: true,
                animateRotate: true
            }
        }
    });

    // Update emotion list display
    const emotionList = document.getElementById('emotionList');
    emotionList.innerHTML = '';

    sortedEmotions.forEach(([emotion, value]) => {
        const emotionItem = document.createElement('div');
        emotionItem.className = 'emotion-item';
        const percentage = (value * 100).toFixed(1);
        
        // Get the emotion icon
        const icon = getEmotionIcon(emotion);
        
        emotionItem.innerHTML = `
            <div class="emotion-icon" style="color: ${emotionColors[emotion]}">
                ${icon}
            </div>
            <div class="emotion-details">
                <div class="emotion-name">${emotion.charAt(0).toUpperCase() + emotion.slice(1)}</div>
                <div class="emotion-score">
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${percentage}%; background-color: ${emotionColors[emotion]}" 
                             aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100">
                        </div>
                    </div>
                    <span class="percentage">${percentage}%</span>
                </div>
            </div>
        `;
        
        emotionList.appendChild(emotionItem);
    });
}

function getEmotionIcon(emotion) {
    const icons = {
        'joy': '<i class="fas fa-smile-beam"></i>',
        'sadness': '<i class="fas fa-sad-tear"></i>',
        'anger': '<i class="fas fa-angry"></i>',
        'fear': '<i class="fas fa-ghost"></i>',
        'surprise': '<i class="fas fa-surprise"></i>',
        'disgust': '<i class="fas fa-grimace"></i>',
        'trust': '<i class="fas fa-handshake"></i>',
        'anticipation': '<i class="fas fa-hourglass-half"></i>',
        'love': '<i class="fas fa-heart"></i>',
        'admiration': '<i class="fas fa-star"></i>',
        'optimism': '<i class="fas fa-sun"></i>',
        'pessimism': '<i class="fas fa-cloud"></i>',
        'neutral': '<i class="fas fa-meh"></i>'
    };
    return icons[emotion] || '<i class="fas fa-question-circle"></i>';
}

function getSentimentClass(polarity) {
    if (polarity > 0.3) return 'positive';
    if (polarity < -0.3) return 'negative';
    return 'neutral';
}
