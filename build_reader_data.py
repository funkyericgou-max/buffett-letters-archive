#!/usr/bin/env python3
"""
把 output/ 下的 6 个 HTML（致股东信 3 卷 + 股东大会问答 3 卷）
解析成阅读器用的结构化数据，输出为 reader/data.js（window.BUFFETT_DATA）。

数据结构：
  window.BUFFETT_DATA = [
    {
      "id": "letter-1957",       # 稳定锚点 id
      "kind": "letter",          # letter | meeting
      "year": 1957,
      "title": "一九五七年 · 巴菲特致股东信",
      "paras": ["文本", ...],    # 正文段落（按顺序）
      "heads": [0, 3, 7]         # 标题段落的索引（用于加粗/导航）
    }, ...
  ]
"""

import re
import json
from pathlib import Path
from html.parser import HTMLParser

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# 中文数字 → 阿拉伯数字
CN_DIGITS = {
    "零": "0", "一": "1", "二": "2", "三": "3", "四": "4",
    "五": "5", "六": "6", "七": "7", "八": "8", "九": "9",
}


def cn_year_to_int(text: str) -> int:
    digits = [CN_DIGITS[ch] for ch in text if ch in CN_DIGITS]
    return int("".join(digits)) if digits else 0


def clean_text(s: str) -> str:
    s = s.replace("　", " ").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_question_heading(text: str) -> bool:
    t = text.strip().lstrip("*").strip()
    return bool(re.match(r"^\d+\s*[、.．]", t))


class LetterParser(HTMLParser):
    """解析致股东信 HTML：<section class="chapter"> 每年一章。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.docs = []
        self._in_chapter = False
        self._in_title = False
        self._in_content = False
        self._in_p = False
        self._p_has_strong = False
        self._title_buf = []
        self._p_buf = []
        self._paras = []
        self._heads = []
        self._cur_title = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag == "section" and "chapter" in cls:
            self._in_chapter = True
            self._paras = []
            self._heads = []
            self._cur_title = ""
        elif tag == "h1" and "chapter-title" in cls:
            self._in_title = True
            self._title_buf = []
        elif tag == "div" and "chapter-content" in cls:
            self._in_content = True
        elif tag == "p" and self._in_content:
            self._in_p = True
            self._p_buf = []
            self._p_has_strong = False
        elif tag == "strong" and self._in_p:
            self._p_has_strong = True

    def handle_endtag(self, tag):
        if tag == "h1" and self._in_title:
            self._cur_title = clean_text("".join(self._title_buf))
            self._in_title = False
        elif tag == "div" and self._in_content:
            self._in_content = False
        elif tag == "p" and self._in_p:
            text = clean_text("".join(self._p_buf))
            if text:
                if self._p_has_strong:
                    self._heads.append(len(self._paras))
                self._paras.append(text)
            self._in_p = False
        elif tag == "section" and self._in_chapter:
            self._in_chapter = False
            if self._paras:
                year = cn_year_to_int(self._cur_title)
                self.docs.append({
                    "id": f"letter-{year}",
                    "kind": "letter",
                    "year": year,
                    "title": self._cur_title,
                    "paras": self._paras,
                    "heads": self._heads,
                })

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)
        elif self._in_p:
            self._p_buf.append(data)


class MeetingParser(HTMLParser):
    """解析股东大会 HTML：year-section > session > session-content。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.docs = []
        self._year_title = ""
        self._in_year_title = False
        self._in_session = False
        self._in_session_title = False
        self._in_content = False
        self._in_h3 = False
        self._in_p = False
        self._buf = []
        self._session_title = ""
        self._paras = []
        self._heads = []
        self._session_seq = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag == "h1" and "year-main-title" in cls:
            self._in_year_title = True
            self._buf = []
        elif tag == "section" and "session" in cls:
            self._in_session = True
            self._paras = []
            self._heads = []
            self._session_title = ""
        elif tag == "h2" and "session-title" in cls:
            self._in_session_title = True
            self._buf = []
        elif tag == "div" and "session-content" in cls:
            self._in_content = True
        elif tag == "h3" and "session-subtitle" in cls and self._in_content:
            self._in_h3 = True
            self._buf = []
        elif tag == "p" and self._in_content:
            self._in_p = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "h1" and self._in_year_title:
            self._year_title = clean_text("".join(self._buf))
            self._in_year_title = False
            self._session_seq = 0
        elif tag == "h2" and self._in_session_title:
            self._session_title = clean_text("".join(self._buf))
            self._in_session_title = False
        elif tag == "div" and self._in_content:
            self._in_content = False
        elif tag == "h3" and self._in_h3:
            text = clean_text("".join(self._buf))
            if is_question_heading(text):
                self._heads.append(len(self._paras))
                self._paras.append(text)
            self._in_h3 = False
        elif tag == "p" and self._in_p:
            text = clean_text("".join(self._buf))
            if text and text != "--------正文--------":
                self._paras.append(text)
            self._in_p = False
        elif tag == "section" and self._in_session:
            self._in_session = False
            if self._paras:
                year = cn_year_to_int(self._year_title)
                sess_name = re.sub(r"^.*?\s*·\s*", "", self._session_title)
                self.docs.append({
                    "id": f"meeting-{year}-{self._session_seq}",
                    "kind": "meeting",
                    "year": year,
                    "title": f"{self._year_title} · {sess_name}" if self._year_title else self._session_title,
                    "session": sess_name,
                    "paras": self._paras,
                    "heads": self._heads,
                })
                self._session_seq += 1

    def handle_data(self, data):
        if self._in_year_title or self._in_session_title or self._in_h3 or self._in_p:
            self._buf.append(data)


def parse_file(parser, fn):
    parser.feed((OUTPUT_DIR / fn).read_text(encoding="utf-8"))


def main():
    letter_parser = LetterParser()
    for fn in [
        "巴菲特致股东信_壹_早期合伙人时期_1957-1969.html",
        "巴菲特致股东信_贰_黄金进化期_1971-1999.html",
        "巴菲特致股东信_叁_巨无霸运营期_2000-2025.html",
    ]:
        parse_file(letter_parser, fn)

    meeting_parser = MeetingParser()
    for fn in [
        "股东大会问答_贰_黄金进化期_1994-1999.html",
        "股东大会问答_叁a_巨无霸运营期_2000-2012.html",
        "股东大会问答_叁b_巨无霸运营期_2013-2025.html",
    ]:
        parse_file(meeting_parser, fn)

    letters = letter_parser.docs
    meetings = meeting_parser.docs
    docs = letters + meetings
    docs.sort(key=lambda d: (d["kind"], d["year"], d["id"]))

    total_paras = sum(len(d["paras"]) for d in docs)
    print(f"letters: {len(letters)}, meetings: {len(meetings)}, total docs: {len(docs)}")
    print(f"total paragraphs: {total_paras}")

    out_js = BASE_DIR / "reader" / "data.js"
    out_js.parent.mkdir(exist_ok=True)
    payload = json.dumps(docs, ensure_ascii=False, separators=(",", ":"))
    out_js.write_text("window.BUFFETT_DATA = " + payload + ";\n", encoding="utf-8")
    size_mb = out_js.stat().st_size / 1024 / 1024
    print(f"wrote {out_js} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
