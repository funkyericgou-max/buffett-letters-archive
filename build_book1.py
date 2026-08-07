#!/usr/bin/env python3
"""
巴菲特致股东信 —— 上卷
从 中文翻译/ 目录读取所有 .docx 文件，生成适合 A4 打印的 HTML。
"""

import os
import json
import re
from pathlib import Path
from docx import Document

BASE_DIR = Path(r"c:\Users\Administrator\Desktop\巴菲特信件整理")
LETTERS_DIR = BASE_DIR / "中文翻译"
OUTPUT_DIR = BASE_DIR / "output"

CSS = r"""
/* ===== 页面设置 ===== */
@page {
    size: A4;
    margin: 2.2cm 2.5cm 2.2cm 2.5cm;
}

@page :first {
    /* 封面页不加页码 */
}

/* ===== 全局 ===== */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: "SimSun", "宋体", "Noto Serif CJK SC", "Source Han Serif SC", serif;
    font-size: 11pt;
    line-height: 1.9;
    color: #1a1a1a;
    text-align: justify;
    word-break: break-all;
}

/* ===== 封面页 ===== */
.cover {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    page: cover;
    text-align: center;
    padding: 3cm 2cm;
}

.cover .book-title {
    font-family: "SimHei", "黑体", "Noto Sans CJK SC", sans-serif;
    font-size: 28pt;
    font-weight: bold;
    letter-spacing: 0.3em;
    margin-bottom: 0.8cm;
    line-height: 1.4;
}

.cover .subtitle {
    font-family: "SimHei", "黑体", sans-serif;
    font-size: 16pt;
    color: #555;
    margin-bottom: 1.5cm;
    letter-spacing: 0.1em;
}

.cover .years {
    font-family: "SimSun", "宋体", serif;
    font-size: 13pt;
    color: #777;
    margin-bottom: 3cm;
    line-height: 2;
}

.cover .divider {
    width: 6cm;
    border-top: 2px solid #333;
    margin: 1.5cm auto;
}

.cover .note {
    font-size: 10pt;
    color: #999;
    line-height: 1.8;
}

/* ===== 目录页 ===== */
.toc {
    page-break-before: always;
    padding-top: 1cm;
}

.toc-title {
    font-family: "SimHei", "黑体", sans-serif;
    font-size: 20pt;
    text-align: center;
    margin-bottom: 1.5cm;
    letter-spacing: 0.2em;
}

.toc-list {
    list-style: none;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.4cm 1cm;
}

.toc-list li {
    font-size: 10.5pt;
    line-height: 1.8;
    color: #333;
}

.toc-list .year {
    font-weight: bold;
    margin-right: 0.3em;
}

.toc-list .missing {
    color: #aaa;
}

/* ===== 每章（每年）===== */
.chapter {
    page-break-before: always;
    padding-top: 0.5cm;
}

.chapter-title {
    font-family: "SimHei", "黑体", "Noto Sans CJK SC", sans-serif;
    font-size: 20pt;
    text-align: center;
    margin-bottom: 1cm;
    letter-spacing: 0.15em;
    padding-bottom: 0.4cm;
    border-bottom: 2px solid #333;
}

.chapter-missing {
    text-align: center;
    font-size: 12pt;
    color: #888;
    padding: 3cm 0;
    font-style: italic;
}

.chapter-content p {
    text-indent: 2em;
    margin-bottom: 0.3em;
}

.chapter-content p.no-indent {
    text-indent: 0;
}

.chapter-content .salutation {
    text-indent: 0;
    font-weight: bold;
    font-size: 11.5pt;
    margin-bottom: 0.6em;
}

/* ===== 尾页 ===== */
.colophon {
    page-break-before: always;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 80vh;
    text-align: center;
}

.colophon p {
    font-size: 11pt;
    color: #777;
    line-height: 2.5;
}

/* ===== 打印设置 ===== */
@media print {
    body {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }
}
"""


def extract_letter_text(docx_path: Path) -> list[dict]:
    """提取 docx 文件中所有段落的文本和样式信息。"""
    try:
        doc = Document(str(docx_path))
    except Exception as e:
        print(f"  [!] 无法读取 {docx_path.name}: {e}")
        return []

    paras = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            # 保留空行（段落间距）
            paras.append({"type": "empty", "text": ""})
            continue

        # 检测是否为标题（粗体或居中）
        is_bold = any(run.bold for run in p.runs if run.bold)
        is_center = p.alignment is not None and p.alignment == 1  # CENTER

        if is_bold or is_center:
            paras.append({"type": "heading", "text": text})
        else:
            paras.append({"type": "para", "text": text})

    return paras


def clean_text(paras: list[dict]) -> list[dict]:
    """清理段落：合并不必要的空行，整理格式。"""
    result = []
    prev_empty = False
    for p in paras:
        if p["type"] == "empty":
            if not prev_empty:
                result.append(p)
            prev_empty = True
        else:
            result.append(p)
            prev_empty = False

    # 去掉末尾的空行
    while result and result[-1]["type"] == "empty":
        result.pop()
    # 去掉开头的空行
    while result and result[0]["type"] == "empty":
        result.pop(0)

    return result


def paras_to_html(paras: list[dict]) -> str:
    """将段落列表转为 HTML 片段。"""
    lines = []
    for p in paras:
        if p["type"] == "empty":
            lines.append("<p>&nbsp;</p>")
        elif p["type"] == "heading":
            # 检测是否是称呼语（致股东信开头通常是"伯克希尔·哈撒韦致全体股东"）
            text = p["text"]
            if any(kw in text for kw in ["致全体股东", "致伯克希尔", "致股东"]):
                lines.append(f'<p class="salutation">{escape_html(text)}</p>')
            else:
                lines.append(f'<p class="no-indent"><strong>{escape_html(text)}</strong></p>')
        else:
            text = p["text"]
            # 判断是否需要缩进（称呼语不缩进）
            if any(kw in text for kw in ["致全体股东", "致伯克希尔", "致股东"]):
                lines.append(f'<p class="no-indent salutation">{escape_html(text)}</p>')
            else:
                lines.append(f"<p>{escape_html(text)}</p>")
    return "\n".join(lines)


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def number_to_chinese(n: int) -> str:
    """将年份数字转为中文数字（如 1957 → 一九五七）。"""
    digits = "零一二三四五六七八九"
    return "".join(digits[int(d)] for d in str(n))


def generate_cover_html(cn_start: str, cn_end: str, era_label: str, era_desc: str = "") -> str:
    """生成封面 HTML，接受中文年份范围和时代标签。"""
    desc_html = f"<br>{era_desc}" if era_desc else ""
    return f"""<section class="cover">
<div class="book-title">巴菲特致股东信</div>
<div class="subtitle">WARREN BUFFETT LETTERS TO SHAREHOLDERS</div>
<div class="divider"></div>
<div class="years">
{cn_start}年 —— {cn_end}年<br>
{era_label}{desc_html}
</div>
<div class="note">
巴菲特历年致伯克希尔·哈撒韦股东信<br>
中文翻译整理 · 内部学习资料<br>
{era_label}
</div>
</section>"""


def generate_toc_html(years_data: list[dict]) -> str:
    """生成目录页 HTML。"""
    items = []
    for entry in years_data:
        year = entry["year"]
        cn_year = number_to_chinese(year)
        if entry.get("missing"):
            items.append(f'<li><span class="year">{cn_year}</span> <span class="missing">（缺失）</span></li>')
        else:
            items.append(f'<li><span class="year">{cn_year}</span> 年</li>')
    items_html = "\n".join(items)
    return f"""<section class="toc">
<h2 class="toc-title">目&emsp;&emsp;录</h2>
<ul class="toc-list">
{items_html}
</ul>
</section>"""


def generate_chapter_html(year: int, paras: list[dict]) -> str:
    """生成某一年的章节 HTML。"""
    cn_year = number_to_chinese(year)
    content_html = paras_to_html(paras)
    return f"""<section class="chapter">
<h1 class="chapter-title">{cn_year}年 · 巴菲特致股东信</h1>
<div class="chapter-content">
{content_html}
</div>
</section>"""


def generate_missing_chapter_html(year: int) -> str:
    """缺失年份的占位章节。"""
    cn_year = number_to_chinese(year)
    return f"""<section class="chapter">
<h1 class="chapter-title">{cn_year}年 · 巴菲特致股东信</h1>
<div class="chapter-missing">（{cn_year}年信件缺失，暂未收录）</div>
</section>"""


def build_volume(year_start: int, year_end: int, era_label: str,
                  era_desc: str, output_filename: str):
    """生成指定年代范围的信件分卷。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cn_start = number_to_chinese(year_start)
    cn_end = number_to_chinese(year_end)
    range_label = f"{year_start}-{year_end}"

    print("=" * 60)
    print(f" 上卷：巴菲特致股东信 {range_label} — {era_label}")
    print("=" * 60)

    # 扫描所有可用文件
    existing_years = {int(f.stem) for f in LETTERS_DIR.glob("*.docx")}
    all_years = list(range(year_start, year_end + 1))

    print(f"\n年份范围 {range_label}，共 {len(all_years)} 年\n")

    years_data = []
    chapters_html = []

    for year in all_years:
        if year in existing_years:
            fpath = LETTERS_DIR / f"{year}.docx"
            print(f"  [.] {year}.docx ...", end=" ")
            raw_paras = extract_letter_text(fpath)
            if not raw_paras:
                print("空文件或读取失败")
                years_data.append({"year": year, "missing": True})
                chapters_html.append(generate_missing_chapter_html(year))
                continue
            paras = clean_text(raw_paras)
            print(f"{len(paras)} 段, {sum(1 for p in paras if p['type']!='empty')} 个非空段落")
            years_data.append({"year": year, "missing": False})
            chapters_html.append(generate_chapter_html(year, paras))
        else:
            print(f"  [X] {year}.docx —— 缺失")
            years_data.append({"year": year, "missing": True})
            chapters_html.append(generate_missing_chapter_html(year))

    # ---- 组装 HTML ----
    print("\n[*] 组装 HTML ...")

    cover_html = generate_cover_html(cn_start, cn_end, era_label, era_desc)
    toc_html = generate_toc_html(years_data)
    chapters_all = "\n".join(chapters_html)
    colophon_html = f"""<section class="colophon">
<p>巴菲特致股东信 · {era_label}</p>
<p>{cn_start}年 —— {cn_end}年</p>
<p>中文译本 · 内部学习资料</p>
<p>本电子版仅供学习研究使用</p>
</section>"""

    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>巴菲特致股东信 {range_label} · {era_label}</title>
<style>
{CSS}
</style>
</head>
<body>
{cover_html}
{toc_html}
{chapters_all}
{colophon_html}
</body>
</html>"""

    output_path = OUTPUT_DIR / output_filename
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    total_chars = len(full_html)
    print(f"\n[OK] {era_label} HTML 已生成：{output_path}")
    print(f"   文件大小：{size_mb:.1f} MB")
    print(f"   总字符数：{total_chars:,}")
    print(f"\n[>>] 下一步：在 Chrome 中打开该 HTML → Ctrl+P → 另存为 PDF（纸张选A4）\n")


def build():
    """按三个时代生成三卷：早期/中期/现代。"""
    build_volume(
        1957, 1969,
        "壹 · 早期合伙人时期",
        "纯格雷厄姆式烟蒂股、套利与清算",
        "巴菲特致股东信_壹_早期合伙人时期_1957-1969.html"
    )
    build_volume(
        1971, 1999,
        "贰 · 黄金进化期",
        "向「以合理价格买伟大企业」转型，护城河、能力圈、所有者收益",
        "巴菲特致股东信_贰_黄金进化期_1971-1999.html"
    )
    build_volume(
        2000, 2025,
        "叁 · 巨无霸运营期",
        "巨额资本分配、现金管理、回购、金融危机与通胀应对",
        "巴菲特致股东信_叁_巨无霸运营期_2000-2025.html"
    )


if __name__ == "__main__":
    build()
