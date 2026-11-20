import pandas as pd
T=pd.read_csv('recon_trades.csv'); X=pd.read_csv('session_features.csv'); N=pd.read_csv('notrade_sessions.csv')
T['R']=T.R.map(lambda r:f"{r:+.1f}")
tt=T[['date','session','dir','R','setup','entry_time','entry','stop','risk_pts','target','exit_time','tier','ruleP','dir_match_frac','opp_dir_frac','conf']].rename(columns={'entry_time':'entry ET','exit_time':'exit ET','risk_pts':'risk pts','dir_match_frac':'match% (dir)','opp_dir_frac':'match% (opp)','target':'target / stop-out'}).to_markdown(index=False)
cols=['date','dow','session','label','dir','pd_range_atr','prior_inside','func_inside_at_open','day_body_pct','loc_vs_PDR','ovn_ext_atr','ema200_dist_pct','OR_atr','first30_dir','sisters_aligned_first30','sess2h_range_atr','sess2h_inside_PDR']
ft=X[X.label!='unknown'][cols].sort_values(['session','label','date']).to_markdown(index=False)
nt=N.to_markdown(index=False)
num=['pd_range_atr','day_body_pct','ovn_ext_atr','ema200_dist_pct','OR_atr','first30_body_pct','sess2h_range_atr']
K=X[X.label.isin(['trade','no_trade'])]
med=K.groupby(['session','label'])[num].median().round(2).to_markdown()
fr=K.groupby(['session','label'])[['prior_inside','func_inside_at_open','sess2h_inside_PDR','sisters_aligned_sofar','sisters_aligned_first30']].mean().round(2).to_markdown()
md=open('report_template.md').read().format(TRADES=tt,FEATS=ft,NOTRADE=nt,MED=med,FRAC=fr)
open('/workspace/zar_backtest_recon.md','w').write(md); print(len(md))
