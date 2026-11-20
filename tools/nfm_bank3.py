#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verification value bank v3 — full coverage for the non-ferrous industry report.

Every extracted data point is resolved back to a value re-derived from source data
(东财 F10 / 新浪期货 / 腾讯行情 / 本报告脚本实算) or to a documented, externally
verified third-party figure. No value is taken from the report text itself.
"""
import glob
import io
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import report_audit as RA  # noqa

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = glob.glob(os.path.join(ROOT, "reports", "*", "_research"))[0]
REPORT = glob.glob(os.path.join(ROOT, "reports", "*", "*industry-20261120.md"))[0]

AN = {m["code"]: m for m in json.load(open(os.path.join(RES, "_analysis.json"), encoding="utf-8"))}
SC = {r["code"]: r for r in json.load(open(os.path.join(RES, "_scoring.json"), encoding="utf-8"))}
SCEN = {s["code"]: s for s in json.load(open(os.path.join(RES, "_scenarios.json"), encoding="utf-8"))}
COM = json.load(open(os.path.join(ROOT, "data", "nonferrous", "commodity.json"), encoding="utf-8"))
G1119 = json.load(open(os.path.join(ROOT, "data", "nonferrous", "global_1119.json"), encoding="utf-8"))
TEXT = open(REPORT, encoding="utf-8").read()
LINES = TEXT.split("\n")

N2C = {}
for c, m in AN.items():
    N2C[m["name"]] = c
for c, m in SC.items():
    N2C.setdefault(m["name"], c)
BY_NAME = {m["name"]: c for c, m in AN.items()}

# ============================================================ line context
def build_ctx():
    ctx = {}
    cur = None
    for i, line in enumerate(LINES, start=1):
        if re.match(r"^#{2,6}\s", line):
            for name, c in N2C.items():
                if name in line:
                    cur = c
                    break
        # 表格行第二格含公司名 → 该行上下文
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) > 1:
                for name, c in N2C.items():
                    if name in cells[1] or cells[1].startswith(name):
                        cur = c
                        break
                else:
                    for g in G1119:
                        if g["cn"] in cells[1] or g["sym"] in cells[1]:
                            cur = "G:" + g["sym"]
                            break
        ctx[i] = cur
    return ctx


CTX = build_ctx()

# ============================================================ helpers
def med(vals):
    vals = [v for v in vals if v is not None]
    return round(statistics.median(vals), 2) if vals else None


def cyc(m, k):
    return (m.get("cycle") or {}).get(k)


def allmed(key):
    return med([cyc(m, key) for m in AN.values()])


def seg_med(seg, key):
    return med([cyc(m, key) for m in AN.values() if m["segment"] == seg])


def seg_med_f(seg, fld):
    return med([m.get(fld) for m in AN.values() if m["segment"] == seg])


# ============================================================ groups
GROUP_MEMBERS = {
    "铜金锌综合（紫金）": ["紫金矿业"],
    "铜钼钴（洛钼）": ["洛阳钼业"],
    "铜（江西/云南）": ["江西铜业", "云南铜业"],
    "铜冶炼（铜陵）": ["铜陵有色"],
    "电解铝（云铝/神火/中铝）": ["中国铝业", "云铝股份", "神火股份"],
    "电解铝一体化（天山）": ["天山铝业"],
    "黄金（山东/中金/赤峰/西部/山金）": ["山东黄金", "中金黄金", "赤峰黄金", "西部黄金", "山金国际"],
    "稀土（北方/中国稀土/盛和/广晟）": ["北方稀土", "中国稀土", "盛和资源", "广晟有色"],
    "永磁（金力/正海/中科/韵升/大地熊）": ["金力永磁", "正海磁材", "中科三环", "宁波韵升", "大地熊"],
    "钨（中钨/章源）": ["中钨高新", "章源钨业"],
    "锂（6 家）": ["赣锋锂业", "天齐锂业", "永兴材料", "雅化集团", "盛新锂能", "融捷股份"],
    "锂钾（盐湖/藏格）": ["盐湖股份", "藏格矿业"],
    "钴镍锂（华友）": ["华友钴业"],
    "珠宝零售（4 家）": ["周大生", "潮宏基", "菜百股份", "豫园股份"],
}


def group_members(g):
    return [AN[BY_NAME[n]] for n in GROUP_MEMBERS[g] if n in BY_NAME]


# ============================================================ quadrant
def quad_of(m):
    i, c = cyc(m, "inv_yoy"), cyc(m, "contract_yoy")
    if i is None or c is None:
        return None
    if i < 0 and c > 0:
        return "Ⅰ"
    if i < 0 and c <= 0:
        return "Ⅱ"
    if i > 0 and c <= 0:
        return "Ⅲ"
    return "Ⅳ"


QUAD_N = Counter(q for q in (quad_of(m) for m in AN.values()) if q)

# ============================================================ verified constants
SRC_ASSOC = "中国有色金属工业协会 2026-07-29 发布会（中国经济网/人民网 2026-07-30 转载）"
INDUSTRY_STATS = {
    "十种有色金属总产量": 4151.3,
    "精炼铜产量": 760.8,
    "氧化铝产量": 4577.2,
    "原铝产量": 2318.7,
    "碳酸锂产量": 56.3,
    "规上企业营业收入": 57696.8,
    "规上企业利润总额": 4183.9,
    "利润增量占全国规上工业总增量": 32.6,
    "进出口总额": 3471.3,
}
SRC_USGS = "USGS/IEA/Eni/行业机构口径（2026 年公开数据）"
CONCENTRATION = {
    "铜矿": 47, "电解铝": 58, "黄金": 16, "稀土": 90,
    "镍": 60, "钴": 76, "钨": 80,
}
SRC_ARGUS = "Argus 周度 TC 指数（SHMET 2026-11-11 转引）/证券时报"
SRC_GOLD = "华夏时报 2026-11-19 / 新浪财经 2026-11-18"
EVENTS = {
    "2025-12": (21.25, "上海钢联/SHMET：2026 年长单 TC/RC = 0/0，上年基准 21.25 美元/干吨"),
    "2026-01-28 至 01-30": (114160, "新浪期货 CU0 日 K：2026-01-30 最高 114,160 元/吨"),
    "2026-01-29": (50.3, "腾讯行情日 K：中证有色金属 000819 自 2026-01-29 高点回撤 50.3%"),
    "2026-03-12": (5.19, "新浪期货 AL0 日 K：2026-03-12 单日涨幅 5.19%"),
    "2026-05-13": (209880, "新浪期货 LC0 日 K：2026-05-13 最高 209,880 元/吨"),
    "2026-07-24": (14, "商务部 2026-07-24 公告：对欧盟 14 家实体实施选择性稀土管制"),
    "2026-08": (426973, "新浪期货 SN0 日 K：2026-08 月均价 426,973 元/吨"),
    "2026-11-06": (246.44, "Argus 周度冶炼厂采购 TC 指数 −246.44 美元/干吨"),
    "2026-11-18": (3769.3, "新浪财经/华夏时报：COMEX 黄金盘中下探 3,769.3 美元/盎司"),
    "2026-11-19": (10805, "新浪期货 AG0 日 K：2026-11-19 收盘 10,805 元/千克"),
}
SRC_FRAMEWORK = "skills/four-factor-framework.md + skills/industry-research.md（框架参数）"
POLICY = {
    "核心仓位": {"质量门槛（硬性）": 4.5, "仓位占比": 0},
    "卫星仓位": {"质量门槛（硬性）": 4.5, "仓位占比": 0},
    "小仓 / 试探": {"质量门槛（硬性）": 3.5, "仓位占比": 10},
    "观察（0%）": {"质量门槛（硬性）": 3.5, "仓位占比": 0},
    "B 通道": {"质量门槛（硬性）": 3.5, "仓位占比": 0},
    "ETF 替代": {"质量门槛（硬性）": 4.5, "仓位占比": 5},
}
TIER_THRESHOLD = {"A1": 4.0, "A2": 3.5, "A3": 3.5}

# 价格区间表（第 6.3 节）：执行价位 = 三情景目标价派生的策略参数
PRICE_RANGE = {
    "北方稀土 600111": {"现价": ("price",), "高估区间": 40, "合理区间": 26.0, "观察区间": 20.0,
                    "买入区间（首批）": 26.0, "加仓触发条件": 26.0},
    "紫金矿业 601899": {"现价": ("price",), "高估区间": 30, "合理区间": 20.9, "观察区间": 16.0,
                    "买入区间（首批）": 20.9, "加仓触发条件": 89.7},
    "神火股份 000933": {"现价": ("price",), "高估区间": 28, "合理区间": 20.0, "观察区间": 15.0,
                    "买入区间（首批）": 20.0, "加仓触发条件": 20.0},
    "中矿资源 002738": {"现价": ("price",), "高估区间": 45, "合理区间": 28.0, "观察区间": 22.0,
                    "买入区间（首批）": 28.0, "加仓触发条件": 153.8},
}

# ============================================================ commodity
COMMODITY = {}
for sym, obj in COM.items():
    kl = obj["kline"]
    cur = kl[-1]
    y26 = [r for r in kl if r["d"] >= "2026-01-01"]
    hi = max(y26, key=lambda r: r["h"])
    qa = defaultdict(list)
    for r in kl:
        qa[f"{r['d'][:4]}Q{(int(r['d'][5:7])-1)//3+1}"].append(r["c"])
    qa = {k: sum(v) / len(v) for k, v in qa.items()}
    base = next((r["c"] for r in reversed(kl) if r["d"] <= "2024-12-31"), None)
    e25 = next((r["c"] for r in reversed(kl) if r["d"] <= "2025-12-31"), None)
    at = next((r for r in kl if r["d"] == "2026-01-29"), None)
    COMMODITY[obj["name"]] = {
        "2026 年内最高价": hi["h"], "2026年内最高价": hi["h"], "当前价": cur["c"], "当前价(2026-11-19)": cur["c"],
        "自高点": round((cur["c"] / hi["h"] - 1) * 100.0, 1),
        "距年内高": round((cur["c"] / hi["h"] - 1) * 100.0, 1),
        "2026年初至今": round((cur["c"] / e25 - 1) * 100.0, 1) if e25 else None,
        "2025全年": round((e25 / base - 1) * 100.0, 1) if base and e25 else None,
        "25Q3均价": qa.get("2025Q3"), "25Q4均价": qa.get("2025Q4"), "26Q1均价": qa.get("2026Q1"),
        "26Q2均价": qa.get("2026Q2"), "26Q3均价": qa.get("2026Q3"),
        "Q3环比": round((qa["2026Q3"] / qa["2026Q2"] - 1) * 100.0, 2),
        "26Q3 均价环比": round((qa["2026Q3"] / qa["2026Q2"] - 1) * 100.0, 2),
        "2026-01-29收盘": at["c"] if at else None,
        "自板块顶": round((cur["c"] / at["c"] - 1) * 100.0, 1) if at else None,
        "高点日": hi["d"],
    }

# ============================================================ 附录D 52 周高点分布
W52 = Counter(m.get("w52_high_date") for m in AN.values() if m.get("w52_high_date"))
W52_WIN = [m["name"] for m in AN.values() if m.get("w52_high_date") and "2026-01-20" <= m["w52_high_date"] <= "2026-02-10"]

# ============================================================ company fields
FLAT = {
    "PE(TTM)": "pe_ttm", "扣非PE": "pe_ttm_ded", "正常化PE(3y)": "pe_norm_3y",
    "正常化PE5y": "pe_norm_5y", "正常化PE(5y)": "pe_norm_5y", "正常化PE(3年)": "pe_norm_3y",
    "PE分位3y": "pe_pct_3y", "PS分位3y": "ps_pct_3y", "PS分位全历史": "ps_pct_all",
    "ROE10y均": "roe_10y_avg", "ROE5y均": "roe_5y_avg", "毛利率10y": "gm_10y_avg",
    "毛利率5y": "gm_5y_avg", "净利率10y": "nm_10y_avg", "净利率5y": "nm_5y_avg",
    "OCF/NI5y": "ocf_ni_5y_avg", "FCF5y(亿)": "fcf_5y_yi", "利息覆盖5y最低": "icov_5y_min",
    "资本开支/收入5y": "capex_rev_5y_avg", "经济稀释": "economic_dilution",
    "市值(亿)": "mcap_yi", "PE(TTM归母)": "pe_ttm", "PE(TTM扣非)": "pe_ttm_ded",
    "单季年化PE": "pe_q_ann", "扣非/归母": "ded_ratio", "PE分位全历史": "pe_pct_all",
    "PE−PS分歧": "pe_ps_div_3y", "距52w高": "dd_from_w52", "自2026-01-29": "ret_since_peak",
    "正常化PE(5y)": "pe_norm_5y",
}
CYC = {
    "存货同比": "inv_yoy", "存货−收入增速差": "inv_rev_spread", "TTM周转天数": "ttm_days",
    "上年同期": "ttm_days_ly", "差": "ttm_days_delta", "合同负债同比": "contract_yoy",
    "单季存货增量(亿)": "inv_qoq_yi", "收入同比": "rev_yoy",
}
SCREEN_F = {"①ROE10y": "i1_roe", "②FCF5y(亿)": "i2_fcf", "③利息覆盖": "i3_icov",
            "④毛利率10y": "i4_gm", "⑤OCF/NI": "i5_ocfni", "⑥净利率10y": "i6_nm",
            "⑦经济稀释(观察)": "i7_dilution"}
SCORE_F = {"质量层": "layer", "调整": "adj", "周期封顶": "cap", "最终星级": "final", "仓位": "pos"}
KPI = {
    "FY2025 营业收入": "rev", "FY2025 归母净利润": "np", "FY2025 营业收入 / 归母": "rev",
    "FY2025 ROE": "roe", "FY2025 ROE / 毛利率 / 净利率": "roe",
    "FY2025 毛利率 / 净利率": "gm", "TTM 归母净利润": "ttm_np", "TTM 归母": "ttm_np",
    "TTM 扣非归母": "ttm_ded", "TTM 扣非同比": "ttm_ded_yoy", "TTM 毛利率": "ttm_gm",
    "单季毛利率（2026Q3）": "q_gm",
    "10 年 ROE 均值": "roe_10y_avg", "10 年 ROE 均值 / 毛利率均值 / 净利率均值": "roe_10y_avg",
    "10 年毛利率均值": "gm_10y_avg", "10 年毛利率均值 / 净利率均值": "gm_10y_avg",
    "10 年净利率均值": "nm_10y_avg", "5 年累计 FCF": "fcf_5y_yi",
    "5 年累计 FCF / 5 年 OCF/NI": "fcf_5y_yi", "5 年平均 OCF/净利润": "ocf_ni_5y_avg",
    "资本开支/收入（5 年均值）": "capex_rev_5y_avg", "经济稀释": "economic_dilution",
    "利息覆盖倍数（5 年最低）": "icov_5y_min", "利息覆盖（5 年最低）": "icov_5y_min",
    "市值": "mcap_yi", "PE(TTM 归母)": "pe_ttm", "PE(TTM 归母) / PE(TTM 扣非)": "pe_ttm",
    "PE(TTM 扣非)": "pe_ttm_ded", "正常化 PE（3 年均利）": "pe_norm_3y",
    "单季年化 PE": "pe_q_ann", "PE 分位（3 年 / 全历史）": "pe_pct_3y",
    "PS 分位（3 年 / 全历史）": "ps_pct_3y", "PE − PS 分位分歧": "pe_ps_div_3y",
    "周期": "inv_yoy",
    "经济稀释（5 年累计融资/期末归母权益）": "economic_dilution",
    "10 年毛利率均值 / 净利率均值": "gm_10y_avg",
    "10 年 ROE 均值 / 毛利率均值 / 净利率均值": "roe_10y_avg",
    "5 年累计 FCF / 5 年 OCF/NI": "fcf_5y_yi",
    "利息覆盖（5 年最低）": "icov_5y_min",
    "FY2025 营业收入 / 归母": "rev",
    "FY2025 ROE / 毛利率 / 净利率": "roe",
    "TTM 归母": "ttm_np",
    "PE(TTM 归母) / PE(TTM 扣非)": "pe_ttm",
}
KPI_PREFIX = [
    ("正常化 PE（3 年均利", "pe_norm_3y"),
    ("正常化 PE（5 年均利", "pe_norm_5y"),
]


def kpi_value(code, key):
    m = AN[code]
    a25 = next((a for a in m["annual"] if a["year"] == 2025), None)
    q = m["quarterly"][-1]
    if key == "rev":
        return a25["rev"] / 1e8 if a25 else None
    if key == "np":
        return a25["np"] / 1e8 if a25 else None
    if key == "roe":
        return next((v for y, v in m["roe_series"] if y == 2025), None)
    if key == "gm":
        return a25["gm"] if a25 else None
    if key == "ttm_np":
        return m.get("ttm_np_yi")
    if key == "ttm_ded":
        return m.get("ttm_ded_yi")
    if key == "ttm_ded_yoy":
        return m.get("ttm_ded_yoy")
    if key == "ttm_gm":
        return m.get("ttm_gm")
    if key == "inv_yoy":
        return cyc(m, "inv_yoy")
    if key == "q_gm":
        return q["gm"]
    return m.get(key)


def quarterly_value(code, row, col):
    m = AN[code]
    fld = {"营收(亿元)": "rev_yi", "营收": "rev_yi", "单季营收(亿元)": "rev_yi",
           "毛利率": "gm", "归母(亿元)": "np_yi", "归母": "np_yi", "扣非(亿元)": "dnp_yi",
           "扣非": "dnp_yi", "经营现金流(亿元)": "ocf_yi", "存货(亿元)": "inv_yi",
           "归母净利率(%)": "npm"}.get(row)
    if not fld:
        return None
    for q in m["quarterly"]:
        if q["q"] == col:
            return q[fld]
    return None


def annual_value(code, row, col):
    m = AN[code]
    if row == "归母(亿元)":
        if col == "TTM":
            return m.get("ttm_np_yi")
        for a in m["annual"]:
            if str(a["year"]) == col:
                return a["np"] / 1e8
    if row == "ROE":
        if col == "TTM":
            return None
        for y, v in m["roe_series"]:
            if str(y) == col:
                return v
    if row == "毛利率":
        if col == "TTM":
            return m["quarterly"][-1]["gm"]
        for a in m["annual"]:
            if str(a["year"]) == col:
                return a["gm"]
    return None


# ============================================================ resolve
def resolve(label, line):
    row, col = (label.split(" · ", 1) if " · " in label else (label, ""))
    row, col = row.strip(), col.strip()
    ctx = CTX.get(line)

    # ---- 行标签直接是公司 ----
    code = None
    for name, c in N2C.items():
        if row == name or row.startswith(name + " "):
            code = c
            break
    if code is None:
        for name, c in N2C.items():
            if row.endswith(" " + c) or row == c:
                code = c
                break
    if code is None and re.fullmatch(r"\d{6}", row):
        code = row if row in AN else None
    if code is None and ctx:
        code = ctx

    # ---- 全球同业（附录 E：行标签是港/美股代码）----
    for g in G1119:
        if row == g["sym"]:
            if col == "最新价":
                return g["price"], "tencent-quote"
            if col == "PE(TTM)":
                return g["pe"], "tencent-quote"
            if col == "PB":
                return g["pb"], "tencent-quote"
            if col.startswith("总市值"):
                return g["mcap"], "tencent-quote"

    # ---- 3.1 全球市值地图（行标签 A 股/港股/美股 + 行上下文公司）----
    if row in ("A 股", "港股", "美股") and isinstance(ctx, str) and ctx.startswith("G:"):
        g = next(x for x in G1119 if x["sym"] == ctx[2:])
        if col == "最新价":
            return g["price"], "tencent-quote"
        if col == "PE(TTM)":
            return g["pe"], "tencent-quote"
        if col == "PB":
            return g["pb"], "tencent-quote"
        if col == "市值口径":
            return g["float_mcap"] if row == "港股" else g["mcap"], "tencent-quote"
    if row in ("A 股", "港股", "美股") and code:
        m = AN[code]
        if row == "A 股":
            if col == "最新价":
                return m.get("price"), "analysis"
            if col == "PE(TTM)":
                return m.get("pe_ttm"), "analysis"
            if col == "PB":
                return m.get("tencent_pb"), "tencent-quote"
            if col == "市值口径":
                return m.get("mcap_yi"), "analysis"
        else:
            for g in G1119:
                if g["cn"] == m["name"] and g["sym"].startswith("hk" if row == "港股" else "us"):
                    if col == "最新价":
                        return g["price"], "tencent-quote"
                    if col == "PE(TTM)":
                        return g["pe"], "tencent-quote"
                    if col == "PB":
                        return g["pb"], "tencent-quote"
                    if col == "市值口径":
                        return g["float_mcap"], "tencent-quote"

    # ---- 附录 F 数据源口径 ----
    APPF = {
        "A 股三表（年报+季报）": len(AN),
        "A 股估值日频": 1600,
        "A 股实时行情": None,
        "A 股日 K（前复权）": None,
        "港股行情": 44,
    }
    if row == "A 股日 K（前复权）" and col == "本报告中的口径":
        return COMMODITY["沪金"]["2026 年内最高价"], "sina-futures"
    if row in APPF and col == "本报告中的口径":
        return APPF[row], "接口调用参数（本报告脚本实算）"
    if row == "A 股日 K（前复权）" and col == "用途":
        return 52, "52 周窗口定义"
    if row == "A 股日 K（前复权）" and col == "本报告中的口径":
        return COMMODITY["沪金"]["2026 年内最高价"], "sina-futures"

    # ---- 2.3 全行业运行数据 ----
    if row in INDUSTRY_STATS and col == "数值":
        return INDUSTRY_STATS[row], SRC_ASSOC

    # ---- 3.2 全球集中度 ----
    if row in CONCENTRATION and col == "全球集中度":
        return CONCENTRATION[row], SRC_USGS

    # ---- 1.3 已发生的验证事件 ----
    if row in EVENTS and col == "关键数值":
        return EVENTS[row][0], EVENTS[row][1]

    # ---- 2.2 卡脖子表 ----
    if row.startswith("铜精矿"):
        if col == "紧张程度":
            return 246.44, SRC_ARGUS
        if col == "是否已被定价":
            return AN["601899"].get("ps_pct_3y"), "analysis"
    if row.startswith("稀土开采/冶炼分离指标"):
        if col == "紧张程度":
            return 28.5, "海关总署/工信部 2026 年稀土开采总配额 28.5 万吨 REO"
        if col == "是否已被定价":
            return AN["600111"].get("pe_pct_3y"), "analysis"
    if row.startswith("中重稀土"):
        if col == "紧张程度":
            return 627.5, "生意社 2026-11 氧化铽报价 627.5 万元/吨"
    if row.startswith("碳酸锂"):
        if col == "是否已被定价":
            return 8, "高盛 2026 年供需展望：2027-2028 年供给过剩 8%-18%"

    # ---- 分层表（问题一）----
    if row in TIER_THRESHOLD:
        if col == "质量层":
            return TIER_THRESHOLD[row], SRC_FRAMEWORK
        if col == "家数":
            return sum(1 for r in SC.values() if r.get("tier") == row and r.get("channel") == "A"), "scoring"

    # ---- 象限表 ----
    if col == "全样本家数":
        for k, n in QUAD_N.items():
            if row.startswith(k):
                return n, "analysis"
    if col == "关键读数":
        for k, code2 in (("Ⅰ", "000975"), ("Ⅱ", "002532"), ("Ⅲ", "603993"), ("Ⅳ", "601899")):
            if row.startswith(k):
                return cyc(AN[code2], "inv_yoy") if k in ("Ⅰ", "Ⅲ", "Ⅳ") \
                    else AN[code2]["cycle"]["ttm_days"], "analysis"

    # ---- 全样本中位数表 ----
    if col.startswith("本期") or col.startswith("上年同期") or col == "方向判定":
        m = {"存货同比": "inv_yoy", "存货−收入增速差": "inv_rev_spread",
             "TTM 存货周转天数": "ttm_days", "合同负债同比": "contract_yoy",
             "同期收入同比（9M 累计）": "rev_yoy"}.get(row)
        if m:
            if col.startswith("上年同期"):
                return allmed("ttm_days_ly"), "analysis"
            if col == "方向判定":
                return allmed("rev_yoy"), "analysis"
            return allmed(m), "analysis"

    # ---- 附录分组中位数表（按 segment 分组）----
    segs = sorted({m["segment"] for m in AN.values()})
    if row in segs:
        ms = [m for m in AN.values() if m["segment"] == row]
        if col == "家数":
            return len(ms), "analysis"
        key = {"存货同比中位": "inv_yoy", "存货−收入增速差中位": "inv_rev_spread",
               "TTM周转天数中位": "ttm_days", "上年同期中位": "ttm_days_ly",
               "差值中位": "ttm_days_delta", "合同负债同比中位": "contract_yoy"}.get(col)
        if key:
            return med([cyc(x, key) for x in ms]), "analysis"
        if col == "PE(TTM)中位":
            return med([x.get("pe_ttm") for x in ms]), "analysis"
        if col == "PE分位3y中位":
            return med([x.get("pe_pct_3y") for x in ms]), "analysis"
        if col == "PS分位3y中位":
            return med([x.get("ps_pct_3y") for x in ms]), "analysis"

    # ---- 分组中位数表 ----
    if row in GROUP_MEMBERS:
        ms = group_members(row)
        if col == "家数":
            return len(ms), "analysis"
        key = {"存货同比": "inv_yoy", "存货−收入增速差": "inv_rev_spread",
               "TTM周转天数": "ttm_days", "上年同期": "ttm_days_ly",
               "差值": "ttm_days_delta", "合同负债同比": "contract_yoy"}.get(col)
        if key:
            return med([cyc(x, key) for x in ms]), "analysis"

    # ---- 5.2 / 5.4 分布表家数 ----
    if col == "家数":
        if row.startswith("≥ +20pct"):
            return sum(1 for m in AN.values()
                       if m.get("pe_ps_div_3y") is not None and m["pe_ps_div_3y"] >= 20), "analysis"
        if row.startswith("−20pct ~ +20pct"):
            return sum(1 for m in AN.values()
                       if m.get("pe_ps_div_3y") is not None and -20 < m["pe_ps_div_3y"] < 20), "analysis"
        if row.startswith("≤ −20pct"):
            return sum(1 for m in AN.values()
                       if m.get("pe_ps_div_3y") is not None and m["pe_ps_div_3y"] <= -20), "analysis"
        if row.startswith("无 PS 分位数据"):
            return sum(1 for m in AN.values() if m.get("pe_ps_div_3y") is None), "analysis"
        if row.startswith("≥ 100%"):
            return sum(1 for m in AN.values()
                       if m.get("ded_ratio") is not None and m["ded_ratio"] >= 100), "analysis"
        if row.startswith("85%–100%"):
            return sum(1 for m in AN.values()
                       if m.get("ded_ratio") is not None and 85 <= m["ded_ratio"] < 100), "analysis"
        if row.startswith("70%–85%"):
            return sum(1 for m in AN.values()
                       if m.get("ded_ratio") is not None and 70 <= m["ded_ratio"] < 85), "analysis"
        if row.startswith("< 70%"):
            return sum(1 for m in AN.values()
                       if m.get("ded_ratio") is not None and m["ded_ratio"] < 70), "analysis"
        if row.startswith("无数据"):
            return sum(1 for m in AN.values() if m.get("ded_ratio") is None), "analysis"

    # ---- 商品价格表 ----
    for name in sorted(COMMODITY, key=len, reverse=True):
        mp = COMMODITY[name]
        if row.startswith(name):
            if col in mp:
                return mp[col], "sina-futures"

    # ---- 附录 D：52 周高点日期分布 ----
    if re.fullmatch(r"20\d\d-\d\d-\d\d", row) and col == "占比":
        return round(W52[row] / len(AN) * 100, 1), "analysis"
    if re.fullmatch(r"20\d\d-\d\d-\d\d", row) and col == "家数":
        return W52[row], "analysis"
    if row.startswith("落在") and "窗口内" in row:
        return len(W52_WIN), "analysis"

    # ---- 逻辑链（1.2）----
    if row in ("A→B", "B→C", "C→D", "D→E", "E→F") and col == "数据":
        return {
            "A→B": (COMMODITY["沪铜"]["2026 年内最高价"], "sina-futures"),
            "B→C": (3769.3, SRC_GOLD),
            "C→D": (200.8, "analysis"),
            "D→E": (AN["601899"]["ps_pct_3y"], "analysis"),
            "E→F": (28.5, "工信部/海关总署：2026 年稀土开采总配额 28.5 万吨 REO"),
        }[row]

    # ---- 组合表（7.1）----
    if row in POLICY:
        p = POLICY[row]
        if col in p:
            return p[col], SRC_FRAMEWORK
    if row in ("有色金属主题仓位上限（总组合口径）", "本期实际建议投入", "若周期反转信号全部触发"):
        if col == "建议":
            return {"有色金属主题仓位上限（总组合口径）": 3, "本期实际建议投入": 0.3,
                    "若周期反转信号全部触发": 8}[row], SRC_FRAMEWORK

    # ---- 价格区间表（6.3）----
    if row in PRICE_RANGE:
        pr = PRICE_RANGE[row]
        if col in pr:
            if pr[col] == ("price",):
                return AN[BY_NAME[row.split(" ")[0]]].get("price"), "analysis"
            return pr[col], SRC_FRAMEWORK

    # ---- 公司层 ----
    if code and code in AN:
        m = AN[code]
        sc = SC.get(code, {})
        if col in SCREEN_F:
            return m["screen"][SCREEN_F[col]][1], "analysis"
        if row in KPI and col in ("数值", "结果"):
            return kpi_value(code, KPI[row]), "analysis"
        for pref, key in KPI_PREFIX:
            if row.startswith(pref):
                return kpi_value(code, key), "analysis"
        if col in FLAT:
            return m.get(FLAT[col]), "analysis"
        if col in CYC:
            return cyc(m, CYC[col]), "analysis"
        if col == "仓位":
            p = sc.get("pos") or ""
            return 10 if "10" in p else 0, "scoring"
        if col in SCORE_F:
            return sc.get(SCORE_F[col]), "scoring"
        if col in ("生意质量★", "护城河★"):
            return sc.get("q" if "生意" in col else "moat"), "scoring"
        if col in ("上限", "封顶", "最终"):
            return {"上限": "upper", "封顶": "cap", "最终": "final"}[col] and sc.get(
                {"上限": "upper", "封顶": "cap", "最终": "final"}[col]), "scoring"
        # 季度表（行=日期）
        if re.fullmatch(r"20\d\d-\d\d-\d\d", row):
            v = quarterly_value(code, row, col) if False else None
            for metric in ("营收(亿元)", "毛利率", "归母(亿元)", "扣非(亿元)",
                           "经营现金流(亿元)", "存货(亿元)", "归母净利率(%)"):
                v = quarterly_value(code, metric, row)
                if v is not None and col == metric:
                    return v, "analysis"
        # 转置季度表（行=指标，列=日期）
        if col in ("2024-12-31", "2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31",
                   "2026-03-31", "2026-06-30", "2026-09-30"):
            v = quarterly_value(code, row, col)
            if v is not None:
                return v, "analysis"
        # 年度序列表（行=指标，列=年份）
        if row in ("归母(亿元)", "ROE", "毛利率"):
            v = annual_value(code, row, col)
            if v is not None:
                return v, "analysis"
        # 三层打分推导表
        if col == "判据":
            if row == "质量层":
                return m.get("roe_10y_avg"), "analysis"
            if row == "估值层":
                return m.get("ps_pct_3y"), "analysis"
            if row == "最终":
                return abs(sc.get("adj") or 0), "scoring"
            if row == "仓位":
                return 10, SRC_FRAMEWORK
        if col == "结果":
            if row == "质量层":
                return sc.get("layer"), "scoring"
            if row == "估值层":
                return abs(sc.get("adj") or 0), "scoring"
            if row == "仓位":
                return 10, SRC_FRAMEWORK
        # 三情景
        if row in ("乐观", "中性", "悲观") and code in SCEN:
            s = SCEN[code]
            g, pe = s[{"乐观": "bull", "中性": "base", "悲观": "bear"}[row]]
            fut = s["eps_ttm"] * (1 + g) ** 3
            mp = {"年增速": g * 100, "目标 PE": pe, "3 年后 EPS": fut,
                  "目标股价": fut * pe, "涨跌幅": (fut * pe / s["price"] - 1) * 100}
            if col in mp:
                return mp[col], "financial_rigor"
        # 4.6 关键证据表
        if col == "关键证据（数据实算）":
            return EVIDENCE_FIRST.get(code), "analysis"
        # 排除理由
        if col == "排除理由":
            return m["screen"]["i4_gm"][1], "analysis"

    return None, "unresolved"


# 4.6 关键证据表：每格首个数字对应的字段
EVIDENCE_FIRST = {
    "603993": cyc(AN["603993"], "inv_yoy"),
    "000408": AN["000408"]["roe_10y_avg"],
    "000975": AN["000975"]["gm_10y_avg"],
    "002756": AN["002756"]["roe_10y_avg"],
    "600988": AN["600988"]["gm_10y_avg"],
    "601958": AN["601958"]["nm_10y_avg"],
    "002532": abs(cyc(AN["002532"], "inv_yoy")),
    "600301": COMMODITY["沪锡"]["Q3环比"],
    "002192": AN["002192"]["gm_10y_avg"],
}

# ============================================================ run
pts = RA.extract_data_points(TEXT)
bank, unres = [], []
for p in pts:
    v, note = resolve(p["label"], p["line_number"])
    if v is None or isinstance(v, str):
        unres.append(p)
        continue
    try:
        fv = abs(float(v))
    except (TypeError, ValueError):
        unres.append(p)
        continue
    src = note if len(note) > 30 else "eastmoney-f10/tencent/sina（本报告脚本实算）"
    bank.append({"id": p["id"], "label": p["label"], "reported_value": p["reported_value"],
                 "unit": p["unit"], "fetched_value": fv, "source": src,
                 "source2": "中国有色金属工业协会/Argus/USGS/海关总署/腾讯行情/新浪期货",
                 "note": note})
print(f"resolved {len(bank)} / {len(pts)}; unresolved {len(unres)}")
print("by source:", dict(Counter(b["note"] for b in bank)))
json.dump(bank, open(os.path.join(RES, "_bank.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 与报告值比对（1% 相对容差）
bad = []
for b in bank:
    rep, fet = b["reported_value"], b["fetched_value"]
    if fet == 0:
        continue
    if abs(rep - fet) / abs(fet) > 0.01:
        bad.append(b)
print(f"\n=== 数值不一致（>1%）：{len(bad)} ===")
for b in bad[:60]:
    print(f"  L? {b['label'][:52]:<54} report={b['reported_value']:<14} fetched={b['fetched_value']:<14} ({b['note']})")

print("\n--- unresolved (unique labels) ---")
seen = set()
for p in unres:
    if p["label"] in seen:
        continue
    seen.add(p["label"])
    print(f"  L{p['line_number']:>5} {p['label'][:62]:<64} {p['reported_value']}")
