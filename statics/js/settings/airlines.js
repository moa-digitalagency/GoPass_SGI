// Extracted from settings/airlines.html

function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
    document.getElementById('formAction').value = 'create';
    document.getElementById('modalTitle').innerText = 'Ajouter une compagnie';
    document.getElementById('airlineId').value = '';
    document.getElementById('name').value = '';
    document.getElementById('iata_code').value = '';
    document.getElementById('icao_code').value = '';
    document.getElementById('country').value = '';
    document.getElementById('logo').value = '';
    document.getElementById('is_active').checked = true;
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function editAirline(airline) {
    openModal('createModal');
    document.getElementById('formAction').value = 'update';
    document.getElementById('modalTitle').innerText = 'Modifier la compagnie';
    document.getElementById('airlineId').value = airline.id;
    document.getElementById('name').value = airline.name;
    document.getElementById('iata_code').value = airline.iata_code || '';
    document.getElementById('icao_code').value = airline.icao_code || '';
    document.getElementById('country').value = airline.country || '';
    document.getElementById('is_active').checked = airline.is_active;
}

document.addEventListener('DOMContentLoaded', function() {
    // Sync Logic
    const syncBtn = document.getElementById('syncAirlinesBtn');
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

            fetch('/api/sync/airlines', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if(data.status === 'success') {
                    if (data.count !== undefined) {
                        alert('Synchronisation réussie: ' + data.count + ' compagnies mises à jour.');
                        window.location.reload();
                    } else {
                        alert(data.message || 'Synchronisation lancée en arrière-plan. Les données seront mises à jour progressivement.');
                        setTimeout(() => window.location.reload(), 2000);
                    }
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
    const cards = document.querySelectorAll('.airline-card');

    if (cards.length > 0 && countryFilter) {
         // Populate Country Filter
        const countries = new Set();
        cards.forEach(card => {
            const c = card.getAttribute('data-country');
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

    function filterCards() {
        if (!searchInput) return;

        const searchTerm = searchInput.value.toLowerCase();
        const countryTerm = countryFilter ? countryFilter.value : '';

        cards.forEach(card => {
            const name = card.getAttribute('data-name') || '';
            const iata = card.getAttribute('data-iata') || '';
            const country = card.getAttribute('data-country') || '';

            let matchesSearch = (name.includes(searchTerm) || iata.includes(searchTerm));
            let matchesCountry = (countryTerm === '' || country === countryTerm);

            if (matchesSearch && matchesCountry) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }

    if(searchInput) searchInput.addEventListener('keyup', filterCards);
    if(countryFilter) countryFilter.addEventListener('change', filterCards);
});
