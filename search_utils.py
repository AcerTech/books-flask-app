import re
from markupsafe import Markup
# from camel_tools.utils.dediac import dediac_ar


def remove_diacritics(text):
    return re.sub(r'[\u064B-\u0652]', '', text)


def highlight_text(original, query_terms):
    original_no_diac = ''
    index_map = []

    for i, c in enumerate(original):
        if not re.match(r'[\u064B-\u0652]', c):
            index_map.append(i)
            original_no_diac += c

    highlights = []

    for q in query_terms:
        for match in re.finditer(re.escape(q), original_no_diac, flags=re.IGNORECASE):
            start_diac, end_diac = match.span()
            try:
                start = index_map[start_diac]
                end = index_map[end_diac - 1] + 1
                highlights.append((start, end))
            except IndexError:
                continue

    highlights = sorted(set(highlights), key=lambda x: x[0])
    result = ''
    last_idx = 0

    for start, end in highlights:
        result += original[last_idx:start]
        result += f'<span class="highlight">{original[start:end]}</span>'
        last_idx = end

    result += original[last_idx:]
    return result

def extract_snippet_around_match(original_line, query_terms):
    no_diac = ''
    index_map = []

    for i, c in enumerate(original_line):
        if not re.match(r'[\u064B-\u0652]', c):
            index_map.append(i)
            no_diac += c

    for q in query_terms:
        match = re.search(re.escape(q), no_diac, flags=re.IGNORECASE)
        if match:
            start_diac, end_diac = match.span()
            try:
                start = index_map[start_diac]
                end = index_map[end_diac - 1] + 1
                snippet_start = max(0, start - 60)
                snippet_end = min(len(original_line), end + 60)
                return original_line[snippet_start:snippet_end].strip()
            except IndexError:
                continue

    return original_line[:120].strip()

def paginate_text(text):
    if '=== صفحة' in text:
        pages = re.split(r'=== صفحة \d+ ===', text)
    elif '----- PDF:' in text:
        pages = re.split(r'-{5,}\s*PDF:\s*\d+,\s*Page\s*\d+\s*-{5,}', text)
    else:
        pages = [text[i:i + 1000] for i in range(0, len(text), 1000)]
    return [p.strip() for p in pages if p.strip()]

def perform_search(raw_query, search_mode, get_all_books, extract_text, paginate_text):
    raw_query = raw_query.strip()

    if search_mode == 'or':
        parts = [p.strip() for p in raw_query.split('|')]
        raw_terms = []
        for part in parts:
            raw_terms.extend(part.split())
    else:
        raw_terms = [raw_query]

    query_terms = [remove_diacritics(term.lower()) for term in raw_terms]
    use_or = (search_mode == 'or')

    books = get_all_books()
    results = []

    for folder, filename in books:
        filepath = f"books/{folder}/{filename}"
        text = extract_text(filepath)
        text_no_diac = remove_diacritics(text.lower())

        match_found = (
            any(q in text_no_diac for q in query_terms) if use_or
            else all(q in text_no_diac for q in query_terms)
        )

        if match_found:
            pages = paginate_text(text)
            highlighted_pages = [highlight_text(page, query_terms) for page in pages]

            snippet_entries = []
            for line in text.splitlines():
                line_no_diac = remove_diacritics(line.lower())

                if (any(q in line_no_diac for q in query_terms) if use_or else all(q in line_no_diac for q in query_terms)):
                    for i, page in enumerate(pages):
                        if line in page:
                            snippet_excerpt = extract_snippet_around_match(line, query_terms)
                            highlighted_line = highlight_text(snippet_excerpt, query_terms)
                            snippet_entries.append({
                                "line": Markup(highlighted_line),
                                "page_number": i
                            })
                            break

            if snippet_entries:
                results.append({
                    'path': f"{folder}/{filename}",
                    'folder': folder,
                    'filename': filename,
                    'snippets': snippet_entries,
                    'pages': highlighted_pages
                })

    return results, books
