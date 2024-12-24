document.getElementById('delete-account-button').addEventListener('click', async () => {
    const confirmation = confirm("Möchtest du deinen Account wirklich löschen?");
    if (!confirmation) return;

    try {
        const response = await fetch('/api/delete-account', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            alert("Dein Account wurde erfolgreich gelöscht.");
            window.location.href = '/logout';
        } else {
            const error = await response.json();
            alert(`Fehler: ${error.message}`);
        }
    } catch (error) {
        console.error("Fehler beim Löschen des Accounts:", error);
        alert("Ein Fehler ist aufgetreten. Bitte versuche es später erneut.");
    }
});