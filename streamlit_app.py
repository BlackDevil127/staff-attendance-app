import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import math

# --- configuration ---
# Apnar office location (Maps URL theke pawa)
OFFICE_LAT = 23.8103 
OFFICE_LON = 90.4125
DISTANCE_LIMIT = 5  # 5 Meters
ADMIN_PASSWORD = "Time0308"

# --- Database ---
conn = sqlite3.connect('attendance.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS attendance 
             (id INTEGER PRIMARY KEY, staff_name TEXT, date TEXT, 
              in_time TIMESTAMP, out_time TIMESTAMP, last_seen TIMESTAMP)''')
conn.commit()

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 # Meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

# --- Admin Panel ---
st.sidebar.title("Owner Login")
pw = st.sidebar.text_input("Password", type="password")

if pw == ADMIN_PASSWORD:
    st.title("📊 Attendance Report")
    month = st.sidebar.date_input("Select Month", value=datetime.now()).strftime('%Y-%m')
    df = pd.read_sql_query(f"SELECT * FROM attendance WHERE date LIKE '{month}%'", conn)
    st.dataframe(df, use_container_width=True)
else:
    st.title("📍 Staff Attendance Server")
    st.info("Mobile app background-e data pathachche...")

# --- API endpoint logic for Mobile App ---
# Streamlit-e API handle kora complex, tobe amra session state use korte pari
def update_attendance(name, lat, lon):
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    dist = calculate_distance(OFFICE_LAT, OFFICE_LON, lat, lon)
    
    c.execute("SELECT * FROM attendance WHERE staff_name=? AND date=?", (name, today))
    record = c.fetchone()
    
    if dist <= DISTANCE_LIMIT:
        if not record:
            c.execute("INSERT INTO attendance (staff_name, date, in_time, last_seen) VALUES (?, ?, ?, ?)",
                      (name, today, now, now))
        else:
            c.execute("UPDATE attendance SET last_seen=? WHERE staff_name=? AND date=?", (now, name, today))
    else:
        if record and record[4] is None: # out_time empty thakle
            last_seen = datetime.strptime(record[5], '%Y-%m-%d %H:%M:%S.%f')
            if (now - last_seen) > timedelta(hours=1):
                c.execute("UPDATE attendance SET out_time=? WHERE staff_name=? AND date=?", (last_seen, name, today))
    conn.commit()
