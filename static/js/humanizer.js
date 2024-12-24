async function createHumanizedText() {
    const notesInput = document.getElementById("notesInput");
    const outputDiv = document.getElementById("humanizerOutput");

    if (!notesInput.value.trim()) {
        alert("Bitte füge Notizen ein, um fortzufahren.");
        return;
    }

    outputDiv.innerText = "Wird geladen...";

    try {
        const response = await fetch("/humanizer/generate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ notes: notesInput.value })
        });

        if (!response.ok) {
            throw new Error("Serverantwort nicht erfolgreich.");
        }

        const data = await response.json();
        outputDiv.innerText = data.humanized_text || "Keine Antwort erhalten.";
    } catch (error) {
        console.error("Fehler:", error);
        outputDiv.innerText = "Fehler beim Erstellen des Textes.";
    } finally {
        notesInput.value = ""; 
    }
}

function copyToClipboard() {
    const summaryElement = document.getElementById("humanizerOutput");
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


