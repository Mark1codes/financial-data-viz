import os
import requests
import pandas as pd
from io import StringIO

FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"
START_DATE = "2010-01-01"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")

SERIES = {
    "consumer_debt": "TOTALSL",
    "savings_rate": "PSAVERT",
    "delinquency_rate": "DRCCLACBS",
    "recession": "USREC",
}


def fetch_series(series_id: str, start: str = START_DATE) -> pd.DataFrame:
    url = f"{FRED_BASE}?id={series_id}"
    print(f"  Fetching {series_id} ...", end=" ")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= start].copy()
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"]).reset_index(drop=True)
    print(f"ok ({len(df)} rows)")
    return df


def save_csv(df: pd.DataFrame, name: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    return path


def main():
    print("=" * 50)
    print("Fetching FRED data...")
    print("=" * 50)

    for name, series_id in SERIES.items():
        df = fetch_series(series_id)
        path = save_csv(df, name)
        print(f"  Saved -> {path}\n")

    print("=" * 50)
    print("All data fetched and saved to /data/")
    print("=" * 50)


if __name__ == "__main__":
    main()
