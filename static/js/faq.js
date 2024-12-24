document.addEventListener('DOMContentLoaded', async () => {
    const notesInput = document.getElementById('notesInput');
    let notes = sessionStorage.getItem('notes');

    if (!notes) {
        alert('Keine Notizen gefunden!');
        window.location.href = 'index.html';
        return;
    }

    let currentQuestion = null;

    async function fetchQuestion(notes) {
        try {
            const response = await fetch('/generate_question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes })
            });

            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            return data;
        } catch (error) {
            console.error('Fehler beim Generieren des Quiz:', error);
            alert('Du bist zu schnell! Bitte warte ein paar Sekunden!');
            return null;
        }
    }

    async function loadNextQuestion() {
        const data = await fetchQuestion(notes);
        if (!data) return;

        currentQuestion = data;

        document.getElementById('question').innerText = data.question;

        const buttons = document.querySelectorAll('#answer-buttons .btn');
        buttons.forEach((btn, index) => {
            btn.innerText = data.answers[index];
            btn.style.display = 'block';
            btn.disabled = false;
            btn.style.backgroundColor = '';
            btn.style.borderColor = '';
            btn.style.transition = 'background-color 0.5s ease-in-out, border-color 0.5s ease-in-out';
            btn.onclick = () => handleAnswer(index, buttons);
        });

        document.getElementById('nextQuestion').style.display = 'none';
    }

    function handleAnswer(selectedIndex, buttons) {
        buttons.forEach((btn, index) => {
            btn.disabled = true;

            if (index === selectedIndex) {
                if (index === currentQuestion.correct_index) {
                    btn.style.backgroundColor = 'rgb(42, 255, 42)';
                    btn.style.borderColor = 'rgb(42, 255, 42)';
                } else {
                    btn.style.backgroundColor = 'rgb(255, 57, 57)'; 
                    btn.style.borderColor = 'rgb(255, 57, 57)';
                }
            }

            if (index === currentQuestion.correct_index) {
                btn.style.backgroundColor = 'rgb(42, 255, 42)'; 
                btn.style.borderColor = 'rgb(42, 255, 42)';
            }
        });

        document.getElementById('nextQuestion').style.display = 'block';
    }

    function handleEnterKey(event) {
        if (event.key === 'Enter' && notesInput) {
            notes = notesInput.value; 
            sessionStorage.setItem('notes', notes);
            notesInput.value = '';
            loadNextQuestion();
            event.preventDefault(); 
        }
    }

    loadNextQuestion();

    if (notesInput) {
        notesInput.addEventListener('keydown', handleEnterKey);
    }

    document.getElementById('nextQuestion').addEventListener('click', loadNextQuestion);
});
