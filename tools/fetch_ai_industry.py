#!/usr/bin/env python3
"""采集AI产业链A股公司财务+行情数据（东方财富年报 + 腾讯行情）。

覆盖五层蛋糕中的可投资A股标的：
  L1 芯片：寒武纪/海光/龙芯（与半导体报告交叉，这里取AI视角）
  L2 基础设施：光模块/服务器/PCB/散热/电源/连接器（核心）
  L3 云/平台：金山云等
  L4 模型：科大讯飞/金山办公等
  L5 应用：金山办公/科大讯飞/恒生电子等

输出 JSON，供 industry-research 报告引用。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

# (代码, 公司, 环节, 层级Tier)
CODES = [
    # ===== L2 光模块（AI算力核心卖铲人）=====
    ("300308", "中际旭创", "光模块", "T1"),
    ("300502", "新易盛",   "光模块", "T1"),
    ("300394", "天孚通信", "光模块(器件)", "T1"),
    ("002281", "光迅科技", "光模块(器件)", "T2"),
    ("688205", "德科立",   "光模块(放大器)", "T2"),
    ("300620", "光库科技", "光模块(铌酸锂)", "T3"),

    # ===== L2 服务器/算力ODM =====
    ("601138", "工业富联", "服务器ODM", "T1"),
    ("000977", "浪潮信息", "服务器", "T1"),
    ("603019", "中科曙光", "服务器/算力", "T2"),
    ("000938", "紫光股份", "服务器/云", "T2"),
    ("000034", "神州数码", "服务器分销/云", "T3"),

    # ===== L2 PCB（AI服务器/交换机高频高速板）=====
    ("002463", "沪电股份", "PCB", "T1"),
    ("300476", "胜宏科技", "PCB", "T1"),
    ("600183", "生益科技", "覆铜板/PCB", "T2"),
    ("002916", "深南电路", "PCB", "T2"),

    # ===== L2 散热/液冷 =====
    ("002837", "英维克",   "液冷/散热", "T1"),
    ("300499", "高澜股份", "液冷", "T3"),
    ("301018", "申菱环境", "数据中心温控", "T3"),

    # ===== L2 电源 =====
    ("002851", "麦格米特", "电源", "T2"),
    ("300870", "欧陆通",   "电源", "T3"),

    # ===== L2 连接器 =====
    ("002475", "立讯精密", "连接器/组装", "T1"),

    # ===== L1 AI芯片（AI视角，财务快照）=====
    ("688256", "寒武纪",   "AI芯片", "T1"),
    ("688041", "海光信息", "AI芯片/CPU", "T1"),
    ("688047", "龙芯中科", "CPU/自主", "T3"),

    # ===== L4/L5 模型与应用 =====
    ("688111", "金山办公", "AI办公应用", "T2"),
    ("002230", "科大讯飞", "AI语音/模型", "T2"),
    ("688561", "奇安信",   "AI安全", "T3"),
    ("600570", "恒生电子", "AI金融", "T3"),
    ("300496", "中科创达", "AI边缘/智能汽车", "T3"),
]


def fetch_financials(code):
    """东方财富年报数据：营收/增速/净利/毛利率/ROE/OCF/负债率。"""
    market = "SH" if code.startswith(("6", "9", "5")) else "SZ"
    url = "https://datacenter.eastmoney.com/securities/api/data/get"
    params = {"type": "RPT_F10_FINANCE_MAINFINADATA", "sty": "ALL",
              "filter": f'(SECUCODE="{code}.{market}")(REPORT_TYPE="年报")',
              "p": "1", "ps": "3", "sr": "-1", "st": "REPORT_DATE",
              "source": "HSF10", "client": "PC"}
    try:
        d = ad._curl_json(url, params)
    except Exception:
        return None
    rows = d.get("result", {}).get("data", []) or []
    if not rows:
        return None
    r = rows[0]
    r_prev = rows[1] if len(rows) > 1 else {}
    rev = r.get("TOTALOPERATEREVE")
    np = r.get("PARENTNETPROFIT")
    rev_g = r.get("TOTALOPERATEREVETZ")
    np_g = r.get("PARENTNETPROFITTZ")
    # 毛利率需另算或取字段；东方财富该接口含 NEWMOFHAO（毛利率%）? 实测取 XLRLJB（销售净利率）
    gross = r.get("XSJLL")  # 销售净利率(%)
    roe = r.get("ROEJQ")
    eps = r.get("EPSJB")
    # 经营现金流与负债率
    ocf = r.get("NETCASH_OPERATE_PK")
    liab = r.get("LIABILITY")
    ta = r.get("TOTAL_ASSETS_PK")
    debt = (liab / ta * 100) if (liab and ta) else None
    ocf_np = (ocf / np) if (ocf and np and np != 0) else None
    return {
        "report_date": (r.get("REPORT_DATE") or "")[:10],
        "revenue_yi": round(rev/1e8, 2) if rev else None,
        "rev_growth_pct": round(rev_g, 1) if rev_g is not None else None,
        "netprofit_yi": round(np/1e8, 2) if np else None,
        "np_growth_pct": round(np_g, 1) if np_g is not None else None,
        "net_margin_pct": round(gross, 1) if gross is not None else None,  # 净利率
        "roe_pct": round(roe, 1) if roe is not None else None,
        "eps": round(eps, 3) if eps is not None else None,
        "ocf_np_ratio": round(ocf_np, 2) if ocf_np else None,
        "debt_ratio_pct": round(debt, 1) if debt is not None else None,
    }


def fetch_quote(code):
    """腾讯行情：现价/总市值/PE/PB。"""
    qq = ad._qq_code(code)
    try:
        raw = ad._curl(f"https://qt.gtimg.cn/q={qq}")
    except Exception:
        return None
    d = ad._parse_qq_quote(raw)
    if not d:
        return None
    def _f(x):
        try:
            return float(x)
        except (ValueError, TypeError):
            return None
    return {
        "price": _f(d.get("price")),
        "market_cap_yi": _f(d.get("market_cap")),   # 亿元
        "pe": _f(d.get("pe")),
        "pb": _f(d.get("pb")),
    }


def main():
    out = []
    print(f"{'公司':10}{'代码':8}{'环节':12}{'营收亿':>9}{'增速':>8}{'净利亿':>9}{'ROE%':>7}{'市值亿':>10}{'PE':>8}", file=sys.stderr)
    for code, name, seg, tier in CODES:
        fin = fetch_financials(code)
        q = fetch_quote(code)
        rec = {"code": code, "name": name, "segment": seg, "tier": tier,
               "fin": fin, "quote": q}
        out.append(rec)
        f = fin or {}
        qq = q or {}
        rev = f"{f.get('revenue_yi','-')}" if f.get('revenue_yi') else "-"
        rg = f"{f.get('rev_growth_pct'):>6.0f}%" if f.get('rev_growth_pct') is not None else "-"
        np_ = f"{f.get('netprofit_yi','-')}" if f.get('netprofit_yi') else "-"
        roe = f"{f.get('roe_pct'):>5.1f}" if f.get('roe_pct') is not None else "-"
        mc = f"{qq.get('market_cap_yi'):>9.0f}" if qq.get('market_cap_yi') else "-"
        pe = f"{qq.get('pe'):>7.1f}" if qq.get('pe') else "-"
        print(f"{name:10}{code:8}{seg:12}{rev:>9}{rg:>8}{np_:>9}{roe:>7}{mc:>10}{pe:>8}", file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
