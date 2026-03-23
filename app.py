import streamlit as st
import paho.mqtt.client as mqtt
import json
import threading
import time

# --- Configuration ---
st.set_page_config(page_title="City Waste Dispatch", page_icon="♻️", layout="wide")
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
# MATCH THE UNIQUE TOPIC HERE
MQTT_TOPIC = "raju_btech_2026/smartcity/waste/#"

# --- Thread-Safe Data Storage ---
# We use cache_resource so the background thread and Streamlit UI share the exact same memory
@st.cache_resource
def get_data_store():
    return {
        "BIN_001": {"location": "North Campus", "fill_percentage": 25.0, "status": "✅ Normal", "last_updated": "--:--:--"},
        "BIN_002": {"location": "South Campus", "fill_percentage": 10.0, "status": "✅ Normal", "last_updated": "--:--:--"}
    }

data_store = get_data_store()

# --- MQTT Setup (Background Thread) ---
def on_connect(client, userdata, flags, rc):
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        bin_id = payload.get("bin_id")
        
        if bin_id:
            fill = float(payload.get("fill_percentage", 0))
            status = "🚨 DISPATCH TRUCK" if fill >= 85.0 else "✅ Normal"
            
            # Update the shared data store
            data_store[bin_id] = {
                "location": payload.get("location", "Unknown"),
                "fill_percentage": fill,
                "status": status,
                "last_updated": time.strftime("%H:%M:%S")
            }
    except Exception as e:
        pass 

@st.cache_resource
def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    thread = threading.Thread(target=client.loop_forever, daemon=True)
    thread.start()
    return client

start_mqtt()

# --- Professional UI ---
st.title("♻️ Municipal Waste Dispatch Dashboard")
st.markdown("Live IoT Telemetry & Routing Center")

# Top Metrics
total_bins = len(data_store)
critical_bins = sum(1 for b in data_store.values() if "DISPATCH" in b["status"])

col1, col2, col3 = st.columns(3)
col1.metric("Active Sensor Nodes", total_bins)
col2.metric("Critical Bins (Action Required)", critical_bins, delta=critical_bins if critical_bins > 0 else None, delta_color="inverse")
col3.metric("Network Status", "Online 🟢")

st.divider()

# --- Dynamic Sensor Cards ---
st.subheader("Live Fleet Status")

# Create a grid layout
cols = st.columns(3)
col_idx = 0

for bin_id, details in data_store.items():
    with cols[col_idx % 3]:
        # Create a visual card for each bin
        with st.container(border=True):
            st.markdown(f"### {bin_id}")
            st.caption(f"📍 {details['location']}")
            
            # Progress bar visualization
            fill_pct = int(details['fill_percentage'])
            st.progress(fill_pct / 100.0, text=f"Capacity: {fill_pct}%")
            
            # Status and timestamp
            if "DISPATCH" in details['status']:
                st.error(details['status'])
            else:
                st.success(details['status'])
                
            st.caption(f"Last ping: {details['last_updated']}")
            
    col_idx += 1

# Silent UI refresh every 3 seconds
time.sleep(3)
st.rerun()