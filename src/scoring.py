from __future__ import annotations

import json
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_RULES_PATH = os.path.join(BASE_DIR, "data", "source_rules.json")


def clamp(value, min_value=0, max_value=100):
    try:
        value = float(value)
    except Exception:
        value = 0

    return max(min_value, min(max_value, round(value, 2)))


def load_source_rules():
    if not os.path.exists(SOURCE_RULES_PATH):
        return {
            "trusted_sources": [],
            "low_trust_sources": [],
            "source_score": {
                "trusted": 90,
                "low_trust": 35,
                "unknown": 55
            }
        }

    with open(SOURCE_RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def source_score_from_url(url=""):
    rules = load_source_rules()

    if not url:
        return rules["source_score"]["unknown"]

    url = url.lower()

    if any(src in url for src in rules["trusted_sources"]):
        return rules["source_score"]["trusted"]

    if any(src in url for src in rules["low_trust_sources"]):
        return rules["source_score"]["low_trust"]

    return rules["source_score"]["unknown"]


def writing_score_from_text(title="", content=""):
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
        "chia sẻ gấp"
    ]

    good_words = [
        "theo",
        "công bố",
        "thông báo",
        "khuyến cáo",
        "cơ quan",
        "bộ",
        "sở",
        "chính phủ"
    ]

    if any(w in text for w in risky_words):
        score -= 30

    if any(w in text for w in good_words):
        score += 12

    if len(content.strip()) < 80:
        score -= 10

    return clamp(score)


def keyword_risk_score(title="", content=""):
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
        "khỏi bệnh"
    ]

    if any(w in text for w in danger_words):
        score -= 35

    return clamp(score)


def aggregate_ai_score(results):
    nb = results.get("nb", {}).get("probability", 50)
    lr = results.get("lr", {}).get("probability", 50)
    svm = results.get("svm", {}).get("probability", 50)

    return clamp(nb * 0.2 + lr * 0.4 + svm * 0.4)


def final_score_formula(ai_score, source_score, writing_score, keyword_score):
    return clamp(
        ai_score * 0.45
        + source_score * 0.25
        + writing_score * 0.20
        + keyword_score * 0.10
    )


def verdict_from_score(score):
    score = float(score)

    if score >= 75:
        return {
            "label": "Đáng tin cậy",
            "badge": "real",
            "display": "Tin có mức độ đáng tin cậy cao"
        }

    if score >= 50:
        return {
            "label": "Cần kiểm chứng thêm",
            "badge": "warning",
            "display": "Tin cần kiểm chứng thêm"
        }

    if score >= 35:
        return {
            "label": "Nghi vấn",
            "badge": "warning",
            "display": "Tin có dấu hiệu nghi vấn"
        }

    return {
        "label": "Không đáng tin cậy",
        "badge": "fake",
        "display": "Tin có dấu hiệu không đáng tin cậy"
    }


def build_explanation(ai_score, source_score, writing_score, keyword_score, final_score):
    return [
        "Điểm tổng hợp được tính theo công thức: 45% AI Score + 25% Source Score + 20% Writing Score + 10% Keyword Risk Score.",
        f"AI Score = {ai_score}/100, được tổng hợp từ Naive Bayes, Logistic Regression và SVM.",
        f"Source Score = {source_score}/100, phản ánh mức độ uy tín của nguồn hoặc URL.",
        f"Writing Score = {writing_score}/100, đánh giá văn phong có trung lập hay giật gân.",
        f"Keyword Risk Score = {keyword_score}/100, đánh giá mức độ xuất hiện từ khóa rủi ro.",
        f"Final Score = {final_score}/100."
    ]