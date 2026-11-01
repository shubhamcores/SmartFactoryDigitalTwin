/**
 * FactoryTwin (P_307) - Individual Machine Digital Twin Inspector
 * High-resolution multi-sensor tracking, anomaly risk profiling, and maintenance log feed.
 */

let detailChart;
const historyLabels = [];
const seriesTemp = [];
const seriesVib = [];
const seriesSpeed = [];
const seriesLoad = [];

document.addEventListener("DOMContentLoaded", () => {
    initDetailChart();
    loadMachineHistory();
    setInterval(pollLiveMachineTelemetry, 3000);
});

function initDetailChart() {
    const ctx = document.getElementById("machine-detail-chart");
    if (!ctx) return;

    detailChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: historyLabels,
            datasets: [
                {
                    label: "Temp (°C)",
                    data: seriesTemp,
                    borderColor: "#f59e0b",
                    backgroundColor: "#f59e0b",
                    borderWidth: 2,
                    pointRadius: 2,
                    tension: 0.25,
                    yAxisID: "yTemp"
                },
                {
                    label: "Vib (mm/s)",
                    data: seriesVib,
                    borderColor: "#06b6d4",
                    backgroundColor: "#06b6d4",
                    borderWidth: 2,
                    pointRadius: 2,
                    tension: 0.25,
                    yAxisID: "yVib"
                },
                {
                    label: "Load (%)",
                    data: seriesLoad,
                    borderColor: "#10b981",
                    backgroundColor: "#10b981",
                    borderWidth: 2,
                    pointRadius: 2,
                    tension: 0.25,
                    yAxisID: "yLoad"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "#94a3b8", font: { size: 10 } } },
                tooltip: {
                    backgroundColor: "#0f172a",
                    titleColor: "#f8fafc",
                    borderColor: "#334155",
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(51, 65, 85, 0.4)" },
                    ticks: { color: "#64748b", font: { size: 9 }, maxTicksLimit: 8 }
                },
                yTemp: {
                    type: "linear",
                    display: true,
                    position: "left",
                    grid: { color: "rgba(51, 65, 85, 0.4)" },
                    ticks: { color: "#f59e0b", font: { size: 9 } },
                    title: { display: true, text: "Temp (°C)", color: "#f59e0b", font: { size: 10 } }
                },
                yVib: {
                    type: "linear",
                    display: true,
                    position: "right",
                    grid: { drawOnChartArea: false },
                    ticks: { color: "#06b6d4", font: { size: 9 } },
                    title: { display: true, text: "Vibration (mm/s)", color: "#06b6d4", font: { size: 10 } }
                },
                yLoad: {
                    type: "linear",
                    display: false,
                    position: "right",
                    grid: { drawOnChartArea: false },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

async function loadMachineHistory() {
    try {
        const res = await fetch(`/api/telemetry/history/${CURRENT_MACHINE_ID}?limit=20`);
        if (!res.ok) return;

        const data = await res.json();
        const records = (data.history || []).reverse();

        historyLabels.length = 0;
        seriesTemp.length = 0;
        seriesVib.length = 0;
        seriesSpeed.length = 0;
        seriesLoad.length = 0;

        records.forEach(r => {
            const timeStr = r.timestamp ? r.timestamp.split(" ")[1] : "";
            historyLabels.push(timeStr);
            seriesTemp.push(r.temperature);
            seriesVib.push(r.vibration);
            seriesSpeed.push(r.speed);
            seriesLoad.push(r.load);
        });

        if (detailChart) detailChart.update();
        if (records.length > 0) {
            updateLiveCards(records[records.length - 1]);
        }
    } catch (e) {
        console.error("Failed to fetch machine history:", e);
    }
}

async function pollLiveMachineTelemetry() {
    try {
        const res = await fetch("/api/telemetry/latest");
        if (!res.ok) return;

        const data = await res.json();
        const list = data.telemetry || [];
        const current = list.find(item => item.machine_id === CURRENT_MACHINE_ID);

        if (current) {
            updateLiveCards(current);

            const timeStr = new Date().toLocaleTimeString();
            historyLabels.push(timeStr);
            seriesTemp.push(current.temperature);
            seriesVib.push(current.vibration);
            seriesSpeed.push(current.speed);
            seriesLoad.push(current.load);

            if (historyLabels.length > 25) {
                historyLabels.shift();
                seriesTemp.shift();
                seriesVib.shift();
                seriesSpeed.shift();
                seriesLoad.shift();
            }

            if (detailChart) detailChart.update("none");
        }

        // Refresh recent anomalies list
        fetchRecentMachineAnomalies();
    } catch (e) {
        console.error("Error polling machine detail:", e);
    }
}

function updateLiveCards(rec) {
    setText("dt-temp", rec.temperature?.toFixed(1));
    setText("dt-vib", rec.vibration?.toFixed(3));
    setText("dt-rpm", Math.round(rec.speed));
    setText("dt-load", rec.load?.toFixed(0));

    // Status Badge
    const stBadge = document.getElementById("detail-machine-status");
    if (stBadge) {
        const st = (rec.status || "RUNNING").toUpperCase();
        stBadge.textContent = st;
        stBadge.className = `badge-scada badge-scada-${st.toLowerCase()}`;
    }

    // AI Anomaly Metrics
    const score = rec.anomaly_score ?? 12.0;
    const cat = (rec.risk_category || "LOW").toUpperCase();
    const action = rec.suggested_action || "Telemetry operating within certified statistical envelope.";
    const method = rec.detection_method === "RULE_BASED_FALLBACK" ? "RULE-BASED DETERMINISTIC" : "ISOLATION FOREST (UNSUPERVISED)";

    setText("dt-ai-score", score.toFixed(1));
    setText("dt-ai-method", method);

    const actionBox = document.getElementById("dt-ai-action");
    if (actionBox) {
        const icon = cat === "CRITICAL" ? "bi-exclamation-octagon-fill text-danger" : (cat === "HIGH" ? "bi-exclamation-triangle-fill text-warning" : "bi-check-circle-fill text-success");
        actionBox.innerHTML = `<i class="bi ${icon} me-2"></i> ${action}`;
    }

    const catBadge = document.getElementById("dt-ai-category");
    if (catBadge) {
        catBadge.textContent = `${cat} RISK`;
        catBadge.className = `badge bg-${getRiskColorClass(cat)} px-3 py-1`;
    }

    const bar = document.getElementById("dt-ai-bar");
    if (bar) {
        bar.style.width = `${Math.min(100, Math.max(5, score))}%`;
        bar.className = `risk-bar risk-bar-${cat.toLowerCase()}`;
    }
}

async function fetchRecentMachineAnomalies() {
    try {
        const res = await fetch(`/api/anomalies/${CURRENT_MACHINE_ID}?limit=6`);
        if (!res.ok) return;

        const data = await res.json();
        const anomalies = data.anomalies || [];
        const tbody = document.getElementById("dt-anomalies-tbody");
        if (!tbody) return;

        if (anomalies.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-secondary py-3">No anomalous events recorded for this asset.</td></tr>`;
            return;
        }

        tbody.innerHTML = anomalies.map(a => {
            const riskClass = getRiskColorClass(a.risk_category);
            return `
                <tr>
                    <td class="small text-secondary font-monospace">${a.timestamp}</td>
                    <td class="small text-white font-monospace">${a.anomaly_score.toFixed(1)}</td>
                    <td><span class="badge bg-${riskClass}" style="font-size: 0.65rem;">${a.risk_category}</span></td>
                    <td class="small text-light">${a.suggested_action || "Operational drift"}</td>
                </tr>
            `;
        }).join("");
    } catch (e) {
        console.error("Failed to load anomalies log:", e);
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.textContent = val;
}

function getRiskColorClass(cat) {
    switch (cat.toUpperCase()) {
        case "CRITICAL": return "danger";
        case "HIGH": return "warning text-dark";
        case "MEDIUM": return "warning text-dark";
        default: return "success";
    }
}
