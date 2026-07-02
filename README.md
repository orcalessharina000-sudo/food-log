# 🥩 Protein Tracker

A simple Streamlit app to log the food you eat and track your daily protein intake.

## Features
- Log food from a built-in database of ~40 common foods (protein per 100g) or add a custom food
- Automatically calculates protein consumed based on the amount eaten
- Daily progress bar against a protein goal you set
- Full history with a bar chart of protein per day
- Delete individual log entries
- Data saved locally to `food_log.csv`

## Run locally

```bash
git clone https://github.com/<your-username>/protein-tracker.git
cd protein-tracker
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Deploy for free (Streamlit Community Cloud)

1. Push this folder to a new GitHub repository.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click "New app", pick your repo/branch, and set the main file to `app.py`.
4. Deploy. You'll get a public URL you can use from your phone.

> Note: Streamlit Community Cloud's filesystem is not permanent — `food_log.csv`
> may reset when the app redeploys or sleeps. For a tracker you use long-term,
> consider swapping the CSV storage for a small database (e.g. Google Sheets,
> Supabase, or SQLite on a persistent volume). Ask if you'd like help wiring
> one of those up.

## Project structure

```
protein-tracker/
├── app.py             # Streamlit app
├── requirements.txt   # Python dependencies
└── README.md
```

## Customizing the food database

Open `app.py` and edit the `FOOD_DB` dictionary near the top — it maps a food
name to grams of protein per 100g. Add, remove, or adjust values as needed.
