// Extracted from validation/scan.html

const video = document.getElementById('scanner-video');
    const startBtn = document.getElementById('start-scanner');
    const stopBtn = document.getElementById('stop-scanner');
    const locationInput = document.getElementById('scan-location');
    const scanResult = document.getElementById('scan-result');
    const scanResultContent = document.getElementById('scan-result-content');

    let codeReader = null;

    async function startScanner() {
        try {
            codeReader = new ZXing.BrowserQRCodeReader();
            const devices = await codeReader.getVideoInputDevices();

            if (devices.length === 0) {
                alert('Aucune camera detectee');
                return;
            }

            startBtn.classList.add('hidden');
            stopBtn.classList.remove('hidden');

            codeReader.decodeFromVideoDevice(devices[0].deviceId, video, async (result, err) => {
                if (result) {
                    stopScanner();
                    await validateScannedCode(result.text);
                }
            });
        } catch (error) {
            alert('Erreur d\'acces a la camera: ' + error.message);
        }
    }

    function stopScanner() {
        if (codeReader) {
            codeReader.reset();
        }
        startBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
    }

    async function validateScannedCode(passNumber) {
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
            showScanResult(result);
        } catch (error) {
            showScanResult({ valid: false, status: 'error', message: 'Erreur de connexion' });
        }
    }

    function showScanResult(result) {
        scanResult.classList.remove('hidden');

        if (result.valid) {
            scanResultContent.innerHTML = `
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
            scanResultContent.innerHTML = `
                <div class="bg-red-100 border-2 border-red-500 rounded-xl p-6 text-center">
                    <i class="fas fa-times-circle text-6xl text-red-500 mb-4"></i>
                    <h3 class="text-2xl font-bold text-red-800">ACCES REFUSE</h3>
                    <p class="mt-4 text-lg text-red-700">${result.message}</p>
                </div>
            `;
        }

        setTimeout(() => {
            scanResult.classList.add('hidden');
            startScanner();
        }, 3000);
    }

    startBtn.addEventListener('click', startScanner);
    stopBtn.addEventListener('click', stopScanner);