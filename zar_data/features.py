import os,sys; os.chdir('/workspace/zar_data'); sys.path.insert(0,'.')
from reconlib import *
import warnings; warnings.filterwarnings('ignore')
days=pd.bdate_range('2026-10-21','2026-11-19')
traded={(d,s if s!='London2' else 'London') for d,s,_,_,_ in trades}
traded_dir={}
for d,s,side,R,_ in trades: traded_dir[(d,'London' if s=='London2' else s)]=side
ntset=set(notrade)
dl=dly.copy(); dl.index=pd.to_datetime(dl.index)
def snap(sym,day,T):
    g=m5[sym]; dayts=pd.Timestamp(day)
    gs=pd.Timestamp(f'{day} 18:00',tz=TZ)-pd.Timedelta(days=1)
    if dayts.day_of_week==0: gs=gs-pd.Timedelta(days=2)
    x=g[(g.index>=gs)&(g.index<T)]
    if not len(x): return None
    return dict(o=x.Open.iloc[0],h=x.High.max(),l=x.Low.min(),p=x.Close.iloc[-1])
F=[]
for d in days:
    day=d.strftime('%Y-%m-%d')
    if d not in D5['NQF'].index: continue
    prevs=D5['NQF'].index[D5['NQF'].index<d]
    if len(prevs)<2: continue
    p1,p2=D5['NQF'].loc[prevs[-1]],D5['NQF'].loc[prevs[-2]]
    dprev=dl[dl.index<d]
    if not len(dprev): continue
    atr=dprev.atr14.iloc[-1]; ema=dprev.ema200.iloc[-1]
    for sess,st in [('London','03:00'),('NY','09:30')]:
        T=pd.Timestamp(f'{day} {st}',tz=TZ)
        s={k:snap(k,day,T) for k in ['NQF','ESF','YMF']}
        if s['NQF'] is None: continue
        n=s['NQF']
        b=m5['NQF']; OR=b[(b.index>=T)&(b.index<T+pd.Timedelta(minutes=30))]
        S2=b[(b.index>=T)&(b.index<T+pd.Timedelta(hours=2))]
        if not len(OR): continue
        orr=OR.High.max()-OR.Low.min(); orb=(OR.Close.iloc[-1]-OR.Open.iloc[0])
        sis=[np.sign(s[k]['p']-s[k]['o']) for k in s if s[k]]
        sisOR=[]
        for k in ['NQF','ESF','YMF']:
            o=m5[k][(m5[k].index>=T)&(m5[k].index<T+pd.Timedelta(minutes=30))]
            if len(o): sisOR.append(np.sign(o.Close.iloc[-1]-o.Open.iloc[0]))
        rng=n['h']-n['l']
        lab='ambiguous' if (day,sess)==('2026-11-18','London') else 'trade' if (day,sess) in traded else ('no_trade' if (day,sess) in ntset else 'unknown')
        loc='above_PDH' if n['p']>p1.High else ('below_PDL' if n['p']<p1.Low else 'inside_PDR')
        F.append(dict(date=day,dow=d.day_name()[:3],session=sess,label=lab,dir=traded_dir.get((day,sess),''),
          pd_range_atr=round((p1.High-p1.Low)/atr,2),prior_inside=bool(p1.High<=p2.High and p1.Low>=p2.Low),
          func_inside_at_open=bool(n['h']<=p1.High and n['l']>=p1.Low),
          day_range_sofar_atr=round(rng/atr,2),
          day_body_pct=round((n['p']-n['o'])/rng*100 if rng else 0,0),
          loc_vs_PDR=loc, pos_in_PDR=round((n['p']-p1.Low)/(p1.High-p1.Low),2),
          ovn_ext_atr=round((n['p']-p1.Close)/atr,2),
          ema200_dist_pct=round((p1.Close-ema)/ema*100,2),
          OR_atr=round(orr/atr,3),OR_pts=round(orr,1),first30_dir=int(np.sign(orb)),first30_body_pct=round(abs(orb)/orr*100 if orr else 0,0),
          sisters_aligned_sofar=bool(len(set(sis))==1 and len(sis)==3),sisters_aligned_first30=bool(len(set(sisOR))==1 and len(sisOR)==3),
          sess2h_range_atr=round((S2.High.max()-S2.Low.min())/atr,2),
          sess2h_inside_PDR=bool(max(S2.High.max(),n['h'])<=p1.High and min(S2.Low.min(),n['l'])>=p1.Low),
          atr14=round(atr,1)))
X=pd.DataFrame(F); X.to_csv('session_features.csv',index=False)
pd.set_option('display.width',320)

num=['pd_range_atr','day_range_sofar_atr','day_body_pct','pos_in_PDR','ovn_ext_atr','ema200_dist_pct','OR_atr','first30_body_pct','sess2h_range_atr']
X['abs_body']=X.day_body_pct.abs(); X['abs_ovn']=X.ovn_ext_atr.abs()
for sess in ['London','NY','all']:
    Y=X if sess=='all' else X[X.session==sess]
    g=Y.groupby('label')
    print('\n==',sess); print(g[num+['abs_body','abs_ovn']].median().round(2).T.to_string())
    print(g[['prior_inside','func_inside_at_open','sisters_aligned_sofar','sisters_aligned_first30','sess2h_inside_PDR']].mean().round(2).T.to_string())
    print(pd.crosstab(Y.label,Y.loc_vs_PDR))
    print(g.size())

# threshold scan: single-feature splits, trade vs no_trade, per session
K=X[X.label.isin(['trade','no_trade'])].copy(); K['y']=(K.label=='trade').astype(int)
for sess in ['London','NY','all']:
    Y=K if sess=='all' else K[K.session==sess]
    res=[]
    for f in num+['abs_body','abs_ovn']:
        for thr in sorted(Y[f].unique()):
            for sgn in ['>=','<']:
                pred=(Y[f]>=thr) if sgn=='>=' else (Y[f]<thr)
                acc=(pred==Y.y.astype(bool)).mean(); tp=(pred&(Y.y==1)).sum(); fp=(pred&(Y.y==0)).sum()
                res.append((round(acc,2),f,sgn,thr,tp,fp))
    for b in ['prior_inside','func_inside_at_open','sess2h_inside_PDR','sisters_aligned_first30','sisters_aligned_sofar']:
        for v in [True,False]:
            pred=(Y[b]!=v); acc=(pred==Y.y.astype(bool)).mean()
            res.append((round(acc,2),b,'!=',v,(pred&(Y.y==1)).sum(),(pred&(Y.y==0)).sum()))
    res.sort(reverse=True); print('\n### scan',sess,'n_trade',Y.y.sum(),'n_no',(1-Y.y).sum())
    for r in res[:12]: print(r)
cols=['date','dow','session','label','dir','pd_range_atr','prior_inside','func_inside_at_open','day_body_pct','loc_vs_PDR','ovn_ext_atr','ema200_dist_pct','OR_atr','first30_dir','sisters_aligned_first30','sess2h_range_atr','sess2h_inside_PDR']
print(X[X.label!='unknown'][cols].sort_values(['session','label']).to_string())
