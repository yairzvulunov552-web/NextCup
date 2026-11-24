"""Release checks for published data, reference predictor and dashboard filters."""
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from analysis_m2 import benchmark, by_period, holdout, scope

ROOT = Path(__file__).resolve().parents[1]


class NextCupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.days = pd.read_csv(ROOT / "data/nextcup_days.csv")

    def test_unit_and_coverage(self):
        d = self.days
        self.assertEqual(d.shape, (8568, 19))
        self.assertEqual(d.person_id.nunique(), 4527)
        self.assertFalse(d.duplicated(["person_id", "recall_day"]).any())
        self.assertEqual(int(d.age.eq(77).sum()), 96)
        self.assertTrue(d.coffee_events.le(d.events).all())
        self.assertTrue(d.coffee_total_mg.le(d.total_mg).all())
        for prefix, n, repeated in [("", 7468, 4648), ("coffee_", 5121, 1039)]:
            view = scope(d, prefix)
            self.assertEqual(view.events.gt(0).sum(), n)
            self.assertEqual(view.gap_min.count(), repeated)
            self.assertTrue(view.first_min.isna().equals(view.events.eq(0)))
            self.assertTrue(view.second_min.isna().equals(view.events.lt(2)))
            pd.testing.assert_series_equal(view.gap_min, view.second_min-view.first_min, check_names=False)
            self.assertTrue(view.gap_min.dropna().between(1, 1439).all())

    def test_denominators_and_holdout(self):
        for prefix, median, counts, error in [("",330,(3747,901),179.87236404),
                                             ("coffee_",300,(860,179),184.74301676)]:
            d = scope(self.days, prefix)
            group = by_period(d[d.events.gt(0)])
            self.assertEqual(group.days.sum(), d.events.gt(0).sum())
            self.assertEqual(group.repeats.sum(), d.gap_min.count())
            train = d[~d.person_id.map(holdout)]
            test = d[d.person_id.map(holdout)]
            self.assertTrue(set(train.person_id).isdisjoint(test.person_id))
            predicted, mae, ntrain, ntest = benchmark(d)
            self.assertEqual(predicted, median)
            self.assertEqual((ntrain,ntest), counts)
            self.assertAlmostEqual(mae,error,places=6)

    def test_interactive_filters(self):
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric], ["7,468","4,648","62.2%","5.5"])
        app.radio[0].set_value("קפה בלבד")
        app.slider[0].set_range(18, 25)
        app.selectbox[0].set_value("יום 2").run()
        expected = self.days.query("18 <= age <= 25 and recall_day == 2")
        n = expected.coffee_events.gt(0).sum()
        r = expected.coffee_gap_min.count()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric], [f"{n:,}",f"{r:,}",f"{r/n:.1%}","5"])
        self.assertLessEqual(len(app.dataframe[0].value), 30)
        # A single age with no repeat should yield a valid empty curve.
        counts = self.days.query("recall_day == 2").groupby("age").coffee_gap_min.count()
        if (counts == 0).any():
            age = int(counts[counts == 0].index[0])
            app.slider[0].set_range(age, age).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.metric[1].value, "0")
