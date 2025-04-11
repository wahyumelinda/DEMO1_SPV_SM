import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, time
import time as tm

def run():
    st.markdown(
        """
        <h1 style='text-align: center; color: white; background-color: #A9DFBF; padding: 15px; border-radius: 10px;'>
            ➕ Tambah Data SPK
        </h1>
        """,
        unsafe_allow_html=True
    )

    # apps script
    APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw8xKTrFGJtqhhkLWOBj4jyMrJQ-id9zWXOouUVoz1mF91IF5uPUuPw2fIm4gxoXDzf/exec"

    def get_all_data():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_data"}, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil data: {e}")
            return []

        
    # untuk mendapatkan opsi dari gsheets
    def get_options():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_options"}, timeout=20)
            response.raise_for_status()
            options = response.json()
            
            # menambahkan opsi kosong "" sebagai default di setiap kategori
            for key in options:
                options[key].insert(0, "")
            return options
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil data: {e}")
            return {}

    # mengambil data hanya saat pertama kali
    if "all_data" not in st.session_state:
        st.session_state.all_data = get_all_data()
    if "options" not in st.session_state:
        st.session_state.options = get_options()

    # untuk mengirim data ke gsheets
    def add_data(form_data):
        try:
            response = requests.post(APPS_SCRIPT_URL, json=form_data, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e)}

    # mengambil data untuk select box
    options = get_options()

    # cek dan set default di session_state jika belum ada
    defaults = {
        "form_bu": "",
        "form_line": "",
        "form_produk": "",
        "form_nomor": "",
        "form_mesin": "",
        "form_masalah": "",
        "form_tindakan": "",
        "form_keterangan": "",
        "form_pic": "",
        "form_date": datetime.today().date(),
    }

    if "reset_trigger" not in st.session_state:
        st.session_state.reset_trigger = False

    if st.session_state.reset_trigger:
        for key, value in defaults.items():
            st.session_state[key] = value
        st.session_state.reset_trigger = False

    st.subheader("Isi Data Berikut:")

    bu_options = [item[0] if isinstance(item, list) and item else item for item in options.get("BU", [""])]
    bu = st.selectbox("BU", bu_options, key="form_bu")

    # reset produk jika BU berubah
    if bu != st.session_state.form_bu:
        st.session_state.form_bu = bu
        st.session_state.form_produk = ""
        st.session_state.form_pic = ""
        st.session_state.form_line = ""

    produk_options = [item[1] for item in options.get("Produk", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu] if bu else [""]
    produk = st.selectbox("Produk", produk_options, key="form_produk")
    
    line_options = [item[1] for item in options.get("Line", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu] if bu else [""]
    line = st.selectbox("Line", line_options , key="form_line")

    mesin_options = [item[1] for item in options.get("Mesin", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu] if bu else [""]
    mesin = st.selectbox("Mesin", mesin_options, key="form_mesin")

    if mesin != st.session_state.form_mesin:
        st.session_state.form_mesin = mesin
        st.session_state.form_masalah = "" 
        
    nomor_mesin = st.text_input("Nomor Mesin", value=st.session_state.get("form_nomor"))

    masalah_options = [item[1] for item in options.get("Masalah", []) if isinstance(item, list) and len(item) > 1 and item[0] == mesin] if bu else [""]
    masalah = st.selectbox("Masalah", masalah_options, key="form_masalah")

    tindakan = st.text_area("Tindakan Perbaikan", value=st.session_state.get("form_tindakan"))
    
    keterangan = st.text_area("Keterangan", value=st.session_state.get("form_keterangan"))

    tanggal = st.date_input("Tanggal Pengerjaan", value=st.session_state.get("form_date"))

    # daftar PIC berdasarkan BU yang dipilih
    pic_options = [item[1] for item in options.get("PIC", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu]
    pic_options = list(pic_options) if pic_options else []  # Pastikan tetap list, bahkan jika kosong

    default_pic = st.session_state.get("form_pic", [])
    default_pic = [p for p in default_pic if p in pic_options]  # Hanya simpan yang valid

    pic = st.multiselect("PIC", pic_options, default=default_pic, key="form_pic")

    all_filled = all([bu, line, produk, mesin, masalah, (tindakan or "").strip(), tanggal, pic])

    if all_filled:
        st.subheader("🔍 **Overview Data yang Akan Dikirim**")
        data_to_send = {
            "BU": bu,
            "Line": line,
            "Produk": produk,
            "Mesin": mesin,
            "Nomor": nomor_mesin,
            "Masalah": masalah,
            "Tindakan": tindakan.strip(),
            "Keterangan" : keterangan.strip(),
            "Tanggal": tanggal.strftime("%Y-%m-%d"),
            "PIC": ", ".join(pic) if pic else ""
        }
        df_preview = pd.DataFrame([data_to_send])
        st.dataframe(df_preview, use_container_width=True)

    if st.button("➕ Tambah Data", disabled=not all_filled):
        st.session_state.show_confirmation = True  

    if st.session_state.get("show_confirmation", False):
        st.warning("⚠️ Apakah Anda yakin ingin menambahkan data ini?")
        
        col1, col2 = st.columns(2)
        with col1:
            confirm = st.button("✅ Ya, Tambah Data")
        with col2:
            cancel = st.button("❌ Batal")

        if confirm:
            response = add_data({"action": "add_data", **data_to_send})
            if response.get("status") == "success":
                st.toast("✅ Data berhasil ditambahkan!")
                tm.sleep(2)
                st.session_state.show_confirmation = False  
                st.rerun()
            else:
                st.error(f"❌ Gagal menambahkan data: {response.get('error', 'Tidak diketahui')}")
                
        elif cancel:
            st.session_state.show_confirmation = False  
            st.info("✅ Data tidak jadi dikirim.")
            st.rerun()
            
if __name__ == "__main__":
    run()            
