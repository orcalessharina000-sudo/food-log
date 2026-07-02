import streamlit as st
import pandas as pd
from datetime import date, datetime
import os

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
st.set_page_config(page_title="Protein Tracker", page_icon="🥩", layout="centered")

LOG_FILE = "food_log.csv"

# Protein content per 100g (or per 100ml for liquids) of common foods.
# Feel free to add more foods to this dictionary.
FOOD_DB = {
    "Chicken breast (cooked)": 31.0,
    "Chicken thigh (cooked)": 26.0,
    "Beef, ground 85% lean (cooked)": 26.0,
    "Pork chop (cooked)": 27.0,
    "Salmon (cooked)": 25.0,
    "Tuna, canned in water": 26.0,
    "Shrimp (cooked)": 24.0,
    "Egg, whole (large, ~50g)": 13.0,
    "Egg white": 11.0,
    "Greek yogurt, plain": 10.0,
    "Regular yogurt, plain": 3.5,
    "Milk, whole": 3.3,
    "Cottage cheese": 11.0,
    "Cheddar cheese": 25.0,
    "Mozzarella cheese": 22.0,
    "Tofu, firm": 15.0,
    "Tempeh": 19.0,
    "Edamame (cooked)": 11.0,
    "Lentils (cooked)": 9.0,
    "Chickpeas (cooked)": 9.0,
    "Black beans (cooked)": 8.9,
    "Kidney beans (cooked)": 8.7,
    "Peanut butter": 25.0,
    "Almonds": 21.0,
    "Peanuts": 26.0,
    "Quinoa (cooked)": 4.4,
    "Brown rice (cooked)": 2.6,
    "White rice (cooked)": 2.7,
    "Oats, dry": 13.0,
    "Whole wheat bread": 13.0,
    "White bread": 9.0,
    "Pasta, cooked": 5.8,
    "Broccoli (cooked)": 2.8,
    "Spinach (cooked)": 3.0,
    "Whey protein powder (per scoop ~30g)": 24.0,
    "Plant protein powder (per scoop ~30g)": 21.0,
    "Bacon (cooked)": 37.0,
    "Turkey breast (cooked)": 29.0,
    "Sausage (pork)": 17.0,
    "Hummus": 8.0,
    "Soy milk": 3.3,
}


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
# Sidebar - daily goal
# ---------------------------------------------------------
st.sidebar.header("Settings")
daily_goal = st.sidebar.number_input(
    "Daily protein goal (g)", min_value=0, max_value=400, value=120, step=5
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data is stored locally in `food_log.csv` next to the app. "
    "Deploy on Streamlit Community Cloud and note that storage resets "
    "on redeploy unless you connect a database."
)

# ---------------------------------------------------------
# Main - log a food
# ---------------------------------------------------------
st.title("🥩 Protein Tracker")
st.write("Log what you eat and track your daily protein intake.")

with st.form("log_food_form", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])

    with col1:
        food_choice = st.selectbox(
            "Food", options=["-- custom food --"] + sorted(FOOD_DB.keys())
        )

    custom_name, custom_protein = None, None
    if food_choice == "-- custom food --":
        custom_name = st.text_input("Custom food name")
        custom_protein = st.number_input(
            "Protein per 100g (g)", min_value=0.0, max_value=100.0, value=20.0, step=0.5
        )

    with col2:
        grams = st.number_input("Amount (g)", min_value=1, max_value=2000, value=100, step=10)

    submitted = st.form_submit_button("Add entry", use_container_width=True)

    if submitted:
        if food_choice == "-- custom food --":
            if not custom_name:
                st.error("Please enter a name for the custom food.")
            else:
                add_entry(custom_name, grams, custom_protein)
                st.success(f"Added {custom_name} ({grams}g)")
        else:
            add_entry(food_choice, grams, FOOD_DB[food_choice])
            st.success(f"Added {food_choice} ({grams}g)")

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
    st.info("No entries yet today. Log your first food above!")
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
