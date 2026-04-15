import streamlit as st
import paho.mqtt.client as mqtt
import json
import threading
import time
import pandas as pd

# --- UI Configuration ---
st.set_page_config(page_title="CityNet Operations", page_icon="🌐", layout="wide")
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "raju_btech_2026/smartcity/waste/#" # Must match ESP32

# Custom CSS for a professional dark mode look
st.markdown("""
    <style>
    .metric-card { background-color: #1E1E1E; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50; margin-bottom: 15px;}
    .critical-card { border-left: 5px solid #FF4B4B;}
    .wet-badge { background-color: #8B4513; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;}
    .dry-badge { background-color: #2196F3; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;}
    .mixed-badge { background-color: #9E9E9E; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- Thread-Safe Data Store ---
@st.cache_resource
def get_fleet_data():
    return {
        "NODE_000_SIM": {"location": "Server Init", "fill": 0.0, "weight": 0.0, "class": "Standby", "time": "--:--"}
    }

fleet_data = get_fleet_data()

# --- MQTT Background Thread ---
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        n_id = data.get("node_id")
        if n_id:
            fleet_data[n_id] = {
                "location": data.get("location", "Unknown"),
                "fill": float(data.get("fill_percentage", 0)),
                "weight": float(data.get("weight_kg", 0)),
                "class": data.get("classification", "Unknown"),
                "time": time.strftime("%H:%M:%S")
            }
    except:
        pass

@st.cache_resource
def init_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    threading.Thread(target=client.loop_forever, daemon=True).start()
    return client

init_mqtt()

# --- Dashboard Layout ---
st.title("🌐 Smart City Edge Intelligence")
st.markdown("**Automated Waste Density Classification & Routing System**")

# Analytics Row
nodes_online = len([k for k in fleet_data.keys() if "SIM" not in k])
critical_nodes = sum(1 for d in fleet_data.values() if d['fill'] >= 85)

c1, c2, c3 = st.columns(3)
with c1:
    st.info(f"📡 **Active Edge Nodes:** {nodes_online}")
with c2:
    st.error(f"🚨 **Critical Bins (>85%):** {critical_nodes}")
with c3:
    st.success(f"⚡ **Network Protocol:** MQTT / WSN")

st.divider()
st.subheader("Real-Time Fleet Telemetry")

# Generate Dynamic UI Cards
cols = st.columns(3)
idx = 0

for node_id, metrics in fleet_data.items():
    if "SIM" in node_id and nodes_online > 0:
        continue # Hide simulator data once real data arrives
        
    with cols[idx % 3]:
        # Determine styling based on state
        is_critical = metrics['fill'] >= 85
        card_class = "metric-card critical-card" if is_critical else "metric-card"
        
        badge_html = f"<span class='mixed-badge'>{metrics['class']}</span>"
        if "DRY" in metrics['class']:
            badge_html = f"<span class='dry-badge'>{metrics['class']}</span>"
        elif "WET" in metrics['class']:
            badge_html = f"<span class='wet-badge'>{metrics['class']}</span>"

        # Action Logic
        action = "✅ Route Optimal"
        if is_critical:
            action = "🚛 DISPATCH: Compost/Organic Truck" if "WET" in metrics['class'] else "🚛 DISPATCH: Recycling Truck"

        # Render the HTML card
        st.markdown(f"""
        <div class="{card_class}">
            <h4>{node_id}</h4>
            <p style="color: gray; margin-top:-10px;">📍 {metrics['location']} | ⏱️ {metrics['time']}</p>
            {badge_html}
            <div style="margin-top: 15px;">
                <strong>Volume Level:</strong> {int(metrics['fill'])}%
            </div>
        """, unsafe_allow_html=True)
        
        # Native Streamlit Progress Bar
        st.progress(int(metrics['fill']) / 100.0)
        
        # Bottom details
        st.markdown(f"""
            <strong>Current Mass:</strong> {metrics['weight']:.1f} kg <br>
            <strong>System Action:</strong> <span style="color: {'#FF4B4B' if is_critical else '#4CAF50'}">{action}</span>
        </div>
        """, unsafe_allow_html=True)
        
    idx += 1

# Silent Polling Loop
time.sleep(2)
st.rerun()