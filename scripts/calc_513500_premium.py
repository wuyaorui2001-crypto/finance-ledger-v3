"""Compute 513500 ETF premium stats since listing (2014-01-15)."""
from __future__ import annotations

import json
import sys
from datetime import datetime

import akshare as ak
import pandas as pd

LISTING_DATE = "2014-01-15"
CODE = "513500"


def fetch_nav() -> pd.DataFrame:
    nav = ak.fund_open_fund_info_em(symbol=CODE, indicator="单位净值走势")
    nav = nav.rename(columns={"净值日期": "date", "单位净值": "nav"})
    nav["date"] = pd.to_datetime(nav["date"])
    nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")
    return nav.dropna(subset=["date", "nav"]).sort_values("date")


def fetch_close() -> pd.DataFrame:
    errors: list[str] = []
    # Eastmoney ETF history
    try:
        df = ak.fund_etf_hist_em(symbol=CODE, period="daily", adjust="")
        if df is not None and len(df):
            out = df.rename(columns={"日期": "date", "收盘": "close"})[["date", "close"]]
            out["date"] = pd.to_datetime(out["date"])
            out["close"] = pd.to_numeric(out["close"], errors="coerce")
            return out.dropna().sort_values("date")
    except Exception as e:
        errors.append(f"fund_etf_hist_em: {e}")

    # Sina
    try:
        df = ak.fund_etf_hist_sina(symbol=f"sh{CODE}")
        if df is not None and len(df):
            out = df.rename(columns={"date": "date", "close": "close"})
            if "date" not in out.columns and len(out.columns) >= 2:
                out.columns = ["date", "open", "high", "low", "close", "volume"][: len(out.columns)]
            out["date"] = pd.to_datetime(out["date"])
            out["close"] = pd.to_numeric(out["close"], errors="coerce")
            return out[["date", "close"]].dropna().sort_values("date")
    except Exception as e:
        errors.append(f"fund_etf_hist_sina: {e}")

    # A-share K-line (ETF listed as stock)
    try:
        df = ak.stock_zh_a_hist(
            symbol=CODE,
            period="daily",
            start_date="20140101",
            end_date=datetime.now().strftime("%Y%m%d"),
            adjust="",
        )
        if df is not None and len(df):
            out = df.rename(columns={"日期": "date", "收盘": "close"})[["date", "close"]]
            out["date"] = pd.to_datetime(out["date"])
            out["close"] = pd.to_numeric(out["close"], errors="coerce")
            return out.dropna().sort_values("date")
    except Exception as e:
        errors.append(f"stock_zh_a_hist: {e}")

    raise RuntimeError("All price sources failed:\n" + "\n".join(errors))


def main() -> None:
    nav = fetch_nav()
    close = fetch_close()

    listing = pd.Timestamp(LISTING_DATE)
    merged = close.merge(nav, on="date", how="inner")
    merged = merged[merged["date"] >= listing].copy()
    merged["premium_pct"] = (merged["close"] / merged["nav"] - 1) * 100

    if merged.empty:
        print(json.dumps({"error": "no overlapping rows after listing"}, ensure_ascii=False))
        sys.exit(1)

    prem = merged["premium_pct"]
    idx_max = prem.idxmax()
    idx_min = prem.idxmin()

    result = {
        "fund_code": CODE,
        "fund_name": "博时标普500ETF",
        "listing_date": LISTING_DATE,
        "stats_start": merged["date"].min().strftime("%Y-%m-%d"),
        "stats_end": merged["date"].max().strftime("%Y-%m-%d"),
        "trading_days": int(len(merged)),
        "formula": "溢价率(%) = (收盘价 / 当日基金份额净值 - 1) × 100",
        "mean_premium_pct": round(float(prem.mean()), 4),
        "median_premium_pct": round(float(prem.median()), 4),
        "std_premium_pct": round(float(prem.std()), 4),
        "max_premium": {
            "date": merged.loc[idx_max, "date"].strftime("%Y-%m-%d"),
            "premium_pct": round(float(prem.loc[idx_max]), 4),
            "close": round(float(merged.loc[idx_max, "close"]), 4),
            "nav": round(float(merged.loc[idx_max, "nav"]), 4),
        },
        "min_premium": {
            "date": merged.loc[idx_min, "date"].strftime("%Y-%m-%d"),
            "premium_pct": round(float(prem.loc[idx_min]), 4),
            "close": round(float(merged.loc[idx_min, "close"]), 4),
            "nav": round(float(merged.loc[idx_min, "nav"]), 4),
        },
        "pct_days_premium_positive": round(float((prem > 0).mean() * 100), 2),
        "pct_days_discount": round(float((prem < 0).mean() * 100), 2),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
