import pandas as pd
import streamlit as st
from fpdf import FPDF
from textwrap import wrap

def run():
    # 1. LINK CSV dari Google Sheets
    sheet_url = "https://docs.google.com/spreadsheets/d/1z5o3P6nxcYMRz23EYUnjkLJUAKpOIkpe7-YI11mt4Ps/export?format=csv&gid=771407842"

    # 2. Baca CSV secara aman
    df = pd.read_csv(sheet_url, engine='python', on_bad_lines='skip')
    df['Tanggal Pengerjaan'] = pd.to_datetime(df['Tanggal Pengerjaan'], errors='coerce')
    df = df.reset_index(drop=True)

    # 3. Pilih kolom ID dan tampilkan opsi
    st.title("🖨️ Cetak PDF Data SPK")

    # Tentukan kolom ID lebih awal
    kolom_id = [col for col in df.columns if "id" in col.lower()][0]

    st.subheader("📆 Filter berdasarkan Rentang Tanggal Pengerjaan")

    # Atur default rentang tanggal
    min_date = df['Tanggal Pengerjaan'].min().date()
    max_date = df['Tanggal Pengerjaan'].max().date()

    tanggal_range = st.date_input("Pilih rentang tanggal", value=(min_date, max_date))

    if len(tanggal_range) == 2:
        tanggal_awal, tanggal_akhir = tanggal_range
        df_filtered = df[(df['Tanggal Pengerjaan'] >= pd.to_datetime(tanggal_awal)) &
                        (df['Tanggal Pengerjaan'] <= pd.to_datetime(tanggal_akhir))]
        
        ids_terpilih = df_filtered[kolom_id].dropna().unique()
        st.write(f"{len(ids_terpilih)} data ditemukan untuk periode tersebut.")
    else:
        ids_terpilih = []


    # 4. Fungsi untuk membuat PDF dari beberapa baris
    def buat_pdf_satu_halaman(rows, tanggal_awal, tanggal_akhir):
        from textwrap import wrap

        pdf = FPDF("L", "mm", "A4")
        pdf.set_auto_page_break(auto=True, margin=15)

        headers = ["ID", "Tanggal Pengerjaan", "Line", "Produk", "Mesin", "Nomor Mesin", "Masalah", "Tindakan Perbaikan", "PIC"]
        col_widths = [8, 35, 20, 25, 30, 25, 45, 60, 30]
        line_height = 6

        last_bu = None

        for row in rows:
            current_bu = row.get("BU", "")
            if current_bu != last_bu:
                pdf.add_page()
                last_bu = current_bu

                # HEADER
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "PT. ULTRA PRIMA ABADI", ln=True, align="C")

                pdf.set_font("Arial", "B", 13)
                pdf.cell(0, 10, "SURAT PERINTAH KERJA", ln=True, align="C")
                pdf.ln(3)

                tgl_awal_str = tanggal_awal.strftime('%d-%b-%y')
                tgl_akhir_str = tanggal_akhir.strftime('%d-%b-%y')
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 8, f"BU: {current_bu} | Periode: {tgl_awal_str} s.d. {tgl_akhir_str}", ln=True)
                pdf.ln(3)

                # Header tabel
                pdf.set_font("Arial", "B", 10)
                for i in range(len(headers)):
                    pdf.cell(col_widths[i], 8, headers[i], border=1, align="C")
                pdf.ln()
                pdf.set_font("Arial", "", 10)

            # CETAK ROW
            # Hitung tinggi row terlebih dahulu
            isi_data = []
            for h in headers:
                val = row.get(h)
                if h == "Tanggal Pengerjaan":
                    val = pd.to_datetime(val).strftime('%d-%b-%y') if pd.notnull(val) else ""
                isi_data.append(str(val) if val is not None else "")

            wrapped_cells = []
            heights = []
            for i, content in enumerate(isi_data):
                baris_baru = content.splitlines()
                hasil_wrap = []
                for baris in baris_baru:
                    hasil_wrap.extend(wrap(baris, width=int(col_widths[i] / 2.5)) or [""])
                wrapped_cells.append(hasil_wrap)
                heights.append(len(hasil_wrap))

            max_lines = max(heights)
            row_height = max_lines * line_height

            # 🚨 Cek apakah masih cukup di halaman
            if pdf.get_y() + row_height > pdf.h - pdf.b_margin:
                pdf.add_page()
                # Cetak ulang header BU
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "PT. ULTRA PRIMA ABADI", ln=True)
                pdf.set_font("Arial", "", 12)
                tgl_awal_str = tanggal_awal.strftime('%d-%b-%y')
                tgl_akhir_str = tanggal_akhir.strftime('%d-%b-%y')
                pdf.cell(0, 8, f"BU: {current_bu} | Periode: {tgl_awal_str} s.d. {tgl_akhir_str}", ln=True)
                pdf.ln(5)
                pdf.set_font("Arial", "B", 13)
                pdf.cell(0, 10, "SURAT PERINTAH KERJA", ln=True, align="C")
                pdf.ln(3)
                pdf.set_font("Arial", "B", 10)
                for i in range(len(headers)):
                    pdf.cell(col_widths[i], 8, headers[i], border=1, align="C")
                pdf.ln()
                pdf.set_font("Arial", "", 10)


            x_start = pdf.get_x()
            y_start = pdf.get_y()

            for i, lines in enumerate(wrapped_cells):
                text = "\n".join(lines)
                align = "L" if headers[i] in ["Masalah", "Tindakan Perbaikan"] else "C"
                pdf.set_xy(x_start + sum(col_widths[:i]), y_start)
                pdf.multi_cell(col_widths[i], line_height, text, border=0, align=align)

            for i in range(len(headers)):
                pdf.rect(x_start + sum(col_widths[:i]), y_start, col_widths[i], row_height)

            pdf.set_y(y_start + row_height)

        # FOOTER di halaman terakhir
        pdf.ln(10)
        pdf.set_font("Arial", "", 10)
        pdf.cell(200)
        pdf.cell(40, 8, "Dibuat oleh,", ln=False)
        pdf.cell(40, 8, "Mengetahui,", ln=True)
        pdf.cell(200)
        pdf.cell(40, 8, "Spv Shift 1", ln=False)
        pdf.cell(40, 8, "SM Teknik", ln=True)

        return pdf.output(dest="S").encode("latin-1")


    # 5. Tombol Download jika ada ID dipilih
    if len(df_filtered) > 0:
        df_filtered = df_filtered.sort_values(by=["BU", "ID"])
        rows_terpilih = df_filtered.to_dict(orient="records")
        pdf_file = buat_pdf_satu_halaman(rows_terpilih, tanggal_awal, tanggal_akhir)
        st.download_button(
            label="📥 Download PDF",
            data=pdf_file,
            file_name=f"Riwayat_Mesin_{tanggal_awal.strftime('%d%b')}_sd_{tanggal_akhir.strftime('%d%b')}.pdf",
            mime="application/pdf"
        )
