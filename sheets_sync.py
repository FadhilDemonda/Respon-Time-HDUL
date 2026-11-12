"""Sinkronisasi hasil ke tab khusus Google Sheets."""
from pathlib import Path

import gspread
import pandas as pd
import streamlit as st
from gspread.exceptions import WorksheetNotFound

SPREADSHEET_ID = "1dbUFFyyseXObg7r4jLofnTrUcWycte4YryeSH62GuII"
TAB = "Data"
RAW_TAB = "Data_kerja_HDUL"


def open_sheet():
    try:
        credentials = dict(st.secrets["gcp_service_account"])
    except (FileNotFoundError, KeyError):
        credentials = None
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    if credentials:
        client = gspread.service_account_from_dict(credentials, scopes=scopes)
    else:
        keys = list(Path("data").glob("*.json"))
        if len(keys) != 1:
            raise ValueError("Isi Secrets [gcp_service_account] atau letakkan satu file JSON service account di folder data.")
        client = gspread.service_account(filename=str(keys[0]), scopes=scopes)
    return client.open_by_key(SPREADSHEET_ID)


def load():
    sheet = open_sheet()
    try:
        tab = sheet.worksheet(RAW_TAB)
        legacy = False
    except WorksheetNotFound:
        try:
            tab = sheet.worksheet(TAB)
        except WorksheetNotFound:
            return None, False
        legacy = True
    values = tab.get_all_values()
    if not values:
        return None, False
    columns = values[0]
    if any(not col for col in columns) or len(columns) != len(set(columns)):
        raise ValueError(f"Nama kolom pada tab {tab.title} kosong atau duplikat.")
    rows = [row[:len(columns)] + [""] * max(0, len(columns) - len(row)) for row in values[1:]]
    return pd.DataFrame(rows, columns=columns, dtype=str), legacy


def write_tab(sheet, title, df):
    try:
        tab = sheet.worksheet(title)
    except WorksheetNotFound:
        tab = sheet.add_worksheet(title=title, rows=1, cols=1)
    current = tab.get_all_values()
    values = [list(df.columns)] + df.fillna("").astype(str).values.tolist()
    width = max(len(values[0]), max((len(row) for row in current), default=0))
    height = max(len(values), len(current))
    padded = [row + [""] * (width - len(row)) for row in values]
    padded.extend([[""] * width for _ in range(height - len(values))])
    if tab.row_count < height or tab.col_count < width:
        tab.resize(rows=max(tab.row_count, height), cols=max(tab.col_count, width))
    tab.update(values=padded, range_name="A1", value_input_option="RAW")


def sync(df, shown):
    sheet = open_sheet()
    write_tab(sheet, RAW_TAB, df)
    write_tab(sheet, TAB, shown)
