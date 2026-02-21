import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium

# ================= API KEYS =================
SARVAM_API_KEY = "sk_9in4zpct_G6oDTi41kwrA0I6FAkWQLKUr"
OPENROUTER_API_KEY = "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"

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="AdiAdvisor — Crop Residue AI",
    layout="wide"
)

st.title("🌾 AdiAdvisor — AI Stubble Management System")

# ================= SIDEBAR =================
st.sidebar.header("🚜 Farmer Inputs")

field_size = st.sidebar.slider("Field Size (acres)", 1, 200, 5)

crop = st.sidebar.selectbox(
    "Crop Type",
    ["Rice", "Wheat", "Maize", "Sugarcane"]
)

location = st.sidebar.selectbox(
    "Location",
    ["Punjab", "Haryana", "Uttar Pradesh", "Rajasthan"]
)

equipment = st.sidebar.multiselect(
    "Available Equipment",
    ["Tractor", "Baler", "Shredder", "Happy Seeder", "None"]
)

language = st.sidebar.selectbox(
    "Language",
    ["English", "Hindi"]
)

# ================= BIOMASS ESTIMATION =================
residue_data = {
    "Rice": 2.5,
    "Wheat": 2.0,
    "Maize": 3.0,
    "Sugarcane": 4.5
}

residue_per_acre = residue_data[crop]
residue_tonnage = field_size * residue_per_acre

st.subheader("📊 Residue Biomass Estimation")
col1, col2 = st.columns(2)

col1.metric("Residue per Acre (tons)", residue_per_acre)
col2.metric("Total Residue (tons)", round(residue_tonnage, 2))

# ================= OPTION DATABASE =================
options = [
    {
        "name": "Biochar Production",
        "setup": 35000,
        "price": 4200,
        "equipment_needed": ["Tractor"]
    },
    {
        "name": "Pellet Manufacturing",
        "setup": 60000,
        "price": 4600,
        "equipment_needed": ["Baler"]
    },
    {
        "name": "Composting",
        "setup": 12000,
        "price": 1600,
        "equipment_needed": []
    },
    {
        "name": "Direct Incorporation",
        "setup": 6000,
        "price": 900,
        "equipment_needed": ["Happy Seeder"]
    }
]

# ================= ROI ENGINE =================
results = []

for opt in options:

    penalty = 1.0
    for eq in opt["equipment_needed"]:
        if eq not in equipment:
            penalty *= 0.7

    income = residue_tonnage * opt["price"] * penalty
    net_profit = income - opt["setup"]

    breakeven_years = opt["setup"] / max(income, 1)

    feasibility = "High"
    if penalty < 0.8:
        feasibility = "Medium"
    if penalty < 0.5:
        feasibility = "Low"

    results.append({
        "Option": opt["name"],
        "Setup Cost (₹)": opt["setup"],
        "Income (₹)": int(income),
        "Net Profit (₹)": int(net_profit),
        "Break-even (years)": round(breakeven_years, 2),
        "Feasibility": feasibility
    })

df = pd.DataFrame(results)
df = df.sort_values("Net Profit (₹)", ascending=False)

st.subheader("💰 Alternatives Ranked by Profit")
st.dataframe(df, use_container_width=True)

best_option = df.iloc[0]["Option"]

st.success(f"🏆 Recommended Option: {best_option}")

# ================= BUYER MAP =================
st.subheader("🗺️ Nearby Buyers / Processing Units")

coords = {
    "Punjab": [31.1471, 75.3412],
    "Haryana": [29.0588, 76.0856],
    "Uttar Pradesh": [26.8467, 80.9462],
    "Rajasthan": [26.9124, 75.7873]
}

m = folium.Map(location=coords[location], zoom_start=7)

buyers = [
    ("Biomass Power Plant", 0.4, 0.2),
    ("Pellet Factory", -0.5, -0.3),
    ("Biochar Unit", 0.2, -0.4),
    ("Compost Center", -0.2, 0.5),
]

for name, dx, dy in buyers:
    folium.Marker(
        [coords[location][0] + dx, coords[location][1] + dy],
        popup=name,
        icon=folium.Icon(color="green")
    ).add_to(m)

st_folium(m, width=900)

# ================= SARVAM TRANSLATION =================
def to_hindi(text):
    url = "https://api.sarvam.ai/v1/translate"
    headers = {"Authorization": f"Bearer {SARVAM_API_KEY}"}

    payload = {
        "source_language": "en-IN",
        "target_language": "hi-IN",
        "text": text
    }

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code == 200:
        return r.json().get("translated_text", text)
    return text

# ================= ADVISORY TEXT =================
advisory = f"""
For your {field_size}-acre {crop} farm in {location},
estimated residue is {residue_tonnage:.2f} tons.

Most profitable alternative to burning:
➡️ {best_option}

Adopting this can generate income while reducing air pollution.
"""

if language == "Hindi":
    advisory = to_hindi(advisory)

st.subheader("🤖 AI Advisory")
st.info(advisory)

# ================= ADVANCED AI STRATEGY =================
if st.button("🧠 Generate Detailed Action Plan"):

    prompt = f"""
Create a step-by-step practical plan for a farmer in {location}
with {field_size} acres of {crop}
to implement {best_option} instead of burning.
Include cost-saving tips and how to sell residue.
"""

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }

    r = requests.post(url, headers=headers, json=data)

    try:
        plan = r.json()["choices"][0]["message"]["content"]
    except:
        plan = "AI service unavailable."

    if language == "Hindi":
        plan = to_hindi(plan)

    st.write(plan)

# ================= FOOTER =================
st.caption("AdiAdvisor — AI for Clean Air & Profitable Farming 🌱")
