const API_URL = window.location.origin + "/get_summary"; 

let loadingInterval;

function startLoadingAnimation(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;

    let dots = 0;

    loadingInterval = setInterval(() => {
        dots = (dots + 1) % 4; 
        element.innerText = `Laden${'.'.repeat(dots)}`;
    }, 500); 
}

function stopLoadingAnimation(elementId, message) {
    clearInterval(loadingInterval); 
    const element = document.getElementById(elementId);
    if (element && message) {
        element.innerText = message;
    }
}


async function fetchSummary() {
    const params = new URLSearchParams(window.location.search);
    const topic = params.get('topic');

    if (!topic) {
        document.getElementById('summaryOutput').innerText = 'Kein Thema angegeben!';
        return;
    }

    startLoadingAnimation('summaryOutput'); 

    try {
        const response = await fetch(`${API_URL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic: topic })
        });

        if (response.ok) {
            const data = await response.json();
            stopLoadingAnimation('summaryOutput', data.summary); 
        } else {
            stopLoadingAnimation('summaryOutput', 'Fehler beim Abrufen der Zusammenfassung.');
        }
    } catch (error) {
        console.error('Error:', error);
        stopLoadingAnimation('summaryOutput', 'Es gab einen Fehler bei der Verbindung zur AI.');
    }
}


async function fetchWithInstructions() {
    const params = new URLSearchParams(window.location.search);
    const topic = params.get('topic');
    const instructionsInput = document.getElementById('instructionsInput');
    const instructions = instructionsInput.value;

    if (!topic) {
        document.getElementById('summaryOutput').innerText = 'Kein Thema angegeben!';
        return;
    }

    document.getElementById('summaryOutput').innerText = 'Laden...';

    try {
        const response = await fetch(`${API_URL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic: topic, instructions: instructions })
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('summaryOutput').innerText = data.summary;
            instructionsInput.value = '';
        } else {
            document.getElementById('summaryOutput').innerText = 'Fehler beim Abrufen der Zusammenfassung.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('summaryOutput').innerText = 'Es gab einen Fehler bei der Verbindung zur AI.';
    }
}

async function generateAdvantagesDisadvantages() {
    const summaryText = document.getElementById('summaryOutput').innerText;

    if (!summaryText || summaryText === 'Laden...') {
        alert('Keine Zusammenfassung verfügbar, um Vorteile und Nachteile zu erstellen.');
        return;
    }

    document.getElementById('summaryOutput').innerText = 'Laden...';


    try {
        const response = await fetch(`${API_URL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic: summaryText, instructions: 'Vorteile und Nachteile' })
        });

        if (response.ok) {
            const data = await response.json();
            document.getElementById('summaryOutput').innerText = data.summary;
        } else {
            document.getElementById('summaryOutput').innerText = 'Fehler beim Abrufen der Vorteile und Nachteile.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('summaryOutput').innerText = 'Es gab einen Fehler bei der Verbindung zur AI.';
    }
}

async function generateExamples() {
    const summaryText = document.getElementById('summaryOutput').innerText;

    if (!summaryText || summaryText === 'Laden...') {
        alert('Keine Zusammenfassung verfügbar, um Beispiele zu erstellen.');
        return;
    }

    document.getElementById('summaryOutput').innerText = 'Laden...';

    try {
        const response = await fetch(`${API_URL}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic: summaryText, instructions: 'Beispiele' })
        });würd

        if (response.ok) {
            const data = await response.json();
            document.getElementById('summaryOutput').innerText = data.summary;
        } else {
            document.getElementById('summaryOutput').innerText = 'Fehler beim Abrufen der Beispiele.';
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('summaryOutput').innerText = 'Es gab einen Fehler bei der Verbindung zur AI.';
    }
}

function handleEnterKey(event) {
    if (event.key === 'Enter') {
        fetchWithInstructions();
        document.getElementById('instructionsInput').value = '';
    }
}

window.onload = function() {
    fetchSummary();
    const inputField = document.getElementById('instructionsInput');
    if (inputField) {
        inputField.addEventListener('keydown', handleEnterKey);
    }
};

function copyToClipboard() {
    const summaryElement = document.getElementById("summaryOutput");
    const textToCopy = summaryElement.innerText || summaryElement.textContent;

    const tempInput = document.createElement("textarea");
    tempInput.value = textToCopy;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand("copy");
    document.body.removeChild(tempInput);

    const copyButton = document.getElementById("copyButton");
    copyButton.classList.add("copied");

    setTimeout(() => {
        copyButton.classList.remove("copied");
    }, 500);
}


