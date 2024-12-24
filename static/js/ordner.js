const fileInput = document.getElementById('fileInput');
const uploadButton = document.getElementById('uploadButton');
const fileContainer = document.getElementById('fileContainer');
const summaryButton = document.getElementById('summaryButton');
let uploadedFiles = []; 

uploadButton.addEventListener('click', () => {
    const files = fileInput.files;

    if (files.length === 0) {
        alert('Bitte wählen Sie mindestens eine Datei aus.');
        return;
    }

    fileContainer.innerHTML = ''; 

    Array.from(files).forEach(file => {
        uploadedFiles.push(file); 
        const listItem = document.createElement('li');
        listItem.textContent = file.name;
        fileContainer.appendChild(listItem);
    });

    fileInput.value = '';
});

summaryButton.addEventListener('click', () => {
    if (uploadedFiles.length === 0) {
        alert('Bitte laden Sie zuerst eine Datei hoch.');
        return;
    }

    const formData = new FormData();
    uploadedFiles.forEach(file => {
        formData.append('files', file);
    });

    console.log('Lade Zusammenfassung...');

    fetch('/create_summary_from_files', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Fehler bei der Verarbeitung der Anfrage.');
        }
        return response.json();
    })
    .then(data => {
        if (data.summary) {
            const summary = encodeURIComponent(data.summary);
            window.location.href = `/summary?topic=${summary}`;
        } else if (data.error) {
            console.log('Fehler:', data.error);
            alert('Fehler bei der Erstellung der Zusammenfassung: ' + data.error);
        } else {
            console.log('Unerwartete Antwort:', data);
        }
    })
    .catch(error => {
        console.log('Ein Fehler ist aufgetreten.');
        console.error('Fehler bei der Anfrage:', error);
    });
});
