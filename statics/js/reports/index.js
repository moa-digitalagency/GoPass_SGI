/**
 * GoPass SGI-GP Reports Logic
 * Extracted from templates/reports/index.html
 */

function initReportCharts(auditData, revenueData, heatmapData) {
    // 1. Audit Chart (Grouped Bar)
    const ctxAudit = document.getElementById('auditChart').getContext('2d');

    const auditLabels = auditData.map(d => d.flight_number);
    const manifestCounts = auditData.map(d => d.manifest);
    const scannedCounts = auditData.map(d => d.scanned);

    // Determine colors for scanned bars (Red if Scanned > Manifest)
    const scannedColors = auditData.map(d => d.alert ? 'rgba(239, 68, 68, 0.8)' : 'rgba(16, 185, 129, 0.8)');

    new Chart(ctxAudit, {
        type: 'bar',
        data: {
            labels: auditLabels,
            datasets: [
                {
                    label: 'Manifeste (Déclarés)',
                    data: manifestCounts,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Scannés (Réels)',
                    data: scannedCounts,
                    backgroundColor: scannedColors,
                    borderColor: scannedColors.map(c => c.replace('0.8', '1')),
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // 2. Revenue Chart (Donut)
    const ctxRevenue = document.getElementById('revenueChart').getContext('2d');
    const revLabels = Object.keys(revenueData);
    const revValues = Object.values(revenueData);
    const revColors = ['#10B981', '#F59E0B', '#3B82F6', '#EF4444']; // Colors for segments

    new Chart(ctxRevenue, {
        type: 'doughnut',
        data: {
            labels: revLabels,
            datasets: [{
                data: revValues,
                backgroundColor: revColors,
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

    // 3. Heatmap (Map)
    // Initialize map centered on DRC
    const map = L.map('map').setView([-2.9, 23.8], 5); // Approximate center of DRC

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Add circles for heatmap data
    heatmapData.forEach(point => {
        // Radius based on count (scaled)
        const radius = Math.max(point.count * 20000, 50000);

        L.circle([point.lat, point.lng], {
            color: 'red',
            fillColor: '#f03',
            fillOpacity: 0.5,
            radius: radius
        }).addTo(map)
        .bindPopup(`<b>${point.name}</b><br>Billets émis (24h): ${point.count}`);
    });

    // Workaround for map rendering issues in tabs/hidden divs (resize)
    setTimeout(() => { map.invalidateSize(); }, 100);
}
