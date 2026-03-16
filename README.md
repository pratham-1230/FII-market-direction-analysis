# FII Derivatives Positioning → Nifty 50 Market Direction

**Author:** Pratham Rathod  
**Background:** BCA Data Analytics | CFA Level 1 Candidate  
**Contact:** prathamrathod345@gmail.com | [LinkedIn](https://www.linkedin.com/in/pratham-rathod-b9a413220)

---

## Why I Built This

While studying derivatives for my CFA exam, I kept reading about how FII flows drive Indian markets. Everyone says it — analysts, news anchors, fund managers. But I wanted to actually test it with data rather than just take it at face value.

NSE publishes FII derivatives positioning data every single day for free. I figured if this data is really as significant as people claim, it should show up in the numbers. So I built a system to find out.

The core question I was trying to answer:

> *When FIIs are heavily net long on Nifty futures, does the market actually go up over the next few weeks?*

---

## What I Did

I pulled 3 years of daily data — Nifty 50 prices from Yahoo Finance and FII positioning from NSE archives. The idea was simple: rank FII net long contracts relative to the past year, and see if extreme positioning (top or bottom 30%) tells you anything useful about where the market is heading.

I used a rolling percentile window rather than a fixed threshold so the signal adapts to changing market conditions and doesn't peek into the future.

Three things I calculated for each signal:
- Average forward return over 5, 10, and 20 trading days
- Hit rate — how often the market actually moved in the predicted direction
- Whether the difference was statistically significant or just noise

---

## What I Found

| Signal | 20-Day Avg Return | Hit Rate |
|--------|-------------------|----------|
| Bullish (FII heavily long) | 1.3% | 66.4% |
| Neutral | ~1.3% | ~52% |
| Bearish (FII heavily short) | 1.89% | ~48% |
| Base rate (all days) | 1.36% | — |

The bullish signal had a **66.4% hit rate** — meaning when FIIs were heavily net long, Nifty went up 2 out of every 3 times over the following month. That's a decent edge.

However — and this is important — the result was **not statistically significant** at the 5% level. So I can't say with confidence this isn't a random pattern. Three years of data is honestly not enough to make strong claims. I'd need closer to 10 years to be sure.

What I can say is: the directional pattern exists, and a 66% hit rate is practically useful even if not statistically confirmed yet.

---

## What I'd Do Differently

A few things I'd improve with more time:

- Get properly parsed NSE data instead of relying on the archive format which had parsing issues
- Test on a longer dataset — ideally 2010 to present
- Combine this signal with other macro factors like RBI rate decisions and FII equity flows to see if a composite signal performs better
- Do walk-forward testing instead of optimising thresholds on the full dataset

---

## How to Run It

```bash
git clone https://github.com/pratham-1230/FII-market-direction-analysis.git
cd FII-market-direction-analysis
pip3 install yfinance pandas numpy matplotlib seaborn scipy
python3 project6_fii.py
```

Charts will be saved in the `charts/` folder. Terminal output shows all the key numbers.

---

## Files

```
project6_fii.py         — main analysis (run this)
download_fii_data.py    — pulls FII data from NSE archives
data/fii_combined.csv   — the dataset used
charts/                 — output visualisations
```

---

## CFA Connection

This project ended up being a good supplement to my CFA studying. Building it forced me to actually understand futures open interest, not just memorise the definition. The backtesting section required applying hypothesis testing and thinking carefully about what statistical significance actually means — which is something I'd been fuzzy on before.
