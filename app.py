import streamlit as st
import pandas as pd
from queue import Queue
import threading
import time
import sqlite3

# Custom component bindings
from data_stream import sensor_producer
from ml_engine import TrainedModelEngine
from database import init_db, log_alert_to_db, fetch_historical_alerts

# --- WEB UI INTERFACE CONFIGURATION ---
st.set_page_config(page_title="IIoT Predictive Maintenance Platform", layout="wide")
st.title("🏭 Real-Time System Monitoring & AI Fault Detection")
st.markdown("---")

if st.checkbox("Show Entire Fault Database History",key="unique_db_history_check"):
        conn = sqlite3.connect("faults.db")
        df_all = pd.read_sql_query("SELECT * FROM system_alerts ORDER BY id DESC", conn)
        st.dataframe(df_all)
        conn.close()
            
# Initialize the local SQLite database
init_db()

# --- INITIALIZE MULTI-THREADED ASYNCHRONOUS PIPELINE ---
if "data_queue" not in st.session_state:
    st.session_state.data_queue = Queue()
    st.session_state.engine = TrainedModelEngine()
    st.session_state.temp_history = []
    st.session_state.vib_history = []
    st.session_state.press_history = []

    # Fire background data production worker thread
    producer_thread = threading.Thread(
        target=sensor_producer, 
        args=(st.session_state.data_queue,), 
        daemon=True
    )
    producer_thread.start()

# --- INSTANTIATE DASHBOARD LAYOUT CONFIGURATIONS ---
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    temp_metric = st.empty()
with kpi_col2:
    vib_metric = st.empty()
with kpi_col3:
    press_metric = st.empty()
with kpi_col4:
    status_metric = st.empty()

st.markdown("### Live Telemetry Visualizations")
chart_col1, chart_col2, chart_col3 = st.columns(3)
with chart_col1:
    st.subheader("Temperature (°C)")
    temp_chart = st.empty()
with chart_col2:
    st.subheader("Vibration Speed (mm/s)")
    vib_chart = st.empty()
with chart_col3:
    st.subheader("Hydraulic Pressure (bar)")
    press_chart = st.empty()

st.markdown("### 🚨 Persistent System Alerts Log (Stored in SQLite)")
alert_table = st.empty()

# --- CONTINUOUS MAIN CONSOLE RUN LOOP ---
while True:
    new_fault_flagged = False
    
    # Process all newly arrived metrics inside the queue buffer
    while not st.session_state.data_queue.empty():
        packet = st.session_state.data_queue.get()
        
        curr_temp = packet["temperature"]
        curr_vib = packet["vibration"]
        curr_press = packet["pressure"]
        
        # Update sliding history records
        st.session_state.temp_history.append(curr_temp)
        st.session_state.vib_history.append(curr_vib)
        st.session_state.press_history.append(curr_press)
        
        if len(st.session_state.temp_history) > 100:
            st.session_state.temp_history.pop(0)
            st.session_state.vib_history.pop(0)
            st.session_state.press_history.pop(0)
            
        # --- RUN INFERENCE ENGINE AGAINST TRAINED MODEL ---
        try:
            model_prediction = st.session_state.engine.predict_live_data(
                curr_vib, curr_temp, curr_press, 
                st.session_state.vib_history, st.session_state.temp_history
            )
            
            # Catch Model Anomalies
            if model_prediction in [1, 1.0, "1", True]:
                new_fault_flagged = True
                log_alert_to_db("CRITICAL", "AI Model predicted an active fault state!")
            
            # Hardware Threshold Fallback Anomaly
            if curr_temp > 85.0 or curr_vib > 5.5:
                log_alert_to_db("WARNING", f"Safety threshold breach! Temp: {curr_temp}°C, Vib: {curr_vib}mm/s")

        except Exception as inference_error:
            st.error(f"Inference Pipeline Failure: {inference_error}")

    # --- UI RENDER REFRESH LOGIC ---
    if st.session_state.temp_history:
        latest_t = st.session_state.temp_history[-1]
        latest_v = st.session_state.vib_history[-1]
        latest_p = st.session_state.press_history[-1]
        
        # Display Big Numbers
        temp_metric.metric("Temperature", f"{latest_t} °C")
        vib_metric.metric("Vibration Speed", f"{latest_v} mm/s")
        press_metric.metric("System Pressure", f"{latest_p} bar")
        
        # Read directly from SQL database to display the table
        db_alerts = fetch_historical_alerts(limit=10)
        
        # Evaluate machine health status badge
        if new_fault_flagged or (db_alerts and db_alerts[0]["Severity"] == "CRITICAL"):
            status_metric.error("STATUS: ANOMALY")
        else:
            status_metric.success("STATUS: NOMINAL")
            
        # Push vector lines to plots
        temp_chart.line_chart(st.session_state.temp_history)
        vib_chart.line_chart(st.session_state.vib_history)
        press_chart.line_chart(st.session_state.press_history)
        
        # Update the Alert logs viewport from Database records
        if db_alerts:
            alert_table.dataframe(pd.DataFrame(db_alerts), use_container_width=True)
    
    time.sleep(0.3)