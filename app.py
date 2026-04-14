import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
st.set_page_config(page_title="Air Quality & Health Dashboard", page_icon="🌍", layout="wide")

# IMPORTANT: Replace this with your actual OpenWeatherMap API Key
API_KEY = "f7c41b7f0c3edcec6de8f1e1f65aebc0"

# --- UI: HEADER & LOCATION INPUT ---
st.title("🌍 Real-Time Air Quality & Health Risk Dashboard")

# Display the exact time the data was requested
current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
st.caption(f"🔄 Data requested and live-synced on: **{current_time}**")

st.markdown("Enter your city below to get a real-time health analysis based on current atmospheric sensors.")

# The search bar for the user
city = st.text_input("Enter City Name (e.g., Pune, Mumbai, London):", "Pune")

if city:
    # --- STEP 1: GEOCODING ---
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
    geo_response = requests.get(geo_url).json()
    
    if isinstance(geo_response, dict):
        st.error(f"API Error: {geo_response.get('message', 'Unknown API Error')}")
        
    elif len(geo_response) == 0:
        st.warning("City not found. Please check the spelling.")
        
    else:
        lat = geo_response[0]['lat']
        lon = geo_response[0]['lon']
        
        # --- STEP 2: FETCH AIR POLLUTION DATA ---
        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={API_KEY}"
        raw_data = requests.get(aqi_url).json()
        
        # --- STEP 3: DATA PREPARATION ---
        timestamps, aqi_list, pm25, pm10, no2 = [], [], [], [], []
        
        for item in raw_data['list']:
            timestamps.append(datetime.fromtimestamp(item['dt']))
            aqi_list.append(item['main']['aqi']) 
            pm25.append(item['components']['pm2_5'])
            pm10.append(item['components']['pm10'])
            no2.append(item['components']['no2'])

        df = pd.DataFrame({
            'Datetime': timestamps, 
            'AQI': aqi_list,
            'PM2.5': pm25, 
            'PM10': pm10, 
            'NO2': no2
        })
        df.set_index('Datetime', inplace=True)

        # --- STEP 4: CALCULATE CURRENT METRICS ---
        current_aqi = int(df['AQI'].iloc[0])
        current_pm25 = df['PM2.5'].iloc[0]
        cigarettes_smoked = max(0, round(current_pm25 / 22.0, 1))
        
        aqi_map = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        aqi_text = aqi_map.get(current_aqi, "Unknown")
        
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
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current PM2.5", f"{current_pm25} μg/m³")
        col2.metric("Overall AQI", f"{current_aqi} ({aqi_text})")
        col3.metric("Health Status", status.split(" ", 1)[1] if " " in status else status)
        col4.metric("Cigarette Equivalent", f"🚬 {cigarettes_smoked} cigs")

        st.info(f"**Recommendation:** {action}  \n**Suggested Gear:** {gear}")

        # --- STEP 6: VISUALIZATION & CONCLUSIONS ---
        st.subheader("📈 5-Day Pollution Forecast & Analysis")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # 1. Draw the Trend Plot
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            sns.lineplot(data=df, x=df.index, y='PM2.5', ax=ax1, color='crimson', label="PM2.5 Concentration")
            ax1.axhline(y=15, color='red', linestyle='--', label='WHO Safe Limit')
            ax1.set_title("PM2.5 Trend (Next 120 Hours)")
            ax1.set_ylabel("μg/m³")
            ax1.tick_params(axis='x', rotation=45)
            ax1.legend()
            st.pyplot(fig1)
            
            st.markdown("""
            **💡 Trend Analysis:** This line charts the forecasted microscopic dust (PM2.5) over the next 5 days. 
            * **The Red Dashed Line** represents the WHO's maximum safe exposure limit (15 μg/m³). 
            * If the solid line repeatedly spikes at the same time every day, it indicates a strong routine pollution source, such as daily rush-hour traffic or industrial shifts. 
            """)
            
        with chart_col2:
            # 1. Draw the Heatmap Plot
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            corr = df[['AQI', 'PM2.5', 'PM10', 'NO2']].corr()
            sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax2, vmin=-1, vmax=1)
            ax2.set_title("Pollutant & AQI Correlation Heatmap")
            st.pyplot(fig2)
            
            st.markdown("""
            **💡 Deep Correlation Analysis:** A heatmap shows how variables interact (1.0 means perfect correlation).
            * **PM2.5 vs PM10:** These are usually highly correlated (close to 1.0) because both are dust particles. PM10 is coarse dust (like construction), while PM2.5 is fine smoke.
            * **AQI vs Pollutants:** Look at which pollutant has the highest correlation with AQI. That specific gas/dust is the primary "culprit" driving your city's bad air quality.
            * **The NO₂ Factor:** Nitrogen Dioxide (NO₂) is primarily emitted by burning fuel (vehicle exhaust). If NO₂ has a high correlation with PM2.5, your city's pollution is heavily traffic-driven rather than dust-driven.
            """)

        # --- STEP 7: AI ROUTINE PLANNER ---
        st.divider()
        st.subheader("📅 AI Routine & Activity Planner (Next 24 Hours)")
        
        # Slice the next 24 hours of data
        df_24h = df.head(24)
        
        # Find the safest and worst hours
        best_time_idx = df_24h['PM2.5'].idxmin()
        worst_time_idx = df_24h['PM2.5'].idxmax()
        
        best_val = df_24h.loc[best_time_idx, 'PM2.5']
        worst_val = df_24h.loc[worst_time_idx, 'PM2.5']
        
        # Format the times for readability
        best_time_str = best_time_idx.strftime('%A at %I:%M %p')
        worst_time_str = worst_time_idx.strftime('%A at %I:%M %p')

        # Display the routine recommendations
        plan_col1, plan_col2 = st.columns(2)
        
        with plan_col1:
            st.success(f"### 🏃‍♂️ Safest Time to Go Out\n**{best_time_str}**")
            st.write(f"**Expected PM2.5:** {best_val:.1f} μg/m³")
            st.write("*This is the optimal window for outdoor activities, exercising, or opening the windows in your house to let fresh air in.*")
            
        with plan_col2:
            st.error(f"### 🛑 Time to Stay Indoors\n**{worst_time_str}**")
            st.write(f"**Expected PM2.5:** {worst_val:.1f} μg/m³")
            st.write("*During this hour, pollution peaks. Avoid heavy outdoor exertion, keep windows closed, and run an air purifier if you have one.*")
