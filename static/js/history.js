let allHistory = [];
let filtered = [];
let currentPage = 1;
const PAGE_SIZE = 10;
let activeFilter = "all";
let searchQuery = "";

const MODEL_NAMES = {
  lr: "Logistic Regression",
  nb: "Naive Bayes",
  svm: "Linear SVM",
  all: "Tất cả mô hình"
};

async function loadHistory() {
  const body = document.getElementById("history-tbody");

  try {
    const res = await fetch("/api/history");
    const data = await res.json();

    allHistory = data.items || [];

    applyFilters();
    renderSummaryStats();
  } catch (err) {
    if (body) {
      body.innerHTML = `
        <tr>
          <td colspan="6" style="text-align:center;padding:40px;color:var(--danger-light);">
            Không thể tải lịch sử.
          </td>
        </tr>
      `;
    }
  }
}

function getItemLabel(item) {
  const score = Number(item.final_score || item.primary_probability || item.result?._summary?.final_score || 0);

  if (score >= 75) return "Đáng tin cậy";
  if (score >= 50) return "Cần kiểm chứng thêm";
  if (score >= 35) return "Nghi vấn";
  return "Không đáng tin cậy";
}

function getItemBadge(item) {
  const score = Number(item.final_score || item.primary_probability || item.result?._summary?.final_score || 0);

  if (score >= 75) return "real";
  if (score < 50) return "fake";
  return "warning";
}

function getItemScore(item) {
  return item.final_score || item.result?._summary?.final_score || 0;
}

function applyFilters() {
  filtered = allHistory.filter((item) => {
    const badge = getItemBadge(item);

    const matchFilter =
      activeFilter === "all" ||
      (activeFilter === "real" && badge === "real") ||
      (activeFilter === "fake" && badge === "fake");

    const q = searchQuery.toLowerCase();

    const matchSearch =
      !q ||
      (item.title || "").toLowerCase().includes(q) ||
      (item.content || "").toLowerCase().includes(q);

    return matchFilter && matchSearch;
  });

  currentPage = 1;
  renderTable();
  renderPagination();
}

function renderTable() {
  const body = document.getElementById("history-tbody");
  const emptyState = document.getElementById("empty-state");
  const tableWrap = document.getElementById("history-table-wrap");

  if (!body) return;

  const start = (currentPage - 1) * PAGE_SIZE;
  const pageData = filtered.slice(start, start + PAGE_SIZE);

  if (filtered.length === 0) {
    body.innerHTML = "";

    if (emptyState) emptyState.style.display = "block";
    if (tableWrap) tableWrap.style.display = "none";

    const counter = document.getElementById("result-counter");
    if (counter) counter.textContent = "Không có kết quả phù hợp.";

    return;
  }

  if (emptyState) emptyState.style.display = "none";
  if (tableWrap) tableWrap.style.display = "block";

  body.innerHTML = pageData.map((item) => {
    const label = getItemLabel(item);
    const badge = getItemBadge(item);
    const score = getItemScore(item);
    const cls = badge === "real" ? "real" : badge === "fake" ? "fake" : "warning";
    const modelDisplay = MODEL_NAMES[item.model] || item.model || "Tất cả";

    return `
      <tr>
        <td style="color:var(--text-muted);font-size:12px;">${escapeHtml(item.created_at || "—")}</td>
        <td class="history-title-cell" title="${escapeHtml(item.title || "")}">
          ${escapeHtml(item.title || "(Không có tiêu đề)")}
        </td>
        <td><span class="badge ${cls}">${escapeHtml(label)}</span></td>
        <td><strong style="color:var(--text-white);">${score}/100</strong></td>
        <td style="font-size:13px;color:var(--text-muted);">${escapeHtml(modelDisplay)}</td>
        <td>
          <button class="delete-btn" onclick="deleteItem('${item.id}')" title="Xoá mục này">🗑️</button>
        </td>
      </tr>
    `;
  }).join("");

  const counter = document.getElementById("result-counter");
  if (counter) {
    counter.textContent = `Hiển thị ${start + 1}–${Math.min(start + PAGE_SIZE, filtered.length)} / ${filtered.length} kết quả`;
  }
}

function renderPagination() {
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const container = document.getElementById("pagination");

  if (!container) return;

  if (totalPages <= 1) {
    container.innerHTML = "";
    return;
  }

  let html = `
    <button class="page-btn" onclick="goPage(${currentPage - 1})" ${currentPage === 1 ? "disabled" : ""}>‹</button>
  `;

  for (let i = 1; i <= totalPages; i++) {
    html += `
      <button class="page-btn ${i === currentPage ? "active" : ""}" onclick="goPage(${i})">${i}</button>
    `;
  }

  html += `
    <button class="page-btn" onclick="goPage(${currentPage + 1})" ${currentPage === totalPages ? "disabled" : ""}>›</button>
  `;

  container.innerHTML = html;
}

function goPage(page) {
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);

  if (page < 1 || page > totalPages) return;

  currentPage = page;
  renderTable();
  renderPagination();
}
function renderSummaryStats() {
  const total = allHistory.length;

  const real = allHistory.filter((h) => {
    const score = Number(h.final_score || h.primary_probability || h.result?._summary?.final_score || 0);
    return score >= 75;
  }).length;

  const fake = allHistory.filter((h) => {
    const score = Number(h.final_score || h.primary_probability || h.result?._summary?.final_score || 0);
    return score < 50;
  }).length;

  const elTotal = document.getElementById("stat-total");
  const elReal = document.getElementById("stat-real");
  const elFake = document.getElementById("stat-fake");

  if (elTotal) elTotal.textContent = total;
  if (elReal) elReal.textContent = real;
  if (elFake) elFake.textContent = fake;
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      activeFilter = btn.dataset.filter;

      document.querySelectorAll(".filter-btn").forEach((b) => {
        b.className = "filter-btn";
      });

      btn.classList.add("active-" + activeFilter);

      applyFilters();
    });
  });

  const searchInput = document.getElementById("search-input");

  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value;
      applyFilters();
    });
  }

  loadHistory();
});

window.deleteItem = deleteItem;
window.clearAllHistory = clearAllHistory;
window.goPage = goPage;