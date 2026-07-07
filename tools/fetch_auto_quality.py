#!/usr/bin/env python3
"""为汽车候选公司补充质量指标：经营现金流/净利、资产负债率。
输出 OCF/净利 比值 + 负债率，用于5条硬指标粗筛。
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

# 候选公司（A股，从industry-research的44家筛选有意义的）
CODES = [
    ("600660", "福耀玻璃"), ("300750", "宁德时代"), ("600066", "宇通客车"),
    ("002920", "德赛西威"), ("603596", "伯特利"), ("601799", "星宇股份"),
    ("601058", "赛轮轮胎"), ("600741", "华域汽车"), ("603799", "华友钴业"),
    ("002594", "比亚迪"), ("601633", "长城汽车"), ("300124", "汇川技术"),
    ("002050", "三花智控"), ("601689", "拓普集团"), ("601966", "玲珑轮胎"),
    ("000338", "潍柴动力"), ("000951", "中国重汽"), ("603659", "璞泰来"),
    ("002460", "赣锋锂业"), ("002126", "银轮股份"), ("300014", "亿纬锂能"),
    ("002074", "国轩高科"), ("601127", "赛力斯"), ("000625", "长安汽车"),
    ("600104", "上汽集团"), ("603179", "新泉股份"), ("603997", "继峰股份"),
    ("002906", "华阳集团"), ("000550", "江铃汽车"), ("600166", "福田汽车"),
    ("603305", "旭升集团"), ("300207", "欣旺达"),
]


def fetch(code):
    market = "SH" if code.startswith(("6", "9", "5")) else "SZ"
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
    ocf = r.get("NETCASH_OPERATE_PK")
    np = r.get("PARENTNETPROFIT")
    liab = r.get("LIABILITY")
    ta = r.get("TOTAL_ASSETS_PK")
    ocf_np = (ocf / np) if (ocf and np and np != 0) else None
    debt_ratio = (liab / ta * 100) if (liab and ta) else None
    return {"ocf_yi": ocf/1e8 if ocf else None,
            "np_yi": np/1e8 if np else None,
            "ocf_np_ratio": ocf_np,
            "debt_ratio_pct": debt_ratio}


def main():
    results = []
    print(f"{'公司':8}{'代码':8}{'OCF亿':>8}{'净利亿':>8}{'OCF/净利':>9}{'负债率%':>9}", file=sys.stderr)
    for code, name in CODES:
        try:
            r = fetch(code)
            if r:
                r["code"] = code; r["name"] = name
                results.append(r)
                ocf = f"{r['ocf_yi']:.1f}" if r['ocf_yi'] else "-"
                npv = f"{r['np_yi']:.1f}" if r['np_yi'] else "-"
                onp = f"{r['ocf_np_ratio']:.0%}" if r['ocf_np_ratio'] else "-"
                dr = f"{r['debt_ratio_pct']:.1f}" if r['debt_ratio_pct'] else "-"
                print(f"{name:8}{code:8}{ocf:>8}{npv:>8}{onp:>9}{dr:>9}", file=sys.stderr)
        except Exception as e:
            print(f"{name}{code} ERR {e}", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
