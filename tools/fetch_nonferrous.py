#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""有色金属行业研究 — 批量取数与指标计算。

数据源：
  1. 东财 F10 全表   RPT_F10_FINANCE_{GBALANCE,GINCOME,GCASHFLOW}（filter=SECUCODE 带市场后缀）
  2. 腾讯行情        qt.gtimg.cn/q=            （A 股 + 港股）
  3. 腾讯日 K        web.ifzq.gtimg.cn/.../fqkline/get  （前复权，用于 52 周高点日期）

用法：
    python tools/fetch_nonferrous.py fetch   [--only 601899,000630] [--workers 6]
    python tools/fetch_nonferrous.py compute
    python tools/fetch_nonferrous.py table

缓存：data/nonferrous/<code>.json
输出：reports/有色金属/_research/_metrics.json
"""
import io
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "nonferrous")
OUT = os.path.join(ROOT, "reports", "有色金属", "_research")
EMU = "https://datacenter.eastmoney.com/securities/api/data/v1/get?"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"

# ---------------------------------------------------------------- universe
# (代码, 简称, 环节, 是否A+H)
UNIVERSE = [
    # ---- 铜链 ----
    ("601899", "紫金矿业", "铜金锌综合", "H"),
    ("603993", "洛阳钼业", "铜钼钴", "H"),
    ("600362", "江西铜业", "铜", ""),
    ("000630", "铜陵有色", "铜冶炼", ""),
    ("000878", "云南铜业", "铜", ""),
    ("601168", "西部矿业", "铜铅锌", ""),
    ("002203", "海亮股份", "铜加工", ""),
    ("603527", "众源新材", "铜加工", ""),
    ("600497", "驰宏锌锗", "铅锌锗", ""),
    ("000060", "中金岭南", "铅锌铜", ""),
    # ---- 铝链 ----
    ("601600", "中国铝业", "电解铝", "H"),
    ("000807", "云铝股份", "电解铝", ""),
    ("000933", "神火股份", "电解铝", ""),
    ("002532", "天山铝业", "电解铝一体化", ""),
    ("600219", "南山铝业", "铝加工", ""),
    ("603876", "鼎胜新材", "铝箔", ""),
    ("002578", "豪美新材", "铝型材", ""),
    ("601388", "怡球资源", "再生铝", ""),
    # ---- 黄金 / 白银 ----
    ("600547", "山东黄金", "黄金", ""),
    ("600489", "中金黄金", "黄金", ""),
    ("600988", "赤峰黄金", "黄金", ""),
    ("002155", "湖南黄金", "黄金锑钨", ""),
    ("601069", "西部黄金", "黄金", ""),
    ("000975", "山金国际", "黄金", ""),
    ("002237", "恒邦股份", "黄金冶炼", ""),
    ("000426", "兴业银锡", "银锡锌", ""),
    ("601212", "白银有色", "银铅锌铜", ""),
    ("002716", "金贵银业", "银", ""),
    ("000603", "盛达资源", "银铅", ""),
    # ---- 珠宝零售 ----
    ("002867", "周大生", "珠宝零售", ""),
    ("002345", "潮宏基", "珠宝零售", ""),
    ("605599", "菜百股份", "珠宝零售", ""),
    ("600655", "豫园股份", "珠宝零售", ""),
    # ---- 稀土 + 永磁 ----
    ("600111", "北方稀土", "稀土", ""),
    ("000831", "中国稀土", "稀土", "H"),
    ("600392", "盛和资源", "稀土", ""),
    ("600259", "广晟有色", "稀土", ""),
    ("000795", "英洛华", "稀土磁材", ""),
    ("300748", "金力永磁", "永磁", "H"),
    ("300224", "正海磁材", "永磁", ""),
    ("000970", "中科三环", "永磁", ""),
    ("600366", "宁波韵升", "永磁", ""),
    ("688077", "大地熊", "永磁", ""),
    # ---- 钨 / 钼 / 钛 / 钒 ----
    ("600549", "厦门钨业", "钨稀土磁材", ""),
    ("000657", "中钨高新", "钨", ""),
    ("002378", "章源钨业", "钨", ""),
    ("601958", "金钼股份", "钼", ""),
    ("600456", "宝钛股份", "钛材", ""),
    ("002149", "西部材料", "钛材", ""),
    ("000629", "钒钛股份", "钒钛", ""),
    # ---- 锂 ----
    ("002460", "赣锋锂业", "锂", "H"),
    ("002466", "天齐锂业", "锂", "H"),
    ("000408", "藏格矿业", "锂钾", ""),
    ("002738", "中矿资源", "锂铯钽", ""),
    ("002756", "永兴材料", "锂", ""),
    ("002497", "雅化集团", "锂", ""),
    ("002240", "盛新锂能", "锂", ""),
    ("002192", "融捷股份", "锂", ""),
    ("000792", "盐湖股份", "锂钾", ""),
    ("000762", "西藏矿业", "锂铬", ""),
    # ---- 钴 / 镍 ----
    ("603799", "华友钴业", "钴镍锂", "H"),
    ("002340", "格林美", "再生钴镍", ""),
    ("300919", "中伟股份", "前驱体", ""),
    ("600711", "盛屯矿业", "镍钴铜", ""),
    # ---- 锡 / 锗 / 稀散 ----
    ("000960", "锡业股份", "锡", ""),
    ("600301", "华锡有色", "锡锑", ""),
    ("002428", "云南锗业", "锗", ""),
    ("002171", "楚江新材", "铜基稀散加工", ""),
]

# ⚠️ 港股代码必须校验名称：02618 是京东物流（不是中国铝业），01211 是比亚迪（不是华友钴业）
HK_CODE = {"601899": "02899", "603993": "03993", "601600": "02600",
           "000831": "00851", "300748": "06680", "002460": "01772",
           "002466": "09696"}   # 华友钴业无 H 股上市


# ---------------------------------------------------------------- http
def curl(url, binary=False, timeout=40):
    r = subprocess.run(["curl", "-s", "--noproxy", "*", "-H", "User-Agent: " + UA, url],
                       capture_output=True, timeout=timeout)
    return r.stdout if binary else r.stdout.decode("utf-8", errors="ignore")


def emu(report, secucode, page_size=140):
    url = (EMU + f"reportName={report}&columns=ALL"
           f"&filter=(SECUCODE%3D%22{secucode}%22)&pageSize={page_size}"
           f"&sortColumns=REPORT_DATE&sortTypes=-1&source=HSF10&client=PC")
    for attempt in range(3):
        try:
            d = json.loads(curl(url))
            if d.get("result") and d["result"].get("data"):
                return d["result"]["data"]
        except Exception:
            pass
        time.sleep(1.2)
    return []


def tq_quote(sym):
    """腾讯行情。返回字段字典。

    ⚠️ 字段口径（A股）：
      f[3]=现价  f[38]=换手率  f[39]=PE(动,年化)  f[44]=流通市值(亿)  f[45]=总市值(亿)
      f[46]=PB  f[47]=涨停价  f[48]=跌停价   ← 不是 52 周高低！
    ⚠️ 港股：f[3]=现价(HKD)  f[39]=PE  f[43]=PB  f[44]=H股市值(亿HKD)
    """
    rawb = curl(f"https://qt.gtimg.cn/q={sym}", binary=True)
    try:
        raw = rawb.decode("gbk", errors="ignore")
    except Exception:
        raw = rawb.decode("utf-8", errors="ignore")
    if '"' not in raw:
        return {}
    f = raw[raw.find('"') + 1:raw.rfind('"')].split("~")
    if len(f) < 50:
        return {}
    return {"fields": f, "n": len(f)}


def tq_kline(sym, days=400):
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,{days},qfq")
    try:
        d = json.loads(curl(url))
        node = d["data"][sym]
        arr = node.get("qfqday") or node.get("day")
        return [[a[0], float(a[1]), float(a[2]), float(a[3]), float(a[4])] for a in arr]
    except Exception:
        return []


def num(v):
    try:
        if v is None or v == "" or v == "-":
            return None
        return float(v)
    except Exception:
        return None


# ---------------------------------------------------------------- fetch
def fetch_one(code):
    path = os.path.join(CACHE, code + ".json")
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    mkt = "SH" if code[0] in "6" else ("BJ" if code[0] in "48" else "SZ")
    secucode = f"{code}.{mkt}"
    out = {"code": code, "secucode": secucode}

    out["balance"] = emu("RPT_F10_FINANCE_GBALANCE", secucode)
    out["income"] = emu("RPT_F10_FINANCE_GINCOME", secucode)
    out["cashflow"] = emu("RPT_F10_FINANCE_GCASHFLOW", secucode)

    sym = ("sh" if mkt == "SH" else "sz") + code
    q = tq_quote(sym)
    if q:
        f = q["fields"]
        out["quote"] = {
            "name": f[1], "price": num(f[3]), "prev_close": num(f[4]),
            "pe_dyn": num(f[39]), "float_cap_yi": num(f[44]),
            "total_cap_yi": num(f[45]), "pb": num(f[46]),
            "high_52w": num(f[47]), "low_52w": num(f[48]),
            "time": f[30] if len(f) > 30 else "",
        }
    out["kline"] = tq_kline(sym, 400)

    if code in HK_CODE:
        hq = tq_quote("hk" + HK_CODE[code])
        if hq:
            f = hq["fields"]
            hp = num(f[3])
            hcap = num(f[44])          # H 股市值（亿 HKD）
            out["hk"] = {
                "code": HK_CODE[code], "price": hp, "mcap_yi": hcap,
                "h_shares_yi": (hcap / hp) if (hcap and hp) else None,
                "pe": num(f[39]), "pb": num(f[43]),
                "time": f[30] if len(f) > 30 else "",
            }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False)
    return out


def cmd_fetch(args):
    os.makedirs(CACHE, exist_ok=True)
    codes = [u[0] for u in UNIVERSE]
    if args.only:
        want = set(args.only.split(","))
        codes = [c for c in codes if c in want]
    todo = [c for c in codes if not os.path.exists(os.path.join(CACHE, c + ".json"))]
    print(f"待抓取 {len(todo)} / {len(codes)}")
    done = [0]

    def run(c):
        try:
            fetch_one(c)
        except Exception as e:
            print("  ERR", c, e)
        done[0] += 1
        if done[0] % 10 == 0:
            print(f"  {done[0]}/{len(todo)}")

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(run, todo))
    print("抓取完成")


# ---------------------------------------------------------------- compute
def periods(rows):
    """去重并按报告期排序，返回 {date: row}，保留最新披露版本。"""
    out = {}
    for r in rows:
        d = (r.get("REPORT_DATE") or "")[:10]
        if not d:
            continue
        prev = out.get(d)
        if prev is None or (r.get("NOTICE_DATE") or "") > (prev.get("NOTICE_DATE") or ""):
            out[d] = r
    return out


def annual(rows):
    """年报记录 {year: row}。"""
    out = {}
    for d, r in periods(rows).items():
        if d.endswith("-12-31"):
            out[int(d[:4])] = r
    return out


def quarterly(rows):
    """季度累计记录 {date: row}。"""
    return {d: r for d, r in periods(rows).items()
            if d[5:7] in ("03", "06", "09", "12")}


def yoy(a, b):
    if a is None or b is None or b == 0:
        return None
    return (a / b - 1.0) * 100.0


def pct(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b * 100.0


def compute(raw):
    code = raw["code"]
    bal, inc, cf = raw.get("balance", []), raw.get("income", []), raw.get("cashflow", [])
    A, I, C = annual(bal), annual(inc), annual(cf)
    QB, QI, QC = quarterly(bal), quarterly(inc), quarterly(cf)
    r = {"code": code, "name": None}

    # ---------- 名称（以东财财报口径为准，腾讯 GBK 可能损坏） ----------
    if raw.get("balance"):
        r["name"] = raw["balance"][0].get("SECURITY_NAME_ABBR")
    if raw.get("quote"):
        r["quote"] = raw["quote"]
        if not r["name"]:
            r["name"] = raw["quote"].get("name")

    years = sorted(set(A) & set(I))

    # ---------- 利润表/资产负债/现金流 年度序列 ----------
    ann = []
    for y in years:
        b, i = A[y], I[y]
        c = C.get(y, {})
        rev = num(i.get("TOTAL_OPERATE_INCOME"))
        cost = num(i.get("OPERATE_COST"))
        np_ = num(i.get("PARENT_NETPROFIT"))
        ded = num(i.get("DEDUCT_PARENT_NETPROFIT"))
        eq = num(b.get("TOTAL_PARENT_EQUITY"))
        ocf = num(c.get("NETCASH_OPERATE"))
        capex = num(c.get("CONSTRUCT_LONG_ASSET"))
        fin_exp = num(i.get("FE_INTEREST_EXPENSE"))
        tp = num(i.get("TOTAL_PROFIT"))
        acc_inv = num(c.get("ACCEPT_INVEST_CASH"))
        ann.append({
            "year": y, "rev": rev, "cost": cost, "np": np_, "ded": ded,
            "eq": eq, "ocf": ocf, "capex": capex, "interest": fin_exp,
            "total_profit": tp, "acc_inv": acc_inv,
            "gm": pct((rev - cost) if (rev is not None and cost is not None) else None, rev),
            "nm": pct(np_, rev),
            "ocf_ni": (ocf / np_ * 100.0) if (ocf is not None and np_ not in (None, 0)) else None,
            "fcf": (ocf - capex) if (ocf is not None and capex is not None) else None,
            "capex_rev": pct(capex, rev),
        })
    r["annual"] = ann

    # ---------- ROE（归母净利 / 期初期末平均归母权益） ----------
    roes = []
    for k, a in enumerate(ann):
        prev_eq = ann[k - 1]["eq"] if k > 0 else None
        if a["eq"] and a["np"] is not None:
            if prev_eq:
                roe = a["np"] / ((prev_eq + a["eq"]) / 2) * 100.0
            else:
                roe = a["np"] / a["eq"] * 100.0
            roes.append((a["year"], roe))
    r["roe_series"] = roes
    last10 = [v for _, v in roes[-10:]]
    r["roe_10y_avg"] = sum(last10) / len(last10) if last10 else None
    last5 = [v for _, v in roes[-5:]]
    r["roe_5y_avg"] = sum(last5) / len(last5) if last5 else None

    # ---------- 5 年累计 FCF ----------
    f5 = [a["fcf"] for a in ann[-5:] if a["fcf"] is not None]
    r["fcf_5y"] = sum(f5) if len(f5) == 5 else None

    # ---------- 利息覆盖倍数 (EBIT/利息) ----------
    covs = []
    for a in ann:
        it = a["interest"]
        tp = a["total_profit"]
        if it and it > 0 and tp is not None:
            covs.append((a["year"], (tp + it) / it))
    r["icov_series"] = covs
    if covs:
        r["icov_last"] = covs[-1][1]
        r["icov_5y_min"] = min(v for _, v in covs[-5:])
    else:
        r["icov_last"] = None
        r["icov_5y_min"] = None

    # ---------- 长期毛利率 / 净利率 ----------
    gms = [(a["year"], a["gm"]) for a in ann if a["gm"] is not None]
    nms = [(a["year"], a["nm"]) for a in ann if a["nm"] is not None]
    r["gm_series"] = gms
    r["nm_series"] = nms
    def avg(seq, k):
        vals = [v for _, v in seq[-k:]]
        return sum(vals) / len(vals) if vals else None
    r["gm_5y_avg"] = avg(gms, 5)
    r["gm_10y_avg"] = avg(gms, 10)
    r["nm_10y_avg"] = avg(nms, 10)
    r["nm_5y_avg"] = avg(nms, 5)

    # ---------- 5 年平均 OCF/NI ----------
    ocfnis = [(a["year"], a["ocf_ni"]) for a in ann[-5:] if a["ocf_ni"] is not None]
    r["ocf_ni_5y_avg"] = sum(v for _, v in ocfnis) / len(ocfnis) if ocfnis else None

    # ---------- 经济稀释（观察项） ----------
    acc5 = [a["acc_inv"] for a in ann[-5:] if a["acc_inv"]]
    eq_last = ann[-1]["eq"] if ann else None
    r["economic_dilution"] = (sum(acc5) / eq_last * 100.0) if (acc5 and eq_last) else None

    # ---------- 资本开支/收入 5 年均值 ----------
    cxr = [a["capex_rev"] for a in ann[-5:] if a["capex_rev"] is not None]
    r["capex_rev_5y_avg"] = sum(cxr) / len(cxr) if cxr else None

    # ---------- 估值：市值 + PE ----------
    # ⚠️ 股本口径：资产负债表 SHARE_CAPITAL 对送转股公司会失真
    #   （紫金 2,659,079,824 vs 实际 265.9 亿股，差 10 倍；洛钼差 5 倍）。
    #   改用「腾讯总市值 ÷ 股价」反推的总股本，与 EPS×股本 勾稽一致。
    q = raw.get("quote", {})
    mcap_a = q.get("total_cap_yi")          # A 股价 × 总股本（含 H 股），腾讯口径
    hk = raw.get("hk")
    price = q.get("price")
    total_shares_yi = None
    if mcap_a and price:
        total_shares_yi = mcap_a * 1e8 / price / 1e8
    r["total_shares_yi"] = total_shares_yi

    h_shares = None
    hk_mcap_cny = None
    FX = 0.915   # HKD/CNY；报告中须注明为 2026-11 近似中间价
    if hk and hk.get("mcap_yi") and hk.get("price"):
        h_shares = hk["h_shares_yi"]
        hk_mcap_cny = hk["mcap_yi"] * FX
    r["hk"] = hk
    r["hk_fx_assumed"] = FX if hk else None
    r["hk_mcap_cny_yi"] = hk_mcap_cny
    r["h_shares_yi"] = h_shares

    mcap_combined = None
    if price and total_shares_yi and h_shares:
        mcap_combined = price * (total_shares_yi - h_shares) + hk_mcap_cny
    elif price and total_shares_yi:
        mcap_combined = price * total_shares_yi
    r["mcap_yi"] = mcap_combined
    r["mcap_a_price_x_allshares_yi"] = mcap_a

    # TTM：最近 4 个季度单季差分
    qd = sorted(QI.keys())
    if len(qd) >= 4:
        last4 = qd[-4:]
        ttm_np = 0.0
        ttm_ded = 0.0
        ttm_rev = 0.0
        ttm_cost = 0.0
        ok = True
        for d in last4:
            cur = QI[d]
            prev_d = (str(int(d[:4]) - 1) + d[4:7] + d[7:10]) if d[5:7] != "03" else None
            if d[5:7] == "03":
                single = num(cur.get("PARENT_NETPROFIT"))
                single_ded = num(cur.get("DEDUCT_PARENT_NETPROFIT"))
                single_rev = num(cur.get("TOTAL_OPERATE_INCOME"))
                single_cost = num(cur.get("OPERATE_COST"))
            else:
                if prev_d not in QI:
                    ok = False
                    break
                pc = QI[prev_d]
                single = num(cur.get("PARENT_NETPROFIT")) - num(pc.get("PARENT_NETPROFIT"))
                single_ded = num(cur.get("DEDUCT_PARENT_NETPROFIT")) - num(pc.get("DEDUCT_PARENT_NETPROFIT"))
                single_rev = num(cur.get("TOTAL_OPERATE_INCOME")) - num(pc.get("TOTAL_OPERATE_INCOME"))
                single_cost = num(cur.get("OPERATE_COST")) - num(pc.get("OPERATE_COST"))
            if None in (single, single_ded, single_rev, single_cost):
                ok = False
                break
            ttm_np += single
            ttm_ded += single_ded
            ttm_rev += single_rev
            ttm_cost += single_cost
        if ok:
            r["ttm_np_yi"] = ttm_np / 1e8
            r["ttm_ded_yi"] = ttm_ded / 1e8
            r["ttm_rev_yi"] = ttm_rev / 1e8
            r["ttm_cost_yi"] = ttm_cost / 1e8
            r["ttm_period"] = f"{last4[0]}~{last4[-1]}"
            if mcap_combined and ttm_np > 0:
                r["pe_ttm"] = mcap_combined / (ttm_np / 1e8)
            if mcap_combined and ttm_ded > 0:
                r["pe_ttm_ded"] = mcap_combined / (ttm_ded / 1e8)
            if mcap_combined and ttm_np > 0:
                r["pe_q_annual"] = mcap_combined / ((ttm_np / 4) / 1e8)
            r["ded_ratio"] = (ttm_ded / ttm_np * 100.0) if ttm_np else None
            r["ttm_gm"] = (1 - ttm_cost / ttm_rev * 100.0) if ttm_rev else None

    # 正常化 PE：近 3 年 / 近 5 年归母均值（剔除亏损年）
    for k in (3, 5):
        vals = [a["np"] for a in ann[-k:] if a["np"] is not None and a["np"] > 0]
        if mcap_combined and len(vals) == k:
            r[f"norm_np_{k}y_yi"] = sum(vals) / 1e8
            r[f"pe_norm_{k}y"] = mcap_combined / (sum(vals) / 1e8)

    # ---------- 周期：库存三指标 + 单季序列 ----------
    cyc = {}
    qdates = sorted(QB.keys())
    if qdates:
        last = qdates[-1]
        ly = (str(int(last[:4]) - 1) + last[4:])
        inv = num(QB[last].get("INVENTORY"))
        inv_ly = num(QB.get(ly, {}).get("INVENTORY"))
        cyc["inv"] = inv
        cyc["inv_ly"] = inv_ly
        cyc["inv_yoy"] = yoy(inv, inv_ly)
        cl = num(QB[last].get("CONTRACT_LIAB"))
        cl_ly = num(QB.get(ly, {}).get("CONTRACT_LIAB"))
        cyc["contract_liab"] = cl
        cyc["contract_liab_ly"] = cl_ly
        cyc["contract_yoy"] = yoy(cl, cl_ly)
        # 累计收入同比（同期口径）
        rev_c = num(QI[last].get("TOTAL_OPERATE_INCOME"))
        rev_ly = num(QI.get(ly, {}).get("TOTAL_OPERATE_INCOME"))
        cyc["rev_yoy"] = yoy(rev_c, rev_ly)
        if cyc["inv_yoy"] is not None and cyc["rev_yoy"] is not None:
            cyc["inv_rev_spread"] = cyc["inv_yoy"] - cyc["rev_yoy"]
        # TTM 周转天数
        def ttm_days(end_date):
            if end_date not in QB:
                return None
            end_inv = num(QB[end_date].get("INVENTORY"))
            # 期初 = 上年末
            py = int(end_date[:4]) - 1
            begin_inv = num(QB.get(f"{py}-12-31", {}).get("INVENTORY"))
            if end_inv is None or begin_inv is None:
                return None
            ds = sorted(d for d in QI if d <= end_date)
            if len(ds) < 4:
                return None
            cost_sum = 0.0
            for d in ds[-4:]:
                cur = QI[d]
                if d[5:7] == "03":
                    single_cost = num(cur.get("OPERATE_COST"))
                else:
                    prev_d = str(int(d[:4]) - 1) + d[4:]
                    if prev_d not in QI:
                        return None
                    single_cost = num(cur.get("OPERATE_COST")) - num(QI[prev_d].get("OPERATE_COST"))
                if single_cost is None:
                    return None
                cost_sum += single_cost
            if cost_sum <= 0:
                return None
            return (begin_inv + end_inv) / 2 / cost_sum * 365.0
        cyc["ttm_days"] = ttm_days(last)
        cyc["ttm_days_ly"] = ttm_days(ly)
        if cyc["ttm_days"] and cyc["ttm_days_ly"]:
            cyc["ttm_days_delta"] = cyc["ttm_days"] - cyc["ttm_days_ly"]
        # 单季存货增量
        if len(qdates) >= 2:
            cyc["inv_qoq"] = num(QB[last].get("INVENTORY")) - num(QB[qdates[-2]].get("INVENTORY"))
            cyc["inv_qoq_date"] = qdates[-2]
        if mcap_combined and inv:
            cyc["inv_to_mcap"] = inv / 1e8 / mcap_combined * 100.0
        if r.get("ttm_rev_yi") and inv:
            cyc["inv_to_ttm_rev"] = inv / 1e8 / r["ttm_rev_yi"] * 100.0
        cyc["date"] = last

    # 单季序列（近 8 季）
    seq = []
    ds = sorted(QI.keys())
    for d in ds[-8:]:
        cur = QI[d]
        if d[5:7] == "03":
            s_rev = num(cur.get("TOTAL_OPERATE_INCOME"))
            s_cost = num(cur.get("OPERATE_COST"))
            s_np = num(cur.get("PARENT_NETPROFIT"))
            prev_d = None
        else:
            prev_d = str(int(d[:4]) - 1) + d[4:]
            if prev_d not in QI:
                continue
            pc = QI[prev_d]
            s_rev = num(cur.get("TOTAL_OPERATE_INCOME")) - num(pc.get("TOTAL_OPERATE_INCOME"))
            s_cost = num(cur.get("OPERATE_COST")) - num(pc.get("OPERATE_COST"))
            s_np = num(cur.get("PARENT_NETPROFIT")) - num(pc.get("PARENT_NETPROFIT"))
        ocf_s = None
        if d in QC:
            ocf_c = num(QC[d].get("NETCASH_OPERATE"))
            if d[5:7] == "03":
                ocf_s = ocf_c
            else:
                prev_d2 = str(int(d[:4]) - 1) + d[4:]
                if prev_d2 in QC:
                    ocf_s = ocf_c - num(QC[prev_d2].get("NETCASH_OPERATE"))
        inv_q = num(QB.get(d, {}).get("INVENTORY"))
        seq.append({
            "date": d, "rev": s_rev, "gm": pct((s_rev - s_cost) if (s_rev is not None and s_cost is not None) else None, s_rev),
            "nm": pct(s_np, s_rev), "ocf": ocf_s, "inv": inv_q,
        })
    r["cycle"] = cyc
    r["quarter_seq"] = seq

    # ---------- 52 周高点日期（前复权收盘 + 最高价） ----------
    kl = raw.get("kline", [])
    if kl:
        win = [k for k in kl if k[0] >= "2025-11-20"]
        if win:
            best = max(win, key=lambda k: k[3])
            r["high_52w_date"] = best[0]
            r["high_52w_price"] = best[3]
            r["drawdown_from_high"] = (num(q.get("price")) / best[3] - 1) * 100.0 if q.get("price") and best[3] else None
            r["ytd_pct"] = None
            if kl:
                base = [k for k in kl if k[0] <= "2025-12-31"]
                if base and q.get("price"):
                    r["ytd_pct"] = (q["price"] / base[-1][2] - 1) * 100.0
            # 52 周高点日期分布用的统一口径（最高价而非收盘）
    return r


def load_all():
    out = []
    for code, name, seg, ah in UNIVERSE:
        p = os.path.join(CACHE, code + ".json")
        if not os.path.exists(p):
            print("MISSING", code)
            continue
        with open(p, encoding="utf-8") as fh:
            raw = json.load(fh)
        try:
            m = compute(raw)
        except Exception as e:
            print("COMPUTE ERR", code, e)
            continue
        m["segment"] = seg
        m["universe_name"] = name
        m["ah"] = ah
        out.append(m)
    return out


def cmd_compute(args):
    os.makedirs(OUT, exist_ok=True)
    data = load_all()
    path = os.path.join(OUT, "_metrics.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print(f"计算 {len(data)} 家 -> {path}")


def f(v, nd=2, pctf=False):
    if v is None:
        return "—"
    try:
        return f"{v:.{nd}f}" + ("%" if pctf else "")
    except Exception:
        return "—"


def cmd_table(args):
    with open(os.path.join(OUT, "_metrics.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    hdr = ("| 代码 | 名称 | 环节 | 市值(亿) | PE(TTM) | PE(扣非) | 正常化PE(3y) | 单季年化PE | "
           "ROE10y均 | 毛利率5y均 | 净利率10y均 | OCF/NI5y | FCF5y(亿) | 利息覆盖 | 经济稀释 | "
           "存货同比 | 存货-收入差 | TTM周转天数 | 上年同期 | 合同负债同比 | 52周高点日 | 回撤% |")
    print(hdr)
    print("|" + "---|" * 22)
    for m in data:
        cyc = m.get("cycle", {})
        print("| {code} | {name} | {seg} | {mc} | {pe} | {ped} | {pn} | {pq} | {roe} | {gm} | {nm} | "
              "{ocf} | {fcf} | {ic} | {dil} | {iy} | {sp} | {td} | {tdl} | {cy} | {hd} | {dd} |".format(
            code=m["code"], name=m.get("name"), seg=m.get("segment"),
            mc=f(m.get("mcap_yi"), 0), pe=f(m.get("pe_ttm")), ped=f(m.get("pe_ttm_ded")),
            pn=f(m.get("pe_norm_3y")), pq=f(m.get("pe_q_annual")),
            roe=f(m.get("roe_10y_avg"), 1, True), gm=f(m.get("gm_5y_avg"), 1, True),
            nm=f(m.get("nm_10y_avg"), 1, True), ocf=f(m.get("ocf_ni_5y_avg"), 1, True),
            fcf=f((m.get("fcf_5y") or 0) / 1e8 if m.get("fcf_5y") else None, 1),
            ic=f(m.get("icov_5y_min")), dil=f(m.get("economic_dilution"), 1, True),
            iy=f(cyc.get("inv_yoy"), 1, True), sp=f(cyc.get("inv_rev_spread"), 1, True),
            td=f(cyc.get("ttm_days"), 1), tdl=f(cyc.get("ttm_days_ly"), 1),
            cy=f(cyc.get("contract_yoy"), 1, True), hd=m.get("high_52w_date"),
            dd=f(m.get("drawdown_from_high"), 1, True)))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    p1 = sub.add_parser("fetch")
    p1.add_argument("--only", default="")
    p1.add_argument("--workers", type=int, default=6)
    p2 = sub.add_parser("compute")
    p2.add_argument("--x", default="")
    sub.add_parser("table")
    args = ap.parse_args()
    if args.cmd == "fetch":
        cmd_fetch(args)
    elif args.cmd == "compute":
        cmd_compute(args)
    elif args.cmd == "table":
        cmd_table(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
