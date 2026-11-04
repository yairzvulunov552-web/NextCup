# NextCup — context for Claude

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
