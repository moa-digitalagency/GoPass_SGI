// Extracted from settings/airports.html

function openModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
        document.getElementById('formAction').value = 'create';
        document.getElementById('modalTitle').innerText = 'Ajouter un aéroport';
        document.getElementById('airportId').value = '';
        document.getElementById('iata_code').value = '';
        document.getElementById('city').value = '';
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
        document.getElementById('city').value = airport.city;
        document.getElementById('type').value = airport.type;
    }