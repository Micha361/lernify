document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const subject = urlParams.get('subject');
    const recipient = urlParams.get('email');  
    console.log("Subject from URL:", subject);
    console.log("Recipient from URL:", recipient);

    if (subject) {
        document.getElementById('subject').value = decodeURIComponent(subject);
    } else {
        console.log("Subject parameter not found in URL");
    }

    if (recipient) {
        document.getElementById('recipient').value = decodeURIComponent(recipient);
    } else {
        console.log("Recipient parameter not found in URL");
    }

    document.getElementById('contactForm').addEventListener('submit', function(event) {
        event.preventDefault();
        
        const senderEmail = document.getElementById('email').value;
        const message = document.getElementById('message').value;
        const subject = document.getElementById('subject').value;
        const recipientEmail = document.getElementById('recipient').value;

        if (senderEmail && message && subject && recipientEmail) {
            window.location.href = `mailto:${recipientEmail}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(message)}`;
            
            document.getElementById('email').value = '';
            document.getElementById('message').value = '';
            document.getElementById('subject').value = '';
            document.getElementById('recipient').value = '';

            alert("Die E-Mail wurde versendet!");
        } else {
            alert("Bitte fülle alle Felder aus.");
        }
    });
});
