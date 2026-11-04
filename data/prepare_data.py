"""Build data/caffeine_events.csv from the public NHANES 2017-2018 dietary recall.

Downloads 4 public CDC files (~145 MB, not committed to git), keeps every
caffeinated drink (>= 10 mg) consumed by an adult, and writes one small CSV
with one row per drink.

Usage (from the repo root):
    python data/prepare_data.py
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/"
FILES = ["DR1IFF_J.xpt", "DR2IFF_J.xpt", "DEMO_J.xpt", "DRXFCD_J.xpt"]

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
OUT = DATA_DIR / "caffeine_events.csv"

MIN_CAFFEINE_MG = 10   # below this it's chocolate crumbs, not a drink
MIN_AGE = 18

WEEKDAYS = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
OCCASIONS = {
    1: "breakfast", 2: "lunch", 3: "dinner", 4: "dinner", 5: "breakfast",
    6: "snack", 7: "drink", 9: "extended", 10: "breakfast", 11: "breakfast",
    12: "lunch", 13: "snack", 14: "dinner", 15: "snack", 16: "snack",
    17: "snack", 18: "snack", 19: "drink",
}


def download() -> None:
    RAW_DIR.mkdir(exist_ok=True)
    for name in FILES:
        target = RAW_DIR / name
        if not target.exists():
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(BASE + name, target)


def drink_category(code: int, desc: str) -> str:
    desc = desc.upper()
    if "ENERGY DRINK" in desc or str(code).startswith("953"):
        return "energy"
    if "COFFEE" in desc or "ESPRESSO" in desc or "CAPPUCCINO" in desc or "LATTE" in desc:
        return "coffee"
    if "TEA" in desc:
        return "tea"
    if "SOFT DRINK" in desc or str(code).startswith("924"):
        return "soda"
    return "other"


def load_day(day: int) -> pd.DataFrame:
    p = f"DR{day}"
    df = pd.read_sas(RAW_DIR / f"{p}IFF_J.xpt")
    df = df[df[f"{p}ICAFF"] >= MIN_CAFFEINE_MG]
    return pd.DataFrame({
        "person_id": df["SEQN"].astype(int),
        "recall_day": day,
        "weekday": df[f"{p}DAY"].astype(int).map(WEEKDAYS),
        "seconds": df[f"{p}_020"].astype(int),
        "occasion": df[f"{p}_030Z"].astype(int).map(OCCASIONS).fillna("other"),
        "food_code": df[f"{p}IFDCD"].astype(int),
        "caffeine_mg": df[f"{p}ICAFF"].round(1),
    })


def main() -> None:
    download()
    events = pd.concat([load_day(1), load_day(2)], ignore_index=True)

    foods = pd.read_sas(RAW_DIR / "DRXFCD_J.xpt", encoding="latin-1")
    foods = foods.rename(columns={"DRXFDCD": "food_code", "DRXFCSD": "item"})
    foods["food_code"] = foods["food_code"].astype(int)
    events = events.merge(foods[["food_code", "item"]], on="food_code", how="left")
    events["category"] = [drink_category(c, d) for c, d in zip(events.food_code, events.item.fillna(""))]

    demo = pd.read_sas(RAW_DIR / "DEMO_J.xpt")[["SEQN", "RIDAGEYR", "RIAGENDR"]]
    demo = demo.rename(columns={"SEQN": "person_id", "RIDAGEYR": "age", "RIAGENDR": "sex"})
    demo["person_id"] = demo["person_id"].astype(int)
    demo["age"] = demo["age"].astype(int)
    demo["sex"] = demo["sex"].map({1: "male", 2: "female"})
    events = events.merge(demo, on="person_id", how="left")

    events = events[(events.age >= MIN_AGE) & (events.category != "other")]
    events["time"] = (
        (events.seconds // 3600).astype(int).astype(str).str.zfill(2) + ":"
        + (events.seconds % 3600 // 60).astype(int).astype(str).str.zfill(2)
    )
    events["hour"] = (events.seconds / 3600).round(2)

    cols = ["person_id", "recall_day", "weekday", "time", "hour", "category",
            "item", "caffeine_mg", "occasion", "age", "sex"]
    events = events.sort_values(["person_id", "recall_day", "seconds"])[cols]
    events.to_csv(OUT, index=False)
    print(f"wrote {OUT.name}: {len(events):,} rows, {events.person_id.nunique():,} people")


if __name__ == "__main__":
    main()
