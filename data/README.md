# data/

| File | What | In git? |
|---|---|---|
| `caffeine_events.csv` | One row per caffeinated drink (≥ 10 mg) by an adult. 11,703 rows × 11 columns | Yes (0.9 MB) |
| `prepare_data.py` | Downloads the raw NHANES files and builds the CSV | Yes |
| `raw/` | Raw CDC `.xpt` files (~145 MB) | No (`.gitignore`) |

To rebuild: `python data/prepare_data.py` from the repo root.

## Source

NHANES 2017–2018, the US national health and nutrition survey (CDC). Each participant
reports everything they ate and drank over 24 hours, including the **clock time** of
each item and its **caffeine mg**. Most people have two non-consecutive recall days.

- Day 1 items: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DR1IFF_J.xpt
- Day 2 items: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DR2IFF_J.xpt
- Demographics: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.xpt
- Food names: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DRXFCD_J.xpt
- Documentation: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017

## Columns of `caffeine_events.csv`

| Column | Meaning |
|---|---|
| `person_id` | NHANES participant id (SEQN) |
| `recall_day` | 1 or 2 (the two recall days are 3–10 days apart) |
| `weekday` | Sun…Sat |
| `time` / `hour` | Clock time of the drink (`08:30` / `8.5`) |
| `category` | coffee / tea / soda / energy |
| `item` | Food description, e.g. `COFFEE, BREWED` |
| `caffeine_mg` | Caffeine in this drink (mg) |
| `occasion` | breakfast / lunch / dinner / snack / drink / extended |
| `age` | Years (80 means 80+) |
| `sex` | male / female |

No missing values after filtering. Times are self-reported and often rounded to the
half hour.
