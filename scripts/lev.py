# lev.py — 杠杆资金（两融）公开数据 → lev.json
# 来源：东方财富数据中心（交易所两融披露汇总，T+1）、新浪财经上证综指日线。仅研究自用，非投资建议。
import json, urllib.request, time, os, glob, datetime
D = os.path.dirname(os.path.abspath(__file__))
def get(url, ref=None):
    for a in range(4):
        try:
            h = {'User-Agent': 'Mozilla/5.0'}
            if ref: h['Referer'] = ref
            return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40).read().decode('utf-8', 'ignore')
        except Exception as e: err = e; time.sleep(3)
    raise err
EM = 'https://datacenter-web.eastmoney.com/api/data/v1/get?source=WEB&reportName={r}&columns={c}&sortColumns={s}&sortTypes=1&pageSize=500&pageNumber={p}{f}'
def em(r, c, s, f=''):
    out, p = [], 1
    while True:
        j = json.loads(get(EM.format(r=r, c=c, s=s, p=p, f=f)))
        if not j.get('result'): break
        out += j['result']['data']
        if p >= j['result']['pages']: break
        p += 1
    return out
# 1) 融资余额 / 融资买入 / 净买入 / 余额占流通市值（2010 起）
L = em('RPTA_RZRQ_LSHJ', 'DIM_DATE,RZYE,RZMRE,RZJME,RZYEZB', 'dim_date')
# 2) 客户数 / 担保物 / 担保比例 / 两融交易额占比（2012 起）
T = em('RPTA_WEB_MARGIN_DAILYTRADE', 'STATISTICS_DATE,FIN_BUY_AMT,MARGIN_TRADE_AMT,TRADE_AMT_RATIO,PERSONAL_INVESTOR_NUM,INVESTOR_NUM,MARGINLIAB_INVESTOR_NUM,FUND_MARKET_CAP,AVG_GUARANTEE_RATIO', 'STATISTICS_DATE')
# 3) 上证综指
K = json.loads(get('https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol=sh000001&scale=240&ma=no&datalen=5000', 'https://finance.sina.com.cn'))
sh = {k['day']: round(float(k['close']), 2) for k in K}
r2 = lambda x, n=2: None if x is None else round(x, n)
tm = {t['STATISTICS_DATE'][:10]: t for t in T}
rows = []
for x in L:
    d = x['DIM_DATE'][:10]; t = tm.get(d, {})
    pers = t.get('PERSONAL_INVESTOR_NUM')  # 万户
    act = liab = buyr = None
    if pers and t.get('INVESTOR_NUM') is not None: act = t['INVESTOR_NUM'] / (pers * 1e4) * 100
    if pers and t.get('MARGINLIAB_INVESTOR_NUM') is not None: liab = t['MARGINLIAB_INVESTOR_NUM'] / (pers * 1e4) * 100
    if t.get('TRADE_AMT_RATIO') and t.get('MARGIN_TRADE_AMT') and x['RZMRE']:
        amt = t['MARGIN_TRADE_AMT'] / (t['TRADE_AMT_RATIO'] / 100)  # A股成交额（亿元）
        buyr = x['RZMRE'] / 1e8 / amt * 100
    rows.append([d, r2(x['RZJME'] / 1e8 if x['RZJME'] is not None else None), r2(x['RZYE'] / 1e8 if x['RZYE'] else None, 1),
                 r2(act, 3), r2(liab, 3), r2(x['RZYEZB'], 3), r2(buyr, 3),
                 r2(t.get('FUND_MARKET_CAP'), 1), r2(t.get('AVG_GUARANTEE_RATIO'), 2), sh.get(d)])
# 4) 分行业融资净买入（东财行业二级 → 申万一级归并），保存每日快照以便对比上期
SW = {'农林牧渔':'动物保健Ⅱ 林业Ⅱ 农产品加工 农业综合Ⅱ 饲料 养殖业 渔业 种植业','基础化工':'橡胶 化学原料 非金属材料Ⅱ 塑料 化学纤维 化学制品 农化制品','钢铁':'普钢 特钢Ⅱ 冶钢原料','有色金属':'能源金属 小金属 工业金属 金属新材料 贵金属','电子':'半导体 消费电子 光学光电子 电子化学品Ⅱ 其他电子Ⅱ 元件','家用电器':'白色家电 厨卫电器 黑色家电 家电零部件Ⅱ 小家电 照明设备Ⅱ','食品饮料':'白酒Ⅱ 调味发酵品Ⅱ 非白酒 食品加工 休闲食品 饮料乳品','纺织服饰':'纺织制造 服装家纺 饰品','轻工制造':'包装印刷 文娱用品 造纸 家居用品','医药生物':'中药Ⅱ 医疗器械 医药商业 生物制品 化学制药 医疗服务','公用事业':'燃气Ⅱ 电力','交通运输':'航空机场 铁路公路 物流 航运港口','房地产':'房地产服务 房地产开发','商贸零售':'互联网电商 旅游零售Ⅱ 专业连锁Ⅱ 一般零售 贸易Ⅱ','社会服务':'专业服务 酒店餐饮 旅游及景区 体育Ⅱ 教育','综合':'综合Ⅱ','建筑材料':'水泥 装修建材 玻璃玻纤','建筑装饰':'房屋建设Ⅱ 基础建设 专业工程 装修装饰Ⅱ 工程咨询服务Ⅱ','电力设备':'电机Ⅱ 光伏设备 风电设备 电池 其他电源设备Ⅱ 电网设备','国防军工':'地面兵装Ⅱ 航海装备Ⅱ 航空装备Ⅱ 航天装备Ⅱ 军工电子Ⅱ','计算机':'IT服务Ⅱ 计算机设备 软件开发','传媒':'游戏Ⅱ 出版 电视广播Ⅱ 广告营销 数字媒体 影视院线','通信':'通信设备 通信服务','银行':'银行Ⅱ','非银金融':'证券Ⅱ 保险Ⅱ 多元金融','汽车':'汽车服务 乘用车 摩托车及其他 商用车 汽车零部件','机械设备':'轨交设备Ⅱ 自动化设备 通用设备 工程机械 专用设备','煤炭':'焦炭Ⅱ 煤炭开采','石油石化':'炼化及贸易 油服工程 油气开采Ⅱ','环保':'环保设备Ⅱ 环境治理','美容护理':'个护用品 化妆品 医疗美容'}
M = {s: k for k, v in SW.items() for s in v.split()}
B = em('RPTA_WEB_BKJYMXN', 'BOARD_NAME,TRADE_DATE,FIN_NETBUY_AMT', 'BOARD_CODE', '&filter=(BOARD_TYPE_CODE%3D%22005%22)')
idate = B[0]['TRADE_DATE'][:10] if B else None
agg, miss = {}, []
for b in B:
    k = M.get(b['BOARD_NAME'])
    if not k: miss.append(b['BOARD_NAME']); continue
    agg[k] = agg.get(k, 0) + (b['FIN_NETBUY_AMT'] or 0) / 1e8
os.makedirs(f'{D}/lev_ind', exist_ok=True)
if idate: json.dump({k: round(v, 2) for k, v in agg.items()}, open(f'{D}/lev_ind/{idate}.json', 'w'), ensure_ascii=False)
hist = sorted(glob.glob(f'{D}/lev_ind/*.json'))
prev = [h for h in hist if os.path.basename(h)[:10] < (idate or '')]
pdate = os.path.basename(prev[-1])[:10] if prev else None
pagg = json.load(open(prev[-1])) if prev else {}
ind = sorted([[k, round(v, 2), pagg.get(k)] for k, v in agg.items()], key=lambda r: -r[1])
out = {'as_of': rows[-1][0], 'cols': ['date', 'net', 'bal', 'act', 'liab', 'balr', 'buyr', 'cash', 'guar', 'sh'],
       'rows': rows, 'ind': {'date': idate, 'prev_date': pdate, 'rows': ind, 'unmapped': miss},
       'source': '东方财富数据中心（交易所两融披露汇总，T+1）；上证综指：新浪财经'}
json.dump(out, open(f'{D}/lev.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('rows', len(rows), rows[0][0], rows[-1], 'ind', idate, len(ind), 'prev', pdate, 'unmapped', miss)
