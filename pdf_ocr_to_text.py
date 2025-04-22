import os
from pdf2image import convert_from_path
import pytesseract

# تحديد مسار tesseract (لو لم يكن معرف في PATH)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def pdf_to_text_via_ocr(pdf_path):
    print(f"🔍 جاري معالجة الملف: {pdf_path}")
    try:
        images = convert_from_path(pdf_path)
        full_text = ""
        for idx, img in enumerate(images, start=1):
            page_text = pytesseract.image_to_string(img, lang="ara")
            full_text += f"\n=== صفحة {idx} ===\n{page_text}\n"
        return full_text
    except Exception as e:
        print(f"❌ خطأ في الملف {pdf_path}: {e}")
        return ""

def process_all_pdfs(base_dir="books"):
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)
                txt_path = os.path.splitext(pdf_path)[0] + ".txt"

                if os.path.exists(txt_path):
                    print(f"✅ تم العثور على ملف نصي بالفعل: {txt_path}")
                    continue

                text = pdf_to_text_via_ocr(pdf_path)
                if text.strip():
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    print(f"📄 تم حفظ النص في: {txt_path}")
                else:
                    print(f"⚠️ النص المستخرج من {pdf_path} فارغ.")

if __name__ == "__main__":
    process_all_pdfs()
