import os,sys; os.chdir('/workspace/zar_data'); sys.path.insert(0,'.')
from reconlib import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
T=pd.read_csv('recon_trades.csv')
ex=[('2026-11-17','NY','short'),('2026-11-12','NY','long'),('2026-11-03','NY','long'),('2026-11-06','London','long')]
b=m1['NQF']
for day,sess,side in ex:
    r=T[(T.date==day)&(T.session==sess)&(T.dir==side)].iloc[0]
    st=SESS[sess][0]; s0=pd.Timestamp(f'{day} {st}',tz=TZ)
    et=pd.Timestamp(f"{day} {r.exit_time}",tz=TZ)
    a=s0-pd.Timedelta(minutes=45); z=max(et,s0+pd.Timedelta(hours=2))+pd.Timedelta(minutes=30)
    x=b[(b.index>=a)&(b.index<=z)].resample('2min').agg({'Open':'first','High':'max','Low':'min','Close':'last'}).dropna()
    fig,ax=plt.subplots(figsize=(14,7)); w=1.4/1440
    for t,c in x.iterrows():
        col='#26a69a' if c.Close>=c.Open else '#ef5350'; tn=matplotlib.dates.date2num(t.tz_localize(None))
        ax.plot([tn,tn],[c.Low,c.High],color=col,lw=0.8)
        ax.add_patch(Rectangle((tn-w/2,min(c.Open,c.Close)),w,max(abs(c.Close-c.Open),0.5),color=col))
    n=lambda t: matplotlib.dates.date2num(pd.Timestamp(t).tz_localize(None) if pd.Timestamp(t).tzinfo is None else pd.Timestamp(t).tz_convert(TZ).tz_localize(None))
    ax.add_patch(Rectangle((n(s0),r.OR_low),30/1440,r.OR_high-r.OR_low,color='gold',alpha=0.18,label='first-30m open range'))
    en=pd.Timestamp(f"{day} {r.entry_time}",tz=TZ)
    for y,c,l in [(r.entry,'blue','entry'),(r.stop,'red','stop'),(r.target,'green',f'target ({abs(r.R) if r.R>0 else 2}R)')]:
        ax.hlines(y,n(en),n(et)+10/1440,colors=c,linestyles='--',lw=1.5,label=f'{l} {y:.2f}')
    ax.plot(n(en),r.entry,marker='^' if side=='long' else 'v',color='blue',ms=12)
    ax.plot(n(et),r.stop if r.R<0 else r.target,marker='X',color='black',ms=10)
    ax.axvline(n(s0),color='gray',lw=0.8); 
    ax.xaxis_date(); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M'))
    ax.set_title(f"NQ=F 2m (ET) {day} {sess} {side.upper()}  posted {r.R:+.1f}R | {r.setup}\nReconstructed (not confirmed): entry {r.entry_time} @{r.entry:.2f}, stop {r.stop:.2f} ({r.risk_pts:.0f} pts), exit {r.exit_time} | confidence {r.conf}",fontsize=10)
    ax.legend(loc='best',fontsize=8); ax.grid(alpha=0.2)
    f=f'chart_{day}_{sess}_{side}.png'; fig.tight_layout(); fig.savefig(f,dpi=110); plt.close(fig); print(f)
