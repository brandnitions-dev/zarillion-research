# Razar's Edge — Technical Spec for Pine Script v6

**Status:** Implementation spec for a later TradingView Pine Script v6 build. Not a finished script.  
**Compiled:** 19 Nov 2026, America/Los_Angeles.  
**Builds on:** `/workspace/zar_strategy.md`, `/workspace/zar_trades_raw.md`, public YouTube auto-captions, X posts, Buy Me a Coffee articles.  
**Quote policy:** Quotes are from public sources (YouTube auto-captions lightly cleaned for obvious ASR errors such as “T con” → TCON). No invented quotes. Every rule is tagged **SOURCED** or **INFERRED**. INFERRED rules are the coder’s proxy and must be inputs so they can be swept.

**Legend**
- **SOURCED:** Zar stated this in a public video, post, or article (quote + URL).
- **INFERRED:** Needed to code the idea; not a formal rule he published. Starting point only, until calibrated.
- **CALIBRATED:** Measured on 1-minute **NQ=F** (front-month futures) from 21 Oct–19 Nov 2026 against the 22 posted trades and labelled no-trade sessions in `/workspace/zar_backtest_recon.md`. In-sample, small sample (20 traded / 10 no-trade sessions). Not his official numbers and not his actual fills — a codeable proxy. Point distances and ATR units carry over to a NAS100 CFD; absolute NQ levels do not (basis can be tens to ~200 pts).

**Timestamp caveat (important):** Times in `/workspace/zar_trades_raw.md` are **Pacific** (America/Los_Angeles, the box clock), not Eastern. Convert to ET (+3 hours in November standard time) before comparing to session clocks. Examples: the Nov 19 “09:42” win post is **12:42 ET**; the Nov 3 “10:05” loss post is **13:05 ET**; the Nov 19 “02:42” London no-trade post is **05:42 ET** (consistent with a London window ending ~05:00 ET). Use these post times only as upper bounds for when a trade had to be finished.

This is not a complete mechanical clone. Zone “feel,” “juice,” and the live order “dance” remain discretionary. The spec makes those knobs explicit. Empirical defaults below supersede earlier INFERRED numbers where they conflict.

---

## 0. Conventions used in this spec

- All clock times are **America/New_York** (ET). Pine timezone string: `"America/New_York"`.
- Session strings use TradingView’s `"HHmm-HHmm:23456"` form (`2–6` = Mon–Fri). Overnight sessions may wrap midnight (`"1800-0300"`).
- `D` = daily, `30` = 30-minute, `1` = 1-minute.
- Long and short are symmetric unless a setup says otherwise. Pseudocode is written for **long**; invert inequalities, highs/lows, and stop/entry sides for short.
- `ATR30` = 30-minute ATR. `ATRD` = daily ATR. Defaults use `ta.atr(14)` unless noted.
- Point values: NQ `$20` / point, MNQ `$2` / point. NAS100 CFDs vary by broker; use `syminfo.pointvalue`.
- 30-minute setup conditions may only flip **on a confirmed 30-minute close** (`timeframe.change("30")` on a 1-minute chart). 1-minute is for execution (stop orders, pivots, shift candles).
- Do not use `request.security(..., lookahead=barmerge.lookahead_on)` except on already-closed higher-timeframe values (`high[1]`, `close[1]`, etc.).

---

## 0.1 CALIBRATED defaults (NQ 1m, 21 Oct–19 Nov 2026)

Source: `/workspace/zar_backtest_recon.md`. Data in `/workspace/zar_data/`. Reconstruction confidence on the 22 posts: 9 High, 7 Medium, 6 Low. **Rule P** (defined below) reproduced **12 of 22** posted outcomes, including the 3 Nov −1R loss. On most winning days many other entries would also have won; these numbers are a calibration aid, not his fills. Zone / turbo / naked-body logic was **not** in the reconstruction.

**Rule P (codeable v1 entry, CALIBRATED):** After the first 30-minute candle of the session closes, take the first **1-minute close beyond the opening-range edge** in the bias direction. Stop = 15-bar 1m swing extreme + 2 points, optionally capped at the opposite OR edge. Target = the model R (usually 2R). This is the closest single programmed approximation of “wait for the first 30m, then trade out of the OR box with a structural stop.” A 30m-signal-candle stop (Rule Z) produced 150–770 pt risk and almost never reached 2R in-session — **do not** use the far end of the 30m signal candle as the stop.

| Parameter | CALIBRATED default | Basis |
|---|---|---|
| Sessions | London **03:00–05:00 ET**; NY **09:30–11:30 ET**; late-London re-open **04:30–08:00 ET** only after a dead morning (stored kinetic) | Posted results. Medium. DST caveat: 26–30 Oct 2026 the UK was already on GMT while the US was still on DST, so London cash opened at **04:00 ET** that week. |
| First-30m wait | `true` (no entry before open+30 min), except optional early Anabolic entries | Entry times clustered 30–80 min after the open; median **41 min London**, **52 min NY** (~40–55 min). High. |
| Entry trigger | Rule P: 1m close beyond OR in the bias direction, **or** break of session high/low | 12/22 posted outcomes, including 3 Nov loss (session-high long 10:56 ET, stopped 11:22 ET, never +1R — matches “ENTRY SESSION HIGH / NO JUICE”). Medium-High. |
| Stop | Beyond the **15-bar 1m swing + 2 pts**, cap at the opposite OR edge | Median risk ≈ **0.13 × ATR14** (NY ≈ 0.14, ~120 NQ pts, ≈ **0.45 × OR**; London ≈ 0.07, ~60 pts, ≈ 0.8 × OR). Medium. |
| Max risk | Skip if stop would exceed **0.18 × ATR14** | 75th percentile risk was 0.156 × ATR. Medium. |
| Target | 2R fixed; optional 1.5R and BE-at-+1R models | 2R reached in a median ~33 min after entry on reconstructed winners. High. |
| Time stop | **No hard 11:30 ET flatten.** Do not auto-exit at Twilight start. | Some 2R targets printed at **12:00–12:48 ET** (21 Oct, 22 Oct, 11 Nov). A strict 11:30 cut would have turned those into partials. Optional soft flatten only if the target is not near. Medium. |
| Inside-day filter (London) | **Skip London** if the Globex range at 03:00 ET is inside the prior-day range (`func_inside_at_open`) | 4/4 such London opens were no-trade; 0/5 traded London sessions were inside at 03:00. High in-sample. |
| Inside-day filter (NY) | **Do not** block at 09:30. Optional: block if still inside the prior-day range at 10:30 **and** OR < 0.25 × ATR | Nov 5, 9, 12, 13 were inside at the NY open and still traded (and won). Only 3 NY no-trade sessions in the sample. Medium-Low. |
| Quiet / sleepy filter | Stand down if session range after **60–90 min** is still **< 0.15 × ATR14** (London) or **< 0.25 × ATR14** (NY) | Every traded London session had a first-2h range ≥ 0.22 × ATR; every no-trade London except Nov 9 (already an inside day) was ≤ 0.19 × ATR (11/12 split). Code as a *progressive* check, not a 2h look-ahead. Medium. |
| Min OR size | London ≥ **0.08 × ATR14**; NY ≥ **0.15 × ATR14** | Weak filter (London traded median OR 0.10 × ATR, no-trade 0.07). Low-Medium. |
| Daily Fade enable | Only if **prior-day range ≥ 2.0 × ATR14** or **\|close − daily 200 EMA\| ≥ 4%**, plus a 30m topping/bottoming tail | Two examples (6 Nov London long, 19 Nov NY short). Low sample. |
| Sister filter (NQ/ES/YM) | **Off** as a hard filter. Optional: ES confirms the *entry bar* direction (not the first 30m candle) | First-30m alignment was **80%** on no-trade sessions vs **40%** on traded sessions — the opposite of a useful hard filter. Low as a rule, High as a “do not hard-block” finding. |
| 200 EMA | Context / magnet / fade distance only, not a standalone filter | 13 Nov short “daily tagging 200 EMA” confirmed (daily high crossed ~28273). |
| Day-of-week | No hard Monday/Friday ban | Monday London was no-trade on Nov 9 and 16, but other Mondays/Fridays did trade. |

**v1 coding priority:** implement Rule P + first-30m wait + London inside-day block + progressive quiet filter + 15-bar/2-pt stop with 0.18×ATR cap + 2R target, with sisters **off** and **no 11:30 time stop**. Then layer zone/turbo/naked and fade/kinetic/V-reversal modules on top.

---

## 1. Instrument / timeframes / sessions


### 1.1 Instrument

| Item | Spec | Tag |
|---|---|---|
| Primary symbol | `CME_MINI:NQ1!` (Nasdaq-100 futures continuous). Small-size alt: `CME_MINI:MNQ1!`. | INFERRED (he says “NAS100” / “Nasdaq”; contract is not named) |
| Sisters | `CME_MINI:ES1!` (S&P 500), `CBOT_MINI:YM1!` (Dow). | SOURCED as “three sisters: Nasdaq, S&P, Dow” — [FLASH!! MY TRADING GRID!!!](https://www.youtube.com/watch?v=O8Qgxou6yIE) |
| Chart TF | Run the script on **1-minute**. Pull 30-minute and daily with `request.security` or by aggregating 1-minute bars. | SOURCED that 30m is the setup frame and 1m is execution only — [KINETIC ENERGY PLAY MASTERCLASS!](https://www.youtube.com/watch?v=UrY4v_cu22Q) |
| Daily bar | Use the symbol’s exchange daily (NQ Globex daily typically **18:00–17:00 ET**). Do not mix a cash-index daily with a futures 30-minute chart. | INFERRED (he reads a daily “tide” plus Asia/London/NY on 30m; exact daily session not declared) |

**Pine notes**
```pine
//@version=6
symbolNq  = input.symbol("CME_MINI:NQ1!", "Primary")
symbolEs  = input.symbol("CME_MINI:ES1!", "Sister ES")
symbolYm  = input.symbol("CBOT_MINI:YM1!", "Sister YM")
tz        = "America/New_York"
```
If the user charts a NAS100 CFD instead, pass that symbol and verify its daily session matches how they want “yesterday’s range” measured.

### 1.2 Timeframes

> “I don’t trade the one minute chart. The one minute chart is simply a necessary evil for the final execution of the trade. The trade idea, the story comes from the daily and the 30 minute time frame.”  
> — [KINETIC ENERGY PLAY MASTERCLASS!](https://www.youtube.com/watch?v=UrY4v_cu22Q) **SOURCED**

> He also: “the 30-minute chart is the setup time frame.”  
> — [LONDON EARLY TAKE! MAY 20 2026](https://www.youtube.com/watch?v=YXeEsJ594V8) **SOURCED**

| Frame | Role | Pine |
|---|---|---|
| Daily | Tide: bias, body, inside-day, extension, 200 EMA, prior-day span | `request.security(syminfo.tickerid, "D", …)` |
| 30-minute | Setup: zones, turbo/naked, OR location, impulses, zone breaks | `request.security(..., "30", …)` or aggregate on 1m with `timeframe.change("30")` |
| 1-minute (optional 30-second) | Execution: stop orders, pullback pivots, shift candles | Chart TF |

**Pine pattern (non-repainting confirmed 30m / daily)**
```pine
new30 = timeframe.change("30")
newD  = timeframe.change("D")

[dO, dH, dL, dC] = request.security(syminfo.tickerid, "D", [open, high, low, close], lookahead=barmerge.lookahead_off)
prevHigh = request.security(syminfo.tickerid, "D", high[1],  lookahead=barmerge.lookahead_on)
prevLow  = request.security(syminfo.tickerid, "D", low[1],   lookahead=barmerge.lookahead_on)
prevOpen = request.security(syminfo.tickerid, "D", open[1],  lookahead=barmerge.lookahead_on)
prevClose= request.security(syminfo.tickerid, "D", close[1], lookahead=barmerge.lookahead_on)

[o30, h30, l30, c30] = request.security(syminfo.tickerid, "30", [open, high, low, close], lookahead=barmerge.lookahead_off)
```
Store confirmed 30m OHLC into arrays only when `new30` is true (the first 1m bar of the new 30m slot has the previous 30m bar complete).

### 1.3 Sessions and Pine session strings

Zar is in the New York time zone. London cash open is **3:00 a.m. ET**; New York cash open is **9:30 a.m. ET**. UK and US DST usually keep London open at 03:00 ET; note the few mismatch weeks. **SOURCED** open times: [HOW TO DRAW ZAR-ZONES!](https://www.youtube.com/watch?v=CY130H-PFb4), [FLASH CHAT! BEST TIMES OF DAY TO TRADE!](https://www.youtube.com/watch?v=MRAhO4A6SXI).

| Window | Clock (ET) | Pine session string | Tag |
|---|---|---|---|
| Asia / Globex overnight | 18:00–03:00 | `"1800-0300:23456"` | **INFERRED** bounds (he marks “Asia” before London; start is not formally defined). 18:00 is NQ Globex reopen. |
| London session | 03:00–09:30 | `"0300-0930:23456"` | Open **SOURCED** at 03:00; end-at-NY-open **INFERRED**. **CALIBRATED** optimal window 03:00–05:00; late re-open 04:30–08:00 only after a dead morning. **DST:** 26–30 Oct 2026 UK already on GMT, US still on DST → London cash actually 04:00 ET that week. |
| London optimal window | 03:00–05:00 | `"0300-0500:23456"` | **SOURCED** as “first 2 hours” of the session — [MASTERCLASS ON KINETIC ENERGY TRADES!](https://www.youtube.com/watch?v=g8PUCU4eF_0) |
| New York session | 09:30–16:00 | `"0930-1600:23456"` | Open **SOURCED** at 09:30; 16:00 cash close **INFERRED** (futures run to ~17:00) |
| New York optimal window | 09:30–11:30 | `"0930-1130:23456"` | **SOURCED** first 2 hours |
| Europe / UK close | ~11:00–11:30 | — | **SOURCED** UK ~11:30; Frankfurt sometimes described as already closed by then — twilight videos |
| Twilight Zone | 11:30–14:00 | `"1130-1400:23456"` | **SOURCED** as a quiet lunch window — [FLASH!! BEHOLD THE TWILIGHT ZONE!](https://www.youtube.com/watch?v=DixL7iVZ00w). **CALIBRATED: not a hard flatten.** Some reconstructed 2R targets printed as late as **12:00–12:48 ET** (21 Oct, 22 Oct, 11 Nov). Do not auto-exit at 11:30. |
| Power hour / remainder | 14:00–16:00 | `"1400-1600:23456"` | **INFERRED** as post-twilight watch window (he brackets TZ and waits for a later break) |

**Inputs (defaults)**
```
tz                 = "America/New_York"
sessAsia           = "1800-0300:23456"
sessLondon         = "0300-0930:23456"
sessLondonOpt      = "0300-0500:23456"
sessNY             = "0930-1600:23456"
sessNYOpt          = "0930-1130:23456"
sessTwilight       = "1130-1400:23456"
orMinutes          = 30          // see §3
```

**Pine helpers**
```pine
inSess(sess) => not na(time("", sess, tz))
inLondon     = inSess(sessLondon)
inNY         = inSess(sessNY)
inLonOpt     = inSess(sessLondonOpt)
inNyOpt      = inSess(sessNYOpt)
inTwilight   = inSess(sessTwilight)
inAsia       = inSess(sessAsia)

activeSession = inLondon ? "LONDON" : inNY ? "NY" : inAsia ? "ASIA" : "OFF"
```

Session start timestamp (for “minutes into session”):
```pine
sessStartHour = inNY ? 9 : 3
sessStartMin  = inNY ? 30 : 0
sessStart     = timestamp(tz, year, month, dayofmonth, sessStartHour, sessStartMin)
minsInto      = inLondon or inNY ? (time - sessStart) / 60000.0 : na
```
Reset session state when `activeSession` changes from OFF/ASIA → LONDON, and from LONDON → NY (NY is a new session with its own open range and trade count).

---

## 2. Daily bias (“tide”)

> He calls daily / 30m / 1m “the tide, the waves, and the ripples. The tide is stronger than the waves and the waves are stronger than the ripples.”  
> — [MASTERCLASS ON FADING THE DAILY BIAS!](https://www.youtube.com/watch?v=yN5NzzDjowk) **SOURCED**

Compute on the **developing** daily bar (for today’s bias) and on the **completed** prior daily bar (for span of travel and inside-day).

### 2.1 Prior-day span of travel

> Anabolic flow includes “trading above the span of travel of the prior day at the time of entry.”  
> — [LONDON EARLY TAKE! MAY 22 2026](https://www.youtube.com/watch?v=DMVlkFkkvaU) **SOURCED**

**Algorithm**
```
prevHigh, prevLow, prevOpen, prevClose  // completed prior daily
aboveSpan = close > prevHigh
belowSpan = close < prevLow
insideSpan = close >= prevLow and close <= prevHigh
```

| Parameter | Default | Tag |
|---|---|---|
| Span reference | Prior **completed** daily high/low | SOURCED concept; INFERRED that it is yesterday’s H/L (not a rolling 24h) |

### 2.2 Body direction and strength

Zar repeatedly checks “Daily Bull Body” / “Daily Bear Body” and “strong bullish body.” **SOURCED** as language; **INFERRED** numeric cut.

```
dBody       = math.abs(dC - dO)
dRange      = dH - dL
bodyRatio   = dRange > 0 ? dBody / dRange : 0.0
bullBody    = dC > dO
bearBody    = dC < dO
strongBody  = bodyRatio >= bodyRatioMin
upDay       = bullBody and dC > prevClose   // weak alt: bullBody only
downDay     = bearBody and dC < prevClose
```

| Parameter | Default | Tag |
|---|---|---|
| `bodyRatioMin` | `0.55` | INFERRED (distinguishes “strong body” / “large naked body” from dojis) |
| `upDay` definition | bullish body, and close vs prior close | INFERRED (he says “up day” and “bullish body” as related but not identical) |

### 2.3 Inside day / tiny day

Recap language: “FUNCTIONAL INSIDE DAY,” “TINY INSIDE DAY,” “SMALL INSIDE DAY.” **SOURCED** as no-trade reasons in Telegram recaps (e.g. 10, 12, 16 Nov 2026). Formal numeric “tiny” is **INFERRED**.

```
atrD = request.security(syminfo.tickerid, "D", ta.atr(14)[1], lookahead=barmerge.lookahead_on)

// Functional inside at a timestamp T (e.g. London 03:00 or NY 09:30):
// today's Globex range so far (from 18:00 ET prior) is fully inside prior-day H/L.
globexHigh(T), globexLow(T) = high/low of the current Globex day as of T
funcInsideAt(T) = globexHigh(T) <= prevHigh and globexLow(T) >= prevLow

insideDay      = dH <= prevHigh and dL >= prevLow          // developing full-day range
tinyDay        = (dH - dL) < tinyAtrMult * atrD
tinyInsideDay  = insideDay and tinyDay

londonInsideBlock = funcInsideAt(03:00 ET)    // CALIBRATED: skip London
nyInsideAtOpen    = funcInsideAt(09:30 ET)    // CALIBRATED: do NOT block NY at the open
```

| Parameter | Default | Tag |
|---|---|---|
| `tinyAtrMult` | `0.55` | INFERRED (size cut). The **London** no-trade switch that actually split the sample is `funcInsideAt(03:00)`, **CALIBRATED**, not this ATR size cut. |

“Functional inside day” **INFERRED:** treat as `insideDay` even if a wick has marginally pierced the prior high/low but the **body** (or almost the entire range) remains inside. Optional stricter body test: `math.max(dO,dC) <= prevHigh and math.min(dO,dC) >= prevLow`. Input `insideMode = "range" | "body"` default `"range"`.

### 2.4 Daily 200 EMA

Recap example: 13 Nov 2026 “ANABOLIC FLOW / DAILY TAGGING 200 EMA.” **SOURCED** as a context tag, not as a standalone trigger.

```
ema200D = request.security(syminfo.tickerid, "D", ta.ema(close, emaDailyLen), lookahead=barmerge.lookahead_off)
tag200  = math.abs(dC - ema200D) <= ema200BandAtr * atrD
      or (dL <= ema200D and dH >= ema200D)   // daily bar touches the EMA
```

| Parameter | Default | Tag |
|---|---|---|
| `emaDailyLen` | `200` | SOURCED length; INFERRED that it is a daily EMA |
| `ema200BandAtr` | `0.15` | INFERRED “tagging” band |

Use as **context** (checklist / filter / fade magnet), not as an entry signal.

### 2.5 Daily extension

> On a “very big down day, super extended on the 30 minute chart… I will throw on my EMAs and absolutely expect a pullback to at least the nine, often the 21 EMA.”  
> — [SOLID WIN!! BUY THE DIP!](https://www.youtube.com/watch?v=5_hNGl7cCH4) **SOURCED**

> “If we are fading the daily candle, it is absolutely a huge mistake to be entering late on an extended move on the upside.”  
> — [MASTERCLASS ON AVOIDING EXTENSION!](https://www.youtube.com/watch?v=9j-Hqmm9Ylg) **SOURCED**

**Algorithm (INFERRED numeric proxy)** — two layers:

```
ema9_30  = EMA(c30, 9)    // on confirmed 30m series
ema21_30 = EMA(c30, 21)
atr30    = ATR(c30, 14)

extUp30   = (c30 - ema21_30) / atr30
extDn30   = (ema21_30 - c30) / atr30
dailyExtUp   = (dC - prevLow)  / atrD     // stretch of the developing day
dailyExtDn   = (prevHigh - dC) / atrD
                      // alts to sweep: (dC - ema21D)/atrD, or dRange/atrD

isExtendedUp   = extUp30 >= extAtr30 or dailyExtUp >= extAtrD
isExtendedDown = extDn30 >= extAtr30 or dailyExtDn >= extAtrD
```

| Parameter | Default | Tag |
|---|---|---|
| `emaFast` / `emaSlow` | 9 / 21 | SOURCED lengths on the 30m/1m |
| `extAtr30` | `1.8` | INFERRED |
| `extAtrD` | `1.4` | INFERRED |
| Late-fade ban | If fading down-day (going long) and `extUp30 >= lateFadeAtr` (`1.2` default), **do not enter** | SOURCED as a mistake; INFERRED threshold |

### 2.6 Composite daily bias

```
biasLong  = (bullBody or upDay) and not isExtendedUp
biasShort = (bearBody or downDay) and not isExtendedDown
biasNeutral = insideDay or (not bullBody and not bearBody)
```
Anabolic Flow (§5.1) is stricter than `biasLong`/`biasShort`. Daily Fade (§5.3) **requires** extension *against* the intended trade.

---

## 3. Open range (dynamic) and the first-30m wait

### 3.1 Minimum open range

> “I typically use the 10 minute candle, the first 10 minute candle, as my minimum open range… if prices are inside of this opening range chances are I will not even think about taking a trade, but the real open range needs to be expanded… my actual functional range.”  
> — [FLASH CHAT! OPEN RANGE!](https://www.youtube.com/watch?v=4VctAH-xj8s) (2022) **SOURCED** (historical 10m minimum)

> 2026 practice waits through the first 30-minute candle and treats a **dynamic open range** as a no-trade box: “My dynamic open range is really just a tool to keep me out of making impulsive decisions based on the lowest time frame. I’m setting an area here, which is basically a no-trade zone, at least for the time being.”  
> “I will often use key pre-market highs and lows as my dynamic open range.”  
> “It’s fine to trade inside of this dynamic open range if a clean setup prints later in the session.”  
> “This break of the 1-minute open range wasn’t an entry signal for me, so I expanded the open range. And this break of the dynamic open range was not an entry signal, so I expanded it again.”  
> — [MASTERCLASS on DYNAMIC OPEN RANGE!](https://www.youtube.com/watch?v=K12mXxKusHU) **SOURCED**

Location filter (execution): “Shorts below the open range, longs [above the] range.” — [KINETIC ENERGY PLAY MASTERCLASS!](https://www.youtube.com/watch?v=UrY4v_cu22Q) **SOURCED**

### 3.2 Algorithm

Reset at each session start (London 03:00, New York 09:30).

```
Inputs:
  orMinutes        = 30      // 2026 default; 10 is the 2022 historical minimum
  orExpandMinutes  = 90      // max time from session start to keep expanding
  usePremarketOR   = true
  orPadPoints      = 0       // optional padding

On session start:
  orHigh = high, orLow = low
  orLocked = false
  if usePremarketOR:
      // London: seed with Asia high/low (18:00–03:00)
      // NY: seed with max/min of Asia+London (18:00–09:30) as a *reference*,
      //     but still start the NY minimum OR from the first orMinutes of NY,
      //     then expand toward those pre-market highs/lows if price ping-pongs
      //     between them without a valid setup (K12mXxKusHU NY example).
      preHigh, preLow = preSessionHiLo()
      // Do not immediately set orHigh/orLow = pre range if that would
      // swallow the whole morning. Store as expand-targets.

While minsInto < orMinutes:
  orHigh = max(orHigh, high)
  orLow  = min(orLow, low)

At minsInto == orMinutes (first 30m close):
  orMinHigh, orMinLow = orHigh, orLow     // freeze the minimum OR
  // 1-minute open range (optional display): high/low of first 1m bar of session

Dynamic expand (minsInto < orExpandMinutes and not in a live trade):
  if close breaks orHigh or orLow
     and no valid setup fired on that break (see §5):
         orHigh = max(orHigh, high)
         orLow  = min(orLow, low)
         // optionally snap outward toward preHigh/preLow if the break
         // is still inside that pre-market box

  orLocked = minsInto >= orExpandMinutes

insideOR = close <= orHigh and close >= orLow
aboveOR  = close > orHigh
belowOR  = close < orLow

emasClearedOR_long  = ema9_30 > orHigh and ema21_30 > orHigh   // “EMAs cleared O-Range”
emasClearedOR_short = ema9_30 < orLow  and ema21_30 < orLow
```

| Parameter | Default | Tag |
|---|---|---|
| `orMinutes` | `30` | SOURCED as current wait; 10m is documented as older minimum |
| `orExpandMinutes` | `90` | INFERRED |
| `usePremarketOR` | `true` | SOURCED idea; INFERRED exact seed windows |
| Trade-inside-OR later | Allowed only if a §5 setup is clean and `minsInto >= orMinutes` | SOURCED exception |

### 3.3 First-30-minute wait

Recap checklists: “Waited First 30M,” sometimes “Waited First 1 Hour” / “90M.” **SOURCED** as a frequent filter.

```
waitFirst30Done = minsInto >= orMinutes
earlyEntryOK    = anabolicFlow and cleanTCON and inOptWindow   // §5.1 early resumption
canEnter        = (waitFirst30Done or earlyEntryOK) and not hardNoTrade
```

Default: **no entries until the first 30-minute candle of the *current* session closes**, except the Anabolic Flow early-resumption exception. **SOURCED** exception: “Strong up days give me permission to do more… early entry for a TCON when we have clean, flowing price action on an anabolic flow day in a turbo zone with a naked body.” — [LONDON EARLY TAKE! MAY 22 2026](https://www.youtube.com/watch?v=DMVlkFkkvaU)

---

## 4. Zones: drawing, turbo / clean traffic, naked bodies

### 4.1 Zar-zones (drawing)

> Draw “zones of support and resistance, areas where prices may in fact reject.” He marks the **top of bodies**, sometimes extends to related wicks, maps Asia before London, flips broken support to resistance, and **deletes** zones that have been “wiped out.”  
> — [HOW TO DRAW ZAR-ZONES!](https://www.youtube.com/watch?v=CY130H-PFb4) **SOURCED** (method is visual, not numeric)

> Refresh: strip clutter and keep only nearby, still-relevant levels. “There’s a myth that these things need to continue… in perpetuity… it’s not true.”  
> — [REFRESH YOUR ZONES! GET NAKED!](https://www.youtube.com/watch?v=kjlprYhAfFs) **SOURCED**

**Algorithm (INFERRED proxy — all parameters are sweepable)**

```
type Zone
    float top
    float bot
    int   bornBar          // 30m bar index
    int   touches
    bool  flipped          // S/R flip
    bool  dead
    bool  turbo
    bool  hasNaked
    int   nakedBar

Inputs:
  zoneLookback30   = 64        // ~32 hours of 30m bars (covers prior day + Asia)
  zoneClusterAtr   = 0.25      // merge edges within 0.25 * ATR30
  zonePadAtr       = 0.10      // half-width around a cluster
  zoneMinTouches   = 2         // a lone wick is weaker than a cluster
  zoneMaxCount     = 12
  zoneKillOnCloseThru = true   // 30m close through the zone “wipes it out” after follow-through

Build (at each confirmed 30m close, and at pre-London map time):
  1. Collect candidate edges from the last zoneLookback30 confirmed 30m bars:
       - body high = max(o30, c30), body low = min(o30, c30)
       - session high/low of Asia, London, NY (if those sessions are complete)
       - optional: wick high/low if the wick is “related” (within zoneClusterAtr of a body edge)
  2. Cluster edges whose prices differ by < zoneClusterAtr * ATR30.
     Zone.bot = clusterMin - zonePadAtr * ATR30
     Zone.top = clusterMax + zonePadAtr * ATR30
  3. Keep clusters with touches >= zoneMinTouches, plus the most recent session H/L even if 1 touch.
  4. Cap at zoneMaxCount, preferring nearer-to-price and more-touched.
  5. S/R flip: if a 30m bar closes through a zone and later retests it from the other side, mark flipped.
  6. Kill: if zoneKillOnCloseThru and a later 30m bar fully closes through and the zone is no longer nearby, set dead and drop from the array.
```

**Pine notes:** store `array<Zone>`. Rebuild or incremental-update on `new30`. Draw with `box.new` / `line.new`. Do not recompute off forming 30m highs (repaint). Pre-session “GRID” arrows = zones + clean-traffic direction flags computed at London open (03:00) and refreshed at NY open (09:30).

### 4.2 Clean traffic

> Look left and stack horizontal lines on prior wicks/bodies. If that builds “an infrastructure of messiness… prices are likely to pause… and get rejected.” If after a close above the last wick “there’s nothing else: clean traffic.”  
> — [FLASH CHAT! CLEAN TRAFFIC EXPLAINED!](https://www.youtube.com/watch?v=Cm_AeaMM63Y) **SOURCED** (visual test; counts are INFERRED)

**Algorithm**
```
countOverlaps(price, lookback) =
    number of confirmed 30m bars i in 1..lookback
    whose [l30[i], h30[i]] contains `price`

countPathOverlaps(p0, p1, lookback) =
    number of confirmed 30m bars whose range intersects [min(p0,p1), max(p0,p1)]
    // optionally ignore the most recent 1–2 impulse bars that *created* the move

cleanAt(price)      = countOverlaps(price, trafficLookback) <= trafficMaxOverlaps
cleanPath(from, to) = countPathOverlaps(from, to, trafficLookback) <= trafficMaxOverlaps
messyPath(from, to) = not cleanPath(from, to)
```

| Parameter | Default | Tag |
|---|---|---|
| `trafficLookback` | `50` | INFERRED (user-suggested N=50 is adopted) |
| `trafficMaxOverlaps` | `4` | INFERRED |
| `turboMaxOverlaps` | `2` | INFERRED (stricter than generic clean) |

### 4.3 Turbo zone

> “Clean traffic turbo zone with a naked body… This is a turbo zone. I love trading turbo zone.”  
> — [LONDON EARLY TAKE! MAY 22 2026](https://www.youtube.com/watch?v=DMVlkFkkvaU) **SOURCED**

> Naked bodies in a turbo zone act as **magnets**: “breaking handily back into a turbo zone with naked body up above as a magnet. That naked body, by the way, is about half covered as we speak.”  
> — [MASTERCLASS ON AVOIDING EXTENSION!](https://www.youtube.com/watch?v=9j-Hqmm9Ylg) **SOURCED**

**Algorithm (INFERRED composition of sourced ideas)**
```
Zone is turbo when:
  cleanPath(currentPrice, zoneMid) using turboMaxOverlaps
  and (hasNakedBodyInOrBeyond(zone) or zone itself is a naked-body cluster)
  and not a “strong rejection zone” in the way
      (strong rejection := cluster with wick-dominated touches and >= rejectTouches failures)

hasNakedBodyInOrBeyond(long zone above price) =
    there exists a naked 30m or daily body whose body mid is in [price, zone.top + magnetPad]
```

| Parameter | Default | Tag |
|---|---|---|
| `turboMaxOverlaps` | `2` | INFERRED |
| `rejectTouches` | `3` | INFERRED |
| `magnetPad` ATR | `0.5` | INFERRED |

### 4.4 Naked body

Zar never published a one-line numeric definition. Usage: he draws markers on uncovered bodies, deletes them when “covered completely,” and still refers to a body that is “about half covered” as a magnet being consumed. **SOURCED** behavior; **INFERRED** formula.

**Algorithm** (adopts the user-proposed starting point)
```
bodyTop(i) = max(o30[i], c30[i])
bodyBot(i) = min(o30[i], c30[i])
bodyLen(i) = bodyTop(i) - bodyBot(i)

A 30m (or daily) bar i is a *candidate* if:
  bodyLen(i) >= nakedMinAtr * ATR30[i]
  and bodyLen(i) / range30[i] >= nakedBodyRatioMin

Fill of bar i as of now:
  covered = 0
  for each later confirmed bar j > i:
      covered += length of intersection([l30[j], h30[j]], [bodyBot(i), bodyTop(i)])
      // union-merge overlaps so fill is not double-counted
  fillPct(i) = covered / bodyLen(i)

isNaked(i)     = fillPct(i) <= nakedFillMax
isHalfCovered  = fillPct(i) >= 0.5 and fillPct(i) < 1.0
isFullyCovered = fillPct(i) >= 1.0     // delete marker

Lookback for candidates: nakedLookback = 50 30m bars (and the current daily body).
```

| Parameter | Default | Tag |
|---|---|---|
| `nakedLookback` | `50` | INFERRED (user proposal) |
| `nakedMinAtr` | `0.40` | INFERRED |
| `nakedBodyRatioMin` | `0.50` | INFERRED |
| `nakedFillMax` | `0.50` | INFERRED (0 = “not traded through by any later bar”; 0.50 matches “half covered” still counting) |
| Fill measure | Later bars’ **range** (high-low), not only bodies | INFERRED |

---

## 5. Setups (pseudocode)

Shared execution helpers are in §5.0. Each setup lists preconditions, trigger, entry, stop, target, invalidation. Long side shown.

### 5.0 Shared 1-minute execution, stop, target

> Entries are buy/sell **stop** orders, often “above this [shift] candle… stop below this shift candle… below the wick of that candle… and the current pivot in the making.”  
> — [LONDON EARLY TAKE! MAY 22 2026](https://www.youtube.com/watch?v=DMVlkFkkvaU) **SOURCED**

> “Normally on a trend continuation or TCON trade I like to see an orderly pullback to the 21 or close to it.”  
> — [TCON MASTERCLASS! TIMING THE ENTRY!](https://www.youtube.com/watch?v=JswxAGbsCs8) **SOURCED**

> Triple-protection stops: “The first protection is the current pivot. The second protection is the top of the open range. The third protection is the key shift candle and being a couple of points or so below that.” He only counts hits when price **crosses the line**.  
> — [STOP LOSS MASTERCLASS! WIN!](https://www.youtube.com/watch?v=IGnfcfMmt3A) **SOURCED**

**Definitions (INFERRED where noted)**
```
Impulse (long): a 30m (or 1m run) of directional closes making a new session or swing high,
                body-dominant, preferably into clean traffic.

Orderly pullback (long): after the impulse, 1m (or 30m) retrace that:
  - reaches or approaches ema9_1m or ema21_1m (or ema9_30 / ema21_30 if the pullback is large)
  - does not become a “choppy meandering grinding lackluster mess” 
    proxy: pullback bars <= pbMaxBars, and pullback depth <= pbMaxAtr * ATR30,
           and close does not lose the impulse start
  - optionally prints a bottom wick (“pullback on a lower time frame”)

Shift candle (long): a 1m bar that closes bullish and breaks the pullback high
                     (or breaks the high of the prior 1m bar after the tag of the 21).
                     “Pivot in the making” = the low of that shift / pullback swing.

Session high/low: high/low since sessStart.

Entry (long), **v1 CALIBRATED default (Rule P):**
  after first 30m close, if close (1m) > orHigh and bias is long:
      enter at that 1m close (or buy stop one tick above orHigh, filled on the close-through)
  alt: buy stop at sessionHigh (reproduces the 3 Nov “ENTRY SESSION HIGH” loss)
  Typical fill time: ~40–55 min after the session open (median 41 min London, 52 min NY).

Entry (long), video language (stop orders on a shift candle):
  strategy.entry(..., stop=shiftHigh + entryPadTicks * syminfo.mintick)
  (he uses stops, not market orders, in the videos)

Stop (long), **v1 CALIBRATED default (use this in code first):**
  swingLow15 = lowest(low, 15) on the 1m chart at the entry bar
  stop = min(swingLow15, orLow) - 2.0 points     // cap at opposite OR edge; +2 pt pad
  riskPts = entry - stop
  if riskPts > 0.18 * atrD: skip the trade        // max-risk cap, CALIBRATED
  // Empirical median risk ≈ 0.13 × ATR14
  //   NY ≈ 0.14 × ATR ≈ 120 NQ pts ≈ 0.45 × OR
  //   London ≈ 0.07 × ATR ≈ 60 pts ≈ 0.8 × OR
  // Do NOT use the far end of a 30m signal candle as the stop (Rule Z: 150–770 pt risk, 2R almost never hit).

Stop (long), TCON / anabolic (SOURCED language, looser than v1):
  stop = min(pivotLow, shiftLow) - stopPadPoints

Stop (long), Daily Fade / “give it room” (SOURCED idea):
  stop = min(pivotLow, shiftLow, orLow) - stopPadPoints
  // still apply the 0.18 × ATR14 cap; if the fade needs more, skip or use a tighter structural swing

Triple-protection option (SOURCED idea; often too wide vs CALIBRATED 0.13×ATR):
  stop = min(pivotLow, orLow, shiftLow) - stopPadPoints

Target:
  R = entry - stop
  t1 = entry + 1.0 * R
  t15= entry + 1.5 * R
  t2 = entry + 2.0 * R
```

| Parameter | Default | Tag |
|---|---|---|
| `pbMaxBars` (1m) | `12` | INFERRED |
| `pbMaxAtr` | `1.0` | INFERRED |
| `emaFast` / `emaSlow` | 9 / 21 | SOURCED |
| `entryPadTicks` | `1` | INFERRED |
| `stopPadPoints` | `2.0` | SOURCED as “a couple of points”; **CALIBRATED** as +2 pts beyond the 15-bar 1m swing |
| Default live model | Model C: 2R all-or-nothing (see §7) | INFERRED (most public recaps post +2.00R) |

Invalidation shared: cancel working orders if the opposite 30m body flip prints, if price closes back through the stop **before** a fill, or if the session ends / hard no-trade begins (Twilight, unless the setup is kinetic or already filled).

---

### 5.1 TCON / Anabolic Flow  (signature)

> “This is anabolic flow. A strong up day with a strong bullish body trading above the span of travel of the prior day at the time of entry, of course. Into a clean traffic turbo zone with a naked body.”  
> “Strong up days give me permission to do more.”  
> “This is actually my preferred entry on TCON trades… this is my signature trade. These aggressive entries are for clean flowing price action on up days if they’re long trades.”  
> “If it’s a neutral day or if I’m fading the daily candle, I absolutely would not be taking an early resumption.”  
> “If it’s a neutral day, or a down day, or a sluggish day, or this is not a turbo zone, or there are no naked bodies, [wait for the breakout / don’t take the early entry].”  
> — [LONDON EARLY TAKE! MAY 22 2026](https://www.youtube.com/watch?v=DMVlkFkkvaU) **SOURCED**

TCON = **Trend Continuation**. **SOURCED** — [X, 18 Jul 2023](https://x.com/ZarillionTrades/status/1681372156356067351); [FLASH! WHY NO TCON TRADES TODAY!](https://www.youtube.com/watch?v=O-wrNLA4Zkw).

**Preconditions (long)** — all must be true unless noted
```
anabolicFlow_long =
    bullBody and strongBody
    and aboveSpan                    // at time of entry
    and not insideDay
    and inSession (London or NY)
    and (inLonOpt or inNyOpt or kineticWindow)   // see §5.4
    and sistersAligned_long          // §6
    and not hardNoTrade              // §6

tconContext_long =
    anabolicFlow_long
    and cleanPath(close, upsideObjective) or turbo zone above
    and hasNakedBody in/beyond the path
    and aboveOR or (early and breaking out of OR)
    and not isExtendedUp             // don’t chase a already-stretched run
```

**Trigger**
```
impulse_up then orderly_pullback (preferably into ema9/ema21)
and 30m structure still bullish (30m bull body / bull wave)
```

**Entry**
```
v1 default (CALIBRATED Rule P), once preconditions are true and first 30m has closed:
    buy on the first 1m close > orHigh
    // or buy stop at sessionHigh if that is the trigger
    // typical 40–55 min after the open; do not enter before open+30
    // early resumption (open+<30) only if anabolicFlow_long is flagged

if anabolicFlow_long and clean flowing PA (video language, on top of Rule P):
    EARLY resumption allowed: buy stop at shiftHigh of the pullback
    // do NOT require a break of the session high / day extreme first
else if tconContext_long is only “ok” (neutral-ish, or no turbo/naked):
    BREAKOUT entry: buy stop at sessionHigh or first 1m close beyond OR
else:
    no trade
```

**Stop:** **CALIBRATED v1** 15-bar 1m swing + 2 pts, cap at opposite OR edge, skip if > 0.18 × ATR14. Video language (wider): pivot + shift wick + pad.  
**Target:** 2R in a “very clear” NY tape; 1.0–1.5R in London or unclear tape (`londonTargetR = 1.5` default, INFERRED).  
**Invalidation**
```
pullback exceeds pbMaxAtr or loses impulse start
or 30m closes back inside OR against the trade
or sisters flip against the trade before fill
or daily body flips from bull to bear (developing) before fill
```

**Momentum / “MOMO TCON” variant (SOURCED as a recap label; rules INFERRED):** same preconditions, but allow a shallower pullback (`pbMaxAtr = 0.5`) in “freefall” conditions (`extDn30` already large and still in direction of the daily body). Do not use early-resumption on a fade day.

**FIB TCON variant (SOURCED):** if the pullback is “too deep / less orderly,” switch to a 50–61.8% retracement of the impulse (“kill zone”), then enter on a 1m shift. Not a standard TCON. — [ADVANCED MASTERCLASS! FIB TCON ENTRY!](https://www.youtube.com/watch?v=BN3kJMT3HgU)

```
impHigh, impLow = start/end of the impulse swing
retrace = (impHigh - close) / (impHigh - impLow)     // long pullback
inKill  = retrace >= 0.50 and retrace <= 0.618
```

---

### 5.2 Zone Break

> “First, we want to identify a period of consolidation or congestion after a move… Then we wait for price to break and close beyond a key 30 minute zone marker… Price must be entering and closing into a clean traffic range… Then I want to enter on a subsequent break of the signal candle… To qualify, the current move should not be overextended… There should be a recent pullback on a lower time frame before entry… You want to seek higher time frame support for the trade idea… be cautious of zone breaks during slow market times of the day.”  
> — [MASTERCLASS ON ZONE BREAK PATIENCE!](https://www.youtube.com/watch?v=aPjfQhONB34) **SOURCED**

> “I typically wait for clean break and close into a turbo zone when the picture [is indecisive].”  
> — [MASTERCLASS BREAK & CLOSE CLINIC!](https://www.youtube.com/watch?v=fF9fcvjSkng) **SOURCED**

**Preconditions (long)**
```
a mapped zone Z above or at price
prior 30m move up, then congestion against Z
  congestion proxy: >= zbCoilBars 30m bars overlapping a box of width <= zbCoilAtr * ATR30
HTF support: bullBody or at least not a strong bearish extended down day
not isExtendedUp
not inTwilight unless kineticWindow
sistersAligned_long (soft: 2of3 allowed — input)
inLondon or inNY, preferably inOptWindow
```

**Trigger**
```
confirmed 30m close > Z.top          // “break and close beyond the zone marker”
and cleanPath(Z.top, nextTurboOrNaked) or landing in a turbo zone
signalCandle = that 30m bar
```

**Entry**
```
after signalCandle is confirmed, place buy stop at signalCandle.high + entryPadTicks
optional: wait for a 1m pullback wick first (bottom wick / “recent pullback”)
auto-trade mode: leave the stop order working unattended (§5 note)
```

**Stop (long):** do **not** use `signalCandle.low` as the risk (Rule Z was 150–770 pts and almost never reached 2R). **CALIBRATED v1:** 15-bar 1m swing + 2 pts, cap at the opposite OR edge, skip if risk > 0.18 × ATR14.  
**Target:** 2R default; reduce if late in session.  
**Invalidation**
```
30m closes back below Z.bot after the signal (failed break)
or price never breaks the signal-candle high within zbExpireBars 30m bars
or congestion was actually a topping pattern into messy traffic
```

| Parameter | Default | Tag |
|---|---|---|
| `zbCoilBars` | `3` | INFERRED |
| `zbCoilAtr` | `0.8` | INFERRED |
| `zbExpireBars` | `4` | INFERRED |

**Zone Continuation / Zone Reversal** — labels **SOURCED** in recaps; mechanics **INFERRED**: continuation = already-trending 30m wave breaking the *next* zone (skip the long coil requirement). Reversal = rejection at a zone then 30m close back through it (can overlap V-reversal / fade).

**Auto-trade:** “an order being set on automatic pilot.” — [PERFECT AUTO TRADE WINNER!](https://www.youtube.com/watch?v=Sf0vqh5IekU) **SOURCED**. Implementation: same Zone Break, no intra-bar cancel except hard invalidation.

---

### 5.3 Daily Fade

> “The reason I didn’t place my stop here below that pivot is because I’m fading the daily candle… I always want to make sure that I give it enough room to work. If this was anabolic flow… I would likely have my stop down below here, and I would be long since done this trade at two R.”  
> — [SOLID WIN!! BUY THE DIP!](https://www.youtube.com/watch?v=5_hNGl7cCH4) **SOURCED**

> “These are the types of orderly days that I will not fade unless I have something incredibly compelling.”  
> — [LONDON EARLY TAKE! MAY 22 2026](https://www.youtube.com/watch?v=DMVlkFkkvaU) **SOURCED**

**Preconditions (long fade of a down day)**
```
// CALIBRATED enable (2-sample, Low confidence — still use it as the v1 gate):
fadeEnabled = (priorDayRange >= 2.0 * atrD) or (abs(prevClose - ema200D) / prevClose >= 0.04)
              and a 30m topping/bottoming tail is present
              // examples: 6 Nov London long (pd range 2.49×ATR, ~−6% vs 200 EMA);
              //           19 Nov NY short (opened above PDH, ~−3.8% vs 200 EMA, first-30m topping tail)

isExtendedDown                     // extreme, not a mild down day
bearish developing daily (downDay or bearBody after a selloff)
NOT anabolicFlow_short in a clean orderly trend (do not fade orderly anabolic days)
preferably a rebound context: daily rejecting low, or 30m body flip bull, or topping/bottoming tail
not late-chase: extUp30 < lateFadeAtr after the bounce has already run
sisters: NOT a hard filter (CALIBRATED). Optional: ES confirms the entry-bar direction.
```

**Trigger**
```
30m signs the extreme is failing:
  body flip, or 30m topping/bottoming tail (wick >= tailWickRatio * range),
  or reclaim of a short-term 30m low, or snapback toward ema9_30 / ema21_30
```

**Entry**
```
NOT early resumption
buy stop after confirmation (shift candle / break of a small 1m base)
often “entry at session high” after the bounce starts — recap language SOURCED, exact trigger INFERRED:
  buy stop at sessionHigh once trigger printed, only if the bounce is not already late-extended
```

**Stop:** Fade stop = `min(pivotLow, orLow) - stopPadPoints` (wider, beyond OR). **SOURCED** idea.  
**Target:** 2R still allowed, but default `fadeTargetR = 1.5` (INFERRED) because the wider stop makes 2R farther. Dynamic-manage if Twilight is near.  
**Invalidation**
```
new 30m close makes a fresh extreme beyond the fade pivot (trend resumes)
or lateFadeAtr breach
or “no juice” proxy fails (optional filter — see open questions)
```

| Parameter | Default | Tag |
|---|---|---|
| `tailWickRatio` | `0.45` | INFERRED (30m topping/bottoming tail) |
| `lateFadeAtr` | `1.2` | INFERRED |
| `fadeTargetR` | `1.5` | INFERRED (many posted fades still booked +2R; keep 2R available) |
| Fade enable: `pdRangeAtrMin` | `2.0` | **CALIBRATED** (2 samples; Low) |
| Fade enable: `ema200DistPctMin` | `0.04` (4%) | **CALIBRATED** (2 samples; Low) |

The 3 Nov 2026 −1R long was a Daily Fade + Zone Break tagged “NO JUICE.” A coded fade **may still fire** that day; do not treat it as a no-trade day. Use it to test a “juice” filter later.

---

### 5.4 Stored Kinetic Energy

> “When the optimal trading window produces no meaningful movement, very often there’s stored kinetic energy. The market wants to express itself, but only does so after the optimal trading window.”  
> “If the morning is dead, expand the window. The Nasdaq index tends to make the biggest move in the first 2 hours… some days the Nasdaq will chop inside a narrow band for the morning. This often leads to a no trade outcome… If that energy is expressed in the morning, then my trading day is done. If that energy has not found expression, I may expand my trading window. Sometimes this kinetic release… will happen in the twilight zone… there are no guarantees… Sometimes we just range all day.”  
> — [KINETIC ENERGY PLAY MASTERCLASS!](https://www.youtube.com/watch?v=UrY4v_cu22Q), [MASTERCLASS ON KINETIC ENERGY TRADES!](https://www.youtube.com/watch?v=g8PUCU4eF_0) **SOURCED**

He often already posted “NO TRADES” for the session, then reopened. When he takes these he **asks less** (1R or 1.5R), and may not run all four models. **SOURCED**.

**Preconditions**
```
optimal window has ended (minsInto >= 120)
and morning was “dead”:
    (orHigh - orLow) < deadOrAtr * ATR30
    or no setup fired in the optimal window
    or session labeled rangebound / sleepy
and daily bias still clear (bullBody or bearBody, not tinyInsideDay)
and energy not already expressed (no already-completed 2R in this session)
```

**Trigger**
```
later expansion: 30m close beyond the dynamic OR and/or beyond session extreme
into a turbo zone / naked-body path
in the direction of the daily body (it is a late TCON, not a late fade)
```

**Entry:** sell/buy stop beyond dynamic OR or the confirming 30m close, TCON-style 1m shift allowed.  
**Stop:** beyond OR and prior pivots / stacked EMAs (example from the video: “Stop loss above the open range and above prior pivot… and both EMAs”). **SOURCED**.  
**Target:** `kineticTargetR = 1.0` default (he cut 1.5R → 1R in the sleepy example). Allow 1.5R if the break is clean.  
**Invalidation:** morning was not actually dead (OR already large); or the late break is messy traffic; or the whole day remains a range (`minsInto` past `kineticExpireMins`).

| Parameter | Default | Tag |
|---|---|---|
| `deadOrAtr` | `0.9` | INFERRED |
| `kineticTargetR` | `1.0` | SOURCED as “ask less”; value INFERRED from the 1R example |
| `kineticExpireMins` | `240` from session start | INFERRED |
| May trade in Twilight | `true` for this setup only | SOURCED |

18 Nov 2026 London: first post was NO TRADES (sleepy), then London #2 short +2R stored kinetic. The state machine must allow **SCAN → SESSION_DONE (no trade) → KINETIC_WATCH → IN_TRADE**.

---

### 5.5 Open-Range V-Reversal

Recap: 18 Nov 2026 NY “STRUCTURAL V-REVERSAL RETEST OF OPEN RANGE.” **SOURCED** label.

> In the V-reversal masterclass he describes a “100% V reversal” back to the top of a wick / session extreme, then trades the next break back in the direction of the larger daily body, often below/above the open range and 9/21 EMAs, sometimes with a 50–61.8 kill zone on the reversal leg.  
> — [MASTERCLASS ON STALKING A V-REVERSAL!](https://www.youtube.com/watch?v=f_uS47m8DcA) **SOURCED** (that instance was a short after a full retrace inside a big bearish daily candle)

**Preconditions (short example, invert for long)**
```
a drive out of (or away from) the open range made a session extreme
price retraces a large fraction of that drive (vrMinRetrace)
daily body still supports the *resumption* direction (fade of the opening drive, not of the daily tide)
```

**Trigger**
```
retracePct = (sessHigh - close) / (sessHigh - sessLow)   // after an opening rally, for a short
retraced   = retracePct >= vrMinRetrace                  // 1.0 = “100% V”
rejection  = 1m/30m failure to make a new extreme + shift back toward the OR
```

**Entry:** sell stop on the shift back through the open-range edge or through a 1m pivot, in the daily-body direction.  
**Stop:** beyond the V extreme (the session high for a short) + pad.  
**Target:** 1.5R–2R; often dynamically managed.  
**Invalidation:** V fails (new session extreme beyond the stop); or retrace never reaches `vrMinRetrace`.

| Parameter | Default | Tag |
|---|---|---|
| `vrMinRetrace` | `0.80` | INFERRED (1.00 matches his “100% V” example) |

Overlap: can coincide with a Daily Fade or a Zone Reversal. Priority if several setups fire: **Anabolic TCON > Zone Break > Kinetic > V-Reversal > Daily Fade** (INFERRED; fade is explicitly higher-risk).

---

### 5.6 Not specified enough to code as primary setups

| Name | What we know | Tag |
|---|---|---|
| Fake-Fake-Drive | Recap label only (27 Oct 2026, with Anabolic Flow) | INFERRED: double fake-out then a drive. Leave unimplemented until calibrated; optional later pattern: false break of OR, return, false break the other way, then drive. |
| Micro Zarphoid Blast | “A sort of ascending triangle type pattern, a micro zarfoid blast, but without the proper impulse wave leading into it… I don’t trade the 1-minute chart.” — [LONDON EARLY TAKE! MAY 20 2026](https://www.youtube.com/watch?v=YXeEsJ594V8) | SOURCED as a 1m compression that is **not** a standalone setup. Optional flag only if an HTF setup already exists and a 1m rising/falling triangle breaks in the setup direction after an impulse. |
| VWAP reversion | Frequent in 2022–2025 videos; less visible in the Oct–Nov 2026 NAS recaps | Out of scope for v1 unless added as a module |

---

## 6. No-trade filters

Evaluate **before** entries. `hardNoTrade` blocks all new risk. Soft filters block some setups only.

```
// Progressive quiet check: use range so far, not a 2h look-ahead.
rangeSoFarAtr = (sessionHigh - sessionLow) / atrD
quietLondon = inLondon and minsInto >= 60 and minsInto <= 90 and rangeSoFarAtr < 0.15
quietNY     = inNY     and minsInto >= 60 and minsInto <= 90 and rangeSoFarAtr < 0.25

hardNoTrade =
    (inLondon and funcInsideAt(03:00))          // CALIBRATED: London inside-day at the open
    or tinyInsideDay
    or quietLondon or quietNY                   // CALIBRATED progressive sleepy filter
    or (inLondon and (orHigh-orLow) < 0.08*atrD and waitFirst30Done)
    or (inNY and (orHigh-orLow) < 0.15*atrD and waitFirst30Done)
    or (inNY and funcInsideAt(10:30) and (orHigh-orLow) < 0.25*atrD)  // optional NY late-inside
    or messyPath to objective
    or sessionTradeCount >= maxTradesPerSession
    or dayTradeCount >= maxTradesPerDay
    or (energyAlreadyExpressed)                 // don't start a new idea once 2R is in
    // NOT in the hard block (CALIBRATED):
    //   - inTwilight / 11:30 clock (some 2R targets hit until 12:48 ET)
    //   - sisters alignment
    //   - NY funcInsideAt(09:30)
    //   - day of week
```

| Filter | Algorithm | Default | Tag |
|---|---|---|---|
| Inside day (London) | `funcInsideAt(03:00 ET)` | **Skip London** | SOURCED as a no-trade reason; **CALIBRATED** 4/4 inside London opens were no-trade, 0/5 traded |
| Inside day (NY) | `funcInsideAt(09:30)` | **Do not block** at the open. Optional: block if still inside PDR at 10:30 and OR < 0.25 × ATR | **CALIBRATED**: Nov 5, 9, 12, 13 were inside at 09:30 and still traded |
| Tiny / small inside day | `tinyInsideDay` | Soft / additional; the London split that worked was `funcInsideAt(03:00)` | SOURCED label; size cut INFERRED |
| Rangebound / sleepy / barcode | Stand down if range after 60–90 min is still **< 0.15 × ATR14** (London) or **< 0.25 × ATR14** (NY). Progressive, not a 2h look-ahead. | Block new entries; London may later arm kinetic (04:30–08:00) if the morning stays dead then expands | SOURCED language; **CALIBRATED** thresholds (London 11/12 split) |
| Overextension | §2.5; plus late-fade ban | On | SOURCED idea; INFERRED numbers |
| Twilight Zone | `inSess("1130-1400:23456")` | **Not a hard flatten.** Optional: stop *arming new* NY entries after 11:30 unless a target is already close, but **leave working trades on** — 2R hits occurred at 12:00–12:48 ET | SOURCED as a lunch window; **CALIBRATED** no hard 11:30 time stop |
| Sisters alignment | §6.1 | **`sistersMode="off"`** as the v1 default. Optional: ES confirms the *entry bar* direction | SOURCED as something he looks at; **CALIBRATED: not a hard filter**. First-30m NQ/ES/YM alignment was 80% of no-trade sessions vs 40% of traded sessions |
| Max trades / session | `maxTradesPerSession=2`, `maxTradesPerDay=3` | Two in one session is rare and “almost always in New York” | SOURCED “1–3 / day,” “less than one trade a day,” “handful per week”; counts INFERRED |
| Energy expressed | A completed +2R (or any fill that reached target) in this session → `SESSION_DONE` unless user allows a second NY trade | SOURCED “if energy is expressed in the morning, my trading day is done” (session-level) | 
| Messy traffic in the path | `not cleanPath(close, objective)` | Block | SOURCED |
| Manic Monday / Freaky Friday | Optional `cautionMonday=true`, `cautionFriday=true`: raise `bodyRatioMin` and require turbo+naked; do not hard-block | SOURCED as caution labels, not hard bans (he does trade some Fridays) |
| Don’t force Thu/Fri | Optional only; **no hard weekday ban** | SOURCED pinned 10x post; **CALIBRATED** Monday/Friday were mixed (some no-trade, some traded) |
| FOMC / news | Input `newsWindows[]`; if inside, force `mgmtModel` to dynamic (1R or BE) or flatten new entries | SOURCED “dynamically managed on FOMC day” (28 Oct 2026); calendar is INFERRED / user-supplied |
| Extended overnight rally into London | If London and `isExtendedUp` already from Asia, block London TCON longs (11 Nov 2026 recap) | SOURCED as a no-trade reason; reuse §2.5 |

### 6.1 Sisters alignment

> “The other screen I look at is the three sisters — that’s the Nasdaq, the S&P in the middle, and the Dow on the right… I look for synchronicity… relative strength.”  
> — [FLASH!! MY TRADING GRID!!!](https://www.youtube.com/watch?v=O8Qgxou6yIE) **SOURCED**

**Algorithm (INFERRED numeric)**
```
For each of NQ, ES, YM, in the current session:
  side =  1 if close > that symbol’s session OR mid (or session open if OR not ready)
        -1 if close < …
         0 if inside that symbol’s OR

aligned_long  = count(side == 1) meets sistersMode
aligned_short = count(side == -1) meets sistersMode
sistersBreak  = intended side is 1 (long) and (ES or YM) side == -1
                and that sister is making a session extreme against the trade
```

| Parameter | Default | Tag |
|---|---|---|
| `sistersMode` | `"off"` | **CALIBRATED** default. Optional `"entryBar"` (ES same direction as the NQ entry bar) or `"2of3"` / `"all"` for sweeps. Do **not** require first-30m alignment. |
| ES/YM TF | 30-minute + their own session OR | INFERRED |

**Pine:** `request.security(symbolEs, "1", close)` etc. for location; build a parallel OR on each sister (same session strings). Watch for gaps when a sister is in a different halt/session.

---

## 7. Risk and management models

### 7.1 R and position sizing

> “If you have a trading account of $10,000 and you’re comfortable risking 1% on a trade, your R-Value for that trade would be $100… profit target is $200… R-Multiple = 2.”  
> — [R-VALUES & R-MULTIPLES IN TRADING!](https://buymeacoffee.com/zarillionc2/r-values-r-multiples-in-trading) **SOURCED**

Pinned Telegram “Mathematics of 10x”: 1R = 1% of account, **recalculate 1R each Monday**, ~4.5R/week is an **average not a quota**. **SOURCED**.

```
riskPct      = 0.01
rCash        = equity * riskPct          // equity as of Monday open if recalcMonday=true
stopDist     = math.abs(entry - stop)
pointValue   = syminfo.pointvalue
qty          = math.floor(rCash / (stopDist * pointValue))
qty          = math.max(qty, 0)
```

| Parameter | Default | Tag |
|---|---|---|
| `riskPct` | `0.01` | SOURCED |
| `recalcMonday` | `true` | SOURCED |
| `pyramiding` | `0` (one working idea per session; a second NY trade is a new R, only if `maxTradesPerSession` allows) | INFERRED |

Use `strategy.equity` or a fixed `input.float` backtest account. For NQ, one point = 4 ticks = $20; reject the trade if `qty < 1` and do not widen the stop to force size. Optional: auto-switch to MNQ if `qty==0` on NQ.

### 7.2 Four models

Zar shows four parallel models on recap videos and says “all four models fully profitable.” **SOURCED** — [TCON MASTERCLASS! TIMING THE ENTRY!](https://www.youtube.com/watch?v=JswxAGbsCs8) and many others.

| ID | Model | Exit | Tag |
|---|---|---|---|
| A | 1R all-or-nothing | Full qty at `entry + 1R`; if stop hits first, −1R | SOURCED |
| B | 1.5R all-or-nothing | Full qty at `entry + 1.5R` | SOURCED |
| C | 2R all-or-nothing | Full qty at `entry + 2R`; if price dies first, −1R | SOURCED |
| D | 2R, stop to break-even at +1R | At `entry + 1R`, move stop to entry (or entry+1 tick). Final is +2R or 0R | SOURCED; also [THE POWER OF BREAK-EVEN!](https://buymeacoffee.com/zarillionc2/the-power-of-break-even) |

**Implementation options**
1. **Research mode:** run all four as virtual tickets (same entry/stop, four P&L streams). Matches his teaching tables.  
2. **Live / posted-result mode:** `mgmtModel = "C"` default (most recaps are +2.00R).  
3. **Dynamic:** if `inTwilight or inNews or not inOptWindow or kineticWindow`, use A or B (`dynamicTargetR = 1.0`). **SOURCED** behavior; switch rule **INFERRED**.

Count a target/stop only when price **crosses** the level (`high > t2` / `low < stop` for longs), not a same-bar tag on a higher TF. **SOURCED**.

Do not trail beyond the model definition in v1 (he “dances” stops; that is not specified enough). Optional later: trail to last 1m pivot after +1.5R.

---

## 8. Strategy architecture (Pine v6)

### 8.1 Indicator vs strategy

Build in two layers that share one library of functions:

1. **Indicator** (`indicator(..., overlay=true)`): daily bias, OR boxes, zones, turbo/naked markers, session background, sisters dots, setup state, and signal markers. This is the visual “GRID.”  
2. **Strategy** (`strategy(..., overlay=true, process_orders_on_close=false, pyramiding=0, calc_on_every_tick=false, commission_type=…, slippage=…)`): consumes the same functions, places stop entries, applies a management model, logs setup IDs.

Do not start with a strategy-only script: you need to *see* zones and OR before trusting fills. `calc_on_every_tick=false` is the conservative default; stop orders still fill intra-bar in a strategy when `process_orders_on_close=false`.

Recommended chart: **1-minute NQ**, regular trading hours off (use 24h futures). `extended_hours` as needed so 18:00–03:00 Asia exists.

### 8.2 Inputs list (defaults)

```
// Symbols
primary, es, ym

// Sessions
tz="America/New_York"
sessAsia, sessLondon, sessLondonOpt, sessNY, sessNYOpt, sessTwilight   // §1.3 defaults

// Daily tide
bodyRatioMin=0.55, tinyAtrMult=0.55, insideMode="range"
emaDailyLen=200, ema200BandAtr=0.15
emaFast=9, emaSlow=21, atrLen=14
extAtr30=1.8, extAtrD=1.4, lateFadeAtr=1.2

// Open range
orMinutes=30, orExpandMinutes=90, usePremarketOR=true, orPadPoints=0

// Zones / traffic / naked
zoneLookback30=64, zoneClusterAtr=0.25, zonePadAtr=0.10, zoneMinTouches=2, zoneMaxCount=12
trafficLookback=50, trafficMaxOverlaps=4, turboMaxOverlaps=2
nakedLookback=50, nakedMinAtr=0.40, nakedBodyRatioMin=0.50, nakedFillMax=0.50

// Setups on/off
useTcon=true, useZoneBreak=true, useFade=true, useKinetic=true, useVReversal=true
useFibTcon=false, useZarphoidFlag=false, useFakeFakeDrive=false   // off until calibrated

// TCON / fade / ZB / kinetic / VR parameters: as in §5
londonTargetR=1.5, fadeTargetR=1.5, kineticTargetR=1.0, vrMinRetrace=0.80

// Stops / entry (CALIBRATED)
swingLookback=15, stopPadPoints=2.0, entryPadTicks=1
maxRiskAtr=0.18, typRiskAtr=0.13
// NY stop ≈ 0.45 × OR, London ≈ 0.8 × OR (informational)

// Fade enable (CALIBRATED, 2 samples)
pdRangeAtrMin=2.0, ema200DistPctMin=0.04

// Filters
sistersMode="off"          // CALIBRATED: not a hard filter; alts "entryBar" | "2of3" | "all"
maxTradesPerSession=2, maxTradesPerDay=3
cautionMonday=false, cautionFriday=false, softEndOfWeek=false  // no hard weekday ban
londonInsideBlocks=true    // CALIBRATED: funcInsideAt(03:00)
nyInsideBlocksAtOpen=false // CALIBRATED: do not block NY at 09:30
quietMins=60, quietMinsEnd=90
quietAtrLondon=0.15, quietAtrNY=0.25
minOrAtrLondon=0.08, minOrAtrNY=0.15
hardTwilightFlatten=false  // CALIBRATED: some 2R hits until 12:48 ET

// Risk
riskPct=0.01, recalcMonday=true
mgmtModel="C"              // A | B | C | D | ALL
dynamicTargetR=1.0
```

### 8.3 State machine (per session)

```
enum SessState
    IDLE
    PRESESSION_MAP      // Asia; build/refresh zones before 03:00 (and again before 09:30)
    WAIT_FIRST_30
    SCAN
    IN_TRADE
    MANAGE
    KINETIC_WATCH       // opt window was dead; window expanded
    TWILIGHT_WATCH      // lunch window: optional no *new* arms; do NOT flatten working trades
    SESSION_DONE

Transitions (session = London or NY, independently):
  session start            → WAIT_FIRST_30 (after a short PRESESSION_MAP)
  minsInto >= orMinutes    → SCAN
  setup+trigger+entry sent → IN_TRADE
  filled                   → MANAGE
  trade closed, count < max and inOptWindow → SCAN
  trade closed and energy expressed (hit >= 2R, or policy) → SESSION_DONE
  opt window ends with no fill and morning dead → KINETIC_WATCH
  opt window ends with energy expressed → SESSION_DONE
  11:30 → TWILIGHT_WATCH (CALIBRATED: do not flatten; some 2R targets hit 12:00–12:48 ET)
  14:00 from TWILIGHT_WATCH → SCAN (post-TZ bracket break only, optional v2) or SESSION_DONE
  session end              → IDLE (persist daily counters)

SETUP_PRIORITY if multiple true: TCON_ANABOLIC > ZONE_BREAK > KINETIC > V_REVERSAL > DAILY_FADE
```

### 8.4 Skeleton outline (not a full script)

```pine
//@version=6
strategy("Razar's Edge v1", overlay = true, pyramiding = 0,
     initial_capital = 100000, commission_type = strategy.commission.cash_per_contract,
     commission_value = 2.0, slippage = 1, process_orders_on_close = false,
     margin_long = 100, margin_short = 100)

// 1) inputs  (§8.2)
// 2) session flags, minsInto, new30, newD  (§1)
// 3) request.security daily + 30m + ES/YM  (§1–2, §6.1)
// 4) daily tide: span, body, inside, ema200, extension  (§2)
// 5) maintain OR + premarket H/L  (§3)
// 6) on new30: push OHLC to arrays; rebuild zones; update naked fill; tag turbo  (§4)
// 7) sisters OR + alignment  (§6.1)
// 8) session state machine  (§8.3)
// 9) evaluate setups in priority order; if canEnter and not hardNoTrade, arm stop  (§5)
// 10) on fill: compute qty from 1% / stopDist; attach exits for mgmtModel  (§7)
// 11) plot boxes (OR, zones), labels (bias, state, setup id), bg color by session
// 12) debug table: bias, OR, insideDay, ext, sisters, state, last setup

// Exits for model C:
// strategy.exit("C", from_entry="Long", stop=stopPx, limit=entryPx + 2*R)
// Model D: when high crosses entry+R, strategy.exit(... stop=entryPx, limit=entryPx+2*R)
```

UDTs to declare:
```
type Zone
type Sister
type SetupSignal   // id, side, entry, stop, targetR, armed
type SessMem       // orHigh, orLow, tradeCount, energyExpressed, state, sessStart
```

Keep 30m history in `array<float>` for `h30Hist`, `l30Hist`, `o30Hist`, `c30Hist` (length `max(zoneLookback30, trafficLookback, nakedLookback)`).

### 8.5 Repaint / lookahead rules

- Arm Zone Break entries only after the signal 30m bar is **closed**.
- Daily “developing” values may change intra-day (that is realistic). Prior-day span must be `high[1]/low[1]`.
- Do not `request.security("30", close)` as a trigger without gating on `timeframe.change("30")`.
- Strategy tester fills stop orders intra-bar; still require the 1m shift condition on a **closed** 1m bar before placing the stop (or place it at the close of the shift bar).

---

## 9. Open questions / hidden parts and calibration

### 9.1 Still hidden (do not pretend to have coded these)

1. Exact turbo-zone geometry and “weak vs strong” zone feel.  
2. Official naked-body fill rule (we provided a proxy).  
3. Key Factors / Units of Conviction weights (which boxes are mandatory).  
4. “Juice” (3 Nov 2026 fade had structure and still lost).  
5. Fake-Fake-Drive and official Zarphoid rules.  
6. How he chooses among the four R models in live trading.  
7. Discretionary “dance” (cancel/replace stops, “I don’t like what I’m seeing”).  
8. VIP power sheets (dynamic OR “cool zone,” kinetic sheet, fake-out checklist).  
9. 200 EMA, “Gladiator” candles, wick-fill — context labels without formal rules.  
10. Exact sister-alignment definition.  
11. Contract, slippage, and padding he actually uses.

### 9.2 Calibration protocol and current results

A first reconstruction against 1-minute NQ already exists: `/workspace/zar_backtest_recon.md` (data in `/workspace/zar_data/`, 21 Oct–19 Nov 2026). **Use those CALIBRATED defaults as v1.** Further sweeps should start from them, not from the earlier INFERRED numbers.

**Timestamp reminder:** `/workspace/zar_trades_raw.md` post times are **Pacific**. Convert to ET before comparing to session clocks or to the reconstruction (which is in ET).

The reconstruction is a **qualitative / session-level** benchmark, not a fill log. He does not publish entry or stop prices. On most winning days, 30–80% of candidate entries in the posted direction also won. Rule P is a proxy.

**What already worked (do not un-learn this):**

- **Rule P** (first 1m close beyond OR after the first 30m, stop = 15-bar swing + 2 pts) reproduced **12 of 22** posted outcomes, including the 3 Nov −1R session-high long (entry 10:56 ET at 28393, swing stop 28324, stopped 11:22 ET, never +1R).
- Direction fit the tape: in traded sessions, 50% of same-side candidates reached the posted R before the stop vs 26% on the opposite side. In no-trade sessions the better side only reached ~35–39%.
- **London `funcInsideAt(03:00)` → no trade** was a clean in-sample split (4/4 vs 0/5).
- **Quiet London:** first-2h range ≥ 0.22 × ATR on every traded London session; ≤ 0.19 × ATR on every no-trade London except Nov 9 (already inside). Code the progressive 60–90 min / 0.15 × ATR check so you do not peek at the full 2h.
- **NY inside-at-09:30 must not block** (Nov 5, 9, 12, 13 traded and won).
- **Sisters first-30m alignment is not a hard filter** (80% of no-trade vs 40% of traded).
- **No hard 11:30 flatten** (2R hits at 12:00–12:48 ET on 21 Oct, 22 Oct, 11 Nov).
- **Do not use a 30m signal-candle extreme as the stop** (too wide; 2R rarely reached).

**Pass bar for later sweeps (still applies):**

- Start from the CALIBRATED input set in §0.1 / §8.2.
- ≥ 80% session-level agreement on fire vs no-fire, and on side when it fires, for the tables below.
- 18 Nov London is a pass only if the first window is quiet and #2 is a kinetic short (or late-London re-open 04:30–08:00).
- 3 Nov NY long −1R: a fire on the long side is **acceptable** (the reconstruction reproduced the loss). Use it to design a v2 “juice” filter without killing 6 Nov London fade.
- If a labelled no-trade session fires, tighten filters before loosening entries to catch missed trades.
- Do not optimize for his advertised win rate. Optimize session agreement first, then whether a 2R target with the 15-bar/+2 pt stop was reachable.
- Sample is small (20 traded / 10 no-trade / 13 unposted sessions excluded). Treat every threshold as a TradingView starting point, not a fitted law. The raw log may have gaps (e.g. 29–30 Oct, 2 and 4 Nov, many October Londons).

**Zone / turbo / naked** were not in the reconstruction. Adding them should be the first v2 experiment, especially on Low-confidence retest and dynamically-managed days (28 Oct FOMC +1R, 23 Oct +1R, 18 Nov NY +1R), where Rule P failed.

#### Days the rules should fire (side / session / expected setup)

| Date (2026) | Session | Side | Posted result | Expected setup family | Recon note |
|---|---|---|---|---|---|
| 21 Oct | NY | long | +2.00R | Anabolic TCON | 2R hit after 11:30 (no hard TZ flatten) |
| 22 Oct | London | short | +2.00R | Anabolic TCON | Low-confidence small-stop candidate in the recon; keep as a fire-day |
| 22 Oct | NY | short | +2.00R | Anabolic TCON | 2R hit after 11:30 |
| 27 Oct | London | long | +0.5R (dynamic, TZ / zone reversal) | Zone reversal / kinetic-ish | DST week (London cash 04:00 ET); target may be model A, not C |
| 27 Oct | NY | long | +2.00R | Anabolic TCON (Fake-Fake-Drive uncoded) | TCON/ZB should still allow a long |
| 5 Nov | NY #1 | short | +2.00R | Anabolic TCON | Freefall; many entries would have won |
| 5 Nov | NY #2 | short | +2.00R | Momentum TCON | Needs `maxTradesPerSession>=2` |
| 13 Nov | NY | short | +2.00R | Anabolic TCON (daily 200 EMA tag) | London that day must stay flat (inside / Friday) |
| 17 Nov | London | short | +2.00R | Anabolic TCON; wait first 30m | Rule P matched (High) |
| 17 Nov | NY | short | +2.00R | Anabolic TCON | Rule P matched (High) |
| 18 Nov | London #2 | short | +2.00R | Stored Kinetic Energy | First London post = no trade; then late re-open |
| 18 Nov | NY | short | +1.00R | Open-Range V-Reversal | Rule P did **not** reproduce (Low); do not overfit Rule P to this day |
| 19 Nov | NY | short | +2.00R | Daily Fade (topping tail) | Low uniqueness (shorts ≈ longs in the 2h window); London that day must stay flat |

#### Sessions that must *not* fire (hard no-trade)

| Date | Session | Stated reason | Filter that should catch it |
|---|---|---|---|
| 19 Nov | London | Rangebound sleepy | Quiet filter (range after 60–90 min < 0.15 × ATR) |
| 18 Nov | London (first window) | Sleepy rangebound | Quiet filter, then **arm kinetic** 04:30–08:00 (do not hard-end the day) |
| 16 Nov | London + NY | Functional inside day; manic Monday chop | London: `funcInsideAt(03:00)`. NY: quiet / chop — not a weekday ban |
| 13 Nov | London | Freaky Friday no-trade | `funcInsideAt(03:00)` (also a Friday, but Friday is not a hard ban) |
| 12 Nov | London | Tiny inside day / rangebound | `funcInsideAt(03:00)` and/or quiet filter |
| 11 Nov | London | Extended overnight rally | Extended-into-London / quiet (OR ~0.07 × ATR); 2h range 0.11 × ATR |
| 10 Nov | London + NY | Tiny / small inside day, sleepy | London: `funcInsideAt(03:00)`. NY: still inside PDR after 2h / small OR |
| 9 Nov | London | Manic Monday, inside day, rangebound 30m | `funcInsideAt(03:00)` (this one was the sleepy-filter exception — catch it with the inside-day rule) |
| 6 Nov | NY | Down day / rangebound after a London fade win | `SESSION_DONE` after the London fade, or NY rangebound; do not TCON long NY |

**Useful non-pass/fail cases**

- **3 Nov NY long −1R** (Daily Fade / Zone Break / “no juice”): Rule P **should fire long** and lose. That is a success for v1. A v2 juice filter may try to skip it without skipping 6 Nov London fade (that one won; pd range 2.49 × ATR).
- **28 Oct NY short +1R** FOMC: if a news window is supplied, expect dynamic 1R, not a forced 2R. Rule P did not reproduce this Low-confidence day.
- **6 Nov London long +2R** fade: should fire under the CALIBRATED fade gate; NY later that day must not.

#### Sweep order (now that Rule P is calibrated)

1. Freeze the §0.1 CALIBRATED set (sessions, OR=30m, Rule P, 15-bar/+2 pt stop, 0.18 × ATR cap, London inside, progressive quiet filter, sisters off, no 11:30 flatten). Re-run on NQ 1m as a Pine parity check against `/workspace/zar_backtest_recon.md`.
2. Add zone / turbo / naked overlays and see whether Low-confidence / dynamically-managed days improve without breaking no-trade days.
3. Sweep only fade thresholds around `pdRangeAtrMin=2.0` and `ema200DistPctMin=0.04` (2 samples).
4. Only then touch `mgmtModel` / targets, or a soft (not hard) twilight “no new arms after 11:30.”
5. Log every session: `{date, session, state, setup, side, orWidth, funcInside, range60, ext, sisters (informational), fired?}`.

### 9.3 Source index

- YouTube channel: https://www.youtube.com/@zarilliontrading  
- X: https://x.com/ZarillionTrades  
- Free Telegram: https://t.me/Zarillion_Trading  
- BMC: https://buymeacoffee.com/zarillionc2  
- Core videos already cited in `/workspace/zar_strategy.md` (dynamic OR `K12mXxKusHU`, TCON definition `DMVlkFkkvaU`, clean traffic `Cm_AeaMM63Y`, zones `CY130H-PFb4`, kinetic `UrY4v_cu22Q` / `g8PUCU4eF_0`, zone break `aPjfQhONB34`, fade `5_hNGl7cCH4` / `9j-Hqmm9Ylg`, stops `IGnfcfMmt3A`, twilight `DixL7iVZ00w`, grid `O8Qgxou6yIE`).  
- Local: `/workspace/zar_strategy.md`, `/workspace/zar_trades_raw.md`, `/workspace/zar_research/`.

---

*End of spec. Next build step: Pine v6 indicator for sessions, OR, daily tide, and zone overlays only — no orders — then add TCON signals, then the strategy wrapper.*
