#!/usr/bin/env python3
"""为食品饮料候选公司(排除酒类)补充质量指标：OCF/净利、资产负债率。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

# 排除所有酒类（白酒/啤酒/葡萄酒）。乳/调味/软饮/休闲/速冻/保健/肉/添加剂/包材/饲料
CODES = [
    # 乳制品
    ("600887", "伊利股份"), ("600597", "光明乳业"), ("002946", "新乳业"), ("002732", "燕塘乳业"),
    # 调味品
    ("603288", "海天味业"), ("600872", "中炬高新"), ("603027", "千禾味业"), ("600305", "恒顺醋业"),
    ("002507", "涪陵榨菜"), ("603317", "天味食品"), ("300908", "仲景食品"), ("603170", "宝立食品"),
    # 软饮料
    ("605499", "东鹏饮料"), ("603156", "养元饮品"), ("000848", "承德露露"),
    ("605337", "李子园"), ("603711", "香飘飘"),
    # 休闲食品
    ("300783", "三只松鼠"), ("603719", "良品铺子"), ("002557", "洽洽食品"), ("603517", "绝味食品"),
    ("603057", "紫燕食品"), ("002847", "盐津铺子"), ("003000", "劲仔食品"), ("002991", "甘源食品"),
    # 速冻/预制/烘焙
    ("603345", "安井食品"), ("002216", "三全食品"), ("001215", "千味央厨"),
    ("300973", "立高食品"), ("603866", "桃李面包"), ("603043", "广州酒家"),
    # 保健品/肉制品
    ("300146", "汤臣倍健"), ("300791", "仙乐健康"), ("000895", "双汇发展"),
    # 食品添加剂/原料
    ("600298", "安琪酵母"), ("002597", "金禾实业"), ("600873", "梅花生物"),
    ("600866", "星湖科技"), ("300138", "晨光生物"), ("300741", "华宝股份"), ("002286", "保龄宝"),
    # 包材
    ("002701", "奥瑞金"), ("600210", "紫江企业"), ("002752", "昇兴股份"), ("002969", "嘉美包装"),
    # 饲料上游
    ("002311", "海大集团"),
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
    ocf = r.get("NETCASH_OPERATE_PK"); np = r.get("PARENTNETPROFIT")
    liab = r.get("LIABILITY"); ta = r.get("TOTAL_ASSETS_PK")
    ocf_np = (ocf / np) if (ocf and np and np != 0) else None
    debt = (liab / ta * 100) if (liab and ta) else None
    return {"ocf_yi": ocf/1e8 if ocf else None, "np_yi": np/1e8 if np else None,
            "ocf_np_ratio": ocf_np, "debt_ratio_pct": debt}


def main():
    results = []
    print(f"{'公司':9}{'代码':8}{'OCF亿':>8}{'净利亿':>8}{'OCF/净利':>9}{'负债率%':>9}", file=sys.stderr)
    for code, name in CODES:
        try:
            r = fetch(code)
            if r:
                r["code"] = code; r["name"] = name; results.append(r)
                ocf = f"{r['ocf_yi']:.1f}" if r['ocf_yi'] else "-"
                npv = f"{r['np_yi']:.1f}" if r['np_yi'] else "-"
                onp = f"{r['ocf_np_ratio']:.0%}" if r['ocf_np_ratio'] else "-"
                dr = f"{r['debt_ratio_pct']:.1f}" if r['debt_ratio_pct'] else "-"
                print(f"{name:9}{code:8}{ocf:>8}{npv:>8}{onp:>9}{dr:>9}", file=sys.stderr)
        except Exception as e:
            print(f"{name}{code} ERR {e}", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
