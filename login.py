import streamlit as st
import requests
import pandas as pd
import pymysql
import hashlib
import base64
import os

# Konfigurasi halaman utama
st.set_page_config(page_title="Login", page_icon="🔐", layout="wide")

# Fungsi koneksi database
def get_connection():
    return pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"],
        ssl={'ssl': {}},
        cursorclass=pymysql.cursors.DictCursor
    )

def hash_password(password):
    salt = os.urandom(16)
    salted_password = password.encode() + salt
    hashed_password = hashlib.sha256(salted_password).hexdigest()
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    return hashed_password, salt_b64

# Login user
def login_user(username, password):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
        conn.close()

        if user:
            stored_salt = base64.b64decode(user['salt'].encode('utf-8'))
            salted_password = password.encode() + stored_salt
            hashed_input_password = hashlib.sha256(salted_password).hexdigest()

            if hashed_input_password == user['password']:
                return user
            else:
                return None
        else:
            return None
    except Exception as e:
        return None

# Ambil user berdasarkan username (untuk validasi ulang saat session aktif)
def get_user_from_db(username):
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        st.error(f"❌ Error checking user from DB: {e}")
        return None

# Session state
if "role" not in st.session_state:
    st.session_state.role = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Validasi awal agar tidak bisa login jika user sudah dihapus dari DB
if st.session_state.get("logged_in", False):
    user_check = get_user_from_db(st.session_state.username)
    if not user_check:
        st.warning("⚠️ Akun Anda sudah tidak ada di database. Session akan direset.")
        for key in ["logged_in", "username", "role"]:
            st.session_state[key] = None if key == "role" else False if key == "logged_in" else ""
        st.experimental_rerun()

# Sidebar login/logout
with st.sidebar:
    st.title("🔐 Login System")

    if not st.session_state.logged_in:
        st.subheader("🔑 Login")
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        if st.button("🔓 Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.role = user['role']
                st.session_state.username = user['username']
                st.success(f"✅ Selamat datang, {user['username']} sebagai {user['role']}!")
                st.rerun()
            else:
                st.error("❌ Username atau password salah!")

    else:
        st.success(f"✅ Anda masuk sebagai **{st.session_state.role}**")
        if st.button("🔓 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role = None
            st.session_state.username = ""
            st.rerun()

# Header dengan tampilan lebih profesional
st.markdown(
    f"""
    <div style="text-align: center; padding: 15px; background-color: {'#2C3E50' if st.session_state.logged_in else '#34495E'}; 
    border-radius: 10px; color: white; font-size: 24px;">
        {'✅ Welcome ' + st.session_state.role  if st.session_state.logged_in else '🔐 Welcome to the Management System.'}
    </div>
    """,
    unsafe_allow_html=True
)

# Halaman sebelum login agar tidak kosong
if not st.session_state.logged_in:
    st.markdown(
        """
        <div style="text-align: center;">
            <p style='font-size: 18px; color: gray;'>
                Sistem ini digunakan untuk pengelolaan dan persetujuan SPK oleh Supervisor dan Section Manager.
                Silakan login untuk mengakses fitur.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Menampilkan fitur utama dalam bentuk kartu
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="background-color: #ECF0F1; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #2C3E50;">🔎 Pengelolaan Data SPK</h4>
                <p style="color: gray;">Supervisor dapat menambahkan serta mengupdate Data SPK.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div style="background-color: #ECF0F1; padding: 15px; border-radius: 10px; text-align: center;">
                <h4 style="color: #2C3E50;">📝 Persetujuan Preventive Form</h4>
                <p style="color: gray;">Supervisor & Manager dapat menyetujui atau menolak Preventive Form.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

import overview 
overview.overview()

# Navigasi setelah login
if st.session_state.logged_in:
    st.sidebar.subheader("📂 Pilih Halaman")

    if st.session_state.role == "Supervisor":
        page = st.sidebar.selectbox("📌 Pilih Halaman:", ["Tambah SPK", "Update SPK", "Approval Preventive Form", "Unduh SPK"], index=0)

        if page == "Tambah SPK":
            import add_spk_spv
            add_spk_spv.run()
        elif page == "Update SPK":
            import update_spk_spv
            update_spk_spv.run()
        elif page == "Approval Preventive Form":
            import try_SPV
            try_SPV.run()
        elif page == "Unduh SPK":
            import SPK_by_BU
            SPK_by_BU.run()
            
    elif st.session_state.role == "Section Manager":
        import try_SM
        try_SM.run()
