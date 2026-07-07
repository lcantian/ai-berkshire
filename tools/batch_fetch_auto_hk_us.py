#!/usr/bin/env python3
"""抓取港股+美股汽车标的行情。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

TICKERS = [
    # 港股 整车
    ("hk01211", "整车", "比亚迪H"),
    ("hk02015", "整车", "理想汽车"),
    ("hk09866", "整车", "蔚来"),
    ("hk09868", "整车", "小鹏汽车"),
    ("hk09863", "整车", "零跑汽车"),
    ("hk00175", "整车", "吉利汽车"),
    ("hk02333", "整车", "长城汽车H"),
    ("hk02238", "整车", "广汽集团H"),
    ("hk00489", "整车", "东风集团"),
    ("hk01958", "整车", "北京汽车"),
    ("hk03808", "商用车", "中国重汽H"),
    # 港股 零部件/电池/智能化
    ("hk03928", "动力电池", "中创新航"),
    ("hk01772", "锂资源", "赣锋锂业H"),
    ("hk03606", "汽车玻璃", "福耀玻璃H"),
    ("hk09660", "智驾芯片", "地平线机器人"),
    ("hk02533", "智驾芯片", "黑芝麻智能"),
    ("hk02498", "激光雷达", "速腾聚创"),
    ("hk09690", "汽车后市场", "途虎养车"),
    ("hk01316", "线控转向", "耐世特"),
    ("hk00881", "汽车经销", "中升控股"),
    # 美股/国际
    ("usTSLA", "整车", "特斯拉"),
    ("usTM", "整车", "丰田汽车"),
    ("usGM", "整车", "通用汽车"),
    ("usF", "整车", "福特汽车"),
    ("usRIVN", "整车", "Rivian"),
    ("usLCID", "整车", "Lucid"),
    ("usRACE", "整车", "法拉利"),
    ("usSTLA", "整车", "Stellantis"),
    ("usHSAI", "激光雷达", "禾赛科技"),
    ("usMBLY", "智驾芯片", "Mobileye"),
    ("usTTM", "整车", "塔塔汽车"),
    ("usGMDEF", "电池", "LG新能源(ADR待核实)"),
]


def parse_qq(raw):
    s = raw.find('"'); e = raw.rfind('"')
    if s < 0 or e <= s: return []
    f = raw[s+1:e].split('~')
    return f if len(f) > 10 else []


def main():
    out = []
    for qq, seg, name in TICKERS:
        try:
            raw = ad._curl(f"https://qt.gtimg.cn/q={qq}")
            f = parse_qq(raw)
            if not f:
                print(f"[{seg}]{name}{qq} ❌无数据", file=sys.stderr); continue
            d = {"qq": qq, "seg": seg, "name": name,
                 "price": f[3] if len(f) > 3 else None,
                 "pe": f[39] if len(f) > 39 else None,
                 "mktcap": f[45] if len(f) > 45 else None}
            out.append(d)
            print(f"[{seg:8}]{name:14}{qq:12} 价{str(d['price']):>9} 市值{str(d['mktcap']):>12} PE{str(d['pe']):>7}", file=sys.stderr)
        except Exception as e:
            print(f"[{seg}]{name}{qq} ERR {e}", file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
