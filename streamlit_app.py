import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import math

# --- Configuration ---
OFFICE_LAT = 23.8103  # Apnar Office Latitude ekhane boshan
OFFICE_LON = 90.4125  # Apnar Office Longitude ekhane boshan
DISTANCE_LIMIT = 5    # 5 Meter range
ADMIN_PASSWORD = "Time0308"

# --- Database Setup ---
conn = sqlite3.connect('attendance.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS attendance 
             (id INTEGER PRIMARY KEY, staff_name TEXT, date TEXT, 
              in_time TIMESTAMP, out_time TIMESTAMP, last_seen TIMESTAMP)''')
conn.commit()

# --- Distance Calculation ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# --- UI Setup ---
st.set_page_config(page_title="Staff Attendance WebApp", layout="wide")

menu = ["Staff Tracking", "Owner Dashboard"]
choice = st.sidebar.selectbox("Menu", menu)

# --- Staff Tracking Logic ---
if choice == "Staff Tracking":
    st.title("📍 Staff Attendance (Automatic)")
    name = st.text_input("Apnar Nam Likhun:")
    
    # JavaScript use kore location neya (Streamlit limitation bypass korar jonno)
    location_data = st.query_params.to_dict()
    
    if name:
        # Streamlit e location accurate neyar jonno button dorkar hoy
        if st.button("Start My Shift / Check My Status"):
            # Browser current location (Simulated for Streamlit)
            # Real webApp e HTML5 Geolocation API use kora hoy
            # Ekhane amra demo logic dichi
            st.warning("Please ensure your GPS is ON.")
            
            # For deployment, Streamlit e client side location neya ektu complex.
            # Ekhane amra ekta simplified logic rakhchi:
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            
            # Database check
            c.execute("SELECT * FROM attendance WHERE staff_name=? AND date=?", (name, today))
            record = c.fetchone()
            
            if not record:
                # Prothom bar office e dhukle (In Time)
                c.execute("INSERT INTO attendance (staff_name, date, in_time, last_seen) VALUES (?, ?, ?, ?)",
                          (name, today, now, now))
                conn.commit()
                st.success(f"Swagotom {name}! Apnar In-Time record kora hoyeche: {now.strftime('%H:%M:%S')}")
            else:
                # Out time logic: 1 hour gap check
                last_seen = datetime.strptime(record[5], '%Y-%m-%d %H:%M:%S.%f')
                if (now - last_seen) > timedelta(hours=1):
                    c.execute("UPDATE attendance SET out_time=? WHERE staff_name=? AND date=?", 
                              (last_seen, name, today))
                    conn.commit()
                    st.error(f"Apnar Out-Time record kora hoyeche: {last_seen.strftime('%H:%M:%S')}")
                else:
                    # Update last seen
                    c.execute("UPDATE attendance SET last_seen=? WHERE staff_name=? AND date=?", 
                              (now, name, today))
                    conn.commit()
                    st.info("Tracking active... Apnar location update kora hoyeche.")

# --- Owner Dashboard Logic ---
elif choice == "Owner Dashboard":
    st.title("🔑 Owner Panel")
    password = st.text_input("Admin Password Din:", type="password")
    
    if password == ADMIN_PASSWORD:
        st.success("Login Successful!")
        
        # Monthly Filter
        month = st.date_input("Mas Select Korun:", value=datetime.now())
        month_str = month.strftime('%Y-%m')
        
        query = f"SELECT staff_name, date, in_time, out_time FROM attendance WHERE date LIKE '{month_str}%'"
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            st.write(f"### {month_str} er Attendance Report")
            st.dataframe(df, use_container_width=True)
            
            # Download CSV option
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Report as CSV", data=csv, file_name=f"Report_{month_str}.csv")
        else:
            st.info("Ei mashe kono data nei.")
    elif password:
        st.error("Vul Password! Abar chesta korun.")
