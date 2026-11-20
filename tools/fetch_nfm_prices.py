import json, os, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_nonferrous import UNIVERSE  # noqa

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def curl(url, headers=None, tries=4):
    h = ["-H", "User-Agent: " + UA]
    for k, v in (headers or {}).items():
        h += ["-H", f"{k}: {v}"]
    for i in range(tries):
        r = subprocess.run(["curl", "-s", "--noproxy", "*"] + h + [url],
                           capture_output=True, timeout=45)
        s = r.stdout.decode("utf-8", errors="ignore")
        if s.strip():
            return s
        time.sleep(1.5)
    return ""


# 新浪期货日K：symbol=交易所代码，如 CU0(沪铜) AL0(沪铝) AU0(沪金) AG0(沪银)
#                LC0(碳酸锂-广期所) SN0(沪锡) NI0(沪镍) ZN0(沪锌) PB0(沪铅) SS0(不锈钢)
SYMS = {"CU0": "沪铜", "AL0": "沪铝", "AU0": "沪金", "AG0": "沪银",
        "LC0": "碳酸锂", "SN0": "沪锡", "NI0": "沪镍", "ZN0": "沪锌",
        "PB0": "沪铅", "SS0": "沪镍(不锈)"}


def fut_kline(sym):
    url = ("https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_"
           + sym + "=/InnerFuturesNewService.getDailyKLine?symbol=" + sym)
    s = curl(url, {"Referer": "https://finance.sina.com.cn"})
    s = s.strip()
    i, j = s.find("("), s.rfind(")")
    if i < 0 or j < 0:
        return []
    try:
        arr = json.loads(s[i + 1:j])
    except Exception:
        return []
    out = []
    for row in arr:
        try:
            out.append({"d": row["d"], "o": float(row["o"]), "h": float(row["h"]),
                        "l": float(row["l"]), "c": float(row["c"])})
        except Exception:
            continue
    return out


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "nonferrous", "commodity.json")
res = {}
if os.path.exists(CACHE):
    res = json.load(open(CACHE, encoding="utf-8"))
for sym, nm in SYMS.items():
    kl = fut_kline(sym)
    if kl:
        res[sym] = {"name": nm, "kline": kl}
        print(f"{sym} {nm}: {len(kl)} 条  {kl[0]['d']} ~ {kl[-1]['d']}")
    else:
        print(f"{sym} {nm}: 空")
    time.sleep(0.6)
json.dump(res, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
print("saved", CACHE)
