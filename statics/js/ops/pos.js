/**
 * GoPass SGI-GP POS Logic
 * Extracted from templates/ops/pos.html
 */

// --- STATE MANAGEMENT ---
const appState = {
    step: 0, // 0: Flight, 1: Passengers
    flightMode: 'today',
    flightData: null, // {id, number, airline, date, ...}
    passengers: [], // Array of objects {name, doc_num, doc_type}
    unitPrice: 50.0,
    verificationSource: 'manual',
    flightDetails: null // Full JSON from API if available
};

let posConfig = {};
let els = {};

function initPOS(config) {
    posConfig = config;

    // --- DOM ELEMENTS ---
    els = {
        phaseFlight: document.getElementById('phase-flight'),
        phasePassengers: document.getElementById('phase-passengers'),
        zoneToday: document.getElementById('zone-today'),
        zoneManual: document.getElementById('zone-manual'),
        badge1: document.getElementById('badge-step-1'),
        badge2: document.getElementById('badge-step-2'),
        confirmedCard: document.getElementById('confirmed-flight-card'),
        submitBtn: document.getElementById('submitBtn'),
        displayAmount: document.getElementById('display-amount'),
        countPassengers: document.getElementById('count-passengers'),
        passengerList: document.getElementById('passenger-list')
    };

    // Load branding
    loadBranding();
}

// --- PHASE 1: FLIGHT LOGIC ---

function setFlightMode(mode) {
    appState.flightMode = mode;
    document.getElementById('flight_mode').value = mode;

    const btnToday = document.getElementById('btn-mode-today');
    const btnManual = document.getElementById('btn-mode-manual');

    if (mode === 'today') {
        btnToday.className = "flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-sm bg-white text-blue-600";
        btnManual.className = "flex-1 py-2.5 rounded-lg text-sm font-semibold text-gray-500 hover:text-gray-700 transition-all";
        els.zoneToday.classList.remove('hidden');
        els.zoneManual.classList.add('hidden');
        appState.unitPrice = 50.0;
    } else {
        btnToday.className = "flex-1 py-2.5 rounded-lg text-sm font-semibold text-gray-500 hover:text-gray-700 transition-all";
        btnManual.className = "flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-sm bg-white text-blue-600";
        els.zoneToday.classList.add('hidden');
        els.zoneManual.classList.remove('hidden');
        appState.unitPrice = 55.0; // Default Int
    }
    updateTotals();
}

function confirmTodayFlight() {
    const select = document.getElementById('flight_id');
    const val = select.value;
    if (!val) {
        alert("Veuillez sélectionner un vol.");
        return;
    }

    const opt = select.options[select.selectedIndex];
    const text = opt.text;

    appState.flightData = {
        id: val,
        desc: text,
        mode: 'today'
    };

    const price = parseFloat(opt.dataset.price || "50.0");
    appState.unitPrice = price;
    appState.verificationSource = 'manual';
    appState.flightDetails = null;

    lockFlightPhase();
}

function checkFlightInput() {
    const num = document.getElementById('manual_flight_number').value;
    const date = document.getElementById('manual_flight_date').value;
    const btn = document.getElementById('verify-btn-container');

    if (num.length >= 3 && date) {
        btn.classList.remove('hidden');
    } else {
        btn.classList.add('hidden');
    }
}

async function verifyManualFlight() {
    const num = document.getElementById('manual_flight_number').value;
    const date = document.getElementById('manual_flight_date').value;
    const spinner = document.getElementById('flight-spinner');

    spinner.classList.remove('hidden');

    try {
            const response = await fetch(posConfig.verifyFlightUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': posConfig.csrfToken },
            body: JSON.stringify({ flight_number: num, flight_date: date })
        });

        const data = await response.json();

        if (response.ok && data.found) {
            appState.flightData = {
                number: data.flight_data.airline + ' ' + num.toUpperCase(),
                date: date,
                route: `${data.flight_data.departure.iata} ➔ ${data.flight_data.arrival.iata}`,
                airline: data.flight_data.airline,
                mode: 'manual'
            };
            appState.unitPrice = data.pricing.amount;
            appState.verificationSource = 'api';
            appState.flightDetails = data.flight_data;

            lockFlightPhase();

        } else {
                document.getElementById('flight-error-msg').classList.remove('hidden');
        }

    } catch(e) {
        alert("Erreur de connexion");
    } finally {
        spinner.classList.add('hidden');
    }
}

function enableManualOverride() {
    document.getElementById('flight-error-msg').classList.add('hidden');
    document.getElementById('manual-type-selector').classList.remove('hidden');
    updatePriceManual();
}

function updatePriceManual() {
    const type = document.getElementById('manual_flight_type').value;
    appState.unitPrice = (type === 'national') ? 15.0 : 55.0;
}

function confirmManualFlight(force = false) {
        const num = document.getElementById('manual_flight_number').value;
        const date = document.getElementById('manual_flight_date').value;

        if (!num || !date) return;

        if (force) {
            appState.flightData = {
                number: num.toUpperCase(),
                date: date,
                route: "Vol Manuel",
                airline: "Inconnu",
                mode: 'manual'
            };
            appState.verificationSource = 'manual';
            appState.flightDetails = null;
        }

        lockFlightPhase();
}

function lockFlightPhase() {
    appState.step = 1;

    // Hide Selector
    els.phaseFlight.classList.add('hidden');

    // Show Card
    els.confirmedCard.classList.remove('hidden');

    // Fill Card
    if (appState.flightMode === 'today') {
        document.getElementById('cf-airline').textContent = "Vol du Jour";
        document.getElementById('cf-route').textContent = appState.flightData.desc;
        document.getElementById('cf-date').textContent = new Date().toISOString().split('T')[0];
    } else {
        document.getElementById('cf-airline').textContent = appState.flightData.airline;
        document.getElementById('cf-route').textContent = appState.flightData.route || (appState.flightData.number);
        document.getElementById('cf-date').textContent = appState.flightData.date;
    }

    document.getElementById('cf-price-badge').textContent = (appState.unitPrice < 50) ? 'DOMESTIQUE' : 'INTERNATIONAL';
    document.getElementById('cf-price-badge').className = (appState.unitPrice < 50)
        ? "bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded"
        : "bg-emerald-100 text-emerald-700 text-xs font-bold px-2 py-1 rounded";

    // Update Steps
    els.badge1.classList.replace('bg-blue-600', 'bg-green-500');
    els.badge1.innerHTML = '<i class="fas fa-check mr-1"></i> Vol OK';
    els.badge2.classList.replace('bg-gray-200', 'bg-blue-600');
    els.badge2.classList.replace('text-gray-500', 'text-white');

    // Show Passengers
    els.phasePassengers.classList.remove('hidden');

    // Initial Empty Passenger
    appState.passengers = [{ name: '', doc_num: '', doc_type: 'Passeport' }];
    renderPassengers();

    checkValidation();
}

function resetFlightSelection() {
    if (!confirm("Attention : Cela va réinitialiser la liste des passagers. Continuer ?")) return;

    appState.step = 0;
    appState.passengers = [];
    appState.flightData = null;

    els.phaseFlight.classList.remove('hidden');
    els.confirmedCard.classList.add('hidden');
    els.phasePassengers.classList.add('hidden');

    // Reset Badges
    els.badge1.classList.replace('bg-green-500', 'bg-blue-600');
    els.badge1.innerHTML = '1. Vol';
    els.badge2.classList.replace('bg-blue-600', 'bg-gray-200');
    els.badge2.classList.replace('text-white', 'text-gray-500');

    renderPassengers();
    checkValidation();
}

// --- PHASE 2: PASSENGER LOGIC ---

function addPassengerRow() {
    appState.passengers.push({ name: '', doc_num: '', doc_type: 'Passeport' });
    renderPassengers();
    checkValidation();
}

function removePassenger(index) {
    if (appState.passengers.length <= 1) return; // Prevent deleting last one
    appState.passengers.splice(index, 1);
    renderPassengers();
    checkValidation();
}

function updatePassengerData(index, field, value) {
    appState.passengers[index][field] = value;
    checkValidation();
}

function renderPassengers() {
    els.passengerList.innerHTML = '';

    appState.passengers.forEach((p, idx) => {
        const el = document.createElement('div');
        el.className = "bg-white p-4 rounded-xl border border-gray-100 shadow-sm relative";

        // Header (Passager X)
        const headerHtml = `
            <div class="flex justify-between items-center mb-3">
                    <span class="text-xs font-bold uppercase tracking-wider text-gray-400">Passager ${idx + 1}</span>
                    ${ (appState.passengers.length > 1) ?
                    `<button type="button" onclick="removePassenger(${idx})" class="text-red-400 hover:text-red-600 text-xs font-bold"><i class="fas fa-trash-alt mr-1"></i> Supprimer</button>`
                    : ''
                    }
            </div>
        `;

        // Inputs
        const inputsHtml = `
            <div class="space-y-3">
                <div>
                    <input type="text"
                            value="${p.name}"
                            oninput="updatePassengerData(${idx}, 'name', this.value)"
                            class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-400 bg-white"
                            placeholder="Nom Complet (ex: Jean Dupont)"
                            autocomplete="off">
                </div>
                <div class="grid grid-cols-3 gap-3">
                    <div class="col-span-1">
                        <select onchange="updatePassengerData(${idx}, 'doc_type', this.value)"
                                class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-400 bg-white">
                            <option value="Passeport" ${p.doc_type === 'Passeport' ? 'selected' : ''}>Passeport</option>
                            <option value="Carte d'Identité" ${p.doc_type === "Carte d'Identité" ? 'selected' : ''}>Carte ID</option>
                            <option value="Permis de Conduire" ${p.doc_type === 'Permis de Conduire' ? 'selected' : ''}>Permis</option>
                        </select>
                    </div>
                    <div class="col-span-2">
                        <input type="text"
                                value="${p.doc_num}"
                                oninput="updatePassengerData(${idx}, 'doc_num', this.value)"
                                class="w-full p-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-400 bg-white"
                                placeholder="N° Document">
                    </div>
                </div>
            </div>
        `;

        el.innerHTML = headerHtml + inputsHtml;
        els.passengerList.appendChild(el);
    });

    updateTotals();
}

function updateTotals() {
    const count = appState.passengers.length;
    const total = count * appState.unitPrice;

    els.countPassengers.textContent = count;
    els.displayAmount.textContent = total.toFixed(2) + " $";
}

// --- PHASE 3: VALIDATION & SUBMIT ---

function checkValidation() {
    // Check flight
    if (appState.step !== 1) return setSubmit(false);

    if (appState.passengers.length === 0) return setSubmit(false);

    let validCount = 0;
    let partialCount = 0;

    appState.passengers.forEach(p => {
        const hasName = p.name.trim().length > 0;
        const hasDoc = p.doc_num.trim().length > 0;

        if (hasName && hasDoc) {
            validCount++;
        } else if (hasName || hasDoc) {
            partialCount++;
        }
        // Empty rows (neither Name nor Doc) are ignored
    });

    // Enable if at least one valid passenger AND no partial/invalid rows blocking
    const canSubmit = (validCount > 0) && (partialCount === 0);

    setSubmit(canSubmit);
}

function setSubmit(enabled) {
        if (enabled) {
        els.submitBtn.disabled = false;
        els.submitBtn.classList.remove('bg-gray-300', 'text-gray-500', 'cursor-not-allowed');
        els.submitBtn.classList.add('bg-gradient-to-r', 'from-emerald-500', 'to-teal-600', 'text-white', 'shadow-lg', 'hover:from-emerald-600');
    } else {
        els.submitBtn.disabled = true;
        els.submitBtn.classList.add('bg-gray-300', 'text-gray-500', 'cursor-not-allowed');
        els.submitBtn.classList.remove('bg-gradient-to-r', 'from-emerald-500', 'to-teal-600', 'text-white', 'shadow-lg', 'hover:from-emerald-600');
    }
}

async function submitSale() {
    if (els.submitBtn.disabled) return;

    const originalHtml = els.submitBtn.innerHTML;
    els.submitBtn.disabled = true;
    els.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> TRAITEMENT...';

    // Filter out empty rows before sending
    const validPassengers = appState.passengers.filter(p =>
        p.name.trim().length > 0 && p.doc_num.trim().length > 0
    );

    // Payload Construction
    const payload = {
        flight_mode: appState.flightMode,
        flight_id: (appState.flightMode === 'today') ? appState.flightData.id : null,
        manual_flight_number: (appState.flightMode === 'manual') ? document.getElementById('manual_flight_number').value : null,
        manual_flight_date: (appState.flightMode === 'manual') ? document.getElementById('manual_flight_date').value : null,

        passengers: validPassengers,
        price: appState.unitPrice,
        verification_source: appState.verificationSource,
        flight_details: appState.flightDetails
    };

    try {
        const response = await fetch(posConfig.posSaleUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': posConfig.csrfToken },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showToast(`${result.tickets.length} billets générés !`);

            // Add to history
            addToHistory(result);

            // Update Session Total
            let currentTotal = parseFloat(document.getElementById('totalSalesDisplay').textContent);
            currentTotal += result.total_price;
            document.getElementById('totalSalesDisplay').textContent = currentTotal.toFixed(1) + " $";

            // PRINT LOOP
            await printLoop(result.tickets);

            // Reset Logic (Keep flight, reset passengers to one empty)
            appState.passengers = [{ name: '', doc_num: '', doc_type: 'Passeport' }];
            renderPassengers();
            checkValidation();

        } else {
            alert("Erreur: " + (result.error || "Inconnue"));
        }

    } catch(e) {
        alert("Erreur réseau: " + e.message);
        console.error(e);
    } finally {
        els.submitBtn.disabled = false;
        els.submitBtn.innerHTML = originalHtml;
        checkValidation();
    }
}

// --- PRINTING ---
async function printLoop(tickets) {
    const container = document.getElementById('print-container');
    container.innerHTML = '';

    for (const ticket of tickets) {
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = ticket.pdf_url;
        container.appendChild(iframe);

        // Wait for load and print
        await new Promise((resolve) => {
            iframe.onload = () => {
                    setTimeout(() => {
                        iframe.contentWindow.focus();
                        iframe.contentWindow.print();
                        resolve();
                    }, 1000); // 1s delay between prints
            };
        });
    }
}

// --- HISTORY ---
function addToHistory(data) {
        const list = document.getElementById('history-list');
        const empty = document.getElementById('empty-state');
        if (empty) empty.remove();

        data.tickets.forEach(ticket => {
            const item = document.createElement('div');
            item.className = "bg-white p-4 rounded-xl border border-gray-100 shadow-sm flex justify-between items-center animate-fade-in-down mb-2";
            item.innerHTML = `
            <div>
                <div class="flex items-center space-x-2 mb-1">
                    <span class="text-xs font-bold text-gray-400">${data.time}</span>
                    <span class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-bold">${data.flight_number}</span>
                </div>
                <p class="font-bold text-gray-800 text-sm truncate max-w-[150px]">${ticket.passenger_name}</p>
                <p class="text-xs text-green-600 font-semibold mt-1">
                    <i class="fas fa-check-circle mr-1"></i> Payé ${ticket.price} $
                </p>
            </div>
            <button onclick="reprintOne('${ticket.pdf_url}')" class="w-10 h-10 rounded-full bg-gray-50 hover:bg-gray-100 flex items-center justify-center text-gray-500 transition-colors" title="Réimprimer">
                <i class="fas fa-print"></i>
            </button>
            `;
            list.insertBefore(item, list.firstChild);
        });

        // Update Mobile Badge (Robust Count)
        const badge = document.getElementById('mobile-history-badge');
        if(badge) badge.textContent = list.children.length;
}

function reprintOne(url) {
        const container = document.getElementById('print-container');
        container.innerHTML = '';
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = url;
        container.appendChild(iframe);
        iframe.onload = function() {
        setTimeout(function() {
            iframe.contentWindow.focus();
            iframe.contentWindow.print();
        }, 500);
    };
}

// Simple Toast
function showToast(message) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = "fixed bottom-6 right-6 z-50 flex flex-col space-y-2";
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = "bg-gray-800 text-white px-6 py-3 rounded-lg shadow-xl flex items-center transform transition-all duration-300 translate-y-10 opacity-0";
    toast.innerHTML = `<i class="fas fa-check-circle text-green-400 mr-3"></i> ${message}`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.remove('translate-y-10', 'opacity-0'));
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// History Toggle
function toggleHistory() {
    const sec = document.getElementById('history-section');
    const overlay = document.getElementById('history-overlay');

    if (sec.classList.contains('translate-x-full')) {
        sec.classList.remove('translate-x-full');
        overlay.classList.remove('hidden');
    } else {
        sec.classList.add('translate-x-full');
        overlay.classList.add('hidden');
    }
}

function loadBranding() {
    fetch('/api/settings/public')
    .then(r => r.json())
    .then(data => {
        if (data.rva_logo) {
            const img = document.getElementById('pos-logo-rva');
            img.src = data.rva_logo;
            img.classList.remove('hidden');
        }
    })
    .catch(console.error);
}
