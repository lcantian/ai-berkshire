#!/usr/bin/env python3
"""为国产半导体候选公司补充质量指标：OCF/净利、资产负债率。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

CODES = [
    # 设备
    ("002371", "北方华创", "设备"), ("688012", "中微公司", "设备"), ("688072", "拓荆科技", "设备"),
    ("688120", "华海清科", "设备"), ("688082", "盛美上海", "设备"), ("300604", "长川科技", "设备"),
    ("688037", "芯源微", "设备"),
    # 材料
    ("688019", "安集科技", "材料"), ("002409", "雅克科技", "材料"), ("300666", "江丰电子", "材料"),
    ("300054", "鼎龙股份", "材料"), ("300346", "南大光电", "材料"), ("688268", "华特气体", "材料"),
    ("688126", "沪硅产业", "材料"),
    # 制造
    ("688981", "中芯国际", "制造"), ("688347", "华虹半导体", "制造"), ("688249", "晶合集成", "制造"),
    # 设计
    ("688041", "海光信息", "设计"), ("688256", "寒武纪", "设计"), ("603501", "韦尔股份", "设计"),
    ("603986", "兆易创新", "设计"), ("002049", "紫光国微", "设计"), ("300661", "圣邦股份", "设计"),
    ("300782", "卓胜微", "设计"), ("300223", "北京君正", "设计"),
    # 封测
    ("600584", "长电科技", "封测"), ("002156", "通富微电", "封测"), ("002185", "华天科技", "封测"),
    # 功率/第三代
    ("688187", "时代电气", "功率"), ("603290", "斯达半导", "功率"), ("600460", "士兰微", "功率"),
    ("600703", "三安光电", "功率"), ("688234", "天岳先进", "第三代"),
    # EDA
    ("301269", "华大九天", "EDA"), ("688521", "芯原股份", "EDA"),
]


def fetch(code):
    market = "SH" if code.startswith(("6", "9", "5")) else ("BJ" if code.startswith("8") else "SZ")
    if code.startswith("688") or code.startswith("300"):
        market = "SH" if code.startswith("688") else "SZ"
    url = "https://datacenter.eastmoney.com/securities/api/data/get"
    params = {"type": "RPT_F10_FINANCE_MAINFINADATA", "sty": "ALL",
              "filter": f'(SECUCODE="{code}.{market}")(REPORT_TYPE="年报")',
              "p": "1", "ps": "2", "sr": "-1", "st": "REPORT_DATE",
              "source": "HSF10", "client": "PC"}
    d = ad._curl_json(url, params)
    rows = d.get("result", {}).get("data", []) or []
    if not rows:
        return None
    r = rows[0]
    ocf = r.get("NETCASH_OPERATE_PK"); np = r.get("PARENTNETPROFIT")
    liab = r.get("LIABILITY"); ta = r.get("TOTAL_ASSETS_PK")
    ocf_np = (ocf / np) if (ocf and np and np != 0) else None
    debt = (liab / ta * 100) if (liab and ta) else None
    return {"ocf_yi": ocf/1e8 if ocf else None, "np_yi": np/1e8 if np else None,
            "ocf_np_ratio": ocf_np, "debt_ratio_pct": debt}


def main():
    results = []
    print(f"{'公司':10}{'代码':8}{'OCF亿':>8}{'净利亿':>8}{'OCF/净利':>9}{'负债率%':>9}", file=sys.stderr)
    for code, name, seg in CODES:
        try:
            r = fetch(code)
            if r:
                r["code"] = code; r["name"] = name; r["seg"] = seg; results.append(r)
                ocf = f"{r['ocf_yi']:.1f}" if r['ocf_yi'] else "-"
                npv = f"{r['np_yi']:.1f}" if r['np_yi'] else "-"
                onp = f"{r['ocf_np_ratio']:.0%}" if r['ocf_np_ratio'] else "-"
                dr = f"{r['debt_ratio_pct']:.1f}" if r['debt_ratio_pct'] else "-"
                print(f"{name:10}{code:8}{ocf:>8}{npv:>8}{onp:>9}{dr:>9}", file=sys.stderr)
        except Exception as e:
            print(f"{name}{code} ERR {e}", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
