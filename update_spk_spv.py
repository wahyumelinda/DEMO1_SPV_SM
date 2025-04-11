import streamlit as st
import requests
import pandas as pd
from datetime import datetime

def run():
    st.markdown(
        """
        <h1 style='text-align: center; color: white; background-color: #F8C471; padding: 15px; border-radius: 10px;'>
            📝 Update Data SPK
        </h1>
        """,
        unsafe_allow_html=True
    )

    APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw8xKTrFGJtqhhkLWOBj4jyMrJQ-id9zWXOouUVoz1mF91IF5uPUuPw2fIm4gxoXDzf/exec"

    def get_all_data():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_data"}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil data: {e}")
            return []

    def get_options():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_options"}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil opsi: {e}")
            return {}

    def get_all_ids():
        try:
            response = requests.get(APPS_SCRIPT_URL, params={"action": "get_all_ids"}, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Terjadi kesalahan saat mengambil ID: {e}")
            return []

    data = get_all_data()
    options = get_options()
    all_ids = get_all_ids()

    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data, columns=["ID", "BU", "Line", "Produk", "Mesin", "Nomor Mesin", "Masalah", "Tindakan", "Tanggal", "PIC", "Keterangan", "Last Update"])
        df["Tanggal"] = pd.to_datetime(df["Tanggal"]).dt.date  

        # Hapus data yang ID-nya ada di all_ids
        editable_df = df[~df["ID"].astype(str).isin([str(i) for i in all_ids])]

        if not editable_df.empty:
            st.subheader("Pilih Data untuk Diperbarui")
            selected_id = st.selectbox("Pilih ID", editable_df["ID"].astype(str))
            selected_data = editable_df[editable_df["ID"].astype(str) == selected_id].iloc[0]
            
            st.subheader("Form Update Data")
            bu_options = [item[0] for item in options.get("BU", []) if isinstance(item, list)]
            bu = st.selectbox("BU", bu_options, index=bu_options.index(selected_data["BU"]) if selected_data["BU"] in bu_options else 0)
            
            produk_options = [item[1] for item in options.get("Produk", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu]
            produk = st.selectbox("Produk", produk_options, index=produk_options.index(selected_data["Produk"]) if selected_data["Produk"] in produk_options else 0)
            
            line_options = [item[1] for item in options.get("Line", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu]
            line = st.selectbox("Line", line_options, index=line_options.index(selected_data["Line"]) if selected_data["Line"] in line_options else 0)
            
            mesin_options = [item[1] for item in options.get("Mesin", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu]
            mesin = st.selectbox("Mesin", mesin_options, index=mesin_options.index(selected_data["Mesin"]) if selected_data["Mesin"] in mesin_options else 0)
            
            nomor = st.text_input("Nomor Mesin", value=selected_data["Nomor Mesin"])

            masalah_options = [item[1] for item in options.get("Masalah", []) if isinstance(item, list) and len(item) > 1 and item[0] == mesin]
            masalah = st.selectbox("Masalah", masalah_options, index=masalah_options.index(selected_data["Masalah"]) if selected_data["Masalah"] in masalah_options else 0)
            
            tindakan = st.text_area("Tindakan Perbaikan", value=selected_data["Tindakan"])
            
            keterangan = st.text_area("Keterangan", value=selected_data["Keterangan"])

            tanggal = st.date_input("Tanggal Pengerjaan", value=pd.to_datetime(selected_data["Tanggal"], format="%d-%b-%y").date())
            
            pic_options = [item[1] for item in options.get("PIC", []) if isinstance(item, list) and len(item) > 1 and item[0] == bu]
            pic = st.multiselect("PIC", pic_options, default=[selected_data["PIC"]] if selected_data["PIC"] in pic_options else [])
            
            if selected_id:
                st.subheader("🔍 Perbandingan Data Sebelum & Sesudah")

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 🟠 **Sebelum Update**")
                    st.dataframe(pd.DataFrame([selected_data]))

                with col2:
                    st.markdown("### 🟢 **Setelah Update**")
                    updated_data = {
                        "ID": selected_id,
                        "BU": bu,
                        "Line": line,
                        "Produk": produk,
                        "Mesin": mesin,
                        "Nomor": nomor,
                        "Masalah": masalah,
                        "Tindakan": tindakan,
                        "Tanggal": tanggal.strftime("%d-%b-%y"),
                        "PIC": ", ".join(pic) if pic else "",
                        "Keterangan": keterangan
                    }
                    st.dataframe(pd.DataFrame([updated_data]))

                st.markdown("---")  # Garis pemisah sebelum tombol update

            # Tombol Update Data
            if st.button("Update Data"):
                update_data = {
                    "action": "update_data",
                    "ID": selected_id,
                    "BU": bu,
                    "Line": line,                    
                    "Produk": produk,
                    "Mesin": mesin,
                    "Nomor": nomor,
                    "Masalah": masalah,
                    "Tindakan": tindakan,
                    "Keterangan": keterangan,
                    "Tanggal": tanggal.strftime("%d-%b-%y"),
                    "PIC": ", ".join(pic) if pic else ""
                }

                try:
                    response = requests.post(APPS_SCRIPT_URL, json=update_data, timeout=10)
                    response.raise_for_status()
                    result = response.json()
                    if result.get("status") == "success":
                        st.success("✅ Data berhasil diperbarui!")
                        st.rerun()
                    else:
                        st.error(f"❌ Gagal memperbarui data: {result.get('error', 'Tidak diketahui')}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Terjadi kesalahan saat mengirim data: {e}")

        else:
            st.warning("Tidak ada data yang bisa diperbarui karena ID sudah ada di sheet ALL.")
    else:
        st.warning("Tidak ada data yang tersedia.")

if __name__ == "__main__":
    run()
