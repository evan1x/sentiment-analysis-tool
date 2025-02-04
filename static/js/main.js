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
                textInput.value = ''; 
                textInput.disabled = true;
                buttonText.innerHTML = '<i class="fas fa-search me-2"></i>Analyze File';
            }
        }

        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
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
    
    // Update sentiment values
    document.getElementById('sentimentValue').textContent = data.sentiment || '-';
    document.getElementById('polarityValue').textContent = data.polarity ? data.polarity.toFixed(2) : '-';
    document.getElementById('subjectivityValue').textContent = data.subjectivity ? data.subjectivity.toFixed(2) : '-';
    
    // Update emotion chart
    if (data.emotions) {
        updateEmotionChart(data.emotions);
    }
    
    // Update key phrases
    if (data.key_phrases) {
        const keyPhrasesContainer = document.getElementById('keyPhrases');
        keyPhrasesContainer.innerHTML = '';
        data.key_phrases.forEach(phrase => {
            const phraseEl = document.createElement('div');
            phraseEl.className = 'phrase-card';
            phraseEl.textContent = phrase;
            keyPhrasesContainer.appendChild(phraseEl);
        });
    }
    
    // Update sentence analysis
    const sentenceContainer = document.getElementById('sentenceAnalysis');
    sentenceContainer.innerHTML = '';
    
    if (data.sentence_analysis && Array.isArray(data.sentence_analysis)) {
        data.sentence_analysis.forEach(sentence => {
            const sentenceEl = document.createElement('div');
            sentenceEl.className = `sentence-item ${getSentimentClass(sentence.polarity)}`;
            sentenceEl.innerHTML = `
                <p>${sentence.text}</p>
                <div class="sentence-metrics">
                    <span>Polarity: ${sentence.polarity.toFixed(2)}</span>
                    <span>Subjectivity: ${sentence.subjectivity.toFixed(2)}</span>
                </div>
            `;
            sentenceContainer.appendChild(sentenceEl);
        });
    }
    
    // Make results visible
    results.classList.add('visible');
}

function updateEmotionChart(emotions) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    const emotionList = document.getElementById('emotionList');
    
    // Clear previous emotion list
    emotionList.innerHTML = '';
    
    if (emotionChart) {
        emotionChart.destroy();
    }
    
    const labels = Object.keys(emotions);
    const data = Object.values(emotions);
    
    // Create the chart
    emotionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
            datasets: [{
                data: data,
                backgroundColor: labels.map(getEmotionColor),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return `${(value * 100).toFixed(1)}%`;
                        }
                    }
                }
            }
        }
    });
    
    // Create emotion list items
    labels.forEach((emotion, index) => {
        const percentage = (data[index] * 100).toFixed(1);
        const emotionColor = getEmotionColor(emotion);
        const emotionIcon = getEmotionIcon(emotion);
        
        const emotionItem = document.createElement('div');
        emotionItem.className = 'emotion-item';
        emotionItem.innerHTML = `
            <div class="emotion-name">
                <div class="emotion-icon" style="background: ${emotionColor}">
                    <i class="${emotionIcon}"></i>
                </div>
                ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}
            </div>
            <div class="emotion-value">${percentage}%</div>
            <div class="emotion-bar">
                <div class="emotion-bar-fill" style="width: ${percentage}%; background: ${emotionColor}"></div>
            </div>
        `;
        
        emotionList.appendChild(emotionItem);
    });
}

function getEmotionIcon(emotion) {
    const icons = {
        'joy': 'fas fa-smile',
        'sadness': 'fas fa-sad-tear',
        'anger': 'fas fa-angry',
        'fear': 'fas fa-ghost',
        'surprise': 'fas fa-surprise',
        'neutral': 'fas fa-meh'
    };
    return icons[emotion.toLowerCase()] || 'fas fa-question';
}

function getEmotionColor(emotion) {
    const colors = {
        'joy': '#2ecc71',
        'sadness': '#3498db',
        'anger': '#e74c3c',
        'fear': '#9b59b6',
        'surprise': '#f1c40f',
        'neutral': '#95a5a6'
    };
    return colors[emotion.toLowerCase()] || '#95a5a6';
}

function getSentimentClass(polarity) {
    if (polarity > 0.3) return 'positive';
    if (polarity < -0.3) return 'negative';
    return 'neutral';
}
