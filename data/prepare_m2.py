"""Rebuild the participant-day analysis table from NHANES public-use files."""
from argparse import ArgumentParser
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

DATA = Path(__file__).resolve().parent
BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/"
KEYS = ["SEQN", "recall_day"]


def read(raw, stem, columns):
    frame = pd.read_sas(raw / f"{stem}_L.xpt", format="xport")[["SEQN", *columns]]
    # SAS transport readers can decode numeric zero as a tiny positive float.
    return frame.mask(frame.abs().lt(1e-60), 0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def collapse(items, prefix):
    # Distinct times are occasions. Several items consumed together count once.
    times = items.groupby([*KEYS, "minute"], as_index=False).mg.sum().sort_values([*KEYS, "minute"])
    times["rank"] = times.groupby(KEYS).cumcount()
    group = times.groupby(KEYS)
    summary = group.agg(events=("minute", "size"), first_min=("minute", "min"),
                        last_min=("minute", "max"), total_mg=("mg", "sum"))
    summary["second_min"] = times[times["rank"].eq(1)].set_index(KEYS).minute
    summary["gap_min"] = summary.second_min - summary.first_min
    return summary.add_prefix(prefix)


def build(raw):
    sleep = read(raw, "SLQ", ["SLD012"])
    fatigue = read(raw, "DPQ", ["DPQ040"])
    demo = read(raw, "DEMO", ["RIDAGEYR", "RIAGENDR"])
    people = sleep.merge(fatigue, validate="one_to_one").merge(demo, validate="one_to_one")
    people = people.loc[people.SLD012.notna() & people.DPQ040.isin([0, 1, 2, 3]) &
                        people.RIDAGEYR.ge(18)].copy()
    days, foods = [], []
    for day in (1, 2):
        pre = f"DR{day}"
        totals = read(raw, pre+"TOT", [pre+"DRSTZ", pre+"TCAFF", pre+"DAY"])
        totals.columns = ["SEQN", "status", "source_mg", "weekday"]
        valid = totals.loc[totals.status.eq(1) & totals.source_mg.notna()]
        if day == 1:
            people = people.merge(valid[["SEQN"]], validate="one_to_one")
        eligible = valid.merge(people, validate="one_to_one").assign(recall_day=day)
        days.append(eligible)
        item = read(raw, pre+"IFF", [pre+"ILINE", pre+"_020", pre+"ICAFF", pre+"IFDCD", pre+"DRSTZ"])
        item.columns = ["SEQN", "line", "second", "mg", "code", "status"]
        item = item[item.SEQN.isin(eligible.SEQN)]
        require(not item.duplicated(["SEQN", "line"]).any(), "Duplicate food line")
        require(item.status.eq(1).all() and item.mg.notna().all() and item.mg.ge(0).all(),
                "Incomplete item recall")
        item = item.loc[item.mg.gt(0)].copy()
        require(item.second.between(0, 86399).all() and item.second.mod(60).eq(0).all(),
                "Invalid occasion time")
        item["minute"] = item.second.floordiv(60).astype(int)
        foods.append(item.assign(recall_day=day))
    daily = pd.concat(days).set_index(KEYS)
    require(daily.index.is_unique, "Duplicate participant-day")
    items = pd.concat(foods)
    codes = pd.read_csv(DATA / "coffee_codes.csv")
    for prefix, source in [("", items), ("coffee_", items[items.code.isin(codes.food_code)])]:
        daily = daily.join(collapse(source, prefix), validate="one_to_one")
        for suffix in ("events", "total_mg"):
            col = prefix + suffix
            daily[col] = daily[col].fillna(0)
        gap = daily[prefix+"gap_min"]
        require(gap.notna().equals(daily[prefix+"events"].ge(2)), "Invalid target coverage")
        require(gap.dropna().between(1, 1439).all(), "Invalid same-day gap")
    require(daily.source_mg.eq(daily.total_mg).all(), "Item caffeine differs from recall totals")
    daily = daily.drop(columns=["source_mg", "status"]).reset_index().rename(columns={
        "SEQN": "person_id", "RIDAGEYR": "age", "RIAGENDR": "sex",
        "SLD012": "usual_sleep_hours", "DPQ040": "fatigue_frequency",
    })
    require(daily.sex.isin([1, 2]).all() and daily.weekday.between(1, 7).all(), "Invalid category")
    for col in daily.columns.difference(["usual_sleep_hours"]):
        daily[col] = daily[col].astype("Int64")
    return daily.sort_values(["person_id", "recall_day"])


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DATA / "raw")
    parser.add_argument("--output", type=Path, default=DATA / "nextcup_days.csv")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.download:
        args.raw.mkdir(parents=True, exist_ok=True)
        for name in ["SLQ", "DPQ", "DEMO", "DR1TOT", "DR2TOT", "DR1IFF", "DR2IFF"]:
            target = args.raw / f"{name}_L.xpt"
            if not target.exists():
                temp = target.with_suffix(".part")
                urlretrieve(BASE + target.name, temp)
                temp.replace(target)
    result = build(args.raw)
    tmp = args.output.with_suffix(".tmp")
    result.to_csv(tmp, index=False, lineterminator="\n")
    tmp.replace(args.output)
    print(f"{len(result):,} participant-days, {result.person_id.nunique():,} participants.")
