#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""有色金属行业研究 — 报告表格生成器（所有数字脚本实算，禁止手写）。"""
import json, os, statistics, sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_nonferrous import UNIVERSE  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, "reports", "有色金属", "_research")
D = json.load(open(os.path.join(BASE, "_analysis.json"), encoding="utf-8"))
BY = {m["code"]: m for m in D}
COMMOD = json.load(open(os.path.join(ROOT, "data", "nonferrous", "commodity.json"), encoding="utf-8"))
GLOBAL = json.load(open(os.path.join(ROOT, "data", "nonferrous", "global_1119.json"), encoding="utf-8"))
# global_1119.json：2026-11-19 收盘口径（价格取日 K 不复权收盘，PE/PB/市值由 11-20 快照按价格比例回算）


def f(v, n=2):
    return ('%.*f' % (n, v)) if v is not None else '—'


def fp(v, pct=False):
    """审计口径精度：|v|<1 写 3 位小数，其余 2 位（1% 相对容差下四舍五入必须留足位数）"""
    if v is None:
        return '—'
    d = 3 if abs(v) < 1 else 2
    return ('%.*f' % (d, v)) + ('%' if pct else '')


def med(vals):
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 2) if vals else None


out = []
W = out.append

# ============================================================ 表2 质量门槛名单
FLABEL = {"i1_roe": "①ROE10y<8%", "i2_fcf": "②FCF5y<0", "i3_icov": "③利息覆盖<2",
          "i4_gm": "④毛利率<15%", "i5_ocfni": "⑤OCF/NI<0.7", "i6_nm": "⑥净利率<5%"}
W("### 表 2 ｜ 质量门槛通过 / 未通过名单（A/B 通道）\n")
W("| 公司 | 代码 | 环节 | ①ROE10y | ②FCF5y(亿) | ③利息覆盖 | ④毛利率10y | ⑤OCF/NI | ⑥净利率10y | ⑦经济稀释(观察) | 豁免 | 门槛结果 |")
W("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|")
for m in D:
    s = m["screen"]
    marks = lambda ok: "✅" if ok else "❌"
    ex = "、".join(m["screen_exempt"]) if m["screen_exempt"] else "—"
    W(f"| {m['name']} | {m['code']} | {m['segment']} | {marks(s['i1_roe'][0])} {fp(s['i1_roe'][1],True)} "
      f"| {marks(s['i2_fcf'][0])} {fp(s['i2_fcf'][1])} | {marks(s['i3_icov'][0])} {fp(s['i3_icov'][1])} "
      f"| {marks(s['i4_gm'][0])} {fp(s['i4_gm'][1],True)} | {marks(s['i5_ocfni'][0])} {fp(s['i5_ocfni'][1])} "
      f"| {marks(s['i6_nm'][0])} {fp(s['i6_nm'][1],True)} | {'👁' if s['i7_dilution'][0] else '—'} {fp(s['i7_dilution'][1],True)} "
      f"| {ex} | {'**通过**' if m['screen_pass'] else '**排除** ' + '、'.join(FLABEL[x] for x in m['screen_fails'])} |")
W("")
passed = [m for m in D if m["screen_pass"]]
failed = [m for m in D if not m["screen_pass"]]
W(f"**门槛通过 {len(passed)} 家 / {len(D)} 家（{len(passed)*100.0/len(D):.1f}%）；排除 {len(failed)} 家。**\n")

# ============================================================ 附录A 逐家明细
W("## 附录 A ｜ 质量门槛与生意质量逐家明细（68 家）\n")
W("| 代码 | 名称 | 环节 | ROE10y均 | ROE5y均 | 毛利率10y | 毛利率5y | 净利率10y | 净利率5y | OCF/NI5y | FCF5y(亿) | 利息覆盖5y最低 | 资本开支/收入5y | 经济稀释 | 门槛 |")
W("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
for m in D:
    W(f"| {m['code']} | {m['name']} | {m['segment']} | {fp(m.get('roe_10y_avg'),True)} | {fp(m.get('roe_5y_avg'),True)} "
      f"| {fp(m.get('gm_10y_avg'),True)} | {fp(m.get('gm_5y_avg'),True)} | {fp(m.get('nm_10y_avg'),True)} | {fp(m.get('nm_5y_avg'),True)} "
      f"| {fp(m.get('ocf_ni_5y_avg'))} | {fp(m.get('fcf_5y_yi'))} | {fp(m.get('icov_5y_min'))} | {fp(m.get('capex_rev_5y_avg'),True)} "
      f"| {fp(m.get('economic_dilution'),True)} | {'通过' if m['screen_pass'] else '排除'} |")
W("")

# ============================================================ 附录B 估值+周期明细
W("## 附录 B ｜ 估值锚点、分位与库存周期逐家明细（68 家）\n")
W("| 代码 | 名称 | 环节 | 市值(亿) | PE(TTM归母) | PE(TTM扣非) | 正常化PE3y | 正常化PE5y | 单季年化PE | 扣非/归母 | PE分位3y | PE分位全历史 | PS分位3y | PS分位全历史 | PE-PS分歧 | 存货同比 | 存货−收入增速差 | TTM周转天数 | 上年同期 | 差 | 合同负债同比 | 单季存货增量(亿) | 52w高日 | 距52w高 | 自2026-01-29 |")
W("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for m in D:
    c = m.get("cycle", {})
    W(f"| {m['code']} | {m['name']} | {m['segment']} | {f(m.get('mcap_yi'),0)} | {f(m.get('pe_ttm'))} | {f(m.get('pe_ttm_ded'))} "
      f"| {f(m.get('pe_norm_3y'))} | {f(m.get('pe_norm_5y'))} | {f(m.get('pe_q_ann'))} | {fp(m.get('ded_ratio'),True)} "
      f"| {fp(m.get('pe_pct_3y'),True)} | {fp(m.get('pe_pct_all'),True)} | {fp(m.get('ps_pct_3y'),True)} | {fp(m.get('ps_pct_all'),True)} "
      f"| {fp(m.get('pe_ps_div_3y'))} | {fp(c.get('inv_yoy'),True)} | {fp(c.get('inv_rev_spread'))} | {fp(c.get('ttm_days'))} "
      f"| {fp(c.get('ttm_days_ly'))} | {fp(c.get('ttm_days_delta'))} | {fp(c.get('contract_yoy'),True)} | {fp(c.get('inv_qoq_yi'))} "
      f"| {m.get('w52_high_date') or '—'} | {f(m.get('dd_from_w52'),1)}% | {f(m.get('ret_since_peak'),1)}% |")
W("")

# ============================================================ 分组中位数
W("## 分组中位数表（周期三指标，按产业链环节）\n")
W("| 环节分组 | 家数 | 存货同比中位 | 存货−收入增速差中位 | TTM周转天数中位 | 上年同期中位 | 差值中位 | 合同负债同比中位 | PE(TTM)中位 | PE分位3y中位 | PS分位3y中位 |")
W("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
groups = defaultdict(list)
for m in D:
    groups[m["segment"]].append(m)
for g, ms in groups.items():
    def gm(k):
        return med([x.get("cycle", {}).get(k) for x in ms])
    def mm(k):
        return med([x.get(k) for x in ms])
    W(f"| {g} | {len(ms)} | {fp(gm('inv_yoy'),True)} | {fp(gm('inv_rev_spread'))} | {fp(gm('ttm_days'))} "
      f"| {fp(gm('ttm_days_ly'))} | {fp(gm('ttm_days_delta'))} | {fp(gm('contract_yoy'),True)} "
      f"| {f(mm('pe_ttm'))} | {fp(mm('pe_pct_3y'),True)} | {fp(mm('ps_pct_3y'),True)} |")
W("")
# 全行业
def gm2(k):
    return med([x.get("cycle", {}).get(k) for x in D])
W(f"**全样本（{len(D)} 家）中位数**：存货同比 {fp(gm2('inv_yoy'),True)} ｜ 存货−收入增速差 {fp(gm2('inv_rev_spread'))} pct "
  f"｜ TTM 存货周转天数 {fp(gm2('ttm_days'))} 天（上年同期 {fp(gm2('ttm_days_ly'))} 天，差 {fp(gm2('ttm_days_delta'))} 天）"
  f"｜ 合同负债同比 {fp(gm2('contract_yoy'),True)}\n")

# ============================================================ 价格周期总表
W("## 附录 C ｜ 商品价格周期总表（沪/广期所主力连续，新浪行情接口）\n")
W("| 品种 | 2026年内最高价 | 说明 | 当前价(2026-11-19) | 距年内高 | 2026年初至今 | 2025全年 | 25Q3均价 | 25Q4均价 | 26Q1均价 | 26Q2均价 | 26Q3均价 | Q3环比 | 2026-01-29收盘 | 自板块顶 |")
W("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for sym, obj in COMMOD.items():
    kl = obj["kline"]
    cur = kl[-1]
    y26 = [r for r in kl if r["d"] >= "2026-01-01"]
    hi = max(y26, key=lambda r: r["h"])
    qa = defaultdict(list)
    for r in kl:
        y, m = int(r["d"][:4]), int(r["d"][5:7])
        qa[f"{y}Q{(m-1)//3+1}"].append(r["c"])
    qa = {k: sum(v)/len(v) for k, v in qa.items()}
    base = next((r["c"] for r in reversed(kl) if r["d"] <= "2024-12-31"), None)
    e25 = next((r["c"] for r in reversed(kl) if r["d"] <= "2025-12-31"), None)
    ret25 = (e25/base-1)*100 if base and e25 else None
    ytd = (cur["c"]/e25-1)*100 if e25 else None
    at = next((r for r in kl if r["d"] == "2026-01-29"), None)
    since = (cur["c"]/at["c"]-1)*100 if at else None
    seq = [qa.get(x) for x in ["2025Q3", "2025Q4", "2026Q1", "2026Q2", "2026Q3"]]
    qoq = (seq[4]/seq[3]-1)*100 if seq[3] and seq[4] else None
    W(f"| {obj['name']} | {f(hi['h'],2)} | {hi['d']} | {f(cur['c'],2)} | {f((cur['c']/hi['h']-1)*100,1)}% "
      f"| {f(ytd,1)}% | {f(ret25,1)}% | {' | '.join(f(x,2) for x in seq)} | {f(qoq,2)}% "
      f"| {f(at['c'],2) if at else '—'} | {f(since,1)}% |")
W("")

# ============================================================ 板块顶统计
W("## 附录 D ｜ A 股有色板块集体见顶证据（52 周高点日期分布）\n")
c = Counter(m.get("w52_high_date") for m in D if m.get("w52_high_date"))
W("| 52 周高点日期 | 家数 | 占比 |")
W("|---|---:|---:|")
for k, v in sorted(c.items(), key=lambda kv: -kv[1]):
    W(f"| {k} | {v} | {v*100.0/len(D):.1f}% |")
w = sum(v for k, v in c.items() if "2026-01-20" <= k <= "2026-02-10")
W(f"\n**落在 2026-01-20 至 2026-02-10 窗口内：{w} 家 / {len(D)} 家 = {w*100.0/len(D):.1f}%。**\n")

# ============================================================ 全球扫描
W("## 附录 E ｜ 全球同业扫描（港股 / 美股，腾讯行情接口，本币）\n")
W("| 代码 | 名称 | 环节 | 最新价 | PE(TTM) | PB | 总市值(亿, 本币) | 说明 |")
W("|---|---|---|---:|---:|---:|---:|---|")
for d in GLOBAL:
    W(f"| {d['sym']} | {d['cn']} | {d['segment']} | {f(d['price'],3 if d['price'] and d['price'] < 1 else 2)} | {f(d['pe'])} | {f(d['pb'])} "
      f"| {f(d['mcap'], 2 if d['mcap'] and abs(d['mcap']) < 100 else 1)} {d['currency']} | 2026-11-19 收盘 |")
W("")

path = os.path.join(BASE, "_tables.md")
open(path, "w", encoding="utf-8").write("\n".join(out))
print("written", path, len("\n".join(out)), "chars")
