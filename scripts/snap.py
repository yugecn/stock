# snap.py — 抓腾讯实时/收盘行情，生成 wangwang_snapshot_YYYYMMDD.json（保留旧快照里的日内成交形状与20日均额）
import json, glob, urllib.request, datetime
old = json.load(open(sorted(glob.glob('wangwang_snapshot_*.json'))[-1]))
prev = {it['code']: it for it in old['items']}
import re
F = re.findall(r"\('(\d{6})'", open('fetch.py').read().split('\n')[2])
codes = list(dict.fromkeys(F + list(prev)))
A20 = {k: v for k, v in json.load(open(sorted(glob.glob('single_etf_*.json'))[-1]))['avg20'].items()}
q = ','.join(('sh' if c[0] == '5' else 'sz') + c for c in codes)
txt = urllib.request.urlopen('https://qt.gtimg.cn/q=' + q, timeout=15).read().decode('gbk')
items, ts = [], ''
for line in txt.split(';'):
    if '="' not in line: continue
    f = line.split('="')[1].split('~')
    if len(f) < 38: continue
    c = f[2]; ts = max(ts, f[30])
    it = dict(prev.get(c, {})); it.update(code=c, price=float(f[3]), pct=float(f[32]), amount_yi=round(float(f[37]) / 1e4, 4))
    if not it.get('avg20_yi') and c in A20: it['avg20_yi'] = A20[c]
    items.append(it)
d = ts[:8]
old.update(generated_at=f'{d[:4]}-{d[4:6]}-{d[6:]} {ts[8:10]}:{ts[10:12]}:{ts[12:14]} (北京时间)', trade_date=d, items=items)
json.dump(old, open(f'wangwang_snapshot_{d}.json', 'w'), ensure_ascii=False)
print(old['generated_at'], len(items), round(sum(i['amount_yi'] for i in items), 2))
