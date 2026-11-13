from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from engine import META, SOURCE, SURAT, category_initial, compare, display_result, initialize, prepare_auto, read_csv, read_excel
from sheets_sync import TAB, load as load_sheet, sync


def review_table(df, show_bottom=False):
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
        .table-wrap {{ overflow: auto; height: 520px; border: 1px solid #686b73; border-radius: 8px; }}
        .table-wrap:focus-visible {{ outline: 3px solid #e26058; outline-offset: -3px; }}
        table {{ border-collapse: separate; border-spacing: 0; table-layout: fixed; }}
        th, td {{ min-width: 160px; max-width: 160px; width: 160px; padding: 8px; border-right: 1px solid #414854; border-bottom: 1px solid #414854; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; background: #0e1117; }}
        th {{ position: sticky; top: 0; z-index: 2; text-align: left; background: #262b35; }}
        .pinned {{ position: sticky; z-index: 1; background: #17202c; }}
        th.pinned {{ z-index: 3; background: #293849; }}
        tbody tr:hover td {{ background: #252d38; }}
        @media (max-width: 900px) {{
            td.pinned {{ position: static; }}
            th.pinned {{ right: auto !important; z-index: 2; }}
        }}
    </style></head><body><div class="table-wrap" tabindex="0" aria-label="Tinjau hasil, geser tabel untuk melihat kolom lain"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>
    <script>const table = document.querySelector('.table-wrap'); {"table.scrollTop = table.scrollHeight;" if show_bottom else "table.scrollLeft = table.scrollWidth;"}</script></body></html>'''
    st.components.v1.html(html, height=525, scrolling=False)

st.set_page_config(page_title="Pengolah HDUL", layout="wide")
st.markdown(f"<style>{Path(__file__).with_name('ui.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
st.title("Pengolah data kontrol")
st.caption("Bandingkan data kontrol, pantau perubahan HDUL, dan simpan hasil ke Google Sheets.")

def save(df):
    sync(df)


if "dataset" not in st.session_state:
    try:
        st.session_state.dataset = load_sheet()
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

st.subheader("1. Impor data")
st.caption("Tarik file ke kotak di bawah atau pilih file dari perangkat. Mendukung CSV dan Excel (.xlsx).")
file = st.file_uploader("Pilih file CSV atau Excel untuk diimpor", label_visibility="collapsed", type=["csv", "xlsx"], key=f"upload_{st.session_state.get('uploader_revision', 0)}")
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
            st.caption(f"{file.name} · {len(cleaned):,} baris · {len(cleaned.columns)} kolom")
            with st.expander("Lihat 10 baris pertama file"):
                st.dataframe(cleaned.head(10), width="stretch", hide_index=True)
            if dataset is None:
                pending = initialize(cleaned, day=import_date)
            else:
                pending, new_rows = compare(dataset, cleaned, day=import_date)
    except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
        st.error(f"File belum dapat diproses: {exc}")

if pending is not None:
    st.divider()
    st.subheader("2. Tinjau hasil")
    review_table(display_result(pending), show_bottom=new_rows is not None and not new_rows.empty)
    if st.button("Simpan hasil ke dataset", type="primary"):
        result = pending
        try:
            with st.spinner("Menyimpan hasil ke Google Sheets…"):
                save(result)
            st.session_state.saved_message = f"{len(result):,} baris berhasil disimpan ke tab {TAB}."
            st.session_state.dataset = result
            st.session_state.revision += 1
            st.session_state["uploader_revision"] = st.session_state.get("uploader_revision", 0) + 1
            st.rerun()
        except Exception as exc:
            st.error(f"Gagal menyimpan ke Google Sheets: {exc}")

if dataset is not None:
    if st.session_state.get("saved_message"):
        st.success(st.session_state.pop("saved_message"))
    st.download_button("Unduh CSV hasil", display_result(dataset).to_csv(index=False).encode("utf-8-sig"), "hasil_kontrol.csv", "text/csv")

st.caption(f"Dataset disimpan di tab {TAB}. Edit langsung di Google Sheets dapat tertimpa saat aplikasi menyimpan.")
