const app = Vue.createApp({
    data() {
        return {
            darkMode: false,
            users: [],
            totalUsers: 0,
        };
    },
    created() {
        this.fetchUsers();
    },
    methods: {
        fetchUsers() {
            fetch('/api/users')
                .then(response => response.json())
                .then(data => {
                    if (data.users) {
                        this.users = data.users;
                        this.totalUsers = data.total;
                    }
                })
                .catch(error => console.error("Fehler beim Abrufen der Benutzerliste:", error));
        },
        deleteUser(userId) {
            if (confirm("Bist du sicher, dass du diesen Benutzer löschen möchtest?")) {
                fetch(`/api/delete-user/${userId}`, {
                    method: 'DELETE',
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert(data.message);
                            this.fetchUsers();
                        } else {
                            alert("Fehler: " + data.error);
                        }
                    })
                    .catch(error => console.error("Fehler beim Löschen des Benutzers:", error));
            }
        },
    },
});
app.mount('#app');


    function filterUsers() {
        const searchInput = document.getElementById('searchInput').value.toLowerCase();
        const tableRows = document.querySelectorAll('#userTableBody tr');

        tableRows.forEach(row => {
            const usernameCell = row.querySelector('.username');
            const username = usernameCell.textContent.toLowerCase();

            if (username.includes(searchInput)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }


