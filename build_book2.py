#!/usr/bin/env python3
"""
巴菲特股东大会问答 —— 下卷
从 巴菲特股东大会1994-2025/ 目录读取所有 .txt 文件，生成适合 A4 打印的 HTML。
"""

import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
MEETINGS_DIR = BASE_DIR / "巴菲特股东大会1994-2025"
OUTPUT_DIR = BASE_DIR / "output"

CSS = r"""
/* ===== 页面设置 ===== */
@page {
    size: A4;
    margin: 2.2cm 2.5cm 2.2cm 2.5cm;
}

/* ===== 全局 ===== */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: "SimSun", "宋体", "Noto Serif CJK SC", "Source Han Serif SC", serif;
    font-size: 10.5pt;
    line-height: 1.85;
    color: #1a1a1a;
    text-align: justify;
}

/* ===== 封面页 ===== */
.cover {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    text-align: center;
    padding: 3cm 2cm;
}

.cover .book-title {
    font-family: "SimHei", "黑体", "Noto Sans CJK SC", sans-serif;
    font-size: 26pt;
    font-weight: bold;
    letter-spacing: 0.3em;
    margin-bottom: 0.6cm;
    line-height: 1.4;
}

.cover .subtitle {
    font-family: "SimHei", "黑体", sans-serif;
    font-size: 14pt;
    color: #555;
    margin-bottom: 1.2cm;
    letter-spacing: 0.1em;
}

.cover .years {
    font-family: "SimSun", "宋体", serif;
    font-size: 12pt;
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
    gap: 0.35cm 1cm;
}

.toc-list li {
    font-size: 10pt;
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

/* ===== 每年 ===== */
.year-section {
    page-break-before: always;
    padding-top: 0.5cm;
}

.year-main-title {
    font-family: "SimHei", "黑体", sans-serif;
    font-size: 20pt;
    text-align: center;
    margin-bottom: 0.3cm;
    letter-spacing: 0.15em;
    padding-bottom: 0.3cm;
    border-bottom: 3px solid #333;
}

.year-missing {
    text-align: center;
    font-size: 12pt;
    color: #888;
    padding: 3cm 0;
    font-style: italic;
}

/* ===== 每场次 ===== */
.session {
    margin-top: 0.8cm;
}

.session-title {
    font-family: "SimHei", "黑体", sans-serif;
    font-size: 14pt;
    text-align: center;
    margin-bottom: 0.6cm;
    padding-bottom: 0.15cm;
    border-bottom: 1px solid #999;
    letter-spacing: 0.1em;
}

.session-content {
    line-height: 1.85;
}

.session-content p {
    text-indent: 2em;
    margin-bottom: 0.25em;
}

.session-content .qa-label {
    font-weight: bold;
    margin-top: 0.5em;
    color: #333;
}

.session-content .speaker {
    font-weight: bold;
    color: #1a1a1a;
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


def number_to_chinese(n: int) -> str:
    """将年份数字转为中文数字。"""
    digits = "零一二三四五六七八九"
    return "".join(digits[int(d)] for d in str(n))


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def scan_meeting_files() -> dict[int, list[tuple[str, Path]]]:
    """
    扫描所有会议文件，返回 {年份: [(标签, 文件路径), ...]}。
    标签如 "上午场（上）"、"下午场（中）"、或 ""（单文件）。
    已按场次排序。
    """
    result: dict[int, list[tuple[str, Path]]] = {}

    # ---- 遍历子目录中的年份文件夹 ----
    for entry in sorted(MEETINGS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        dirname = entry.name
        # 提取年份，如 "1994" 或 "2019"
        match = re.match(r"(\d{4})", dirname)
        if not match:
            continue
        year = int(match.group(1))
        if year not in result:
            result[year] = []

        # 扫描该年文件夹下的所有 txt
        txt_files = sorted(entry.glob("*.txt"))
        for tf in txt_files:
            label = parse_session_label(tf.name, year)
            result[year].append((label, tf))

    # ---- 处理根目录级别的 txt（2023-2025） ----
    for tf in sorted(MEETINGS_DIR.glob("*.txt")):
        match = re.match(r"(\d{4})", tf.stem)
        if match:
            year = int(match.group(1))
            if year not in result:
                result[year] = []
            result[year].append(("", tf))

    # ---- 按标签排序 ----
    session_order = {
        "上午场（上）": 0, "上午场（中）": 1, "上午场（下）": 2,
        "上午场": 2.5,
        "下午场（上）": 3, "下午场（中）": 4, "下午场（下）": 5,
        "下午场": 5.5,
        "第一部分": 10, "第二部分": 11, "第三部分": 12,
        "第四部分": 13, "第五部分": 14, "第六部分": 15,
        "": 20,  # 单文件或无标签
    }
    for year in result:
        result[year].sort(key=lambda x: session_order.get(x[0], 50))

    return result


def parse_session_label(filename: str, year: int) -> str:
    """从文件名解析场次标签。"""
    # 1994-2016 格式: "1994年伯克希尔股东大会Q&A 上午场（上）.txt"
    # 2019 格式: "2019 年伯克希尔·哈撒韦股东大会文字记录.txt"
    # 2020-2022 格式: "2020 年伯克希尔·哈撒韦股东大会文字记录（第一部分）.txt"

    # 先尝试匹配旧格式
    m = re.search(r"(上午场|下午场)[（(]([上中下])[）)]", filename)
    if m:
        session = m.group(1)
        part = m.group(2)
        return f"{session}（{part}）"

    # 新格式：第X部分
    m = re.search(r"第([一二三四五六\d]+)部分", filename)
    if m:
        num = m.group(1)
        if num.isdigit():
            digits_map = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}
            num = digits_map.get(int(num), num)
        return f"第{num}部分"

    # 无分部的场次（如"下午场.txt"无上中下）
    m = re.search(r"(上午场|下午场)", filename)
    if m:
        return m.group(1)

    return ""


def read_file_content(filepath: Path) -> str:
    """读取 txt 文件内容，自动处理编码。"""
    # 尝试常见编码
    for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030"]:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 最后的兜底
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def clean_meeting_content(text: str) -> str:
    """清理会议记录内容，移除无关头部、URL 等。"""
    lines = text.split("\n")
    cleaned = []
    skip_patterns = [
        r"^URL[：:]",
        r"^https?://",
        r"^-{4,}",  # 分隔线
        r"^={4,}",
        r"^\*{4,}",
    ]

    for line in lines:
        stripped = line.strip()
        # 跳过纯分隔线
        if re.match(r"^-{4,}$", stripped) or re.match(r"^={4,}$", stripped) or re.match(r"^\*{4,}$", stripped):
            continue
        # 跳过 URL 行
        if re.match(r"^URL[：:]", stripped) or re.match(r"^https?://", stripped):
            continue
        cleaned.append(line)

    return "\n".join(cleaned)


def content_to_html(text: str) -> str:
    """将会议记录文本转为 HTML 段落。"""
    lines = text.split("\n")
    html_parts = []
    in_header = True  # 跳过开头无关的头部

    for line in lines:
        stripped = line.strip()

        # 空行 → 段落间距
        if not stripped:
            html_parts.append("<p>&nbsp;</p>")
            in_header = False
            continue

        # 检测标题行（## 开头）
        if stripped.startswith("##"):
            title = stripped.lstrip("#").strip()
            html_parts.append(f'<h3 class="session-subtitle">{escape_html(title)}</h3>')
            in_header = False
            continue

        # 检测标题行（### 开头）
        if stripped.startswith("###"):
            title = stripped.lstrip("#").strip()
            html_parts.append(f'<h4 class="qa-title">{escape_html(title)}</h4>')
            in_header = False
            continue

        # 跳过头部元信息
        if in_header and len(stripped) < 60:
            continue

        in_header = False

        # 检测 Q&A 标签
        if re.match(r"^(Q\s*\d+|第\s*\d+\s*[问个题])", stripped):
            html_parts.append(f'<p class="qa-label">{escape_html(stripped)}</p>')
            continue

        # 检测发言者
        if re.match(r"^(巴菲特|芒格|查理|阿吉特|格雷格|阿贝尔|贾恩|贝琪|Becky|股东|观众)", stripped):
            html_parts.append(f'<p class="speaker">{escape_html(stripped)}</p>')
            continue

        # 普通段落
        html_parts.append(f"<p>{escape_html(stripped)}</p>")

    return "\n".join(html_parts)


def generate_cover_html() -> str:
    return """<section class="cover">
<div class="book-title">巴菲特股东大会问答</div>
<div class="subtitle">BERKSHIRE HATHAWAY ANNUAL MEETING Q&amp;A</div>
<div class="divider"></div>
<div class="years">
一九九四年 —— 二〇二五年<br>
中文译本 · 全集
</div>
<div class="note">
巴菲特与芒格在伯克希尔·哈撒韦股东大会上的问答实录<br>
中文翻译整理 · 内部学习资料<br>
下卷
</div>
</section>"""


def generate_toc_html(years_data: list[dict]) -> str:
    items = []
    for entry in years_data:
        year = entry["year"]
        cn_year = number_to_chinese(year)
        if entry.get("missing"):
            items.append(f'<li><span class="year">{cn_year}</span> <span class="missing">（缺失）</span></li>')
        else:
            files_count = entry.get("files", 0)
            items.append(f'<li><span class="year">{cn_year}</span> 年 ({files_count}篇)</li>')
    items_html = "\n".join(items)
    return f"""<section class="toc">
<h2 class="toc-title">目&emsp;&emsp;录</h2>
<ul class="toc-list">
{items_html}
</ul>
</section>"""


def generate_year_html(year: int, sessions: list[tuple[str, Path]]) -> str:
    """生成某一年所有场次的 HTML。"""
    cn_year = number_to_chinese(year)
    parts_html = []

    for label, filepath in sessions:
        try:
            raw = read_file_content(filepath)
        except Exception as e:
            print(f"    [!] 读取失败：{filepath.name} — {e}")
            continue

        cleaned = clean_meeting_content(raw)

        if label:
            parts_html.append(f'<section class="session">')
            parts_html.append(f'<h2 class="session-title">{cn_year}年 · {label}</h2>')
        else:
            # 单文件，不加场次标题
            parts_html.append(f'<section class="session">')

        parts_html.append(f'<div class="session-content">')
        parts_html.append(content_to_html(cleaned))
        parts_html.append(f'</div>')
        parts_html.append(f'</section>')

    sessions_html = "\n".join(parts_html)

    return f"""<section class="year-section">
<h1 class="year-main-title">{cn_year}年 · 伯克希尔股东大会</h1>
{sessions_html}
</section>"""


def generate_missing_year_html(year: int) -> str:
    cn_year = number_to_chinese(year)
    return f"""<section class="year-section">
<h1 class="year-main-title">{cn_year}年 · 伯克希尔股东大会</h1>
<div class="year-missing">（{cn_year}年股东大会问答记录缺失，暂未收录）</div>
</section>"""


def build_volume(year_start: int, year_end: int, volume_label: str, output_filename: str):
    """生成指定年份范围的分卷 HTML。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cn_start = number_to_chinese(year_start)
    cn_end = number_to_chinese(year_end)
    range_label = f"{year_start}-{year_end}"

    print("=" * 60)
    print(f" 股东大会问答 · {volume_label}：{range_label}")
    print("=" * 60)

    # ---- 步骤 1：扫描所有文件 ----
    print("\n[*] 扫描会议文件 ...\n")
    files_by_year = scan_meeting_files()

    # 筛选年份
    filtered = {y: files_by_year[y] for y in files_by_year if year_start <= y <= year_end}
    total_files = sum(len(v) for v in filtered.values())
    print(f"年份范围 {range_label}，共 {len(filtered)} 个年份，{total_files} 个文件\n")

    for year in sorted(filtered.keys()):
        sessions = filtered[year]
        labels = [lbl for lbl, _ in sessions]
        print(f"  {year}: {len(sessions)} 个文件 → {labels}")

    # ---- 步骤 2：构建 HTML ----
    all_years = list(range(year_start, year_end + 1))
    years_data = []
    sections_html = []

    print("\n[*] 处理文件内容 ...\n")
    for year in all_years:
        if year in filtered:
            sessions = filtered[year]
            total_chars = 0
            for _, fp in sessions:
                try:
                    total_chars += len(read_file_content(fp))
                except Exception:
                    pass
            print(f"  [.] {year}年 — {len(sessions)} 个文件, ~{total_chars:,} 字符")
            years_data.append({"year": year, "missing": False, "files": len(sessions)})
            sections_html.append(generate_year_html(year, sessions))
        else:
            print(f"  [X] {year}年 —— 缺失")
            years_data.append({"year": year, "missing": True, "files": 0})
            sections_html.append(generate_missing_year_html(year))

    # ---- 步骤 3：组装 HTML ----
    print("\n[*] 组装 HTML ...")

    cover_html = f"""<section class="cover">
<div class="book-title">巴菲特股东大会问答</div>
<div class="subtitle">BERKSHIRE HATHAWAY ANNUAL MEETING Q&amp;A</div>
<div class="divider"></div>
<div class="years">
{cn_start}年 —— {cn_end}年<br>
中文译本
</div>
<div class="note">
巴菲特与芒格在伯克希尔·哈撒韦股东大会上的问答实录<br>
中文翻译整理 · 内部学习资料<br>
{volume_label}
</div>
</section>"""

    toc_html = generate_toc_html(years_data)
    chapters_all = "\n".join(sections_html)
    colophon_html = f"""<section class="colophon">
<p>巴菲特股东大会问答 · {volume_label}</p>
<p>{cn_start}年 —— {cn_end}年</p>
<p>中文译本 · 内部学习资料</p>
<p>本电子版仅供学习研究使用</p>
</section>"""

    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>巴菲特股东大会问答 {range_label} · {volume_label}</title>
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
    total_chars_all = len(full_html)
    print(f"\n[OK] {volume_label} HTML 已生成：{output_path}")
    print(f"   文件大小：{size_mb:.1f} MB")
    print(f"   总字符数：{total_chars_all:,}")
    print(f"\n[>>] 下一步：在 Chrome 中打开该 HTML → Ctrl+P → 另存为 PDF（纸张选A4）\n")


def build():
    """按三阶段框架生成会议问答分卷（会议记录仅从1994年开始）。"""
    build_volume(
        1994, 1999,
        "贰 · 黄金进化期",
        "股东大会问答_贰_黄金进化期_1994-1999.html"
    )
    build_volume(
        2000, 2012,
        "叁 · 巨无霸运营期（上）",
        "股东大会问答_叁a_巨无霸运营期_2000-2012.html"
    )
    build_volume(
        2013, 2025,
        "叁 · 巨无霸运营期（下）",
        "股东大会问答_叁b_巨无霸运营期_2013-2025.html"
    )


if __name__ == "__main__":
    build()
