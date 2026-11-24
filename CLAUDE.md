# NextCup — M2 handoff

Run `streamlit run app.py` from the repository root. The active dashboard and README
use the 2021–2023 NHANES cohort. The historical M1 notes below describe the original
2017–2018 prototype, available through `streamlit run app_m1.py` and `docs/M1.md`.

## What the data showed

The M2 table has 8,568 participant-days and 4,527 participants. First and second
occasions are distinct minutes within one recall day. Positive caffeine from any
food or beverage gives 7,468 exposed days and 4,648 observed second occasions.
The USDA coffee-only subset gives 5,121 and 1,039 respectively. Keep zero intake,
one occasion, and an observed second occasion distinct.

The primary target is `gap_min`. Before noon, 4,133 of 6,057 first occasions were
followed by another that day. From noon onward the counts were 515 of 1,411.
Observation ends at midnight. Group differences are descriptive, unweighted and
partly reflect the time remaining in the day.

The training median of 330 minutes has a held-out MAE of 179.87 minutes on 901
participant-days. Keep the same participant split for M3 and tune inside training.
Use only information available when the first occasion happens. In particular,
the daily total, event count and later timestamps all contain future information.

`data/prepare_m2.py` rebuilds both targets and reconciles daily totals with CDC.
`analysis_m2.py` owns metric definitions. Run `python -m unittest discover -s tests -v`.
See `docs/data-m2.md` for missingness, sources and the data dictionary.

## Historical M1 context

**Goal:** a Streamlit app that predicts when a user will drink their next caffeinated drink,
learned from thousands of people's real drinking times. Later stages: predict how alert the
user will feel (caffeine blood-level curve), then detect drinks automatically (smartwatch / NFC).

**Course:** Vibe Coding with Claude, Ariel University. Milestones: M1 definition + first app →
M2 dashboard → M3 model → demo day. `README.md` (Hebrew) is the full spec; read it first.

**Data:** `data/caffeine_events.csv`, one row per caffeinated drink (≥10 mg) by an adult,
from NHANES 2017–2018 (US). 11,703 rows, 4,013 people, 1–2 recall days each.
Columns: person_id, recall_day, weekday, time, hour, category (coffee/tea/soda/energy),
item, caffeine_mg, occasion, age, sex. Built by `data/prepare_data.py`; column docs in `data/README.md`.

**Model target (M3):** for each drink, the hours until the person's next caffeinated drink the
same day (regression) and whether there is one at all (classification). Features: hour of the
drink, category, caffeine_mg, drinks/mg so far today, weekday, occasion, age, sex.
Split train/test **by person_id** so one person never appears in both.

**Files:**
- `app.py`: Streamlit entry point (`streamlit run app.py`)
- `data/`: dataset, prep script, raw downloads (git-ignored)
- `requirements.txt`: pinned versions; pin any library you add

**Conventions:** UI text in Hebrew (RTL), code and comments in English. Keep `app.py` simple;
move logic to modules once it grows. Never commit secrets or `data/raw/`. Not medical advice:
say so wherever we show predictions about the body.
