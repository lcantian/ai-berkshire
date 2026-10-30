# -*- coding: utf-8 -*-
"""report_audit 抽取预检：逐单元格复现抽取器，找出"取值列首个数字不是真值"的伪影。

用法：
    python3 tools/audit_artifacts.py <报告路径> [--verbose]

与 tools/report_audit.py extract 的关系：
    extract 抽样 30 点做准出判定；本脚本做**全量**预检，用来在提交抽检之前
    把报告里所有会造成伪影的写法找出来并修掉。

判定逻辑（与 report_audit._parse_md_tables 一致）：
    cells = split('|') → 丢弃空单元格 → row_label = cells[0]（不参与取值）
    → cells[1:] 按序对应表头 → 每格用 re.search(r'[~约]?\\$?([\\d,，\\.]+)\\s*(...)?', cell)
    取该格**首个**数字片段
"""
import io
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import report_audit  # noqa: E402

CELL_RE = re.compile(r'[~约]?\$?([\d,，\.]+)')
# 抽取器跳过的列头（精确匹配，大小写不敏感）
SKIP_HEADERS = ("YOY", "YOY增速", "增速", "同比", "变化", "趋势", "说明", "备注")

# 取值列里这些前缀会让首个数字变成无意义的 token
TOKEN_PREFIX = re.compile(r'(Q[1-4]|F\d+|P\d+|第[一二三四]|\d{4}Q[1-4])\b')
YEAR_RE = re.compile(r'(19|20)\d{2}')


def analyze(path, verbose=False):
    text = io.open(path, encoding="utf-8").read()
    points = report_audit.extract_data_points(text)
    lines = text.split("\n")

    issues = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "|" in line and not re.match(r'^\|[\-\s\|:]+\|$', line):
            heads = [h.strip().strip("*_").strip() for h in line.split("|")]
            heads = [h for h in heads if h]
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                dline = lines[j].strip()
                cs = [c.strip().strip("*_~").strip() for c in dline.split("|")]
                cs = [c for c in cs if c != ""]
                if len(cs) >= 2:
                    row_label = cs[0]
                    for ci, cell in enumerate(cs[1:], start=1):
                        ch = heads[ci] if ci < len(heads) else ""
                        if ch.upper() in SKIP_HEADERS:
                            continue
                        m = CELL_RE.search(cell)
                        if not m:
                            continue
                        raw = m.group(1).replace(",", "").replace("，", "")
                        try:
                            val = float(raw)
                        except ValueError:
                            continue
                        pre = cell[:m.start(1)]
                        tail = cell[m.end(1):]
                        hard = []
                        soft = []
                        # (1) 首个数字前紧邻字母/连字符 → token 伪影（Q3→3、P12→12）
                        if pre and re.search(r'[A-Za-z\-/]$', pre[-1:]):
                            hard.append("前缀token(%s)" % pre[-1])
                        # (2) 首个数字是四位年份
                        if 1900 < val < 2100 and len(raw) == 4:
                            hard.append("年份")
                        # (3) 取值格首位出现 Q1..Q4 / 第X 等期间 token
                        if TOKEN_PREFIX.search(pre):
                            hard.append("期间token")
                        # (4) 软提示：同格还有别的数字 —— 首个数字是否是真值需人工确认
                        if re.search(r'[\d]', tail):
                            soft.append("同格多数字")
                        if hard:
                            issues.append((j + 1, row_label, ch, val, cell, hard, "必修"))
                        elif soft:
                            issues.append((j + 1, row_label, ch, val, cell, soft, "待确认"))
                j += 1
            i = j
        else:
            i += 1

    print("=" * 76)
    print("抽取预检：%s" % path)
    print("全量可抽取数据点：%d" % len(points))
    n_hard = sum(1 for x in issues if x[6] == "必修")
    n_soft = sum(1 for x in issues if x[6] == "待确认")
    print("必修伪影：%d    待确认：%d" % (n_hard, n_soft))
    print("=" * 76)
    for ln, rl, ch, val, cell, flags, kind in issues:
        mark = "❌必修" if kind == "必修" else "⚠️待确认"
        print("%s 行%-5d [%s | %s] = %s  <%s>" % (mark, ln, rl[:26], ch[:16], val, ",".join(flags)))
        print("        %s" % cell[:110])
    if not issues:
        print("✅ 未发现伪影")
    if verbose:
        print("\n---- 全部数据点 ----")
        for p in points:
            print("%3d L%-5d %-46s %14s %-6s | %s" % (
                p["id"], p["line_number"], p["label"][:46], p["reported_value"], p["unit"], p["raw_text"][:56]))
    return n_hard


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    analyze(sys.argv[1], "--verbose" in sys.argv)
