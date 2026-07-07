#!/usr/bin/env python3
"""抓取港股+美股食品饮料核心标的行情。腾讯行情支持 hkXXXXX / usTICKER。"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ashare_data as ad

# (qq_code, 市场, 环节, 公司)
TICKERS = [
    # 港股
    ("hk09633", "HK", "软饮料", "农夫山泉"),
    ("hk02319", "HK", "乳制品", "蒙牛乳业"),
    ("hk00291", "HK", "啤酒", "华润啤酒"),
    ("hk00168", "HK", "啤酒", "青岛啤酒H"),
    ("hk01876", "HK", "啤酒", "百威亚太"),
    ("hk06186", "HK", "乳制品", "中国飞鹤"),
    ("hk01458", "HK", "休闲食品", "周黑鸭"),
    ("hk09985", "HK", "休闲食品", "卫龙美味"),
    ("hk00345", "HK", "软饮料", "维他奶"),
    ("hk00322", "HK", "综合食品", "康师傅控股"),
    ("hk00220", "HK", "综合食品", "统一企业中国"),
    ("hk00506", "HK", "软饮料", "中国食品(中粮可口可乐)"),
    ("hk09858", "HK", "乳制品上游", "优然牧业"),
    ("hk01117", "HK", "乳制品上游", "现代牧业"),
    ("hk00546", "HK", "食品添加", "阜丰集团"),
    ("hk01006", "HK", "包材", "中粮包装"),
    ("hk01112", "HK", "保健品", "H&H国际控股(健合)"),
    ("hk01475", "HK", "方便食品", "日清食品"),
    # 美股/国际(ADR)
    ("usKO", "US", "软饮料", "可口可乐"),
    ("usPEP", "US", "综合食品", "百事可乐"),
    ("usNSRGY", "US", "综合食品", "雀巢(ADR)"),
    ("usDEO", "US", "洋酒", "帝亚吉欧(ADR)"),
    ("usDANOY", "US", "乳制品", "达能(ADR)"),
    ("usSBUX", "US", "餐饮连锁", "星巴克"),
    ("usKHC", "US", "综合食品", "卡夫亨氏"),
    ("usMNST", "US", "能量饮料", "怪物饮料"),
    ("usTAP", "US", "啤酒", "Molson Coors"),
    ("usABEV", "US", "啤酒", "Ambev安贝"),
    ("usKOF", "US", "软饮料", "Coca-Cola FEMSA"),
    ("usSTZ", "US", "啤酒/葡萄酒", "Constellation Brands"),
]


def parse_qq(raw):
    s = raw.find('"'); e = raw.rfind('"')
    if s<0 or e<=s: return {}
    f = raw[s+1:e].split('~')
    if len(f) < 10: return {}
    return f


def main():
    out = []
    for qq, mkt, seg, name in TICKERS:
        try:
            raw = ad._curl(f"https://qt.gtimg.cn/q={qq}")
            f = parse_qq(raw)
            if not f:
                print(f"[{seg}]{name:18}{qq} ❌无数据", file=sys.stderr); continue
            # 港股/美股字段位置与A股不同，name在[1], price在[3] 等，但市值单位港美股不同
            d = {"qq": qq, "mkt": mkt, "seg": seg, "name": name,
                 "price": f[3] if len(f)>3 else None,
                 "change_pct": f[32] if len(f)>32 else None,
                 "pe": f[39] if len(f)>39 else None,
                 "mktcap": f[45] if len(f)>45 else None,   # 港股:亿港元 美股:亿美元
                 "pb": f[46] if len(f)>46 else None,
                 "high52": f[47] if len(f)>47 else None,
                 "low52": f[48] if len(f)>48 else None,
                 "raw_name": f[1] if len(f)>1 else None}
            out.append(d)
            print(f"[{seg:6}]{name:18}{qq:12} 价{str(d['price']):>9} 市值{str(d['mktcap']):>12} PE{str(d['pe']):>7} PB{str(d['pb']):>6}", file=sys.stderr)
        except Exception as e:
            print(f"[{seg}]{name}{qq} ERR {e}", file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
