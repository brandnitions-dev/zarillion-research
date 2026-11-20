import yfinance as yf, pandas as pd
out='/workspace/zar_data/'
jobs=[]
for t in ['NQ=F','ES=F','YM=F','^NDX']:
    for iv,per in [('5m','60d'),('30m','60d'),('1d','2y'),('1m','8d')]:
        jobs.append((t,iv,per))
for t,iv,per in jobs:
    try:
        df=yf.download(t,period=per,interval=iv,progress=False,auto_adjust=False,prepost=True)
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        name=t.replace('=','').replace('^','')
        df.to_csv(f'{out}{name}_{iv}.csv')
        print(t,iv,len(df),df.index.min() if len(df) else None,df.index.max() if len(df) else None)
    except Exception as e: print(t,iv,'ERR',e)
