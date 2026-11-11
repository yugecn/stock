import json,urllib.request,time,os
from concurrent.futures import ThreadPoolExecutor
F=[('510310','沪深300ETF易方达','沪深300'),('588000','科创50ETF华夏','科创50'),('159915','创业板ETF易方达','创业板'),('510300','沪深300ETF华泰柏瑞','沪深300'),('563360','A500ETF华泰柏瑞','A500'),('159352','A500ETF南方','A500'),('512100','中证1000ETF南方','中证1000'),('159338','中证A500ETF国泰','A500'),('510500','中证500ETF南方','中证500'),('159949','创业板50ETF华安','创业板'),('588080','科创50ETF易方达','科创50'),('510050','上证50ETF华夏','上证50'),('510210','上证指数ETF富国','上证指数'),('159845','中证1000ETF华夏','中证1000'),('159952','创业板ETF广发','创业板'),('159361','A500ETF易方达','A500'),('512050','A500ETF华夏','A500'),('159633','中证1000ETF易方达','中证1000'),('560010','中证1000ETF广发','中证1000'),('159919','沪深300ETF嘉实','沪深300')]
def get(url,ref=None):
    for a in range(4):
        try:
            h={'User-Agent':'Mozilla/5.0'}
            if ref:h['Referer']=ref
            return urllib.request.urlopen(urllib.request.Request(url,headers=h),timeout=40).read().decode('utf-8','ignore')
        except Exception as e: err=e; time.sleep(2)
    raise err
os.makedirs('k',exist_ok=True); os.makedirs('sse',exist_ok=True)
K={}
for c,n,cat in F:
    tc=('sh' if c[0] in '5' else 'sz')+c
    d=json.loads(get(f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tc},day,2023-09-01,2026-12-31,1000,'))['data'][tc]
    K[c]=d.get('day') or d.get('qfqday')
json.dump(K,open('kline.json','w'))
dates=sorted({r[0] for v in K.values() for r in v})
# SZSE per fund
SZ={}
for c,n,cat in F:
    if c[0]!='1': continue
    rows={}
    for (s,e) in [('2023-09-01','2024-06-30'),('2024-07-01','2025-03-31'),('2025-04-01','2025-12-31'),('2026-01-01','2026-12-31')]:
        p=1
        while True:
            d=json.loads(get(f'https://fund.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=fund_jjgm&TABKEY=tab1&txtDm={c}&txtStart={s}&txtEnd={e}&PAGENO={p}'))[0]
            for r in d['data']: rows[r['size_date']]=float(r['current_size'].replace(',',''))
            if p>=d['metadata']['pagecount']: break
            p+=1
    SZ[c]=rows; print(c,len(rows),flush=True)
json.dump(SZ,open('szse.json','w'))
shc={c for c,_,_ in F if c[0]=='5'}
def sse(dt):
    fn=f'sse/{dt}.json'
    if os.path.exists(fn): return
    d=json.loads(get(f'https://query.sse.com.cn/commonQuery.do?isPagination=true&pageHelp.pageSize=2000&pageHelp.pageNo=1&sqlId=COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L&STAT_DATE={dt}','https://www.sse.com.cn/'))
    json.dump({r['SEC_CODE']:float(r['TOT_VOL']) for r in d['pageHelp']['data'] if r['SEC_CODE'] in shc},open(fn,'w'))
with ThreadPoolExecutor(8) as ex: list(ex.map(sse,[x for x in dates if x>='2023-09-25']))
print('done',len(os.listdir('sse')))
