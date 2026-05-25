import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"D:\OCR\tesseract.exe"

def extract_text_from_image(image_path):
    try:
        image = Image.open(image_path).convert("L")

        max_width = 1200
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height))

        text = pytesseract.image_to_string(image, lang="vie+eng")

        return text.strip()

    except Exception as e:
        print("OCR ERROR:", e)
        return ""