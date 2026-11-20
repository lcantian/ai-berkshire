#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""有色金属行业研究 — 统一计算引擎。

口径说明（全部写进报告附录）：
  1. 归母净利润 = PARENT_NETPROFIT；扣非 = DEDUCT_PARENT_NETPROFIT
  2. 单季值一律由累计数差分实算（累计会掩盖崩塌）
  3. ROE = 归母净利 / 期初期末平均归母权益
  4. FCF = 经营活动现金流净额 - 购建固定资产等长期资产支付的现金
  5. 利息覆盖 = (利润总额 + 利息费用) / 利息费用（利息费用取 FINANCE_EXPENSE 中的
     利息费用 FE_INTEREST_EXPENSE；该字段缺失时用财务费用倒轧并标注）
  6. 净利率分母 = 营业总收入 TOTAL_OPERATE_INCOME
  7. 估值分位用东财 RPT_VALUEANALYSIS_DET 日频序列（PE_TTM/PB_MRQ/PS_TTM/收盘价/总市值）
     并自建季末 TTM PE 序列做双口径交叉验证
  8. A+H 公司市值按两地价格加总（A 价 × A 股 + H 价 × H 股，HKD/CNY 汇率标注）
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_nonferrous import UNIVERSE, HK_CODE  # noqa  (stdout UTF-8 包装在此完成)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "nonferrous")
OUT = os.path.join(ROOT, "reports", "有色金属", "_research")

FX_HKD_CNY = 0.915     # 2026-11-20 附近中间价近似值，报告中标注为估计
PEAK_DATE = "2026-01-29"   # 有色板块集体见顶日（国证有色/中证有色金属双指数确认）


def rd(x):
    return x if isinstance(x, (int, float)) else None


def yoy(a, b):
    if a is None or b is None or b == 0:
        return None
    return 100.0 * (a - b) / abs(b)


def pct(a, b):
    if a is None or b in (None, 0):
        return None
    return 100.0 * a / b


def pct_rank(series, val):
    """经验分布分位：序列中严格小于 val 的占比（负值不入排序）。"""
    s = [x for x in series if x is not None and x > 0]
    if not s or val is None or val <= 0:
        return None
    return round(100.0 * sum(1 for x in s if x < val) / len(s), 1)


def single_q(rows, field):
    """累计 → 单季。返回 {报告期: 单季值}。

    ⚠️ 差分基准必须是「同一会计年度内的上一期」：
        Q2 = H1 − Q1(同年)、Q3 = 9M − H1(同年)、Q4 = FY − 9M(同年)
       若误用「上年同期累计」相减，得到的是同比差额而非单季值，
       会同时污染单季序列、TTM 口径和周转天数（毛利率可算出 >100%）。
    """
    by = {}
    for r in rows:
        d = (r.get("REPORT_DATE") or "")[:10]
        if d:
            by[d] = rd(r.get(field))
    res = {}
    for d, v in by.items():
        if v is None:
            continue
        mm = d[5:7]
        if mm == "03":
            res[d] = v
            continue
        if mm == "06":
            prev = d[:4] + "-03-31"
        elif mm == "09":
            prev = d[:4] + "-06-30"
        else:
            prev = d[:4] + "-09-30"
        p = by.get(prev)
        res[d] = None if p is None else v - p
    return res


def ttm_of(sq):
    ds = sorted([d for d in sq if sq[d] is not None])
    if len(ds) < 4:
        return None, None
    last4 = ds[-4:]
    return sum(sq[d] for d in last4), last4


def load(code):
    p = os.path.join(CACHE, f"{code}.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        raw = json.load(fh)
    vp = os.path.join(CACHE, f"val_{code}.json")
    val = []
    if os.path.exists(vp):
        with open(vp, encoding="utf-8") as fh:
            val = json.load(fh)
    kp = os.path.join(CACHE, f"kl_{code}.json")
    kl = []
    if os.path.exists(kp):
        with open(kp, encoding="utf-8") as fh:
            kl = json.load(fh)
    return raw, val, kl


def build(code, name, seg, ah):
    got = load(code)
    if not got:
        return None
    raw, val, kl = got
    bal, inc, cf = raw.get("balance", []), raw.get("income", []), raw.get("cashflow", [])
    if not inc or not bal:
        return None

    r = {"code": code, "name": name, "segment": seg, "ah": ah}
    r["name_api"] = bal[0].get("SECURITY_NAME_ABBR")
    if raw.get("quote"):
        r["quote"] = raw["quote"]
        r["tencent_price"] = raw["quote"].get("price")
        r["tencent_pb"] = raw["quote"].get("pb")
        r["tencent_total_cap_yi"] = raw["quote"].get("total_cap_yi")

    # ---------- 年度序列 ----------
    ann_by = {}
    for row in inc:
        d = (row.get("REPORT_DATE") or "")[:10]
        if d.endswith("-12-31"):
            ann_by[d] = row
    bal_ann = {}
    for row in bal:
        d = (row.get("REPORT_DATE") or "")[:10]
        if d.endswith("-12-31"):
            bal_ann[d] = row
    cf_ann = {}
    for row in cf:
        d = (row.get("REPORT_DATE") or "")[:10]
        if d.endswith("-12-31"):
            cf_ann[d] = row

    years = sorted(set(ann_by) & set(bal_ann))
    ann = []
    for d in years:
        i, b = ann_by[d], bal_ann[d]
        c = cf_ann.get(d, {})
        rev = rd(i.get("TOTAL_OPERATE_INCOME"))
        cost = rd(i.get("OPERATE_COST"))
        np_ = rd(i.get("PARENT_NETPROFIT"))
        ded = rd(i.get("DEDUCT_PARENT_NETPROFIT"))
        eq = rd(b.get("TOTAL_PARENT_EQUITY"))
        ocf = rd(c.get("NETCASH_OPERATE"))
        capex = rd(c.get("CONSTRUCT_LONG_ASSET"))
        ie = rd(i.get("FE_INTEREST_EXPENSE"))
        tp = rd(i.get("TOTAL_PROFIT"))
        acc = rd(c.get("ACCEPT_INVEST_CASH"))
        ann.append({
            "year": int(d[:4]), "date": d,
            "rev": rev, "cost": cost, "np": np_, "ded": ded, "eq": eq,
            "ocf": ocf, "capex": capex, "interest": ie, "total_profit": tp,
            "acc_inv": acc,
            "gm": pct((rev - cost) if None not in (rev, cost) else None, rev),
            "nm": pct(np_, rev),
            "ocf_ni": pct(ocf, np_) if None not in (ocf, np_) and np_ != 0 else None,
            "fcf": (ocf - capex) if None not in (ocf, capex) else None,
            "capex_rev": pct(capex, rev),
        })
    r["annual"] = ann

    # ---------- ROE ----------
    roe = []
    for k, a in enumerate(ann):
        if a["eq"] is None or a["np"] is None:
            continue
        prev_eq = ann[k - 1]["eq"] if k > 0 else None
        base = (prev_eq + a["eq"]) / 2 if prev_eq else a["eq"]
        if base:
            roe.append((a["year"], 100.0 * a["np"] / base))
    r["roe_series"] = roe
    last10 = [v for _, v in roe[-10:]]
    last5 = [v for _, v in roe[-5:]]
    r["roe_10y_avg"] = round(sum(last10) / len(last10), 2) if last10 else None
    r["roe_5y_avg"] = round(sum(last5) / len(last5), 2) if last5 else None
    r["roe_n"] = len(last10)

    # ---------- 5 年累计 FCF ----------
    f5 = [a["fcf"] for a in ann[-5:] if a["fcf"] is not None]
    r["fcf_5y_yi"] = round(sum(f5) / 1e8, 2) if len(f5) == 5 else None

    # ---------- 利息覆盖 ----------
    cov = []
    for a in ann:
        if a["interest"] and a["interest"] > 0 and a["total_profit"] is not None:
            cov.append((a["year"], (a["total_profit"] + a["interest"]) / a["interest"]))
    r["icov_series"] = cov
    r["icov_5y_min"] = round(min(v for _, v in cov[-5:]), 2) if len(cov) >= 5 else None
    r["icov_last"] = round(cov[-1][1], 2) if cov else None
    r["icov_n"] = len(cov)

    # ---------- 毛利率 / 净利率 ----------
    def avg(seq, k):
        v = [x for _, x in seq[-k:]]
        return round(sum(v) / len(v), 2) if v else None
    gms = [(a["year"], a["gm"]) for a in ann if a["gm"] is not None]
    nms = [(a["year"], a["nm"]) for a in ann if a["nm"] is not None]
    r["gm_10y_avg"] = avg(gms, 10)
    r["gm_5y_avg"] = avg(gms, 5)
    r["nm_10y_avg"] = avg(nms, 10)
    r["nm_5y_avg"] = avg(nms, 5)
    r["gm_series"] = gms
    r["nm_series"] = nms
    r["gm_n"] = len(gms)

    # ---------- OCF/NI ----------
    o5 = [(a["year"], a["ocf_ni"]) for a in ann[-5:] if a["ocf_ni"] is not None]
    r["ocf_ni_5y_avg"] = round(sum(v for _, v in o5) / len(o5), 2) if o5 else None
    r["ocf_ni_n"] = len(o5)

    # ---------- 经济稀释（观察项） ----------
    acc5 = [a["acc_inv"] for a in ann[-5:] if a["acc_inv"] is not None]
    eq_last = ann[-1]["eq"] if ann else None
    r["economic_dilution"] = round(sum(acc5) / eq_last * 100.0, 2) if (acc5 and eq_last) else None

    # ---------- 资本开支强度 ----------
    cx = [a["capex_rev"] for a in ann[-5:] if a["capex_rev"] is not None]
    r["capex_rev_5y_avg"] = round(sum(cx) / len(cx), 2) if cx else None

    # ---------- 季度序列（单季差分） ----------
    rev_sq = single_q(inc, "TOTAL_OPERATE_INCOME")
    np_sq = single_q(inc, "PARENT_NETPROFIT")
    ded_sq = single_q(inc, "DEDUCT_PARENT_NETPROFIT")
    cost_sq = single_q(inc, "OPERATE_COST")
    op_sq = single_q(inc, "OPERATE_PROFIT")
    ocf_sq = single_q(cf, "NETCASH_OPERATE")
    sales_sq = single_q(cf, "SALES_SERVICES")

    bal_q = {}
    for row in bal:
        d = (row.get("REPORT_DATE") or "")[:10]
        if d:
            bal_q[d] = row

    ds_all = sorted([d for d in rev_sq if rev_sq[d] is not None])
    ttm_rev, last4 = ttm_of(rev_sq)
    ttm_np, _ = ttm_of(np_sq)
    ttm_ded, _ = ttm_of(ded_sq)
    ttm_cost, _ = ttm_of(cost_sq)
    ttm_ocf, _ = ttm_of(ocf_sq)
    r["ttm_rev_yi"] = round(ttm_rev / 1e8, 2) if ttm_rev is not None else None
    r["ttm_np_yi"] = round(ttm_np / 1e8, 2) if ttm_np is not None else None
    r["ttm_ded_yi"] = round(ttm_ded / 1e8, 2) if ttm_ded is not None else None
    r["ttm_ocf_yi"] = round(ttm_ocf / 1e8, 2) if ttm_ocf is not None else None
    r["ttm_gm"] = round(pct((ttm_rev - ttm_cost) if None not in (ttm_rev, ttm_cost) else None, ttm_rev), 2) \
        if None not in (ttm_rev, ttm_cost) and ttm_rev else None
    r["ttm_period"] = [last4[0], last4[-1]] if last4 else None
    # TTM 扣非同比（估值层第③条需要）：取上一年同期的 4 个单季
    if len(ds_all) >= 8:
        prev4 = ds_all[-8:-4]
        pd_ = [ded_sq.get(x) for x in prev4]
        if all(v is not None for v in pd_) and ttm_ded is not None:
            prev_sum = sum(pd_)
            r["ttm_ded_yoy"] = round((ttm_ded / prev_sum - 1) * 100.0, 2) if prev_sum > 0 else None
            r["ttm_np_yoy"] = None
            prevn = [np_sq.get(x) for x in prev4]
            if all(v is not None for v in prevn) and ttm_np is not None and sum(prevn) > 0:
                r["ttm_np_yoy"] = round((ttm_np / sum(prevn) - 1) * 100.0, 2)

    # 单季明细（近 8 季）
    seq = []
    for d in ds_all[-8:]:
        rv, cs, n_, dn_ = rev_sq.get(d), cost_sq.get(d), np_sq.get(d), ded_sq.get(d)
        seq.append({
            "q": d,
            "rev_yi": round(rv / 1e8, 2) if rv is not None else None,
            "gm": round(pct((rv - cs) if None not in (rv, cs) else None, rv), 2) if rv else None,
            "npm": round(pct(n_, rv), 2) if (n_ is not None and rv) else None,
            "np_yi": round(n_ / 1e8, 2) if n_ is not None else None,
            "dnp_yi": round(dn_ / 1e8, 2) if dn_ is not None else None,
            "ocf_yi": round(ocf_sq[d] / 1e8, 2) if ocf_sq.get(d) is not None else None,
            "inv_yi": round(rd(bal_q.get(d, {}).get("INVENTORY")) / 1e8, 2)
                       if bal_q.get(d, {}).get("INVENTORY") is not None else None,
        })
    r["quarterly"] = seq

    # ---------- 周期三指标 ----------
    cyc = {}
    qd = sorted([d for d in bal_q if d.endswith(("-03-31", "-06-30", "-09-30", "-12-31"))])
    last = qd[-1] if qd else None
    if last:
        ly = f"{int(last[:4]) - 1}{last[4:]}"
        inv = rd(bal_q[last].get("INVENTORY"))
        inv_ly = rd(bal_q.get(ly, {}).get("INVENTORY"))
        cyc["date"] = last
        cyc["inv_yi"] = round(inv / 1e8, 2) if inv is not None else None
        cyc["inv_yoy"] = round(yoy(inv, inv_ly), 2) if None not in (inv, inv_ly) else None
        cl = rd(bal_q[last].get("CONTRACT_LIAB"))
        cl_ly = rd(bal_q.get(ly, {}).get("CONTRACT_LIAB"))
        cyc["contract_liab_yi"] = round(cl / 1e8, 2) if cl is not None else None
        cyc["contract_yoy"] = round(yoy(cl, cl_ly), 2) if None not in (cl, cl_ly) else None
        # 同期收入同比（累计口径，同报告期）
        rc, rl = rd(ann_by and inc[0] and None), None
        cum = {}
        for row in inc:
            d = (row.get("REPORT_DATE") or "")[:10]
            cum[d] = rd(row.get("TOTAL_OPERATE_INCOME"))
        rc, rl = cum.get(last), cum.get(ly)
        cyc["rev_yoy"] = round(yoy(rc, rl), 2) if None not in (rc, rl) else None
        if cyc["inv_yoy"] is not None and cyc["rev_yoy"] is not None:
            cyc["inv_rev_spread"] = round(cyc["inv_yoy"] - cyc["rev_yoy"], 2)
        # TTM 周转天数：期初 = 上年末
        def days_at(end):
            if end not in bal_q:
                return None
            e = rd(bal_q[end].get("INVENTORY"))
            b = rd(bal_q.get(f"{int(end[:4]) - 1}-12-31", {}).get("INVENTORY"))
            ds = [d for d in ds_all if d <= end]
            if len(ds) < 4 or e is None or b is None:
                return None
            c = sum(cost_sq[d] for d in ds[-4:] if cost_sq.get(d) is not None)
            if not c or c <= 0:
                return None
            return (b + e) / 2 / c * 365
        cyc["ttm_days"] = round(days_at(last), 1) if days_at(last) else None
        dly = days_at(ly)
        cyc["ttm_days_ly"] = round(dly, 1) if dly else None
        if cyc["ttm_days"] is not None and cyc["ttm_days_ly"] is not None:
            cyc["ttm_days_delta"] = round(cyc["ttm_days"] - cyc["ttm_days_ly"], 1)
        prev_q = qd[-2] if len(qd) >= 2 else None
        if prev_q:
            pi = rd(bal_q[prev_q].get("INVENTORY"))
            cyc["inv_qoq_yi"] = round((inv - pi) / 1e8, 2) if None not in (inv, pi) else None
            cyc["inv_qoq_date"] = prev_q
        cyc["inv_to_mcap"] = round(inv / 1e8 / r["mcap_yi"] * 100.0, 2) if inv is not None and r.get("mcap_yi") else None
        cyc["inv_to_ttm_rev"] = round(inv / 1e8 / r["ttm_rev_yi"] * 100.0, 2) \
            if inv is not None and r.get("ttm_rev_yi") else None
    r["cycle"] = cyc

    # ---------- 市值（先算，用于存货/市值） ----------
    val_sorted = sorted(val, key=lambda x: x.get("TRADE_DATE", ""), reverse=True)
    r["price_date"] = val_sorted[0].get("TRADE_DATE", "")[:10] if val_sorted else None
    r["price"] = val_sorted[0].get("CLOSE_PRICE") if val_sorted else None
    r["total_shares"] = val_sorted[0].get("TOTAL_SHARES") if val_sorted else None
    em_mcap_yi = round(val_sorted[0]["TOTAL_MARKET_CAP"] / 1e8, 2) if val_sorted and val_sorted[0].get("TOTAL_MARKET_CAP") else None
    r["mcap_em_yi"] = em_mcap_yi
    hk = raw.get("hk")
    h_shares = hk.get("h_shares_yi") if hk else None
    hk_cny = hk["mcap_yi"] * FX_HKD_CNY if (hk and hk.get("mcap_yi")) else None
    r["hk"] = hk
    r["h_shares_yi"] = h_shares
    if r["price"] and r["total_shares"]:
        total_yi = r["total_shares"] / 1e8
        r["total_shares_yi"] = round(total_yi, 4)
        if h_shares and h_shares < total_yi * 0.98:
            r["mcap_yi"] = round(r["price"] * (total_yi - h_shares) + hk_cny, 2)
            r["mcap_note"] = f"A+H 合并（A 股 {round(total_yi - h_shares, 2)} 亿 + H 股 {round(h_shares, 2)} 亿 × {FX_HKD_CNY}）"
        elif h_shares:
            r["mcap_yi"] = round(r["price"] * total_yi, 2)
            r["mcap_note"] = "A price x all shares (HK market-cap field broken; A+H not obtained)"
        else:
            r["mcap_yi"] = round(r["price"] * total_yi, 2)
            r["mcap_note"] = "A 股价 × 总股本"
    else:
        r["mcap_yi"] = em_mcap_yi
        r["mcap_note"] = "东财 TOTAL_MARKET_CAP"

    # ---------- 四锚点估值 ----------
    mc = r.get("mcap_yi")
    if mc and r.get("ttm_np_yi") and r["ttm_np_yi"] > 0:
        r["pe_ttm"] = round(mc / r["ttm_np_yi"], 2)
    if mc and r.get("ttm_ded_yi") and r["ttm_ded_yi"] > 0:
        r["pe_ttm_ded"] = round(mc / r["ttm_ded_yi"], 2)
    if mc and r.get("ttm_np_yi") and r["ttm_np_yi"] > 0:
        q3 = seq[-1]["np_yi"] if seq else None
        if q3 and q3 > 0:
            r["pe_q_ann"] = round(mc / (q3 * 4), 2)
            r["pe_q_ann_quarter"] = seq[-1]["q"]
    if mc and r.get("ttm_ded_yi") and r["ttm_ded_yi"] > 0:
        r["ded_ratio"] = round(r["ttm_ded_yi"] / r["ttm_np_yi"] * 100.0, 2) if r.get("ttm_np_yi") else None
    for k in (3, 5):
        vals = [a["np"] for a in ann[-k:] if a["np"] is not None and a["np"] > 0]
        if mc and len(vals) == k:
            # 均值利润 = sum / k；PE = 市值 ÷ 均值利润（单位统一为亿元）
            r[f"norm_np_{k}y_yi"] = round(sum(vals) / k / 1e8, 2)
            r[f"pe_norm_{k}y"] = round(mc / (sum(vals) / k / 1e8), 2)

    # ---------- 估值分位（双口径） ----------
    # 口径 A：东财日频 PE_TTM / PB / PS 序列
    pe_daily = [rd(x.get("PE_TTM")) for x in val_sorted]
    pb_daily = [rd(x.get("PB_MRQ")) for x in val_sorted]
    ps_daily = [rd(x.get("PS_TTM")) for x in val_sorted]
    cur_pe = val_sorted[0].get("PE_TTM") if val_sorted else None
    cur_pb = val_sorted[0].get("PB_MRQ") if val_sorted else None
    cur_ps = val_sorted[0].get("PS_TTM") if val_sorted else None
    n3y = 750
    r["pe_pct_3y"] = pct_rank(pe_daily[:n3y], cur_pe)
    r["pe_pct_all"] = pct_rank(pe_daily, cur_pe)
    r["pb_pct_3y"] = pct_rank(pb_daily[:n3y], cur_pb)
    r["pb_pct_all"] = pct_rank(pb_daily, cur_pb)
    r["ps_pct_3y"] = pct_rank(ps_daily[:n3y], cur_ps)
    r["ps_pct_all"] = pct_rank(ps_daily, cur_ps)
    r["val_n"] = len(val_sorted)
    r["val_start"] = val_sorted[-1].get("TRADE_DATE", "")[:10] if val_sorted else None
    r["pe_em_ttm"] = cur_pe

    # 口径 B：自建季末 TTM PE 序列（用东财市值 + 自算 TTM 归母）
    #   ⚠️ 单位：TOTAL_MARKET_CAP 与 TTM 归母都是「元」，PE = mc / tnp（不可先除 1e8 再相除）
    #   ⚠️ 季末日未必是交易日 → 取「≤ 该季末的最近一个交易日」市值
    mcap_by_date = {}
    for x in val_sorted:
        d = x.get("TRADE_DATE", "")[:10]
        if d and d not in mcap_by_date:
            mcap_by_date[d] = x.get("TOTAL_MARKET_CAP")
    mc_dates = sorted(mcap_by_date)

    def mc_asof(d):
        lo = [x for x in mc_dates if x <= d]
        return mcap_by_date[lo[-1]] if lo else None

    self_series = []
    for d in ds_all:
        if d < "2016-01-01":
            continue
        ds = [x for x in ds_all if x <= d]
        if len(ds) < 4:
            continue
        vals = [np_sq.get(x) for x in ds[-4:]]
        if any(v is None for v in vals):
            continue
        tnp = sum(vals)
        if tnp <= 0:
            continue
        mc_d = mc_asof(d)
        if not mc_d:
            continue
        self_series.append((d, mc_d / tnp))
    r["self_pe_series"] = [(d, round(v, 2)) for d, v in self_series]
    cur_self_pe = r.get("pe_ttm")
    vals3 = [v for d, v in self_series if d >= "2023-11-20"]
    vals_all = [v for _, v in self_series]
    r["self_pe_pct_3y"] = pct_rank(vals3, cur_self_pe)
    r["self_pe_pct_all"] = pct_rank(vals_all, cur_self_pe)
    r["self_pe_n"] = len(self_series)
    r["self_pe_start"] = self_series[0][0] if self_series else None

    # ---------- 价格位置 ----------
    closes = [(x.get("TRADE_DATE", "")[:10], rd(x.get("CLOSE_PRICE"))) for x in val_sorted
              if rd(x.get("CLOSE_PRICE")) is not None]
    w52 = [c for c in closes if c[0] >= "2025-11-20"]
    if w52:
        hi = max(w52, key=lambda c: c[1])
        lo = min(w52, key=lambda c: c[1])
        r["w52_high"] = hi[1]
        r["w52_high_date"] = hi[0]
        r["w52_low"] = lo[1]
        r["w52_low_date"] = lo[0]
        r["dd_from_w52"] = round((closes[0][1] / hi[1] - 1) * 100.0, 2) if closes else None
    if kl:
        klw = [x for x in kl if x["day"] >= "2025-11-20"]
        if klw:
            ih = max(klw, key=lambda x: float(x["high"]))
            il = min(klw, key=lambda x: float(x["low"]))
            r["intraday_52w_high"] = float(ih["high"])
            r["intraday_52w_high_date"] = ih["day"]
            r["intraday_52w_low"] = float(il["low"])
            r["intraday_52w_low_date"] = il["day"]
            r["dd_from_intraday_52w"] = round((closes[0][1] / float(ih["high"]) - 1) * 100.0, 2) if closes else None
    # 板块顶（2026-01-29）以来收益
    base = next((c[1] for c in closes if c[0] <= PEAK_DATE), None)
    r["price_at_peak"] = base
    r["ret_since_peak"] = round((closes[0][1] / base - 1) * 100.0, 2) if (base and closes) else None
    # 2025 / 2026 年度涨跌
    def ret_between(d0, d1):
        b = next((c[1] for c in closes if c[0] <= d0), None)
        e = next((c[1] for c in closes if c[0] <= d1), None)
        if b and e:
            return round((e / b - 1) * 100.0, 2)
        return None
    r["ret_2025"] = ret_between("2024-12-31", "2025-12-31")
    r["ret_ytd_2026"] = ret_between("2025-12-31", "2026-11-19")
    return r


def screen(r):
    """质量门槛 6 条淘汰指标 + 1 条观察指标 + 3 条豁免（唯一口径见 skills/quality-screen.md）。

    ① 10 年平均 ROE < 8%          ② 5 年累计 FCF < 0
    ③ 利息覆盖倍数 < 2 倍          ④ 长期毛利率 < 15%
    ⑤ 5 年平均 OCF/净利润 < 0.7    ⑥ 长期净利率 < 5%
    ⑦ 5 年经济稀释 > 20%（观察项，只标注不淘汰）
    """
    res = {}
    roe = r.get("roe_10y_avg")
    res["i1_roe"] = (roe is not None and roe >= 8.0, roe)
    fcf = r.get("fcf_5y_yi")
    res["i2_fcf"] = (fcf is not None and fcf > 0, fcf)
    ic = r.get("icov_5y_min")
    res["i3_icov"] = (ic is not None and ic >= 2.0, ic)
    gm = r.get("gm_10y_avg")
    res["i4_gm"] = (gm is not None and gm >= 15.0, gm)
    oc = r.get("ocf_ni_5y_avg")
    # ⚠️ OCF/NI 以百分数计（100×比率），阈值 0.7 必须写成 70
    res["i5_ocfni"] = (oc is not None and oc >= 70.0, oc)
    nm = r.get("nm_10y_avg")
    res["i6_nm"] = (nm is not None and nm >= 5.0, nm)
    dil = r.get("economic_dilution")
    res["i7_dilution"] = (dil is not None and dil > 20.0, dil)

    fails = [k for k in ("i1_roe", "i2_fcf", "i3_icov", "i4_gm", "i5_ocfni", "i6_nm")
             if not res[k][0]]

    # ---- 豁免规则 ----
    ann = r.get("annual", [])
    ex = []
    gm_now = ann[-1]["gm"] if ann else None
    nm_now = ann[-1]["nm"] if ann else None
    ocf_last2 = [a["ocf"] for a in ann[-2:] if a["ocf"] is not None]
    # 豁免A：战略投入期（上市不足 10 年 + 毛利率>30% + 近 2 年 OCF 为正）
    listed_years = len(ann)
    if "i1_roe" in fails and listed_years < 10 and (gm_now or 0) > 30 \
            and len(ocf_last2) == 2 and all(x > 0 for x in ocf_last2):
        ex.append("豁免A(战略投入期)")
        fails.remove("i1_roe")
    # 豁免B：主动低利润率（毛利率>30% + 净利率回升至 5% 以上）
    #   附加条件：近 10 年不得出现单年巨亏（净利率 < -50%）的"爆雷年"——
    #   一次巨额减值属于资本配置失败，不是"主动不赚"，不得豁免。
    nm_worst = min([a["nm"] for a in ann[-10:] if a["nm"] is not None], default=None)
    if "i6_nm" in fails and (gm_now or 0) > 30 and (nm_now or 0) >= 5 \
            and (nm_worst is None or nm_worst > -50):
        ex.append("豁免B(主动低利润率)")
        fails.remove("i6_nm")
    # 豁免C：高周转薄利（ROE>20% + OCF/NI>1.0 + 平台/会员模式）——有色不适用
    r["screen"] = res
    r["screen_fails"] = fails
    r["screen_exempt"] = ex
    r["screen_pass"] = (len(fails) == 0)
    # 经济稀释为观察项：不改变判定
    return r


def pe_ps_divergence(r):
    """PE 分位与 PS 分位的分歧 = 利润率周期性扩张的检验。

    正常化PE ≡ PS ÷ 恒定净利率 → 若 PE 分位极低而 PS 分位居中，
    说明低 PE 来自「利润率处于历史高位」，而非股价便宜。
    """
    pe = r.get("pe_pct_3y")
    ps = r.get("ps_pct_3y")
    if pe is None or ps is None:
        r["pe_ps_div_3y"] = None
        return r
    r["pe_ps_div_3y"] = round(ps - pe, 1)
    d = r["pe_ps_div_3y"]
    if d >= 20:
        r["pe_credible"] = False
    elif d <= -20:
        r["pe_credible"] = True
    else:
        r["pe_credible"] = None
    return r


def main():
    out = []
    for code, name, seg, ah in UNIVERSE:
        try:
            r = build(code, name, seg, ah)
        except Exception as e:
            print("ERR", code, type(e).__name__, e)
            continue
        if r:
            screen(r)
            pe_ps_divergence(r)
            out.append(r)
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "_analysis.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"完成 {len(out)} 家 -> {p}")


if __name__ == "__main__":
    main()
