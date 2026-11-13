from datetime import date, datetime
from html import escape
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from engine import INSERTED, KEY, META, RESPON, SOURCE, SURAT, UPDATED, category_initial, compare, display_result, initialize, prepare_auto, read_csv, read_excel
from sheets_sync import TAB, load as load_sheet, sync


def review_table(df):
    fixed = ["no_surat_kontrol_baru", "respon_bpjs_baru", "updated_date_baru", "kategori"]
    columns = [col for col in df.columns if col not in fixed] + [col for col in fixed if col in df.columns]
    pinned = [col for col in fixed if col in columns]

    def cell(tag, value, col):
        style = ""
        if col in pinned:
            offset = (len(pinned) - pinned.index(col) - 1) * 160
            style = f' class="pinned" style="right:{offset}px"'
        text = escape(str(value))
        return f'<{tag}{style} title="{text}">{text}</{tag}>'

    header = "".join(cell("th", col, col) for col in columns)
    body = "".join("<tr>" + "".join(cell("td", value, col) for col, value in zip(columns, row)) + "</tr>" for row in df[columns].itertuples(index=False, name=None))
    html = f'''<!doctype html><html lang="id"><head><style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; font: 14px sans-serif; color: #fafafa; background: #0e1117; }}
        .table-wrap {{ overflow: auto; height: 520px; border: 1px solid #414854; }}
        table {{ border-collapse: separate; border-spacing: 0; table-layout: fixed; }}
        th, td {{ min-width: 160px; max-width: 160px; width: 160px; padding: 8px; border-right: 1px solid #414854; border-bottom: 1px solid #414854; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; background: #0e1117; }}
        th {{ position: sticky; top: 0; z-index: 2; text-align: left; background: #262b35; }}
        .pinned {{ position: sticky; z-index: 1; background: #17202c; }}
        th.pinned {{ z-index: 3; background: #293849; }}
    </style></head><body><div class="table-wrap" tabindex="0" aria-label="Tinjau hasil, geser tabel untuk melihat kolom lain"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>
    <script>const table = document.querySelector('.table-wrap'); table.scrollLeft = table.scrollWidth;</script></body></html>'''
    st.components.v1.html(html, height=525, scrolling=False)

st.set_page_config(page_title="Pengolah HDUL", layout="wide")
st.title("Pengolah data kontrol")
st.caption("Impor CSV atau Excel, rapikan data, cocokkan rencana kontrol, lalu unduh hasilnya.")

def save(df):
    sync(df, display_result(df))


if "dataset" not in st.session_state:
    try:
        st.session_state.dataset, st.session_state.legacy_sheet = load_sheet()
    except Exception as exc:
        st.error(f"Gagal membaca Google Sheets: {exc}")
        st.stop()
if "revision" not in st.session_state:
    st.session_state.revision = 0
dataset = st.session_state.dataset
if dataset is not None and (any(c not in dataset.columns for c in SOURCE) or "no_surat_kontrol_baru" not in dataset.columns):
    st.error("Dataset tersimpan memakai format lama. Gunakan database baru melalui HDUL_DB_PATH, lalu impor ulang data awal. Data lama tidak dihapus.")
    st.stop()
if dataset is not None:
    dataset = dataset.copy()
    for col in META:
        if col not in dataset.columns:
            dataset[col] = ""
    dataset["kategori_awal"] = dataset[SURAT].map(category_initial)
    if st.session_state.get("legacy_sheet", False):
        st.info("Dataset dibaca dari tab Data. Impor data terbaru untuk melengkapi nilai pembanding sebelum mengedit tabel.")

st.subheader("1. Impor data")
st.write("Unggah CSV atau Excel. Kolom dan pemisah CSV dikenali otomatis.")
file = st.file_uploader("File CSV atau Excel", type=["csv", "xlsx"], key=f"upload_{st.session_state.get('uploader_revision', 0)}")
pending = None
new_rows = None
if file:
    try:
        import_date = st.date_input("Tanggal pengambilan data", value=datetime.now(ZoneInfo("Asia/Jakarta")).date(), help="Pilih tanggal saat data dalam file diambil.")
        raw = read_excel(file.getvalue()) if file.name.lower().endswith(".xlsx") else read_csv(file.getvalue())
        if raw.empty or len(raw.columns) < 5:
            st.error("File harus memiliki data dan setidaknya lima kolom.")
        else:
            cleaned = prepare_auto(raw)
            st.caption(f"Pratinjau impor: {len(cleaned)} baris. Kolom wajib dikenali otomatis.")
            st.dataframe(cleaned.head(10), width="stretch")
            if dataset is None:
                pending = initialize(cleaned, day=import_date)
            else:
                pending, new_rows = compare(dataset, cleaned, day=import_date)
    except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
        st.error(f"File belum dapat diproses: {exc}")

if pending is not None:
    st.subheader("2. Tinjau hasil")
    st.caption("Jika nomor surat sudah terbit, target dihitung dari inserted_date awal sampai updated_date baru: 0–2 hari sesuai target.")
    st.caption("Jika masih HDUL, target dihitung sampai tanggal pengambilan data terbaru.")
    st.caption("Kolom baru dikosongkan pada tampilan jika nilainya sama dengan data awal. Kategori awal kosong atau '-' dihitung sebagai Tidak HDUL.")
    st.caption("Kolom surat, respons, tanggal terbaru, dan kategori tetap terlihat di kanan. Geser tabel ke kiri untuk melihat kolom lain.")
    review_table(display_result(pending))
    if new_rows is not None and not new_rows.empty:
        st.info(f"{len(new_rows)} ID baru ditambahkan di bagian bawah hasil.")
    if st.button("Simpan hasil ke dataset", type="primary"):
        result = pending
        try:
            save(result)
            st.session_state.dataset = result
            st.session_state.legacy_sheet = False
            st.session_state.revision += 1
            st.session_state["uploader_revision"] = st.session_state.get("uploader_revision", 0) + 1
            st.rerun()
        except Exception as exc:
            st.error(f"Gagal menyimpan ke Google Sheets: {exc}")

st.subheader("3. Dataset kerja")
if dataset is None:
    st.info("Belum ada dataset. Unggah CSV pertama untuk memulai.")
else:
    st.caption("Edit kolom sumber atau tambah baris. Kolom perbandingan dihitung dari data impor dan tidak dapat diedit langsung.")
    edited = st.data_editor(display_result(dataset), num_rows="dynamic", disabled=META, width="stretch", key=f"editor_{st.session_state.revision}")
    if st.button("Simpan edit tabel", disabled=st.session_state.get("legacy_sheet", False)):
        try:
            edited = edited.fillna("").astype(str)
            edited[KEY] = edited[KEY].str.strip()
            if edited[KEY].eq("").any() or edited[KEY].duplicated().any():
                raise ValueError("Setiap baris harus memiliki ID yang unik dan tidak kosong.")
            existing = set(dataset[KEY])
            if not existing.issubset(set(edited[KEY])):
                raise ValueError("Menghapus atau mengubah ID lama belum didukung; gunakan ID baru untuk baris tambahan.")
            old = dataset.set_index(KEY)
            for idx, row in edited.iterrows():
                if row[KEY] in existing:
                    for col in META:
                        edited.at[idx, col] = old.at[row[KEY], col]
                    row = edited.loc[idx]
                if row[KEY] in existing and row["ketersediaan_data"] == "Ditemukan":
                    original = pd.DataFrame([row])
                    comparison = pd.DataFrame([{KEY: row[KEY], SURAT: row["no_surat_kontrol_baru"], INSERTED: row[INSERTED], UPDATED: row["updated_date_baru"], RESPON: row["respon_bpjs_baru"]}])
                    try:
                        snapshot_date = date.fromisoformat(row["tanggal_pengambilan_data"])
                    except ValueError:
                        snapshot_date = None
                    recalculated, _ = compare(original, comparison, day=snapshot_date)
                    for col in META:
                        edited.at[idx, col] = recalculated.iloc[0][col]
                elif row[KEY] in existing:
                    edited.at[idx, "kategori_awal"] = category_initial(row[SURAT])
                if row[KEY] not in existing:
                    fresh = initialize(pd.DataFrame([row.drop(labels=META)])).iloc[0]
                    for col in META:
                        edited.at[idx, col] = fresh[col]
            save(edited)
            st.session_state.dataset = edited
            st.session_state.revision += 1
            st.success("Edit tersimpan.")
            st.rerun()
        except Exception as exc:
            st.error(f"Gagal menyimpan: {exc}")
    st.download_button("Unduh CSV hasil", display_result(dataset).to_csv(index=False).encode("utf-8-sig"), "hasil_kontrol.csv", "text/csv")

st.caption(f"Dataset kerja disimpan di tab Data_kerja_HDUL; hasil ditampilkan di tab {TAB}. Edit langsung di Google Sheets dapat tertimpa saat aplikasi menyimpan.")
