"""
PROJECT 6: FII Derivatives Positioning → Nifty Market Direction
Author: Pratham Rathod
Run with: python3 project6_fii.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Works without display
import seaborn as sns
from scipy import stats
from pathlib import Path

print("=" * 55)
print("PROJECT 6: FII Positioning → Market Direction")
print("Author: Pratham Rathod")
print("=" * 55)

# ── LOAD DATA ──
print("\nLoading data...")
import yfinance as yf

nifty = yf.download('^NSEI', start='2022-01-01', end='2024-12-31', progress=False)
nifty = nifty[['Close']].copy()
nifty.columns = ['nifty_close']
nifty['daily_return'] = nifty['nifty_close'].pct_change() * 100
nifty['fwd_5d']  = nifty['nifty_close'].pct_change(5).shift(-5)  * 100
nifty['fwd_10d'] = nifty['nifty_close'].pct_change(10).shift(-10) * 100
nifty['fwd_20d'] = nifty['nifty_close'].pct_change(20).shift(-20) * 100
nifty.dropna(inplace=True)
print(f"Nifty data: {len(nifty)} days")

# Load FII data
fii = pd.read_csv('data/fii_combined.csv', parse_dates=['date'])
fii.set_index('date', inplace=True)

# Merge
df = nifty.join(fii, how='inner').dropna()
print(f"Combined: {len(df)} observations")
print(df.head())

# ── BUILD SIGNAL ──
print("\nBuilding signal...")
LOOKBACK  = 252
UPPER_PCT = 70
LOWER_PCT = 30

df['fii_percentile'] = df['fii_net_long'].rolling(LOOKBACK).rank(pct=True) * 100
df['signal'] = 0
df.loc[df['fii_percentile'] >= UPPER_PCT, 'signal'] =  1
df.loc[df['fii_percentile'] <= LOWER_PCT, 'signal'] = -1
df.dropna(inplace=True)

counts = df['signal'].value_counts()
print(f"Bullish days:  {counts.get(1,0)}")
print(f"Neutral days:  {counts.get(0,0)}")
print(f"Bearish days:  {counts.get(-1,0)}")

# ── BACKTEST RESULTS ──
print("\n=== BACKTEST RESULTS ===")
results = {}
for horizon, col in [('5d', 'fwd_5d'), ('10d', 'fwd_10d'), ('20d', 'fwd_20d')]:
    bull = df[df['signal'] ==  1][col].dropna()
    bear = df[df['signal'] == -1][col].dropna()
    base = df[col].dropna()
    t, p = stats.ttest_ind(bull, base)
    results[horizon] = {
        'Bullish Avg%': round(bull.mean(), 2),
        'Bearish Avg%': round(bear.mean(), 2),
        'Base Rate%':   round(base.mean(), 2),
        'Bull Hit Rate': f"{(bull>0).mean()*100:.1f}%",
        'Bear Hit Rate': f"{(bear<0).mean()*100:.1f}%",
        'P-Value': round(p, 4),
        'Significant': 'YES' if p < 0.05 else 'NO'
    }
    print(f"\n{horizon} Forward Return:")
    for k, v in results[horizon].items():
        print(f"  {k}: {v}")

# ── STRATEGY PERFORMANCE ──
print("\n=== STRATEGY PERFORMANCE ===")
bt = df[['daily_return', 'signal']].copy().dropna()
bt['signal_lag'] = bt['signal'].shift(1)
bt['strat_return'] = np.where(bt['signal_lag'] == 1, bt['daily_return'], 0)
bt['cum_bh']   = (1 + bt['daily_return']/100).cumprod() - 1
bt['cum_strat'] = (1 + bt['strat_return']/100).cumprod() - 1

def sharpe(r):
    excess = r/100 - 0.065/252
    return round(excess.mean() / excess.std() * np.sqrt(252), 3) if excess.std() > 0 else 0

print(f"Buy & Hold Total Return:    {bt['cum_bh'].iloc[-1]*100:.1f}%")
print(f"FII Strategy Total Return:  {bt['cum_strat'].iloc[-1]*100:.1f}%")
print(f"Buy & Hold Sharpe:          {sharpe(bt['daily_return'])}")
print(f"FII Strategy Sharpe:        {sharpe(bt['strat_return'])}")
print(f"Days in market (strategy):  {int((bt['signal_lag']==1).sum())}/{len(bt)}")

# ── CHARTS ──
print("\nGenerating charts...")
Path("charts").mkdir(exist_ok=True)
plt.style.use('dark_background')

# Chart 1: FII vs Nifty
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
ax1.plot(df.index, df['nifty_close'], color='#38BDF8', linewidth=1.5)
ax1.set_title('Nifty 50 vs FII Net Long Positioning', fontsize=14, fontweight='bold')
ax1.set_ylabel('Nifty Level')
ax1.grid(alpha=0.2)
colors = ['#10B981' if x > 0 else '#EF4444' for x in df['fii_net_long']]
ax2.bar(df.index, df['fii_net_long'], color=colors, alpha=0.7, width=1)
ax2.axhline(0, color='white', linewidth=0.8, linestyle='--')
ax2.set_ylabel('FII Net Long Contracts')
ax2.grid(alpha=0.2)
plt.tight_layout()
plt.savefig('charts/chart1_fii_vs_nifty.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 1 saved.")

# Chart 2: Returns by signal
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
for ax, (horizon, col) in zip(axes, [('5 Days','fwd_5d'),('10 Days','fwd_10d'),('20 Days','fwd_20d')]):
    avgs = [df[df['signal']==1][col].mean(),
            df[df['signal']==0][col].mean(),
            df[df['signal']==-1][col].mean()]
    bars = ax.bar(['Bullish', 'Neutral', 'Bearish'], avgs,
                  color=['#10B981','#64748B','#EF4444'], alpha=0.85, width=0.5)
    ax.axhline(df[col].mean(), color='#F59E0B', linestyle='--', linewidth=1.5,
               label=f'Base: {df[col].mean():.2f}%')
    ax.set_title(f'Forward {horizon}', fontweight='bold')
    ax.set_ylabel('Avg Return (%)')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.2, axis='y')
    for bar, val in zip(bars, avgs):
        ax.text(bar.get_x()+bar.get_width()/2,
                bar.get_height() + (0.05 if val >= 0 else -0.15),
                f'{val:.2f}%', ha='center', fontweight='bold', fontsize=10)
plt.suptitle('Nifty Returns by FII Signal Regime', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('charts/chart2_signal_returns.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 2 saved.")

# Chart 3: Cumulative returns
fig, ax = plt.subplots(figsize=(16, 7))
ax.plot(bt.index, bt['cum_bh']*100,    color='#64748B', linewidth=1.5, label='Buy & Hold Nifty')
ax.plot(bt.index, bt['cum_strat']*100, color='#38BDF8', linewidth=2,   label='FII Signal Strategy')
ax.fill_between(bt.index, bt['cum_strat']*100, bt['cum_bh']*100,
                where=bt['cum_strat']>=bt['cum_bh'], alpha=0.15, color='#10B981')
ax.fill_between(bt.index, bt['cum_strat']*100, bt['cum_bh']*100,
                where=bt['cum_strat']<bt['cum_bh'],  alpha=0.15, color='#EF4444')
ax.set_title('Cumulative Returns: FII Strategy vs Buy & Hold', fontsize=14, fontweight='bold')
ax.set_ylabel('Cumulative Return (%)')
ax.legend(fontsize=11)
ax.grid(alpha=0.2)
ax.axhline(0, color='white', linewidth=0.5)
plt.tight_layout()
plt.savefig('charts/chart3_cumulative.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 3 saved.")

# Chart 4: Distribution
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for ax, (horizon, col) in zip(axes, [('5d','fwd_5d'),('10d','fwd_10d'),('20d','fwd_20d')]):
    bull_r = df[df['signal']==1][col].dropna()
    bear_r = df[df['signal']==-1][col].dropna()
    ax.hist(bull_r, bins=25, alpha=0.6, color='#10B981', label=f'Bullish n={len(bull_r)}', density=True)
    ax.hist(bear_r, bins=25, alpha=0.6, color='#EF4444', label=f'Bearish n={len(bear_r)}', density=True)
    ax.axvline(bull_r.mean(), color='#10B981', linestyle='--', linewidth=2)
    ax.axvline(bear_r.mean(), color='#EF4444', linestyle='--', linewidth=2)
    ax.axvline(0, color='white', linewidth=0.8, alpha=0.5)
    ax.set_title(f'{horizon} Distribution', fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.2)
plt.suptitle('Return Distribution: Bullish vs Bearish Regimes', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('charts/chart4_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Chart 4 saved.")

print("\n" + "="*55)
print("ALL DONE!")
print("="*55)
print("\nCharts saved in: charts/")
print("  chart1_fii_vs_nifty.png")
print("  chart2_signal_returns.png")
print("  chart3_cumulative.png")
print("  chart4_distribution.png")
print("\nOpen these PNG files to see your results.")
print("\nYOUR KEY FINDINGS TO NOTE DOWN:")
r20 = results['20d']
print(f"  Bullish signal 20d avg return: {r20['Bullish Avg%']}%")
print(f"  Bearish signal 20d avg return: {r20['Bearish Avg%']}%")
print(f"  Base rate 20d avg return:      {r20['Base Rate%']}%")
print(f"  Statistically significant:     {r20['Significant']}")
print(f"  Bull hit rate:                 {r20['Bull Hit Rate']}")
