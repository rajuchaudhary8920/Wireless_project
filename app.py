import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import threading
import time

# --- Configuration ---
st.set_page_config(page_title="Smart City Waste Dispatch", page_icon="♻️", layout="wide")
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "btech/smartcity/waste/#"

# --- Initialize Data Storage ---
if 'bins' not in st.session_state:
    # Simulating some existing bins, plus the one you will connect from Wokwi
    st.session_state.bins = {
        "BIN_001": {"location": "North Campus", "fill_percentage": 25.0, "status": "Normal"},
        "BIN_002": {"location": "South Campus", "fill_percentage": 10.0, "status": "Normal"}
    }

# --- MQTT Setup (Runs in background) ---
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        # Expecting JSON like: {"bin_id": "BIN_003", "location": "Library", "fill_percentage": 88.5}
        payload = json.loads(msg.payload.decode('utf-8'))
        bin_id = payload.get("bin_id")
        
        if bin_id:
            fill = float(payload.get("fill_percentage", 0))
            status = "🚨 DISPATCH TRUCK" if fill >= 85.0 else "Normal"
            
            st.session_state.bins[bin_id] = {
                "location": payload.get("location", "Unknown"),
                "fill_percentage": fill,
                "status": status
            }
    except Exception as e:
        pass # Ignore bad messages

@st.cache_resource
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    # Run MQTT loop in a background thread so it doesn't freeze the dashboard
    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()
    return client

start_mqtt()

# --- Dashboard UI ---
st.title("♻️ Smart City Waste Dispatch Center")
st.markdown("Real-time IoT telemetry monitoring for municipal waste management.")

# Auto-refresh the Streamlit UI every 2 seconds to show live data
st.markdown("""
    <meta http-equiv="refresh" content="2">
""", unsafe_allow_html=True)

# Convert our dictionary to a Pandas DataFrame for easy display
df = pd.DataFrame.from_dict(st.session_state.bins, orient='index').reset_index()
df.rename(columns={'index': 'Bin ID', 'location': 'Location', 'fill_percentage': 'Fill Level (%)', 'status': 'Action Required'}, inplace=True)

# Top Metrics
total_bins = len(df)
critical_bins = len(df[df['Action Required'] == "🚨 DISPATCH TRUCK"])

col1, col2 = st.columns(2)
col1.metric("Total Monitored Bins", total_bins)
col2.metric("Critical Bins (Needs Pickup)", critical_bins, delta=critical_bins, delta_color="inverse")

st.divider()

# Display the Data
st.subheader("Live Fleet Status")
# Highlight critical rows in red
def highlight_critical(val):
    color = '#ff4b4b' if val == '🚨 DISPATCH TRUCK' else ''
    return f'background-color: {color}'

st.dataframe(df.style.map(highlight_critical, subset=['Action Required']), use_container_width=True)

# Visual Bar Chart
st.subheader("Fill Levels Overview")
st.bar_chart(data=df, x='Bin ID', y='Fill Level (%)')