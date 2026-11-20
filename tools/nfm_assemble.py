#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Assemble the final non-ferrous metals industry report from chapter files + generated tables."""
import glob
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = glob.glob(os.path.join(ROOT, "reports", "*", "_research"))[0]
OUT = os.path.join(ROOT, "reports", "有色金属", "有色金属-industry-20261120.md")


def read(p):
    return open(os.path.join(RES, p), encoding="utf-8").read()


tables = read("_tables.md")
excl = read("_tables_excl.md")
head = read("_c0_head.md")
chain = read("_c1_chain.md")
glob_ = read("_c2_global.md")
comp = read("_c3_companies.md")
val = read("_c4_valuation.md")
port = read("_c5_portfolio.md")

# ---- split c1_chain.md: table 1 (before the logic-chain chapter) ----
marker = "\n---\n\n## 第一章"
i = chain.index(marker)
tbl1 = chain[:i]
chain_rest = chain[i:]

# ---- split tables.md ----
m = {}
for key in ["### 表 2", "## 附录 A", "## 附录 B", "## 分组中位数表", "## 附录 C",
            "## 附录 D", "## 附录 E"]:
    m[key] = tables.index(key)
t2 = tables[m["### 表 2"]:m["## 附录 A"]]
apA = tables[m["## 附录 A"]:m["## 附录 B"]]
apB = tables[m["## 附录 B"]:m["## 分组中位数表"]]
grp = tables[m["## 分组中位数表"]:m["## 附录 C"]]
apC = tables[m["## 附录 C"]:m["## 附录 D"]]
apD = tables[m["## 附录 D"]:m["## 附录 E"]]
apE = tables[m["## 附录 E"]:]
apF = read("_c6_appendix.md")
apG = read("_c7_audit.md")

parts = [
    head.rstrip(),
    tbl1.rstrip(),
    t2.rstrip(),
    excl.rstrip(),
    chain_rest.strip(),
    glob_.strip(),
    comp.strip(),
    val.strip(),
    port.strip(),
    "\n---\n\n## 附录 ｜ 全样本明细与数据来源\n",
    apA.strip(), apB.strip(), grp.strip(), apC.strip(), apD.strip(), apE.strip(),
    apF.strip(), apG.strip(),
]
text = "\n\n".join(parts) + "\n"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(text)
print("written", OUT, len(text), "chars,", text.count("\n"), "lines")
