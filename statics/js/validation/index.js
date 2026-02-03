// Extracted from validation/index.html

const passNumberInput = document.getElementById('pass-number');
    const locationInput = document.getElementById('location');
    const validateBtn = document.getElementById('validate-btn');
    const resultContainer = document.getElementById('result-container');
    const resultContent = document.getElementById('result-content');
    const recentValidations = document.getElementById('recent-validations');

    async function validatePass() {
        const passNumber = passNumberInput.value.trim().toUpperCase();
        if (!passNumber) {
            alert('Veuillez entrer un numero de pass');
            return;
        }

        validateBtn.disabled = true;
        validateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Validation...';

        try {
            const response = await fetch('/validation/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    pass_number: passNumber,
                    location: locationInput.value
                })
            });

            const result = await response.json();
            showResult(result);
            loadRecentValidations();
        } catch (error) {
            showResult({ valid: false, status: 'error', message: 'Erreur de connexion' });
        } finally {
            validateBtn.disabled = false;
            validateBtn.innerHTML = '<i class="fas fa-check-circle mr-2"></i>Valider le Pass';
        }
    }

    function showResult(result) {
        resultContainer.classList.remove('hidden');

        if (result.valid) {
            resultContent.innerHTML = `
                <div class="bg-green-100 border-2 border-green-500 rounded-xl p-6 text-center">
                    <i class="fas fa-check-circle text-6xl text-green-500 mb-4"></i>
                    <h3 class="text-2xl font-bold text-green-800">ACCES AUTORISE</h3>
                    ${result.pass ? `
                        <p class="mt-4 text-lg">${result.pass.holder.first_name} ${result.pass.holder.last_name}</p>
                        <p class="text-green-700">${result.pass.pass_type.name}</p>
                    ` : ''}
                </div>
            `;
        } else {
            resultContent.innerHTML = `
                <div class="bg-red-100 border-2 border-red-500 rounded-xl p-6 text-center">
                    <i class="fas fa-times-circle text-6xl text-red-500 mb-4"></i>
                    <h3 class="text-2xl font-bold text-red-800">ACCES REFUSE</h3>
                    <p class="mt-4 text-lg text-red-700">${result.message}</p>
                    ${result.pass ? `
                        <p class="mt-2">${result.pass.holder.first_name} ${result.pass.holder.last_name}</p>
                    ` : ''}
                </div>
            `;
        }
    }

    async function loadRecentValidations() {
        try {
            const response = await fetch('/api/recent-validations?limit=5');
            const validations = await response.json();

            if (validations.length === 0) {
                recentValidations.innerHTML = '<p class="text-gray-500 text-center py-4">Aucune validation recente</p>';
                return;
            }

            recentValidations.innerHTML = validations.map(v => `
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                        <span class="font-mono font-semibold">${v.pass_number || 'N/A'}</span>
                        <span class="text-sm text-gray-500 ml-2">${v.location || ''}</span>
                    </div>
                    <div class="flex items-center">
                        <span class="px-2 py-1 rounded-full text-xs mr-3 ${v.status === 'granted' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                            ${v.status === 'granted' ? 'Accorde' : 'Refuse'}
                        </span>
                        <span class="text-sm text-gray-500">${new Date(v.validation_time).toLocaleTimeString('fr-FR')}</span>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            recentValidations.innerHTML = '<p class="text-gray-500 text-center py-4">Erreur de chargement</p>';
        }
    }

    validateBtn.addEventListener('click', validatePass);
    passNumberInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') validatePass();
    });

    loadRecentValidations();