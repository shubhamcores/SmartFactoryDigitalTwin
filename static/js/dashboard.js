/**
 * FactoryTwin (P_307) - Central SCADA Dashboard Controller
 * Real-time asynchronous polling, Chart.js telemetry visualization,
 * digital twin status updates, and interactive alert management.
 */

const MACHINE_COLORS = {
    "Motor": "#3b82f6",     // Blue
    "Conveyor": "#10b981",  // Emerald
    "Pump": "#06b6d4",      // Cyan
    "CNC": "#f59e0b"        // Amber
};

const MAX_HISTORY_POINTS = 20;

// Chart Instances
let chartTemp, chartVib, chartSpeed, chartProd;

// Telemetry Time-Series Buffers
const timeLabels = [];
const telemetryBuffers = {
    "Motor": { temp: [], vib: [], speed: [], prod: [] },
    "Conveyor": { temp: [], vib: [], speed: [], prod: [] },
    "Pump": { temp: [], vib: [], speed: [], prod: [] },
    "CNC": { temp: [], vib: [], speed: [], prod: [] }
};

document.addEventListener("DOMContentLoaded", () => {
    initCharts();
    fetchDashboardTelemetry();
    fetchRecentAlerts();

    // Auto-refresh interval (every 3 seconds)
    setInterval(fetchDashboardTelemetry, 3000);
    setInterval(fetchRecentAlerts, 4000);
});

function initCharts() {
    const commonChartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        plugins: {
            legend: {
                labels: { color: "#94a3b8", font: { size: 10, family: "inherit" }, boxWidth: 12 }
            },
            tooltip: {
                backgroundColor: "#0f172a",
                titleColor: "#f8fafc",
                bodyColor: "#94a3b8",
                borderColor: "#334155",
                borderWidth: 1
            }
        },
        scales: {
            x: {
                grid: { color: "rgba(51, 65, 85, 0.4)" },
                ticks: { color: "#64748b", font: { size: 9 }, maxTicksLimit: 8 }
            },
            y: {
                grid: { color: "rgba(51, 65, 85, 0.4)" },
                ticks: { color: "#94a3b8", font: { size: 9 } }
            }
        }
    };

    const makeDatasets = (metricKey) => {
        return Object.keys(MACHINE_COLORS).map(mId => ({
            label: mId,
            data: telemetryBuffers[mId][metricKey],
            borderColor: MACHINE_COLORS[mId],
            backgroundColor: MACHINE_COLORS[mId],
            borderWidth: 2,
            pointRadius: 2,
            tension: 0.3
        }));
    };

    // 1. Temperature Chart
    const ctxTemp = document.getElementById("chart-temperature");
    if (ctxTemp) {
        chartTemp = new Chart(ctxTemp, {
            type: "line",
            data: { labels: timeLabels, datasets: makeDatasets("temp") },
            options: commonChartOptions
        });
    }

    // 2. Vibration Chart
    const ctxVib = document.getElementById("chart-vibration");
    if (ctxVib) {
        chartVib = new Chart(ctxVib, {
            type: "line",
            data: { labels: timeLabels, datasets: makeDatasets("vib") },
            options: commonChartOptions
        });
    }

    // 3. Speed Chart
    const ctxSpeed = document.getElementById("chart-speed");
    if (ctxSpeed) {
        chartSpeed = new Chart(ctxSpeed, {
            type: "line",
            data: { labels: timeLabels, datasets: makeDatasets("speed") },
            options: commonChartOptions
        });
    }

    // 4. Production Chart
    const ctxProd = document.getElementById("chart-production");
    if (ctxProd) {
        chartProd = new Chart(ctxProd, {
            type: "line",
            data: { labels: timeLabels, datasets: makeDatasets("prod") },
            options: commonChartOptions
        });
    }
}

async function fetchDashboardTelemetry() {
    try {
        const res = await fetch("/api/telemetry/latest");
        if (!res.ok) return;

        const data = await res.json();
        const telemetryList = data.telemetry || [];
        const simRunning = data.simulator_running;
        const nowTime = new Date().toLocaleTimeString();

        // Update Simulator Pulse Pill
        const pulseDot = document.getElementById("simulator-pulse");
        const statusText = document.getElementById("simulator-status-text");
        if (pulseDot && statusText) {
            if (simRunning) {
                pulseDot.className = "status-dot status-dot-pulse bg-success";
                statusText.textContent = "Digital Twin Engine: Active";
            } else {
                pulseDot.className = "status-dot bg-danger";
                statusText.textContent = "Digital Twin Engine: Stopped";
            }
        }

        const lastSync = document.getElementById("last-updated-time");
        if (lastSync) lastSync.textContent = nowTime;

        let runningCount = 0;
        let warningCount = 0;
        let stoppedCount = 0;
        let lastSource = "SIMULATED";

        // Push time label
        if (telemetryList.length > 0) {
            timeLabels.push(nowTime);
            if (timeLabels.length > MAX_HISTORY_POINTS) timeLabels.shift();
        }

        telemetryList.forEach(item => {
            const mId = item.machine_id;
            lastSource = item.data_source || "SIMULATED";

            // Count statuses
            const st = (item.status || "RUNNING").toUpperCase();
            if (st === "RUNNING") runningCount++;
            else if (st === "WARNING" || st === "IDLE") warningCount++;
            else stoppedCount++;

            // Update DOM Card Elements
            updateElementText(`val-temp-${mId}`, item.temperature?.toFixed(1));
            updateElementText(`val-vib-${mId}`, item.vibration?.toFixed(2));
            updateElementText(`val-rpm-${mId}`, Math.round(item.speed));
            updateElementText(`val-load-${mId}`, item.load?.toFixed(0));
            updateElementText(`val-prod-${mId}`, item.production_count);

            // Update Status Badge
            const badge = document.getElementById(`badge-status-${mId}`);
            if (badge) {
                badge.textContent = st;
                badge.className = `badge-scada badge-scada-${st.toLowerCase()}`;
            }

            // Update Machine Source Badge
            const srcBadge = document.getElementById(`badge-source-${mId}`);
            if (srcBadge) {
                if (item.data_source === "ESP32_EDGE") {
                    srcBadge.textContent = "ESP32";
                    srcBadge.className = "badge bg-success text-white font-monospace";
                } else if (item.data_source === "MQTT_LIVE") {
                    srcBadge.textContent = "MQTT";
                    srcBadge.className = "badge bg-info text-dark font-monospace";
                } else {
                    srcBadge.textContent = "SIM";
                    srcBadge.className = "badge bg-dark border border-secondary text-info font-monospace";
                }
            }

            // Update AI Risk Gauge
            const riskScore = item.anomaly_score ?? 15.0;
            const riskCategory = item.risk_category || "LOW";
            const detectionMethod = item.detection_method === "RULE_BASED_FALLBACK" ? "Rule Engine" : "Isolation Forest";

            updateElementText(`val-risk-score-${mId}`, riskScore.toFixed(1));
            updateElementText(`val-risk-method-${mId}`, detectionMethod);

            const riskBadge = document.getElementById(`badge-risk-${mId}`);
            if (riskBadge) {
                riskBadge.textContent = riskCategory;
                riskBadge.className = `badge bg-${getRiskColorClass(riskCategory)}`;
            }

            const riskBar = document.getElementById(`risk-bar-${mId}`);
            if (riskBar) {
                riskBar.style.width = `${Math.min(100, Math.max(5, riskScore))}%`;
                riskBar.className = `risk-bar risk-bar-${riskCategory.toLowerCase()}`;
            }

            // Append to Chart Buffers
            if (telemetryBuffers[mId]) {
                const b = telemetryBuffers[mId];
                b.temp.push(item.temperature);
                b.vib.push(item.vibration);
                b.speed.push(item.speed);
                b.prod.push(item.production_count);

                if (b.temp.length > MAX_HISTORY_POINTS) {
                    b.temp.shift();
                    b.vib.shift();
                    b.speed.shift();
                    b.prod.shift();
                }
            }
        });

        // Update KPIs
        updateElementText("kpi-running-machines", runningCount);
        updateElementText("kpi-warning-machines", warningCount);
        updateElementText("kpi-stopped-machines", stoppedCount);
        updateElementText("kpi-data-source", lastSource);

        const navSource = document.getElementById("nav-data-source");
        if (navSource) {
            navSource.textContent = lastSource;
            navSource.className = lastSource === "MQTT_LIVE" ? "badge bg-success text-white" : "badge bg-primary text-white";
        }

        // Update Charts
        if (chartTemp) chartTemp.update("none");
        if (chartVib) chartVib.update("none");
        if (chartSpeed) chartSpeed.update("none");
        if (chartProd) chartProd.update("none");

    } catch (err) {
        console.error("Dashboard telemetry sync error:", err);
    }
}

async function fetchRecentAlerts() {
    try {
        const res = await fetch("/api/alerts?limit=6");
        if (!res.ok) return;

        const data = await res.json();
        const alerts = data.alerts || [];
        const tbody = document.getElementById("recent-alerts-tbody");
        if (!tbody) return;

        // Update KPI active alerts
        const kpiAlerts = document.getElementById("kpi-active-alerts");
        if (kpiAlerts && data.statistics) {
            kpiAlerts.textContent = data.statistics.new || 0;
        }

        if (alerts.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-secondary py-3"><i class="bi bi-shield-check text-success me-1"></i> All machinery operating within nominal parameters. Zero active alerts.</td></tr>`;
            return;
        }

        tbody.innerHTML = alerts.map(a => {
            const sevBadge = a.severity === "CRITICAL" ? "bg-danger" : (a.severity === "WARNING" ? "bg-warning text-dark" : "bg-info text-dark");
            const statusBadge = a.status === "NEW" ? "bg-danger" : (a.status === "ACKNOWLEDGED" ? "bg-warning text-dark" : "bg-success");
            const isNew = a.status === "NEW";

            return `
                <tr>
                    <td><span class="badge ${sevBadge}">${a.severity}</span></td>
                    <td class="fw-semibold text-white font-monospace">${a.machine_id}</td>
                    <td class="small text-secondary">${a.alert_type.replace(/_/g, " ")}</td>
                    <td class="small text-light">${a.message}</td>
                    <td class="small text-secondary font-monospace">${a.timestamp}</td>
                    <td><span class="badge ${statusBadge}">${a.status}</span></td>
                    <td>
                        ${isNew ? `
                            <button onclick="acknowledgeAlert(${a.id})" class="btn btn-sm btn-outline-warning py-0 px-2" style="font-size: 0.72rem;">
                                Acknowledge
                            </button>
                        ` : `<span class="text-secondary small">Acknowledged</span>`}
                    </td>
                </tr>
            `;
        }).join("");

    } catch (err) {
        console.error("Failed to load alerts feed:", err);
    }
}

async function acknowledgeAlert(alertId) {
    try {
        const res = await fetch(`/api/alerts/${alertId}/acknowledge`, { method: "POST" });
        const data = await res.json();
        if (data.success) {
            fetchRecentAlerts();
        }
    } catch (e) {
        console.error("Failed to acknowledge alert:", e);
    }
}

function updateElementText(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) {
        el.textContent = val;
    }
}

function getRiskColorClass(cat) {
    switch (cat.toUpperCase()) {
        case "CRITICAL": return "danger";
        case "HIGH": return "warning text-dark";
        case "MEDIUM": return "warning text-dark";
        default: return "success";
    }
}
