from src.ocr import extract_text_from_image


def analyze_image_news(image_path):
    text = extract_text_from_image(image_path)

    if not text:
        return {
            "success": False,
            "message": "Không đọc được chữ trong ảnh."
        }

    return {
        "success": True,
        "ocr_text": text,
        "message": "Đã đọc chữ từ ảnh."
    }