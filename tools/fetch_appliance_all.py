#!/usr/bin/env python3
"""家电漏斗：一次抓全~30家候选的 quote(PE/市值)+financials(营收/净利/毛利/ROE)+quality(OCF/负债率)。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

CODES = [
    # 白电三巨头
    ("000333", "美的集团", "白电"), ("000651", "格力电器", "白电"), ("600690", "海尔智家", "白电"),
    # 黑电
    ("600060", "海信视像", "黑电"), ("000100", "TCL科技", "黑电/面板"), ("600839", "四川长虹", "黑电"),
    ("000921", "海信家电", "白电/厨电"),
    # 厨电
    ("002508", "老板电器", "厨电"), ("002035", "华帝股份", "厨电"), ("002677", "浙江美大", "集成灶"),
    ("300894", "火星人", "集成灶"), ("605336", "帅丰电器", "集成灶"),
    # 小家电
    ("002032", "苏泊尔", "小家电"), ("002242", "九阳股份", "小家电"), ("002705", "新宝股份", "小家电/外销"),
    ("603355", "莱克电气", "小家电"), ("603486", "科沃斯", "清洁电器"), ("688169", "石头科技", "清洁电器"),
    ("605555", "德昌股份", "微特电机"),
    # 电工/照明
    ("603195", "公牛集团", "电工"), ("603515", "欧普照明", "照明"), ("000541", "佛山照明", "照明"),
    # 零部件
    ("002011", "盾安环境", "阀件"), ("600619", "海立股份", "压缩机"), ("002050", "三花智控", "阀件"),
    ("003816", "声光电科", "半导体-待核实"),
]


def fetch(code):
    out = {"code": code}
    # quote
    try:
        qq = ad._qq_code(code)
        d = ad._parse_qq_quote(ad._curl(f"https://qt.gtimg.cn/q={qq}"))
        out["price"] = d.get("price"); out["mktcap_yi"] = d.get("market_cap")
        out["pe"] = d.get("pe"); out["pb"] = d.get("pb")
    except Exception as e:
        out["quote_err"] = str(e)
    # financials + quality
    market = "SH" if code.startswith(("6", "9", "5")) else "SZ"
    url = "https://datacenter.eastmoney.com/securities/api/data/get"
    params = {"type": "RPT_F10_FINANCE_MAINFINADATA", "sty": "ALL",
              "filter": f'(SECUCODE="{code}.{market}")(REPORT_TYPE="年报")',
              "p": "1", "ps": "2", "sr": "-1", "st": "REPORT_DATE", "source": "HSF10", "client": "PC"}
    try:
        rows = ad._curl_json(url, params).get("result", {}).get("data", []) or []
        if rows:
            r = rows[0]
            ocf = r.get("NETCASH_OPERATE_PK"); np = r.get("PARENTNETPROFIT")
            liab = r.get("LIABILITY"); ta = r.get("TOTAL_ASSETS_PK")
            out["rev"] = r.get("TOTALOPERATEREVE")
            out["np"] = np
            out["gm"] = r.get("XSMLL")  # 毛利率
            out["roe"] = r.get("ROEJQ")
            out["rev_g"] = r.get("TOTALOPERATEREVETZ")
            out["np_g"] = r.get("PARENTNETPROFITTZ")
            out["ocf"] = ocf
            out["ocf_np"] = (ocf/np) if (ocf and np and np != 0) else None
            out["debt"] = (liab/ta*100) if (liab and ta) else None
    except Exception as e:
        out["fin_err"] = str(e)
    return out


def yi(v):
    try: return f"{float(v)/1e8:.0f}"
    except: return "-"
def pct(v):
    try: return f"{float(v):+.0f}%"
    except: return "-"


def main():
    results = []
    print(f"{'公司':9}{'环节':8}{'价':>7}{'市值亿':>9}{'PE':>7}{'PB':>6} | {'营收':>6}{'增':>5}{'净利':>6}{'增':>6}{'毛利':>5}{'ROE':>5}{'OCF/净利':>8}{'负债%':>6}", file=sys.stderr)
    for code, name, seg in CODES:
        r = fetch(code); r["name"] = name; r["seg"] = seg; results.append(r)
        onp = f"{r['ocf_np']:.0%}" if r.get('ocf_np') else "-"
        dr = f"{r['debt']:.0f}" if r.get('debt') else "-"
        print(f"{name:9}{seg:8}{str(r.get('price')):>7}{str(r.get('mktcap_yi')):>9}{str(r.get('pe')):>7}{str(r.get('pb')):>6} | {yi(r.get('rev')):>6}{pct(r.get('rev_g')):>5}{yi(r.get('np')):>6}{pct(r.get('np_g')):>6}{pct(r.get('gm')):>5}{pct(r.get('roe')):>5}{onp:>8}{dr:>6}", file=sys.stderr)
    print(json.dumps(results, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
