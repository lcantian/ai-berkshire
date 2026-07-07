#!/usr/bin/env python3
"""批量抓取汽车产业链公司行情+财务，输出紧凑JSON。
用法: py tools/batch_fetch_auto.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

# (代码, 环节, 公司) —— A股
TICKERS = [
    # 整车 OEM
    ("002594", "整车", "比亚迪"),
    ("601127", "整车", "赛力斯"),
    ("000625", "整车", "长安汽车"),
    ("601633", "整车", "长城汽车"),
    ("600104", "整车", "上汽集团"),
    ("601238", "整车", "广汽集团"),
    ("600733", "整车", "北汽蓝谷"),
    ("600418", "整车", "江淮汽车"),
    ("600166", "商用车", "福田汽车"),
    ("600066", "商用车", "宇通客车"),
    ("000550", "整车", "江铃汽车"),
    # 动力电池/电驱
    ("300750", "动力电池", "宁德时代"),
    ("300014", "动力电池", "亿纬锂能"),
    ("002074", "动力电池", "国轩高科"),
    ("300207", "动力电池", "欣旺达"),
    ("300124", "电驱电控", "汇川技术"),
    # 智能化/零部件
    ("002920", "智能驾驶", "德赛西威"),
    ("002906", "智能座舱", "华阳集团"),
    ("603596", "线控底盘", "伯特利"),
    ("688326", "智能驾驶", "经纬恒润"),
    ("601799", "车灯", "星宇股份"),
    ("600660", "汽车玻璃", "福耀玻璃"),
    ("002050", "热管理", "三花智控"),
    ("002126", "热管理", "银轮股份"),
    ("603997", "座椅", "继峰股份"),
    ("600741", "零部件综合", "华域汽车"),
    ("601689", "零部件", "拓普集团"),
    ("603179", "内饰", "新泉股份"),
    ("603305", "零部件", "旭升集团"),
    # 电池材料
    ("002460", "锂资源", "赣锋锂业"),
    ("002466", "锂资源", "天齐锂业"),
    ("603799", "三元前驱体", "华友钴业"),
    ("002812", "隔膜", "恩捷股份"),
    ("603659", "负极/涂覆", "璞泰来"),
    ("002709", "电解液", "天赐材料"),
    ("688005", "正极", "容百科技"),
    ("300073", "正极", "当升科技"),
    ("300769", "正极", "德方纳米"),
    ("300919", "前驱体", "中伟股份"),
    # 轮胎
    ("601966", "轮胎", "玲珑轮胎"),
    ("601058", "轮胎", "赛轮轮胎"),
    ("002984", "轮胎", "森麒麟"),
    # 商用车动力
    ("000338", "商用车动力", "潍柴动力"),
    ("000951", "重卡", "中国重汽"),
]


def fetch_one(code, seg, name):
    out = {"code": code, "seg": seg, "name": name}
    try:
        qq = ad._qq_code(code)
        raw = ad._curl(f"https://qt.gtimg.cn/q={qq}")
        d = ad._parse_qq_quote(raw)
        out["price"] = d.get("price")
        out["mktcap_yi"] = d.get("market_cap")
        out["pe"] = d.get("pe")
        out["pb"] = d.get("pb")
        out["high52"] = d.get("high_52w")
        out["low52"] = d.get("low_52w")
    except Exception as e:
        out["quote_err"] = str(e)
    try:
        code_clean = code.strip()
        market = "SH" if code_clean.startswith(("6", "9", "5")) else "SZ"
        url = "https://datacenter.eastmoney.com/securities/api/data/get"
        params = {"type": "RPT_F10_FINANCE_MAINFINADATA", "sty": "ALL",
                  "filter": f'(SECUCODE="{code_clean}.{market}")(REPORT_TYPE="年报")',
                  "p": "1", "ps": "3", "sr": "-1", "st": "REPORT_DATE",
                  "source": "HSF10", "client": "PC"}
        data = ad._curl_json(url, params)
        rows = data.get("result", {}).get("data", []) or []
        fin = []
        for r in rows[:3]:
            fin.append({"date": (r.get("REPORT_DATE") or "")[:10],
                "rev": r.get("TOTALOPERATEREVE"), "rev_g": r.get("TOTALOPERATEREVETZ"),
                "np": r.get("PARENTNETPROFIT"), "np_g": r.get("PARENTNETPROFITTZ"),
                "gm": r.get("XSMLL"), "npm": r.get("XSJLL"), "roe": r.get("ROEJQ"),
                "eps": r.get("EPSJB"), "bps": r.get("BPS")})
        out["fin"] = fin
    except Exception as e:
        out["fin_err"] = str(e)
    return out


def main():
    results = []
    for code, seg, name in TICKERS:
        r = fetch_one(code, seg, name)
        results.append(r)
        rev = r.get("fin", [{}])[0].get("rev") if r.get("fin") else None
        print(f"[{r['seg']:8}]{r['name']:8}{r['code']} 价{str(r.get('price')):>8} 市值{str(r.get('mktcap_yi')):>10}亿 PE{str(r.get('pe')):>8} PB{str(r.get('pb')):>6}", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
