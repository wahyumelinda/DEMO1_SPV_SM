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
    API_URL = "https://script.google.com/macros/s/AKfycbzY_RY2XLPmVOTqMLG-GqFShxCsCC3rQW54o5efxwNgwxk0k9RqBzqQptC7_VnQUz_86g/exec"

    # Ambil semua data 
    def get_all_data():
        response = requests.get(f"{API_URL}?action=get_data")
        if response.status_code == 200:
            return response.json()
        return []

    # Ambil opsi SM dari sheet Google Spreadsheet
    def get_sm_list():
        response = requests.get(f"{API_URL}?action=get_options")
        if response.status_code == 200:
            options = response.json()
            return options.get("SM", [])
        return []

    # Inisialisasi semua data
    all_data = get_all_data()

    # Jika data berhasil diambil
    if all_data:
        # Konversi ke DataFrame
        df = pd.DataFrame(all_data, columns=[
            "ID", "BU", "Line", "Produk", "Mesin", "Nomor Mesin","Tanggal Pengerjaan",
            "Mulai", "Selesai", "Masalah", "Tindakan Perbaikan", "Deskripsi",
            "Quantity", "PIC", "Kondisi", "Alasan", "SPV", "Last Update SPV", 
            "Approve", "Reason", "SM", "Last Update SM"
        ])

        # Pastikan kolom yang digunakan benar
        if "ID" in df.columns and "Approve" in df.columns:

            # **Pilihan ID dari selectbox (berdasarkan hasil filter)**
            id_to_update = st.selectbox("Pilih ID untuk diupdate", df)

            # **Jika ID dipilih, tampilkan data terkait**
            if id_to_update:
                record = df[df["ID"] == id_to_update]
                st.write("### Data Saat Ini:")
                st.dataframe(record)
                
                kondisi_status = record["Kondisi"].values[0]
                
                if kondisi_status in ["","On Progress"]:
                    st.warning("🚫 Data ini belum dalam kondisi close/done oleh SPV!")
                else:
                    # Pilihan kondisi
                    kondisi_options = ["Approved", "Revise"]
                    kondisi = st.selectbox("Pilih Kondisi", kondisi_options)

                    # Alasan hanya muncul jika kondisi "Revise"
                    alasan = ""
                    if kondisi == "Revise":
                        alasan = st.text_area("Alasan")

                    # Pilihan SM dari Google Sheet
                    sm_list = get_sm_list()
                    sm = st.selectbox("SM", sm_list)

                    # **Tombol Update Data**
                    if st.button("Update Data"):
                        data = {
                            "action": "update_data",
                            "ID": id_to_update,
                            "Approve": kondisi,
                            "Reason": alasan,
                            "SM": sm
                        }

                        response = requests.post(API_URL, data=json.dumps(data))

                        if response.status_code == 200:
                            result = response.json()
                            last_update_sm = result.get("last_update_sm", "Tidak tersedia")
                            
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
