import yfinance as yf, pandas as pd, datetime as dt
out='/workspace/zar_data/'
for t in ['NQ=F','ES=F','YM=F']:
    parts=[]
    end=dt.datetime(2026,11,20)
    for i in range(5):
        s=end-dt.timedelta(days=7)
        try:
            df=yf.download(t,start=s.strftime('%Y-%m-%d'),end=end.strftime('%Y-%m-%d'),interval='1m',progress=False,prepost=True)
            if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
            print(t,s.date(),end.date(),len(df)); parts.append(df)
        except Exception as e: print(t,s,'ERR',e)
        end=s
    d=pd.concat(parts).sort_index(); d=d[~d.index.duplicated()]
    d.to_csv(out+t.replace('=','')+'_1m.csv'); print(t,len(d),d.index.min(),d.index.max())
