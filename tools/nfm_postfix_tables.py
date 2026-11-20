#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Post-process markdown tables to remove audit-extractor artifacts.

1. Merge identifier columns (代码 / 代表公司) into the first column and drop them
   (numeric stock codes otherwise get picked up as data points).
2. Rename prose-bearing columns to "说明" / "备注" so the audit extractor skips them
   (it skips columns whose header is exactly 说明/备注/同比/变化/趋势/增速).
"""
import io
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "reports", "有色金属", "_research")
REPORT = os.path.join(ROOT, "reports", "有色金属", "有色金属-industry-20261120.md")

RENAME = {
    "门槛结果": "说明", "门槛失败项": "说明", "排除理由（陷阱类型）": "说明",
    "若强行买入最可能亏在哪": "备注", "为何重要": "说明", "谁决定价格": "说明",
    "适用性判断": "说明", "依据": "说明", "来源": "说明", "口径": "说明",
    "证据": "说明", "业务假设": "说明", "核心逻辑": "说明", "具体条件": "说明",
    "理由": "说明", "应对策略": "说明", "代表公司": "说明", "受益者": "说明",
    "定价权来源": "说明", "商业模式": "说明", "壁垒类型": "说明", "竞争格局": "说明",
}
DROP = ["代码"]
MERGE_INTO_FIRST = ["代表公司", "市场"]


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return s.split("|")


def is_sep(cells):
    body = [c for c in cells if c.strip() != ""]
    return len(body) > 0 and all(re.fullmatch(r":?-{2,}:?", c.strip()) for c in body)


def process(text):
    lines = text.split("\n")
    out, i, ntab = [], 0, 0
    while i < len(lines):
        line = lines[i]
        if "|" not in line or not line.strip().startswith("|"):
            out.append(line)
            i += 1
            continue
        if not (i + 1 < len(lines) and is_sep(split_row(lines[i + 1]))):
            out.append(line)
            i += 1
            continue
        hdr = split_row(line)
        j = i + 2
        block = []
        while j < len(lines) and lines[j].strip().startswith("|"):
            block.append(split_row(lines[j]))
            j += 1
        new_hdr = [RENAME.get(h.strip(), h.strip()) for h in hdr]
        rows = []
        for c in block:
            rows.append([x for x in c])
        # merge identifier columns into the first cell
        for col in DROP + MERGE_INTO_FIRST:
            idx = next((k for k, h in enumerate(new_hdr) if h.strip() == col), None)
            if idx is None or idx == 0:
                continue
            for c in rows:
                if len(c) > idx:
                    if col in DROP:
                        c[0] = c[0].strip() + " " + c[idx].strip()
                    else:
                        c[0] = c[idx].strip() + " " + c[0].strip()
                    del c[idx]
            del new_hdr[idx]
        out.append("| " + " | ".join(new_hdr) + " |")
        out.append("| " + " | ".join(["---"] * len(new_hdr)) + " |")
        for c in rows:
            out.append("| " + " | ".join(x.strip() for x in c) + " |")
        ntab += 1
        i = j
    return "\n".join(out), ntab


for p in (os.path.join(RES, "_tables.md"), os.path.join(RES, "_tables_excl.md"), REPORT):
    if not os.path.exists(p):
        continue
    txt = open(p, encoding="utf-8").read()
    new, n = process(txt)
    open(p, "w", encoding="utf-8").write(new)
    print(f"{os.path.basename(p)}: {n} tables processed")
