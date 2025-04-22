from flask import Flask, render_template, request,redirect, url_for
from markupsafe import Markup
import os, json, re
from search_utils import perform_search

app = Flask(__name__)
BOOKS_DIR = "books"

# استخراج النص من ملف .txt أو .json
def extract_text(file_path):
    if file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, indent=2)
    return ""

# جلب جميع الكتب من مجلد الكتب
def get_all_books():
    books = []
    for folder in os.listdir(BOOKS_DIR):
        folder_path = os.path.join(BOOKS_DIR, folder)
        if os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith('.txt') or filename.endswith('.json'):
                    books.append((folder, filename))
    return sorted(books)

# تقسيم الصفحات حسب عنوان صفحة مكتوب في النص
def paginate_text(text):
    # أولاً تحقق أي نمط موجود داخل النص
    if '=== صفحة' in text:
        # تقسيم حسب النمط العربي
        pages = re.split(r'=== صفحة \d+ ===', text)
    elif '----- PDF:' in text:
        # تقسيم حسب نمط PDF
        pages = re.split(r'-{5,}\s*PDF:\s*\d+,\s*Page\s*\d+\s*-{5,}', text)
    else:
        # fallback: تقسيم كل 1000 حرف
        pages = [text[i:i + 1000] for i in range(0, len(text), 1000)]

    return [p.strip() for p in pages if p.strip()]


# اختياري: تنظيف النصوص من رؤوس الصفحات (للاستخدام اليدوي فقط إن أحببت)
def clean_page_headers(folder="books"):
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".txt"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                cleaned = [line for line in lines if not line.strip().startswith("=== صفحة")]
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(cleaned)
                    
# الصفحة الرئيسية
@app.route('/welcome')
def index():
    return render_template("index.html")


# عدّل دالة home بهذا الشكل:
@app.route('/')
def home():
    books = get_all_books()
    if books:
        first_folder, first_filename = books[0]
        return redirect(url_for('view_book', folder=first_folder, filename=first_filename))
    return render_template('books.html', books=books)


# عرض صفحات كتاب معين
@app.route('/view/<folder>/<filename>')
def view_book(folder, filename):
    filepath = os.path.join(BOOKS_DIR, folder, filename)
    text = extract_text(filepath)
    pages = paginate_text(text)
    books = get_all_books()
    return render_template(
        'view_book.html',
        folder=folder,
        filename=filename,
        books=books,
        book_pages=pages,
        current_folder=folder,
        current_filename=filename
    )


@app.route('/search', methods=['POST'])
def search():
    raw_query = request.form['query'].strip()
    search_mode = request.form.get('search_mode', 'and')

    results, books = perform_search(
        raw_query=raw_query,
        search_mode=search_mode,
        get_all_books=get_all_books,
        extract_text=extract_text,
        paginate_text=paginate_text
    )

    return render_template('search_results.html', query=raw_query, results=results, books=books)










if __name__ == '__main__':
    # clean_page_headers()  ← فعّل هذه فقط إذا أردت إزالة العناوين من النصوص
    app.run(debug=True)
