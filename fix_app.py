import os

app_content = """from __future__ import annotations

import json
import os
import random as _random
import re as _re
import unicodedata as _unicodedata

from flask import Flask, jsonify, render_template, request

from src.crawler import extract_news_from_url
from src.image_analyzer import analyze_image_news
from src.history import (
    add_to_history,
    clear_history,
    delete_from_history,
    get_history,
)
from src.predict import confidence_to_trust_percent, predict_all_models, predict_news


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
METRICS_PATH = os.path.join(BASE_DIR, "models", "metrics.json")
SOURCE_RULES_PATH = os.path.join(BASE_DIR, "data", "source_rules.json")

MODEL_DISPLAY = {
    "lr": "Logistic Regression",
    "nb": "Naive Bayes",
    "svm": "Linear SVM",
}


def clamp(value, min_value=0, max_value=100):
    try:
        value = float(value)
    except Exception:
        value = 0

    return max(min_value, min(max_value, round(value, 2)))


def load_source_rules():
    default_rules = {
        "trusted_sources": [
            "gov.vn",
            "chinhphu.vn",
            "baochinhphu.vn",
            "moet.gov.vn",
            "moh.gov.vn",
            "mic.gov.vn",
            "vnexpress.net",
            "tuoitre.vn",
            "thanhnien.vn",
            "dantri.com.vn",
            "vietnamnet.vn",
            "vtv.vn",
            "vov.vn",
            "nhandan.vn",
        ],
        "low_trust_sources": [
            "facebook.com",
            "tiktok.com",
            "youtube.com",
            "blogspot",
            "wordpress",
            "telegram",
        ],
        "source_score": {
            "trusted": 90,
            "low_trust": 35,
            "unknown": 55,
        },
    }

    if not os.path.exists(SOURCE_RULES_PATH):
        return default_rules

    try:
        with open(SOURCE_RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_rules


def source_score_from_url(url: str = ""):
    rules = load_source_rules()

    if not url:
        return rules["source_score"]["unknown"]

    url = url.lower()

    if any(src in url for src in rules["trusted_sources"]):
        return rules["source_score"]["trusted"]

    if any(src in url for src in rules["low_trust_sources"]):
        return rules["source_score"]["low_trust"]

    return rules["source_score"]["unknown"]


def writing_score_from_text(title: str = "", content: str = ""):
    text = f"{title} {content}".lower()
    score = 70

    risky_words = [
        "cam kết",
        "100%",
        "chắc chắn",
        "duy nhất hôm nay",
        "nhận ngay",
        "lãi mỗi ngày",
        "lợi nhuận khủng",
        "chuyển khoản",
        "đặt cọc",
        "trúng thưởng",
        "việc nhẹ lương cao",
        "thần dược",
        "khỏi hoàn toàn",
        "chia sẻ gấp",
    ]

    good_words = [
        "theo",
        "công bố",
        "thông báo",
        "khuyến cáo",
        "cơ quan",
        "bộ",
        "sở",
        "chính phủ",
    ]

    if any(word in text for word in risky_words):
        score -= 30

    if any(word in text for word in good_words):
        score += 12

    if len(content.strip()) < 80:
        score -= 10

    return clamp(score)


def keyword_risk_score(title: str = "", content: str = ""):
    text = f"{title} {content}".lower()
    score = 75

    danger_words = [
        "lừa đảo",
        "giả mạo",
        "mạo danh",
        "chuyển khoản",
        "đặt cọc",
        "trúng thưởng",
        "lợi nhuận",
        "thần dược",
        "khỏi bệnh",
    ]

    if any(word in text for word in danger_words):
        score -= 35

    return clamp(score)


def aggregate_ai_score(results: dict):
    nb = results.get("nb", {}).get("probability", 50)
    lr = results.get("lr", {}).get("probability", 50)
    svm = results.get("svm", {}).get("probability", 50)

    return clamp(nb * 0.2 + lr * 0.4 + svm * 0.4)


def final_score_formula(ai_score, source_score, writing_score, keyword_score_value):
    return clamp(
        ai_score * 0.45
        + source_score * 0.25
        + writing_score * 0.20
        + keyword_score_value * 0.10
    )


def verdict_from_score(score):
    score = float(score)

    if score >= 75:
        return {
            "label": "Đáng tin cậy",
            "badge": "real",
            "display": "Tin có mức độ đáng tin cậy cao",
        }

    if score >= 50:
        return {
            "label": "Cần kiểm chứng thêm",
            "badge": "warning",
            "display": "Tin cần kiểm chứng thêm",
        }

    if score >= 35:
        return {
            "label": "Nghi vấn",
            "badge": "warning",
            "display": "Tin có dấu hiệu nghi vấn",
        }

    return {
        "label": "Không đáng tin cậy",
        "badge": "fake",
        "display": "Tin có dấu hiệu không đáng tin cậy",
    }


def build_explanation(ai_score, source_score, writing_score, keyword_score_value, final_score):
    return [
        "Điểm hiển thị chính được đồng bộ theo AI Score để thống nhất giữa trang Phân tích và Lịch sử.",
        f"AI Score = {ai_score}/100, được lấy từ mô hình đang chọn hoặc tổng hợp từ Naive Bayes, Logistic Regression và SVM.",
        f"Source Score = {source_score}/100, phản ánh mức độ uy tín của nguồn hoặc URL.",
        f"Writing Score = {writing_score}/100, đánh giá văn phong có trung lập hay giật gân.",
        f"Keyword Risk Score = {keyword_score_value}/100, đánh giá mức độ xuất hiện từ khóa rủi ro.",
        f"Final Score hiển thị = {final_score}/100.",
    ]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyzer")
def analyzer():
    return render_template("analyzer.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/api/models", methods=["GET"])
def api_models():
    if not os.path.exists(METRICS_PATH):
        return jsonify({"success": False, "error": "Chưa có dữ liệu metrics."}), 404
    try:
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            metrics = json.load(f)
        return jsonify({"success": True, "metrics": metrics})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


@app.route("/api/dashboard-summary", methods=["GET"])
def api_dashboard_summary():
    history = get_history()
    total = len(history)
    reliable = 0
    suspicious = 0
    unreliable = 0

    for item in history:
        badge = item.get("badge", "")
        label = item.get("label", "")
        if badge == "real":
            reliable += 1
        elif badge == "fake":
            unreliable += 1
        else:
            suspicious += 1

    return jsonify({
        "success": True,
        "total": total,
        "reliable": reliable,
        "suspicious": suspicious,
        "unreliable": unreliable,
    })


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True, silent=True) or {}

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    url = data.get("url", "").strip()
    model_key = data.get("model", "all").strip().lower()

    if url and not content:
        try:
            extracted = extract_news_from_url(url)
            title = title or extracted.get("title", "")
            content = extracted.get("content", "")
        except Exception:
            pass

    if not title and not content:
        return jsonify({
            "success": False,
            "error": "Vui lòng nhập tiêu đề, nội dung hoặc URL tin tức."
        }), 400

    try:

        # =========================
        # MODEL PREDICTION
        # =========================

        if model_key == "all":
            results = predict_all_models(title, content)

        else:
            if model_key not in MODEL_DISPLAY:
                return jsonify({
                    "success": False,
                    "error": f"Model '{model_key}' không hợp lệ."
                }), 400

            label, prob = predict_news(title, content, model_key)

            results = {
                model_key: {
                    "model_name": MODEL_DISPLAY[model_key],
                    "label": label,
                    "probability": confidence_to_trust_percent(label, prob),
                    "display": (
                        "Tin đáng tin cậy"
                        if label == "reliable"
                        else "Tin có dấu hiệu không đáng tin cậy"
                    ),
                    "badge": "real" if label == "reliable" else "fake",
                }
            }

        # =========================
        # AI SCORE
        # =========================

        if model_key != "all" and model_key in results:
            ai_score = clamp(
                results[model_key].get("probability", 50)
            )
        else:
            ai_score = aggregate_ai_score(results)

        # =========================
        # EXTRA SCORES
        # =========================

        source_score = source_score_from_url(url)

        writing_score = writing_score_from_text(
            title,
            content
        )

        keyword_score_value = keyword_risk_score(
            title,
            content
        )

        # =========================
        # FINAL SCORE
        # =========================

        reference_final_score = final_score_formula(
            ai_score,
            source_score,
            writing_score,
            keyword_score_value
        )

        final_score = reference_final_score

        # =========================
        # RISK KEYWORDS
        # =========================

        risk_text = f"{title} {content}".lower()

        high_risk_keywords = [
            "khẩn cấp", "khan cap",
            "chia sẻ gấp", "chia se gap",
            "sự thật bị che giấu", "su that bi che giau",
            "cảnh báo", "canh bao",
            "bí mật", "bi mat",
            "100%", "cam kết", "cam ket",
            "chắc chắn", "chac chan",
            "trúng thưởng", "trung thuong",
            "chuyển khoản", "chuyen khoan",
            "đặt cọc", "dat coc",
            "lợi nhuận", "loi nhuan",
            "việc nhẹ lương cao", "viec nhe luong cao",
            "thần dược", "than duoc",
            "khỏi bệnh", "khoi benh",
            "mất nhà mất đất", "mat nha mat dat",
            "biểu tình", "bieu tinh",
            "kích động", "kich dong",
            "việt tân", "viet tan"
        ]

        risk_hits = [
            word for word in high_risk_keywords
            if word in risk_text
        ]

        if len(risk_hits) >= 1:
            final_score = min(final_score, 60)

        if len(risk_hits) >= 2:
            final_score = min(final_score, 45)

        if len(risk_hits) >= 3:
            final_score = min(final_score, 35)

        if not url and len(risk_hits) >= 2:
            final_score = min(final_score, 40)

        # =========================
        # VERDICT
        # =========================

        verdict = verdict_from_score(final_score)

        # =========================
        # SCORE DETAIL
        # =========================

        score_detail = {
            "ai_score": ai_score,
            "source_score": source_score,
            "writing_score": writing_score,
            "keyword_risk_score": keyword_score_value,
            "final_score": final_score,
            "reference_final_score": reference_final_score,
            "risk_hits": risk_hits
        }

        score_formula = {
            "display_score": "Final Score = AI + Source + Writing + Keyword Risk",
            "reference_formula": "0.45*AI + 0.25*Source + 0.20*Writing + 0.10*KeywordRisk",
            "note": "Hệ thống kết hợp AI và các luật đánh giá rủi ro."
        }

        explanation = build_explanation(
            ai_score,
            source_score,
            writing_score,
            keyword_score_value,
            final_score
        )

        if risk_hits:
            explanation.append(
                "Phát hiện dấu hiệu rủi ro: "
                + ", ".join(risk_hits)
            )

        # =========================
        # SAVE HISTORY
        # =========================

        entry = add_to_history(
            title,
            content,
            {
                **results,
                "_summary": {
                    "final_score": final_score,
                    "verdict": verdict,
                    "score_detail": score_detail,
                    "score_formula": score_formula,
                    "explanation": explanation,
                    "url": url,
                }
            },
            model_key
        )

        # =========================
        # RETURN RESPONSE
        # =========================

        return jsonify({
            "success": True,
            "title": title,
            "content_preview": content[:300],
            "url": url,
            "results": results,
            "ai_score": ai_score,
            "source_score": source_score,
            "writing_score": writing_score,
            "keyword_risk_score": keyword_score_value,
            "final_score": final_score,
            "reference_final_score": reference_final_score,
            "risk_hits": risk_hits,
            "verdict": verdict,
            "score_detail": score_detail,
            "score_formula": score_formula,
            "explanation": explanation,
            "history_id": entry["id"]
        })

    except FileNotFoundError as exc:
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 503

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": f"Lỗi xử lý: {str(exc)}"
        }), 500

@app.route("/api/history", methods=["GET"])
def api_history():
    return jsonify({
        "success": True,
        "items": get_history()
    })


@app.route("/api/history/<hist_id>", methods=["DELETE"])
def api_delete_history(hist_id):
    success = delete_from_history(hist_id)

    if success:
        return jsonify({
            "success": True,
            "message": "Đã xoá thành công."
        })

    return jsonify({
        "success": False,
        "error": "Không tìm thấy mục lịch sử này."
    }), 404


@app.route("/api/history/clear", methods=["DELETE"])
def api_clear_history():
    count = clear_history()

    return jsonify({
        "success": True,
        "deleted": count
    })


@app.route("/api/extract", methods=["POST"])
def api_extract():
    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({
            "success": False,
            "error": "Vui lòng nhập đường dẫn bài báo."
        }), 400

    try:
        result = extract_news_from_url(url)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as exc:
        return jsonify({
            "success": False,
            "error": str(exc)
        }), 500

# ==========================================
# CHATBOT LOCAL TÍCH HỢP INTENT-MATCHING
# ==========================================

def _normalize(text: str) -> str:
    \"\"\"Chuyển về chữ thường, bỏ dấu, chuẩn hoá khoảng trắng.\"\"\"
    text = text.lower().strip()
    nfkd = _unicodedata.normalize("NFKD", text)
    no_accent = "".join(c for c in nfkd if not _unicodedata.combining(c))
    return _re.sub(r"\\s+", " ", no_accent)

_INTENTS: dict[str, dict] = {
    "greeting": {
        "keywords": [
            "chao", "hello", "hi", "xin chao", "alo", "hey",
            "chao ban", "good morning", "buoi sang",
        ],
        "replies": [
            "Chào bạn 👋 Mình là trợ lý của TrustCheck AI.\\nBạn muốn kiểm tra tin nào? Dán tiêu đề, nội dung hoặc URL vào trang **Phân tích** là mình hỗ trợ liền nha!",
            "Hello! 👋 Mình sẵn sàng giúp bạn kiểm chứng tin tức.\\nBạn có thể hỏi mình về cách hệ thống chấm điểm, mô hình ML, hoặc dán tin cần kiểm tra nhé.",
            "Chào bạn! Mình là trợ lý local của TrustCheck AI 🤖\\nHỏi mình bất cứ gì về kiểm chứng tin tức, mình sẽ hướng dẫn bạn nhé!",
        ],
    },
    "thanks": {
        "keywords": [
            "cam on", "thank", "thanks", "ok", "oke", "oki",
            "good", "tot lam", "hay lam", "tuyet voi",
        ],
        "replies": [
            "Không có gì nha 😊 Khi gặp tin nghi vấn, nhớ dán vào trang **Phân tích** để hệ thống chấm điểm bạn nhé!",
            "Rất vui được giúp bạn! 💙 Nếu cần kiểm tra thêm tin nào, cứ gửi mình nhé.",
            "Hehe, không có chi! Mình luôn ở đây hỗ trợ bạn kiểm chứng tin tức 🙌",
        ],
    },
    "analyze_request": {
        "keywords": [
            "kiem tra", "phan tich", "check", "xac minh",
            "dung hay sai", "that hay gia", "co dung khong",
            "co phai that", "tin nay", "thong tin nay",
            "cho rang", "nghe noi", "fact check", "factcheck",
        ],
        "replies": [
            "Để kiểm tra tin này, bạn hãy dán tiêu đề hoặc nội dung vào trang **Phân tích** nhé.\\nHệ thống sẽ dùng 3 mô hình ML (Naive Bayes, Logistic Regression, SVM) kết hợp phân tích nguồn và văn phong để chấm điểm tin cậy.",
            "Mình hiểu bạn muốn kiểm chứng tin! 🔍\\nCách nhanh nhất: dán nội dung hoặc URL vào trang **Phân tích**. Sau đó mình có thể giải thích kết quả cho bạn.",
            "Bạn muốn xác minh thông tin phải không? 👍\\nHãy vào trang **Phân tích**, dán tiêu đề + nội dung hoặc URL bài báo. Hệ thống sẽ trả về điểm tin cậy chi tiết.",
        ],
    },
    "ask_no_content": {
        "keywords": [
            "dung hay sai", "that hay gia", "co dung khong",
            "co that khong", "tin nay dung", "tin nay sai",
        ],
        "replies": [
            "Bạn gửi giúp mình tiêu đề, nội dung hoặc ảnh tin đó nhé 📝\\nMình cần có nội dung cụ thể thì mới phân tích được.",
            "Mình cần bạn gửi nội dung cụ thể để kiểm tra nha.\\nBạn có thể dán tiêu đề, đoạn tin hoặc URL vào đây hoặc vào trang **Phân tích**.",
        ],
    },
    "score_explain": {
        "keywords": [
            "diem", "phan tram", "%", "cong thuc", "tinh diem",
            "score", "tin cay", "do tin cay", "cham diem",
            "diem so", "bang diem",
        ],
        "replies": [
            "Điểm tin cậy được tính như sau:\\n\\n• **AI Score** (45%): từ mô hình ML (NB, LR, SVM)\\n• **Source Score** (25%): độ uy tín nguồn/URL\\n• **Writing Score** (20%): văn phong trung lập hay giật gân\\n• **Keyword Risk** (10%): từ khóa rủi ro\\n\\nĐiểm cuối cùng = tổng hợp có trọng số các thành phần trên. Nếu phát hiện nhiều từ khóa rủi ro, điểm sẽ bị giới hạn thêm.",
            "Hệ thống chấm điểm dựa trên 4 tiêu chí:\\n\\n1. **AI Score**: mô hình ML phân loại tin\\n2. **Source Score**: nguồn uy tín hay mạng xã hội\\n3. **Writing Score**: văn phong có khách quan không\\n4. **Keyword Risk**: có từ giật gân không\\n\\nCông thức: `0.45×AI + 0.25×Source + 0.20×Writing + 0.10×Keyword`",
        ],
    },
    "fake_reason": {
        "keywords": [
            "vi sao gia", "tai sao gia", "ly do gia",
            "nghi van", "khong dang tin", "fake",
            "vi sao bi danh gia", "tai sao khong tin",
        ],
        "replies": [
            "Tin bị đánh giá **nghi vấn/không đáng tin** thường do:\\n\\n• Mô hình ML phát hiện mẫu ngôn ngữ giống tin giả\\n• Nguồn không rõ ràng hoặc từ mạng xã hội\\n• Văn phong giật gân, kêu gọi \"chia sẻ gấp\"\\n• Chứa từ khóa rủi ro: \"trúng thưởng\", \"cam kết 100%\"...\\n\\nBạn có thể xem chi tiết từng thành phần điểm trong kết quả phân tích.",
            "Khi tin bị đánh giá thấp, có thể do:\\n\\n1. AI Score thấp — mô hình nhận dạng mẫu tin giả\\n2. Source Score thấp — nguồn từ blog, mạng xã hội\\n3. Có nhiều từ khóa rủi ro (\"khẩn cấp\", \"lợi nhuận khủng\"...)\\n\\nHãy kiểm tra lại kết quả chi tiết trên trang **Phân tích** nhé.",
        ],
    },
    "reliable_reason": {
        "keywords": [
            "vi sao dang tin", "tai sao tin cay",
            "vi sao that", "dang tin cay", "reliable",
            "tin tot", "diem cao",
        ],
        "replies": [
            "Tin được đánh giá **đáng tin cậy** khi:\\n\\n• Mô hình ML cho AI Score cao (giống mẫu tin thật)\\n• Nguồn từ báo chính thống (VnExpress, Tuổi Trẻ, VTV...)\\n• Văn phong trung lập, khách quan\\n• Không chứa từ khóa rủi ro\\n\\nTuy nhiên, kết quả ML chỉ mang tính tham khảo, bạn vẫn nên đối chiếu thêm nhé!",
        ],
    },
    "model_explain": {
        "keywords": [
            "model", "mo hinh", "naive bayes", "logistic",
            "svm", "tf-idf", "tfidf", "machine learning",
            "hoc may", "algorithm", "thuat toan",
        ],
        "replies": [
            "Hệ thống dùng **TF-IDF** để chuyển văn bản thành vector số, rồi đưa qua 3 mô hình:\\n\\n• **Naive Bayes**: nhanh, tốt với dữ liệu văn bản\\n• **Logistic Regression**: ổn định, dễ giải thích\\n• **Linear SVM**: mạnh với bài toán phân loại nhị phân\\n\\nKhi chọn \"Tất cả\", hệ thống tổng hợp kết quả với trọng số: NB 20%, LR 40%, SVM 40%.",
            "TrustCheck AI sử dụng pipeline: **TF-IDF → ML Model**\\n\\n📊 **TF-IDF**: đo tần suất từ, giảm trọng số từ phổ biến\\n🧠 **3 mô hình**: Naive Bayes, Logistic Regression, SVM\\n\\nBạn có thể xem Accuracy, Precision, Recall, F1 của từng mô hình trên trang **Dashboard**.",
        ],
    },
    "ocr_help": {
        "keywords": [
            "ocr", "doc anh", "anh chup", "hinh anh",
            "screenshot", "scan", "upload anh", "gui anh",
            "nhan dang chu", "nhan dien anh",
        ],
        "replies": [
            "TrustCheck AI hỗ trợ phân tích ảnh tin tức! 📷\\n\\nBạn chỉ cần:\\n1. Vào trang **Phân tích**\\n2. Chọn tab **Phân tích ảnh**\\n3. Upload ảnh chụp màn hình tin tức\\n\\nHệ thống sẽ dùng OCR (Tesseract) để trích xuất chữ trong ảnh, rồi phân tích bằng mô hình ML.",
            "Bạn có ảnh chụp tin tức muốn kiểm tra? 🖼️\\n\\nHãy vào trang **Phân tích** → tab **Phân tích ảnh** → upload ảnh lên.\\nHệ thống sẽ đọc chữ trong ảnh (OCR) và phân tích tự động nhé!",
        ],
    },
    "source_check": {
        "keywords": [
            "nguon", "url", "link", "bao", "website",
            "chinh thong", "uy tin", "source", "trang web",
        ],
        "replies": [
            "**Source Score** đánh giá uy tín nguồn tin:\\n\\n✅ **Nguồn tin cậy** (90đ): gov.vn, chinhphu.vn, VnExpress, Tuổi Trẻ, VTV, Thanh Niên...\\n⚠️ **Nguồn cần cẩn trọng** (35đ): Facebook, TikTok, YouTube, blog cá nhân\\n❓ **Nguồn chưa xác định** (55đ): các trang khác\\n\\nNếu có URL, hãy dán vào trang **Phân tích** để hệ thống đánh giá nguồn tự động.",
        ],
    },
    "share_advice": {
        "keywords": [
            "chia se", "share", "forward", "chuyen tiep",
            "gui di", "dang lai", "co nen chia se",
            "nen share", "repost",
        ],
        "replies": [
            "Trước khi chia sẻ một tin, bạn nên:\\n\\n1️⃣ Kiểm tra nguồn — tin từ đâu?\\n2️⃣ Đối chiếu với báo chính thống\\n3️⃣ Dán vào TrustCheck AI để chấm điểm\\n\\n📌 Nguyên tắc: **Nếu không chắc chắn, đừng chia sẻ.**\\nTin giả lan truyền nhanh vì mọi người chia sẻ trước khi kiểm chứng.",
            "Nguyên tắc vàng: **Chưa chắc → Chưa share** ✋\\n\\nĐặc biệt cẩn trọng với tin có:\\n• Giọng khẩn cấp, kêu gọi \"chia sẻ gấp\"\\n• Không có nguồn trích dẫn\\n• Hứa hẹn quá tốt (trúng thưởng, lợi nhuận...)\\n\\nDán tin vào trang **Phân tích** để kiểm tra trước khi share nhé!",
        ],
    },
    "dashboard_help": {
        "keywords": [
            "dashboard", "bieu do", "accuracy", "precision",
            "recall", "f1", "hieu suat", "performance",
            "do chinh xac", "chart",
        ],
        "replies": [
            "Trang **Dashboard** hiển thị hiệu suất các mô hình ML:\\n\\n📊 **Accuracy**: tỷ lệ dự đoán đúng tổng thể\\n🎯 **Precision**: trong các tin dự đoán \"giả\", bao nhiêu đúng\\n📈 **Recall**: phát hiện được bao nhiêu tin giả thực tế\\n⚖️ **F1-Score**: cân bằng giữa Precision và Recall\\n\\nCác chỉ số này chứng minh mô hình đã được huấn luyện và đánh giá nghiêm túc.",
        ],
    },
    "history_help": {
        "keywords": [
            "lich su", "da phan tich", "xem lai", "history",
            "ket qua cu", "lan truoc",
        ],
        "replies": [
            "Trang **Lịch sử** lưu lại tất cả các lần bạn phân tích tin tức 📋\\n\\nMỗi mục gồm: tiêu đề, điểm tin cậy, mô hình đã dùng, nhãn kết quả và thời gian.\\nBạn có thể xoá từng mục hoặc xoá toàn bộ lịch sử.",
            "**Lịch sử phân tích** giúp bạn:\\n\\n• Xem lại các tin đã kiểm tra\\n• So sánh kết quả giữa các lần\\n• Theo dõi xu hướng tin giả/tin thật\\n\\nVào trang **Lịch sử** để xem chi tiết nhé!",
        ],
    },
    "out_of_scope": {
        "keywords": [],
        "replies": [
            "Câu hỏi này nằm ngoài phạm vi của mình rồi 😅\\nMình chuyên hỗ trợ **kiểm chứng tin tức** thôi nha.\\n\\nBạn có thể hỏi mình về:\\n• Cách kiểm tra tin đúng/sai\\n• Điểm tin cậy tính thế nào\\n• Mô hình ML hoạt động ra sao\\n• Cách dùng các trang Phân tích, Dashboard, Lịch sử",
            "Hmm, mình chỉ hỗ trợ về kiểm chứng tin tức thôi nha 🙏\\nNhưng nếu bạn gặp tin nghi vấn nào, cứ gửi mình — mình sẽ hướng dẫn cách kiểm tra!",
            "Mình không rành lĩnh vực này lắm 😊 Nhưng nếu bạn muốn kiểm tra một tin tức nào đó, mình sẵn sàng giúp!\\nChỉ cần dán tiêu đề hoặc nội dung vào trang **Phân tích** là được.",
        ],
    },
}

def _match_intent(msg_normalized: str, msg_original: str) -> tuple[str, str]:
    best_intent = None
    best_score = 0

    for intent_name, intent_data in _INTENTS.items():
        if intent_name in ("out_of_scope", "ask_no_content"):
            continue
        hits = sum(1 for kw in intent_data["keywords"] if kw in msg_normalized)
        if hits > best_score:
            best_score = hits
            best_intent = intent_name

    ask_kws = ["dung hay sai", "that hay gia", "co dung khong", "co that khong", "nhu the nao", "phai khong"]
    if any(kw in msg_normalized for kw in ask_kws) and len(msg_original) < 60:
        return "ask_no_content", _random.choice(_INTENTS["ask_no_content"]["replies"])

    if len(msg_original) > 120:
        return "long_content", (
            "Mình thấy bạn gửi một đoạn nội dung khá dài — có vẻ đây là tin cần kiểm chứng! 📰\\n\\n"
            "Để có kết quả chính xác nhất, bạn hãy **dán nội dung này vào trang Phân tích** nhé.\\n"
            "Hệ thống sẽ dùng AI + phân tích nguồn + văn phong để chấm điểm chi tiết cho bạn."
        )

    if best_intent and best_score > 0:
        return best_intent, _random.choice(_INTENTS[best_intent]["replies"])

    return "out_of_scope", _random.choice(_INTENTS["out_of_scope"]["replies"])

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "success": False,
            "error": "Không có nội dung tin nhắn."
        }), 400

    msg_normalized = _normalize(message)
    intent, reply = _match_intent(msg_normalized, message)

    return jsonify({
        "success": True,
        "reply": reply
    })

@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    import uuid
    from werkzeug.utils import secure_filename

    file = request.files.get("image")

    if not file:
        return jsonify({
            "success": False,
            "message": "Chưa chọn ảnh."
        }), 400

    filename = secure_filename(file.filename or "image.jpg")
    ext = filename.rsplit(".", 1)[-1].lower()

    if ext not in ["jpg", "jpeg", "png", "webp"]:
        return jsonify({
            "success": False,
            "message": "Chỉ hỗ trợ ảnh JPG, JPEG, PNG hoặc WEBP."
        }), 400

    upload_folder = os.path.join(BASE_DIR, "static", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(upload_folder, safe_name)

    file.save(file_path)

    result = analyze_image_news(file_path)

    return jsonify(result)


if __name__ == "__main__":
    print("VietNewsCheck đang chạy tại: http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)
"""

with open("d:\\DoAnCoSo\\app.py", "w", encoding="utf-8") as f:
    f.write(app_content)
