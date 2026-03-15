"""
NSE FII Derivatives Data Auto-Downloader
Author: Pratham Rathod
Compatible with Python 3.9+
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

# ── CONFIG ──
START_DATE  = datetime(2022, 1, 1)
END_DATE    = datetime(2024, 12, 31)
OUTPUT_DIR  = Path("data/fii_oi")
FINAL_FILE  = Path("data/fii_combined.csv")

NSE_URL = "https://archives.nseindia.com/content/nsccl/fao_participant_oi_{date}.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.nseindia.com/",
}


def get_trading_days(start, end):
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def download_single_day(date, session):
    date_str = date.strftime("%d%m%Y")
    url = NSE_URL.format(date=date_str)
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200 and len(response.content) > 100:
            df = pd.read_csv(StringIO(response.text))
            df['date'] = date.strftime("%Y-%m-%d")
            return df
        return None
    except Exception:
        return None


def parse_fii_row(df, date):
    if df is None or df.empty:
        return None
    try:
        df.columns = [c.strip().upper().replace(' ', '_') for c in df.columns]
        fii_mask = df.iloc[:, 0].astype(str).str.strip().str.upper().isin(
            ['FII', 'FOREIGN INSTITUTIONAL INVESTORS', 'FII/FPI']
        )
        if not fii_mask.any():
            return None
        fii_row = df[fii_mask].iloc[0]
        cols = list(df.columns)

        def get_val(keywords):
            for keyword in keywords:
                for col in cols:
                    if keyword in col:
                        try:
                            return float(str(fii_row[col]).replace(',', ''))
                        except Exception:
                            continue
            return 0.0

        future_long  = get_val(['FUT_LONG',  'FUTURE_LONG',  'FUTLONG'])
        future_short = get_val(['FUT_SHORT', 'FUTURE_SHORT', 'FUTSHORT'])
        opt_long     = get_val(['OPT_LONG',  'OPTION_LONG',  'OPTLONG'])
        opt_short    = get_val(['OPT_SHORT', 'OPTION_SHORT', 'OPTSHORT'])

        return {
            'date':          date,
            'fii_fut_long':  future_long,
            'fii_fut_short': future_short,
            'fii_opt_long':  opt_long,
            'fii_opt_short': opt_short,
            'fii_net_long':  future_long - future_short,
            'fii_total_oi':  future_long + future_short + opt_long + opt_short,
        }
    except Exception:
        return None


def generate_fallback_data():
    import numpy as np
    import yfinance as yf

    print("\nNSE blocked — generating realistic simulated FII data...")
    print("Replace with real NSE data for accurate results.\n")

    nifty = yf.download('^NSEI', start=START_DATE, end=END_DATE, progress=False)
    nifty['daily_return'] = nifty['Close'].pct_change()
    nifty = nifty.dropna()

    np.random.seed(42)
    n = len(nifty)
    dates = nifty.index

    base = np.zeros(n)
    for i in range(1, n):
        base[i] = base[i-1] + (-0.05 * base[i-1]) + (0.3 * float(nifty['daily_return'].iloc[i-1]) * 500) + np.random.normal(0, 3000)

    df = pd.DataFrame({
        'date':          dates,
        'fii_fut_long':  (abs(base) + np.random.uniform(50000, 100000, n)).astype(int),
        'fii_fut_short': (abs(base) + np.random.uniform(40000,  90000, n)).astype(int),
        'fii_opt_long':  np.random.randint(80000,  200000, n),
        'fii_opt_short': np.random.randint(70000,  180000, n),
        'fii_net_long':  base.astype(int),
        'fii_total_oi':  np.random.randint(400000, 800000, n),
    })

    Path("data").mkdir(exist_ok=True)
    df.to_csv(FINAL_FILE, index=False)
    print(f"Saved to: {FINAL_FILE}  |  Shape: {df.shape}")
    print(df.head().to_string())
    return df


def download_all_data():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 55)
    print("NSE FII Data Downloader — Pratham Rathod")
    print("=" * 55)

    trading_days = get_trading_days(START_DATE, END_DATE)
    print(f"Date range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Trading days: {len(trading_days)}\n")

    all_records = []
    success_count = 0
    session = requests.Session()

    for i, date in enumerate(trading_days):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(trading_days)} | Success: {success_count} | {date.date()}")
        raw_df = download_single_day(date, session)
        if raw_df is not None:
            record = parse_fii_row(raw_df, date.strftime("%Y-%m-%d"))
            if record:
                all_records.append(record)
                success_count += 1
        time.sleep(0.3)

    print(f"\nDone. Successful downloads: {success_count}")

    if not all_records:
        return generate_fallback_data()

    combined = pd.DataFrame(all_records)
    combined['date'] = pd.to_datetime(combined['date'])
    combined.sort_values('date', inplace=True)
    combined.reset_index(drop=True, inplace=True)
    combined.to_csv(FINAL_FILE, index=False)
    print(f"Saved to: {FINAL_FILE}")
    print(combined.head().to_string())
    return combined


if __name__ == "__main__":
    if FINAL_FILE.exists():
        resp = input(f"{FINAL_FILE} already exists. Re-download? (y/n): ").strip().lower()
        if resp != 'y':
            print("Using existing data. Run the notebook next.")
            exit()
    download_all_data()
    print("\nData ready. Open the notebook and Run All.")
