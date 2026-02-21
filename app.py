import streamlit as st
import requests
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from gtts import gTTS
import tempfile

OPENROUTER_API_KEY = "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"

st.set_page_config(layout="wide")
st.title("🌾 AdiAdvisor Ω — National Anti-Burning AI")

# ================= LOCATION =================

location = st.text_input("Enter village/district",
                         "Karnal, Haryana")

geo = Nominatim(user_agent="adiadvisor")
loc_data = geo.geocode(location)

if loc_data:
    farmer_loc = (loc_data.latitude,
                  loc_data.longitude)
else:
    farmer_loc = (29.6857, 76.9905)

# ================= FIELD DRAW MAP =================

st.subheader("🛰️ Draw Your Field")

m = folium.Map(location=farmer_loc,
               zoom_start=15)

# Satellite tiles
folium.TileLayer(
    tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    name="Satellite",
    attr="Satellite"
).add_to(m)

field = st_folium(m, height=500)

# Estimate area manually
area = st.number_input("Field size (hectares)",
                       0.1, 100.0, 2.0)

crop = st.selectbox("Crop",
                    ["Rice","Wheat",
                     "Maize","Sugarcane"])

# ================= BIOMASS =================

factor = {"Rice":2.6,
          "Wheat":1.6,
          "Maize":2.1,
          "Sugarcane":3.2}

biomass = area * factor[crop]

st.metric("📡 Residue Estimate (tons)",
          f"{biomass:.1f}")

# ================= BUYERS =================

buyers = [
    ("Biomass Power Plant",
     (29.70,76.99), 5200),

    ("Pellet Factory",
     (29.65,77.05), 5400),

    ("Compost Unit",
     (29.72,76.90), 2600)
]

st.subheader("🚛 Nearby Buyers")

m2 = folium.Map(location=farmer_loc,
                zoom_start=9)

for name, loc, price in buyers:

    dist = geodesic(farmer_loc, loc).km
    transport = dist * 40
    net = biomass * price - transport

    folium.Marker(
        loc,
        popup=f"{name}\nDistance {dist:.1f} km\nNet ₹{int(net)}"
    ).add_to(m2)

st_folium(m2)

# ================= CARBON =================

co2 = biomass * 1.5
carbon_value = co2 * 20

st.subheader("🌍 Climate Impact")

col1, col2 = st.columns(2)

col1.metric("CO₂ Avoided (tons)",
            f"{co2:.1f}")

col2.metric("Carbon Value ($)",
            f"{carbon_value:.0f}")

# ================= SUBSIDIES =================

st.subheader("🏛️ Government Schemes")

schemes = {
    "Rice":"Happy Seeder subsidy up to 50%",
    "Wheat":"Crop residue management scheme",
    "Maize":"Composting incentives",
    "Sugarcane":"Bioenergy linkage program"
}

st.info(schemes[crop])

# ================= BURN RISK =================

risk = 30
if area > 5:
    risk += 20
if biomass > 10:
    risk += 20

st.subheader("🔥 Burning Risk")
st.progress(min(risk,100))

# ================= AI PLAN =================

prompt = f"""
Farmer in {location} has {area} ha {crop}.
Residue {biomass:.1f} tons.
Give step-by-step plan to avoid burning,
sell residue, maximize profit.
"""

def ask_ai(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model":"mistralai/mistral-7b-instruct",
        "messages":[{"role":"user",
                     "content":prompt}]
    }

    r = requests.post(url,
                      headers=headers,
                      json=data)

    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]

    return "AI unavailable"

if st.button("🤖 Generate Action Plan"):

    advice = ask_ai(prompt)

    st.success(advice)

    # TEXT TO SPEECH
    tts = gTTS(advice)
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tts.save(tmp.name)

    st.audio(tmp.name)

# ================= DOWNLOAD =================

df = pd.DataFrame({
    "Location":[location],
    "Crop":[crop],
    "Area":[area],
    "Biomass":[biomass],
    "CO2":[co2],
    "CarbonValue":[carbon_value]
})

st.download_button("📄 Download Report",
                   df.to_csv(index=False),
                   file_name="adiadvisor_report.csv")
