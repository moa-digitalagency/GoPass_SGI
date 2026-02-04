// Extracted from settings/airports.html

function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
    document.getElementById('formAction').value = 'create';
    document.getElementById('modalTitle').innerText = 'Ajouter un aéroport';
    document.getElementById('airportId').value = '';
    document.getElementById('iata_code').value = '';
    document.getElementById('name').value = '';
    document.getElementById('city').value = '';
    document.getElementById('country').value = '';
    document.getElementById('type').value = 'national';
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function editAirport(airport) {
    openModal('createModal');
    document.getElementById('formAction').value = 'update';
    document.getElementById('modalTitle').innerText = 'Modifier l\'aéroport';
    document.getElementById('airportId').value = airport.id;
    document.getElementById('iata_code').value = airport.iata_code;
    document.getElementById('name').value = airport.name || '';
    document.getElementById('city').value = airport.city;
    document.getElementById('country').value = airport.country || '';
    document.getElementById('type').value = airport.type;
}

document.addEventListener('DOMContentLoaded', function() {
    // Sync Logic
    const syncBtn = document.getElementById('syncAirportsBtn');
    if(syncBtn) {
        syncBtn.addEventListener('click', function() {
            const icon = document.getElementById('syncIcon');
            const text = document.getElementById('syncText');

            // Get CSRF token
            const csrfTokenInput = document.querySelector('input[name="csrf_token"]');
            const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

            if (!csrfToken) {
                alert("Erreur: Token CSRF introuvable.");
                return;
            }

            icon.classList.add('fa-spin');
            text.innerText = 'Synchronisation...';
            syncBtn.disabled = true;
            syncBtn.classList.add('opacity-75', 'cursor-not-allowed');

            fetch('/api/sync/airports', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'success') {
                    alert('Synchronisation réussie: ' + data.count + ' aéroports mis à jour.');
                    window.location.reload();
                } else {
                    alert('Erreur: ' + (data.message || 'Erreur inconnue'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Erreur réseau lors de la synchronisation.');
            })
            .finally(() => {
                icon.classList.remove('fa-spin');
                text.innerText = 'Synchroniser via API';
                syncBtn.disabled = false;
                syncBtn.classList.remove('opacity-75', 'cursor-not-allowed');
            });
        });
    }

    // Filter Logic
    const searchInput = document.getElementById('searchInput');
    const countryFilter = document.getElementById('countryFilter');
    const typeFilter = document.getElementById('typeFilter');
    const rows = document.querySelectorAll('.airport-row');

    if (rows.length > 0 && countryFilter) {
        // Populate Country Filter
        const countries = new Set();
        rows.forEach(row => {
            const c = row.getAttribute('data-country');
            if(c && c !== '-') countries.add(c);
        });
        const sortedCountries = Array.from(countries).sort();
        sortedCountries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.text = country;
            countryFilter.add(option);
        });
    }

    function filterTable() {
        if (!searchInput) return;

        const searchTerm = searchInput.value.toLowerCase();
        const countryTerm = countryFilter ? countryFilter.value : '';
        const typeTerm = typeFilter ? typeFilter.value : '';

        rows.forEach(row => {
            const name = row.getAttribute('data-name') || '';
            const iata = row.getAttribute('data-iata') || '';
            const city = row.getAttribute('data-city') || '';
            const country = row.getAttribute('data-country') || '';
            const type = row.getAttribute('data-type') || '';

            let matchesSearch = (name.includes(searchTerm) || iata.includes(searchTerm) || city.includes(searchTerm));
            let matchesCountry = (countryTerm === '' || country === countryTerm);
            let matchesType = (typeTerm === '' || type === typeTerm);

            if (matchesSearch && matchesCountry && matchesType) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (searchInput) searchInput.addEventListener('keyup', filterTable);
    if (countryFilter) countryFilter.addEventListener('change', filterTable);
    if (typeFilter) typeFilter.addEventListener('change', filterTable);
});
