#!/usr/bin/env python3
"""批量抓取食品饮料公司行情+财务，输出紧凑JSON/文本摘要。
用法: py tools/batch_fetch_fb.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

# (代码, 环节, 备注)  —— 排除白酒
TICKERS = [
    # 乳制品
    ("600887", "乳制品", "伊利股份"),
    ("600597", "乳制品", "光明乳业"),
    ("002946", "乳制品", "新乳业"),
    ("002732", "乳制品", "燕塘乳业"),
    # 调味品
    ("603288", "调味品", "海天味业"),
    ("600872", "调味品", "中炬高新"),
    ("603027", "调味品", "千禾味业"),
    ("600305", "调味品", "恒顺醋业"),
    ("002507", "调味品", "涪陵榨菜"),
    ("603317", "调味品", "天味食品"),
    ("300908", "调味品", "仲景食品"),
    ("603170", "调味品", "宝立食品"),
    # 软饮料
    ("605499", "软饮料", "东鹏饮料"),
    ("603156", "软饮料", "养元饮品"),
    ("000848", "软饮料", "承德露露"),
    ("605337", "软饮料", "李子园"),
    ("603711", "软饮料", "香飘飘"),
    # 啤酒(A股)
    ("600600", "啤酒", "青岛啤酒"),
    ("000729", "啤酒", "燕京啤酒"),
    ("600132", "啤酒", "重庆啤酒"),
    ("002461", "啤酒", "珠江啤酒"),
    # 休闲食品
    ("300783", "休闲食品", "三只松鼠"),
    ("603719", "休闲食品", "良品铺子"),
    ("002557", "休闲食品", "洽洽食品"),
    ("603517", "休闲食品", "绝味食品"),
    ("603057", "休闲食品", "紫燕食品"),
    ("002847", "休闲食品", "盐津铺子"),
    ("003000", "休闲食品", "劲仔食品"),
    ("002991", "休闲食品", "甘源食品"),
    # 速冻/预制菜/烘焙
    ("603345", "速冻预制", "安井食品"),
    ("002216", "速冻预制", "三全食品"),
    ("001215", "速冻预制", "千味央厨"),
    ("300973", "烘焙原料", "立高食品"),
    ("603866", "烘焙", "桃李面包"),
    ("603043", "烘焙", "广州酒家"),
    # 保健品
    ("300146", "保健品", "汤臣倍健"),
    ("300791", "保健品", "仙乐健康"),
    # 肉制品
    ("000895", "肉制品", "双汇发展"),
    # 食品添加剂/原料
    ("600298", "食品添加", "安琪酵母"),
    ("002597", "食品添加", "金禾实业"),
    ("600873", "食品添加", "梅花生物"),
    ("600866", "食品添加", "星湖科技"),
    ("300138", "食品添加", "晨光生物"),
    ("300741", "食品添加", "华宝股份"),
    ("002286", "食品添加", "保龄宝"),
    # 包材
    ("002701", "包材", "奥瑞金"),
    ("600210", "包材", "紫江企业"),
    ("002752", "包材", "昇兴股份"),
    ("002969", "包材", "嘉美包装"),
    # 葡萄酒
    ("000869", "葡萄酒", "张裕A"),
    # 饲料/上游
    ("002311", "饲料上游", "海大集团"),
]


def fetch_one(code, seg, name):
    out = {"code": code, "seg": seg, "name": name}
    # quote
    try:
        qq = ad._qq_code(code)
        raw = ad._curl(f"https://qt.gtimg.cn/q={qq}")
        d = ad._parse_qq_quote(raw)
        out["price"] = d.get("price")
        out["mktcap_yi"] = d.get("market_cap")  # 亿
        out["pe"] = d.get("pe")
        out["pb"] = d.get("pb")
        out["high52"] = d.get("high_52w")
        out["low52"] = d.get("low_52w")
    except Exception as e:
        out["quote_err"] = str(e)
    # financials via eastmoney
    try:
        code_clean = code.strip()
        market = "SH" if code_clean.startswith(("6", "9", "5")) else "SZ"
        url = "https://datacenter.eastmoney.com/securities/api/data/get"
        params = {
            "type": "RPT_F10_FINANCE_MAINFINADATA", "sty": "ALL",
            "filter": f'(SECUCODE="{code_clean}.{market}")(REPORT_TYPE="年报")',
            "p": "1", "ps": "3", "sr": "-1", "st": "REPORT_DATE",
            "source": "HSF10", "client": "PC",
        }
        data = ad._curl_json(url, params)
        rows = data.get("result", {}).get("data", []) or []
        fin = []
        for r in rows[:3]:
            fin.append({
                "date": (r.get("REPORT_DATE") or "")[:10],
                "rev": r.get("TOTALOPERATEREVE"),
                "rev_g": r.get("TOTALOPERATEREVETZ"),
                "np": r.get("PARENTNETPROFIT"),
                "np_g": r.get("PARENTNETPROFITTZ"),
                "gm": r.get("XSMLL"),       # 销售毛利率
                "npm": r.get("XSJLL"),      # 销售净利率
                "roe": r.get("ROEJQ"),
                "eps": r.get("EPSJB"),
                "bps": r.get("BPS"),
            })
        out["fin"] = fin
    except Exception as e:
        out["fin_err"] = str(e)
    return out


def main():
    results = []
    for code, seg, name in TICKERS:
        r = fetch_one(code, seg, name)
        results.append(r)
        # 进度
        rev = r.get("fin", [{}])[0].get("rev") if r.get("fin") else None
        print(f"[{r['seg']:6}]{r['name']:8} {r['code']} 价{r.get('price'):>7} 市值{str(r.get('mktcap_yi')):>9}亿 PE{str(r.get('pe')):>7} PB{str(r.get('pb')):>6} | 25营收{rev}", file=sys.stderr)
    # dump JSON
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
