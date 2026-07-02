import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
import os

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
st.set_page_config(page_title="Protein Tracker", page_icon="🥩", layout="centered")

LOG_FILE = "food_log.csv"
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Small local fallback database, used only if the API is unavailable
# or you don't have an API key set up yet.
FALLBACK_DB = {
    "Chicken breast (cooked)": 31.0,
    "Egg, whole (large)": 13.0,
    "Greek yogurt, plain": 10.0,
    "Tofu, firm": 15.0,
    "White rice, cooked": 2.7,
}


# ---------------------------------------------------------
# USDA FoodData Central lookup
# ---------------------------------------------------------
@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def search_food(query: str, api_key: str):
    """
    Search USDA FoodData Central for a food name and return a list of
    candidates, each with a description and protein grams per 100g.
    Cached for 24h so repeated searches don't burn API calls.
    """
    if not query or not api_key:
        return []

    params = {
        "api_key": api_key,
        "query": query,
        "pageSize": 8,
        # Prefer whole/generic foods over heavily branded products
        "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"],
    }
    try:
        resp = requests.get(USDA_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        st.error(f"Couldn't reach USDA FoodData Central: {e}")
        return []

    results = []
    for food in data.get("foods", []):
        protein = None
        for nutrient in food.get("foodNutrients", []):
            if nutrient.get("nutrientName") == "Protein":
                protein = nutrient.get("value")
                break
        if protein is not None:
            results.append(
                {
                    "description": food.get("description", "Unknown"),
                    "protein_per_100g": round(protein, 1),
                }
            )
    return results


# ---------------------------------------------------------
# Data persistence helpers
# ---------------------------------------------------------
def load_log() -> pd.DataFrame:
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE, parse_dates=["date"])
        return df
    return pd.DataFrame(columns=["date", "time", "food", "grams", "protein_g"])


def save_log(df: pd.DataFrame) -> None:
    df.to_csv(LOG_FILE, index=False)


def add_entry(food: str, grams: float, protein_per_100g: float) -> None:
    df = load_log()
    protein = round(grams * protein_per_100g / 100, 1)
    new_row = {
        "date": pd.to_datetime(date.today()),
        "time": datetime.now().strftime("%H:%M"),
        "food": food,
        "grams": grams,
        "protein_g": protein,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_log(df)


def delete_entry(index: int) -> None:
    df = load_log()
    df = df.drop(index).reset_index(drop=True)
    save_log(df)


# ---------------------------------------------------------
# Sidebar - settings
# ---------------------------------------------------------
st.sidebar.header("Settings")
daily_goal = st.sidebar.number_input(
    "Daily protein goal (g)", min_value=0, max_value=400, value=120, step=5
)

st.sidebar.markdown("---")
st.sidebar.subheader("USDA API key")
default_key = st.secrets.get("USDA_API_KEY", "") if hasattr(st, "secrets") else ""
api_key = st.sidebar.text_input(
    "FoodData Central API key",
    value=default_key,
    type="password",
    help="Free key from https://fdc.nal.usda.gov/api-key-signup.html",
)
st.sidebar.caption(
    "Get a free key at fdc.nal.usda.gov/api-key-signup.html, then paste it "
    "here (or add it as `USDA_API_KEY` in Streamlit secrets so you don't "
    "have to re-enter it)."
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Log data is stored locally in `food_log.csv` next to the app. "
    "On Streamlit Community Cloud this resets on redeploy unless you "
    "connect a persistent database."
)

# ---------------------------------------------------------
# Main - log a food
# ---------------------------------------------------------
st.title("🥩 Protein Tracker")
st.write("Search a food, enter how much you ate, and protein is calculated automatically.")

if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "search_query" not in st.session_state:
    st.session_state.search_query = ""

search_col, btn_col = st.columns([3, 1])
with search_col:
    query = st.text_input("Food name", placeholder="e.g. tilapia, sourdough bread, avocado")
with btn_col:
    st.write("")
    st.write("")
    search_clicked = st.button("🔍 Search", use_container_width=True)

if search_clicked:
    if not api_key:
        st.warning(
            "Add a free USDA API key in the sidebar to enable automatic lookup. "
            "Using the small built-in food list for now."
        )
        st.session_state.search_results = [
            {"description": name, "protein_per_100g": val}
            for name, val in FALLBACK_DB.items()
            if query.lower() in name.lower()
        ]
    else:
        with st.spinner(f"Searching for '{query}'..."):
            st.session_state.search_results = search_food(query, api_key)
        if not st.session_state.search_results:
            st.info("No matches found. Try a simpler search term, e.g. 'tilapia' instead of '1 pc medium tilapia'.")
    st.session_state.search_query = query

if st.session_state.search_results:
    options = [
        f"{r['description']} — {r['protein_per_100g']}g protein / 100g"
        for r in st.session_state.search_results
    ]
    chosen_idx = st.radio("Select the closest match:", range(len(options)), format_func=lambda i: options[i])
    chosen = st.session_state.search_results[chosen_idx]

    grams = st.number_input("Amount (g)", min_value=1, max_value=2000, value=100, step=10)
    computed_protein = round(grams * chosen["protein_per_100g"] / 100, 1)
    st.caption(f"≈ {computed_protein}g protein for {grams}g of {chosen['description']}")

    if st.button("➕ Add to log", use_container_width=True):
        add_entry(chosen["description"], grams, chosen["protein_per_100g"])
        st.success(f"Added {chosen['description']} ({grams}g, {computed_protein}g protein)")
        st.session_state.search_results = []
        st.rerun()

with st.expander("Add a custom food manually instead"):
    with st.form("manual_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        manual_name = c1.text_input("Food name")
        manual_grams = c2.number_input("Grams", min_value=1, max_value=2000, value=100, step=10)
        manual_protein = c3.number_input("Protein per 100g", min_value=0.0, max_value=100.0, value=20.0, step=0.5)
        manual_submit = st.form_submit_button("Add entry")
        if manual_submit:
            if not manual_name:
                st.error("Please enter a food name.")
            else:
                add_entry(manual_name, manual_grams, manual_protein)
                st.success(f"Added {manual_name} ({manual_grams}g)")
                st.rerun()

# ---------------------------------------------------------
# Today's log
# ---------------------------------------------------------
st.markdown("---")
st.subheader("Today's log")

log_df = load_log()
today_df = log_df[log_df["date"].dt.date == date.today()] if not log_df.empty else log_df

total_protein_today = today_df["protein_g"].sum() if not today_df.empty else 0.0

progress = min(total_protein_today / daily_goal, 1.0) if daily_goal > 0 else 0.0
st.progress(progress, text=f"{total_protein_today:.1f}g / {daily_goal}g protein today")

if today_df.empty:
    st.info("No entries yet today. Search and log your first food above!")
else:
    display_df = today_df[["time", "food", "grams", "protein_g"]].reset_index()
    display_df.columns = ["idx", "Time", "Food", "Grams", "Protein (g)"]

    for _, row in display_df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([1, 3, 1.2, 1.2, 0.6])
        c1.write(row["Time"])
        c2.write(row["Food"])
        c3.write(f"{row['Grams']}g")
        c4.write(f"{row['Protein (g)']}g")
        if c5.button("🗑️", key=f"del_{row['idx']}"):
            delete_entry(int(row["idx"]))
            st.rerun()

# ---------------------------------------------------------
# History
# ---------------------------------------------------------
st.markdown("---")
st.subheader("History")

if log_df.empty:
    st.caption("No history yet.")
else:
    daily_totals = (
        log_df.groupby(log_df["date"].dt.date)["protein_g"].sum().reset_index()
    )
    daily_totals.columns = ["Date", "Protein (g)"]
    daily_totals = daily_totals.sort_values("Date")

    st.bar_chart(daily_totals.set_index("Date"))

    with st.expander("View all entries"):
        st.dataframe(
            log_df[["date", "time", "food", "grams", "protein_g"]]
            .sort_values(["date", "time"], ascending=False)
            .rename(
                columns={
                    "date": "Date",
                    "time": "Time",
                    "food": "Food",
                    "grams": "Grams",
                    "protein_g": "Protein (g)",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
