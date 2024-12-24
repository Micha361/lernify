document.addEventListener("DOMContentLoaded", function () {
    fetch('/api/get_dark_mode')
        .then(response => response.json())
        .then(data => {
            const darkMode = data.dark_mode;
            document.body.classList.toggle('dark-mode', darkMode);
            const toggleInput = document.querySelector('.switch input');
            if (toggleInput) {
                toggleInput.checked = darkMode;
            }
        });

    const toggleInput = document.querySelector('.switch input');
    if (toggleInput) {
        toggleInput.addEventListener('click', function () {
            const darkMode = this.checked;
            document.body.classList.toggle('dark-mode', darkMode);
            fetch('/api/set_dark_mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ dark_mode: darkMode }),
            });
        });
    }
});
