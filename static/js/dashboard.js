/* ═══════════════════════════════════════════════
   TrustCheck AI — Dashboard JS v2
   Glassmorphism / Neon Dashboard
═══════════════════════════════════════════════ */

let metricsData = null;
let summaryData = null;
let historyData = null;

/* ─── Helpers ─── */
function toPercent(value) {
  if (value === undefined || value === null || value === "" || isNaN(Number(value))) return null;
  const n = Number(value);
  return n <= 1 ? (n * 100).toFixed(1) : Number(n).toFixed(1);
}

function metricValue(value) {
  const n = Number(value || 0);
  return n <= 1 ? n * 100 : n;
}

function animateNumber(el, target, duration = 900) {
  const start = 0;
  const startTime = performance.now();
  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ─── Summary Cards ─── */
function renderSummary(data) {
  const fields = [
    { id: "sum-total", key: "total" },
    { id: "sum-reliable", key: "reliable" },
    { id: "sum-suspicious", key: "suspicious" },
    { id: "sum-unreliable", key: "unreliable" },
  ];

  fields.forEach(({ id, key }) => {
    const el = document.getElementById(id);
    if (!el) return;
    const val = data[key] || 0;
    if (val === 0) {
      el.textContent = "0";
    } else {
      animateNumber(el, val);
    }
  });
}

/* ─── Model Performance Cards ─── */
function renderModelPerformance(metrics) {
  const grid = document.getElementById("model-perf-grid");
  if (!grid) return;

  const models = [
    { key: "lr", name: "Logistic Regression", icon: "🤖", color: "#4e7cff", glow: "rgba(78,124,255,.25)" },
    { key: "nb", name: "Naive Bayes", icon: "🧠", color: "#a855f7", glow: "rgba(168,85,247,.25)" },
    { key: "svm", name: "Linear SVM", icon: "⚡", color: "#00d4ff", glow: "rgba(0,212,255,.25)" },
  ];

  grid.innerHTML = models.map((model, i) => {
    const m = metrics[model.key] || {};
    const accuracy = toPercent(m.accuracy);
    const precision = toPercent(m.precision);
    const recall = toPercent(m.recall);
    const f1 = toPercent(m.f1 || m.f1_score);

    return `
      <div class="glass-card model-card" style="animation-delay:${i * 0.1}s;--card-accent:${model.color};--card-glow:${model.glow};">
        <div class="model-card-header">
          <div class="model-card-icon" style="background:linear-gradient(135deg,${model.color}22,${model.color}11);border:1px solid ${model.color}44;">
            <span>${model.icon}</span>
          </div>
          <div>
            <h3 class="model-card-name">${model.name}</h3>
            <p class="model-card-sub">Mô hình phân loại tin tức</p>
          </div>
        </div>
        <div class="model-metrics-grid">
          ${renderMetricMini("ACCURACY", accuracy, model.color)}
          ${renderMetricMini("PRECISION", precision, model.color)}
          ${renderMetricMini("RECALL", recall, model.color)}
          ${renderMetricMini("F1-SCORE", f1, model.color)}
        </div>
      </div>
    `;
  }).join("");
}

function renderMetricMini(label, value, color) {
  const display = value !== null ? `${value}%` : "N/A";
  const barWidth = value !== null ? value : 0;
  return `
    <div class="metric-mini-glass">
      <div class="metric-mini-top">
        <span class="metric-mini-label">${label}</span>
        <strong class="metric-mini-value" style="color:${color};">${display}</strong>
      </div>
      <div class="metric-mini-bar-track">
        <div class="metric-mini-bar-fill" style="width:${barWidth}%;background:${color};"></div>
      </div>
    </div>
  `;
}

/* ─── Comparison Bar Chart ─── */
function renderComparisonChart(metrics) {
  const container = document.getElementById("comparison-chart");
  if (!container) return;

  const models = [
    { key: "lr", name: "Logistic Regression", color: "#4e7cff" },
    { key: "nb", name: "Naive Bayes", color: "#a855f7" },
    { key: "svm", name: "Linear SVM", color: "#00d4ff" },
  ];

  const metricNames = ["Accuracy", "Precision", "Recall", "F1-Score"];
  const metricKeys = ["accuracy", "precision", "recall", "f1"];

  let html = '<div class="comparison-chart-inner">';

  metricNames.forEach((name, idx) => {
    html += `<div class="comparison-group">
      <div class="comparison-label">${name}</div>
      <div class="comparison-bars">`;

    models.forEach(model => {
      const m = metrics[model.key] || {};
      let raw = m[metricKeys[idx]];
      if (metricKeys[idx] === "f1") raw = m.f1 || m.f1_score;
      const val = metricValue(raw);

      html += `
        <div class="comparison-bar-row">
          <span class="comparison-model-label" style="color:${model.color};">${model.name}</span>
          <div class="comparison-bar-track">
            <div class="comparison-bar-fill" style="width:${val}%;background:linear-gradient(90deg,${model.color},${model.color}cc);box-shadow:0 0 12px ${model.color}44;"></div>
          </div>
          <span class="comparison-bar-value">${val.toFixed(1)}%</span>
        </div>
      `;
    });

    html += `</div></div>`;
  });

  html += "</div>";
  container.innerHTML = html;
}

/* ─── Donut Chart (CSS-based) ─── */
function renderDonutChart(data) {
  const container = document.getElementById("donut-chart-container");
  if (!container) return;

  const total = data.total || 0;
  if (total === 0) {
    container.innerHTML = `
      <div class="empty-state-mini">
        <div style="font-size:40px;margin-bottom:12px;opacity:.5;">📊</div>
        <div style="color:var(--text-secondary);font-size:14px;">Chưa có dữ liệu phân tích</div>
        <div style="color:var(--text-muted);font-size:13px;margin-top:4px;">Hãy phân tích tin tức để xem biểu đồ</div>
      </div>
    `;
    return;
  }

  const reliable = data.reliable || 0;
  const suspicious = data.suspicious || 0;
  const unreliable = data.unreliable || 0;

  const rPct = ((reliable / total) * 100).toFixed(1);
  const sPct = ((suspicious / total) * 100).toFixed(1);
  const uPct = ((unreliable / total) * 100).toFixed(1);

  // Conic gradient for donut
  const rDeg = (reliable / total) * 360;
  const sDeg = rDeg + (suspicious / total) * 360;

  container.innerHTML = `
    <div class="donut-wrapper">
      <div class="donut-ring" style="background:conic-gradient(
        #10b981 0deg ${rDeg}deg,
        #f59e0b ${rDeg}deg ${sDeg}deg,
        #f43f5e ${sDeg}deg 360deg
      );">
        <div class="donut-hole">
          <div class="donut-center-num">${total}</div>
          <div class="donut-center-label">Tổng tin</div>
        </div>
      </div>
      <div class="donut-legend">
        <div class="donut-legend-item">
          <span class="donut-dot" style="background:#10b981;box-shadow:0 0 8px rgba(16,185,129,.5);"></span>
          <span class="donut-legend-text">Đáng tin cậy</span>
          <strong class="donut-legend-val" style="color:#34d399;">${reliable} <small>(${rPct}%)</small></strong>
        </div>
        <div class="donut-legend-item">
          <span class="donut-dot" style="background:#f59e0b;box-shadow:0 0 8px rgba(245,158,11,.5);"></span>
          <span class="donut-legend-text">Cần kiểm chứng</span>
          <strong class="donut-legend-val" style="color:#fbbf24;">${suspicious} <small>(${sPct}%)</small></strong>
        </div>
        <div class="donut-legend-item">
          <span class="donut-dot" style="background:#f43f5e;box-shadow:0 0 8px rgba(244,63,94,.5);"></span>
          <span class="donut-legend-text">Không đáng tin</span>
          <strong class="donut-legend-val" style="color:#fb7185;">${unreliable} <small>(${uPct}%)</small></strong>
        </div>
      </div>
    </div>
  `;
}

/* ─── Confusion Matrix ─── */
function renderConfusionMatrix(metrics, modelKey = "lr") {
  const container = document.getElementById("cm-container");
  if (!container) return;

  const matrix = metrics[modelKey]?.confusion_matrix || [[0, 0], [0, 0]];

  container.innerHTML = `
    <div class="cm-grid">
      <div class="cm-corner"></div>
      <div class="cm-header-cell">Dự đoán thật</div>
      <div class="cm-header-cell">Dự đoán giả</div>

      <div class="cm-row-label">Thực tế thật</div>
      <div class="cm-cell good">${matrix[0]?.[0] ?? 0}</div>
      <div class="cm-cell bad">${matrix[0]?.[1] ?? 0}</div>

      <div class="cm-row-label">Thực tế giả</div>
      <div class="cm-cell bad">${matrix[1]?.[0] ?? 0}</div>
      <div class="cm-cell good">${matrix[1]?.[1] ?? 0}</div>
    </div>
  `;
}

/* ─── Confusion Matrix Tabs ─── */
function bindTabs(metrics) {
  document.querySelectorAll(".model-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".model-tab").forEach(x => x.classList.remove("active"));
      tab.classList.add("active");
      renderConfusionMatrix(metrics, tab.dataset.model);
    });
  });
}

/* ─── Recent Analysis Table ─── */
function renderRecentTable(history) {
  const container = document.getElementById("recent-table-container");
  if (!container) return;

  if (!history || history.length === 0) {
    container.innerHTML = `
      <div class="empty-state-mini">
        <div style="font-size:40px;margin-bottom:12px;opacity:.5;">📋</div>
        <div style="color:var(--text-secondary);font-size:14px;">Chưa có tin nào được phân tích</div>
        <div style="color:var(--text-muted);font-size:13px;margin-top:4px;">Hãy sử dụng trang Phân tích để kiểm tra tin tức</div>
      </div>
    `;
    return;
  }

  const recent = history.slice(0, 10);
  const MODEL_NAMES = { lr: "Logistic Regression", nb: "Naive Bayes", svm: "Linear SVM", all: "Tất cả" };

  let html = `
    <div class="recent-table-wrap">
      <table class="recent-table">
        <thead>
          <tr>
            <th>Thời gian</th>
            <th>Tiêu đề</th>
            <th>Kết quả</th>
            <th>Điểm tin cậy</th>
            <th>Mô hình</th>
          </tr>
        </thead>
        <tbody>
  `;

  recent.forEach(item => {
    const badge = item.badge || "warning";
    const label = item.label || "N/A";
    const score = item.final_score != null ? Number(item.final_score).toFixed(1) : "N/A";
    const model = MODEL_NAMES[item.model_used || item.model] || item.model_used || item.model || "N/A";
    const title = (item.title || "Không có tiêu đề").substring(0, 50) + (item.title && item.title.length > 50 ? "…" : "");
    const time = item.created_at || "—";

    let badgeClass = "badge-warning";
    if (badge === "real") badgeClass = "badge-real";
    else if (badge === "fake") badgeClass = "badge-fake";

    let scoreColor = "var(--text-white)";
    if (score !== "N/A") {
      const s = parseFloat(score);
      if (s >= 75) scoreColor = "var(--success-light)";
      else if (s >= 50) scoreColor = "var(--warning)";
      else scoreColor = "var(--danger-light)";
    }

    html += `
      <tr>
        <td class="td-time">${time}</td>
        <td class="td-title" title="${(item.title || '').replace(/"/g, '&quot;')}">${title}</td>
        <td><span class="table-badge ${badgeClass}">${label}</span></td>
        <td><strong style="color:${scoreColor};font-weight:800;">${score !== "N/A" ? score + "%" : score}</strong></td>
        <td class="td-model">${model}</td>
      </tr>
    `;
  });

  html += `</tbody></table></div>`;
  container.innerHTML = html;
}

/* ─── Error State ─── */
function showDashboardError(message) {
  const grid = document.getElementById("model-perf-grid");
  if (!grid) return;
  grid.innerHTML = `
    <div class="glass-card" style="text-align:center;padding:50px;grid-column:1/-1;">
      <div style="font-size:40px;margin-bottom:12px;">⚠️</div>
      <div style="color:var(--danger-light);font-weight:800;">${message}</div>
    </div>
  `;
}

/* ─── Main Loader ─── */
async function loadDashboard() {
  try {
    // Fetch all data in parallel
    const [modelsRes, summaryRes, historyRes] = await Promise.all([
      fetch("/api/models"),
      fetch("/api/dashboard-summary"),
      fetch("/api/history"),
    ]);

    const modelsJson = await modelsRes.json();
    const summaryJson = await summaryRes.json();
    const historyJson = await historyRes.json();

    // Summary
    if (summaryJson.success) {
      summaryData = summaryJson;
      renderSummary(summaryData);
    }

    // Models
    if (modelsJson.success) {
      metricsData = modelsJson.metrics || {};
      window.metricsData = metricsData;
      renderModelPerformance(metricsData);
      renderComparisonChart(metricsData);
      renderConfusionMatrix(metricsData, "lr");
      bindTabs(metricsData);
    } else {
      showDashboardError(modelsJson.error || "Không đọc được dữ liệu mô hình.");
    }

    // History & Donut
    if (historyJson.success) {
      historyData = historyJson.items || [];
      renderRecentTable(historyData);
    }

    // Donut uses summary data
    if (summaryJson.success) {
      renderDonutChart(summaryJson);
    } else {
      renderDonutChart({ total: 0 });
    }

  } catch (err) {
    console.error("Dashboard load error:", err);
    showDashboardError("Không gọi được API. Kiểm tra server.");
  }
}

document.addEventListener("DOMContentLoaded", loadDashboard);