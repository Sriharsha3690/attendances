
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# Connect to SQLite database (creates if not exists)
conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()

# Initialize DB if not exists
def init_db():
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        daily_wage INTEGER DEFAULT 100
    )''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        status TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    conn.commit()

def seed_users():
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        # Add admin
        c.execute("INSERT INTO users (username, role) VALUES (?, ?)", ('admin', 'admin'))
        # Add 10 employees
        for i in range(1, 11):
            c.execute("INSERT INTO users (username, role) VALUES (?, ?)", (f'employee{i}', 'user'))
        conn.commit()

init_db()
seed_users()

# Streamlit UI
st.title("📋 Admin Attendance & Payroll System")

menu = ["Attendance", "Payroll"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Attendance":
    st.subheader("Mark Attendance")
    selected_date = st.date_input("Select Date", value=date.today())
    df = pd.read_sql_query("SELECT * FROM users WHERE role='user'", conn)

    for index, row in df.iterrows():
        status = st.selectbox(f"{row['username']}", ["", "present", "absent"], key=f"status_{row['id']}")
        if status:
            existing = c.execute("SELECT * FROM attendance WHERE user_id=? AND date=?", (row['id'], selected_date)).fetchone()
            if existing:
                c.execute("UPDATE attendance SET status=? WHERE user_id=? AND date=?", (status, row['id'], selected_date))
            else:
                c.execute("INSERT INTO attendance (user_id, date, status) VALUES (?, ?, ?)", (row['id'], selected_date, status))
            conn.commit()
    st.success("✅ Attendance marked for selected date.")

elif choice == "Payroll":
    st.subheader("Payroll Report")
    month = st.text_input("Enter month (YYYY-MM):", value=date.today().strftime('%Y-%m'))
    if month:
        df = pd.read_sql_query("""
            SELECT u.username, u.daily_wage, 
                   COUNT(CASE WHEN a.status = 'present' THEN 1 END) as days_present
            FROM users u LEFT JOIN attendance a ON u.id = a.user_id
            WHERE u.role = 'user' AND a.date LIKE ?
            GROUP BY u.id
        """, conn, params=(month + '%',))
        if not df.empty:
            df['salary'] = df['daily_wage'] * df['days_present']
            st.dataframe(df[['username', 'days_present', 'salary']])
        else:
            st.warning("⚠️ No records found for selected month.")
