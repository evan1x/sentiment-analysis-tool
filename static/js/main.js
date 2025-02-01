document.getElementById('sentimentForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const text = document.getElementById('textInput').value.trim();
    if (!text) return;

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
    }
});

function displayResults(data) {
    const resultDiv = document.getElementById('result');
    const sentimentSpan = document.getElementById('sentimentResult');
    const polaritySpan = document.getElementById('polarityResult');
    const subjectivitySpan = document.getElementById('subjectivityResult');

    // Remove any existing sentiment classes
    sentimentSpan.classList.remove('positive', 'negative', 'neutral');
    
    // Add appropriate class and set text
    sentimentSpan.textContent = data.sentiment.charAt(0).toUpperCase() + data.sentiment.slice(1);
    sentimentSpan.classList.add(data.sentiment.toLowerCase());
    
    // Set polarity and subjectivity
    polaritySpan.textContent = data.polarity.toFixed(2);
    subjectivitySpan.textContent = data.subjectivity.toFixed(2);
    
    // Show results
    resultDiv.style.display = 'block';
}
