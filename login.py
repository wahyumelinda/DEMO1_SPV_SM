import streamlit as st
import requests
import pandas as pd

# Konfigurasi halaman utama
st.set_page_config(page_title="Login", page_icon="🔐", layout="wide")

# Dummy database (bisa diganti dengan database nyata)
USER = {
    "SPV": {"username": "supervisor", "password": "spv123"},
    "SM": {"username": "manager", "password": "sm123"}
}

# Session state
if "role" not in st.session_state:
    st.session_state.role = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Sidebar untuk navigasi login/logout
with st.sidebar:
    st.title("🔐 Login System")

    if not st.session_state.logged_in:
        st.info("Silakan pilih role untuk login.")
        if st.button("🛠 Supervisor (SPV)", use_container_width=True):
            st.session_state.role = "SPV"
            st.rerun()

        if st.button("📊 Section Manager (SM)", use_container_width=True):
            st.session_state.role = "SM"
            st.rerun()
    else:
        st.success(f"✅ Anda masuk sebagai **{st.session_state.role}**")
        if st.button("🔓 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role = None
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

# URL dari Apps Script Web App
API_URL = "https://script.google.com/macros/s/AKfycbxvwyWXOiVC812g2ZO-Uzr6HtYujXnx7nu75YW26KVH1kCHWUUvh_uXSA65Hc4W-zknpQ/exec"

# Pilihan sheet yang bisa ditampilkan
option = st.selectbox("📂 Pilih Data yang Ingin Dilihat:", ["Data Preventive", "Data SPK"])

# Ambil data sesuai pilihan
if option == "Data Preventive":
    response = requests.get(f"{API_URL}?action=get_all_data")
    expected_columns = [
        "ID", "BU", "Line", "Produk", "Nomor Mesin", "Mesin", "Tanggal Pengerjaan",
        "Mulai", "Selesai", "Masalah", "Tindakan Perbaikan", "Deskripsi",
        "Quantity", "PIC", "Kondisi", "Alasan", "SPV", "Last Update SPV", 
        "Approve", "Reason", "SM", "Last Update SM"
    ]
elif option == "Data SPK":
    response = requests.get(f"{API_URL}?action=get_data")
    expected_columns = [
        "ID", "BU", "Line", "Produk", "Nomor Mesin", "Mesin",
        "Masalah", "Tindakan Perbaikan", "Tanggal Pengerjaan", "PIC", "Last Update"
    ]

# Cek apakah API berhasil mendapatkan data
if response.status_code == 200:
    all_data = response.json()
    
    if isinstance(all_data, list) and len(all_data) > 0:
        df = pd.DataFrame(all_data)
        df = df[[col for col in expected_columns if col in df.columns]]

        # Pastikan nama kolom tanggal sesuai
        if "Tanggal Pengerjaan" in df.columns:
            df["Tanggal Pengerjaan"] = pd.to_datetime(df["Tanggal Pengerjaan"], errors='coerce').dt.date
            df = df.rename(columns={"Tanggal Pengerjaan": "Tanggal"})
        else:
            st.error("Kolom 'Tanggal Pengerjaan' tidak ditemukan dalam data API!")

        # === Fungsi untuk Filter ===
        def filter_data(df):
            st.sidebar.header("Filter Data (Opsional)")
            
            # Filter berdasarkan PIC
            pic_options = df["PIC"].dropna().unique().tolist()
            selected_pic = st.sidebar.multiselect("Pilih PIC", pic_options)
            
            # Filter berdasarkan rentang tanggal
            min_date, max_date = df["Tanggal"].min(), df["Tanggal"].max()
            date_range = st.sidebar.date_input("Pilih Rentang Tanggal", [min_date, max_date], min_value=min_date, max_value=max_date)
            
            # Terapkan filter
            df_filtered = df.copy()
            if selected_pic:
                df_filtered = df_filtered[df_filtered["PIC"].isin(selected_pic)]
            if len(date_range) == 2:
                start_date, end_date = date_range
                df_filtered = df_filtered[(df_filtered["Tanggal"] >= start_date) & (df_filtered["Tanggal"] <= end_date)]
            
            return df_filtered
        
        df_filtered = filter_data(df)

        # === Pagination ===
        items_per_page = 10
        total_pages = max(1, -(-len(df_filtered) // items_per_page))
        page_number = st.sidebar.number_input("Pilih Halaman", min_value=1, max_value=total_pages, value=1, step=1)
        
        start_idx = (page_number - 1) * items_per_page
        end_idx = start_idx + items_per_page
        df_paginated = df_filtered.iloc[start_idx:end_idx]
        
        # === Tampilkan Data ===
        st.subheader(f"{option} (Menampilkan Halaman {page_number} dari {total_pages})")
        st.dataframe(df_paginated, use_container_width=True)
        st.caption(f"Menampilkan {len(df_paginated)} dari {len(df_filtered)} data yang tersedia.")
    
    else:
        st.warning("Data tidak tersedia atau kosong dari API.")
else:
    st.error(f"Gagal mengambil data dari API. Status code: {response.status_code}")
    

# Form login jika role sudah dipilih
if st.session_state.role and not st.session_state.logged_in:
    st.markdown(
        f"""
        <div style="background-color: #D5DBDB; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
            <b>🔑 Login sebagai {st.session_state.role}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form(key="login_form"):
        username = st.text_input("👤 Username")
        password = st.text_input("🔒 Password", type="password")
        submit_button = st.form_submit_button("✅ Login", use_container_width=True)

    if submit_button:
        creds = USER.get(st.session_state.role, {})
        if username == creds.get("username") and password == creds.get("password"):
            st.session_state.logged_in = True
            st.success("✅ Login berhasil! Redirecting...")
            st.rerun()
        else:
            st.error("❌ Username atau password salah!")

# Navigasi halaman setelah login
if st.session_state.logged_in:
    
    if st.session_state.role == "SPV":
        page = st.sidebar.selectbox("📌 Pilih Halaman:", ["Tambah SPK", "Update SPK", "Approval Preventive Form"], index=0)

        if page == "Tambah SPK":
            import add_spk_spv
            add_spk_spv.run()
        elif page == "Update SPK":
            import update_spk_spv
            update_spk_spv.run()
        elif page == "Approval Preventive Form":
            import try_SPV
            try_SPV.run()

    elif st.session_state.role == "SM":
        import try_SM
        try_SM.run()
