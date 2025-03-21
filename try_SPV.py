import streamlit as st
import requests
import json
import pandas as pd  

def run():
    st.markdown(
        """
        <h1 style='text-align: center; color: white; background-color: #F8C471; padding: 15px; border-radius: 10px;'>
            📝 Approval Preventive Form
        </h1>
        """,
        unsafe_allow_html=True
    )
    # URL apps script
    API_URL = "https://script.google.com/macros/s/AKfycbzr96YkQ_yT1Rld_I3Dw_q64FLKkawP9uTvennnlgJ0T8tYFuK6hiqgOBRj9y5XuZgI/exec"

    # Ambil semua data 
    def get_all_data():
        response = requests.get(f"{API_URL}?action=get_data")
        if response.status_code == 200:
            return response.json()
        return []

    # Ambil opsi SPV dari sheet Google Spreadsheet
    def get_spv_list():
        response = requests.get(f"{API_URL}?action=get_options")
        if response.status_code == 200:
            options = response.json()
            return options.get("SPV", [])
        return []

    # Inisialisasi semua data
    all_data = get_all_data()

    # Jika data berhasil diambil
    if all_data:
        # Konversi ke DataFrame
        df = pd.DataFrame(all_data, columns=[
            "ID", "BU", "Line", "Produk", "Nomor Mesin", "Mesin", "Tanggal Pengerjaan",
            "Mulai", "Selesai", "Masalah", "Tindakan Perbaikan", "Deskripsi",
            "Quantity", "PIC", "Kondisi", "Alasan", "SPV", "Last Update SPV", 
            "Approve", "Reason", "SM", "Last Update SM"
        ])

        # Pastikan kolom yang digunakan benar
        if "ID" in df.columns and "Kondisi" in df.columns:

            # **Pilihan ID dari selectbox (berdasarkan hasil filter)**
            id_to_update = st.selectbox("Pilih ID untuk diupdate", df)

            # **Jika ID dipilih, tampilkan data terkait**
            if id_to_update:
                record = df[df["ID"] == id_to_update]
                st.write("### Data Saat Ini:")
                st.dataframe(record)
                
                approve_status = record["Approve"].values[0]
                
                if approve_status == "Approved":
                    st.warning("🚫 Data ini sudah di-approve oleh SM!")
                else:
                    # Pilihan kondisi
                    kondisi_options = ["On Progress", "Close", "Done"]
                    kondisi = st.selectbox("Pilih Kondisi", kondisi_options)

                    # Alasan hanya muncul jika kondisi "On Progress"
                    alasan = ""
                    if kondisi == "On Progress":
                        alasan = st.text_area("Alasan")

                    # Pilihan SPV dari Google Sheet
                    spv_list = get_spv_list()
                    spv = st.selectbox("SPV", spv_list)

                    # **Tombol Update Data**
                    if st.button("Update Data"):
                        data = {
                            "action": "update_data",
                            "ID": id_to_update,
                            "Kondisi": kondisi,
                            "Alasan": alasan,
                            "SPV": spv
                        }

                        response = requests.post(API_URL, data=json.dumps(data))

                        if response.status_code == 200:
                            result = response.json()
                            last_update_spv = result.get("last_update_spv", "Tidak tersedia")
                            
                            st.success(f"✅ Data berhasil diperbarui!")
                            st.session_state.form_add_reset = True
                            st.rerun()
                        else:
                            st.error("❌ Gagal memperbarui data. Cek kembali input dan koneksi.")
        else:
            st.error("❌ Kolom 'ID' atau 'Kondisi' tidak ditemukan. Periksa struktur data yang diambil!")

    else:
        st.error("❌ Gagal mengambil data dari Google Sheet.")

if __name__ == "__main__":
    run()