/**
 * GoPass SGI-GP Dashboard Logic
 * Extracted from templates/dashboard/index.html
 */

function initDashboardCharts(trans, auditData, financialData) {
    // --- Audit Gap Analysis Chart ---
    const auditCtx = document.getElementById('auditChart').getContext('2d');

    const labels = auditData.map(d => d.flight_number);
    const declaredData = auditData.map(d => d.declared);
    const scannedData = auditData.map(d => d.scanned);

    // Determine background colors dynamically: Red if scanned > declared, else Green
    const scannedColors = auditData.map(d => d.alert ? 'rgba(239, 68, 68, 0.8)' : 'rgba(16, 185, 129, 0.8)');
    const scannedBorders = auditData.map(d => d.alert ? 'rgb(239, 68, 68)' : 'rgb(16, 185, 129)');

    new Chart(auditCtx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: trans.declared,
                    data: declaredData,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
                },
                {
                    label: trans.scanned,
                    data: scannedData,
                    backgroundColor: scannedColors,
                    borderColor: scannedBorders,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            if (context.datasetIndex === 1 && auditData[context.dataIndex].alert) {
                                return trans.alert;
                            }
                        }
                    }
                }
            }
        }
    });

    // --- Financial Pie Chart ---
    const revenueCtx = document.getElementById('revenueChart').getContext('2d');

    new Chart(revenueCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(financialData),
            datasets: [{
                data: Object.values(financialData),
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)', // Cash (Red - risky)
                    'rgba(16, 185, 129, 0.8)' // Mobile Money (Green - safe)
                ],
                borderColor: [
                    'rgb(239, 68, 68)',
                    'rgb(16, 185, 129)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}
