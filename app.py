"""NextCup — first app (M1): project name, project sentence, first look at the data."""

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).parent / "data" / "caffeine_events.csv"

st.set_page_config(page_title="NextCup", page_icon="☕", layout="centered")

# Hebrew UI: right-to-left text, but keep tables and numbers left-to-right.
st.markdown(
    """
    <style>
      .stApp, .stMarkdown, h1, h2, h3, p, li { direction: rtl; text-align: right; }
      [data-testid="stDataFrame"], [data-testid="stMetricValue"] { direction: ltr; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("☕ NextCup")
st.subheader("יודעים מתי תרצו את הקפה הבא, ואיך תרגישו אחריו")

st.info(
    "**משפט הפרויקט:** סטודנטים ועובדים שתלויים בקפאין שותים קפה מתוך הרגל ובלי תכנון, "
    "ומשלמים על זה בשינה גרועה ובנפילות אנרגיה. אנחנו בונים אפליקציה שמנבאת מתי יגיע "
    "הקפה הבא שלכם, ומבוססת על מודל ML שאומן על נתוני שתייה של אלפי אנשים "
    "(סקר התזונה הלאומי בארה״ב, NHANES)."
)


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_FILE)


st.header("הנתונים: מבט ראשון")

if not DATA_FILE.exists():
    st.warning("קובץ הנתונים חסר. הריצו `python data/prepare_data.py` מתיקיית הריפו.")
else:
    df = load_data()
    days = df.groupby(["person_id", "recall_day"]).ngroups

    c1, c2, c3 = st.columns(3)
    c1.metric("משקאות עם קפאין", f"{len(df):,}")
    c2.metric("אנשים", f"{df.person_id.nunique():,}")
    c3.metric("משקאות ליום (ממוצע)", f"{len(df) / days:.2f}")

    st.caption("5 השורות הראשונות. כל שורה היא משקה אחד עם קפאין שאדם אחד שתה:")
    st.dataframe(df.head(5), hide_index=True, width="stretch")

st.header("בקרוב")
st.markdown(
    """
- **דשבורד (M2):** מתי ביום שותים קפה, לפי גיל, מין, יום בשבוע וסוג משקה.
- **מודל (M3):** מזינים את המשקה האחרון שלכם, ומקבלים חיזוי לשעה של הקפה הבא.
- **בהמשך:** עקומת קפאין בדם ותחזית למצב הערנות שלכם לאורך היום.
"""
)
