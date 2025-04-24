import streamlit as st
import requests
import pandas as pd

def overview():
    # URL dari Apps Script Web App
    API_URL = "https://script.google.com/macros/s/AKfycbxvwyWXOiVC812g2ZO-Uzr6HtYujXnx7nu75YW26KVH1kCHWUUvh_uXSA65Hc4W-zknpQ/exec"

    # Pilihan sheet yang bisa ditampilkan
    option = st.selectbox("📂 Pilih Data yang Ingin Dilihat:", ["Data Preventive", "Data SPK"])

    # Ambil data sesuai pilihan
    if option == "Data Preventive":
        response = requests.get(f"{API_URL}?action=get_all_data")
        expected_columns = [
            "ID", "BU", "Line", "Produk", "Mesin", "Nomor Mesin", "Tanggal Pengerjaan",
            "Mulai", "Selesai", "Masalah", "Tindakan Perbaikan", "Deskripsi",
            "Quantity", "PIC", "Kondisi", "Alasan", "SPV", "Last Update SPV", 
            "Approve", "Reason", "SM", "Last Update SM"
        ]
    elif option == "Data SPK":
        response = requests.get(f"{API_URL}?action=get_data")
        expected_columns = [
            "ID", "BU", "Line", "Produk", "Mesin", "Nomor Mesin",
            "Masalah", "Tindakan Perbaikan", "Tanggal Pengerjaan", "PIC", "Keterangan", "Last Update"
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