import os,sys; os.chdir('/workspace/zar_data'); sys.path.insert(0,'.')
from reconlib import *
import warnings; warnings.filterwarnings('ignore')
POSTCAP={('2026-11-19','NY'):'12:42',('2026-11-03','NY'):'13:05'}  # Telegram post times shown in PT (box clock) -> ET
def cands(day,sess,side,R,cap=None):
    b=m1['NQF']; s0,s1=session(day,sess)
    orst=pd.Timestamp(f'{day} {SESS[sess][0]}',tz=TZ)
    OR=b[(b.index>=orst)&(b.index<orst+pd.Timedelta(minutes=30))]; orh,orl=OR.High.max(),OR.Low.min()
    W=b[(b.index>=s0-pd.Timedelta(minutes=60))&(b.index<=s1+pd.Timedelta(hours=3))]
    horizon=s1+pd.Timedelta(hours=2,minutes=30)
    if cap: horizon=min(horizon,pd.Timestamp(f'{day} {cap}',tz=TZ))
    Rt=abs(R) if R>0 else 2.0; out=[]
    for i,t in enumerate(W.index):
        if t<s0 or t>s1: continue
        bar=W.iloc[i]
        for k in (5,10,15,30):
            if i-k<0: continue
            lb=W.iloc[i-k:i+1]
            entry=bar.Close; stop=lb.Low.min()-BUF if side=='long' else lb.High.max()+BUF
            risk=abs(entry-stop)
            if risk<10 or risk>150: continue
            res,ht,tgt=sim(W,i,side,entry,stop,Rt,horizon)
            out.append(dict(t=t,k=k,entry=entry,stop=stop,risk=risk,tgt=tgt,res=res,hit=ht,
              post30=t>=orst+pd.Timedelta(minutes=30),outsideOR=(entry>orh) if side=='long' else (entry<orl)))
    return pd.DataFrame(out),orh,orl,W
def fm(t): return '' if t is None or pd.isna(t) else pd.Timestamp(t).strftime('%H:%M')
rows=[]; best_store={}
for (day,sess,side,R,tag) in trades:
    cap=POSTCAP.get((day,sess))
    C,orh,orl,W=cands(day,sess,side,R,cap)
    opp='short' if side=='long' else 'long'
    Co,_,_,_=cands(day,sess,opp,abs(R) if R>0 else 2.0,cap)
    want='loss' if R<0 else 'win'
    frac=(C.res==want).mean(); ofrac=(Co.res=='win').mean()
    floor=max(15,0.3*(orh-orl))
    best=None;tier='none'
    tiers=[('A',(C.post30)&(C.outsideOR)&(C.k>=15)&(C.risk>=floor)),('B',(C.post30)&(C.outsideOR)),('C',C.post30),('D',C.k>0)]
    if sess=='London2': tiers=[('A',(C.k>=15)&(C.risk>=15)),('D',C.k>0)]
    for nm,mk in tiers:
        q=C[mk&(C.res==want)]
        if len(q): best=q.iloc[0];tier=nm;break
    # deterministic Rule P (OR break after 1st 30m, 15-bar swing stop)
    q=C[(C.post30)&(C.outsideOR)&(C.k==15)]; P=q.iloc[0] if len(q) else None
    Pres = P.res if P is not None else 'no-break'
    pmatch = (Pres==want)
    if R>0 and R<2 and P is not None and Pres!='win':
        pass
    if tier=='A' and pmatch and frac>ofrac: conf='High'
    elif tier in('A','B') and (pmatch or frac>ofrac): conf='Medium'
    else: conf='Low'
    rows.append(dict(date=day,session=sess,dir=side,R=R,setup=tag,OR_low=round(orl,2),OR_high=round(orh,2),
       entry_time=fm(best.t) if best is not None else '',entry=round(best.entry,2) if best is not None else None,
       stop=round(best.stop,2) if best is not None else None,risk_pts=round(best.risk,1) if best is not None else None,
       target=round(best.tgt,2) if best is not None else None,exit_time=fm(best.hit) if best is not None else '',tier=tier,
       ruleP=(f"{fm(P.t)} {P.entry:.0f}/stop {P.stop:.0f} -> {P.res} {fm(P.hit)}" if P is not None else 'no OR break in window'),
       ruleP_match=pmatch,dir_match_frac=round(frac,2),opp_dir_frac=round(ofrac,2),conf=conf))
    best_store[(day,sess,side,R)]=dict(best=None if best is None else best.to_dict(),orh=orh,orl=orl)
T=pd.DataFrame(rows); T.to_csv('recon_trades.csv',index=False)
pd.set_option('display.width',320); pd.set_option('display.max_colwidth',60)
print(T.drop(columns=['setup']).to_string())
print(T.conf.value_counts())
import pickle; pickle.dump(best_store,open('best.pkl','wb'))
# no-trade sessions: how easy were 2R trades in either direction?
nt=[]
for day,sess in notrade:
    a,_,_,_=cands(day,sess,'long',2.0); b,_,_,_=cands(day,sess,'short',2.0)
    nt.append(dict(date=day,session=sess,long_frac=round((a.res=='win').mean(),2),short_frac=round((b.res=='win').mean(),2),
      long_ruleP=(lambda q: q.iloc[0].res if len(q) else 'no-break')(a[(a.post30)&(a.outsideOR)&(a.k==15)]),
      short_ruleP=(lambda q: q.iloc[0].res if len(q) else 'no-break')(b[(b.post30)&(b.outsideOR)&(b.k==15)])))
NT=pd.DataFrame(nt); NT.to_csv('notrade_sessions.csv',index=False); print(NT.to_string())
