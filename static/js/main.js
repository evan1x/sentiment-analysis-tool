let emotionChart = null;
let lastAnalysisResult = null;

document.addEventListener('DOMContentLoaded', function() {
    // Add Chart.js script dynamically and wait for it to load
    const chartScript = document.createElement('script');
    chartScript.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    chartScript.onload = function() {
        // Initialize any global chart settings after Chart.js loads
        if (window.Chart) {
            Chart.defaults.font.family = "'Inter', sans-serif";
            Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--text-color');
        }
    };
    document.head.appendChild(chartScript);

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
        const textInput = document.getElementById('text');
        const buttonText = document.querySelector('#analyzeButton .button-text');

        if (!dropZone || !browseButton || !fileInput || !textInput || !buttonText) {
            console.error('Required elements for file upload not found');
            return;
        }

        function updateFileName(file) {
            const uploadText = dropZone.querySelector('.upload-text');
            if (!uploadText) {
                console.error('Upload text element not found');
                return;
            }
            if (file) {
                uploadText.innerHTML = `<span>${file.name}</span>`;
            } else {
                uploadText.innerHTML = '<span>Drop your file here or</span><button type="button" class="btn btn-link p-0 mx-1" id="browseButton">browse</button>';
            }
        }

        dropZone.addEventListener('click', (e) => {
            const browseBtn = document.getElementById('browseButton');
            if (browseBtn && (e.target !== browseBtn && !browseBtn.contains(e.target))) {
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
    const resultsSection = document.getElementById('results');
    const sentimentResult = document.getElementById('sentimentResult');
    const emotionContainer = document.getElementById('emotionDistribution');
    const keyPhrasesContainer = document.getElementById('keyPhrases');
    const sentenceAnalysisContainer = document.getElementById('sentenceAnalysis');

    if (!resultsSection || !sentimentResult || !emotionContainer || !keyPhrasesContainer || !sentenceAnalysisContainer) {
        console.error('Required results elements not found');
        return;
    }

    // Update sentiment section
    const sentimentClass = getSentimentClass(data.polarity);
    sentimentResult.innerHTML = `
        <div class="metric ${sentimentClass}">
            <h3>Overall Sentiment</h3>
            <p class="sentiment-value">${data.sentiment}</p>
            <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${data.polarity * 100}%"></div>
            </div>
            <p class="confidence-value">Confidence: ${(data.polarity * 100).toFixed(1)}%</p>
        </div>
    `;

    // Update emotion distribution
    const emotionCards = emotionContainer.querySelector('.emotion-cards');
    emotionCards.innerHTML = ''; // Clear existing cards

    // Check if we're in a neutral state (all emotions near 0)
    const emotions = data.emotions;
    const isNeutral = Object.values(emotions).every(emotion => emotion.score < 0.1);

    if (isNeutral) {
        // Display only neutral emotion
        const card = document.createElement('div');
        card.className = 'emotion-card emotion-neutral';
        card.setAttribute('data-description', 'No strong emotions detected');
        
        card.innerHTML = `
            <div class="emotion-header">
                <span class="emotion-icon">😐</span>
                <span class="emotion-name">Neutral</span>
            </div>
            <div class="emotion-score">
                <div class="emotion-score-fill" style="width: 100%"></div>
            </div>
            <div class="emotion-percentage">100%</div>
        `;
        
        emotionCards.appendChild(card);
        
        // Update pie chart for neutral state
        updateEmotionChart([{
            name: 'Neutral',
            score: 1,
            color: '#9e9e9e'
        }]);
    } else {
        // Convert emotions object to array and sort by score
        const emotionArray = Object.entries(emotions)
            .map(([emotion, emotionData]) => ({
                name: emotion,
                score: emotionData.score,
                symbol: emotionData.symbol,
                description: emotionData.description
            }))
            .filter(emotion => emotion.score > 0.05) // Filter out very low scores
            .sort((a, b) => b.score - a.score);

        // Create cards for each emotion
        emotionArray.forEach(emotion => {
            const card = document.createElement('div');
            card.className = `emotion-card emotion-${emotion.name}`;
            card.setAttribute('data-description', emotion.description);

            const percentage = (emotion.score * 100).toFixed(1);
            
            card.innerHTML = `
                <div class="emotion-header">
                    <span class="emotion-icon">${emotion.symbol}</span>
                    <span class="emotion-name">${emotion.name}</span>
                </div>
                <div class="emotion-score">
                    <div class="emotion-score-fill" style="width: ${percentage}%"></div>
                </div>
                <div class="emotion-percentage">${percentage}%</div>
            `;

            emotionCards.appendChild(card);
            card.style.animationDelay = `${emotionCards.children.length * 0.1}s`;
        });

        // Update pie chart with emotion data
        const chartData = emotionArray.map((emotion, index) => ({
            name: emotion.name,
            score: emotion.score,
            color: getEmotionColor(index)
        }));
        updateEmotionChart(chartData);
    }

    // Update key phrases
    if (data.key_phrases && data.key_phrases.length > 0) {
        const phrasesList = data.key_phrases
            .map(phrase => `<span class="badge bg-secondary me-2 mb-2">${phrase}</span>`)
            .join('');
        keyPhrasesContainer.innerHTML = `
            <h3>Key Phrases</h3>
            <div class="phrases-cloud">${phrasesList}</div>
        `;
    } else {
        keyPhrasesContainer.innerHTML = '';
    }

    // Update sentence analysis
    if (data.sentence_analysis && data.sentence_analysis.length > 0) {
        const sentencesList = data.sentence_analysis
            .map(sentence => `
                <div class="sentence-item ${getSentimentClass(sentence.confidence)}">
                    <p class="sentence-text">${sentence.text}</p>
                    <div class="sentence-metadata">
                        <span class="sentiment-label">${sentence.sentiment}</span>
                        <div class="confidence-bar">
                            <div class="confidence-fill" 
                                 style="width: ${sentence.confidence * 100}%"></div>
                        </div>
                    </div>
                </div>
            `)
            .join('');
        sentenceAnalysisContainer.innerHTML = `
            <h3>Sentence Analysis</h3>
            <div class="sentences-list">${sentencesList}</div>
        `;
    } else {
        sentenceAnalysisContainer.innerHTML = '';
    }

    // Show export buttons
    const exportButtons = document.getElementById('exportButtons');
    if (exportButtons) {
        exportButtons.classList.remove('d-none');
    }
    
    // Make results visible
    resultsSection.classList.add('visible');
}

function getSentimentClass(polarity) {
    if (polarity > 0.3) return 'positive';
    if (polarity < -0.3) return 'negative';
    return 'neutral';
}

function updateEmotionChart(emotions) {
    // Wait for Chart to be available
    if (!window.Chart) {
        console.log('Chart.js not loaded yet, retrying in 100ms...');
        setTimeout(() => updateEmotionChart(emotions), 100);
        return;
    }

    const ctx = document.getElementById('emotionChart');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (window.emotionChart && window.emotionChart.destroy) {
        window.emotionChart.destroy();
    }

    window.emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: emotions.map(e => e.name),
            datasets: [{
                data: emotions.map(e => e.score),
                backgroundColor: emotions.map(e => e.color),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: getComputedStyle(document.documentElement).getPropertyValue('--text-color'),
                        font: {
                            size: 12,
                            family: "'Inter', sans-serif"
                        },
                        padding: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return `${context.label}: ${(value * 100).toFixed(1)}%`;
                        }
                    }
                }
            },
            cutout: '60%',
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
}

function getEmotionColor(index) {
    const colors = [
        '#FF6B6B', // Red
        '#4ECDC4', // Teal
        '#45B7D1', // Blue
        '#96CEB4', // Green
        '#FFEEAD', // Yellow
        '#D4A5A5', // Pink
        '#9B59B6', // Purple
        '#3498DB', // Light Blue
        '#E67E22', // Orange
        '#1ABC9C'  // Turquoise
    ];
    return colors[index % colors.length];
}
