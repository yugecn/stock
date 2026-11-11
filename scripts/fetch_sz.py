import json,urllib.request,time,datetime
from concurrent.futures import ThreadPoolExecutor
exec(open('fetch.py').read().split('def get')[0])
def get(url):
    for a in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=40).read().decode()
        except Exception as e: err=e;time.sleep(2)
    raise err
months=[]
y,m=2023,9
while (y,m)<=(2026,11):
    s=f'{y}-{m:02d}-01'; ny,nm=(y+1,1) if m==12 else (y,m+1); e=(datetime.date(ny,nm,1)-datetime.timedelta(1)).isoformat()
    months.append((s,e)); y,m=ny,nm
def one(c):
    rows={}
    for s,e in months:
        p=1
        while True:
            d=json.loads(get(f'https://fund.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=fund_jjgm&TABKEY=tab1&txtDm={c}&txtStart={s}&txtEnd={e}&PAGENO={p}'))[0]
            for r in d['data']: rows[r['size_date']]=float(r['current_size'].replace(',',''))
            if p>=d['metadata']['pagecount']: break
            p+=1
    return c,rows
with ThreadPoolExecutor(9) as ex: SZ=dict(ex.map(one,[c for c,_,_ in F if c[0]=='1']))
for c,r in SZ.items(): print(c,len(r),min(r) if r else '')
json.dump(SZ,open('szse.json','w'))
