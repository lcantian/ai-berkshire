#!/usr/bin/env python3
"""抓取公牛集团分部收入(主营构成)+现金/债务明细。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

code = "603195"

# 1. 主营构成（分产品/分地区）
print("=" * 60, file=sys.stderr)
print("主营构成（分产品，2025年报）", file=sys.stderr)
print("=" * 60, file=sys.stderr)
url = "https://datacenter.eastmoney.com/securities/api/data/get"
# 主营构成按产品
for rpt in ["RPT_F10_FN_MAINOP"]:
    params = {"type": rpt, "sty": "ALL",
              "filter": f'(SECUCODE="{code}.SH")(REPORT_TYPE="年报")',
              "p": "1", "ps": "30", "sr": "-1", "st": "REPORT_DATE",
              "source": "HSF10", "client": "PC"}
    try:
        d = ad._curl_json(url, params)
        rows = d.get("result", {}).get("data", []) or []
        # 取最新一期
        if rows:
            latest_date = rows[0].get("REPORT_DATE", "")[:10]
            print(f"\n--- {latest_date} ---", file=sys.stderr)
            for r in rows:
                if r.get("REPORT_DATE", "")[:10] != latest_date:
                    continue
                item = r.get("ITEM_NAME", "")
                rev = r.get("MAIN_BUSINESS_INCOME", 0)
                ratio = r.get("MAIN_BUSINESS_RATIO", 0)
                gm = r.get.get("MAIN_BUSINESS_GROSS", 0) if hasattr(r.get, '__call__') else r.get("MAIN_BUSINESS_GROSSMARGIN", r.get("GROSSMARGIN"))
                rev_yi = f"{float(rev)/1e8:.1f}亿" if rev else "-"
                print(f"  {item:20} 收入{rev_yi:>8} 占比{ratio:.1f}%  毛利率{gm:.1f}%" if gm else f"  {item:20} 收入{rev_yi:>8} 占比{ratio:.1f}%", file=sys.stderr)
    except Exception as e:
        print(f"ERR {rpt}: {e}", file=sys.stderr)

# 2. 资产负债表关键项（现金/债务）
print("\n" + "=" * 60, file=sys.stderr)
print("资产负债关键项（2025年报）", file=sys.stderr)
print("=" * 60, file=sys.stderr)
params = {"type": "RPT_F10_FINANCE_MAINFINADATA", "sty": "ALL",
          "filter": f'(SECUCODE="{code}.SH")(REPORT_TYPE="年报")',
          "p": "1", "ps": "1", "sr": "-1", "st": "REPORT_DATE",
          "source": "HSF10", "client": "PC"}
d = ad._curl_json(url, params)
r = d.get("result", {}).get("data", [])[0]
# 打印所有含现金/资产/负债/股本的字段
for k, v in r.items():
    if v is None or v == "":
        continue
    kl = k.upper()
    if any(s in kl for s in ["CASH", "ASSET", "LIAB", "DEBT", "SHARE", "EQUITY", "DIVIDEND", "CAPITAL"]):
        if isinstance(v, (int, float)) and abs(v) > 1e7:
            print(f"  {k} = {v/1e8:.2f}亿", file=sys.stderr)
        elif isinstance(v, (int, float)):
            print(f"  {k} = {v}", file=sys.stderr)
