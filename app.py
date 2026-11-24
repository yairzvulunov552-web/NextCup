"""NextCup M2 | Same-day repeat caffeine consumption in NHANES."""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from analysis_m2 import MODES, benchmark, by_period, scope

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="NextCup · הכוס הבאה", page_icon="☕", layout="wide")
st.markdown("""<style>
[data-testid="stMainBlockContainer"]{max-width:1320px;padding-top:2.2rem}
[data-testid="stMain"],[data-testid="stSidebarContent"]{direction:rtl;text-align:right}
[data-testid="stAppViewContainer"],.stMarkdown,button,input,.hero{font-family:"Segoe UI",Arial,sans-serif}
[data-testid="stSlider"] [data-baseweb="slider"]{direction:ltr}
[data-testid="stSidebar"]{background:#f1ece4}
[data-testid="stSidebarContent"] h2{font-size:1.35rem}
[data-testid="stMetric"]{background:#fffdf9;border:1px solid #dcd3c5;border-top:3px solid #a36c46;
border-radius:10px;padding:.85rem 1rem;min-height:108px}
[data-testid="stMetricLabel"] p{font-size:.94rem}
[data-testid="stMetricValue"]{font-weight:700;line-height:1.4;font-variant-numeric:tabular-nums}
[data-testid="stVegaLiteChart"],[data-testid="stDataFrame"]{direction:ltr}
[data-testid="stHeader"]{background:transparent;height:2rem}
.hero{background:#30251f;color:#fff9ef;border-radius:16px;padding:26px 34px;position:relative;
display:flex;gap:2rem;justify-content:space-between;align-items:center}
.hero h1{font-size:clamp(1.8rem,3.2vw,3.15rem);letter-spacing:-.04em;color:#fff9ef;
padding:.28em 0 .16em;line-height:1.16}
.hero p{margin:0;max-width:720px;font-size:1.05rem;line-height:1.6;color:#e8dcd0}
.hero .source{font-size:.85rem;letter-spacing:.035em;color:#f2bf90}
.wordmark{direction:ltr;font-family:Georgia,serif;font-size:clamp(1.7rem,3.4vw,3.25rem);
letter-spacing:-.07em;color:#fff7ed;white-space:nowrap}
.wordmark i{color:#f2b57d;font-weight:400}
h3{font-size:1.23rem}
@media(max-width:760px){.hero{padding:19px;display:block}.wordmark{display:none}
[data-testid="stMainBlockContainer"]{padding-inline:1rem;padding-top:3rem}}
</style>""", unsafe_allow_html=True)


@st.cache_data
def load(path, version):
    return pd.read_csv(path)


def clock(minutes):
    if pd.isna(minutes):
        return None
    hours, minute = divmod(int(minutes), 60)
    return f"{hours:02d}:{minute:02d}"


def hours(minutes):
    return "—" if pd.isna(minutes) else f"{minutes/60:.2f}".rstrip("0").rstrip(".")


def show_chart(chart, data, description):
    spec = (chart.properties(height=245, description=description).configure_view(stroke=None)
            .configure_axis(labelFontSize=12, titleFontSize=13, titlePadding=10,
                            gridColor="#e8e1d7", domainColor="#b8aa99", labelColor="#473d34",
                            titleColor="#473d34").to_dict())
    spec.pop("data", None)
    spec.pop("datasets", None)
    # The aggregates are small. Keep marks and filtered values in the same
    # Vega-Lite layer so a rerun replaces them together.
    spec["layer"] = [{"mark": spec.pop("mark"), "encoding": spec.pop("encoding"),
                      "data": {"values": data.to_dict("records")}}]
    st.vega_lite_chart(spec=spec, use_container_width=True, theme=None)


path = ROOT / "data" / "nextcup_days.csv"
days = load(path, path.stat().st_mtime_ns)
with st.sidebar:
    st.header("סינון הנתונים")
    mode = st.radio("מקור הקפאין", list(MODES), help="קפה בלבד כולל פריטים בקטגוריית הקפה של USDA עם קפאין מדווח.")
    age = st.slider("טווח גיל במדגם", 18, 80, (18, 80))
    day = st.selectbox("יום דיווח", ["שני ימי הדיווח", "יום 1", "יום 2"])
    st.caption("הגיל 80 כולל בני 80 ומעלה. כל שורה מייצגת משתתף ביום דיווח אחד.")
base = scope(days, MODES[mode])
sample = base[base.age.between(*age)]
if day != "שני ימי הדיווח":
    sample = sample[sample.recall_day.eq(int(day[-1]))]
started = sample[sample.events.gt(0)]
gaps = started.gap_min.dropna()
repeat_rate = len(gaps) / len(started) if len(started) else None
prediction, mae, train_n, test_n = benchmark(base)
noun = "קפה" if MODES[mode] else "קפאין"
insight = (f"ב־{repeat_rate:.1%} מהימים שבהם נרשמה צריכת {noun}, המשתתפים דיווחו על צריכה נוספת עד חצות."
           if repeat_rate is not None else "אין ימי צריכה בקבוצה שנבחרה. אפשר להרחיב את טווח הגיל.")
early = started.loc[started.first_min.lt(720), "events"]
late = started.loc[started.first_min.ge(720), "events"]
if len(early) and len(late):
    insight = (f"כשהצריכה הראשונה הייתה לפני 12:00, נרשמה צריכה נוספת ב־{early.ge(2).mean():.1%} מהימים. "
               f"כשהתחילו מ־12:00 ואילך, השיעור היה {late.ge(2).mean():.1%}. "
               "כדאי להשוות את היום שלכם לימים שהתחילו בשעה דומה.")
st.markdown(f"""<section class="hero"><div><p class="source">סקר התזונה האמריקאי · NHANES 2021–2023</p>
<h1>מתי חוזרים ל{noun}?</h1><p>{insight}</p></div>
<div class="wordmark" aria-label="NextCup">Next<i>Cup</i></div></section>""", unsafe_allow_html=True)
st.caption(f"{mode}  ·  {sample.person_id.nunique():,} משתתפים  ·  {len(sample):,} ימי דיווח בסינון הנוכחי")
cols = st.columns(4)
cols[0].metric("ימים עם צריכה", f"{len(started):,}")
cols[1].metric("ימים עם צריכה נוספת", f"{len(gaps):,}")
cols[2].metric("שיעור הצריכה החוזרת", "—" if repeat_rate is None else f"{repeat_rate:.1%}")
cols[3].metric("Baseline באימון (ש׳)", hours(prediction),
               help="תחזית קבועה של הזמן מהצריכה הראשונה לשנייה. מחושבת לפי מקור הקפאין, על משתתפי האימון בלבד.")
periods = by_period(started)
chart_scope = f"{mode}, גיל {age[0]} עד {age[1]}, {day}"
left, right = st.columns(2, gap="medium")
with left.container(border=True):
    st.subheader("הסיכוי לצריכה נוספת עד חצות")
    st.caption("שיעור הימים עם אירוע שני, לפי שעת האירוע הראשון")
    rates = periods.dropna(subset=["share"])
    if len(rates):
        chart = alt.Chart().mark_bar(color="#9b542f", size=38).encode(
            x=alt.X("period:N", title="שעת הצריכה הראשונה", sort=list(periods.period), axis=alt.Axis(labelAngle=0)),
            y=alt.Y("share:Q", title="שיעור הימים", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
            tooltip=[alt.Tooltip("period:N", title="שעות"), alt.Tooltip("days:Q", title="ימי צריכה"),
                     alt.Tooltip("repeats:Q", title="ימים עם אירוע שני"), alt.Tooltip("share:Q", title="שיעור", format=".1%")])
        show_chart(chart, rates, f"שיעור הצריכה החוזרת לפי שעת התחלה. {chart_scope}")
    else:
        st.info("אין ימי צריכה להצגה.")
    st.caption("התחלה מאוחרת משאירה פחות זמן לתעד אירוע שני לפני סיום יום הדיווח.")
with right.container(border=True):
    st.subheader("כמה זמן עבר עד הפעם השנייה?")
    st.caption("שיעור מצטבר מתוך הימים שבהם נרשמה צריכה חוזרת")
    if len(gaps):
        curve = gaps.value_counts().sort_index().rename_axis("minute").reset_index(name="count")
        curve["hours"] = curve.minute / 60
        curve["share"] = curve["count"].cumsum() / len(gaps)
        origin = pd.DataFrame([{"hours": 0, "share": 0}])
        points = pd.concat([origin, curve[["hours", "share"]]], ignore_index=True)
        chart = alt.Chart().mark_line(
            interpolate="step-after", color="#28736a", strokeWidth=3).encode(
            x=alt.X("hours:Q", title="שעות מאז הצריכה הראשונה", scale=alt.Scale(zero=True)),
            y=alt.Y("share:Q", title="שיעור מצטבר", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
            tooltip=[alt.Tooltip("hours:Q", title="שעות", format=".2f"), alt.Tooltip("share:Q", title="שיעור מצטבר", format=".1%")])
        show_chart(chart, points, f"התפלגות זמני ההמתנה. {chart_scope}")
        st.caption(f"חציון הקבוצה הוא {hours(gaps.median())} שעות. מחצית מזמני ההמתנה נמצאים בין {hours(gaps.quantile(.25))} ל־{hours(gaps.quantile(.75))} שעות.")
    else:
        st.info("בקבוצה זו אין ימים עם אירוע שני.")
with st.expander("היעד והמדד שהמודל יצטרך לנצח"):
    st.write(f"היעד הוא מספר הדקות עד לאירוע השני של {noun} באותו יום, החל מהאירוע הראשון. "
             "אם היום הסתיים אחרי אירוע אחד, משך ההמתנה נשאר חסר.")
    st.write(f"חציון האימון הוא {prediction:g} דקות על פני {train_n:,} ימי צריכה חוזרת. "
             f"ב־{test_n:,} ימי מבחן של משתתפים אחרים, השגיאה המוחלטת הממוצעת (MAE) היא {mae:.2f} דקות. "
             "ב־M3 נשווה את המודל לאותו פיצול לפי משתתף ונשאף לשגיאה נמוכה יותר.")
    st.caption("גיל ויום דיווח משנים את תיאור הקבוצה. נקודת הייחוס נשארת קבועה לכל הגדרה של מקור הקפאין.")
st.subheader("דוגמה מהנתונים הנקיים")
st.caption("עד 30 ימי דיווח לפי הסינון. תא ריק בזמן הצריכה מציין שאירוע כזה לא דווח.")
preview = sample.head(30).copy()
for name in ("first_min", "second_min"):
    preview[name] = preview[name].map(clock)
st.dataframe(preview[["person_id","recall_day","age","events","first_min","second_min","gap_min","total_mg"]].rename(columns={
    "person_id":"מזהה משתתף","recall_day":"יום דיווח","age":"גיל","events":"מועדי צריכה",
    "first_min":"שעה ראשונה","second_min":"שעה שנייה","gap_min":"יעד בדקות","total_mg":"קפאין במ״ג"
}), hide_index=True, width="stretch", height=240)
st.caption("מקור: CDC/NCHS, סקר NHANES. התוצאות מתארות את ימי הדיווח במדגם, ללא שקלול לאוכלוסייה. שעות הצריכה בדיווח עצמי.")
