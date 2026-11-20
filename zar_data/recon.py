import pandas as pd, numpy as np, json
TZ='America/New_York'
def load(f):
    d=pd.read_csv(f,index_col=0); d.index=pd.to_datetime(d.index,utc=True).tz_convert(TZ)
    return d[['Open','High','Low','Close']].astype(float).dropna()
m1={s:load(f'{s}_1m.csv') for s in ['NQF','ESF','YMF']}
m5={s:load(f'{s}_5m.csv') for s in ['NQF','ESF','YMF']}
dly=pd.read_csv('NQF_1d.csv',index_col=0,parse_dates=True)[['Open','High','Low','Close']]
dly['ema200']=dly.Close.ewm(span=200,adjust=False).mean()
dly['atr14']=(pd.concat([dly.High-dly.Low,(dly.High-dly.Close.shift()).abs(),(dly.Low-dly.Close.shift()).abs()],axis=1).max(axis=1)).rolling(14).mean()

# Globex day: 18:00 prev -> 17:00
def gday(idx):
    t=idx.tz_convert(TZ); d=pd.Series(t.date,index=idx)
    nxt=(t.hour>=18)
    d[nxt]=(t[nxt]+pd.Timedelta(days=1)).date
    return pd.to_datetime(d.values)
def daily_from5(df):
    g=df.copy(); g['gd']=gday(g.index)
    o=g.groupby('gd').agg(Open=('Open','first'),High=('High','max'),Low=('Low','min'),Close=('Close','last'))
    o=o[o.index.day_of_week<5]; return o
D5={s:daily_from5(m5[s]) for s in m5}

SESS={'London':('03:00',120),'NY':('09:30',120),'London2':('03:00',300)}
trades=[ # date, session, dir, R, setup tags
('2026-11-19','NY','short',2.0,'DAILY FADE / failed attempts higher / 30m topping tail'),
('2026-11-18','NY','short',1.0,'V-reversal retest of open range'),
('2026-11-18','London2','short',2.0,'Stored kinetic energy / late session resumption'),
('2026-11-17','NY','short',2.0,'Anabolic flow / 30m turbo zones / 30m double top resumption'),
('2026-11-17','London','short',2.0,'Anabolic flow / waited first 30m'),
('2026-11-13','NY','short',2.0,'Anabolic flow / daily tagging 200 EMA / premarket topping tail'),
('2026-11-12','NY','long',1.5,'Zone break / turbo zone / naked body'),
('2026-11-11','NY','long',2.0,'Anabolic flow / extension relieved / resumption'),
('2026-11-09','NY','long',1.5,'Anabolic flow / turbo zone / naked bodies'),
('2026-11-06','London','long',2.0,'Daily fade / extreme extension / rebound'),
('2026-11-05','NY','short',2.0,'Anabolic flow / turbo zone / double naked (NY #1)'),
('2026-11-05','NY','short',2.0,'Anabolic flow / freefall (NY #2)'),
('2026-11-03','NY','long',-1.0,'Daily fade / zone break / entry session high / no juice (LOSS, posted 10:05 PT = 13:05 ET)'),
('2026-10-28','NY','short',1.0,'Dynamically managed, FOMC day'),
('2026-10-27','NY','long',2.0,'Anabolic flow / fake-fake-drive'),
('2026-10-27','London','long',0.5,'Dynamically managed in twilight zone / zone reversal'),
('2026-10-26','NY','long',1.5,'Anabolic flow / zone break / TCON'),
('2026-10-23','NY','long',1.0,'Dynamically managed near twilight zone'),
('2026-10-23','London','long',1.0,'Dynamically managed near twilight zone'),
('2026-10-22','NY','short',2.0,'Anabolic flow / very bearish daily'),
('2026-10-22','London','short',2.0,'Anabolic flow / strong overnight selling'),
('2026-10-21','NY','long',2.0,'Anabolic flow / long tug o war resolving'),
]
notrade=[('2026-11-19','London'),('2026-11-18','London'),('2026-11-16','London'),('2026-11-16','NY'),('2026-11-13','London'),
('2026-11-12','London'),('2026-11-11','London'),('2026-11-10','London'),('2026-11-10','NY'),('2026-11-09','London'),('2026-11-06','NY')]

BUF=2.0; TICK=0.25
def sim(bars,i,side,entry,stop,R,horizon_end):
    """bars after index i; returns ('win'|'loss'|'open', time). conservative: same-bar both -> loss"""
    risk=abs(entry-stop); tgt=entry+R*risk if side=='long' else entry-R*risk
    fut=bars.iloc[i+1:]; fut=fut[fut.index<=horizon_end]
    for t,b in fut.iterrows():
        hs = b.Low<=stop if side=='long' else b.High>=stop
        ht = b.High>=tgt+TICK if side=='long' else b.Low<=tgt-TICK
        if hs: return 'loss',t,tgt
        if ht: return 'win',t,tgt
    return 'open',None,tgt

def session(day,sess):
    st,mins=SESS[sess]; start=pd.Timestamp(f'{day} {st}',tz=TZ)
    if sess=='London2': start=start+pd.Timedelta(hours=1,minutes=30)  # late-London window 04:30-08:00
    return start, start+pd.Timedelta(minutes=mins if sess!='London2' else 210)

def recon(day,sess,side,R):
    b=m1['NQF']; s0,s1=session(day,sess)
    orst=pd.Timestamp(f'{day} {SESS[sess][0]}',tz=TZ)
    OR=b[(b.index>=orst)&(b.index<orst+pd.Timedelta(minutes=30))]
    orh,orl=OR.High.max(),OR.Low.min()
    W=b[(b.index>=s0-pd.Timedelta(minutes=60))&(b.index<=s1+pd.Timedelta(hours=3))]
    horizon=s1+pd.Timedelta(hours=2,minutes=30)  # allow target to be hit up to ~2.5h after window
    Rt=abs(R) if R>0 else 2.0
    cands=[]
    idx=list(W.index)
    for i,t in enumerate(idx):
        if t<s0 or t>s1: continue
        bar=W.iloc[i]
        for k in (5,10,15,30):
            if i-k<0: continue
            lb=W.iloc[i-k:i+1]
            if side=='long':
                entry=bar.Close; stop=lb.Low.min()-BUF
            else:
                entry=bar.Close; stop=lb.High.max()+BUF
            risk=abs(entry-stop)
            if risk<10 or risk>150: continue
            res,ht,tgt=sim(W,i,side,entry,stop,Rt,horizon)
            cands.append(dict(t=t,k=k,entry=entry,stop=stop,risk=risk,tgt=tgt,res=res,hit=ht,
                post30=t>=orst+pd.Timedelta(minutes=30),
                outsideOR=(entry>orh) if side=='long' else (entry<orl)))
    C=pd.DataFrame(cands)
    # Rule P: first 1m close beyond OR after first 30m, stop = 15-bar swing
    P=None
    if len(C):
        q=C[(C.post30)&(C.outsideOR)&(C.k==15)]
        if len(q): P=q.iloc[0].to_dict()
    # Rule Z: 30m signal-candle break (on 30m bars resampled from 1m)
    b30=W.resample('30min',origin='start_day').agg({'Open':'first','High':'max','Low':'min','Close':'last'}).dropna()
    Z=None
    for j in range(1,len(b30)):
        t=b30.index[j]
        if t<orst or t+pd.Timedelta(minutes=30)>s1: continue
        c=b30.iloc[j]; p=b30.iloc[j-1]
        sig = (c.Close>p.High and c.Close>c.Open) if side=='long' else (c.Close<p.Low and c.Close<c.Open)
        if not sig: continue
        lvl=c.High+TICK if side=='long' else c.Low-TICK
        stop=c.Low-BUF if side=='long' else c.High+BUF
        after=W[(W.index>=t+pd.Timedelta(minutes=30))&(W.index<=s1+pd.Timedelta(minutes=30))]
        trig=after[after.High>=lvl] if side=='long' else after[after.Low<=lvl]
        if not len(trig): continue
        tt=trig.index[0]; i=list(W.index).index(tt)
        risk=abs(lvl-stop)
        # simulate from the trigger bar itself (stop in same bar => loss conservative)
        res,ht,tgt=sim(W,i-1,side,lvl,stop,Rt,horizon) if risk>0 else ('n/a',None,None)
        Z=dict(signal=t,t=tt,entry=lvl,stop=stop,risk=risk,tgt=tgt,res=res,hit=ht); break
    return C,P,Z,orh,orl

if __name__=='__main__':
    rows=[]; allC={}
  for (day,sess,side,R,tag) in trades:
      C,P,Z,orh,orl=recon(day,sess,side,R)
      want='loss' if R<0 else 'win'
      n=len(C); nw=(C.res==want).sum() if n else 0
      # best search candidate: zar-consistent first (post30 & outsideOR), else earliest match
      best=None; tier=None
      if n:
          for tiername,mask in [('A: after 1st 30m, outside OR, swing-15 stop',(C.post30)&(C.outsideOR)&(C.k==15)),
                                ('B: after 1st 30m, outside OR, any swing stop',(C.post30)&(C.outsideOR)),
                                ('C: after 1st 30m, any',(C.post30)),('D: any in window',C.res.notna())]:
              q=C[mask&(C.res==want)]
              if len(q): best=q.iloc[0].to_dict(); tier=tiername; break
      rows.append(dict(day=day,sess=sess,side=side,R=R,tag=tag,orh=orh,orl=orl,ncand=n,frac=nw/n if n else np.nan,best=best,tier=tier,P=P,Z=Z))
      allC[(day,sess,side,R)]=C

  def fmt(t): return '' if t is None or (isinstance(t,float) and np.isnan(t)) else pd.Timestamp(t).strftime('%H:%M')
  out=[]
  for r in rows:
      b=r['best'];P=r['P'];Z=r['Z']
      out.append(dict(date=r['day'],session=r['sess'],dir=r['side'],posted_R=r['R'],
        OR=f"{r['orl']:.0f}-{r['orh']:.0f}",cand=r['ncand'],match_frac=round(r['frac'],2),
        best_tier=r['tier'] or 'none',
        best_entry=(f"{fmt(b['t'])} @{b['entry']:.2f}" if b else ''),best_stop=(f"{b['stop']:.2f}" if b else ''),
        best_risk=(round(b['risk'],1) if b else ''),best_tgt=(f"{b['tgt']:.2f}" if b else ''),best_hit=(fmt(b['hit']) if b else ''),
        P=(f"{fmt(P['t'])} @{P['entry']:.0f} stop {P['stop']:.0f} -> {P['res']} {fmt(P['hit'])}" if P else 'no OR break'),
        Z=(f"sig {fmt(Z['signal'])} trig {fmt(Z['t'])} @{Z['entry']:.0f} stop {Z['stop']:.0f} risk {Z['risk']:.0f} -> {Z['res']} {fmt(Z['hit'])}" if Z else 'no signal')))
  T=pd.DataFrame(out); T.to_csv('recon_trades.csv',index=False)
  pd.set_option('display.width',300); pd.set_option('display.max_colwidth',80)
  print(T.to_string())
  import pickle; pickle.dump(rows,open('recon_rows.pkl','wb'))
