import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Air Quality & Health Dashboard", page_icon="🌍", layout="wide")
API_KEY = "5f5d358e200291f8b5ba8c5b504aac0b" # Put your OpenWeatherMap key here!

# --- UI: HEADER & LOCATION INPUT ---
st.title("🌍 Real-Time Air Quality & Health Risk Dashboard")
st.markdown("Enter your city below to get a real-time health analysis based on current atmospheric sensors.")

# The search bar for the user
city = st.text_input("Enter City Name (e.g., Pune, Mumbai, London):", "Pune")

if city:
    # --- STEP 1: GEOCODING (Convert City to Lat/Lon) ---
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    geo_response = requests.get(geo_url).json()
    
    if len(geo_response) == 0:
        st.error("City not found. Please check the spelling.")
    else:
        lat = geo_response[0]['lat']
        lon = geo_response[0]['lon']
        
        # --- STEP 2: FETCH AIR POLLUTION DATA ---
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
        raw_data = requests.get(aqi_url).json()
        
        # --- STEP 3: DATA PREPARATION (Pandas) ---
        timestamps, pm25, pm10, no2 = [], [], [], []
        
        for item in raw_data['list']:
            timestamps.append(datetime.fromtimestamp(item['dt']))
            pm25.append(item['components']['pm2_5'])
            pm10.append(item['components']['pm10'])
            no2.append(item['components']['no2'])

        df = pd.DataFrame({'Datetime': timestamps, 'PM2.5': pm25, 'PM10': pm10, 'NO2': no2})
        df.set_index('Datetime', inplace=True)

        # --- STEP 4: CALCULATE METRICS ---
        current_pm25 = df['PM2.5'].iloc[0]
        cigarettes_smoked = max(0, round(current_pm25 / 22.0, 1)) # Berkeley Earth math
        
        if current_pm25 <= 12.0:
            status, action, gear = "🟢 Good", "Great day to be outside!", "None"
        elif current_pm25 <= 35.4:
            status, action, gear = "🟡 Moderate", "Safe, but limit heavy exertion.", "Light scarf"
        elif current_pm25 <= 55.4:
            status, action, gear = "🟠 Unhealthy for Sensitive", "Limit prolonged outdoor activities.", "Standard mask"
        elif current_pm25 <= 150.4:
            status, action, gear = "🔴 Unhealthy", "Avoid prolonged outdoor exposure.", "N95 Mask"
        else:
            status, action, gear = "🟣 Hazardous", "Strictly stay indoors.", "N95 Mask Mandatory"

        # --- STEP 5: UI LAYOUT & DISPLAY ---
        st.divider()
        st.subheader(f"📍 Live Status for {city.title()}")
        
        # Display large metrics side-by-side
        col1, col2, col3 = st.columns(3)
        col1.metric("Current PM2.5", f"{current_pm25} μg/m³")
        col2.metric("Air Quality Status", status.split(" ")[1])
        col3.metric("Cigarette Equivalent", f"🚬 {cigarettes_smoked} cigs")

        # Display Advice
        st.info(f"**Recommendation:** {action}  \n**Suggested Gear:** {gear}")

        # --- STEP 6: VISUALIZATION (Matplotlib/Seaborn) ---
        st.subheader("📈 5-Day Pollution Forecast & Analysis")
        
        # Create a layout with 2 columns for the graphs
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            sns.lineplot(data=df, x=df.index, y='PM2.5', ax=ax1, color='crimson')
            ax1.axhline(y=15, color='red', linestyle='--', label='WHO Safe Limit')
            ax1.set_title("PM2.5 Trend (Next 120 Hours)")
            ax1.set_ylabel("μg/m³")
            st.pyplot(fig1) # This is how Streamlit renders Matplotlib!
            
        with chart_col2:
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            corr = df[['PM2.5', 'PM10', 'NO2']].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax2)
            ax2.set_title("Pollutant Correlation Heatmap")
            st.pyplot(fig2)
