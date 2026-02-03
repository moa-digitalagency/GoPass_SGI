import os
import re

TEMPLATES_DIR = 'templates'
STATICS_DIR = 'statics'
CSS_DIR = os.path.join(STATICS_DIR, 'css')
JS_DIR = os.path.join(STATICS_DIR, 'js')

# Regex patterns
STYLE_PATTERN = re.compile(r'(<style\b[^>]*>)(.*?)(</style>)', re.DOTALL | re.IGNORECASE)
SCRIPT_PATTERN = re.compile(r'(<script\b[^>]*>)(.*?)(</script>)', re.DOTALL | re.IGNORECASE)
SRC_ATTR_PATTERN = re.compile(r'src\s*=', re.IGNORECASE)
JINJA_PATTERN = re.compile(r'(\{\{)|(\{%|#\})')

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_relative_path(full_path, start_dir):
    return os.path.relpath(full_path, start_dir)

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    rel_path = get_relative_path(filepath, TEMPLATES_DIR)
    base_name = os.path.splitext(rel_path)[0]

    # Define target paths
    css_rel_path = base_name + '.css'
    js_rel_path = base_name + '.js'

    css_file_path = os.path.join(CSS_DIR, css_rel_path)
    js_file_path = os.path.join(JS_DIR, js_rel_path)

    # URL paths (for HTML)
    css_url_path = f"/static/css/{css_rel_path.replace(os.sep, '/')}"
    js_url_path = f"/static/js/{js_rel_path.replace(os.sep, '/')}"

    modifications = [] # List of (start, end, replacement)

    # --- PROCESS CSS ---
    css_content_acc = []
    style_matches = list(STYLE_PATTERN.finditer(content))
    first_style_match = None

    for match in style_matches:
        tag_open, inner_content, tag_close = match.groups()

        # Check for Jinja
        if JINJA_PATTERN.search(inner_content):
            print(f"Skipping style block in {rel_path} due to Jinja syntax.")
            continue

        css_content_acc.append(inner_content.strip())

        if first_style_match is None:
            first_style_match = match
            # Will replace with link
            modifications.append((match.start(), match.end(), f'<link rel="stylesheet" href="{css_url_path}">'))
        else:
            # Remove subsequent blocks
            modifications.append((match.start(), match.end(), ''))

    if css_content_acc:
        ensure_dir(css_file_path)
        with open(css_file_path, 'w', encoding='utf-8') as f:
            f.write("/* Extracted from " + rel_path + " */\n\n")
            f.write("\n\n".join(css_content_acc))
        print(f"Created CSS: {css_file_path}")

    # --- PROCESS JS ---
    js_content_acc = []
    script_matches = list(SCRIPT_PATTERN.finditer(content))
    first_js_match = None

    for match in script_matches:
        tag_open, inner_content, tag_close = match.groups()

        # Check if it has src
        if SRC_ATTR_PATTERN.search(tag_open):
            continue

        # Check for Jinja
        if JINJA_PATTERN.search(inner_content):
            print(f"Skipping script block in {rel_path} due to Jinja syntax.")
            continue

        # Check for specific attributes (e.g., type="module")
        # For simplicity, we assume if it's safe (no jinja), it's extractable.
        # But we should preserve attributes if we replace the tag?
        # If we merge multiple scripts, attributes might conflict.
        # We will assume standard scripts.

        js_content_acc.append(inner_content.strip())

        if first_js_match is None:
            first_js_match = match
            # Replace with script src
            # We use the original tag attributes if possible?
            # Or just cleaner <script src="...">.
            # Let's keep it simple: <script src="...">
            modifications.append((match.start(), match.end(), f'<script src="{js_url_path}"></script>'))
        else:
            modifications.append((match.start(), match.end(), ''))

    if js_content_acc:
        ensure_dir(js_file_path)
        with open(js_file_path, 'w', encoding='utf-8') as f:
            f.write("// Extracted from " + rel_path + "\n\n")
            f.write("\n\n".join(js_content_acc))
        print(f"Created JS: {js_file_path}")

    # Apply modifications
    if modifications:
        # Sort by start index descending to replace without offset issues
        modifications.sort(key=lambda x: x[0], reverse=True)

        new_content = list(content)
        for start, end, replacement in modifications:
            new_content[start:end] = replacement

        new_content_str = "".join(new_content)

        if new_content_str != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content_str)
            print(f"Updated HTML: {filepath}")

def main():
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                process_file(filepath)

if __name__ == '__main__':
    main()
