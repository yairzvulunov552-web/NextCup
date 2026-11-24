"""Definitions shared by the dashboard and the audit."""
from hashlib import sha256

import pandas as pd

MODES = {"כל מקורות הקפאין": "", "קפה בלבד": "coffee_"}


def scope(days, prefix):
    columns = ["events", "first_min", "second_min", "gap_min", "total_mg"]
    view = days[["person_id", "recall_day", "weekday", "age", *[prefix+c for c in columns]]].copy()
    view.columns = ["person_id", "recall_day", "weekday", "age", *columns]
    return view


def holdout(person_id):
    digest = sha256(str(int(person_id)).encode("ascii")).hexdigest()
    return int(digest[:8], 16) % 5 == 0


def benchmark(view):
    observed = view.dropna(subset=["gap_min"])
    test = observed.person_id.map(holdout)
    prediction = observed.loc[~test, "gap_min"].median()
    errors = (observed.loc[test, "gap_min"] - prediction).abs()
    return prediction, errors.mean(), int((~test).sum()), int(test.sum())


def by_period(started):
    periods = pd.cut(started.first_min, [0, 360, 720, 1080, 1440], right=False,
                     labels=["00–06", "06–12", "12–18", "18–24"])
    table = started.groupby(periods, observed=False).agg(days=("events", "size"),
                                                         repeats=("gap_min", "count"))
    table["share"] = table.repeats.div(table.days.where(table.days.gt(0)))
    return table.rename_axis("period").reset_index()
