from __future__ import annotations

import json
import os
import uuid
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(BASE_DIR, "database", "history.json")


def ensure_history_file():
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)

    if not os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def get_history():
    ensure_history_file()

    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(items):
    ensure_history_file()

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_to_history(title, content, result, model_key="all"):
    items = get_history()

    summary = result.get("_summary", {})
    verdict = summary.get("verdict", {})

    final_score = summary.get("final_score", 0)

    item = {
        "id": uuid.uuid4().hex[:12],
        "title": title or "Không có tiêu đề",
        "content": content or "",
        "content_preview": (content or "")[:180],
        "model": model_key,
        "model_used": model_key,
        "result": result,

        "final_score": final_score,
        "primary_probability": final_score,

        "label": verdict.get("label", "Chưa xác định"),
        "badge": verdict.get("badge", "warning"),

        "primary_label": (
            "reliable" if final_score >= 75
            else "unreliable" if final_score < 50
            else "suspicious"
        ),

        "created_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    items.insert(0, item)
    save_history(items)

    return item

def delete_from_history(hist_id):
    items = get_history()
    new_items = [item for item in items if item.get("id") != hist_id]

    if len(new_items) == len(items):
        return False

    save_history(new_items)
    return True


def clear_history():
    items = get_history()
    count = len(items)
    save_history([])
    return count
