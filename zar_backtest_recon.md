# Zarillion NAS100: trade reconstruction against real price data (Oct 21 to Nov 19, 2026)

_Built 2026-11-19 by Grok Bot. Data: Yahoo Finance via yfinance. All times are US Eastern (ET) unless marked otherwise. Prices are **NQ=F front-month futures**, not the NAS100 CFD Zar trades. Levels are offset from the CFD by the futures basis, but point distances, timing and structure carry over._

## 1. Bottom line

* **Data:** I got complete 1-minute NQ, ES and YM bars for **Oct 21 to Nov 19**, which covers every posted trade. I also got 5m/30m bars from Sep 11, daily bars for 2 years, and ^NDX cash data at 1m/5m/30m/1d. Nothing posted is missing data.
* **The posted direction fits the tape.** In traded sessions, **50%** of all candidate entries in the posted direction (1m closes inside the session window with structural swing stops) reach the posted R target before the stop. Only **26%** do in the opposite direction. In no-trade sessions, even the better direction only reaches **~35-39%**. So on the sessions he traded, there really was a clean move in the stated direction, and the sessions he skipped were choppier.
* **Reconstruction confidence (22 posted trades):** **9 High, 7 Medium, 6 Low.** High means a fixed, pre-defined rule (Rule P below) reproduces the posted outcome, and the direction beats the opposite side. Medium means a Zar-consistent candidate exists but the fixed rule does not reproduce it, or the trade is the second one of the day. Low means only an ad-hoc candidate was found, or the price action does not single out the posted direction.
* **The Nov 3 loss reproduces cleanly.** Rule P buys the break of the **session high at 10:56 ET (28393)**, with a swing stop at 28324 (69 pts). It stops out at **11:22 ET** without ever reaching +1R. That matches the post's text, "ENTRY SESSION HIGH / NO JUICE".
* **Main caveat: this does not identify his actual entries.** On most days several entries would have won. The table shows one plausible, rule-consistent entry. It is a calibration aid, not his real fill.

## 2. Data obtained (`/workspace/zar_data/`)

| File | Content | Coverage |
|---|---|---|
| `NQF_1m.csv`, `ESF_1m.csv`, `YMF_1m.csv` | 1-minute futures incl. pre/post market | 2026-10-21 00:09 ET to 2026-11-19 20:07 ET (Yahoo caps 1m at the last 30 days) |
| `NQF_5m.csv`, `ESF_5m.csv`, `YMF_5m.csv` | 5-minute | 2026-09-11 to 2026-11-19 |
| `NQF_30m.csv`, `ESF_30m.csv`, `YMF_30m.csv` | 30-minute | 2026-09-11 to 2026-11-19 |
| `NQF_1d.csv`, `ESF_1d.csv`, `YMF_1d.csv` | daily (for 200 EMA, ATR14) | 2024-11-19 to 2026-11-19 |
| `NDX_*.csv` | ^NDX cash index 1m/5m/30m/1d (RTH only) | 1m from Nov 10; 5m/30m from Aug 27 |
| `recon_trades.csv`, `session_features.csv`, `notrade_sessions.csv` | outputs of this analysis | |
| `recon.py`/`reconlib.py`, `analysis.py`, `features.py`, `charts.py`, `fetch*.py` | reproducible scripts (run with `/workspace/tgenv/bin/python`) | |

Notes:
- **Post times in `zar_trades_raw.md` are Pacific (box clock).** The "09:42" Nov 19 win post is 12:42 ET, and the "10:05" Nov 3 loss post is 13:05 ET. The 02:42 London no-trade post is 05:42 ET, which fits London ending around 05:00 ET. I used these as upper bounds for when the trade had to be finished.
- **Daily candles use Globex days** (18:00 ET to 17:00 ET), the same as the CFD New York-close daily. The Nov 19 daily row from Yahoo looks incomplete/rolled, so I computed prior-day features from 5m data.
- **London is taken as 03:00 ET throughout,** per the strategy notes. Between Oct 26 and Oct 30, the UK had already left summer time but the US had not, so London cash actually opened at 04:00 ET. The Oct 27 London trade may be affected.

## 3. Method

For each posted trade (date, session, direction, R):
1. **Window:** London 03:00-05:00 ET, NY 09:30-11:30 ET (first ~2h). For "London #2 / stored kinetic energy" I used 04:30-08:00. A target may be hit up to 2.5h after the window, capped by the post time where known.
2. **Candidates:** every 1m close in the window is a possible entry. Stops sit beyond the extreme of the last 5/10/15/30 one-minute bars, plus a 2-pt buffer. Risk is limited to 10-150 NQ pts. Target = posted R (2R for the loss). The target counts only if price trades **through** it by a tick; if stop and target fall in the same bar, it counts as a loss (conservative, and his "line must be crossed" rule).
3. **Rule P (fixed, no look-ahead):** after the first 30m candle closes, take the first 1m close beyond the opening range (OR) in the posted direction. Stop goes beyond the 15-bar swing plus 2 pts; target is the posted R. This is the closest single codeable approximation of "wait for the first 30m, then trade out of the OR box with a structural stop".
4. **Selected candidate:** the earliest winning candidate (or losing one, for Nov 3), by tier.
   - **A:** after the first 30m, beyond the OR, stop at least a 15-bar swing, and risk at least 0.3 × OR size.
   - **B:** after the first 30m, beyond the OR, any swing stop.
   - **C:** after the first 30m, anywhere.
   - **D:** anything in the window.
5. **match% (dir / opp):** the share of all candidates that win in the posted direction versus the opposite direction. This shows how much the tape favoured the posted side.

Rule Z (30m signal-candle break, stop at the far end of the signal candle) was also tested. Using the whole 30m candle as the stop usually gives 150-770 pt risk, and the 2R target is then rarely reached in the session. That argues **against** stops at the signal-candle extreme. His stops are much tighter, around 0.1-0.15 × ATR (see section 6).

## 4. Per-trade reconstruction table

"target / stop-out" is the target price, or for the Nov 3 loss the level that would have been +2R. `exit ET` is when the target was hit (or, for Nov 3, the stop). Rule P is shown as entry time, price / stop -> outcome and time.

| date       | session   | dir   |    R | setup                                                                                      | entry ET   |   entry |    stop |   risk pts |   target / stop-out | exit ET   | tier                | ruleP                                |   match% (dir) |   match% (opp) | conf   |
|:-----------|:----------|:------|-----:|:-------------------------------------------------------------------------------------------|:-----------|--------:|--------:|-----------:|--------------------:|:----------|:--------------------|:-------------------------------------|---------------:|---------------:|:-------|
| 2026-11-19 | NY        | short |  2   | DAILY FADE / failed attempts higher / 30m topping tail                                     | 10:17      | 27533.2 | 27665.2 |      132   |             27269.2 | 10:31     | B                   | 10:47 27189/stop 27292 -> loss 11:02 |           0.32 |           0.34 | Low    |
| 2026-11-18 | NY        | short |  1   | V-reversal retest of open range                                                            | 10:00      | 27272.2 | 27327.5 |       55.2 |             27217   | 10:01     | C                   | no OR break in window                |           0.64 |           0.36 | Low    |
| 2026-11-18 | London2   | short |  2   | Stored kinetic energy / late session resumption                                            | 05:08      | 27396   | 27426.5 |       30.5 |             27335   | 06:09     | A                   | 07:36 27237/stop 27321 -> loss 08:41 |           0.62 |           0.09 | Medium |
| 2026-11-17 | NY        | short |  2   | Anabolic flow / 30m turbo zones / 30m double top resumption                                | 10:16      | 27158   | 27285.8 |      127.8 |             26902.5 | 10:41     | A                   | 10:16 27158/stop 27286 -> win 10:41  |           0.65 |           0.16 | High   |
| 2026-11-17 | London    | short |  2   | Anabolic flow / waited first 30m                                                           | 03:31      | 27272.5 | 27333.5 |       61   |             27150.5 | 04:04     | A                   | 03:31 27272/stop 27334 -> win 04:04  |           0.53 |           0.36 | High   |
| 2026-11-13 | NY        | short |  2   | Anabolic flow / daily tagging 200 EMA / premarket topping tail                             | 10:00      | 28062.5 | 28189.2 |      126.8 |             27809   | 10:14     | B                   | 10:26 27756/stop 27891 -> loss 12:06 |           0.36 |           0.13 | Medium |
| 2026-11-12 | NY        | long  |  1.5 | Zone break / turbo zone / naked body                                                       | 10:51      | 28406   | 28268   |      138   |             28613   | 11:10     | A                   | 10:51 28406/stop 28268 -> win 11:10  |           0.56 |           0.28 | High   |
| 2026-11-11 | NY        | long  |  2   | Anabolic flow / extension relieved / resumption                                            | 10:43      | 28441.5 | 28334.5 |      107   |             28655.5 | 12:23     | A                   | 10:43 28442/stop 28334 -> win 12:23  |           0.68 |           0.12 | High   |
| 2026-11-09 | NY        | long  |  1.5 | Anabolic flow / turbo zone / naked bodies                                                  | 10:10      | 27809.8 | 27686.8 |      123   |             27994.2 | 10:58     | B                   | 10:10 27810/stop 27687 -> win 10:58  |           0.5  |           0.26 | Medium |
| 2026-11-06 | London    | long  |  2   | Daily fade / extreme extension / rebound                                                   | 03:41      | 27057.5 | 26967   |       90.5 |             27238.5 | 04:31     | A                   | 03:41 27058/stop 26967 -> win 04:31  |           0.44 |           0.24 | High   |
| 2026-11-05 | NY        | short |  2   | Anabolic flow / turbo zone / double naked (NY #1)                                          | 10:08      | 27454.8 | 27523.8 |       69   |             27316.8 | 10:12     | B                   | 10:16 27388/stop 27535 -> win 10:27  |           0.56 |           0.19 | Medium |
| 2026-11-05 | NY        | short |  2   | Anabolic flow / freefall (NY #2)                                                           | 10:16      | 27388.2 | 27535.2 |      147   |             27094.2 | 10:27     | A (after NY#1 exit) | 10:16 27388/stop 27535 -> win 10:27  |           0.56 |           0.19 | Medium |
| 2026-11-03 | NY        | long  | -1   | Daily fade / zone break / entry session high / no juice (LOSS, posted 10:05 PT = 13:05 ET) | 10:56      | 28393   | 28324   |       69   |             28531   | 11:22     | A                   | 10:56 28393/stop 28324 -> loss 11:22 |           0.55 |           0.21 | High   |
| 2026-10-28 | NY        | short |  1   | Dynamically managed, FOMC day                                                              | 10:04      | 29872.2 | 29948.8 |       76.5 |             29795.8 | 10:11     | C                   | no OR break in window                |           0.38 |           0.53 | Low    |
| 2026-10-27 | NY        | long  |  2   | Anabolic flow / fake-fake-drive                                                            | 10:54      | 29691.5 | 29613   |       78.5 |             29848.5 | 12:00     | A                   | 10:54 29692/stop 29613 -> win 12:00  |           0.49 |           0.12 | High   |
| 2026-10-27 | London    | long  |  0.5 | Dynamically managed in twilight zone / zone reversal                                       | 04:02      | 29332.8 | 29292.8 |       40   |             29352.8 | 04:03     | A                   | 03:50 29335/stop 29307 -> loss 04:00 |           0.81 |           0.47 | Medium |
| 2026-10-26 | NY        | long  |  1.5 | Anabolic flow / zone break / TCON                                                          | 10:25      | 29338.8 | 29215   |      123.8 |             29524.4 | 10:57     | A                   | 10:25 29339/stop 29215 -> win 10:57  |           0.49 |           0.34 | High   |
| 2026-10-23 | NY        | long  |  1   | Dynamically managed near twilight zone                                                     | 10:31      | 29187.8 | 29073.5 |      114.2 |             29302   | 10:52     | A                   | 10:02 29180/stop 29084 -> loss 10:18 |           0.4  |           0.47 | Low    |
| 2026-10-23 | London    | long  |  1   | Dynamically managed near twilight zone                                                     | 04:10      | 29220.5 | 29175.8 |       44.8 |             29265.2 | 04:13     | B                   | 04:10 29220/stop 29161 -> loss 05:24 |           0.29 |           0.53 | Low    |
| 2026-10-22 | NY        | short |  2   | Anabolic flow / very bearish daily                                                         | 10:20      | 29433.2 | 29564.2 |      131   |             29171.2 | 12:48     | A                   | 10:20 29433/stop 29564 -> win 12:48  |           0.36 |           0.14 | High   |
| 2026-10-22 | London    | short |  2   | Anabolic flow / strong overnight selling                                                   | 03:31      | 29497   | 29519.8 |       22.8 |             29451.5 | 04:09     | C                   | 03:50 29467/stop 29521 -> loss 06:31 |           0.27 |           0.19 | Low    |
| 2026-10-21 | NY        | long  |  2   | Anabolic flow / long tug o war resolving                                                   | 10:49      | 29918.8 | 29827.8 |       91   |             30100.8 | 12:40     | A                   | 10:02 29925/stop 29823 -> loss 10:10 |           0.64 |           0.11 | Medium |

Comments on specific trades:
- **Nov 17 NY short (High):** Rule P sells the break below the OR at 10:16 (27158), with stop 27286. Target 26902 is hit at 10:41, about 25 minutes later, during a straight freefall. It fits "Anabolic flow / turbo zone" well. See chart.
- **Nov 12 NY long 1.5R (High):** the zone break above the OR (OR high 28398) triggers at 10:51 (28406). The 1.5R target 28613 is hit at 11:10.
- **Nov 6 London long, daily fade (High):** the day opened after a 2.5 × ATR prior day, about 6% below the 200 EMA (extreme extension). The OR-break long at 03:41 (27058, stop 26967) hits 2R at 04:31.
- **Nov 3 NY loss (High):** as described in section 1. The 28386 OR high was also the session high, and price had no follow-through ("no juice").
- **Nov 13 NY short (Medium):** the daily high of 28608 was above the 200 EMA (~28273), so the daily did tag it, confirming the "daily tagging 200 EMA" tag. The fixed OR-break rule entered too late (10:26) and stopped out. A short at the 10:00 OR-low break (28062, stop 28189) reaches 2R at 10:14.
- **Nov 5 NY #1 / #2 (Medium):** this was a freefall day with a 770-pt OR. #1 is 10:08 @27455 → 10:12. #2 is the Rule P entry at 10:16 @27388 → 10:27. Many entries would have won.
- **Nov 19 NY daily-fade short (Low):** price spiked to 27838 in the first 30m, then failed ("failed attempts higher"). Shorts after 10:00 work, but almost as many longs worked in the 2h window (match 0.32 vs 0.34). The 30m topping tail is visible in the first 30m candle (high 27838, closed back near 27680). A short from the 09:50-10:05 topping-tail area with a stop above 27840 is plausible but I couldn't pin it down.
- **Oct 28 FOMC (+1R), Oct 23 London/NY (+1R), Nov 18 NY (+1R) (Low):** these are "dynamically managed" or retest trades. Rule P does not reproduce them, and in several the opposite direction fit the tape as well or better. Treat these as unknown entries.
- **Oct 22 London short (Low):** only a small-stop candidate reached 2R (03:31 @27497, 23-pt stop). Selling was strong overnight but the session itself was slow.

## 5. Traded vs no-trade sessions: features

Feature definitions (all known at session open unless noted):
- `pd_range_atr`: prior-day range / ATR14.
- `prior_inside`: prior day was inside the day before it.
- `func_inside_at_open`: today's Globex range so far is fully inside the prior day's range.
- `day_body_pct`: (price − Globex open) / range so far, in %.
- `loc_vs_PDR`: price versus the prior-day high/low.
- `ovn_ext_atr`: (price − prior close) / ATR.
- `ema200_dist_pct`: prior close versus the daily 200 EMA, in %.
- `OR_atr`: first-30m range / ATR.
- `first30_dir`: direction of the first 30m candle.
- `sisters_aligned_first30`: NQ, ES and YM first-30m candles all point the same way.
- `sess2h_range_atr`, `sess2h_inside_PDR`: **after the fact.** The range of the first 2h, and whether the day was still inside the prior-day range after it.

Label counts: 20 traded sessions (Nov 18 London is excluded as ambiguous, since there was a London "no trade" and a later "London #2" win), 10 no-trade sessions, 13 sessions with no post found (unknown, excluded).

**Medians by session and label:**

|                        |   pd_range_atr |   day_body_pct |   ovn_ext_atr |   ema200_dist_pct |   OR_atr |   first30_body_pct |   sess2h_range_atr |
|:-----------------------|---------------:|---------------:|--------------:|------------------:|---------:|-------------------:|-------------------:|
| ('London', 'no_trade') |           0.93 |            -38 |         -0.12 |             -0.84 |     0.07 |                 26 |               0.13 |
| ('London', 'trade')    |           1.06 |             16 |          0.08 |              3.03 |     0.1  |                 18 |               0.25 |
| ('NY', 'no_trade')     |           1.52 |            -64 |         -0.36 |             -0.84 |     0.42 |                 58 |               0.47 |
| ('NY', 'trade')        |           0.94 |             -2 |          0.06 |              0.6  |     0.3  |                 20 |               0.67 |

**Flag frequencies (share of sessions):**

|                        |   prior_inside |   func_inside_at_open |   sess2h_inside_PDR |   sisters_aligned_sofar |   sisters_aligned_first30 |
|:-----------------------|---------------:|----------------------:|--------------------:|------------------------:|--------------------------:|
| ('London', 'no_trade') |           0.29 |                  0.57 |                0.57 |                    0.57 |                      0.86 |
| ('London', 'trade')    |           0    |                  0    |                0    |                    0.2  |                      0.6  |
| ('NY', 'no_trade')     |           0    |                  0.33 |                0.33 |                    0.67 |                      0.67 |
| ('NY', 'trade')        |           0.13 |                  0.27 |                0.07 |                    0.47 |                      0.33 |

**How easy were 2R trades on the no-trade sessions?** This is the share of candidates that win, for each side:

| date       | session   |   long_frac |   short_frac | long_ruleP   | short_ruleP   |
|:-----------|:----------|------------:|-------------:|:-------------|:--------------|
| 2026-11-19 | London    |        0.23 |         0.2  | loss         | loss          |
| 2026-11-18 | London    |        0.2  |         0.11 | loss         | no-break      |
| 2026-11-16 | London    |        0.13 |         0.41 | loss         | win           |
| 2026-11-16 | NY        |        0.27 |         0.3  | no-break     | loss          |
| 2026-11-13 | London    |        0.42 |         0.17 | open         | loss          |
| 2026-11-12 | London    |        0.34 |         0.25 | loss         | no-break      |
| 2026-11-11 | London    |        0.5  |         0.13 | loss         | no-break      |
| 2026-11-10 | London    |        0.2  |         0.23 | no-break     | open          |
| 2026-11-10 | NY        |        0.22 |         0.64 | loss         | no-break      |
| 2026-11-09 | London    |        0.63 |         0.11 | win          | no-break      |
| 2026-11-06 | NY        |        0.24 |         0.35 | no-break     | no-break      |

**All labelled sessions:**

| date       | dow   | session   | label     | dir   |   pd_range_atr | prior_inside   | func_inside_at_open   |   day_body_pct | loc_vs_PDR   |   ovn_ext_atr |   ema200_dist_pct |   OR_atr |   first30_dir | sisters_aligned_first30   |   sess2h_range_atr | sess2h_inside_PDR   |
|:-----------|:------|:----------|:----------|:------|---------------:|:---------------|:----------------------|---------------:|:-------------|--------------:|------------------:|---------:|--------------:|:--------------------------|-------------------:|:--------------------|
| 2026-11-18 | Wed   | London    | ambiguous | short |           0.83 | False          | False                 |              2 | inside_PDR   |          0.26 |             -3.98 |    0.14  |            -1 | False                     |               0.17 | False               |
| 2026-11-09 | Mon   | London    | no_trade  | nan   |           1.25 | False          | True                  |            -51 | inside_PDR   |         -0.32 |             -4.22 |    0.248 |             1 | True                      |               0.4  | True                |
| 2026-11-10 | Tue   | London    | no_trade  | nan   |           1.52 | False          | True                  |            -47 | inside_PDR   |         -0.12 |             -0.72 |    0.094 |             1 | True                      |               0.19 | True                |
| 2026-11-11 | Wed   | London    | no_trade  | nan   |           0.65 | True           | False                 |             80 | above_PDH    |          0.37 |             -1.31 |    0.07  |             1 | True                      |               0.11 | False               |
| 2026-11-12 | Thu   | London    | no_trade  | nan   |           0.93 | False          | True                  |            -38 | inside_PDR   |         -0.25 |              0.6  |    0.065 |            -1 | True                      |               0.13 | True                |
| 2026-11-13 | Fri   | London    | no_trade  | nan   |           0.69 | True           | True                  |            -18 | inside_PDR   |         -0.07 |              0.45 |    0.089 |            -1 | True                      |               0.13 | True                |
| 2026-11-16 | Mon   | London    | no_trade  | nan   |           0.95 | False          | False                 |            -63 | inside_PDR   |         -0.23 |             -0.84 |    0.064 |            -1 | True                      |               0.12 | False               |
| 2026-11-19 | Thu   | London    | no_trade  | nan   |           0.68 | False          | False                 |             92 | above_PDH    |          0.52 |             -3.77 |    0.07  |             1 | False                     |               0.11 | False               |
| 2026-10-22 | Thu   | London    | trade     | short |           0.73 | False          | False                 |            -90 | below_PDL    |         -0.92 |              6.36 |    0.151 |            -1 | True                      |               0.25 | False               |
| 2026-10-23 | Fri   | London    | trade     | long  |           1.71 | False          | False                 |             30 | inside_PDR   |          0.16 |              3.03 |    0.09  |            -1 | True                      |               0.22 | False               |
| 2026-10-27 | Tue   | London    | trade     | long  |           0.95 | False          | False                 |            -57 | inside_PDR   |         -0.25 |              4.28 |    0.076 |             1 | False                     |               0.25 | False               |
| 2026-11-06 | Fri   | London    | trade     | long  |           2.49 | False          | False                 |             43 | inside_PDR   |          0.46 |             -5.96 |    0.136 |             1 | True                      |               0.38 | False               |
| 2026-11-17 | Tue   | London    | trade     | short |           1.06 | False          | False                 |             16 | inside_PDR   |          0.08 |             -3.46 |    0.099 |            -1 | False                     |               0.29 | False               |
| 2026-11-06 | Fri   | NY        | no_trade  | nan   |           2.49 | False          | False                 |             60 | inside_PDR   |          0.69 |             -5.96 |    0.471 |             1 | True                      |               0.47 | False               |
| 2026-11-10 | Tue   | NY        | no_trade  | nan   |           1.52 | False          | True                  |            -64 | inside_PDR   |         -0.36 |             -0.72 |    0.419 |             1 | False                     |               0.5  | True                |
| 2026-11-16 | Mon   | NY        | no_trade  | nan   |           0.95 | False          | False                 |            -74 | below_PDL    |         -0.38 |             -0.84 |    0.241 |            -1 | True                      |               0.39 | False               |
| 2026-10-21 | Wed   | NY        | trade     | long  |           0.94 | False          | False                 |            -18 | inside_PDR   |         -0.04 |              5.96 |    0.27  |             1 | False                     |               0.4  | False               |
| 2026-10-22 | Thu   | NY        | trade     | short |           0.73 | False          | False                 |            -80 | below_PDL    |         -0.95 |              6.36 |    0.253 |             1 | True                      |               0.69 | False               |
| 2026-10-23 | Fri   | NY        | trade     | long  |           1.71 | False          | False                 |            -32 | below_PDL    |         -0.12 |              3.03 |    0.335 |             1 | False                     |               0.6  | False               |
| 2026-10-26 | Mon   | NY        | trade     | long  |           0.61 | False          | False                 |            -19 | inside_PDR   |          0.2  |              3.08 |    0.303 |            -1 | False                     |               0.73 | False               |
| 2026-10-27 | Tue   | NY        | trade     | long  |           0.95 | False          | False                 |             23 | inside_PDR   |          0.16 |              4.28 |    0.286 |             1 | False                     |               0.49 | False               |
| 2026-10-28 | Wed   | NY        | trade     | short |           1.01 | False          | False                 |             53 | above_PDH    |          0.21 |              5.41 |    0.315 |            -1 | False                     |               0.31 | False               |
| 2026-11-03 | Tue   | NY        | trade     | long  |           1.11 | False          | False                 |             17 | inside_PDR   |          0.06 |             -0.28 |    0.238 |             1 | False                     |               0.32 | False               |
| 2026-11-05 | Thu   | NY        | trade     | short |           1.83 | False          | True                  |            -91 | inside_PDR   |         -0.6  |              1.2  |    1.04  |            -1 | True                      |               2.02 | False               |
| 2026-11-09 | Mon   | NY        | trade     | long  |           1.25 | False          | True                  |             38 | inside_PDR   |          0.3  |             -4.22 |    0.57  |             1 | True                      |               0.83 | False               |
| 2026-11-11 | Wed   | NY        | trade     | long  |           0.65 | True           | False                 |             82 | above_PDH    |          0.49 |             -1.31 |    0.248 |            -1 | True                      |               0.41 | False               |
| 2026-11-12 | Thu   | NY        | trade     | long  |           0.93 | False          | True                  |            -68 | inside_PDR   |         -0.42 |              0.6  |    0.389 |             1 | False                     |               0.67 | True                |
| 2026-11-13 | Fri   | NY        | trade     | short |           0.69 | True           | True                  |             -2 | inside_PDR   |         -0.01 |              0.45 |    0.358 |            -1 | True                      |               0.76 | False               |
| 2026-11-17 | Tue   | NY        | trade     | short |           1.06 | False          | False                 |              7 | inside_PDR   |          0.05 |             -3.46 |    0.156 |            -1 | False                     |               0.7  | False               |
| 2026-11-18 | Wed   | NY        | trade     | short |           0.83 | False          | False                 |            -26 | inside_PDR   |          0.12 |             -3.98 |    0.361 |            -1 | False                     |               0.4  | False               |
| 2026-11-19 | Thu   | NY        | trade     | short |           0.68 | False          | False                 |             74 | above_PDH    |          0.49 |             -3.77 |    0.218 |             1 | False                     |               0.8  | False               |

### Thresholds found (small sample: 5 traded and 7 no-trade London sessions, 15 traded and 3 no-trade NY sessions)

1. **London: a functional inside day at 03:00 ET means no trade.** 4 of 7 London no-trade sessions were inside the prior-day range at the open (Nov 9, 10, 12, 13), against **0 of 5** traded London sessions. This split had 100% precision in-sample, and it matches his "TINY INSIDE DAY / FUNCTIONAL INSIDE DAY" posts.
2. **London: a sleepy session means no trade.** Every traded London session had a first-2h range of **≥ 0.22 × ATR14**. Every no-trade London session except Nov 9 (an inside day) was **≤ 0.19 × ATR**. This was the best single split, at 11/12 correct. It is only known in real time as the session unfolds, so code it as a progressive check, e.g. "the London range after 60-90 min is still < 0.15 × ATR, so stand down".
3. **London OR size:** traded 0.076-0.151 × ATR (median 0.10). No-trade was mostly 0.064-0.094 (median 0.07). A weak filter: **OR ≥ ~0.09 × ATR**.
4. **NY: an inside-day open does NOT block NY trades.** Nov 5, 9, 12 and 13 were inside at 09:30 and still traded, and won. In NY, the no-trade sessions were the ones **still inside the prior-day range after 2h** (Nov 10 "small inside day") or chop after a big down move (Nov 6 after the London fade, Nov 16 Monday). Only 3 no-trade NY sessions were found, so this is weak.
5. **Extreme extension means a fade, not continuation.** Nov 6 (prior-day range 2.49 × ATR, about −6% below the 200 EMA) was traded as a daily-fade rebound long in London, and NY was skipped. Nov 19 (opened above PDH, about −3.8% below the 200 EMA, a gap up into a falling market) was faded short. Candidate fade trigger: **prior-day range ≥ ~2 × ATR, or |200-EMA distance| ≥ ~4% together with a counter-trend opening move.** These are only 2 examples.
6. **Sister alignment did not separate the groups the way the strategy notes suggest.** First-30m NQ/ES/YM alignment was **80%** on no-trade sessions versus **40%** on traded sessions. With 1m sisters this crude, I would not code alignment as a hard filter. If you use it, apply it at the entry bar, not the first 30m candle.
7. **200 EMA:** not a filter by itself. The Nov 13 "daily tagging 200 EMA" short is confirmed, since the daily high crossed the ~28273 EMA. Use it as a context or target level.
8. **Day of week:** Monday London was a no-trade both times we have it (Nov 9, Nov 16), and NY Monday Nov 16 was also no-trade, though Oct 26 and Nov 9 NY did trade. Friday London: Nov 13 was no-trade, but Oct 23 and Nov 6 traded. This does not support a hard rule.

## 6. Suggested Pine defaults (calibrated on NQ, applied to NAS100 CFD)

| Parameter | Suggested default | Basis / confidence |
|---|---|---|
| Sessions | London 03:00-05:00 ET, NY 09:30-11:30 ET; "late London" re-open window 04:30-08:00 only after a dead morning | posted results; Medium |
| Wait for first 30m candle | true (entries ≥ open+30 min); allow early entries only when `anabolic` | entries are clustered 30-80 min after the open (median 41 min London, 52 min NY); High |
| Entry trigger | 1m close beyond the opening-range edge in the bias direction (Rule P), or break of session high/low | reproduces 12 of 22 posted outcomes, including the Nov 3 loss; Medium-High |
| Stop | beyond the 15-bar 1m swing + 2 pts, capped at the opposite OR edge | median risk ≈ **0.13 × ATR14** (NY ≈ 0.14, ~120 NQ pts; London ≈ 0.07, ~60 pts); ≈ 0.45 × OR in NY, ≈ 0.8 × OR in London; Medium |
| Max risk | 0.18 × ATR14 (skip if the stop needs more) | 75th percentile 0.156 × ATR; Medium |
| Target | 2R fixed; optional 1.5R / BE-at-1R modes | 2R reached within a median ~33 min of entry; High |
| Time stop | flat at 11:30 ET (NY) / 06:00 ET (London) unless the target is near | Twilight Zone rule; some 2R hits came at 12:00-12:48 (Oct 22, Oct 21, Nov 11), so a strict 11:30 cut would have turned them into partials; Medium |
| Inside-day filter (London) | skip London if Globex range at 03:00 is inside the prior-day range | 4/4 inside London opens were no-trade; High (in-sample) |
| Inside-day filter (NY) | do **not** block at 09:30; block if still inside PDR at 10:30 and OR < 0.25 × ATR | Medium-Low |
| Sleepy filter | stand down if session range after 60 min < 0.15 × ATR (London) / < 0.25 × ATR (NY) | Medium |
| Min OR size | London ≥ 0.08 × ATR; NY ≥ 0.15 × ATR | Low-Medium |
| Fade mode | enable `dailyFade` only if prior-day range ≥ 2.0 × ATR or |dist to 200 EMA| ≥ 4%, plus a 30m topping/bottoming tail | 2 samples; Low |
| Sister filter | off by default (or require only that ES confirms the entry bar direction) | data contradicts a first-30m alignment rule; Low |

## 7. Confidence and limitations

- **Not unique:** on most winning days, between 30% and 80% of candidate entries in the posted direction also win. The reconstruction shows that a plausible rule-based entry exists. It cannot show where he actually got in. Without post-time timestamps for the trades (only a few are known) or entry prices, this cannot be narrowed further.
- **Futures vs CFD:** NQ has a basis versus the cash index/CFD, so absolute levels differ by tens to ~200 points. Distances in points and ATR units carry over.
- **Small samples:** 20 traded and 10 no-trade sessions, with only 3 NY no-trade sessions. Treat every threshold as a starting point to optimise in TradingView, not as a fitted rule.
- **The search caps risk at 150 NQ pts and floors it at 10 pts.** That bounds the risk statistics above.
- **The raw log may have gaps:** sessions with no post found (e.g. Oct 29-30, Nov 2, 4, and many London sessions in October) are excluded rather than assumed to be no-trade.
- **Zone, turbo-zone and naked-body logic was not modelled** (it needs the 30m zone map). Including it should improve on the plain OR-break Rule P, especially for the Low-confidence retest and dynamically-managed trades.

## 8. Charts (2-minute NQ, ET, reconstructed levels marked)

- `/workspace/zar_data/chart_2026-11-17_NY_short.png`: Anabolic-flow short, High
- `/workspace/zar_data/chart_2026-11-12_NY_long.png`: zone-break long 1.5R, High
- `/workspace/zar_data/chart_2026-11-03_NY_long.png`: the −1R session-high long that stopped out, High
- `/workspace/zar_data/chart_2026-11-06_London_long.png`: daily-fade rebound long, High
