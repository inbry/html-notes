#!/usr/bin/env python3
"""docs/ 配下のHTMLを走査して一覧ページ(_site/index.html)を生成する。"""

import html
import os
import shutil
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
SITE_DIR = ROOT / "_site"
INDEX_NAME = "index.html"


class TitleExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.h1 = None
        self._in_title = False
        self._in_h1 = False

    def handle_starttag(self, tag, attrs):
        if tag == "title" and self.title is None:
            self._in_title = True
        elif tag == "h1" and self.h1 is None:
            self._in_h1 = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data
        elif self._in_h1:
            self.h1 = (self.h1 or "") + data


def extract_title(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = TitleExtractor()
    parser.feed(text)
    for candidate in (parser.title, parser.h1):
        if candidate and candidate.strip():
            return " ".join(candidate.split())
    return path.stem


def get_last_commit_date(path: Path) -> datetime:
    # コミット履歴がないファイルはファイルシステムの更新日時にフォールバックする
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        out = result.stdout.strip()
        if out:
            return datetime.fromisoformat(out)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def find_html_files():
    if not DOCS_DIR.exists():
        return []
    return [
        path
        for path in sorted(DOCS_DIR.rglob("*.html"))
        if path.name != INDEX_NAME
    ]


def render_index(entries) -> str:
    rows = []
    for title, date, rel_path in entries:
        href = quote(str(rel_path).replace(os.sep, "/"))
        date_str = date.strftime("%Y-%m-%d")
        rows.append(
            f'<li class="entry"><a href="{href}">'
            f'<span class="entry-title">{html.escape(title)}</span>'
            f'<span class="entry-date">{date_str}</span>'
            f"</a></li>"
        )
    rows_html = "\n".join(rows) if rows else (
        '<li class="empty">まだHTMLがありません。docs/ に追加してください。</li>'
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>解説HTML一覧</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 1.5rem 1rem 3rem;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    max-width: 720px;
    margin-inline: auto;
    line-height: 1.4;
  }}
  h1 {{ font-size: 1.3rem; margin: 0 0 1rem; }}
  ul {{ list-style: none; margin: 0; padding: 0; }}
  .entry {{ border-bottom: 1px solid #ddd; }}
  .entry a {{
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    padding: 0.9rem 0.25rem;
    text-decoration: none;
    color: inherit;
    word-break: break-word;
  }}
  .entry-title {{ font-size: 1rem; font-weight: 500; }}
  .entry-date {{ font-size: 0.8rem; color: #777; }}
  .empty {{ padding: 1rem 0.25rem; color: #777; }}
</style>
</head>
<body>
<h1>解説HTML一覧</h1>
<ul>
{rows_html}
</ul>
</body>
</html>
"""


def main():
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    if DOCS_DIR.exists():
        shutil.copytree(DOCS_DIR, SITE_DIR, dirs_exist_ok=True)

    entries = []
    for path in find_html_files():
        title = extract_title(path)
        date = get_last_commit_date(path)
        rel_path = path.relative_to(DOCS_DIR)
        entries.append((title, date, rel_path))

    entries.sort(key=lambda e: e[1], reverse=True)

    index_html = render_index(entries)
    (SITE_DIR / INDEX_NAME).write_text(index_html, encoding="utf-8")

    print(f"Generated {SITE_DIR / INDEX_NAME} with {len(entries)} entries.")


if __name__ == "__main__":
    main()
