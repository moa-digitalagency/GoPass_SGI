// Extracted from settings/airlines.html

function openModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
        document.getElementById('formAction').value = 'create';
        document.getElementById('modalTitle').innerText = 'Ajouter une compagnie';
        document.getElementById('airlineId').value = '';
        document.getElementById('name').value = '';
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
        document.getElementById('is_active').checked = airline.is_active;
    }