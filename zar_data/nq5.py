import os,sys; os.chdir('/workspace/zar_data'); sys.path.insert(0,'.')
from analysis import cands, fm
import pandas as pd
C,orh,orl,W=cands('2026-11-05','NY','short',2.0)
first_exit=pd.Timestamp('2026-11-05 10:12',tz='America/New_York')
q=C[(C.t>first_exit)&(C.res=='win')&(C.k>=15)&(C.risk>=0.3*(orh-orl)*0+15)]
print(q.head(8).to_string())
q2=C[(C.t>pd.Timestamp('2026-11-05 10:27',tz='America/New_York'))&(C.res=='win')&(C.k>=15)]
print(q2.head(5).to_string()); print(len(C[C.t>first_exit]), (C[C.t>first_exit].res=='win').mean())
