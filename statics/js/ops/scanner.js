/**
 * GoPass SGI-GP Scanner Logic
 * Extracted from templates/ops/scanner.html
 */

let scannerConfig = {};
let currentFlightId = null;
let html5QrcodeScanner = null;
let isScanning = false;
let pendingScans = JSON.parse(localStorage.getItem('pendingScans') || '[]');

// DOM Elements (Cached after init)
let els = {};

function initScanner(config) {
    scannerConfig = config;

    // Cache DOM Elements
    els = {
        setupScreen: document.getElementById('setup-screen'),
        scanScreen: document.getElementById('scan-screen'),
        flightSelect: document.getElementById('flight_select'),
        startBtn: document.getElementById('start-btn'),
        currentFlightDisplay: document.getElementById('current-flight-display'),
        laserInput: document.getElementById('laser-input'),
        feedbackScreen: document.getElementById('feedback-screen'),
        offlineIndicator: document.getElementById('offline-indicator'),
        pendingCountFn: document.getElementById('pending-count'),
        changeFlightBtn: document.getElementById('change-flight-btn'),
        cameraToggle: document.getElementById('camera-toggle'),
        scanStatus: document.getElementById('scan-status'),
        feedbackIcon: document.getElementById('feedback-icon'),
        feedbackTitle: document.getElementById('feedback-title'),
        feedbackMessage: document.getElementById('feedback-message'),
        feedbackDetails: document.getElementById('feedback-details'),
        syncBtn: document.getElementById('sync-btn'),
        scannerSetupLogo: document.getElementById('scanner-setup-logo'),
        scannerHeaderLogo: document.getElementById('scanner-header-logo')
    };

    // Attach Event Listeners
    attachEventListeners();

    // Initial Sync Check
    if (navigator.onLine) {
        syncScans();
    }
    updateOfflineUI();

    // Branding Load
    loadBranding();
}

function attachEventListeners() {
    els.flightSelect.addEventListener('change', () => {
        if (els.flightSelect.value) {
            els.startBtn.disabled = false;
            els.startBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    });

    els.startBtn.addEventListener('click', () => {
        currentFlightId = els.flightSelect.value;
        const flightText = els.flightSelect.options[els.flightSelect.selectedIndex].getAttribute('data-info');
        els.currentFlightDisplay.textContent = flightText;

        els.setupScreen.classList.add('hidden');
        els.scanScreen.classList.remove('hidden');

        // Focus laser input
        els.laserInput.focus();

        // Update offline UI
        updateOfflineUI();
    });

    els.changeFlightBtn.addEventListener('click', () => {
        if (html5QrcodeScanner) stopCamera();
        els.scanScreen.classList.add('hidden');
        els.setupScreen.classList.remove('hidden');
        currentFlightId = null;
    });

    // Laser Scanner Logic (Keyboard)
    document.addEventListener('click', () => {
        if (!els.scanScreen.classList.contains('hidden') && els.feedbackScreen.classList.contains('hidden')) {
            els.laserInput.focus();
        }
    });

    // Prevent loss of focus
    els.laserInput.addEventListener('blur', () => {
         if (!els.scanScreen.classList.contains('hidden')) {
             setTimeout(() => els.laserInput.focus(), 100);
         }
    });

    els.laserInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const token = els.laserInput.value.trim();
            els.laserInput.value = '';
            if (token) processScan(token);
        }
    });

    // Camera Logic
    els.cameraToggle.addEventListener('click', () => {
        if (isScanning) {
            stopCamera();
        } else {
            startCamera();
        }
    });

    if(els.syncBtn) {
        els.syncBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            syncScans();
        });
    }

    window.addEventListener('online', () => {
         updateOfflineUI();
         syncScans();
    });

    window.addEventListener('offline', updateOfflineUI);
}

function startCamera() {
    html5QrcodeScanner = new Html5Qrcode("reader");
    const config = { fps: 10, qrbox: { width: 250, height: 250 } };

    html5QrcodeScanner.start({ facingMode: "environment" }, config, onScanSuccess)
    .then(() => {
        isScanning = true;
        els.scanStatus.textContent = "Caméra active";
    })
    .catch(err => {
        console.error("Erreur caméra", err);
        alert("Impossible d'accéder à la caméra");
    });
}

function stopCamera() {
    if (html5QrcodeScanner) {
        html5QrcodeScanner.stop().then(() => {
            html5QrcodeScanner.clear();
            isScanning = false;
            els.scanStatus.textContent = "Prêt à scanner (Caméra ou Laser)";
        });
    }
}

function onScanSuccess(decodedText, decodedResult) {
    processScan(decodedText);
}

// Processing Logic
async function processScan(token) {
    if (els.feedbackScreen.classList.contains('block')) return; // Already showing result

    // Check connectivity
    if (!navigator.onLine) {
        storeOfflineScan(token);
        showFeedback('offline', { message: 'Scan enregistré hors-ligne', token: token });
        return;
    }

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': scannerConfig.csrfToken
            },
            body: JSON.stringify({
                token: token,
                flight_id: currentFlightId,
                location: scannerConfig.userLocation
            })
        });

        const data = await response.json();
        showFeedback(data.code, data);

    } catch (error) {
        console.error(error);
        // Fallback to offline store if network error
        storeOfflineScan(token);
        showFeedback('offline', { message: 'Erreur réseau - Enregistré', token: token });
    }
}

// Feedback Logic
function showFeedback(code, data) {
    const screen = els.feedbackScreen;
    const trans = scannerConfig.trans;

    screen.classList.remove('hidden', 'bg-green-600', 'bg-red-600', 'bg-orange-500', 'bg-gray-800', 'animate-pulse');
    screen.classList.add('flex'); // Enable flex

    let colorClass = 'bg-gray-800';

    // Reset content
    els.feedbackDetails.innerHTML = '';

    switch(code) {
        case 'VALID':
            colorClass = 'bg-green-600';
            els.feedbackIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
            els.feedbackTitle.textContent = trans.status_valid;
            els.feedbackMessage.textContent = data.data.passenger || trans.bon_voyage;

            if(data.data) {
                els.feedbackDetails.innerHTML = `
                    <div class="mt-4 border-t border-white/20 pt-4">
                        <p class="text-sm opacity-75">${trans.document}:</p>
                        <p class="font-bold text-lg">${data.data.document_type || 'Passeport'}</p>
                        <p class="font-mono text-xl">${data.data.passport || '---'}</p>
                    </div>
                `;
            }
            break;
        case 'ALREADY_SCANNED':
            colorClass = 'bg-red-600 animate-pulse';
            els.feedbackIcon.innerHTML = '<i class="fas fa-hand-paper"></i>';
            els.feedbackTitle.textContent = trans.status_fraud;
            els.feedbackMessage.textContent = trans.already_scanned_msg;

            if (data.data && data.data.original_scan) {
                els.feedbackDetails.innerHTML = `
                    <div class="bg-white/10 p-4 rounded text-center">
                        <p class="text-yellow-300 font-bold uppercase text-sm mb-2">${trans.first_scan}</p>
                        <p class="text-2xl font-mono font-bold mb-1">${data.data.original_scan.scan_date.split(' ')[1] || data.data.original_scan.scan_date}</p>
                        <p class="text-sm">${data.data.original_scan.scan_date.split(' ')[0] || ''}</p>
                        <hr class="border-white/20 my-2">
                        <p class="text-xs uppercase opacity-75">${trans.by}</p>
                        <p class="font-bold">${data.data.original_scan.scanned_by}</p>
                        <p class="text-xs uppercase opacity-75 mt-1">${trans.location}</p>
                        <p class="font-bold">${data.data.original_scan.location || 'Unknown'}</p>
                    </div>
                `;
            }
            break;
        case 'WRONG_FLIGHT':
            colorClass = 'bg-orange-500';
            els.feedbackIcon.innerHTML = '<i class="fas fa-plane-slash"></i>';
            els.feedbackTitle.textContent = trans.status_wrong_flight;

            if (data.data && data.data.valid_for) {
                els.feedbackMessage.textContent = `${trans.redirect_instruction} ${data.data.valid_for}. Redirigez-le.`;
                els.feedbackDetails.innerHTML = `
                    <div class="mt-2 text-center">
                        <p class="text-sm opacity-75">${trans.flight_ticket}</p>
                        <p class="text-3xl font-bold">${data.data.valid_for}</p>
                        <p class="text-lg">${data.data.date}</p>
                    </div>
                `;
            } else {
                els.feedbackMessage.textContent = trans.wrong_flight_msg;
            }
            break;
        case 'EXPIRED':
            colorClass = 'bg-red-600';
            els.feedbackIcon.innerHTML = '<i class="fas fa-calendar-times"></i>';
            els.feedbackTitle.textContent = trans.status_expired;
            els.feedbackMessage.textContent = trans.expired_msg;

            if (data.data) {
                els.feedbackDetails.innerHTML = `
                    <div class="grid grid-cols-2 gap-4 text-center mt-2">
                        <div>
                            <p class="text-xs opacity-75">${trans.date} (Billet)</p>
                            <p class="text-xl font-bold text-red-300">${data.data.valid_for_date}</p>
                        </div>
                        <div>
                            <p class="text-xs opacity-75">${trans.date_expected}</p>
                            <p class="text-xl font-bold text-green-300">${data.data.expected_date}</p>
                        </div>
                    </div>
                    <div class="mt-4 text-center">
                        <p class="text-sm opacity-75">${trans.flight_ticket}</p>
                        <p class="text-2xl font-bold">${data.data.flight}</p>
                    </div>
                `;
            }
            break;
        case 'INVALID':
        case 'FLIGHT_CLOSED':
            colorClass = 'bg-red-600';
            els.feedbackIcon.innerHTML = '<i class="fas fa-times-circle"></i>';
            els.feedbackTitle.textContent = trans.status_invalid;
            els.feedbackMessage.textContent = data.message || trans.invalid_doc;
            break;
        case 'offline':
            colorClass = 'bg-blue-600';
            els.feedbackIcon.innerHTML = '<i class="fas fa-save"></i>';
            els.feedbackTitle.textContent = trans.status_registered;
            els.feedbackMessage.textContent = trans.offline_msg;
            break;
        default:
            colorClass = 'bg-red-600';
            els.feedbackIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            els.feedbackTitle.textContent = trans.status_error;
            els.feedbackMessage.textContent = data.message || trans.system_error;
    }

    // Safe add for multiple classes
    colorClass.split(' ').forEach(cls => screen.classList.add(cls));

    // Wait for user to dismiss
    screen.onclick = () => {
        screen.classList.add('hidden');
        screen.classList.remove('flex');
        els.laserInput.focus();
    };
}

// Offline / Sync Logic
function storeOfflineScan(token) {
    const scan = {
        token: token,
        flight_id: currentFlightId,
        timestamp: new Date().toISOString()
    };
    pendingScans.push(scan);
    localStorage.setItem('pendingScans', JSON.stringify(pendingScans));
    updateOfflineUI();
}

function updateOfflineUI() {
    els.pendingCountFn.textContent = pendingScans.length;
    if (pendingScans.length > 0 || !navigator.onLine) {
        els.offlineIndicator.classList.remove('hidden');
    } else {
        els.offlineIndicator.classList.add('hidden');
    }
}

async function syncScans() {
    if (pendingScans.length === 0 || !navigator.onLine) return;

    if(els.syncBtn) els.syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    const scansToSync = [...pendingScans];
    const remainingScans = [];

    for (const scan of scansToSync) {
        try {
            await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': scannerConfig.csrfToken
                },
                body: JSON.stringify({
                    token: scan.token,
                    flight_id: scan.flight_id,
                    location: scannerConfig.userLocation
                })
            });
        } catch (e) {
            console.error("Sync failed for one item", e);
            remainingScans.push(scan);
        }
    }

    pendingScans = remainingScans;
    localStorage.setItem('pendingScans', JSON.stringify(pendingScans));
    updateOfflineUI();

    if(els.syncBtn) els.syncBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
}

function loadBranding() {
    fetch('/api/settings/public')
        .then(r => r.json())
        .then(data => {
            if (data.rva_logo) {
                els.scannerSetupLogo.src = data.rva_logo;
                els.scannerSetupLogo.classList.remove('hidden');

                els.scannerHeaderLogo.src = data.rva_logo;
                els.scannerHeaderLogo.classList.remove('hidden');
            }
        })
        .catch(console.error);
}

// Export for usage (optional, but good practice if using modules)
// window.initScanner = initScanner;
