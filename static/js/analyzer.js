/* ═══════════════════════════════════
   ANALYZER PAGE LOGIC
═══════════════════════════════════ */

let selectedModel = "lr";

/* ─── Model selector ─────────── */
document.querySelectorAll(".model-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".model-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    selectedModel = btn.dataset.model;
  });
});

/* ─── Quick fill buttons ─────── */
function fillExample(type) {
  const examples = {
    fake: {
      title: "Thuốc bí truyền chữa ung thư 100% trong 3 ngày",
      content:
        "Một bài đăng trên mạng xã hội quảng cáo loại thuốc bí truyền có thể chữa ung thư hoàn toàn trong ba ngày mà không cần xạ trị hay hóa trị, được nhiều người chia sẻ rộng rãi."
    },
    real: {
      title: "Ngân hàng Nhà nước công bố điều chỉnh lãi suất điều hành",
      content:
        "Ngân hàng Nhà nước Việt Nam vừa ban hành quyết định điều chỉnh lãi suất điều hành nhằm hỗ trợ nền kinh tế phục hồi, có hiệu lực từ ngày ký theo thông báo chính thức."
    }
  };

  const ex = examples[type];

  if (ex) {
    document.getElementById("title").value = ex.title;
    document.getElementById("content").value = ex.content;
  }
}

function clearForm() {
  document.getElementById("title").value = "";
  document.getElementById("content").value = "";
  document.getElementById("url-input").value = "";
  document.getElementById("result-container").innerHTML = "";

  const imageResult = document.getElementById("imageResult");
  const imageInput = document.getElementById("imageInput");

  if (imageResult) imageResult.innerHTML = "";
  if (imageInput) imageInput.value = "";
}

/* ─── URL Fetch ────── */
const btnFetchUrl = document.getElementById("btn-fetch-url");

if (btnFetchUrl) {
  btnFetchUrl.addEventListener("click", async () => {
    const url = document.getElementById("url-input").value.trim();

    if (!url) {
      showToast("Vui lòng nhập đường dẫn URL", "warning");
      return;
    }

    btnFetchUrl.disabled = true;
    const oldText = btnFetchUrl.innerHTML;
    btnFetchUrl.innerHTML = "Đang tải...";

    try {
      const res = await fetch("/api/extract", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ url })
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.error || "Không thể lấy dữ liệu từ URL");
      }

      document.getElementById("title").value = data.data.title || "";
      document.getElementById("content").value = data.data.content || "";

      showToast("Đã tải nội dung bài báo!", "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btnFetchUrl.disabled = false;
      btnFetchUrl.innerHTML = oldText;
    }
  });
}

/* ─── Form submit ────────────── */
const analyzeForm = document.getElementById("analyze-form");

if (analyzeForm) {
  analyzeForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const title = document.getElementById("title").value.trim();
    const content = document.getElementById("content").value.trim();
    const url = document.getElementById("url-input").value.trim();

    if (!title && !content && !url) {
      showToast("Vui lòng nhập tiêu đề, nội dung, URL hoặc tải ảnh để phân tích.", "warning");
      return;
    }

    const btn = document.getElementById("submit-btn");
    const oldText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = "Đang phân tích...";

    const resultContainer = document.getElementById("result-container");
    resultContainer.innerHTML = "";

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          title,
          content,
          url,
          model: selectedModel
        })
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        throw new Error(data.error || "Không phân tích được tin tức");
      }

      renderResults(data, selectedModel);
      showToast("Phân tích hoàn tất!", "success");
    } catch (err) {
      showToast(err.message, "error");

      resultContainer.innerHTML = `
        <div class="result-card fake" style="text-align:center;padding:28px;">
          <div style="font-size:36px;margin-bottom:12px;">⚠️</div>
          <div style="font-size:16px;font-weight:700;color:var(--danger-light);">
            ${escapeHtml(err.message)}
          </div>
        </div>
      `;
    } finally {
      btn.disabled = false;
      btn.innerHTML = oldText;
    }
  });
}

/* ─── Render results ─────────── */
function renderResults(data, modelKey) {
  const container = document.getElementById("result-container");
  const results = data.results || {};
  const keys = Object.keys(results);

  if (modelKey === "all" || keys.length > 1) {
    renderMultiResults(data, container);
  } else {
    const r = results[keys[0]];
    renderSingleResult(r, container, data);
  }
}

function getVerdictByScore(score) {
  if (score >= 75) {
    return {
      cls: "real",
      icon: "✅",
      title: "Tin đáng tin cậy",
      badge: "Tin thật",
      note:
        "Hệ thống đánh giá nội dung này có mức độ đáng tin cậy tương đối cao. Tuy nhiên, vẫn nên đối chiếu thêm với nguồn chính thống."
    };
  }

  if (score >= 50) {
    return {
      cls: "warning",
      icon: "🟡",
      title: "Cần kiểm chứng thêm",
      badge: "Cần kiểm chứng",
      note:
        "Nội dung này chưa đủ chắc chắn để kết luận. Bạn nên kiểm tra thêm nguồn đăng, thời điểm đăng và các nguồn báo chí chính thống."
    };
  }

  return {
    cls: "fake",
    icon: "⚠️",
    title: "Tin có dấu hiệu không đáng tin cậy",
    badge: "Tin nghi vấn",
    note:
      "Hệ thống phát hiện nội dung có dấu hiệu rủi ro, giật gân hoặc chưa có nguồn xác thực rõ ràng. Không nên chia sẻ ngay."
  };
}

function renderSingleResult(r, container, data) {
  const finalScore = Number(data.final_score || r.probability || 0);
  const verdict = getVerdictByScore(finalScore);

  const riskHits = data.risk_hits || [];

  container.innerHTML = `
    <div class="result-container animate-in">
      <div class="result-card ${verdict.cls}">
        <div class="result-header">
          <div>
            <div class="result-label">Kết quả phân tích</div>
            <div class="result-verdict">${verdict.title}</div>
          </div>

          <div style="text-align:right;">
            <span class="result-badge ${verdict.cls}">
              ${verdict.icon} ${verdict.badge}
            </span>

            <div class="result-prob" style="margin-top:10px;">
              <div class="result-prob-label">Độ tin cậy nội dung</div>
              <div class="result-prob-value">
                ${finalScore.toFixed(2)}
                <span style="font-size:18px;color:var(--text-secondary);">%</span>
              </div>
            </div>
          </div>
        </div>

        <div class="progress-track">
          <div class="progress-fill ${verdict.cls}" style="width:0%" id="pbar"></div>
        </div>

        <p class="result-note">${verdict.note}</p>

        ${
          riskHits.length
            ? `
              <div style="
                margin-top:14px;
                padding:12px;
                border-radius:12px;
                background:rgba(255,120,120,0.08);
                border:1px solid rgba(255,120,120,0.22);
                font-size:13px;
                color:#ffb4b4;
              ">
                ⚠️ Dấu hiệu rủi ro phát hiện:
                <strong>${riskHits.map(escapeHtml).join(", ")}</strong>
              </div>
            `
            : ""
        }

        <div style="margin-top:14px;font-size:13px;color:var(--text-muted);">
          Mô hình:
          <strong style="color:var(--text-secondary);">${escapeHtml(r.model_name || selectedModel)}</strong>
        </div>
      </div>
    </div>
  `;

  setTimeout(() => {
    const pbar = document.getElementById("pbar");
    if (pbar) pbar.style.width = finalScore + "%";
  }, 100);
}

function renderMultiResults(data, container) {
  const results = data.results || {};
  const keys = Object.keys(results);
  const finalScore = Number(data.final_score || 0);
  const verdict = getVerdictByScore(finalScore);

  const cards = keys
    .map((key, i) => {
      const r = results[key];
      const modelScore = Number(r.probability || 0);
      const modelVerdict = r.label === "reliable" ? "real" : "fake";

      return `
        <div class="model-result-item" style="animation-delay:${i * 0.1}s">
          <div class="model-result-name">${escapeHtml(r.model_name || key)}</div>
          <span class="result-badge ${modelVerdict}" style="font-size:12px;">
            ${r.label === "reliable" ? "✅ Tin thật" : "⚠️ Tin giả"}
          </span>
          <div class="model-result-prob">${modelScore.toFixed(2)}%</div>
        </div>
      `;
    })
    .join("");

  container.innerHTML = `
    <div class="result-container animate-in">
      <div style="
        text-align:center;
        margin-bottom:20px;
        padding:20px;
        background:${verdict.cls === "real" ? "var(--success-bg)" : "var(--danger-bg)"};
        border:1px solid ${verdict.cls === "real" ? "var(--success-border)" : "var(--danger-border)"};
        border-radius:var(--radius-lg);
      ">
        <div style="font-size:40px;margin-bottom:8px;">${verdict.icon}</div>
        <div style="font-size:14px;color:var(--text-secondary);margin-bottom:4px;">
          Kết quả tổng hợp
        </div>
        <div style="font-size:22px;font-weight:800;color:var(--text-white);">
          ${verdict.title}
        </div>
        <div style="margin-top:8px;font-size:18px;font-weight:900;color:var(--text-white);">
          ${finalScore.toFixed(2)}%
        </div>
      </div>

      <div class="multi-results">${cards}</div>
    </div>
  `;
}

/* ─── Image OCR auto analyze ───── */
document.addEventListener("DOMContentLoaded", () => {
  const imageInput = document.getElementById("imageInput");
  const analyzeImageBtn = document.getElementById("analyzeImageBtn");
  const imageResult = document.getElementById("imageResult");
  const titleInput = document.getElementById("title");
  const contentInput = document.getElementById("content");

  if (!imageInput || !analyzeImageBtn || !imageResult) return;

  analyzeImageBtn.addEventListener("click", async () => {
    if (!imageInput.files.length) {
      imageResult.innerHTML = "Vui lòng chọn ảnh trước.";
      return;
    }

    const formData = new FormData();
    formData.append("image", imageInput.files[0]);

    imageResult.innerHTML = "Đang đọc chữ trong ảnh...";

    try {
      const response = await fetch("/analyze-image", {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (!data.success || !data.ocr_text) {
        imageResult.innerHTML = data.message || "Không đọc được chữ trong ảnh.";
        return;
      }

      if (titleInput && !titleInput.value.trim()) {
        titleInput.value = "Tin tức trích xuất từ hình ảnh";
      }

      if (contentInput) {
        contentInput.value = data.ocr_text;
      }

      imageResult.innerHTML = `
        <div class="result-card" style="margin-top:14px;">
          <h3>Kết quả OCR</h3>
          <p>${escapeHtml(data.ocr_text)}</p>
        </div>
      `;

      setTimeout(() => {
        analyzeForm.dispatchEvent(
          new Event("submit", {
            cancelable: true,
            bubbles: true
          })
        );
      }, 500);
    } catch (error) {
      imageResult.innerHTML = "Lỗi khi gửi ảnh lên server.";
    }
  });
});

/* ─── Helpers ─────────────── */
function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

window.fillExample = fillExample;
window.clearForm = clearForm;