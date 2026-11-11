# build2.py — 汪汪队资金看板数据构建（公开数据自算）
# 输入: sse/*.json (上交所份额,万份), szse.json (深交所份额,万份), kline.json (腾讯日K不复权,量=手),
#       wangwang_snapshot_*.json (盘中成交额快照, 可选)
# 输出: own_flow.json (兼容旧格式), dashboard.json (Page 用), flows_daily.csv, flows_by_fund.csv
# 口径: 当日净流入 = Σ (当日份额 − 前日份额) × 当日收盘价；份额拆分/合并自动检测并按折算后价格计算
import json, os, glob, csv
os.chdir(os.path.dirname(os.path.abspath(__file__)))
exec(open('fetch.py').read().split('def get')[0])  # -> F
K = json.load(open('kline.json')); SZ = json.load(open('szse.json'))
SH = {os.path.basename(f)[:-5]: json.load(open(f)) for f in glob.glob('sse/*.json')}
px = {c: {r[0]: dict(o=float(r[1]), c=float(r[2]), h=float(r[3]), l=float(r[4]), v=float(r[5])) for r in K[c]} for c, _, _ in F}
dates = sorted(d for d in {r[0] for v in K.values() for r in v} if d >= '2023-09-25')
NAME = {c: n for c, n, _ in F}; CAT = {c: k for c, _, k in F}
CATS = ['沪深300', '中证500', '中证1000', 'A500', '科创50', '创业板', '上证50', '上证指数']

def sh(c, d): return SZ[c].get(d) if c[0] == '1' else SH.get(d, {}).get(c)

KS = [2, 3, 4, 5, 10, 0.5, 1/3, 0.25, 0.2, 0.1]
def split_check(c, i):
    """返回 k (份额倍数) 若 dates[i] 发生拆分/合并，否则 None。要求份额比≈k 且 价格在当日或次日≈1/k。"""
    p, d = dates[i-1], dates[i]
    a, b = sh(c, p), sh(c, d)
    if not a or not b: return None
    r = b / a
    if 0.77 < r < 1.3: return None
    k = min(KS, key=lambda x: abs(r/x - 1))
    if abs(r/k - 1) > 0.12: return None
    p0 = px[c].get(p)
    for j in (i, i+1):
        if j < len(dates) and p0 and px[c].get(dates[j]):
            if abs(px[c][dates[j]]['c'] / p0['c'] * k - 1) < 0.12:
                return k, (j == i)
    return None

out = []; splits = []
for i, d in enumerate(dates[1:], 1):
    p = dates[i-1]; tot = 0; amt = 0; per = {}
    for c in NAME:
        P = px[c].get(d)
        if P: amt += P['v']*100*(P['o']+P['c']+P['h']+P['l'])/4/1e8
        a, b = sh(c, p), sh(c, d)
        if a is None or b is None or not P: continue
        sc = split_check(c, i)
        if sc:
            k, adj_today = sc
            post_px = P['c'] if adj_today else P['c'] / k
            f = (b - a*k)*1e4*post_px/1e8
            splits.append(dict(code=c, name=NAME[c], date=d, ratio=round(b/a, 3), k=k,
                               raw_flow=round((b-a)*1e4*P['c']/1e8, 2), adj_flow=round(f, 2)))
        else:
            f = (b - a)*1e4*P['c']/1e8
        per[c] = round(f, 2); tot += f
    out.append(dict(date=d, netflow=round(tot, 2), amount=round(amt, 2), per=per))

json.dump(dict(funds=F, days=out, splits=splits), open('own_flow.json', 'w'), ensure_ascii=False)

# ---------- dashboard.json ----------
last = out[-1]['date']
def sumf(c, n):
    return round(sum(x['per'].get(c, 0) for x in out[-n:]), 2)
def sum_since(c, d0):
    return round(sum(x['per'].get(c, 0) for x in out if x['date'] >= d0), 2)
funds = []
for c, n, cat in F:
    s = sh(c, last); P = px[c][last]
    funds.append(dict(code=c, name=n, cat=cat, ex='SH' if c[0] == '5' else 'SZ',
        shares_yi=round(s/1e4, 2), close=P['c'], aum_yi=round(s*1e4*P['c']/1e8, 2),
        f1=sumf(c, 1), f5=sumf(c, 5), f20=sumf(c, 20), f60=sumf(c, 60),
        ytd=sum_since(c, '2026-01-01'), cum=sum_since(c, '2023-10-09'),
        amt1=round(P['v']*100*(P['o']+P['c']+P['h']+P['l'])/4/1e8, 2)))
daily = []; cum = 0
for x in out:
    if x['date'] >= '2023-10-09': cum += x['netflow']
    cats = {k: 0.0 for k in CATS}
    for c, v in x['per'].items(): cats[CAT[c]] += v
    daily.append(dict(d=x['date'], nf=x['netflow'], amt=x['amount'],
                      cum=round(cum, 2) if x['date'] >= '2023-10-09' else None,
                      cat={k: round(v, 2) for k, v in cats.items()}))
def roll(n): return round(sum(x['netflow'] for x in out[-n:]), 2)
work_days = [x for x in out if x['netflow'] >= 100]
streak = 0
for x in reversed(out):
    if x['netflow'] >= 100: streak += 1
    else: break
snap = None
sf = sorted(glob.glob('wangwang_snapshot_*.json'))
if sf:
    S = json.load(open(sf[-1])); our = set(NAME)
    items = [it for it in S['items'] if it['code'] in our]
    # 篮子平均日内成交额分布
    shapes = [it['shape'] for it in items if it.get('shape')]
    tg = [t for t, _ in shapes[0]] if shapes else []
    avg = [[t, round(sum(s[j][1] for s in shapes)/len(shapes), 5)] for j, t in enumerate(tg)]
    snap = dict(generated_at=S['generated_at'], trade_date=S['trade_date'],
                amount_yi=round(sum(it['amount_yi'] for it in items), 2),
                avg20_yi=round(sum(it.get('avg20_yi') or 0 for it in items), 2),
                items=[dict(code=it['code'], amount_yi=it['amount_yi'], pct=it['pct'], price=it['price']) for it in items],
                shape=avg)
D = dict(as_of=last, first=out[0]['date'], cum_start='2023-10-09', cats=CATS, funds=funds, daily=daily,
         stats=dict(nf1=out[-1]['netflow'], amt1=out[-1]['amount'], nf5=roll(5), nf20=roll(20), nf60=roll(60),
                    ytd=round(sum(x['netflow'] for x in out if x['date'] >= '2026-01-01'), 2), cum=round(cum, 2),
                    work_days_total=len(work_days), work_days_60=sum(1 for x in out[-60:] if x['netflow'] >= 100),
                    streak=streak, aum=round(sum(f['aum_yi'] for f in funds), 2)),
         top_in=[dict(d=x['date'], nf=x['netflow'], amt=x['amount']) for x in sorted(out, key=lambda x: -x['netflow'])[:12]],
         top_out=[dict(d=x['date'], nf=x['netflow'], amt=x['amount']) for x in sorted(out, key=lambda x: x['netflow'])[:8]],
         splits=splits, snapshot=snap)
json.dump(D, open('dashboard.json', 'w'), ensure_ascii=False, separators=(',', ':'))

with open('flows_daily.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh); w.writerow(['日期', '净流入(亿元)', '成交额估算(亿元)', '累计净流入(亿元,自2023-10-09)'] + CATS)
    for x in daily: w.writerow([x['d'], x['nf'], x['amt'], x['cum'] if x['cum'] is not None else ''] + [x['cat'][k] for k in CATS])
with open('flows_by_fund.csv', 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh); w.writerow(['日期'] + [f'{c} {n}' for c, n, _ in F])
    for x in out: w.writerow([x['date']] + [x['per'].get(c, '') for c, _, _ in F])

print('as_of', last, 'splits', splits)
print({k: v for k, v in D['stats'].items()})
for x in out[-5:]: print(x['date'], x['netflow'], x['amount'])
print('top', [(x['d'], x['nf']) for x in D['top_in'][:6]])
print('out', [(x['d'], x['nf']) for x in D['top_out'][:6]])
print('snap', snap and (snap['amount_yi'], snap['avg20_yi'], snap['generated_at']))
print('size', os.path.getsize('dashboard.json'))
