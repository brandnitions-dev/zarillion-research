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

{TRADES}

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

{MED}

**Flag frequencies (share of sessions):**

{FRAC}

**How easy were 2R trades on the no-trade sessions?** This is the share of candidates that win, for each side:

{NOTRADE}

**All labelled sessions:**

{FEATS}

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
